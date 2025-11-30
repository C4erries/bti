import logging
import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.chat import ChatThread
from app.models.order import ExecutorAssignment, Order, OrderChatMessage
from app.models.user import User
from app.schemas.chat import CreateChatRequest
from app.schemas.orders import ChatMessageCreate
from app.services.gemini_client import generate_text
from app.services.plan_description import summarize_plan


def get_chat(db: Session, chat_id: uuid.UUID) -> ChatThread | None:
    return db.get(ChatThread, chat_id)


def get_or_create_order_chat(db: Session, order: Order, client: User) -> ChatThread:
    chat = db.scalar(select(ChatThread).where(ChatThread.order_id == order.id))
    if chat:
        return chat
    payload = CreateChatRequest(title=order.title, orderId=order.id)
    return create_chat(db, client=client, payload=payload)


def list_client_chats(db: Session, client_id: uuid.UUID) -> list[ChatThread]:
    return list(
        db.scalars(
            select(ChatThread).where(ChatThread.client_id == client_id).order_by(ChatThread.updated_at.desc())
        )
    )


def _resolve_title(title: str | None) -> str:
    return title or "New chat"


def create_chat(db: Session, client: User, payload: CreateChatRequest, order: Order | None = None) -> ChatThread:
    title = _resolve_title(payload.title)
    chat = ChatThread(
        client_id=client.id,
        order_id=payload.order_id or (order.id if order else None),
        title=title,
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    if payload.first_message:
        add_message(
            db,
            chat=chat,
            sender=client,
            sender_type="CLIENT",
            text=payload.first_message,
        )
    return chat


def list_chat_messages(db: Session, chat: ChatThread) -> list[OrderChatMessage]:
    return list(
        db.scalars(
            select(OrderChatMessage)
            .where(OrderChatMessage.chat_id == chat.id)
            .order_by(OrderChatMessage.created_at)
        )
    )


def add_message(
    db: Session,
    chat: ChatThread,
    sender: User | None,
    sender_type: str,
    text: str,
) -> OrderChatMessage:
    msg = OrderChatMessage(
        chat_id=chat.id,
        order_id=chat.order_id,
        sender_id=sender.id if sender else None,
        sender_type=sender_type,
        message_text=text,
        created_at=datetime.utcnow(),
    )
    chat.updated_at = datetime.utcnow()
    db.add(msg)
    db.add(chat)
    db.commit()
    db.refresh(msg)
    return msg


async def delegate_to_ai(db: Session, chat: ChatThread, user_message: ChatMessageCreate) -> OrderChatMessage | None:
    """Delegate a chat message to Gemini using a minimal prompt."""
    from app.services import order_service

    logger = logging.getLogger(__name__)

    order_context_lines: list[str] = []
    plan_summary = None
    if chat.order_id:
        order = db.get(Order, chat.order_id)
        if order:
            status_value = order.status.value if hasattr(order.status, "value") else str(order.status)
            order_context_lines.append(f"ID заказа: {order.id}")
            order_context_lines.append(f"Статус: {status_value}")
            order_context_lines.append(f"Название: {order.title}")
            if order.address:
                order_context_lines.append(f"Адрес: {order.address}")
            if order.district_code:
                order_context_lines.append(f"Округ: {order.district_code}")
            if order.house_type_code:
                order_context_lines.append(f"Тип дома: {order.house_type_code}")

            versions = order_service.get_plan_versions(db, order.id)
            if versions:
                plan_summary = summarize_plan(versions[-1].plan)

    history = list_chat_messages(db, chat)
    history_limit = settings.chat_max_history or 10
    last_messages = history[-history_limit:] if history_limit > 0 else []
    history_lines = []
    for msg in last_messages:
        role = "Клиент" if msg.sender_type in ["CLIENT", "EXECUTOR"] else "Ассистент"
        history_lines.append(f"{role}: {msg.message_text}")
    history_text = "\n".join(history_lines) if history_lines else "История пуста."

    system_prompt = (
        "Ты помощник инженера БТИ. "
        "Отвечай кратко и по делу, опираясь на историю чата и краткий контекст заказа. "
        "Если данных не хватает, уточняй вопросы."
    )

    prompt_parts = []
    if order_context_lines:
        prompt_parts.append("Контекст заказа:\n" + "\n".join(order_context_lines))
    if plan_summary:
        prompt_parts.append("Описание плана:\n" + plan_summary)
    prompt_parts.append("История чата:\n" + history_text)
    prompt_parts.append(f"Новое сообщение пользователя:\n{user_message.message}")
    prompt_parts.append("Сформулируй ответ ассистента.")
    prompt = "\n\n".join(prompt_parts)

    fallback_text = "Сервис помощника временно недоступен. Попробуйте позже."
    ai_text = fallback_text
    try:
        response_text = await generate_text(
            system=system_prompt,
            prompt=prompt,
            temperature=settings.chat_temperature,
        )
        ai_text = response_text.strip() or fallback_text
    except Exception as exc:
        logger.error("AI chat error: %s", exc)
    return add_message(db, chat, sender=None, sender_type="AI", text=ai_text)


def ensure_access(chat: ChatThread, user: User, db: Session) -> None:
    if user.is_admin or user.is_superadmin:
        return
    if chat.client_id == user.id:
        return
    if chat.order_id:
        assignment = db.scalar(
            select(ExecutorAssignment).where(
                ExecutorAssignment.order_id == chat.order_id,
                ExecutorAssignment.executor_id == user.id,
            )
        )
        if assignment:
            return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
