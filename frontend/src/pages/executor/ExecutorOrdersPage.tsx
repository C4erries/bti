import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiFetch } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { cardClass, inputClass, sectionTitleClass, subtleButtonClass } from '../../components/ui';
import type { ExecutorOrderListItem } from '../../types';

const ExecutorOrdersPage = () => {
  const { token } = useAuth();
  const [orders, setOrders] = useState<ExecutorOrderListItem[]>([]);
  const [filters, setFilters] = useState({ status: '', departmentCode: '' });
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (token) void loadOrders();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const loadOrders = async () => {
    if (!token) return;
    try {
      const data = await apiFetch<ExecutorOrderListItem[]>(
        '/executor/orders',
        { query: { status: filters.status || undefined, departmentCode: filters.departmentCode || undefined } },
        token,
      );
      setOrders(data);
      setMessage(null);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Ошибка загрузки');
    }
  };

  return (
    <div className={cardClass}>
      <div className="flex items-center justify-between">
        <h3 className={sectionTitleClass}>Заказы исполнителя</h3>
        <button className={subtleButtonClass} onClick={() => void loadOrders()}>
          Обновить
        </button>
      </div>
      <div className="mt-3 grid gap-3 lg:grid-cols-2">
        <label className="text-sm text-slate-700">
          Статус (NEW — новые, IN_PROGRESS — в работе, DONE — завершенные)
          <select
            className={`${inputClass} mt-1`}
            value={filters.status}
            onChange={(e) => setFilters((p) => ({ ...p, status: e.target.value }))}
          >
            <option value="">Все</option>
            <option value="NEW">NEW</option>
            <option value="IN_PROGRESS">IN_PROGRESS</option>
            <option value="DONE">DONE</option>
          </select>
        </label>
        <label className="text-sm text-slate-700">
          Код отдела
          <input
            className={`${inputClass} mt-1`}
            value={filters.departmentCode}
            onChange={(e) => setFilters((p) => ({ ...p, departmentCode: e.target.value }))}
            placeholder="LEGAL / MASTERS"
          />
        </label>
      </div>
      {message && <p className="mt-2 text-sm text-red-600">{message}</p>}
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
              <tr key={o.id} className="hover:bg-slate-50">
                <td className="px-3 py-2 font-mono">
                  <Link className="text-blue-600 underline" to={`/executor/orders/${o.id}`}>
                    {o.id.slice(0, 8)}…
                  </Link>
                </td>
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
  );
};

export default ExecutorOrdersPage;
