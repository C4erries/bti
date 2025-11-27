import { useState, type FormEvent } from 'react';
import { apiFetch } from '../api/client';
import { useAuth } from '../context/AuthContext';
import {
  buttonClass,
  cardClass,
  inputClass,
  sectionTitleClass,
  subtleButtonClass,
  textareaClass,
} from '../components/ui';
import type { Order, User } from '../types';

export const AdminSection = () => {
  const { token, user } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [userEdit, setUserEdit] = useState({ fullName: '', phone: '', isAdmin: false });
  const [orders, setOrders] = useState<Order[]>([]);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [orderEdit, setOrderEdit] = useState({
    status: '',
    currentDepartmentCode: '',
    estimatedPrice: '',
    totalPrice: '',
  });
  const [assignExecutorId, setAssignExecutorId] = useState('');
  const [scheduleForm, setScheduleForm] = useState({
    executorId: '',
    startTime: '',
    endTime: '',
    location: '',
    status: '',
  });
  const [newExecutor, setNewExecutor] = useState({
    email: '',
    password: '',
    fullName: '',
    phone: '',
    departmentCode: '',
    experienceYears: '',
    isAdmin: false,
  });
  const [catalogForm, setCatalogForm] = useState({
    serviceCode: '',
    serviceTitle: '',
    districtCode: '',
    districtName: '',
    houseTypeCode: '',
    houseTypeName: '',
  });
  const [message, setMessage] = useState<string | null>(null);

  if (!token) {
    return (
      <div className={cardClass}>
        <h3 className={sectionTitleClass}>Админ</h3>
        <p className="text-sm text-slate-600">Нужна авторизация администратора.</p>
      </div>
    );
  }

  const loadUsers = async () => {
    const data = await apiFetch<User[]>('/admin/users', {}, token);
    setUsers(data);
  };

  const loadUserDetails = async (id: string) => {
    const data = await apiFetch<User>(`/admin/users/${id}`, {}, token);
    setSelectedUser(data);
    setUserEdit({
      fullName: data.fullName,
      phone: data.phone || '',
      isAdmin: data.isAdmin,
    });
  };

  const updateUser = async (e: FormEvent) => {
    e.preventDefault();
    if (!selectedUser) return;
    await apiFetch<User>(
      `/admin/users/${selectedUser.id}`,
      {
        method: 'PATCH',
        data: {
          fullName: userEdit.fullName || undefined,
          phone: userEdit.phone || undefined,
          isAdmin: userEdit.isAdmin,
        },
      },
      token,
    );
    setMessage('Пользователь обновлен');
    await loadUserDetails(selectedUser.id);
  };

  const createExecutor = async (e: FormEvent) => {
    e.preventDefault();
    await apiFetch('/admin/executors', {
      method: 'POST',
      data: {
        email: newExecutor.email,
        password: newExecutor.password,
        fullName: newExecutor.fullName,
        phone: newExecutor.phone || null,
        departmentCode: newExecutor.departmentCode || null,
        experienceYears: newExecutor.experienceYears
          ? Number(newExecutor.experienceYears)
          : null,
        isAdmin: newExecutor.isAdmin || undefined,
      },
    }, token);
    setMessage('Исполнитель создан');
  };

  const loadOrders = async () => {
    const data = await apiFetch<Order[]>('/admin/orders', {}, token);
    setOrders(data);
  };

  const loadOrderDetails = async (id: string) => {
    const data = await apiFetch<Order>(`/admin/orders/${id}`, {}, token);
    setSelectedOrder(data);
    setOrderEdit({
      status: data.status || '',
      currentDepartmentCode: data.currentDepartmentCode || '',
      estimatedPrice: data.estimatedPrice?.toString() || '',
      totalPrice: data.totalPrice?.toString() || '',
    });
  };

  const updateOrder = async (e: FormEvent) => {
    e.preventDefault();
    if (!selectedOrder) return;
    await apiFetch(
      `/admin/orders/${selectedOrder.id}`,
      {
        method: 'PATCH',
        data: {
          status: orderEdit.status || undefined,
          currentDepartmentCode: orderEdit.currentDepartmentCode || undefined,
          estimatedPrice: orderEdit.estimatedPrice ? Number(orderEdit.estimatedPrice) : undefined,
          totalPrice: orderEdit.totalPrice ? Number(orderEdit.totalPrice) : undefined,
        },
      },
      token,
    );
    setMessage('Заказ обновлен');
    await loadOrderDetails(selectedOrder.id);
  };

  const assignExecutor = async (e: FormEvent) => {
    e.preventDefault();
    if (!selectedOrder || !assignExecutorId) return;
    await apiFetch(
      `/admin/orders/${selectedOrder.id}/assign-executor`,
      { method: 'POST', data: { executorId: assignExecutorId } },
      token,
    );
    setMessage('Исполнитель назначен');
  };

  const scheduleVisit = async (e: FormEvent, mode: 'create' | 'update') => {
    e.preventDefault();
    if (!selectedOrder) return;
    const payload =
      mode === 'create'
        ? {
            executorId: scheduleForm.executorId,
            startTime: scheduleForm.startTime,
            endTime: scheduleForm.endTime,
            location: scheduleForm.location,
          }
        : {
            executorId: scheduleForm.executorId || undefined,
            startTime: scheduleForm.startTime || undefined,
            endTime: scheduleForm.endTime || undefined,
            status: scheduleForm.status || undefined,
          };
    await apiFetch(
      `/admin/orders/${selectedOrder.id}/schedule-visit`,
      { method: mode === 'create' ? 'POST' : 'PATCH', data: payload },
      token,
    );
    setMessage('Визит обновлен');
  };

  const createCatalogItems = async (e: FormEvent) => {
    e.preventDefault();
    await Promise.allSettled([
      catalogForm.serviceCode && catalogForm.serviceTitle
        ? apiFetch('/admin/services', {
            method: 'POST',
            data: {
              code: Number(catalogForm.serviceCode),
              title: catalogForm.serviceTitle,
            },
          }, token)
        : Promise.resolve(null),
      catalogForm.districtCode && catalogForm.districtName
        ? apiFetch('/admin/districts', {
            method: 'POST',
            data: { code: catalogForm.districtCode, name: catalogForm.districtName },
          }, token)
        : Promise.resolve(null),
      catalogForm.houseTypeCode && catalogForm.houseTypeName
        ? apiFetch('/admin/house-types', {
            method: 'POST',
            data: { code: catalogForm.houseTypeCode, name: catalogForm.houseTypeName },
          }, token)
        : Promise.resolve(null),
    ]);
    setMessage('Справочники обновлены (если эндпоинты доступны)');
  };

  return (
    <div className="space-y-4">
      {user?.isAdmin === false && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
          Роль администратора не подтверждена, возможны ошибки доступа.
        </div>
      )}

      <div className={cardClass}>
        <div className="flex items-center justify-between">
          <h3 className={sectionTitleClass}>Пользователи</h3>
          <button className={subtleButtonClass} onClick={() => void loadUsers()}>
            Обновить
          </button>
        </div>
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
                  onClick={() => void loadUserDetails(u.id)}
                >
                  <td className="px-3 py-2">{u.email}</td>
                  <td className="px-3 py-2">{u.fullName}</td>
                  <td className="px-3 py-2">{u.isAdmin ? 'Да' : 'Нет'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {selectedUser && (
          <form className="mt-3 grid gap-3 lg:grid-cols-3" onSubmit={updateUser}>
            <label className="text-sm text-slate-700">
              Имя
              <input
                className={`${inputClass} mt-1`}
                value={userEdit.fullName}
                onChange={(e) => setUserEdit((p) => ({ ...p, fullName: e.target.value }))}
              />
            </label>
            <label className="text-sm text-slate-700">
              Телефон
              <input
                className={`${inputClass} mt-1`}
                value={userEdit.phone}
                onChange={(e) => setUserEdit((p) => ({ ...p, phone: e.target.value }))}
              />
            </label>
            <label className="mt-6 inline-flex items-center gap-2 text-sm font-medium text-slate-700">
              <input
                type="checkbox"
                checked={userEdit.isAdmin}
                onChange={(e) => setUserEdit((p) => ({ ...p, isAdmin: e.target.checked }))}
              />
              Админ
            </label>
            <button type="submit" className={buttonClass}>
              Сохранить пользователя
            </button>
          </form>
        )}
      </div>

      <div className={cardClass}>
        <h3 className={sectionTitleClass}>Создать исполнителя</h3>
        <form className="mt-3 grid gap-3 lg:grid-cols-3" onSubmit={createExecutor}>
          <label className="text-sm text-slate-700">
            Email
            <input
              className={`${inputClass} mt-1`}
              value={newExecutor.email}
              onChange={(e) => setNewExecutor((p) => ({ ...p, email: e.target.value }))}
              required
            />
          </label>
          <label className="text-sm text-slate-700">
            Пароль
            <input
              className={`${inputClass} mt-1`}
              value={newExecutor.password}
              onChange={(e) => setNewExecutor((p) => ({ ...p, password: e.target.value }))}
              required
            />
          </label>
          <label className="text-sm text-slate-700">
            ФИО
            <input
              className={`${inputClass} mt-1`}
              value={newExecutor.fullName}
              onChange={(e) => setNewExecutor((p) => ({ ...p, fullName: e.target.value }))}
              required
            />
          </label>
          <label className="text-sm text-slate-700">
            Телефон
            <input
              className={`${inputClass} mt-1`}
              value={newExecutor.phone}
              onChange={(e) => setNewExecutor((p) => ({ ...p, phone: e.target.value }))}
            />
          </label>
          <label className="text-sm text-slate-700">
            Отдел
            <input
              className={`${inputClass} mt-1`}
              value={newExecutor.departmentCode}
              onChange={(e) => setNewExecutor((p) => ({ ...p, departmentCode: e.target.value }))}
              placeholder="LEGAL / MASTERS"
            />
          </label>
          <label className="text-sm text-slate-700">
            Стаж (лет)
            <input
              className={`${inputClass} mt-1`}
              value={newExecutor.experienceYears}
              onChange={(e) =>
                setNewExecutor((p) => ({ ...p, experienceYears: e.target.value }))
              }
            />
          </label>
          <label className="mt-6 inline-flex items-center gap-2 text-sm font-medium text-slate-700">
            <input
              type="checkbox"
              checked={newExecutor.isAdmin}
              onChange={(e) => setNewExecutor((p) => ({ ...p, isAdmin: e.target.checked }))}
            />
            Сделать админом
          </label>
          <button type="submit" className={buttonClass}>
            Создать
          </button>
        </form>
      </div>

      <div className={cardClass}>
        <div className="flex items-center justify-between">
          <h3 className={sectionTitleClass}>Заказы (админ)</h3>
          <button className={subtleButtonClass} onClick={() => void loadOrders()}>
            Обновить
          </button>
        </div>
        <div className="mt-3 overflow-auto rounded border">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-100 text-left">
              <tr>
                <th className="px-3 py-2">ID</th>
                <th className="px-3 py-2">Статус</th>
                <th className="px-3 py-2">Сервис</th>
                <th className="px-3 py-2">Цена</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr
                  key={o.id}
                  className="cursor-pointer hover:bg-slate-50"
                  onClick={() => void loadOrderDetails(o.id)}
                >
                  <td className="px-3 py-2 font-mono">{o.id.slice(0, 8)}…</td>
                  <td className="px-3 py-2">{o.status}</td>
                  <td className="px-3 py-2">{o.serviceCode}</td>
                  <td className="px-3 py-2">{o.totalPrice ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {selectedOrder && (
          <div className="mt-4 grid gap-3 lg:grid-cols-2">
            <div className="space-y-3">
              <div className="rounded border border-slate-200 bg-slate-50 p-3">
                <p className="font-semibold">Детали заказа</p>
                <pre className="mt-2 whitespace-pre-wrap text-xs">
                  {JSON.stringify(selectedOrder, null, 2)}
                </pre>
              </div>
              <form className="grid gap-3 lg:grid-cols-2" onSubmit={updateOrder}>
                <label className="text-sm text-slate-700">
                  Статус
                  <input
                    className={`${inputClass} mt-1`}
                    value={orderEdit.status}
                    onChange={(e) => setOrderEdit((p) => ({ ...p, status: e.target.value }))}
                  />
                </label>
                <label className="text-sm text-slate-700">
                  Отдел
                  <input
                    className={`${inputClass} mt-1`}
                    value={orderEdit.currentDepartmentCode}
                    onChange={(e) =>
                      setOrderEdit((p) => ({ ...p, currentDepartmentCode: e.target.value }))
                    }
                  />
                </label>
                <label className="text-sm text-slate-700">
                  Оценка цены
                  <input
                    className={`${inputClass} mt-1`}
                    value={orderEdit.estimatedPrice}
                    onChange={(e) =>
                      setOrderEdit((p) => ({ ...p, estimatedPrice: e.target.value }))
                    }
                  />
                </label>
                <label className="text-sm text-slate-700">
                  Итоговая цена
                  <input
                    className={`${inputClass} mt-1`}
                    value={orderEdit.totalPrice}
                    onChange={(e) =>
                      setOrderEdit((p) => ({ ...p, totalPrice: e.target.value }))
                    }
                  />
                </label>
                <button type="submit" className={buttonClass}>
                  Сохранить заказ
                </button>
              </form>
            </div>
            <div className="space-y-3">
              <form className="rounded border border-slate-200 p-3" onSubmit={assignExecutor}>
                <p className="font-semibold">Назначить исполнителя</p>
                <div className="mt-2 flex items-center gap-2">
                  <input
                    className={inputClass}
                    value={assignExecutorId}
                    onChange={(e) => setAssignExecutorId(e.target.value)}
                    placeholder="executorId (UUID)"
                    required
                  />
                  <button type="submit" className={subtleButtonClass}>
                    Назначить
                  </button>
                </div>
              </form>
              <form
                className="rounded border border-slate-200 p-3"
                onSubmit={(e) => void scheduleVisit(e, 'create')}
              >
                <p className="font-semibold">Запланировать визит (POST)</p>
                <div className="mt-2 grid gap-2">
                  <input
                    className={inputClass}
                    value={scheduleForm.executorId}
                    onChange={(e) => setScheduleForm((p) => ({ ...p, executorId: e.target.value }))}
                    placeholder="executorId"
                    required
                  />
                  <input
                    className={inputClass}
                    value={scheduleForm.startTime}
                    onChange={(e) => setScheduleForm((p) => ({ ...p, startTime: e.target.value }))}
                    placeholder="startTime ISO"
                    required
                  />
                  <input
                    className={inputClass}
                    value={scheduleForm.endTime}
                    onChange={(e) => setScheduleForm((p) => ({ ...p, endTime: e.target.value }))}
                    placeholder="endTime ISO"
                    required
                  />
                  <textarea
                    className={textareaClass}
                    rows={2}
                    value={scheduleForm.location}
                    onChange={(e) =>
                      setScheduleForm((p) => ({ ...p, location: e.target.value }))
                    }
                    placeholder="Адрес"
                    required
                  />
                  <button type="submit" className={subtleButtonClass}>
                    Отправить POST
                  </button>
                </div>
              </form>
              <form
                className="rounded border border-slate-200 p-3"
                onSubmit={(e) => void scheduleVisit(e, 'update')}
              >
                <p className="font-semibold">Обновить визит (PATCH)</p>
                <div className="mt-2 grid gap-2">
                  <input
                    className={inputClass}
                    value={scheduleForm.status}
                    onChange={(e) => setScheduleForm((p) => ({ ...p, status: e.target.value }))}
                    placeholder="Новый статус"
                  />
                  <button type="submit" className={subtleButtonClass}>
                    Отправить PATCH
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>

      <div className={cardClass}>
        <h3 className={sectionTitleClass}>Справочники (admin)</h3>
        <p className="text-sm text-slate-600">
          Пробные формы для /admin/services, /admin/districts, /admin/house-types.
        </p>
        <form className="mt-3 grid gap-3 lg:grid-cols-3" onSubmit={createCatalogItems}>
          <label className="text-sm text-slate-700">
            Service code
            <input
              className={`${inputClass} mt-1`}
              value={catalogForm.serviceCode}
              onChange={(e) => setCatalogForm((p) => ({ ...p, serviceCode: e.target.value }))}
              placeholder="число"
            />
          </label>
          <label className="text-sm text-slate-700">
            Service title
            <input
              className={`${inputClass} mt-1`}
              value={catalogForm.serviceTitle}
              onChange={(e) => setCatalogForm((p) => ({ ...p, serviceTitle: e.target.value }))}
            />
          </label>
          <label className="text-sm text-slate-700">
            District (code/name)
            <input
              className={`${inputClass} mt-1`}
              value={catalogForm.districtCode}
              onChange={(e) => setCatalogForm((p) => ({ ...p, districtCode: e.target.value }))}
              placeholder="code"
            />
            <input
              className={`${inputClass} mt-2`}
              value={catalogForm.districtName}
              onChange={(e) => setCatalogForm((p) => ({ ...p, districtName: e.target.value }))}
              placeholder="name"
            />
          </label>
          <label className="text-sm text-slate-700">
            House type (code/name)
            <input
              className={`${inputClass} mt-1`}
              value={catalogForm.houseTypeCode}
              onChange={(e) => setCatalogForm((p) => ({ ...p, houseTypeCode: e.target.value }))}
              placeholder="code"
            />
            <input
              className={`${inputClass} mt-2`}
              value={catalogForm.houseTypeName}
              onChange={(e) => setCatalogForm((p) => ({ ...p, houseTypeName: e.target.value }))}
              placeholder="name"
            />
          </label>
          <button type="submit" className={buttonClass}>
            Отправить запросы
          </button>
        </form>
      </div>

      {message && (
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm">
          {message}
        </div>
      )}
    </div>
  );
};
