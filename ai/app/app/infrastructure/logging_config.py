"""Настройка логирования для приложения."""

import logging
import sys
from typing import Optional


_logger: Optional[logging.Logger] = None


def setup_logging(
    level: int = logging.INFO,
    format_string: Optional[str] = None
) -> None:
    """
    Настраивает глобальное логирование для приложения.
    
    Args:
        level: Уровень логирования (по умолчанию INFO)
        format_string: Формат строки логирования (опционально)
    """
    global _logger
    
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=level,
        format=format_string,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    _logger = logging.getLogger("v2")


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Получает логгер для указанного модуля.
    
    Args:
        name: Имя модуля (если None, возвращает корневой логгер)
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    if name:
        return logging.getLogger(f"v2.{name}")
    return logging.getLogger("v2")

