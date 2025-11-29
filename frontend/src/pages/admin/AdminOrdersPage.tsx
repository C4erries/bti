import { useEffect, useState, type FormEvent } from 'react';
import { apiFetch } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import {
  buttonClass,
  cardClass,
  inputClass,
  sectionTitleClass,
  subtleButtonClass,
  textareaClass,
} from '../../components/ui';
import type {
  AdminOrderListItem,
  AdminOrderDetails,
  Department,
  User,
  OrderPlanVersion,
  OrderFile,
} from '../../types';

const ORDER_STATUSES = [
  'DRAFT',
  'SUBMITTED',
  'EXECUTOR_ASSIGNED',
  'VISIT_SCHEDULED',
  'DOCUMENTS_IN_PROGRESS',
  'READY_FOR_APPROVAL',
  'AWAITING_CLIENT_APPROVAL',
  'COMPLETED',
  'CANCELLED',
  'REJECTED',
  'REJECTED_BY_EXECUTOR',
];

const AdminOrdersPage = () => {
  const { token } = useAuth();
  const [orders, setOrders] = useState<AdminOrderListItem[]>([]);
  const [selected, setSelected] = useState<AdminOrderDetails | null>(null);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [executors, setExecutors] = useState<User[]>([]);
  const [filters, setFilters] = useState({
    status: '',
    executorId: '',
    departmentCode: '',
  });
  const [activeTab, setActiveTab] = useState<string>('all'); // 'all' или код отдела
  const [message, setMessage] = useState<string | null>(null);
  const [actionModal, setActionModal] = useState<{
    type: 'revision' | 'approve' | 'reject' | 'comment' | null;
    comment: string;
  }>({ type: null, comment: '' });
  const [files, setFiles] = useState<OrderFile[]>([]);
  const [fileToUpload, setFileToUpload] = useState<File | null>(null);
  const [activeDetailTab, setActiveDetailTab] = useState<'info' | 'files' | 'plans' | 'history'>('info');

  useEffect(() => {
    if (token) {
      void loadDepartments();
      void loadExecutors();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  useEffect(() => {
    if (token) {
      void loadOrders();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, filters, activeTab]);

  const loadOrders = async () => {
    if (!token) return;
    try {
      const queryParams: Record<string, string> = {};
      if (filters.status) queryParams.status = filters.status;
      if (filters.executorId) queryParams.executorId = filters.executorId;
      // Если выбрана вкладка отдела, используем её вместо фильтра
      if (activeTab !== 'all') {
        queryParams.departmentCode = activeTab;
      } else if (filters.departmentCode) {
        queryParams.departmentCode = filters.departmentCode;
      }

      const queryString = new URLSearchParams(queryParams).toString();
      const url = `/admin/orders${queryString ? `?${queryString}` : ''}`;
      const data = await apiFetch<AdminOrderListItem[]>(url, {}, token);
      setOrders(data || []);
      if (data && data.length === 0) {
        setMessage('Заказы не найдены');
      } else {
        setMessage(null);
      }
    } catch (error: any) {
      setMessage(`Ошибка загрузки: ${error.message}`);
      setOrders([]);
    }
  };

  const loadDepartments = async () => {
    if (!token) return;
    try {
      const data = await apiFetch<Department[]>('/admin/departments', {}, token);
      setDepartments(data);
    } catch (error) {
      console.error('Failed to load departments:', error);
    }
  };

  const loadExecutors = async () => {
    if (!token) return;
    try {
      // Загружаем список исполнителей через аналитику
      const data = await apiFetch<any[]>('/admin/executors/analytics', {}, token);
      setExecutors(
        data.map((e) => ({
          id: e.executorId,
          fullName: e.fullName,
          email: e.email,
          phone: null,
          isAdmin: false,
        } as User))
      );
    } catch (error) {
      console.error('Failed to load executors:', error);
    }
  };

  const loadOrder = async (id: string) => {
    if (!token) return;
    try {
      const data = await apiFetch<AdminOrderDetails>(`/admin/orders/${id}`, {}, token);
      setSelected(data);
      await loadFiles(id);
    } catch (error: any) {
      setMessage(`Ошибка загрузки заказа: ${error.message}`);
    }
  };

  const loadFiles = async (orderId: string) => {
    if (!token) return;
    try {
      const data = await apiFetch<OrderFile[]>(`/admin/orders/${orderId}/files`, {}, token);
      setFiles(data || []);
    } catch (error: any) {
      console.error('Failed to load files:', error);
      setFiles([]);
    }
  };

  const uploadFile = async (e: FormEvent) => {
    e.preventDefault();
    if (!selected || !token || !fileToUpload) return;
    try {
      const formData = new FormData();
      formData.append('upload', fileToUpload);
      await apiFetch<OrderFile>(
        `/admin/orders/${selected!.order.id}/files`,
        {
          method: 'POST',
          data: formData,
          isFormData: true,
        },
        token,
      );
      setMessage('Файл загружен');
      setFileToUpload(null);
      await loadFiles(selected!.order.id);
    } catch (error: any) {
      setMessage(`Ошибка загрузки файла: ${error.message}`);
    }
  };

  const loadPlanVersions = async (orderId: string) => {
    if (!token) return;
    try {
      const data = await apiFetch<OrderPlanVersion[]>(`/admin/orders/${orderId}/plan/versions`, {}, token);
      if (selected) {
        setSelected({ ...selected, planVersions: data });
      }
    } catch (error: any) {
      setMessage(`Ошибка загрузки версий плана: ${error.message}`);
    }
  };

  const handleAction = async (action: 'revision' | 'approve' | 'reject' | 'comment') => {
    if (!token || !selected || !actionModal.comment.trim()) {
      if (action !== 'approve') {
        setMessage('Комментарий обязателен');
        return;
      }
    }

    try {
      const endpoint = `/admin/orders/${selected!.order.id}/${action === 'revision' ? 'send-for-revision' : action === 'comment' ? 'comment' : action}`;
      await apiFetch(
        endpoint,
        {
          method: 'POST',
          data: {
            comment: actionModal.comment || undefined,
          },
        },
        token,
      );
      setMessage(`Действие "${action}" выполнено`);
      setActionModal({ type: null, comment: '' });
      await loadOrder(selected!.order.id);
      await loadOrders();
    } catch (error: any) {
      setMessage(`Ошибка: ${error.message}`);
    }
  };

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return '—';
    try {
      return new Date(dateString).toLocaleString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateString;
    }
  };

  // Фильтрация уже выполняется на backend через параметры запроса

  return (
    <div className="space-y-4">
      <div className={cardClass}>
        <div className="flex items-center justify-between">
          <h3 className={sectionTitleClass}>Модерация заказов</h3>
          <button className={subtleButtonClass} onClick={() => void loadOrders()}>
            Обновить
          </button>
        </div>

        {message && (
          <div
            className={`mt-2 rounded p-2 text-sm ${
              message.includes('Ошибка') ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'
            }`}
          >
            {message}
          </div>
        )}

        {/* Фильтры */}
        <div className="mt-4 grid gap-3 rounded border border-slate-200 bg-slate-50 p-3 lg:grid-cols-3">
          <label className="text-sm text-slate-700">
            Фильтр по статусу:
            <select
              className={`${inputClass} mt-1`}
              value={filters.status}
              onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}
            >
              <option value="">Все статусы</option>
              {ORDER_STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm text-slate-700">
            Фильтр по исполнителю:
            <select
              className={`${inputClass} mt-1`}
              value={filters.executorId}
              onChange={(e) => setFilters((f) => ({ ...f, executorId: e.target.value }))}
            >
              <option value="">Все исполнители</option>
              {executors.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.fullName}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm text-slate-700">
            Фильтр по отделу:
            <select
              className={`${inputClass} mt-1`}
              value={filters.departmentCode}
              onChange={(e) => setFilters((f) => ({ ...f, departmentCode: e.target.value }))}
            >
              <option value="">Все отделы</option>
              {departments.map((d) => (
                <option key={d.code} value={d.code}>
                  {d.name || d.code}
                </option>
              ))}
            </select>
          </label>
        </div>

        {/* Вкладки по отделам */}
        <div className="mt-4 flex flex-wrap gap-2 border-b border-slate-200">
          <button
            className={`px-4 py-2 text-sm font-medium ${
              activeTab === 'all'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-slate-600 hover:text-slate-900'
            }`}
            onClick={() => setActiveTab('all')}
          >
            Все заказы
          </button>
          {departments.map((d) => (
            <button
              key={d.code}
              className={`px-4 py-2 text-sm font-medium ${
                activeTab === d.code
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
              onClick={() => setActiveTab(d.code)}
            >
              {d.name || d.code}
            </button>
          ))}
        </div>

        {/* Таблица заказов */}
        <div className="mt-4 overflow-auto rounded border border-slate-200">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-100 text-left">
              <tr>
                <th className="px-4 py-3 font-semibold">ID</th>
                 <th className="px-4 py-3 font-semibold">Клиент</th>
                 <th className="px-4 py-3 font-semibold">Исполнитель</th>
                 <th className="px-4 py-3 font-semibold">Тип работы</th>
                 <th className="px-4 py-3 font-semibold">Описание</th>
                 <th className="px-4 py-3 font-semibold text-center">Файлы</th>
                 <th className="px-4 py-3 font-semibold">Дата создания</th>
                 <th className="px-4 py-3 font-semibold">Срок выполнения</th>
                 <th className="px-4 py-3 font-semibold">Комментарий</th>
                 <th className="px-4 py-3 font-semibold">Статус</th>
              </tr>
            </thead>
            <tbody>
              {orders.length === 0 ? (
                <tr>
                  <td colSpan={10} className="px-4 py-8 text-center text-slate-500">
                    Заказы не найдены
                  </td>
                </tr>
              ) : (
                orders.map((o) => (
                  <tr
                    key={o.id}
                    className="border-t border-slate-200 hover:bg-slate-50 cursor-pointer"
                    onClick={() => void loadOrder(o.id)}
                  >
                    <td className="px-4 py-3 font-mono text-xs">{o.id.slice(0, 8)}…</td>
                    <td className="px-4 py-3">{o.clientName || '—'}</td>
                    <td className="px-4 py-3">{o.executorName || '—'}</td>
                    <td className="px-4 py-3">
                  <span className="rounded bg-blue-100 px-2 py-1 text-xs">
                    {o.title}
                      </span>
                    </td>
                    <td className="px-4 py-3 max-w-xs truncate">{o.description || '—'}</td>
                    <td className="px-4 py-3 text-center">
                      <span className="rounded bg-slate-100 px-2 py-1 text-xs">{o.filesCount}</span>
                    </td>
                    <td className="px-4 py-3 text-xs">{formatDate(o.createdAt)}</td>
                    <td className="px-4 py-3 text-xs">{formatDate(o.plannedVisitAt)}</td>
                    <td className="px-4 py-3 max-w-xs truncate text-xs text-slate-600">
                      {o.executorComment || '—'}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
                          o.status === 'COMPLETED'
                            ? 'bg-green-100 text-green-700'
                            : o.status === 'REJECTED' || o.status === 'REJECTED_BY_EXECUTOR'
                              ? 'bg-red-100 text-red-700'
                              : o.status === 'CANCELLED'
                                ? 'bg-gray-100 text-gray-700'
                                : 'bg-yellow-100 text-yellow-700'
                        }`}
                      >
                        {o.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Детали заказа */}
      {selected && (
        <div className={cardClass}>
          <div className="flex items-center justify-between">
            <h4 className={sectionTitleClass}>Детали заказа</h4>
            <button className={subtleButtonClass} onClick={() => setSelected(null)}>
              Закрыть
            </button>
          </div>

          {/* Информация о заказе */}
          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            <div>
              <h5 className="font-semibold text-slate-700">Клиент</h5>
              <p className="text-sm text-slate-600">{selected.client?.fullName || '—'}</p>
              <p className="text-xs text-slate-500">{selected.client?.email || ''}</p>
            </div>
            <div>
              <h5 className="font-semibold text-slate-700">Исполнитель</h5>
              <p className="text-sm text-slate-600">{selected.executor?.fullName || '—'}</p>
              <p className="text-xs text-slate-500">{selected.executor?.email || ''}</p>
            </div>
            <div>
              <h5 className="font-semibold text-slate-700">Статус</h5>
              <p className="text-sm text-slate-600">{selected.order.status}</p>
            </div>
            <div>
              <h5 className="font-semibold text-slate-700">Цена</h5>
              <p className="text-sm text-slate-600">{selected.order.totalPrice || selected.order.estimatedPrice || '—'}</p>
            </div>
          </div>

          {/* Действия */}
          <div className="mt-4 flex flex-wrap gap-2 rounded-lg bg-blue-50 p-4">
            <button
              className={`${buttonClass} bg-yellow-600 hover:bg-yellow-700`}
              onClick={() => setActionModal({ type: 'revision', comment: '' })}
            >
              Отправить на доработку
            </button>
            <button
              className={`${buttonClass} bg-green-600 hover:bg-green-700`}
              onClick={() => setActionModal({ type: 'approve', comment: '' })}
            >
              Утвердить
            </button>
            <button
              className={`${buttonClass} bg-red-600 hover:bg-red-700`}
              onClick={() => setActionModal({ type: 'reject', comment: '' })}
            >
              Отклонить
            </button>
            <button
              className={`${buttonClass} bg-blue-600 hover:bg-blue-700`}
              onClick={() => setActionModal({ type: 'comment', comment: '' })}
            >
              Оставить комментарий
            </button>
          </div>

          {/* Модальное окно для действий */}
          {actionModal.type && (
            <div className="mt-4 rounded border border-slate-200 bg-slate-50 p-4">
              <h5 className="font-semibold text-slate-700">
                {actionModal.type === 'revision'
                  ? 'Отправить на доработку'
                  : actionModal.type === 'approve'
                    ? 'Утвердить заказ'
                    : actionModal.type === 'reject'
                      ? 'Отклонить заказ'
                      : 'Добавить комментарий'}
              </h5>
              <textarea
                className={`${textareaClass} mt-2`}
                rows={3}
                value={actionModal.comment}
                onChange={(e) => setActionModal({ ...actionModal, comment: e.target.value })}
                placeholder="Введите комментарий..."
                required={actionModal.type !== 'approve'}
              />
              <div className="mt-3 flex gap-2">
                <button
                  className={buttonClass}
                  onClick={() => void handleAction(actionModal.type!)}
                  disabled={actionModal.type !== 'approve' && !actionModal.comment.trim()}
                >
                  Подтвердить
                </button>
                <button
                  className={subtleButtonClass}
                  onClick={() => setActionModal({ type: null, comment: '' })}
                >
                  Отмена
                </button>
              </div>
            </div>
          )}

          {/* Вкладки деталей */}
          <div className="mt-6">
            <div className="flex border-b border-slate-200">
              <button
                className={`px-4 py-2 text-sm font-medium ${
                  activeDetailTab === 'info'
                    ? 'border-b-2 border-blue-600 text-blue-600'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
                onClick={() => setActiveDetailTab('info')}
              >
                Информация
              </button>
              <button
                className={`px-4 py-2 text-sm font-medium ${
                  activeDetailTab === 'files'
                    ? 'border-b-2 border-blue-600 text-blue-600'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
                onClick={() => {
                  setActiveDetailTab('files');
                  void loadFiles(selected.order.id);
                }}
              >
                Файлы ({files.length})
              </button>
              <button
                className={`px-4 py-2 text-sm font-medium ${
                  activeDetailTab === 'plans'
                    ? 'border-b-2 border-blue-600 text-blue-600'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
                onClick={() => {
                  setActiveDetailTab('plans');
                  void loadPlanVersions(selected.order.id);
                }}
              >
                Версии плана
              </button>
              <button
                className={`px-4 py-2 text-sm font-medium ${
                  activeDetailTab === 'history'
                    ? 'border-b-2 border-blue-600 text-blue-600'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
                onClick={() => setActiveDetailTab('history')}
              >
                История
              </button>
            </div>

            {/* Содержимое вкладок */}
            {activeDetailTab === 'info' && (
              <div className="mt-4">
                <div className="grid gap-4 lg:grid-cols-2">
                  <div>
                    <h5 className="font-semibold text-slate-700">Описание</h5>
                    <p className="text-sm text-slate-600">{selected.order.description || '—'}</p>
                  </div>
                  <div>
                    <h5 className="font-semibold text-slate-700">Адрес</h5>
                    <p className="text-sm text-slate-600">{selected.order.address || '—'}</p>
                  </div>
                </div>
              </div>
            )}

            {activeDetailTab === 'files' && (
              <div className="mt-4">
                <div className="flex items-center justify-between mb-4">
                  <h5 className="font-semibold text-slate-700">Файлы заказа</h5>
                  <form className="flex items-center gap-2" onSubmit={uploadFile}>
                    <input
                      type="file"
                      className="text-sm"
                      onChange={(e) => setFileToUpload(e.target.files?.[0] ?? null)}
                    />
                    <button type="submit" className={buttonClass} disabled={!fileToUpload}>
                      Загрузить
                    </button>
                  </form>
                </div>
                {files.length === 0 ? (
                  <p className="text-sm text-slate-500">Файлы отсутствуют</p>
                ) : (
                  <div className="space-y-2">
                    {files.map((f) => (
                      <div
                        key={f.id}
                        className="flex items-center justify-between rounded border border-slate-200 p-3"
                      >
                        <div>
                          <span className="font-medium text-sm">{f.filename}</span>
                        </div>
                        <a
                          className="text-blue-600 hover:text-blue-800 text-sm"
                          href={f.path}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Открыть
                        </a>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeDetailTab === 'plans' && (
              <div className="mt-4">

                {selected.planVersions.length === 0 ? (
                  <p className="text-sm text-slate-500">Версии плана не найдены</p>
                ) : (
                  <div className="space-y-3">
                    {selected.planVersions.map((version) => (
                      <div
                        key={version.id}
                        className="rounded border border-slate-200 p-3 cursor-pointer hover:bg-slate-50"
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <span className="font-semibold text-sm">{version.versionType}</span>
                            {version.comment && (
                              <p className="text-xs text-slate-600 mt-1">{version.comment}</p>
                            )}
                          </div>
                          <span className="text-xs text-slate-500">
                            {formatDate(version.createdAt)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeDetailTab === 'history' && (
              <div className="mt-4">
                <h5 className="font-semibold text-slate-700 mb-3">История статусов</h5>
                <div className="space-y-2">
                  {selected.statusHistory.map((item, idx) => (
                    <div key={idx} className="rounded border border-slate-200 p-2 text-sm">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{item.status}</span>
                        <span className="text-xs text-slate-500">{formatDate(item.changedAt)}</span>
                      </div>
                      {item.comment && (
                        <p className="text-xs text-slate-600 mt-1">{item.comment}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminOrdersPage;
