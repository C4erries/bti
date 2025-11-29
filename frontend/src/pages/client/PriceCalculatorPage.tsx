import { useEffect, useState } from 'react';
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
import type {
  CalculatorInput,
  District,
  HouseType,
  PriceCalculatorRequest,
  PriceEstimateResponse,
} from '../../types';

interface CalculatorState {
  area: string;
  walls: boolean;
  wetZone: boolean;
  doorways: boolean;
  hasBasement: boolean;
  joinApartments: boolean;
  urgent: boolean;
  notes: string;
}

const PriceCalculatorPage = () => {
  const { token } = useAuth();
  const [districts, setDistricts] = useState<District[]>([]);
  const [houseTypes, setHouseTypes] = useState<HouseType[]>([]);

  const [form, setForm] = useState({
    districtCode: '',
    houseTypeCode: '',
  });

  const [calculator, setCalculator] = useState<CalculatorState>({
    area: '',
    walls: true,
    wetZone: false,
    doorways: true,
    hasBasement: false,
    joinApartments: false,
    urgent: false,
    notes: '',
  });

  const [estimate, setEstimate] = useState<PriceEstimateResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  const handleCalculate = async () => {
    setLoading(true);
    setError(null);
    setEstimate(null);
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

      const payload: PriceCalculatorRequest = {
        districtCode: form.districtCode || null,
        houseTypeCode: form.houseTypeCode || null,
        calculatorInput,
      };

      const data = await apiFetch<PriceEstimateResponse>(
        '/calc/estimate',
        { method: 'POST', data: payload },
        token,
      );
      setEstimate(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка расчёта');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={cardClass}>
      <div className="flex items-center justify-between">
        <h3 className={sectionTitleClass}>Калькулятор стоимости</h3>
        <div className="flex gap-2">
          <button className={subtleButtonClass} onClick={() => void loadDistricts()}>
            Обновить округа
          </button>
          <button className={subtleButtonClass} onClick={() => void loadHouseTypes()}>
            Обновить типы домов
          </button>
        </div>
      </div>

      <div className="mt-4 space-y-4">
        <div className="grid gap-3 lg:grid-cols-2">
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
          <p className="text-sm font-semibold text-slate-800">Параметры расчёта</p>
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
              Заметки
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
          <button className={buttonClass} onClick={() => void handleCalculate()} disabled={loading}>
            {loading ? 'Рассчитываем...' : 'Рассчитать стоимость'}
          </button>
          {error && <p className="text-sm text-red-600">{error}</p>}
        </div>

        {estimate && (
          <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm">
            <p className="font-semibold">
              Предварительная стоимость: {estimate.estimatedPrice.toLocaleString()} ₽
            </p>
            <p className="mt-1 text-xs text-slate-600">
              База: {estimate.breakdown.baseComponent.toLocaleString()} ₽, работы:{' '}
              {estimate.breakdown.worksComponent.toLocaleString()} ₽, коэф. особенностей{' '}
              {estimate.breakdown.featuresCoef}
            </p>
            <pre className="mt-2 whitespace-pre-wrap text-xs">
              {JSON.stringify(estimate.breakdown.raw ?? {}, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};

export default PriceCalculatorPage;
