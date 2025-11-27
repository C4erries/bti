import { useEffect, useMemo, useState } from 'react';
import { apiFetch } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { badgeClass, cardClass, sectionTitleClass, subtleButtonClass } from '../../components/ui';
import type { ExecutorCalendarEvent } from '../../types';

const daysInMonth = (date: Date) => {
  const start = new Date(date.getFullYear(), date.getMonth(), 1);
  const days: Date[] = [];
  while (start.getMonth() === date.getMonth()) {
    days.push(new Date(start));
    start.setDate(start.getDate() + 1);
  }
  return days;
};

const formatDateKey = (date: Date) => date.toISOString().split('T')[0];

const ExecutorCalendarPage = () => {
  const { token } = useAuth();
  const [events, setEvents] = useState<ExecutorCalendarEvent[]>([]);
  const [currentMonth, setCurrentMonth] = useState(() => new Date());
  const [selectedDay, setSelectedDay] = useState<string | null>(null);

  useEffect(() => {
    if (token) void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const load = async () => {
    if (!token) return;
    const data = await apiFetch<ExecutorCalendarEvent[]>('/executor/calendar', {}, token);
    setEvents(data);
  };

  const days = useMemo(() => daysInMonth(currentMonth), [currentMonth]);

  const eventsByDay = useMemo(() => {
    const map: Record<string, ExecutorCalendarEvent[]> = {};
    events.forEach((ev) => {
      const key = formatDateKey(new Date(ev.startTime));
      map[key] = map[key] || [];
      map[key].push(ev);
    });
    return map;
  }, [events]);

  const visibleEvents = selectedDay ? eventsByDay[selectedDay] || [] : events;

  const monthLabel = currentMonth.toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' });

  return (
    <div className="grid gap-4 lg:grid-cols-[360px_1fr]">
      <div className={cardClass}>
        <div className="flex items-center justify-between">
          <h3 className={sectionTitleClass}>Список выездов</h3>
          <div className="flex gap-2">
            <button className={subtleButtonClass} onClick={() => void load()}>
              Обновить
            </button>
            {selectedDay && (
              <button className={subtleButtonClass} onClick={() => setSelectedDay(null)}>
                Сброс фильтра
              </button>
            )}
          </div>
        </div>
        <div className="mt-3 space-y-2 text-sm">
          {visibleEvents.length === 0 && <p className="text-slate-600">Нет событий</p>}
          {visibleEvents.map((e, idx) => (
            <div key={e.id} className="rounded border border-slate-200 p-2">
              <div className="flex items-center justify-between">
                <span className="font-semibold">Выезд #{idx + 1}</span>
                {e.status && <span className={badgeClass}>{e.status}</span>}
              </div>
              <p className="text-xs text-slate-500">
                {new Date(e.startTime).toLocaleString()} — {new Date(e.endTime).toLocaleString()}
              </p>
              <p>Адрес: {e.location || '—'}</p>
              <p className="text-slate-600 text-xs">Заказ: {e.orderId || '—'}</p>
              {e.description && <p className="text-xs text-slate-700"> {e.description}</p>}
            </div>
          ))}
        </div>
      </div>

      <div className={cardClass}>
        <div className="flex items-center justify-between">
          <h3 className={sectionTitleClass}>Календарь заказов</h3>
          <div className="flex gap-2">
            <button
              className={subtleButtonClass}
              onClick={() =>
                setCurrentMonth(
                  (d) => new Date(d.getFullYear(), d.getMonth() - 1, 1),
                )
              }
            >
              ←
            </button>
            <span className="text-sm font-medium text-slate-800">{monthLabel}</span>
            <button
              className={subtleButtonClass}
              onClick={() =>
                setCurrentMonth(
                  (d) => new Date(d.getFullYear(), d.getMonth() + 1, 1),
                )
              }
            >
              →
            </button>
          </div>
        </div>
        <div className="mt-3 grid grid-cols-7 gap-2 text-sm">
          {days.map((day) => {
            const key = formatDateKey(day);
            const hasEvents = Boolean(eventsByDay[key]?.length);
            const isSelected = selectedDay === key;
            return (
              <button
                key={key}
                className={`h-16 rounded-lg border text-left p-2 ${
                  isSelected ? 'border-blue-500 bg-blue-50' : 'border-slate-200'
                } ${hasEvents ? 'shadow-inner' : ''}`}
                onClick={() => setSelectedDay(key)}
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold">{day.getDate()}</span>
                  {hasEvents && <span className={badgeClass}>{eventsByDay[key].length}</span>}
                </div>
                <div className="mt-1 text-xs text-slate-600">
                  {hasEvents ? 'Есть выезды' : ''}
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default ExecutorCalendarPage;
