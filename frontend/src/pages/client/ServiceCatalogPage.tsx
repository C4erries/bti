import { useEffect, useState } from 'react';
import { apiFetch } from '../../api/client';
import { cardClass, sectionTitleClass, subtleButtonClass } from '../../components/ui';
import type { Service } from '../../types';

const ServiceCatalogPage = () => {
  const [services, setServices] = useState<Service[]>([]);
  const [selected, setSelected] = useState<Service | null>(null);

  useEffect(() => {
    void loadServices();
  }, []);

  const loadServices = async () => {
    const data = await apiFetch<Service[]>('/services');
    setServices(data);
  };

  const loadDetails = async (code: number) => {
    const data = await apiFetch<Service>(`/services/${code}`);
    setSelected(data);
  };

  return (
    <div className="space-y-4">
      <div className={cardClass}>
        <div className="flex items-center justify-between">
          <h3 className={sectionTitleClass}>Каталог услуг</h3>
          <button className={subtleButtonClass} onClick={() => void loadServices()}>
            Обновить
          </button>
        </div>
        <div className="mt-3 overflow-auto rounded border">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-100 text-left">
              <tr>
                <th className="px-3 py-2">Код</th>
                <th className="px-3 py-2">Название</th>
                <th className="px-3 py-2">Цена</th>
                <th className="px-3 py-2">Длительность</th>
              </tr>
            </thead>
            <tbody>
              {services.map((s) => (
                <tr
                  key={s.code}
                  className="cursor-pointer hover:bg-slate-50"
                  onClick={() => void loadDetails(s.code)}
                >
                  <td className="px-3 py-2 font-mono">{s.code}</td>
                  <td className="px-3 py-2">{s.title}</td>
                  <td className="px-3 py-2">{s.basePrice ?? '—'}</td>
                  <td className="px-3 py-2">{s.baseDurationDays ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {selected && (
        <div className={cardClass}>
          <h4 className={sectionTitleClass}>Детали услуги</h4>
          <pre className="mt-2 whitespace-pre-wrap text-xs">
            {JSON.stringify(selected, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

export default ServiceCatalogPage;
