"""Менеджер WebSocket подключений для чатов"""
from __future__ import annotations

import uuid
from typing import Dict, Set

from fastapi import WebSocket


class ConnectionManager:
    """Менеджер WebSocket подключений для чатов"""
    
    def __init__(self):
        # chat_id -> Set[WebSocket]
        self.active_connections: Dict[uuid.UUID, Set[WebSocket]] = {}
        # websocket -> (user_id, chat_id)
        self.connection_info: Dict[WebSocket, tuple[uuid.UUID, uuid.UUID]] = {}
    
    async def connect(self, websocket: WebSocket, chat_id: uuid.UUID, user_id: uuid.UUID):
        """Подключить пользователя к чату"""
        await websocket.accept()
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = set()
        self.active_connections[chat_id].add(websocket)
        self.connection_info[websocket] = (user_id, chat_id)
    
    def disconnect(self, websocket: WebSocket):
        """Отключить пользователя"""
        if websocket in self.connection_info:
            user_id, chat_id = self.connection_info[websocket]
            if chat_id in self.active_connections:
                self.active_connections[chat_id].discard(websocket)
                if not self.active_connections[chat_id]:
                    del self.active_connections[chat_id]
            del self.connection_info[websocket]
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Отправить сообщение конкретному подключению"""
        try:
            await websocket.send_json(message)
        except Exception:
            # Соединение закрыто, удаляем его
            self.disconnect(websocket)
    
    async def broadcast_to_chat(
        self, 
        message: dict, 
        chat_id: uuid.UUID, 
        exclude: WebSocket | None = None
    ):
        """Отправить сообщение всем подключенным к чату (кроме exclude)"""
        if chat_id not in self.active_connections:
            return
        
        disconnected = set()
        for connection in self.active_connections[chat_id]:
            if connection == exclude:
                continue
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        
        # Удаляем отключенные соединения
        for conn in disconnected:
            self.disconnect(conn)
    
    def get_chat_connections_count(self, chat_id: uuid.UUID) -> int:
        """Получить количество активных подключений к чату"""
        return len(self.active_connections.get(chat_id, set()))


# Глобальный экземпляр менеджера
manager = ConnectionManager()

