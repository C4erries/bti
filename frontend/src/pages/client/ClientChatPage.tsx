import { useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { apiFetch } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import {
  badgeClass,
  buttonClass,
  cardClass,
  sectionTitleClass,
  subtleButtonClass,
  textareaClass,
} from '../../components/ui';
import type { ChatMessagePairResponse, Order, OrderChatMessage } from '../../types';

const ClientChatPage = () => {
  const { chatId } = useParams();
  const { token } = useAuth();
  const [messages, setMessages] = useState<OrderChatMessage[]>([]);
  const [order, setOrder] = useState<Order | null>(null);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatId && token) {
      void Promise.all([loadChat(), loadOrder()]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chatId, token]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadChat = async () => {
    if (!chatId || !token) return;
    try {
      const data = await apiFetch<OrderChatMessage[]>(`/orders/${chatId}/chat`, {}, token);
      setMessages(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить чат');
    }
  };

  const loadOrder = async () => {
    if (!chatId || !token) return;
    try {
      const data = await apiFetch<Order>(`/client/orders/${chatId}`, {}, token);
      setOrder(data);
    } catch {
      setOrder(null);
    }
  };

  const sendMessage = async () => {
    if (!chatId || !token || !input.trim()) return;
    setLoading(true);
    try {
      const data = await apiFetch<ChatMessagePairResponse>(
        `/orders/${chatId}/chat`,
        { method: 'POST', data: { message: input } },
        token,
      );
      const newMessages = [
        ...(data.userMessage ? [data.userMessage] : []),
        ...(data.aiMessage ? [data.aiMessage] : []),
      ];
      setMessages((prev) => [...prev, ...newMessages]);
      setInput('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка отправки');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className={cardClass}>
        <div className="flex items-center justify-between">
          <div>
            <h3 className={sectionTitleClass}>Чат</h3>
            {order && (
              <div className="mt-1 flex flex-wrap gap-2 text-sm">
                <span className={badgeClass}>{order.serviceTitle || order.serviceCode}</span>
                <span className={badgeClass}>Статус: {order.status}</span>
              </div>
            )}
          </div>
          <div className="flex gap-2">
            <button className={subtleButtonClass} onClick={() => void loadChat()}>
              Обновить
            </button>
            {order && (
              <Link className={subtleButtonClass} to={`/client/orders/${order.id}`}>
                К заказу
              </Link>
            )}
          </div>
        </div>
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      </div>

      <div className={cardClass}>
        <div className="flex flex-col gap-3">
          <div className="max-h-[60vh] overflow-y-auto space-y-2">
            {messages.length === 0 && (
              <p className="text-sm text-slate-600">Пока нет сообщений. Напишите первый запрос.</p>
            )}
            {messages.map((m, idx) => (
              <div
                key={`${m.createdAt}-${idx}`}
                className={`rounded border border-slate-200 p-2 ${
                  m.senderType === 'AI' ? 'bg-slate-50' : 'bg-white'
                }`}
              >
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <span>{m.senderType || 'USER'}</span>
                  {m.createdAt && <span>{new Date(m.createdAt).toLocaleString()}</span>}
                </div>
                <p className="mt-1 whitespace-pre-wrap text-sm">{m.messageText}</p>
              </div>
            ))}
            <div ref={bottomRef} />
          </div>
          <div className="space-y-2">
            <textarea
              className={textareaClass}
              rows={3}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Введите сообщение"
            />
            <div className="flex items-center gap-2">
              <button className={buttonClass} onClick={() => void sendMessage()} disabled={loading}>
                Отправить
              </button>
              <button className={subtleButtonClass} onClick={() => setInput('')}>
                Очистить
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ClientChatPage;
