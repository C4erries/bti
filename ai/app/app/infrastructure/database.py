"""Настройка подключения к базе данных."""

from typing import Optional
from sqlalchemy import create_engine, Engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import asynccontextmanager

Base = declarative_base()

# Глобальные переменные для движков
_sync_engine: Optional[Engine] = None
_async_engine: Optional[AsyncEngine] = None
_async_session_factory: Optional[sessionmaker] = None


def get_sync_engine(database_url: str) -> Engine:
    """
    Получает синхронный движок БД.
    
    Args:
        database_url: URL подключения к БД
        
    Returns:
        Engine: Синхронный движок SQLAlchemy
    """
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = create_engine(database_url, echo=False)
    return _sync_engine


def get_async_engine(database_url: str) -> AsyncEngine:
    """
    Получает асинхронный движок БД.
    
    Args:
        database_url: URL подключения к БД (asyncpg для PostgreSQL, aiosqlite для SQLite)
        
    Returns:
        AsyncEngine: Асинхронный движок SQLAlchemy
    """
    global _async_engine, _async_session_factory
    if _async_engine is None:
        _async_engine = create_async_engine(database_url, echo=False)
        _async_session_factory = sessionmaker(
            _async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    return _async_engine


@asynccontextmanager
async def get_async_session(database_url: str):
    """
    Контекстный менеджер для получения асинхронной сессии БД.
    
    Args:
        database_url: URL подключения к БД
        
    Yields:
        AsyncSession: Асинхронная сессия БД
    """
    engine = get_async_engine(database_url)
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def create_tables(engine: Engine):
    """
    Создает все таблицы в БД.
    
    Args:
        engine: Движок БД
    """
    Base.metadata.create_all(engine)


async def create_tables_async(engine: AsyncEngine):
    """
    Создает все таблицы в БД асинхронно.
    
    Args:
        engine: Асинхронный движок БД
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

