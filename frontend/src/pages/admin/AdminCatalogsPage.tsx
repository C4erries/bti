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
import type { District, HouseType, Department } from '../../types';

const AdminCatalogsPage = () => {
  const { token } = useAuth();
  const [districts, setDistricts] = useState<District[]>([]);
  const [houseTypes, setHouseTypes] = useState<HouseType[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [form, setForm] = useState({
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
    const [dst, house] = await Promise.allSettled([
      apiFetch<District[]>('/districts'),
      apiFetch<HouseType[]>('/house-types'),
    ]);
    if (dst.status === 'fulfilled') setDistricts(dst.value);
    if (house.status === 'fulfilled') setHouseTypes(house.value);
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
    if (form.districtCode && form.districtName) {
      calls.push(
        apiFetch(
          '/admin/districts',
          {
            method: 'POST',
            data: { code: form.districtCode, name: form.districtName },
          },
          token,
        ),
      );
    }
    if (form.houseTypeCode && form.houseTypeName) {
      calls.push(
        apiFetch(
          '/admin/house-types',
          {
            method: 'POST',
            data: { code: form.houseTypeCode, name: form.houseTypeName },
          },
          token,
        ),
      );
    }
    if (form.departmentCode && form.departmentName) {
      calls.push(
        apiFetch(
          '/admin/departments',
          {
            method: 'POST',
            data: { code: form.departmentCode, name: form.departmentName },
          },
          token,
        ),
      );
    }
    await Promise.allSettled(calls);
    setMessage('Изменения применены (для существующей БД может потребоваться обновление записей)');
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
            Округ (код/название)
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
            Тип дома (код/название)
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
            Отдел (код/название)
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
            Сохранить
          </button>
        </form>
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
