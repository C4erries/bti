from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreateChatRequest(BaseModel):
    service_code: int = Field(alias="serviceCode")
    title: str | None = None
    order_id: uuid.UUID | None = Field(default=None, alias="orderId")
    first_message: str | None = Field(default=None, alias="firstMessage")

    model_config = ConfigDict(populate_by_name=True)


class ClientChatThread(BaseModel):
    chat_id: uuid.UUID = Field(alias="chatId")
    service_code: int | None = Field(default=None, alias="serviceCode")
    service_title: str | None = Field(default=None, alias="serviceTitle")
    order_id: uuid.UUID | None = Field(default=None, alias="orderId")
    order_status: str | None = Field(default=None, alias="orderStatus")
    last_message_text: str | None = Field(default=None, alias="lastMessageText")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
