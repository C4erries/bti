import { useEffect, useState } from 'react';
import { apiFetch } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { cardClass, sectionTitleClass, subtleButtonClass } from '../../components/ui';
import type { ExecutorCalendarEvent } from '../../types';

const ExecutorCalendarPage = () => {
  const { token } = useAuth();
  const [events, setEvents] = useState<ExecutorCalendarEvent[]>([]);

  useEffect(() => {
    if (token) void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const load = async () => {
    if (!token) return;
    const data = await apiFetch<ExecutorCalendarEvent[]>('/executor/calendar', {}, token);
    setEvents(data);
  };

  return (
    <div className={cardClass}>
      <div className="flex items-center justify-between">
        <h3 className={sectionTitleClass}>Календарь исполнителя</h3>
        <button className={subtleButtonClass} onClick={() => void load()}>
          Обновить
        </button>
      </div>
      <div className="mt-3 overflow-auto rounded border">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-100 text-left">
            <tr>
              <th className="px-3 py-2">Начало</th>
              <th className="px-3 py-2">Конец</th>
              <th className="px-3 py-2">Локация</th>
              <th className="px-3 py-2">Статус</th>
              <th className="px-3 py-2">Заказ</th>
            </tr>
          </thead>
          <tbody>
            {events.map((e) => (
              <tr key={e.id} className="hover:bg-slate-50">
                <td className="px-3 py-2">{new Date(e.startTime).toLocaleString()}</td>
                <td className="px-3 py-2">{new Date(e.endTime).toLocaleString()}</td>
                <td className="px-3 py-2">{e.location || '—'}</td>
                <td className="px-3 py-2">{e.status || '—'}</td>
                <td className="px-3 py-2">{e.orderId || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ExecutorCalendarPage;
