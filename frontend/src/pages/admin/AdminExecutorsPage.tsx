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
import type { ExecutorAnalytics, Department } from '../../types';

const AdminExecutorsPage = () => {
  const { token } = useAuth();
  const [analytics, setAnalytics] = useState<ExecutorAnalytics[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [filters, setFilters] = useState({
    departmentCode: '',
    search: '',
  });
  const [createForm, setCreateForm] = useState({
    email: '',
    password: '',
    fullName: '',
    phone: '',
    departmentCode: '',
    experienceYears: '',
    isAdmin: false,
  });
  const [message, setMessage] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);

  useEffect(() => {
    if (token) {
      void loadAnalytics();
      void loadDepartments();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, filters]);

  const loadAnalytics = async () => {
    if (!token) return;
    try {
      const queryParams: Record<string, string> = {};
      // Передаем departmentCode только если он не пустой
      if (filters.departmentCode && filters.departmentCode.trim() !== '') {
        queryParams.departmentCode = filters.departmentCode.trim();
      }
      if (filters.search && filters.search.trim() !== '') {
        queryParams.search = filters.search.trim();
      }

      const queryString = new URLSearchParams(queryParams).toString();
      const url = `/admin/executors/analytics${queryString ? `?${queryString}` : ''}`;
      const data = await apiFetch<ExecutorAnalytics[]>(url, {}, token);
      setAnalytics(data);
    } catch (error: any) {
      setMessage(`Ошибка загрузки: ${error.message}`);
    }
  };

  const loadDepartments = async () => {
    if (!token) return;
    try {
      const data = await apiFetch<Department[]>('/admin/departments', {}, token);
      setDepartments(data);
    } catch (error) {
      console.error('Failed to load departments:', error);
    }
  };

  const handleCreateExecutor = async (e: FormEvent) => {
    e.preventDefault();
    if (!token) {
      setMessage('Нужна авторизация');
      return;
    }
    try {
      await apiFetch(
        '/admin/executors',
        {
          method: 'POST',
          data: {
            email: createForm.email,
            password: createForm.password,
            fullName: createForm.fullName,
            phone: createForm.phone || null,
            departmentCode: createForm.departmentCode || null,
            experienceYears: createForm.experienceYears ? Number(createForm.experienceYears) : null,
            isAdmin: createForm.isAdmin || undefined,
          },
        },
        token,
      );
      setMessage('Исполнитель создан');
      setCreateForm({
        email: '',
        password: '',
        fullName: '',
        phone: '',
        departmentCode: '',
        experienceYears: '',
        isAdmin: false,
      });
      setShowCreateForm(false);
      await loadAnalytics();
    } catch (error: any) {
      setMessage(`Ошибка: ${error.message}`);
    }
  };

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return '—';
    try {
      return new Date(dateString).toLocaleString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateString;
    }
  };

  return (
    <div className="space-y-4">
      <div className={cardClass}>
        <div className="flex items-center justify-between">
          <h3 className={sectionTitleClass}>Аналитика загрузки исполнителей</h3>
          <div className="flex gap-2">
            <button
              className={subtleButtonClass}
              onClick={() => {
                setShowCreateForm(!showCreateForm);
              }}
            >
              {showCreateForm ? 'Скрыть форму' : 'Создать исполнителя'}
            </button>
            <button className={subtleButtonClass} onClick={() => void loadAnalytics()}>
              Обновить
            </button>
          </div>
        </div>
        {message && (
          <div
            className={`mt-2 rounded p-2 text-sm ${
              message.includes('Ошибка') ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'
            }`}
          >
            {message}
          </div>
        )}

        {/* Фильтры */}
        <div className="mt-4 grid gap-3 rounded border border-slate-200 bg-slate-50 p-3 lg:grid-cols-2">
          <label className="text-sm text-slate-700">
            Поиск по ФИО или email:
            <input
              className={`${inputClass} mt-1`}
              type="text"
              value={filters.search}
              onChange={(e) => setFilters((f) => ({ ...f, search: e.target.value }))}
              placeholder="Введите имя или email..."
            />
          </label>
          <label className="text-sm text-slate-700">
            Фильтр по отделу:
            <select
              className={`${inputClass} mt-1`}
              value={filters.departmentCode}
              onChange={(e) => setFilters((f) => ({ ...f, departmentCode: e.target.value }))}
            >
              <option value="">Все отделы</option>
              {departments.map((d) => (
                <option key={d.code} value={d.code}>
                  {d.name || d.code}
                </option>
              ))}
            </select>
          </label>
        </div>

        {/* Форма создания */}
        {showCreateForm && (
          <div className="mt-4 rounded border border-blue-200 bg-blue-50 p-4">
            <h4 className="mb-3 font-semibold text-blue-900">Создание исполнителя</h4>
            <form className="grid gap-3 lg:grid-cols-3" onSubmit={handleCreateExecutor}>
              <label className="text-sm text-slate-700">
                Email
                <input
                  className={`${inputClass} mt-1`}
                  type="email"
                  value={createForm.email}
                  onChange={(e) => setCreateForm((f) => ({ ...f, email: e.target.value }))}
                  required
                />
              </label>
              <label className="text-sm text-slate-700">
                Пароль
                <input
                  className={`${inputClass} mt-1`}
                  type="password"
                  value={createForm.password}
                  onChange={(e) => setCreateForm((f) => ({ ...f, password: e.target.value }))}
                  required
                />
              </label>
              <label className="text-sm text-slate-700">
                ФИО
                <input
                  className={`${inputClass} mt-1`}
                  value={createForm.fullName}
                  onChange={(e) => setCreateForm((f) => ({ ...f, fullName: e.target.value }))}
                  required
                />
              </label>
              <label className="text-sm text-slate-700">
                Телефон
                <input
                  className={`${inputClass} mt-1`}
                  value={createForm.phone}
                  onChange={(e) => setCreateForm((f) => ({ ...f, phone: e.target.value }))}
                />
              </label>
              <label className="text-sm text-slate-700">
                Отдел
                <select
                  className={`${inputClass} mt-1`}
                  value={createForm.departmentCode}
                  onChange={(e) => setCreateForm((f) => ({ ...f, departmentCode: e.target.value }))}
                >
                  <option value="">Выберите отдел</option>
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
                  type="number"
                  value={createForm.experienceYears}
                  onChange={(e) => setCreateForm((f) => ({ ...f, experienceYears: e.target.value }))}
                />
              </label>
              <label className="mt-6 inline-flex items-center gap-2 text-sm font-medium text-slate-700">
                <input
                  type="checkbox"
                  checked={createForm.isAdmin}
                  onChange={(e) => setCreateForm((f) => ({ ...f, isAdmin: e.target.checked }))}
                />
                Сделать админом
              </label>
              <button type="submit" className={buttonClass}>
                Создать
              </button>
            </form>
          </div>
        )}

        {/* Таблица исполнителей */}
        <div className="mt-4 overflow-auto rounded border border-slate-200">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-100 text-left">
              <tr>
                <th className="px-4 py-3 font-semibold">ФИО</th>
                <th className="px-4 py-3 font-semibold">Email</th>
                <th className="px-4 py-3 font-semibold">Отдел</th>
                <th className="px-4 py-3 font-semibold text-center">Нагрузка</th>
                <th className="px-4 py-3 font-semibold">Последняя активность</th>
                <th className="px-4 py-3 font-semibold text-center">Ср. время выполнения</th>
                <th className="px-4 py-3 font-semibold text-center">Ошибки/отказы</th>
                <th className="px-4 py-3 font-semibold text-center">Выполнено</th>
                <th className="px-4 py-3 font-semibold text-center">Всего назначено</th>
              </tr>
            </thead>
            <tbody>
              {analytics.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-4 py-8 text-center text-slate-500">
                    Исполнители не найдены
                  </td>
                </tr>
              ) : (
                analytics.map((exec) => (
                  <tr key={exec.executorId} className="border-t border-slate-200 hover:bg-slate-50">
                    <td className="px-4 py-3 font-medium">{exec.fullName}</td>
                    <td className="px-4 py-3 text-slate-600">{exec.email}</td>
                    <td className="px-4 py-3">
                      <span className="rounded bg-slate-100 px-2 py-1 text-xs">
                        {exec.departmentCode || '—'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span
                        className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
                          exec.currentLoad === 0
                            ? 'bg-green-100 text-green-700'
                            : exec.currentLoad <= 3
                              ? 'bg-blue-100 text-blue-700'
                              : exec.currentLoad <= 5
                                ? 'bg-yellow-100 text-yellow-700'
                                : 'bg-red-100 text-red-700'
                        }`}
                      >
                        {exec.currentLoad}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-600">
                      {formatDate(exec.lastActivity)}
                    </td>
                    <td className="px-4 py-3 text-center text-slate-600">
                      {exec.avgCompletionDays !== null && exec.avgCompletionDays !== undefined
                        ? `${exec.avgCompletionDays} дн.`
                        : '—'}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span
                        className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
                          exec.errorsRejections === 0
                            ? 'bg-green-100 text-green-700'
                            : exec.errorsRejections <= 2
                              ? 'bg-yellow-100 text-yellow-700'
                              : 'bg-red-100 text-red-700'
                        }`}
                      >
                        {exec.errorsRejections}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center text-slate-600">{exec.totalCompleted}</td>
                    <td className="px-4 py-3 text-center text-slate-600">{exec.totalAssigned}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AdminExecutorsPage;
