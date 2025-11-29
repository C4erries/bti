import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.params import Form
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.schemas.texture import Texture as TextureSchema
from app.services import texture_service


router = APIRouter(prefix="/textures", tags=["textures"])


@router.get("", response_model=list[TextureSchema], summary="Список доступных текстур")
def list_textures(db: Session = Depends(get_db)) -> list[TextureSchema]:
    textures = texture_service.list_textures(db)
    return [
        TextureSchema.model_validate(
            {
                "id": t.id,
                "handle": t.handle,
                "description": t.description,
                "url": f"{settings.static_url}/textures/{t.filename}",
            }
        )
        for t in textures
    ]


@router.get("/{texture_id}", response_model=TextureSchema, summary="Получить текстуру по id")
def get_texture(texture_id: uuid.UUID, db: Session = Depends(get_db)) -> TextureSchema:
    texture = texture_service.get_texture(db, texture_id)
    if not texture:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Texture not found")
    return TextureSchema.model_validate(
        {
            "id": texture.id,
            "handle": texture.handle,
            "description": texture.description,
            "url": f"{settings.static_url}/textures/{texture.filename}",
        }
    )


@router.post(
    "",
    response_model=TextureSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Загрузить новую текстуру",
)
def create_texture(
    handle: str = Form(..., description="Уникальный код текстуры"),
    description: str | None = Form(None, description="Описание текстуры"),
    file: UploadFile = File(..., description="Файл текстуры"),
    db: Session = Depends(get_db),
) -> TextureSchema:
    existing = texture_service.get_texture_by_handle(db, handle)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Handle already exists")

    texture = texture_service.create_texture(db, handle=handle, upload=file, description=description)
    return TextureSchema.model_validate(
        {
            "id": texture.id,
            "handle": texture.handle,
            "description": texture.description,
            "url": f"{settings.static_url}/textures/{texture.filename}",
        }
    )
