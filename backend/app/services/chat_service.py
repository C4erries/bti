import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chat import ChatThread
from app.models.order import ExecutorAssignment, Order, OrderChatMessage
from app.models.user import User
from app.schemas.chat import CreateChatRequest
from app.schemas.orders import ChatMessageCreate


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
    if title:
        return title
    return "Новый чат"


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
    """Делегирование сообщения AI для обработки."""
    try:
        from app.services import ai_integration_service
        
        # Получаем контекст заказа если есть
        order_context = {}
        plan_data = None
        if chat.order_id:
            from app.models.order import Order
            order = db.get(Order, chat.order_id)
            if order:
                order_context = {
                    "order_id": str(order.id),
                    "order_title": order.title,
                    "order_status": order.status.value if hasattr(order.status, 'value') else str(order.status),
                }
                # Получаем последнюю версию плана если есть
                from app.services import order_service
                versions = order_service.get_plan_versions(db, order.id)
                if versions:
                    latest_version = versions[-1]
                    plan_data = latest_version.plan
        
        # Получаем историю чата
        history = list_chat_messages(db, chat)
        chat_history = []
        for msg in history[-10:]:  # Последние 10 сообщений
            chat_history.append({
                "role": "user" if msg.sender_type in ["CLIENT", "EXECUTOR"] else "assistant",
                "content": msg.message_text
            })
        
        # Получаем правила AI и статьи (можно расширить позже)
        ai_rules = []
        articles = []
        
        # Обрабатываем через AI
        ai_response = await ai_integration_service.process_chat_with_ai(
            message=user_message.message,
            plan_data=plan_data,
            order_context=order_context,
            chat_history=chat_history,
            ai_rules=ai_rules,
            articles=articles,
            user_profile=None
        )
        
        return add_message(db, chat, sender=None, sender_type="AI", text=ai_response)
    except Exception as e:
        # Fallback на заглушку при ошибке
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"AI chat error: {e}")
        ai_text = f"AI stub: {user_message.message}"
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
