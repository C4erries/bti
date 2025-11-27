import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models.order import Order, ExecutorAssignment
from app.schemas.chat import ClientChatThread, CreateChatRequest
from app.schemas.orders import ChatMessageCreate, ChatMessagePairResponse, OrderChatMessage
from app.services import chat_service

router = APIRouter(tags=["Client"])


@router.get("/client/chats", response_model=list[ClientChatThread])
def list_client_chats(db: Session = Depends(get_db_session), current_user=Depends(get_current_user)):
    chats = chat_service.list_client_chats(db, current_user.id)
    threads: list[ClientChatThread] = []
    for chat in chats:
        last_msg = chat_service.list_chat_messages(db, chat)[-1] if chat.messages else None
        threads.append(
            ClientChatThread(
                chatId=chat.id,
                serviceCode=chat.service_code,
                serviceTitle=chat.order.service.title if chat.order and chat.order.service else None,
                orderId=chat.order_id,
                orderStatus=chat.order.status.value if chat.order else None,
                lastMessageText=last_msg.message_text if last_msg else None,
                updatedAt=last_msg.created_at if last_msg else chat.updated_at,
            )
        )
    return threads


@router.post("/client/chats", response_model=ClientChatThread, status_code=201)
def create_chat(
    payload: CreateChatRequest,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    # validate order ownership if provided
    order_obj = None
    if payload.order_id:
        order_obj = db.get(Order, payload.order_id)
        if not order_obj or order_obj.client_id != current_user.id:
            raise HTTPException(status_code=403, detail="Order not found or not yours")
    chat = chat_service.create_chat(db, client=current_user, payload=payload, order=order_obj)
    last_msg = chat_service.list_chat_messages(db, chat)[-1] if chat.messages else None
    return ClientChatThread(
        chatId=chat.id,
        serviceCode=chat.service_code,
        serviceTitle=chat.order.service.title if chat.order and chat.order.service else None,
        orderId=chat.order_id,
        orderStatus=chat.order.status.value if chat.order else None,
        lastMessageText=last_msg.message_text if last_msg else None,
        updatedAt=last_msg.created_at if last_msg else chat.updated_at,
    )


def _check_chat_access(db: Session, chat, user):
    try:
        chat_service.ensure_access(chat, user, db)
    except HTTPException:
        raise


def _sender_type(user) -> str:
    if user.is_admin:
        return "ADMIN"
    if user.executor_profile:
        return "EXECUTOR"
    return "CLIENT"


@router.get("/chats/{chat_id}/messages", response_model=list[OrderChatMessage])
def list_messages(
    chat_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    chat = chat_service.get_chat(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    _check_chat_access(db, chat, current_user)
    messages = chat_service.list_chat_messages(db, chat)
    return [OrderChatMessage.model_validate(m) for m in messages]


@router.post("/chats/{chat_id}/messages", response_model=ChatMessagePairResponse)
def post_message(
    chat_id: uuid.UUID,
    payload: ChatMessageCreate,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    chat = chat_service.get_chat(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    _check_chat_access(db, chat, current_user)
    user_msg = chat_service.add_message(db, chat, sender=current_user, sender_type=_sender_type(current_user), text=payload.message)
    ai_msg = chat_service.delegate_to_ai(db, chat, payload)
    return ChatMessagePairResponse(userMessage=user_msg, aiMessage=ai_msg)


def _ensure_order_access(order: Order, user, db: Session):
    if user.is_admin or order.client_id == user.id:
        return
    assignment = db.scalar(
        select(ExecutorAssignment).where(
            ExecutorAssignment.order_id == order.id,
            ExecutorAssignment.executor_id == user.id,
        )
    )
    if assignment:
        return
    raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/orders/{order_id}/chat", response_model=list[OrderChatMessage])
def order_chat_messages(
    order_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    _ensure_order_access(order, current_user, db)
    chat = chat_service.get_or_create_order_chat(db, order, client=order.client)
    messages = chat_service.list_chat_messages(db, chat)
    return [OrderChatMessage.model_validate(m) for m in messages]


@router.post("/orders/{order_id}/chat", response_model=ChatMessagePairResponse)
def post_order_chat_message(
    order_id: uuid.UUID,
    payload: ChatMessageCreate,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    _ensure_order_access(order, current_user, db)
    chat = chat_service.get_or_create_order_chat(db, order, client=order.client)
    user_msg = chat_service.add_message(
        db, chat, sender=current_user, sender_type=_sender_type(current_user), text=payload.message
    )
    ai_msg = chat_service.delegate_to_ai(db, chat, payload)
    return ChatMessagePairResponse(userMessage=user_msg, aiMessage=ai_msg)
