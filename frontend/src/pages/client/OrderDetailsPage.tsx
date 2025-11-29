import { useEffect, useState, type FormEvent } from 'react';
import { Link, useParams } from 'react-router-dom';
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
  AiAnalysis,
  ChatMessagePairResponse,
  Order,
  OrderChatMessage,
  OrderFile,
  OrderPlanVersion,
  OrderStatusHistoryItem,
  PlanGeometry,
} from '../../types';

type TabKey = 'info' | 'files' | 'plan' | 'history' | 'chat';
type PlanViewMode = 'json' | '3d';

const ClientOrderDetailsPage = () => {
  const { orderId } = useParams();
  const { token } = useAuth();
  const [order, setOrder] = useState<Order | null>(null);
  const [files, setFiles] = useState<OrderFile[]>([]);
  const [statusHistory, setStatusHistory] = useState<OrderStatusHistoryItem[]>([]);
  const [plan, setPlan] = useState<OrderPlanVersion | null>(null);
  const [planData, setPlanData] = useState<PlanGeometry | null>(null);
  const [planVersionType, setPlanVersionType] = useState<'ORIGINAL' | 'MODIFIED'>('MODIFIED');
  const [planContent, setPlanContent] = useState('{}');
  const [planViewMode, setPlanViewMode] = useState<PlanViewMode>('json');
  const [chatMessages, setChatMessages] = useState<OrderChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [analysis, setAnalysis] = useState<AiAnalysis | null>(null);
  const [fileToUpload, setFileToUpload] = useState<File | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [tab, setTab] = useState<TabKey>('info');

  useEffect(() => {
    if (orderId && token) {
      void Promise.all([
        loadOrder(),
        loadFiles(),
        loadPlan(),
        loadHistory(),
        loadChat(),
        loadAnalysis(),
      ]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orderId, token]);

  const loadOrder = async () => {
    if (!orderId || !token) return;
    const data = await apiFetch<Order>(`/client/orders/${orderId}`, {}, token);
    setOrder(data);
  };

  const loadFiles = async () => {
    if (!orderId || !token) return;
    const data = await apiFetch<OrderFile[]>(`/client/orders/${orderId}/files`, {}, token);
    setFiles(data);
  };

  const loadPlan = async () => {
    if (!orderId || !token) return;
    try {
      const data = await apiFetch<OrderPlanVersion>(`/client/orders/${orderId}/plan`, {}, token);
      setPlan(data);
      const geometry = data.plan as unknown;
      if (geometry && typeof geometry === 'object' && (geometry as any).meta && (geometry as any).elements) {
        setPlanData(geometry as PlanGeometry);
        setPlanContent(JSON.stringify(geometry, null, 2));
      } else {
        setPlanData(null);
        setPlanContent(JSON.stringify(data.plan ?? {}, null, 2));
      }
    } catch {
      setPlan(null);
      setPlanData(null);
    }
  };

  const loadHistory = async () => {
    if (!orderId || !token) return;
    try {
      const data = await apiFetch<OrderStatusHistoryItem[]>(
        `/client/orders/${orderId}/status-history`,
        {},
        token,
      );
      setStatusHistory(data);
    } catch {
      setStatusHistory([]);
    }
  };

  const loadChat = async () => {
    if (!orderId || !token) return;
    try {
      const data = await apiFetch<OrderChatMessage[]>(`/orders/${orderId}/chat`, {}, token);
      setChatMessages(data);
    } catch {
      setChatMessages([]);
    }
  };

  const loadAnalysis = async () => {
    if (!orderId || !token) return;
    try {
      const data = await apiFetch<AiAnalysis>(`/client/orders/${orderId}/ai/analysis`, {}, token);
      setAnalysis(data);
    } catch {
      setAnalysis(null);
    }
  };

  const uploadFile = async (e: FormEvent) => {
    e.preventDefault();
    if (!orderId || !token || !fileToUpload) return;
    const formData = new FormData();
    formData.append('file', fileToUpload);
    await apiFetch<OrderFile>(
      `/client/orders/${orderId}/files`,
      {
        method: 'POST',
        data: formData,
        isFormData: true,
      },
      token,
    );
    setMessage('Файл загружен');
    setFileToUpload(null);
    await loadFiles();
  };

  const savePlan = async (e: FormEvent) => {
    e.preventDefault();
    if (!orderId || !token) return;
    try {
      const parsed = planContent ? JSON.parse(planContent) : {};
      await apiFetch<OrderPlanVersion>(
        `/client/orders/${orderId}/plan/changes`,
        {
          method: 'POST',
          data: { versionType: planVersionType, plan: parsed },
        },
        token,
      );
      setMessage('План обновлен');
      await loadPlan();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Ошибка обновления плана');
    }
  };

  const sendChat = async (e: FormEvent) => {
    e.preventDefault();
    if (!orderId || !token || !chatInput) return;
    try {
      const data = await apiFetch<ChatMessagePairResponse>(
        `/orders/${orderId}/chat`,
        {
          method: 'POST',
          data: { message: chatInput },
        },
        token,
      );
      const newMessages = [
        ...(data.userMessage ? [data.userMessage] : []),
        ...(data.aiMessage ? [data.aiMessage] : []),
      ];
      setChatMessages((prev) => [...prev, ...newMessages]);
      setChatInput('');
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Ошибка отправки сообщения');
    }
  };

  const requestAnalysis = async () => {
    if (!orderId || !token) return;
    try {
      await apiFetch(`/client/orders/${orderId}/ai/analyze`, { method: 'POST' }, token);
      await loadAnalysis();
      setMessage('Запрос на анализ отправлен');
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Ошибка анализа');
    }
  };

  const handlePlanChange = (updated: PlanGeometry) => {
    setPlanData(updated);
    setPlanContent(JSON.stringify(updated, null, 2));
  };

  return (
    <div className="space-y-4">
      <div className={cardClass}>
        <div className="flex items-center justify-between">
          <h3 className={sectionTitleClass}>Детали заказа</h3>
          <div className="flex gap-2">
            {(['info', 'files', 'plan', 'history', 'chat'] as TabKey[]).map((key) => (
              <button
                key={key}
                className={`${subtleButtonClass} ${tab === key ? 'bg-slate-100' : ''}`}
                onClick={() => setTab(key)}
              >
                {key === 'info' && 'Инфо'}
                {key === 'files' && 'Файлы'}
                {key === 'plan' && 'План'}
                {key === 'history' && 'История'}
                {key === 'chat' && 'Чат (AI)'}
              </button>
            ))}
            {orderId && (
              <Link className={subtleButtonClass} to={`/client/chat/${orderId}`}>
                Открыть в чате
              </Link>
            )}
          </div>
        </div>
        {message && <p className="mt-2 text-sm text-red-600">{message}</p>}
      </div>

      {tab === 'info' && (
        <div className={cardClass}>
          {order ? (
            <div className="space-y-2 text-sm">
              <div className="flex flex-wrap gap-2">
                <span className={badgeClass}>Статус: {order.status}</span>
                <span className={badgeClass}>Услуга: {order.title}</span>
              </div>
              <p className="font-semibold">{order.title}</p>
              <p>{order.description}</p>
              <p className="text-slate-600">Адрес: {order.address || '—'}</p>
              <pre className="mt-2 whitespace-pre-wrap text-xs">
                {JSON.stringify(order, null, 2)}
              </pre>
            </div>
          ) : (
            <p className="text-sm text-slate-600">Нет данных</p>
          )}
        </div>
      )}

      {tab === 'files' && (
        <div className={cardClass}>
          <div className="flex items-center justify-between">
            <h4 className={sectionTitleClass}>Файлы</h4>
            <form className="flex items-center gap-2" onSubmit={uploadFile}>
              <input type="file" onChange={(e) => setFileToUpload(e.target.files?.[0] ?? null)} />
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
            <p className="text-sm text-slate-600">Файлы отсутствуют</p>
          )}
        </div>
      )}

      {tab === 'plan' && (
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
            </div>
          </div>

          {planViewMode === 'json' && (
            <>
              {plan ? (
                <pre className="mt-2 whitespace-pre-wrap text-xs">
                  {JSON.stringify(plan, null, 2)}
                </pre>
              ) : (
                <p className="text-sm text-slate-600">План не найден</p>
              )}
              <form className="mt-3 space-y-2" onSubmit={savePlan}>
                <label className="text-sm text-slate-700">
                  Версия
                  <select
                    className={`${inputClass} mt-1`}
                    value={planVersionType}
                    onChange={(e) => setPlanVersionType(e.target.value as 'ORIGINAL' | 'MODIFIED')}
                  >
                    <option value="ORIGINAL">ORIGINAL</option>
                    <option value="MODIFIED">MODIFIED</option>
                  </select>
                </label>
                <label className="text-sm text-slate-700">
                  JSON
                  <textarea
                    className={`${textareaClass} mt-1`}
                    rows={8}
                    value={planContent}
                    onChange={(e) => setPlanContent(e.target.value)}
                  />
                </label>
                <button type="submit" className={buttonClass}>
                  Сохранить изменения
                </button>
              </form>
            </>
          )}

          {planViewMode === '3d' && planData ? (
            <div className="mt-3">
              <Plan3DViewer plan={planData} onPlanChange={handlePlanChange} />
            </div>
          ) : null}
          {planViewMode === '3d' && !planData && (
            <p className="mt-2 text-sm text-slate-600">Нет данных плана для отображения.</p>
          )}
        </div>
      )}

      {tab === 'history' && (
        <div className={cardClass}>
          <h4 className={sectionTitleClass}>История статусов</h4>
          {statusHistory.length ? (
            <ul className="mt-2 space-y-1 text-sm">
              {statusHistory.map((h, idx) => (
                <li key={`${h.status}-${idx}`} className="rounded bg-slate-50 px-2 py-1">
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
      )}

      {tab === 'chat' && (
        <div className="grid gap-4 lg:grid-cols-2">
          <div className={cardClass}>
            <div className="flex items-center justify-between">
              <h4 className={sectionTitleClass}>Чат с AI</h4>
              <button className={subtleButtonClass} onClick={() => void loadChat()}>
                Обновить
              </button>
            </div>
            <div className="mt-2 space-y-2 text-sm">
              {chatMessages.length ? (
                chatMessages.map((m, idx) => (
                  <div key={`${m.createdAt}-${idx}`} className="rounded border border-slate-200 p-2">
                    <div className="flex items-center justify-between text-xs text-slate-500">
                      <span>{m.senderType || 'USER'}</span>
                      {m.createdAt && <span>{new Date(m.createdAt).toLocaleString()}</span>}
                    </div>
                    <p className="mt-1 whitespace-pre-wrap">{m.messageText}</p>
                  </div>
                ))
              ) : (
                <p className="text-slate-600">Сообщений пока нет</p>
              )}
            </div>
            <form className="mt-3 space-y-2" onSubmit={sendChat}>
              <textarea
                className={textareaClass}
                rows={3}
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Ваш вопрос"
              />
              <button type="submit" className={buttonClass}>
                Отправить
              </button>
            </form>
          </div>

          <div className={cardClass}>
            <div className="flex items-center justify-between">
              <h4 className={sectionTitleClass}>AI анализ</h4>
              <button className={subtleButtonClass} onClick={() => void requestAnalysis()}>
                Запросить анализ
              </button>
            </div>
            {analysis ? (
              <pre className="mt-2 whitespace-pre-wrap text-xs">
                {JSON.stringify(analysis, null, 2)}
              </pre>
            ) : (
              <p className="mt-2 text-sm text-slate-600">Нет анализа</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ClientOrderDetailsPage;
