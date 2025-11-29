from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict


class Texture(BaseModel):
    id: uuid.UUID
    handle: str
    url: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TextureCreateResponse(Texture):
    pass
