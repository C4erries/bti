import { useEffect, useMemo, useState } from 'react';
import { Link, NavLink, Outlet, useNavigate, useParams } from 'react-router-dom';
import { apiFetch } from '../api/client';
import { useAuth } from '../context/AuthContext';
import {
  badgeClass,
  buttonClass,
  cardClass,
  inputClass,
  sectionTitleClass,
  subtleButtonClass,
  textareaClass,
} from '../components/ui';
import type { ClientChatThread, Service } from '../types';

const normalizeThread = (t: Partial<ClientChatThread> & Record<string, any>): ClientChatThread => ({
  chatId: t.chatId || (t as any).id || (t as any).orderId || crypto.randomUUID(),
  orderId: t.orderId ?? (t as any).order_id ?? null,
  serviceCode: Number(t.serviceCode ?? 0),
  serviceTitle: t.serviceTitle ?? (t as any).title ?? 'Без названия',
  orderStatus: t.orderStatus,
  lastMessageText: t.lastMessageText ?? (t as any).lastMessage ?? null,
  updatedAt: t.updatedAt ?? (t as any).createdAt ?? new Date().toISOString(),
});

const SidebarItem = ({ chat, isActive }: { chat: ClientChatThread; isActive: boolean }) => (
  <NavLink
    to={`/client/chat/${chat.chatId}`}
    className={`block rounded-md px-3 py-2 text-sm hover:bg-slate-200 ${isActive ? 'bg-slate-200' : ''}`}
  >
    <div className="flex items-center justify-between">
      <span className="font-medium">{chat.serviceTitle}</span>
      {chat.orderStatus && <span className={badgeClass}>{chat.orderStatus}</span>}
    </div>
    <p className="text-xs text-slate-600 truncate">{chat.lastMessageText || 'Новый чат'}</p>
  </NavLink>
);

const ClientChatShell = () => {
  const { token } = useAuth();
  const [chats, setChats] = useState<ClientChatThread[]>([]);
  const [services, setServices] = useState<Service[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showNew, setShowNew] = useState(false);
  const [newChat, setNewChat] = useState({ serviceCode: '', title: '', firstMessageText: '' });
  const navigate = useNavigate();
  const params = useParams();

  const activeChatId = useMemo(() => params.chatId || '', [params.chatId]);

  useEffect(() => {
    void refreshChats();
    void loadServices();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const refreshChats = async () => {
    if (!token) return;
    try {
      const data = await apiFetch<any[]>('/client/chats', {}, token);
      setChats(data.map((item) => normalizeThread(item)));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить чаты');
    }
  };

  const loadServices = async () => {
    try {
      const data = await apiFetch<Service[]>('/services');
      setServices(data);
    } catch {
      // ignore
    }
  };

  const createChat = async () => {
    if (!token || !newChat.serviceCode) return;
    setLoading(true);
    try {
      const created = await apiFetch<ClientChatThread>(
        '/client/chats',
        {
          method: 'POST',
          data: {
            serviceCode: Number(newChat.serviceCode),
            title: newChat.title || undefined,
            firstMessageText: newChat.firstMessageText || undefined,
          },
        },
        token,
      );
      const normalized = normalizeThread(created);
      setChats((prev) => [normalized, ...prev]);
      setShowNew(false);
      setNewChat({ serviceCode: '', title: '', firstMessageText: '' });
      navigate(`/client/chat/${normalized.chatId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось создать чат');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid min-h-[80vh] grid-cols-1 gap-4 lg:grid-cols-[320px_1fr]">
      <aside className="rounded-xl border border-slate-200 bg-white p-3">
        <div className="flex items-center justify-between">
          <h3 className={sectionTitleClass}>Чаты</h3>
          <button className={subtleButtonClass} onClick={() => void refreshChats()}>
            ↻
          </button>
        </div>
        <button className={`${buttonClass} mt-3 w-full justify-center`} onClick={() => setShowNew((v) => !v)}>
          Новый чат
        </button>
        {showNew && (
          <div className={`${cardClass} mt-3 bg-slate-50`}>
            <div className="space-y-2">
              <label className="text-sm text-slate-700">
                Услуга
                <select
                  className={`${inputClass} mt-1`}
                  value={newChat.serviceCode}
                  onChange={(e) => setNewChat((p) => ({ ...p, serviceCode: e.target.value }))}
                >
                  <option value="">Выберите</option>
                  {services.map((s) => (
                    <option key={s.code} value={s.code}>
                      {s.title}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-sm text-slate-700">
                Заголовок (опционально)
                <input
                  className={`${inputClass} mt-1`}
                  value={newChat.title}
                  onChange={(e) => setNewChat((p) => ({ ...p, title: e.target.value }))}
                />
              </label>
              <label className="text-sm text-slate-700">
                Первое сообщение (опционально)
                <textarea
                  className={`${textareaClass} mt-1`}
                  rows={3}
                  value={newChat.firstMessageText}
                  onChange={(e) =>
                    setNewChat((p) => ({ ...p, firstMessageText: e.target.value }))
                  }
                />
              </label>
              <button
                className={buttonClass}
                onClick={() => void createChat()}
                disabled={loading || !newChat.serviceCode}
              >
                Создать
              </button>
            </div>
          </div>
        )}

        <div className="mt-4 space-y-1">
          {chats.map((chat) => (
            <SidebarItem key={chat.chatId} chat={chat} isActive={chat.chatId === activeChatId} />
          ))}
          {chats.length === 0 && (
            <p className="text-sm text-slate-600">Нет чатов. Создайте новый чат.</p>
          )}
        </div>

        <div className="mt-6 border-t border-slate-200 pt-3 text-sm">
          <p className="font-semibold text-slate-800">Другие разделы</p>
          <div className="mt-2 flex flex-col gap-2">
            <Link className={subtleButtonClass} to="/client/orders">
              Мои заказы
            </Link>
            <Link className={subtleButtonClass} to="/client/services">
              Каталог услуг
            </Link>
            <Link className={subtleButtonClass} to="/client/orders/new">
              Создать заказ
            </Link>
          </div>
        </div>
        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      </aside>

      <section className="space-y-4">
        <Outlet />
      </section>
    </div>
  );
};

export default ClientChatShell;
