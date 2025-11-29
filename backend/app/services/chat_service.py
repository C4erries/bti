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
    payload = CreateChatRequest(serviceCode=order.service_code, title=order.title, orderId=order.id)
    return create_chat(db, client=client, payload=payload)


def list_client_chats(db: Session, client_id: uuid.UUID) -> list[ChatThread]:
    return list(
        db.scalars(
            select(ChatThread).where(ChatThread.client_id == client_id).order_by(ChatThread.updated_at.desc())
        )
    )


def _resolve_title(db: Session, service_code: int | None, title: str | None) -> str:
    if title:
        return title
    if service_code:
        from app.models.directory import Service

        svc = db.get(Service, service_code)
        if svc:
            return f"Помощь по услуге {svc.title}"
    return "Чат с поддержкой"


def create_chat(db: Session, client: User, payload: CreateChatRequest, order: Order | None = None) -> ChatThread:
    title = _resolve_title(db, payload.service_code, payload.title)
    chat = ChatThread(
        client_id=client.id,
        order_id=payload.order_id or (order.id if order else None),
        service_code=payload.service_code,
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


def delegate_to_ai(db: Session, chat: ChatThread, user_message: ChatMessageCreate) -> OrderChatMessage | None:
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
