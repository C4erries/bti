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
import type {
  ExecutorCalendarEvent,
  ExecutorOrderDetails,
  ExecutorOrderListItem,
} from '../types';

export const ExecutorSection = () => {
  const { token, user } = useAuth();
  const [orders, setOrders] = useState<ExecutorOrderListItem[]>([]);
  const [filters, setFilters] = useState({ status: '', departmentCode: '' });
  const [selected, setSelected] = useState<ExecutorOrderDetails | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [calendar, setCalendar] = useState<ExecutorCalendarEvent[]>([]);
  const [slots, setSlots] = useState<any[] | null>(null);
  const [scheduleForm, setScheduleForm] = useState({
    executorId: '',
    startTime: '',
    endTime: '',
    location: '',
    status: '',
  });
  const [message, setMessage] = useState<string | null>(null);

  if (!token) {
    return (
      <div className={cardClass}>
        <h3 className={sectionTitleClass}>Исполнитель</h3>
        <p className="text-sm text-slate-600">Нужна авторизация исполнителя.</p>
      </div>
    );
  }

  const loadOrders = async () => {
    const data = await apiFetch<ExecutorOrderListItem[]>(
      '/executor/orders',
      { query: { status: filters.status || undefined, departmentCode: filters.departmentCode || undefined } },
      token,
    );
    setOrders(data);
  };

  const loadDetails = async (orderId: string) => {
    const data = await apiFetch<ExecutorOrderDetails>(`/executor/orders/${orderId}`, {}, token);
    setSelected(data);
    setSelectedId(orderId);
  };

  const handleTake = async () => {
    if (!selectedId) return;
    await apiFetch(`/executor/orders/${selectedId}/take`, { method: 'POST' }, token);
    await loadDetails(selectedId);
    setMessage('Заказ взят в работу');
  };

  const handleDecline = async () => {
    if (!selectedId) return;
    await apiFetch(`/executor/orders/${selectedId}/decline`, { method: 'POST' }, token);
    await loadDetails(selectedId);
    setMessage('Отказ отправлен');
  };

  const loadCalendar = async () => {
    const data = await apiFetch<ExecutorCalendarEvent[]>('/executor/calendar', {}, token);
    setCalendar(data);
  };

  const loadSlots = async () => {
    if (!selectedId) return;
    const data = await apiFetch<any[]>(`/executor/orders/${selectedId}/available-slots`, {}, token);
    setSlots(data);
  };

  const handleSchedule = async (e: FormEvent, mode: 'create' | 'update') => {
    e.preventDefault();
    if (!selectedId) return;
    const payload =
      mode === 'create'
        ? {
            executorId: scheduleForm.executorId || undefined,
            startTime: scheduleForm.startTime,
            endTime: scheduleForm.endTime,
            location: scheduleForm.location || null,
          }
        : {
            executorId: scheduleForm.executorId || undefined,
            startTime: scheduleForm.startTime || undefined,
            endTime: scheduleForm.endTime || undefined,
            status: scheduleForm.status || undefined,
            location: scheduleForm.location || undefined,
          };
    await apiFetch(
      `/executor/orders/${selectedId}/schedule-visit`,
      { method: mode === 'create' ? 'POST' : 'PATCH', data: payload },
      token,
    );
    setMessage('Данные визита отправлены');
    await loadDetails(selectedId);
  };

  return (
    <div className="space-y-4">
      {user?.isExecutor === false && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
          Пользователь не имеет роли исполнителя, методы могут вернуть 403.
        </div>
      )}

      <div className={cardClass}>
        <div className="flex items-center justify-between">
          <h3 className={sectionTitleClass}>Заказы исполнителя</h3>
          <button className={subtleButtonClass} onClick={() => void loadOrders()}>
            Загрузить
          </button>
        </div>
        <div className="mt-3 grid gap-3 lg:grid-cols-3">
          <label className="text-sm font-medium text-slate-700">
            Статус
            <input
              className={`${inputClass} mt-1`}
              value={filters.status}
              onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}
              placeholder="SUBMITTED / ..."
            />
          </label>
          <label className="text-sm font-medium text-slate-700">
            Код отдела
            <input
              className={`${inputClass} mt-1`}
              value={filters.departmentCode}
              onChange={(e) => setFilters((f) => ({ ...f, departmentCode: e.target.value }))}
              placeholder="LEGAL / MASTERS"
            />
          </label>
        </div>
        <div className="mt-3 overflow-auto rounded border">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-100 text-left">
              <tr>
                <th className="px-3 py-2">ID</th>
                <th className="px-3 py-2">Статус</th>
                <th className="px-3 py-2">Услуга</th>
                <th className="px-3 py-2">Стоимость</th>
                <th className="px-3 py-2">Создан</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr
                  key={o.id}
                  className="cursor-pointer hover:bg-slate-50"
                  onClick={() => void loadDetails(o.id)}
                >
                  <td className="px-3 py-2 font-mono">{o.id.slice(0, 8)}…</td>
                  <td className="px-3 py-2">{o.status}</td>
                  <td className="px-3 py-2">{o.serviceTitle}</td>
                  <td className="px-3 py-2">{o.totalPrice ?? '—'}</td>
                  <td className="px-3 py-2">{new Date(o.createdAt).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {selected && selectedId && (
        <div className="grid gap-4 lg:grid-cols-2">
          <div className={cardClass}>
            <div className="flex items-center justify-between">
              <h3 className={sectionTitleClass}>Детали заказа</h3>
              <div className="flex gap-2">
                <button className={buttonClass} onClick={() => void handleTake()}>
                  Взять в работу
                </button>
                <button className={subtleButtonClass} onClick={() => void handleDecline()}>
                  Отказаться
                </button>
              </div>
            </div>
            <pre className="mt-3 whitespace-pre-wrap text-xs">
              {JSON.stringify(selected.order ?? selected, null, 2)}
            </pre>
            {selected.client && (
              <div className="mt-3 rounded border border-slate-200 bg-slate-50 p-2 text-sm">
                <p className="font-semibold">Клиент</p>
                <p>{selected.client.fullName}</p>
                <p className="text-slate-600">{selected.client.email}</p>
              </div>
            )}
            {selected.statusHistory && selected.statusHistory.length > 0 && (
              <div className="mt-3 space-y-1 text-sm">
                <p className="font-semibold">Статусы</p>
                {selected.statusHistory.map((h, idx) => (
                  <div key={`${h.status}-${idx}`} className="rounded bg-slate-50 px-2 py-1">
                    <span className="font-mono text-xs text-slate-500">
                      {new Date(h.changedAt).toLocaleString()}
                    </span>{' '}
                    {h.status}
                  </div>
                ))}
              </div>
            )}
            {selected.files && selected.files.length > 0 && (
              <div className="mt-3 space-y-1 text-sm">
                <p className="font-semibold">Файлы</p>
                {selected.files.map((f) => (
                  <div key={f.id} className="flex items-center gap-2">
                    <span className="font-mono text-xs">{f.filename}</span>
                    <a className="text-blue-600" href={f.path} target="_blank" rel="noreferrer">
                      открыть
                    </a>
                  </div>
                ))}
              </div>
            )}
            {message && <p className="mt-3 text-sm text-slate-700">{message}</p>}
          </div>

          <div className="space-y-4">
            <div className={cardClass}>
              <div className="flex items-center justify-between">
                <h3 className={sectionTitleClass}>Календарь</h3>
                <button className={subtleButtonClass} onClick={() => void loadCalendar()}>
                  Обновить
                </button>
              </div>
              {calendar.length ? (
                <ul className="mt-2 space-y-1 text-sm">
                  {calendar.map((c) => (
                    <li key={c.id} className="rounded border border-slate-200 px-2 py-1">
                      <span className="font-semibold">{c.title || 'Событие'}</span> ·{' '}
                      {new Date(c.startTime).toLocaleString()} —{' '}
                      {new Date(c.endTime).toLocaleString()} · {c.location || '—'}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-slate-600">Нет событий</p>
              )}
            </div>

            <div className={cardClass}>
              <div className="flex items-center justify-between">
                <h3 className={sectionTitleClass}>Слоты / визит</h3>
                <button className={subtleButtonClass} onClick={() => void loadSlots()}>
                  Доступные слоты
                </button>
              </div>
              {slots && (
                <pre className="mt-2 whitespace-pre-wrap text-xs">
                  {JSON.stringify(slots, null, 2)}
                </pre>
              )}
              <form className="mt-3 space-y-2" onSubmit={(e) => void handleSchedule(e, 'create')}>
                <p className="text-sm font-semibold text-slate-800">Запланировать</p>
                <label className="text-sm text-slate-700">
                  Executor ID
                  <input
                    className={`${inputClass} mt-1`}
                    value={scheduleForm.executorId}
                    onChange={(e) =>
                      setScheduleForm((f) => ({ ...f, executorId: e.target.value }))
                    }
                    placeholder="UUID, опционально"
                  />
                </label>
                <label className="text-sm text-slate-700">
                  Start time (ISO)
                  <input
                    className={`${inputClass} mt-1`}
                    value={scheduleForm.startTime}
                    onChange={(e) =>
                      setScheduleForm((f) => ({ ...f, startTime: e.target.value }))
                    }
                    required
                  />
                </label>
                <label className="text-sm text-slate-700">
                  End time (ISO)
                  <input
                    className={`${inputClass} mt-1`}
                    value={scheduleForm.endTime}
                    onChange={(e) =>
                      setScheduleForm((f) => ({ ...f, endTime: e.target.value }))
                    }
                    required
                  />
                </label>
                <label className="text-sm text-slate-700">
                  Location / статус
                  <textarea
                    className={`${textareaClass} mt-1`}
                    rows={2}
                    value={scheduleForm.location}
                    onChange={(e) =>
                      setScheduleForm((f) => ({ ...f, location: e.target.value }))
                    }
                    placeholder="Адрес или комментарий"
                  />
                </label>
                <button type="submit" className={buttonClass}>
                  Отправить POST
                </button>
              </form>
              <form className="mt-3 space-y-2 border-t border-slate-200 pt-3" onSubmit={(e) => void handleSchedule(e, 'update')}>
                <p className="text-sm font-semibold text-slate-800">Изменить визит</p>
                <label className="text-sm text-slate-700">
                  Статус (опционально)
                  <input
                    className={`${inputClass} mt-1`}
                    value={scheduleForm.status}
                    onChange={(e) =>
                      setScheduleForm((f) => ({ ...f, status: e.target.value }))
                    }
                    placeholder="например, CANCELLED"
                  />
                </label>
                <button type="submit" className={subtleButtonClass}>
                  Отправить PATCH
                </button>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
