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
import type { User } from '../../types';

const AdminUsersPage = () => {
  const { token } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [selected, setSelected] = useState<User | null>(null);
  const [edit, setEdit] = useState({ fullName: '', phone: '', isAdmin: false });
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (token) void loadUsers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const loadUsers = async () => {
    if (!token) return;
    const data = await apiFetch<User[]>('/admin/users', {}, token);
    setUsers(data);
  };

  const selectUser = async (id: string) => {
    if (!token) return;
    const data = await apiFetch<User>(`/admin/users/${id}`, {}, token);
    setSelected(data);
    setEdit({
      fullName: data.fullName,
      phone: data.phone || '',
      isAdmin: data.isAdmin,
    });
  };

  const saveUser = async (e: FormEvent) => {
    e.preventDefault();
    if (!token || !selected) return;
    await apiFetch<User>(
      `/admin/users/${selected.id}`,
      {
        method: 'PATCH',
        data: { fullName: edit.fullName, phone: edit.phone || undefined, isAdmin: edit.isAdmin },
      },
      token,
    );
    setMessage('Пользователь обновлен');
    await selectUser(selected.id);
  };

  return (
    <div className={cardClass}>
      <div className="flex items-center justify-between">
        <h3 className={sectionTitleClass}>Пользователи</h3>
        <button className={subtleButtonClass} onClick={() => void loadUsers()}>
          Обновить
        </button>
      </div>
      {message && <p className="mt-2 text-sm text-slate-700">{message}</p>}
      <div className="mt-3 overflow-auto rounded border">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-100 text-left">
            <tr>
              <th className="px-3 py-2">Email</th>
              <th className="px-3 py-2">Имя</th>
              <th className="px-3 py-2">Admin</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr
                key={u.id}
                className="cursor-pointer hover:bg-slate-50"
                onClick={() => void selectUser(u.id)}
              >
                <td className="px-3 py-2">{u.email}</td>
                <td className="px-3 py-2">{u.fullName}</td>
                <td className="px-3 py-2">{u.isAdmin ? 'Да' : 'Нет'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {selected && (
        <form className="mt-4 grid gap-3 lg:grid-cols-3" onSubmit={saveUser}>
          <label className="text-sm text-slate-700">
            Имя
            <input
              className={`${inputClass} mt-1`}
              value={edit.fullName}
              onChange={(e) => setEdit((p) => ({ ...p, fullName: e.target.value }))}
            />
          </label>
          <label className="text-sm text-slate-700">
            Телефон
            <input
              className={`${inputClass} mt-1`}
              value={edit.phone}
              onChange={(e) => setEdit((p) => ({ ...p, phone: e.target.value }))}
            />
          </label>
          <label className="mt-6 inline-flex items-center gap-2 text-sm font-medium text-slate-700">
            <input
              type="checkbox"
              checked={edit.isAdmin}
              onChange={(e) => setEdit((p) => ({ ...p, isAdmin: e.target.checked }))}
            />
            Админ
          </label>
          <button type="submit" className={buttonClass}>
            Сохранить
          </button>
        </form>
      )}
    </div>
  );
};

export default AdminUsersPage;
