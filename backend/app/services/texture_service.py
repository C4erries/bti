import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.texture import Texture


def list_textures(db: Session) -> list[Texture]:
    return db.scalars(select(Texture)).all()


def get_texture(db: Session, texture_id: uuid.UUID) -> Texture | None:
    return db.get(Texture, texture_id)


def get_texture_by_handle(db: Session, handle: str) -> Texture | None:
    return db.scalar(select(Texture).where(Texture.handle == handle))


def save_texture_file(upload: UploadFile, filename: str) -> Path:
    textures_dir = Path(settings.static_root) / "textures"
    textures_dir.mkdir(parents=True, exist_ok=True)
    file_path = textures_dir / filename
    with file_path.open("wb") as out:
        content = upload.file.read()
        out.write(content)
    return file_path


def create_texture(
    db: Session,
    *,
    handle: str,
    upload: UploadFile,
    description: str | None = None,
) -> Texture:
    existing = get_texture_by_handle(db, handle)
    if existing:
        return existing

    suffix = Path(upload.filename).suffix or ".bin"
    filename = f"{handle}{suffix}"
    file_path = save_texture_file(upload, filename)

    texture = Texture(
        handle=handle,
        filename=file_path.name,
        description=description,
        mime_type=upload.content_type,
    )
    db.add(texture)
    db.commit()
    db.refresh(texture)
    return texture
