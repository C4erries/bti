from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthTokenResponse(BaseModel):
    access_token: str = Field(alias="accessToken")
    token_type: str = Field(default="Bearer", alias="tokenType")

    model_config = ConfigDict(populate_by_name=True)


class CurrentUserResponse(BaseModel):
    user: "User"
    is_client: bool = Field(alias="isClient")
    is_executor: bool = Field(alias="isExecutor")
    is_admin: bool = Field(alias="isAdmin")

    model_config = ConfigDict(populate_by_name=True)


from app.schemas.user import User  # noqa: E402

CurrentUserResponse.model_rebuild()
