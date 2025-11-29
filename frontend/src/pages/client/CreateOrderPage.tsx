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
import type { CalculatorInput, District, HouseType, Order } from '../../types';

type CalculatorFormState = {
  area: string;
  walls: boolean;
  wetZone: boolean;
  doorways: boolean;
  hasBasement: boolean;
  joinApartments: boolean;
  urgent: boolean;
  notes: string;
};

const CreateOrderPage = () => {
  const { token } = useAuth();
  const [districts, setDistricts] = useState<District[]>([]);
  const [houseTypes, setHouseTypes] = useState<HouseType[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [created, setCreated] = useState<Order | null>(null);

  const [form, setForm] = useState({
    title: '',
    description: '',
    address: '',
    districtCode: '',
    houseTypeCode: '',
  });

  const [calculator, setCalculator] = useState<CalculatorFormState>({
    area: '',
    walls: true,
    wetZone: false,
    doorways: true,
    hasBasement: false,
    joinApartments: false,
    urgent: false,
    notes: '',
  });

  useEffect(() => {
    void Promise.all([loadDistricts(), loadHouseTypes()]);
  }, []);

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
      const calculatorInput: CalculatorInput = {};
      if (calculator.area) calculatorInput.area = Number(calculator.area);
      calculatorInput.works = {
        walls: calculator.walls,
        wet_zone: calculator.wetZone,
        doorways: calculator.doorways,
      };
      calculatorInput.features = {
        basement: calculator.hasBasement,
        join_apartments: calculator.joinApartments,
      };
      calculatorInput.urgent = calculator.urgent;
      if (calculator.notes) calculatorInput.notes = calculator.notes;

      const payload = {
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
      setMessage(`Создан заказ: ${createdOrder.id}`);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Ошибка при создании заказа');
    }
  };

  return (
    <div className={cardClass}>
      <div className="flex items-center justify-between">
        <h3 className={sectionTitleClass}>Создание заказа</h3>
        <div className="flex gap-2">
          <button className={subtleButtonClass} onClick={() => void loadDistricts()}>
            Обновить округа
          </button>
          <button className={subtleButtonClass} onClick={() => void loadHouseTypes()}>
            Обновить типы домов
          </button>
        </div>
      </div>
      <form className="mt-4 space-y-3" onSubmit={handleSubmit}>
        <div className="grid gap-3 lg:grid-cols-1">
          <label className="text-sm font-medium text-slate-700">
            Название заказа
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
          <p className="text-sm font-semibold text-slate-800">Расчёт стоимости</p>
          <div className="mt-2 grid gap-3 lg:grid-cols-3">
            <label className="text-sm font-medium text-slate-700">
              Площадь (кв.м)
              <input
                className={`${inputClass} mt-1`}
                value={calculator.area}
                onChange={(e) => setCalculator((p) => ({ ...p, area: e.target.value }))}
              />
            </label>
            <label className="mt-6 inline-flex items-center gap-2 text-sm font-medium text-slate-700">
              <input
                type="checkbox"
                checked={calculator.walls}
                onChange={(e) => setCalculator((p) => ({ ...p, walls: e.target.checked }))}
              />
              Стены (перенос/монтаж)
            </label>
            <label className="mt-6 inline-flex items-center gap-2 text-sm font-medium text-slate-700">
              <input
                type="checkbox"
                checked={calculator.wetZone}
                onChange={(e) => setCalculator((p) => ({ ...p, wetZone: e.target.checked }))}
              />
              Влажные зоны
            </label>
            <label className="mt-6 inline-flex items-center gap-2 text-sm font-medium text-slate-700">
              <input
                type="checkbox"
                checked={calculator.doorways}
                onChange={(e) => setCalculator((p) => ({ ...p, doorways: e.target.checked }))}
              />
              Проёмы
            </label>
            <label className="mt-6 inline-flex items-center gap-2 text-sm font-medium text-slate-700">
              <input
                type="checkbox"
                checked={calculator.hasBasement}
                onChange={(e) => setCalculator((p) => ({ ...p, hasBasement: e.target.checked }))}
              />
              Есть подвал/цоколь
            </label>
            <label className="mt-6 inline-flex items-center gap-2 text-sm font-medium text-slate-700">
              <input
                type="checkbox"
                checked={calculator.joinApartments}
                onChange={(e) => setCalculator((p) => ({ ...p, joinApartments: e.target.checked }))}
              />
              Объединение квартир
            </label>
            <label className="mt-6 inline-flex items-center gap-2 text-sm font-medium text-slate-700">
              <input
                type="checkbox"
                checked={calculator.urgent}
                onChange={(e) => setCalculator((p) => ({ ...p, urgent: e.target.checked }))}
              />
              Срочно
            </label>
            <label className="text-sm font-medium text-slate-700 lg:col-span-3">
              Доп. комментарий / особенности
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
