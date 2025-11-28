import { useEffect, useState, type FormEvent } from 'react';
import { useParams } from 'react-router-dom';
import { apiFetch } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import {
  badgeClass,
  buttonClass,
  cardClass,
  inputClass,
  sectionTitleClass,
  subtleButtonClass,
  textareaClass,
} from '../../components/ui';
import Plan3DViewer from '../../components/Plan3DViewer';
import type {
  ExecutorOrderDetails,
  OrderPlanVersion,
  PlanGeometry,
} from '../../types';

type TabKey = 'info' | 'files' | 'plan' | 'history';
type PlanViewMode = 'json' | '3d' | 'edit';

const ExecutorOrderDetailsPage = () => {
  const { orderId } = useParams();
  const { token } = useAuth();
  const [data, setData] = useState<ExecutorOrderDetails | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [tab, setTab] = useState<TabKey>('info');
  const [planViewMode, setPlanViewMode] = useState<PlanViewMode>('json');
  const [currentPlan, setCurrentPlan] = useState<OrderPlanVersion | null>(null);
  const [planData, setPlanData] = useState<PlanGeometry | null>(null);
  const [planVersions, setPlanVersions] = useState<OrderPlanVersion[]>([]);
  const [isEditing, setIsEditing] = useState(false);
  const [editComment, setEditComment] = useState('');
  const [rejectComment, setRejectComment] = useState('');
  const [rejectIssues, setRejectIssues] = useState<string[]>(['']);
  const [showApproveModal, setShowApproveModal] = useState(false);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [approveComment, setApproveComment] = useState('');

  useEffect(() => {
    if (token && orderId) {
      void loadDetails();
      void loadPlanVersions();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orderId, token]);

  const loadDetails = async () => {
    if (!token || !orderId) return;
    const details = await apiFetch<ExecutorOrderDetails>(`/executor/orders/${orderId}`, {}, token);
    setData(details);
    // Загружаем план по умолчанию
    if (details.planOriginal || details.planModified) {
      const planToLoad = details.planModified || details.planOriginal;
      if (planToLoad) {
        setCurrentPlan(planToLoad);
        setPlanData(planToLoad.plan);
      }
    }
  };

  const loadPlanVersions = async () => {
    if (!token || !orderId) return;
    try {
      const versions = await apiFetch<OrderPlanVersion[]>(
        `/executor/orders/${orderId}/plan/versions`,
        {},
        token
      );
      setPlanVersions(versions);
    } catch (error) {
      console.error('Failed to load plan versions:', error);
    }
  };

  const loadPlan = async (versionType?: string) => {
    if (!token || !orderId) return;
    try {
      const query = versionType ? `?version=${versionType}` : '';
      const plan = await apiFetch<OrderPlanVersion>(
        `/executor/orders/${orderId}/plan${query}`,
        {},
        token
      );
      setCurrentPlan(plan);
      setPlanData(plan.plan);
    } catch (error) {
      console.error('Failed to load plan:', error);
    }
  };

  const handlePlanChange = (newPlan: PlanGeometry) => {
    setPlanData(newPlan);
  };

  const handleAction = async (action: 'take' | 'decline') => {
    if (!token || !orderId) return;
    await apiFetch(`/executor/orders/${orderId}/${action}`, { method: 'POST' }, token);
    setMessage(action === 'take' ? 'Взято в работу' : 'Отказ отправлен');
    await loadDetails();
  };

  const handleApprove = async (e: FormEvent) => {
    e.preventDefault();
    if (!token || !orderId) return;
    try {
      await apiFetch(
        `/executor/orders/${orderId}/plan/approve`,
        {
          method: 'POST',
          data: { comment: approveComment || null },
        },
        token
      );
      setShowApproveModal(false);
      setApproveComment('');
      setMessage('План одобрен');
      await loadDetails();
      await loadPlanVersions();
    } catch (error: any) {
      setMessage(`Ошибка: ${error.message}`);
    }
  };

  const handleEdit = async (e: FormEvent) => {
    e.preventDefault();
    if (!token || !orderId || !planData || !editComment.trim()) {
      setMessage('Заполните комментарий с описанием изменений');
      return;
    }
    try {
      await apiFetch(
        `/executor/orders/${orderId}/plan/edit`,
        {
          method: 'POST',
          data: {
            plan: planData,
            comment: editComment,
          },
        },
        token
      );
      setIsEditing(false);
      setEditComment('');
      setMessage('План отредактирован и отправлен клиенту на утверждение');
      await loadDetails();
      await loadPlanVersions();
    } catch (error: any) {
      setMessage(`Ошибка: ${error.message}`);
    }
  };

  const handleReject = async (e: FormEvent) => {
    e.preventDefault();
    if (!token || !orderId || !rejectComment.trim()) {
      setMessage('Заполните комментарий с замечаниями');
      return;
    }
    try {
      const issues = rejectIssues.filter((i) => i.trim());
      await apiFetch(
        `/executor/orders/${orderId}/plan/reject`,
        {
          method: 'POST',
          data: {
            comment: rejectComment,
            issues: issues.length > 0 ? issues : null,
          },
        },
        token
      );
      setShowRejectModal(false);
      setRejectComment('');
      setRejectIssues(['']);
      setMessage('План отклонен');
      await loadDetails();
    } catch (error: any) {
      setMessage(`Ошибка: ${error.message}`);
    }
  };

  const savePlanChanges = async () => {
    if (!token || !orderId || !planData) return;
    try {
      await apiFetch(
        `/executor/orders/${orderId}/plan/save`,
        {
          method: 'POST',
          data: {
            versionType: 'EXECUTOR_EDITED',
            plan: planData,
            comment: editComment || 'Изменения в плане',
          },
        },
        token
      );
      setMessage('Изменения сохранены');
      await loadPlanVersions();
    } catch (error: any) {
      setMessage(`Ошибка: ${error.message}`);
    }
  };

  // Кнопки действий доступны, если заказ взят в работу и есть план
  const canEditPlan = data?.executorAssignment && 
                      (data?.order?.status === 'EXECUTOR_ASSIGNED' || 
                       data?.order?.status === 'VISIT_SCHEDULED' ||
                       data?.order?.status === 'DOCUMENTS_IN_PROGRESS' ||
                       data?.order?.status === 'SUBMITTED') &&
                      (currentPlan || planData);

  return (
    <div className="space-y-3">
      <div className={cardClass}>
        <div className="flex items-center justify-between">
          <h3 className={sectionTitleClass}>Заказ исполнителя</h3>
          <div className="flex gap-2">
            {!data?.executorAssignment && (
              <>
                <button className={buttonClass} onClick={() => void handleAction('take')}>
                  Взять в работу
                </button>
                <button className={subtleButtonClass} onClick={() => void handleAction('decline')}>
                  Отказаться
                </button>
              </>
            )}
          </div>
        </div>
        {message && (
          <div className={`mt-2 rounded p-2 text-sm ${
            message.includes('Ошибка') ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'
          }`}>
            {message}
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className={cardClass}>
        <div className="flex gap-2 border-b border-slate-200">
          {(['info', 'files', 'plan', 'history'] as TabKey[]).map((t) => (
            <button
              key={t}
              className={`px-4 py-2 text-sm font-medium ${
                tab === t
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
              onClick={() => setTab(t)}
            >
              {t === 'info' ? 'Информация' : t === 'files' ? 'Файлы' : t === 'plan' ? 'План' : 'История'}
            </button>
          ))}
        </div>
      </div>

      {/* Info Tab */}
      {tab === 'info' && data?.order && (
        <div className={cardClass}>
          <div className="flex flex-wrap gap-2">
            <span className={badgeClass}>Статус: {data.order.status}</span>
            <span className={badgeClass}>Услуга: {data.order.serviceCode}</span>
            {data.order.complexity && (
              <span className={badgeClass}>Сложность: {data.order.complexity}</span>
            )}
          </div>
          <h4 className="mt-3 font-semibold">{data.order.title}</h4>
          {data.order.description && <p className="mt-2 text-sm">{data.order.description}</p>}
          {data.order.address && (
            <p className="mt-2 text-sm text-slate-600">Адрес: {data.order.address}</p>
          )}
          {data.order.totalPrice && (
            <p className="mt-2 text-sm font-semibold">Стоимость: {data.order.totalPrice} ₽</p>
          )}
          {data?.client && (
            <div className="mt-4 rounded border border-slate-200 bg-slate-50 p-3 text-sm">
              <p className="font-semibold">Клиент</p>
              <p>{data.client.fullName}</p>
              <p className="text-slate-600">{data.client.email}</p>
            </div>
          )}
        </div>
      )}

      {/* Files Tab */}
      {tab === 'files' && (
        <div className={cardClass}>
          <h4 className={sectionTitleClass}>Файлы</h4>
          {data?.files && data.files.length > 0 ? (
            <ul className="mt-3 space-y-2">
              {data.files.map((f) => (
                <li key={f.id} className="flex items-center justify-between rounded border border-slate-200 p-2">
                  <span className="font-mono text-sm">{f.filename}</span>
                  <a
                    className="text-blue-600 hover:underline"
                    href={`/api/v1/client/orders/${orderId}/files/${f.id}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Скачать
                  </a>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-sm text-slate-600">Файлы не загружены</p>
          )}
        </div>
      )}

      {/* Plan Tab */}
      {tab === 'plan' && (
        <div className="space-y-3">
          <div className={cardClass}>
            <div className="flex items-center justify-between">
              <h4 className={sectionTitleClass}>План заказа</h4>
              <div className="flex gap-2">
                <button
                  className={`${subtleButtonClass} ${planViewMode === 'json' ? 'bg-slate-100' : ''}`}
                  onClick={() => setPlanViewMode('json')}
                >
                  JSON
                </button>
                <button
                  className={`${subtleButtonClass} ${planViewMode === '3d' ? 'bg-slate-100' : ''}`}
                  onClick={() => setPlanViewMode('3d')}
                >
                  3D
                </button>
                {canEditPlan && (
                  <button
                    className={`${subtleButtonClass} ${planViewMode === 'edit' ? 'bg-slate-100' : ''}`}
                    onClick={() => {
                      setPlanViewMode('edit');
                      setIsEditing(true);
                    }}
                  >
                    Редактировать
                  </button>
                )}
              </div>
            </div>

            {/* Version selector */}
            {planVersions.length > 0 && (
              <div className="mt-3">
                <label className="text-sm text-slate-700">
                  Версия плана:
                  <select
                    className={`${inputClass} mt-1`}
                    value={currentPlan?.versionType || ''}
                    onChange={(e) => void loadPlan(e.target.value)}
                  >
                    {planVersions.map((v) => (
                      <option key={v.id} value={v.versionType}>
                        {v.versionType} {v.comment ? `- ${v.comment.substring(0, 30)}...` : ''}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
            )}

            {planViewMode === 'json' && (
              <div className="mt-3">
                {currentPlan ? (
                  <pre className="mt-2 max-h-96 overflow-auto whitespace-pre-wrap rounded border border-slate-200 bg-slate-50 p-3 text-xs">
                    {JSON.stringify(currentPlan, null, 2)}
                  </pre>
                ) : (
                  <p className="mt-2 text-sm text-slate-600">План не найден</p>
                )}
              </div>
            )}

            {planViewMode === '3d' && planData && (
              <div className="mt-3">
                <Plan3DViewer plan={planData} onPlanChange={handlePlanChange} />
              </div>
            )}

            {planViewMode === 'edit' && planData && (
              <div className="mt-3 space-y-3">
                <div className="rounded border border-blue-200 bg-blue-50 p-3 text-sm">
                  <p className="font-semibold text-blue-900">Режим редактирования</p>
                  <p className="mt-1 text-blue-700">
                    Красный — удаляемые элементы, Зеленый — новые, Желтый — изменяемые
                  </p>
                </div>
                <Plan3DViewer plan={planData} onPlanChange={handlePlanChange} />
                <form onSubmit={handleEdit} className="space-y-3">
                  <label className="text-sm text-slate-700">
                    Комментарий с описанием изменений (обязательно):
                    <textarea
                      className={`${textareaClass} mt-1`}
                      rows={4}
                      value={editComment}
                      onChange={(e) => setEditComment(e.target.value)}
                      placeholder="Опишите внесенные изменения..."
                      required
                    />
                  </label>
                  <div className="flex gap-2">
                    <button type="submit" className={buttonClass} disabled={!editComment.trim()}>
                      Отправить клиенту на утверждение
                    </button>
                    <button
                      type="button"
                      className={subtleButtonClass}
                      onClick={() => void savePlanChanges()}
                    >
                      Сохранить черновик
                    </button>
                    <button
                      type="button"
                      className={subtleButtonClass}
                      onClick={() => {
                        setIsEditing(false);
                        setPlanViewMode('3d');
                        setEditComment('');
                      }}
                    >
                      Отмена
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* Action buttons - показываем если заказ взят в работу */}
            {data?.executorAssignment && planViewMode !== 'edit' && (
              <div className="mt-4 rounded-lg border-2 border-blue-200 bg-blue-50 p-4">
                <p className="mb-3 text-sm font-semibold text-blue-900">Действия с планом:</p>
                <div className="flex flex-wrap gap-2">
                  <button
                    className={`${buttonClass} bg-green-600 hover:bg-green-700 text-white`}
                    onClick={() => setShowApproveModal(true)}
                    disabled={!currentPlan && !planData}
                    title={!currentPlan && !planData ? 'Сначала загрузите план' : 'Одобрить план клиента'}
                  >
                    ✓ Одобрить
                  </button>
                  <button
                    className={`${buttonClass} bg-yellow-600 hover:bg-yellow-700 text-white`}
                    onClick={() => {
                      if (!planData && currentPlan) {
                        setPlanData(currentPlan.plan);
                      }
                      setPlanViewMode('edit');
                      setIsEditing(true);
                    }}
                    disabled={!currentPlan && !planData}
                    title={!currentPlan && !planData ? 'Сначала загрузите план' : 'Отредактировать план'}
                  >
                    ✏️ Править
                  </button>
                  <button
                    className={`${buttonClass} bg-red-600 hover:bg-red-700 text-white`}
                    onClick={() => setShowRejectModal(true)}
                    title="Отклонить план с замечаниями"
                  >
                    ✗ Отклонить
                  </button>
                </div>
                {(!currentPlan && !planData) && (
                  <p className="mt-2 text-xs text-blue-700">
                    ⚠️ План не загружен. Загрузите план, чтобы выполнить действия.
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* History Tab */}
      {tab === 'history' && (
        <div className={cardClass}>
          <h4 className={sectionTitleClass}>История статусов</h4>
          {data?.statusHistory && data.statusHistory.length > 0 ? (
            <ul className="mt-3 space-y-2">
              {data.statusHistory.map((h, idx) => (
                <li key={`${h.status}-${idx}`} className="rounded border border-slate-200 bg-slate-50 p-3">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold">{h.status}</span>
                    <span className="text-xs text-slate-500">
                      {new Date(h.changedAt).toLocaleString()}
                    </span>
                  </div>
                  {h.comment && (
                    <p className="mt-1 text-sm text-slate-600">{h.comment}</p>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-sm text-slate-600">История пуста</p>
          )}
        </div>
      )}

      {/* Approve Modal */}
      {showApproveModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-full max-w-md rounded-lg bg-white p-6">
            <h3 className="text-lg font-semibold">Одобрить план</h3>
            <form onSubmit={handleApprove} className="mt-4 space-y-3">
              <label className="text-sm text-slate-700">
                Комментарий (необязательно):
                <textarea
                  className={`${textareaClass} mt-1`}
                  rows={3}
                  value={approveComment}
                  onChange={(e) => setApproveComment(e.target.value)}
                  placeholder="Добавьте комментарий..."
                />
              </label>
              <div className="flex gap-2">
                <button type="submit" className={buttonClass}>
                  Одобрить
                </button>
                <button
                  type="button"
                  className={subtleButtonClass}
                  onClick={() => {
                    setShowApproveModal(false);
                    setApproveComment('');
                  }}
                >
                  Отмена
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-full max-w-md rounded-lg bg-white p-6">
            <h3 className="text-lg font-semibold">Отклонить план</h3>
            <form onSubmit={handleReject} className="mt-4 space-y-3">
              <label className="text-sm text-slate-700">
                Комментарий с замечаниями (обязательно):
                <textarea
                  className={`${textareaClass} mt-1`}
                  rows={4}
                  value={rejectComment}
                  onChange={(e) => setRejectComment(e.target.value)}
                  placeholder="Опишите замечания..."
                  required
                />
              </label>
              <div className="text-sm text-slate-700">
                <p className="mb-2">Список замечаний (необязательно):</p>
                {rejectIssues.map((issue, idx) => (
                  <input
                    key={idx}
                    type="text"
                    className={`${inputClass} mb-2`}
                    value={issue}
                    onChange={(e) => {
                      const newIssues = [...rejectIssues];
                      newIssues[idx] = e.target.value;
                      setRejectIssues(newIssues);
                    }}
                    placeholder={`Замечание ${idx + 1}`}
                  />
                ))}
                <button
                  type="button"
                  className={subtleButtonClass}
                  onClick={() => setRejectIssues([...rejectIssues, ''])}
                >
                  + Добавить замечание
                </button>
              </div>
              <div className="flex gap-2">
                <button type="submit" className={`${buttonClass} bg-red-600 hover:bg-red-700`} disabled={!rejectComment.trim()}>
                  Отклонить
                </button>
                <button
                  type="button"
                  className={subtleButtonClass}
                  onClick={() => {
                    setShowRejectModal(false);
                    setRejectComment('');
                    setRejectIssues(['']);
                  }}
                >
                  Отмена
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExecutorOrderDetailsPage;
