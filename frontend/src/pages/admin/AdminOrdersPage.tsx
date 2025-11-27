import { useEffect, useState, type FormEvent } from 'react';
import { apiFetch } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import {
  buttonClass,
  cardClass,
  inputClass,
  sectionTitleClass,
  subtleButtonClass,
  textareaClass,
} from '../../components/ui';
import type { Order } from '../../types';

const AdminOrdersPage = () => {
  const { token } = useAuth();
  const [orders, setOrders] = useState<Order[]>([]);
  const [selected, setSelected] = useState<Order | null>(null);
  const [edit, setEdit] = useState({
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
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (token) void loadOrders();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const loadOrders = async () => {
    if (!token) return;
    const data = await apiFetch<Order[]>('/admin/orders', {}, token);
    setOrders(data);
  };

  const loadOrder = async (id: string) => {
    if (!token) return;
    const data = await apiFetch<Order>(`/admin/orders/${id}`, {}, token);
    setSelected(data);
    setEdit({
      status: data.status || '',
      currentDepartmentCode: data.currentDepartmentCode || '',
      estimatedPrice: data.estimatedPrice?.toString() || '',
      totalPrice: data.totalPrice?.toString() || '',
    });
  };

  const saveOrder = async (e: FormEvent) => {
    e.preventDefault();
    if (!token || !selected) return;
    await apiFetch(
      `/admin/orders/${selected.id}`,
      {
        method: 'PATCH',
        data: {
          status: edit.status || undefined,
          currentDepartmentCode: edit.currentDepartmentCode || undefined,
          estimatedPrice: edit.estimatedPrice ? Number(edit.estimatedPrice) : undefined,
          totalPrice: edit.totalPrice ? Number(edit.totalPrice) : undefined,
        },
      },
      token,
    );
    setMessage('Заказ обновлен');
    await loadOrder(selected.id);
  };

  const assignExecutor = async (e: FormEvent) => {
    e.preventDefault();
    if (!token || !selected || !assignExecutorId) return;
    await apiFetch(
      `/admin/orders/${selected.id}/assign-executor`,
      { method: 'POST', data: { executorId: assignExecutorId } },
      token,
    );
    setMessage('Исполнитель назначен');
  };

  const scheduleVisit = async (e: FormEvent, mode: 'create' | 'update') => {
    e.preventDefault();
    if (!token || !selected) return;
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
      `/admin/orders/${selected.id}/schedule-visit`,
      { method: mode === 'create' ? 'POST' : 'PATCH', data: payload },
      token,
    );
    setMessage('Данные визита отправлены');
  };

  return (
    <div className="space-y-4">
      <div className={cardClass}>
        <div className="flex items-center justify-between">
          <h3 className={sectionTitleClass}>Все заказы</h3>
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
                <th className="px-3 py-2">Услуга</th>
                <th className="px-3 py-2">Цена</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr
                  key={o.id}
                  className="cursor-pointer hover:bg-slate-50"
                  onClick={() => void loadOrder(o.id)}
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
      </div>

      {selected && (
        <div className={cardClass}>
          <h4 className={sectionTitleClass}>Детали заказа</h4>
          <pre className="mt-2 whitespace-pre-wrap text-xs">
            {JSON.stringify(selected, null, 2)}
          </pre>
          <form className="mt-3 grid gap-3 lg:grid-cols-2" onSubmit={saveOrder}>
            <label className="text-sm text-slate-700">
              Статус
              <input
                className={`${inputClass} mt-1`}
                value={edit.status}
                onChange={(e) => setEdit((p) => ({ ...p, status: e.target.value }))}
              />
            </label>
            <label className="text-sm text-slate-700">
              Отдел
              <input
                className={`${inputClass} mt-1`}
                value={edit.currentDepartmentCode}
                onChange={(e) => setEdit((p) => ({ ...p, currentDepartmentCode: e.target.value }))}
              />
            </label>
            <label className="text-sm text-slate-700">
              Оценка цены
              <input
                className={`${inputClass} mt-1`}
                value={edit.estimatedPrice}
                onChange={(e) => setEdit((p) => ({ ...p, estimatedPrice: e.target.value }))}
              />
            </label>
            <label className="text-sm text-slate-700">
              Итоговая цена
              <input
                className={`${inputClass} mt-1`}
                value={edit.totalPrice}
                onChange={(e) => setEdit((p) => ({ ...p, totalPrice: e.target.value }))}
              />
            </label>
            <button type="submit" className={buttonClass}>
              Сохранить заказ
            </button>
          </form>

          <div className="mt-4 grid gap-3 lg:grid-cols-2">
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
            <div className="space-y-3 rounded border border-slate-200 p-3">
              <form onSubmit={(e) => void scheduleVisit(e, 'create')} className="space-y-2">
                <p className="font-semibold">Запланировать визит (POST)</p>
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
                  onChange={(e) => setScheduleForm((p) => ({ ...p, location: e.target.value }))}
                  placeholder="Адрес"
                  required
                />
                <button type="submit" className={subtleButtonClass}>
                  Отправить POST
                </button>
              </form>
              <form onSubmit={(e) => void scheduleVisit(e, 'update')} className="space-y-2 border-t border-slate-200 pt-3">
                <p className="font-semibold">Обновить визит (PATCH)</p>
                <input
                  className={inputClass}
                  value={scheduleForm.status}
                  onChange={(e) => setScheduleForm((p) => ({ ...p, status: e.target.value }))}
                  placeholder="Новый статус"
                />
                <button type="submit" className={subtleButtonClass}>
                  Отправить PATCH
                </button>
              </form>
            </div>
          </div>
        </div>
      )}
      {message && !selected && (
        <div className={cardClass}>
          <p className="text-sm text-slate-700">{message}</p>
        </div>
      )}
    </div>
  );
};

export default AdminOrdersPage;
