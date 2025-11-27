import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiFetch } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { cardClass, sectionTitleClass, subtleButtonClass } from '../../components/ui';
import type { Order } from '../../types';

const ClientOrdersPage = () => {
  const { token } = useAuth();
  const [orders, setOrders] = useState<Order[]>([]);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (token) void loadOrders();
  }, [token]);

  const loadOrders = async () => {
    try {
      const data = await apiFetch<Order[]>('/client/orders', {}, token);
      setOrders(data);
      setMessage(null);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Ошибка загрузки заказов');
    }
  };

  return (
    <div className={cardClass}>
      <div className="flex items-center justify-between">
        <h3 className={sectionTitleClass}>Мои заказы</h3>
        <button className={subtleButtonClass} onClick={() => void loadOrders()}>
          Обновить
        </button>
      </div>
      {message && <p className="mt-2 text-sm text-red-600">{message}</p>}
      <div className="mt-3 overflow-auto rounded border">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-100 text-left">
            <tr>
              <th className="px-3 py-2">ID</th>
              <th className="px-3 py-2">Услуга</th>
              <th className="px-3 py-2">Статус</th>
              <th className="px-3 py-2">Адрес</th>
              <th className="px-3 py-2">Создан</th>
              <th className="px-3 py-2">Цена</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((o) => (
              <tr key={o.id} className="hover:bg-slate-50">
                <td className="px-3 py-2 font-mono">
                  <Link className="text-blue-600 underline" to={`/client/orders/${o.id}`}>
                    {o.id.slice(0, 8)}…
                  </Link>
                </td>
                <td className="px-3 py-2">{o.serviceTitle || o.serviceCode}</td>
                <td className="px-3 py-2">{o.status}</td>
                <td className="px-3 py-2">{o.address || '—'}</td>
                <td className="px-3 py-2">{new Date(o.createdAt).toLocaleString()}</td>
                <td className="px-3 py-2">{o.totalPrice ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-3 text-sm">
        <Link className="text-blue-600 underline" to="/client/orders/new">
          Создать новый заказ →
        </Link>
      </div>
    </div>
  );
};

export default ClientOrdersPage;
