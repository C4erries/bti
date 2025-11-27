from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreateChatRequest(BaseModel):
    service_code: int = Field(alias="serviceCode")
    title: str | None = None
    first_message_text: str | None = Field(default=None, alias="firstMessageText")

    model_config = ConfigDict(populate_by_name=True)


class ClientChatThread(BaseModel):
    id: uuid.UUID
    service_code: int = Field(alias="serviceCode")
    service_title: str | None = Field(default=None, alias="serviceTitle")
    order_status: str = Field(alias="orderStatus")
    last_message_text: str | None = Field(default=None, alias="lastMessageText")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
