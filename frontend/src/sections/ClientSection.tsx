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
  District,
  HouseType,
  Order,
  OrderFile,
  OrderPlanVersion,
  OrderStatusHistoryItem,
  Service,
} from '../types';

export const ClientSection = () => {
  const { token, user } = useAuth();
  const [services, setServices] = useState<Service[]>([]);
  const [selectedService, setSelectedService] = useState<Service | null>(null);
  const [districts, setDistricts] = useState<District[]>([]);
  const [houseTypes, setHouseTypes] = useState<HouseType[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [files, setFiles] = useState<OrderFile[]>([]);
  const [plan, setPlan] = useState<OrderPlanVersion | null>(null);
  const [statusHistory, setStatusHistory] = useState<OrderStatusHistoryItem[]>([]);
  const [fileToUpload, setFileToUpload] = useState<File | null>(null);
  const [createPayload, setCreatePayload] = useState({
    serviceCode: '',
    title: '',
    description: '',
    address: '',
    city: '',
    region: '',
    districtCode: '',
    houseTypeCode: '',
    calculatorInput: '',
  });
  const [message, setMessage] = useState<string | null>(null);

  if (!token) {
    return (
      <div className={cardClass}>
        <h3 className={sectionTitleClass}>Клиент</h3>
        <p className="text-sm text-slate-600">Авторизуйтесь как клиент, чтобы работать с заказами.</p>
      </div>
    );
  }

  const ensureClient = () =>
    user?.isClient !== false || !user ? true : false;

  const loadServices = async () => {
    const data = await apiFetch<Service[]>('/services');
    setServices(data);
  };

  const loadServiceDetails = async (code: number) => {
    const data = await apiFetch<Service>(`/services/${code}`);
    setSelectedService(data);
  };

  const loadDistricts = async () => {
    const data = await apiFetch<District[]>('/districts');
    setDistricts(data);
  };

  const loadHouseTypes = async () => {
    const data = await apiFetch<HouseType[]>('/house-types');
    setHouseTypes(data);
  };

  const loadOrders = async () => {
    const data = await apiFetch<Order[]>('/client/orders', {}, token);
    setOrders(data);
  };

  const loadOrderDetails = async (orderId: string) => {
    const details = await apiFetch<Order>(`/client/orders/${orderId}`, {}, token);
    setSelectedOrder(details);
    const [fileList, planVersion, history] = await Promise.allSettled([
      apiFetch<OrderFile[]>(`/orders/${orderId}/files`, {}, token),
      apiFetch<OrderPlanVersion>(`/orders/${orderId}/plan`, {}, token),
      apiFetch<OrderStatusHistoryItem[]>(`/orders/${orderId}/status-history`, {}, token),
    ]);
    if (fileList.status === 'fulfilled') setFiles(fileList.value);
    if (planVersion.status === 'fulfilled') setPlan(planVersion.value);
    if (history.status === 'fulfilled') setStatusHistory(history.value);
  };

  const handleCreateOrder = async (e: FormEvent) => {
    e.preventDefault();
    setMessage(null);
    try {
      const calculatorInput = createPayload.calculatorInput
        ? JSON.parse(createPayload.calculatorInput)
        : null;
      const payload = {
        serviceCode: Number(createPayload.serviceCode),
        title: createPayload.title,
        description: createPayload.description || null,
        address: createPayload.address || null,
        city: createPayload.city || null,
        region: createPayload.region || null,
        districtCode: createPayload.districtCode || null,
        houseTypeCode: createPayload.houseTypeCode || null,
        calculatorInput,
      };
      const created = await apiFetch<Order>('/client/orders', { method: 'POST', data: payload }, token);
      setMessage(`Заказ создан: ${created.id}`);
      await loadOrders();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Ошибка создания заказа');
    }
  };

  const handleUpload = async (e: FormEvent) => {
    e.preventDefault();
    if (!selectedOrder || !fileToUpload) return;
    try {
      const formData = new FormData();
      formData.append('file', fileToUpload);
      await apiFetch<OrderFile>(`/orders/${selectedOrder.id}/files`, {
        method: 'POST',
        data: formData,
        isFormData: true,
        token,
      });
      setMessage('Файл загружен');
      setFileToUpload(null);
      await loadOrderDetails(selectedOrder.id);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Ошибка загрузки файла');
    }
  };

  return (
    <div className="space-y-4">
      {!ensureClient() && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
          Пользователь не отмечен как клиент, доступ к методам может быть ограничен.
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <div className={cardClass}>
          <div className="flex items-center justify-between">
            <h3 className={sectionTitleClass}>Справочники</h3>
            <div className="flex gap-2">
              <button className={subtleButtonClass} onClick={() => void loadServices()}>
                Загрузить услуги
              </button>
              <button className={subtleButtonClass} onClick={() => void loadDistricts()}>
                Районы
              </button>
              <button className={subtleButtonClass} onClick={() => void loadHouseTypes()}>
                Типы домов
              </button>
            </div>
          </div>
          <div className="mt-3 space-y-2">
            {services.length > 0 && (
              <div>
                <p className="text-sm font-medium text-slate-700">Услуги</p>
                <div className="overflow-auto rounded border">
                  <table className="min-w-full text-sm">
                    <thead className="bg-slate-100 text-left">
                      <tr>
                        <th className="px-3 py-2">Code</th>
                        <th className="px-3 py-2">Title</th>
                        <th className="px-3 py-2">Price</th>
                      </tr>
                    </thead>
                    <tbody>
                      {services.map((service) => (
                        <tr
                          key={service.code}
                          className="cursor-pointer hover:bg-slate-50"
                          onClick={() => void loadServiceDetails(service.code)}
                        >
                          <td className="px-3 py-2 font-mono">{service.code}</td>
                          <td className="px-3 py-2">{service.title}</td>
                          <td className="px-3 py-2">{service.basePrice ?? '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            {selectedService && (
              <div className="rounded border border-slate-200 bg-slate-50 p-3 text-sm">
                <p className="font-semibold">Детали услуги</p>
                <pre className="mt-2 whitespace-pre-wrap text-xs">
                  {JSON.stringify(selectedService, null, 2)}
                </pre>
              </div>
            )}
            {districts.length > 0 && (
              <div>
                <p className="text-sm font-medium text-slate-700">Районы</p>
                <div className="flex flex-wrap gap-2 text-xs">
                  {districts.map((d) => (
                    <span key={d.code} className="rounded bg-slate-100 px-2 py-1">
                      {d.code} — {d.name}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {houseTypes.length > 0 && (
              <div>
                <p className="text-sm font-medium text-slate-700">Типы домов</p>
                <div className="flex flex-wrap gap-2 text-xs">
                  {houseTypes.map((d) => (
                    <span key={d.code} className="rounded bg-slate-100 px-2 py-1">
                      {d.code} — {d.name}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className={cardClass}>
          <h3 className={sectionTitleClass}>Создание заказа</h3>
          <form className="mt-3 space-y-3" onSubmit={handleCreateOrder}>
            <div className="grid grid-cols-2 gap-3">
              <label className="text-sm font-medium text-slate-700">
                Услуга (code)
                <input
                  className={`${inputClass} mt-1`}
                  value={createPayload.serviceCode}
                  onChange={(e) => setCreatePayload((p) => ({ ...p, serviceCode: e.target.value }))}
                  placeholder="Например, 101"
                  required
                />
              </label>
              <label className="text-sm font-medium text-slate-700">
                Заголовок
                <input
                  className={`${inputClass} mt-1`}
                  value={createPayload.title}
                  onChange={(e) => setCreatePayload((p) => ({ ...p, title: e.target.value }))}
                  required
                />
              </label>
            </div>
            <label className="text-sm font-medium text-slate-700">
              Описание
              <textarea
                className={`${textareaClass} mt-1`}
                rows={2}
                value={createPayload.description}
                onChange={(e) =>
                  setCreatePayload((p) => ({ ...p, description: e.target.value }))
                }
              />
            </label>
            <div className="grid grid-cols-2 gap-3">
              <label className="text-sm font-medium text-slate-700">
                Адрес
                <input
                  className={`${inputClass} mt-1`}
                  value={createPayload.address}
                  onChange={(e) => setCreatePayload((p) => ({ ...p, address: e.target.value }))}
                />
              </label>
              <label className="text-sm font-medium text-slate-700">
                Город
                <input
                  className={`${inputClass} mt-1`}
                  value={createPayload.city}
                  onChange={(e) => setCreatePayload((p) => ({ ...p, city: e.target.value }))}
                />
              </label>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <label className="text-sm font-medium text-slate-700">
                Регион
                <input
                  className={`${inputClass} mt-1`}
                  value={createPayload.region}
                  onChange={(e) => setCreatePayload((p) => ({ ...p, region: e.target.value }))}
                />
              </label>
              <label className="text-sm font-medium text-slate-700">
                District code
                <input
                  className={`${inputClass} mt-1`}
                  value={createPayload.districtCode}
                  onChange={(e) =>
                    setCreatePayload((p) => ({ ...p, districtCode: e.target.value }))
                  }
                  placeholder="LEGAL / ..."
                />
              </label>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <label className="text-sm font-medium text-slate-700">
                House type code
                <input
                  className={`${inputClass} mt-1`}
                  value={createPayload.houseTypeCode}
                  onChange={(e) =>
                    setCreatePayload((p) => ({ ...p, houseTypeCode: e.target.value }))
                  }
                />
              </label>
              <label className="text-sm font-medium text-slate-700">
                calculatorInput (JSON)
                <textarea
                  className={`${textareaClass} mt-1`}
                  rows={2}
                  value={createPayload.calculatorInput}
                  onChange={(e) =>
                    setCreatePayload((p) => ({ ...p, calculatorInput: e.target.value }))
                  }
                  placeholder='{"rooms":2}'
                />
              </label>
            </div>
            <div className="flex items-center gap-2">
              <button type="submit" className={buttonClass}>
                Создать
              </button>
              {message && <p className="text-sm text-slate-600">{message}</p>}
            </div>
          </form>
        </div>
      </div>

      <div className={cardClass}>
        <div className="flex items-center justify-between">
          <h3 className={sectionTitleClass}>Мои заказы</h3>
          <button className={subtleButtonClass} onClick={() => void loadOrders()}>
            Обновить список
          </button>
        </div>
        <div className="mt-3">
          {orders.length === 0 ? (
            <p className="text-sm text-slate-600">Нет данных. Нажмите «Обновить список».</p>
          ) : (
            <div className="overflow-auto rounded border">
              <table className="min-w-full text-sm">
                <thead className="bg-slate-100 text-left">
                  <tr>
                    <th className="px-3 py-2">ID</th>
                    <th className="px-3 py-2">Статус</th>
                    <th className="px-3 py-2">Сервис</th>
                    <th className="px-3 py-2">Создан</th>
                    <th className="px-3 py-2">Цена</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.map((order) => (
                    <tr
                      key={order.id}
                      className="cursor-pointer hover:bg-slate-50"
                      onClick={() => void loadOrderDetails(order.id)}
                    >
                      <td className="px-3 py-2 font-mono">{order.id.slice(0, 8)}…</td>
                      <td className="px-3 py-2">{order.status}</td>
                      <td className="px-3 py-2">{order.serviceCode}</td>
                      <td className="px-3 py-2">{new Date(order.createdAt).toLocaleString()}</td>
                      <td className="px-3 py-2">{order.totalPrice ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {selectedOrder && (
          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            <div className="space-y-3">
              <div className="rounded border border-slate-200 p-3">
                <p className="font-semibold">Детали заказа</p>
                <pre className="mt-2 whitespace-pre-wrap text-xs">
                  {JSON.stringify(selectedOrder, null, 2)}
                </pre>
              </div>
              <div className="rounded border border-slate-200 p-3">
                <p className="font-semibold">План заказа</p>
                {plan ? (
                  <pre className="mt-2 whitespace-pre-wrap text-xs">
                    {JSON.stringify(plan, null, 2)}
                  </pre>
                ) : (
                  <p className="text-sm text-slate-600">Нет данных</p>
                )}
              </div>
            </div>
            <div className="space-y-3">
              <div className="rounded border border-slate-200 p-3">
                <div className="flex items-center justify-between">
                  <p className="font-semibold">Файлы</p>
                  <form className="flex items-center gap-2" onSubmit={handleUpload}>
                    <input
                      type="file"
                      onChange={(e) => setFileToUpload(e.target.files?.[0] ?? null)}
                      className="text-sm"
                    />
                    <button type="submit" className={subtleButtonClass}>
                      Загрузить
                    </button>
                  </form>
                </div>
                {files.length ? (
                  <ul className="mt-2 space-y-1 text-sm">
                    {files.map((f) => (
                      <li key={f.id} className="flex items-center gap-2">
                        <span className="font-mono text-xs">{f.filename}</span>
                        <a className="text-blue-600" href={f.path} target="_blank" rel="noreferrer">
                          открыть
                        </a>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-slate-600">Файлы не найдены</p>
                )}
              </div>
              <div className="rounded border border-slate-200 p-3">
                <p className="font-semibold">Статус-история</p>
                {statusHistory.length ? (
                  <ul className="mt-2 space-y-1 text-sm">
                    {statusHistory.map((h, idx) => (
                      <li key={`${h.status}-${idx}`}>
                        <span className="font-mono text-xs text-slate-500">
                          {new Date(h.changedAt).toLocaleString()}
                        </span>{' '}
                        {h.oldStatus ? `${h.oldStatus} → ` : ''}
                        <span className="font-semibold">{h.status}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-slate-600">Нет записей</p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
