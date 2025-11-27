import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { apiFetch } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { badgeClass, buttonClass, cardClass, sectionTitleClass, subtleButtonClass } from '../../components/ui';
import type { ExecutorOrderDetails } from '../../types';

const ExecutorOrderDetailsPage = () => {
  const { orderId } = useParams();
  const { token } = useAuth();
  const [data, setData] = useState<ExecutorOrderDetails | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (token && orderId) void loadDetails();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orderId, token]);

  const loadDetails = async () => {
    if (!token || !orderId) return;
    const details = await apiFetch<ExecutorOrderDetails>(`/executor/orders/${orderId}`, {}, token);
    setData(details);
  };

  const handleAction = async (action: 'take' | 'decline') => {
    if (!token || !orderId) return;
    await apiFetch(`/executor/orders/${orderId}/${action}`, { method: 'POST' }, token);
    setMessage(action === 'take' ? 'Взято в работу' : 'Отказ отправлен');
    await loadDetails();
  };

  return (
    <div className={cardClass}>
      <div className="flex items-center justify-between">
        <h3 className={sectionTitleClass}>Заказ исполнителя</h3>
        <div className="flex gap-2">
          <button className={buttonClass} onClick={() => void handleAction('take')}>
            Взять в работу
          </button>
          <button className={subtleButtonClass} onClick={() => void handleAction('decline')}>
            Отказаться
          </button>
        </div>
      </div>
      {message && <p className="mt-2 text-sm text-slate-700">{message}</p>}
      {data?.order ? (
        <div className="mt-3 space-y-2 text-sm">
          <div className="flex flex-wrap gap-2">
            <span className={badgeClass}>Статус: {data.order.status}</span>
            <span className={badgeClass}>Услуга: {data.order.serviceCode}</span>
          </div>
          <p className="font-semibold">{data.order.title}</p>
          <p>{data.order.description}</p>
          <pre className="mt-2 whitespace-pre-wrap text-xs">
            {JSON.stringify(data.order, null, 2)}
          </pre>
        </div>
      ) : (
        <p className="mt-3 text-sm text-slate-600">Нет данных</p>
      )}
      {data?.client && (
        <div className="mt-4 rounded border border-slate-200 bg-slate-50 p-3 text-sm">
          <p className="font-semibold">Клиент</p>
          <p>{data.client.fullName}</p>
          <p className="text-slate-600">{data.client.email}</p>
        </div>
      )}
      {data?.files && data.files.length > 0 && (
        <div className="mt-4">
          <p className="font-semibold">Файлы</p>
          <ul className="mt-2 space-y-1 text-sm">
            {data.files.map((f) => (
              <li key={f.id} className="flex items-center gap-2">
                <span className="font-mono text-xs">{f.filename}</span>
                <a className="text-blue-600" href={f.path} target="_blank" rel="noreferrer">
                  открыть
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
      {data?.statusHistory && data.statusHistory.length > 0 && (
        <div className="mt-4">
          <p className="font-semibold">Статусы</p>
          <ul className="mt-2 space-y-1 text-sm">
            {data.statusHistory.map((h, idx) => (
              <li key={`${h.status}-${idx}`} className="rounded bg-slate-50 px-2 py-1">
                <span className="font-mono text-xs text-slate-500">
                  {new Date(h.changedAt).toLocaleString()}
                </span>{' '}
                {h.status}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default ExecutorOrderDetailsPage;
