import { useState, type FormEvent } from 'react';
import { apiFetch } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { buttonClass, cardClass, inputClass, sectionTitleClass } from '../../components/ui';

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

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!token) {
      setMessage('Нужна авторизация');
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
  };

  return (
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
          <input
            className={`${inputClass} mt-1`}
            value={form.departmentCode}
            onChange={(e) => setForm((p) => ({ ...p, departmentCode: e.target.value }))}
            placeholder="LEGAL / MASTERS"
          />
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
          Сделать админом
        </label>
        <button type="submit" className={buttonClass}>
          Создать
        </button>
      </form>
    </div>
  );
};

export default AdminExecutorsPage;
