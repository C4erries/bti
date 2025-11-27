import { useEffect, useState, type FormEvent } from 'react';
import { apiFetch } from '../../api/client';
import {
  buttonClass,
  cardClass,
  inputClass,
  sectionTitleClass,
  subtleButtonClass,
  textareaClass,
} from '../../components/ui';
import { useAuth } from '../../context/AuthContext';
import type { District, HouseType, Order, Service } from '../../types';

const CreateOrderPage = () => {
  const { token } = useAuth();
  const [services, setServices] = useState<Service[]>([]);
  const [districts, setDistricts] = useState<District[]>([]);
  const [houseTypes, setHouseTypes] = useState<HouseType[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [created, setCreated] = useState<Order | null>(null);

  const [form, setForm] = useState({
    serviceCode: '',
    title: '',
    description: '',
    address: '',
    districtCode: '',
    houseTypeCode: '',
  });

  const [calculator, setCalculator] = useState({
    area: '',
    hasBasement: false,
    urgent: false,
    notes: '',
  });

  useEffect(() => {
    void Promise.all([loadServices(), loadDistricts(), loadHouseTypes()]);
  }, []);

  const loadServices = async () => {
    const data = await apiFetch<Service[]>('/services');
    setServices(data);
  };
  const loadDistricts = async () => {
    const data = await apiFetch<District[]>('/districts');
    setDistricts(data);
  };
  const loadHouseTypes = async () => {
    const data = await apiFetch<HouseType[]>('/house-types');
    setHouseTypes(data);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!token) {
      setMessage('Нужна авторизация');
      return;
    }
    setMessage(null);
    try {
      const calculatorInput: Record<string, unknown> = {};
      if (calculator.area) calculatorInput.area = Number(calculator.area);
      calculatorInput.hasBasement = calculator.hasBasement;
      calculatorInput.urgent = calculator.urgent;
      if (calculator.notes) calculatorInput.notes = calculator.notes;

      const payload = {
        serviceCode: Number(form.serviceCode),
        title: form.title,
        description: form.description || null,
        address: form.address || null,
        districtCode: form.districtCode || null,
        houseTypeCode: form.houseTypeCode || null,
        calculatorInput,
      };

      const createdOrder = await apiFetch<Order>(
        '/client/orders',
        { method: 'POST', data: payload },
        token,
      );
      setCreated(createdOrder);
      setMessage(`Заказ создан: ${createdOrder.id}`);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Ошибка создания заказа');
    }
  };

  return (
    <div className={cardClass}>
      <div className="flex items-center justify-between">
        <h3 className={sectionTitleClass}>Создать заказ</h3>
        <div className="flex gap-2">
          <button className={subtleButtonClass} onClick={() => void loadServices()}>
            Обновить услуги
          </button>
          <button className={subtleButtonClass} onClick={() => void loadDistricts()}>
            Округа
          </button>
          <button className={subtleButtonClass} onClick={() => void loadHouseTypes()}>
            Типы домов
          </button>
        </div>
      </div>
      <form className="mt-4 space-y-3" onSubmit={handleSubmit}>
        <div className="grid gap-3 lg:grid-cols-2">
          <label className="text-sm font-medium text-slate-700">
            Услуга
            <select
              className={`${inputClass} mt-1`}
              value={form.serviceCode}
              onChange={(e) => setForm((p) => ({ ...p, serviceCode: e.target.value }))}
              required
            >
              <option value="">Выберите услугу</option>
              {services.map((s) => (
                <option key={s.code} value={s.code}>
                  {s.title} ({s.code})
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm font-medium text-slate-700">
            Заголовок
            <input
              className={`${inputClass} mt-1`}
              value={form.title}
              onChange={(e) => setForm((p) => ({ ...p, title: e.target.value }))}
              required
            />
          </label>
        </div>
        <label className="text-sm font-medium text-slate-700">
          Описание
          <textarea
            className={`${textareaClass} mt-1`}
            rows={2}
            value={form.description}
            onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
          />
        </label>
        <div className="grid gap-3 lg:grid-cols-3">
          <label className="text-sm font-medium text-slate-700">
            Адрес
            <input
              className={`${inputClass} mt-1`}
              value={form.address}
              onChange={(e) => setForm((p) => ({ ...p, address: e.target.value }))}
            />
          </label>
          <label className="text-sm font-medium text-slate-700">
            Округ
            <select
              className={`${inputClass} mt-1`}
              value={form.districtCode}
              onChange={(e) => setForm((p) => ({ ...p, districtCode: e.target.value }))}
            >
              <option value="">Не выбрано</option>
              {districts.map((d) => (
                <option key={d.code} value={d.code}>
                  {d.name} ({d.code})
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm font-medium text-slate-700">
            Тип дома
            <select
              className={`${inputClass} mt-1`}
              value={form.houseTypeCode}
              onChange={(e) => setForm((p) => ({ ...p, houseTypeCode: e.target.value }))}
            >
              <option value="">Не выбрано</option>
              {houseTypes.map((h) => (
                <option key={h.code} value={h.code}>
                  {h.name} ({h.code})
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="rounded-lg border border-slate-200 p-3">
          <p className="text-sm font-semibold text-slate-800">Калькулятор</p>
          <div className="mt-2 grid gap-3 lg:grid-cols-4">
            <label className="text-sm font-medium text-slate-700">
              Площадь (м²)
              <input
                className={`${inputClass} mt-1`}
                value={calculator.area}
                onChange={(e) => setCalculator((p) => ({ ...p, area: e.target.value }))}
              />
            </label>
            <label className="mt-6 inline-flex items-center gap-2 text-sm font-medium text-slate-700">
              <input
                type="checkbox"
                checked={calculator.hasBasement}
                onChange={(e) => setCalculator((p) => ({ ...p, hasBasement: e.target.checked }))}
              />
              Есть подвал
            </label>
            <label className="mt-6 inline-flex items-center gap-2 text-sm font-medium text-slate-700">
              <input
                type="checkbox"
                checked={calculator.urgent}
                onChange={(e) => setCalculator((p) => ({ ...p, urgent: e.target.checked }))}
              />
              Срочно
            </label>
            <label className="text-sm font-medium text-slate-700 lg:col-span-1">
              Особенности
              <textarea
                className={`${textareaClass} mt-1`}
                rows={2}
                value={calculator.notes}
                onChange={(e) => setCalculator((p) => ({ ...p, notes: e.target.value }))}
              />
            </label>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button type="submit" className={buttonClass}>
            Создать заказ
          </button>
          {message && <p className="text-sm text-slate-700">{message}</p>}
        </div>
      </form>

      {created && (
        <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm">
          <p className="font-semibold">Созданный заказ</p>
          <pre className="mt-2 whitespace-pre-wrap text-xs">
            {JSON.stringify(created, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

export default CreateOrderPage;
