import { useEffect, useState, type FormEvent } from 'react';
import { apiFetch } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import {
  buttonClass,
  cardClass,
  inputClass,
  sectionTitleClass,
  subtleButtonClass,
} from '../../components/ui';
import type { District, HouseType, Service, Department } from '../../types';

const AdminCatalogsPage = () => {
  const { token } = useAuth();
  const [services, setServices] = useState<Service[]>([]);
  const [districts, setDistricts] = useState<District[]>([]);
  const [houseTypes, setHouseTypes] = useState<HouseType[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [form, setForm] = useState({
    serviceCode: '',
    serviceTitle: '',
    districtCode: '',
    districtName: '',
    houseTypeCode: '',
    houseTypeName: '',
    departmentCode: '',
    departmentName: '',
  });
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    void refreshLists();
  }, []);

  const refreshLists = async () => {
    const [srv, dst, house] = await Promise.allSettled([
      apiFetch<Service[]>('/services'),
      apiFetch<District[]>('/districts'),
      apiFetch<HouseType[]>('/house-types'),
    ]);
    if (srv.status === 'fulfilled') setServices(srv.value);
    if (dst.status === 'fulfilled') setDistricts(dst.value);
    if (house.status === 'fulfilled') setHouseTypes(house.value);
    // departments endpoint может отсутствовать, пробуем мягко
    try {
      const deps = await apiFetch<Department[]>('/admin/departments', {}, token ?? undefined);
      setDepartments(deps);
    } catch {
      setDepartments([]);
    }
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!token) {
      setMessage('Нужна авторизация');
      return;
    }
    const calls: Promise<unknown>[] = [];
    if (form.serviceCode && form.serviceTitle) {
      calls.push(
        apiFetch('/admin/services', {
          method: 'POST',
          data: { code: Number(form.serviceCode), title: form.serviceTitle },
        }, token),
      );
    }
    if (form.districtCode && form.districtName) {
      calls.push(
        apiFetch('/admin/districts', {
          method: 'POST',
          data: { code: form.districtCode, name: form.districtName },
        }, token),
      );
    }
    if (form.houseTypeCode && form.houseTypeName) {
      calls.push(
        apiFetch('/admin/house-types', {
          method: 'POST',
          data: { code: form.houseTypeCode, name: form.houseTypeName },
        }, token),
      );
    }
    if (form.departmentCode && form.departmentName) {
      calls.push(
        apiFetch('/admin/departments', {
          method: 'POST',
          data: { code: form.departmentCode, name: form.departmentName },
        }, token),
      );
    }
    await Promise.allSettled(calls);
    setMessage('Запросы отправлены (проверьте логи бекенда)');
    await refreshLists();
  };

  return (
    <div className="space-y-4">
      <div className={cardClass}>
        <div className="flex items-center justify-between">
          <h3 className={sectionTitleClass}>Справочники</h3>
          <button className={subtleButtonClass} onClick={() => void refreshLists()}>
            Обновить
          </button>
        </div>
        {message && <p className="mt-2 text-sm text-slate-700">{message}</p>}
        <form className="mt-3 grid gap-3 lg:grid-cols-3" onSubmit={submit}>
          <label className="text-sm text-slate-700">
            Service code/title
            <input
              className={`${inputClass} mt-1`}
              value={form.serviceCode}
              onChange={(e) => setForm((p) => ({ ...p, serviceCode: e.target.value }))}
              placeholder="code"
            />
            <input
              className={`${inputClass} mt-2`}
              value={form.serviceTitle}
              onChange={(e) => setForm((p) => ({ ...p, serviceTitle: e.target.value }))}
              placeholder="title"
            />
          </label>
          <label className="text-sm text-slate-700">
            District code/name
            <input
              className={`${inputClass} mt-1`}
              value={form.districtCode}
              onChange={(e) => setForm((p) => ({ ...p, districtCode: e.target.value }))}
              placeholder="code"
            />
            <input
              className={`${inputClass} mt-2`}
              value={form.districtName}
              onChange={(e) => setForm((p) => ({ ...p, districtName: e.target.value }))}
              placeholder="name"
            />
          </label>
          <label className="text-sm text-slate-700">
            House type code/name
            <input
              className={`${inputClass} mt-1`}
              value={form.houseTypeCode}
              onChange={(e) => setForm((p) => ({ ...p, houseTypeCode: e.target.value }))}
              placeholder="code"
            />
            <input
              className={`${inputClass} mt-2`}
              value={form.houseTypeName}
              onChange={(e) => setForm((p) => ({ ...p, houseTypeName: e.target.value }))}
              placeholder="name"
            />
          </label>
          <label className="text-sm text-slate-700">
            Department code/name
            <input
              className={`${inputClass} mt-1`}
              value={form.departmentCode}
              onChange={(e) => setForm((p) => ({ ...p, departmentCode: e.target.value }))}
              placeholder="code"
            />
            <input
              className={`${inputClass} mt-2`}
              value={form.departmentName}
              onChange={(e) => setForm((p) => ({ ...p, departmentName: e.target.value }))}
              placeholder="name"
            />
          </label>
          <button type="submit" className={buttonClass}>
            Отправить
          </button>
        </form>
      </div>

      <div className={cardClass}>
        <h4 className={sectionTitleClass}>Услуги</h4>
        <div className="mt-2 flex flex-wrap gap-2 text-xs">
          {services.map((s) => (
            <span key={s.code} className="rounded bg-slate-100 px-2 py-1">
              {s.title} ({s.code})
            </span>
          ))}
        </div>
      </div>
      <div className={cardClass}>
        <h4 className={sectionTitleClass}>Округа</h4>
        <div className="mt-2 flex flex-wrap gap-2 text-xs">
          {districts.map((d) => (
            <span key={d.code} className="rounded bg-slate-100 px-2 py-1">
              {d.name} ({d.code})
            </span>
          ))}
        </div>
      </div>
      <div className={cardClass}>
        <h4 className={sectionTitleClass}>Типы домов</h4>
        <div className="mt-2 flex flex-wrap gap-2 text-xs">
          {houseTypes.map((h) => (
            <span key={h.code} className="rounded bg-slate-100 px-2 py-1">
              {h.name} ({h.code})
            </span>
          ))}
        </div>
      </div>
      {departments.length > 0 && (
        <div className={cardClass}>
          <h4 className={sectionTitleClass}>Отделы</h4>
          <div className="mt-2 flex flex-wrap gap-2 text-xs">
            {departments.map((d) => (
              <span key={d.code} className="rounded bg-slate-100 px-2 py-1">
                {d.name || d.code}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminCatalogsPage;
