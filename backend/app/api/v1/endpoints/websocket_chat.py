"""WebSocket endpoints для чатов"""
import json
import uuid
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import _get_user_from_token
from app.services import chat_service
from app.services.websocket_manager import manager
from app.schemas.orders import OrderChatMessage, ChatMessageCreate

router = APIRouter(tags=["WebSocket"])


async def authenticate_websocket(
    websocket: WebSocket,
    token: str,
    db: Session,
) -> Optional[tuple[uuid.UUID, "User"]]:
    """Аутентификация пользователя через WebSocket токен"""
    try:
        user = _get_user_from_token(db, token)
        return (user.id, user)
    except Exception:
        await websocket.close(code=1008, reason="Unauthorized")
        return None


@router.websocket("/ws/chat/{chat_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    chat_id: uuid.UUID,
    token: str = Query(..., description="JWT токен для аутентификации"),
):
    """
    WebSocket endpoint для чата.
    
    Подключение: ws://host/api/v1/ws/chat/{chat_id}?token=JWT_TOKEN
    
    Формат сообщений от клиента:
    {
        "type": "message",
        "message": "Текст сообщения",
        "delegate_to_ai": true/false
    }
    
    Формат сообщений от сервера:
    - history: {"type": "history", "messages": [...]}
    - new_message: {"type": "new_message", "message": {...}}
    - message_sent: {"type": "message_sent", "messageId": "uuid"}
    - error: {"type": "error", "message": "..."}
    """
    # Получаем сессию БД
    from app.db.session import SessionLocal
    db = SessionLocal()
    
    try:
        # Аутентификация
        auth_result = await authenticate_websocket(websocket, token, db)
        if not auth_result:
            return
        
        user_id, user = auth_result
        
        # Проверка доступа к чату
        chat = chat_service.get_chat(db, chat_id)
        if not chat:
            await websocket.close(code=1008, reason="Chat not found")
            return
        
        try:
            chat_service.ensure_access(chat, user, db)
        except Exception:
            await websocket.close(code=1008, reason="Access denied")
            return
        
        # Подключение
        await manager.connect(websocket, chat_id, user_id)
        
        # Отправляем историю сообщений при подключении
        messages = chat_service.list_chat_messages(db, chat)
        await websocket.send_json({
            "type": "history",
            "messages": [OrderChatMessage.model_validate(m).model_dump(mode="json") for m in messages]
        })
        
        # Определяем тип отправителя
        sender_type = "ADMIN" if (user.is_admin or user.is_superadmin) else ("EXECUTOR" if user.executor_profile else "CLIENT")
        
        # Основной цикл обработки сообщений
        while True:
            try:
                # Получаем сообщение от клиента
                data = await websocket.receive_json()
                
                if data.get("type") == "message":
                    message_text = data.get("message", "").strip()
                    if not message_text:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Message cannot be empty"
                        })
                        continue
                    
                    # Сохраняем сообщение в БД
                    user_msg = chat_service.add_message(
                        db, chat, sender=user, sender_type=sender_type, text=message_text
                    )
                    
                    # Отправляем сообщение всем подключенным к чату (кроме отправителя)
                    message_data = {
                        "type": "new_message",
                        "message": OrderChatMessage.model_validate(user_msg).model_dump(mode="json")
                    }
                    await manager.broadcast_to_chat(message_data, chat_id, exclude=websocket)
                    
                    # Отправляем подтверждение отправителю
                    await websocket.send_json({
                        "type": "message_sent",
                        "messageId": str(user_msg.id)
                    })
                    
                    # Если нужно, делегируем AI (асинхронно)
                    if data.get("delegate_to_ai", False):
                        ai_msg = await chat_service.delegate_to_ai(
                            db, chat, ChatMessageCreate(message=message_text)
                        )
                        if ai_msg:
                            ai_message_data = {
                                "type": "new_message",
                                "message": OrderChatMessage.model_validate(ai_msg).model_dump(mode="json")
                            }
                            await manager.broadcast_to_chat(ai_message_data, chat_id)
                
                elif data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {data.get('type')}"
                    })
                    
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Error processing message: {str(e)}"
                })
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)
        db.close()

