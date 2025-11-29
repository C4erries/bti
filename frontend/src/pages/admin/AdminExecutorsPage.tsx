import { useEffect, useState, type FormEvent } from 'react';
import { apiFetch } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import {
  buttonClass,
  cardClass,
  inputClass,
  sectionTitleClass,
  subtleButtonClass,
} from '../../components/ui';
import type { Department, ExecutorDetails } from '../../types';

const AdminExecutorsPage = () => {
  const { token } = useAuth();
  const [form, setForm] = useState({
    email: '',
    password: '',
    fullName: '',
    phone: '',
    departmentCode: '',
    experienceYears: '',
    isAdmin: false,
  });
  const [message, setMessage] = useState<string | null>(null);
  const [executors, setExecutors] = useState<ExecutorDetails[]>([]);
  const [departmentFilter, setDepartmentFilter] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [departments, setDepartments] = useState<Department[]>([]);

  const loadExecutors = async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch<ExecutorDetails[]>(
        '/admin/executors',
        { query: { departmentCode: departmentFilter || undefined } },
        token,
      );
      setExecutors(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка загрузки исполнителей');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadExecutors();
    void loadDepartments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const loadDepartments = async () => {
    if (!token) return;
    try {
      const data = await apiFetch<Department[]>('/admin/departments', {}, token);
      setDepartments(data);
    } catch (err) {
      console.error('Failed to load departments', err);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!token) {
      setMessage('Требуется авторизация');
      return;
    }
    await apiFetch(
      '/admin/executors',
      {
        method: 'POST',
        data: {
          email: form.email,
          password: form.password,
          fullName: form.fullName,
          phone: form.phone || null,
          departmentCode: form.departmentCode || null,
          experienceYears: form.experienceYears ? Number(form.experienceYears) : null,
          isAdmin: form.isAdmin || undefined,
        },
      },
      token,
    );
    setMessage('Исполнитель создан');
    void loadExecutors();
  };

  return (
    <div className="space-y-4">
      <div className={cardClass}>
        <h3 className={sectionTitleClass}>Создание исполнителя</h3>
        {message && <p className="mt-2 text-sm text-slate-700">{message}</p>}
        <form className="mt-3 grid gap-3 lg:grid-cols-3" onSubmit={handleSubmit}>
          <label className="text-sm text-slate-700">
            Email
            <input
              className={`${inputClass} mt-1`}
              value={form.email}
              onChange={(e) => setForm((p) => ({ ...p, email: e.target.value }))}
              required
            />
          </label>
          <label className="text-sm text-slate-700">
            Пароль
            <input
              className={`${inputClass} mt-1`}
              value={form.password}
              onChange={(e) => setForm((p) => ({ ...p, password: e.target.value }))}
              required
            />
          </label>
          <label className="text-sm text-slate-700">
            ФИО
            <input
              className={`${inputClass} mt-1`}
              value={form.fullName}
              onChange={(e) => setForm((p) => ({ ...p, fullName: e.target.value }))}
              required
            />
          </label>
          <label className="text-sm text-slate-700">
            Телефон
            <input
              className={`${inputClass} mt-1`}
              value={form.phone}
              onChange={(e) => setForm((p) => ({ ...p, phone: e.target.value }))}
            />
          </label>
          <label className="text-sm text-slate-700">
            Отдел
            <select
              className={`${inputClass} mt-1`}
              value={form.departmentCode}
              onChange={(e) => setForm((p) => ({ ...p, departmentCode: e.target.value }))}
            >
              <option value="">Не выбран</option>
              {departments.map((d) => (
                <option key={d.code} value={d.code}>
                  {d.name || d.code}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm text-slate-700">
            Стаж (лет)
            <input
              className={`${inputClass} mt-1`}
              value={form.experienceYears}
              onChange={(e) => setForm((p) => ({ ...p, experienceYears: e.target.value }))}
            />
          </label>
          <label className="mt-6 inline-flex items-center gap-2 text-sm font-medium text-slate-700">
            <input
              type="checkbox"
              checked={form.isAdmin}
              onChange={(e) => setForm((p) => ({ ...p, isAdmin: e.target.checked }))}
            />
            Админские права
          </label>
          <button type="submit" className={buttonClass}>
            Создать
          </button>
        </form>
      </div>

      <div className={cardClass}>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className={sectionTitleClass}>Исполнители и аналитика</h3>
          <div className="flex flex-wrap items-center gap-2">
            <input
              className={inputClass}
              placeholder="Код отдела (BTI / GEO / ...)"
              value={departmentFilter}
              onChange={(e) => setDepartmentFilter(e.target.value)}
            />
            <button className={subtleButtonClass} onClick={() => void loadExecutors()}>
              Обновить
            </button>
          </div>
        </div>
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        <div className="mt-3 overflow-auto rounded border">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-100 text-left">
              <tr>
                <th className="px-3 py-2">ФИО</th>
                <th className="px-3 py-2">Email</th>
                <th className="px-3 py-2">Отдел</th>
                <th className="px-3 py-2">Стаж</th>
                <th className="px-3 py-2">Нагрузка</th>
                <th className="px-3 py-2">Всего заказов</th>
                <th className="px-3 py-2">Завершено</th>
                <th className="px-3 py-2">Среднее время</th>
                <th className="px-3 py-2">Последняя активность</th>
              </tr>
            </thead>
            <tbody>
              {executors.map((ex) => {
                const p = ex.executorProfile;
                return (
                  <tr key={ex.user.id} className="hover:bg-slate-50">
                    <td className="px-3 py-2">{ex.user.fullName}</td>
                    <td className="px-3 py-2">{ex.user.email}</td>
                    <td className="px-3 py-2">{p?.departmentCode || '—'}</td>
                    <td className="px-3 py-2">{p?.experienceYears ?? '—'}</td>
                    <td className="px-3 py-2">{ex.currentLoad ?? 0}</td>
                    <td className="px-3 py-2">{ex.totalOrders ?? 0}</td>
                    <td className="px-3 py-2">{ex.completedOrders ?? 0}</td>
                    <td className="px-3 py-2">
                      {ex.avgCompletionDays != null ? `${ex.avgCompletionDays.toFixed(1)} дн.` : '—'}
                    </td>
                    <td className="px-3 py-2">
                      {ex.lastActivityAt ? new Date(ex.lastActivityAt).toLocaleString() : '—'}
                    </td>
                  </tr>
                );
              })}
              {!executors.length && (
                <tr>
                  <td className="px-3 py-4 text-center text-slate-600" colSpan={9}>
                    {loading ? 'Загружаем...' : 'Исполнители не найдены'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AdminExecutorsPage;
