"""Клиент для работы с API CubiCasa5K."""

import os
from typing import Optional, Dict, Any
import httpx
from ...infrastructure.config import load_config


class CubiCasaProcessingError(Exception):
    """Ошибка при обработке плана через API CubiCasa5K."""
    pass


class CubiCasaClient:
    """Клиент для работы с API CubiCasa5K."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 300.0  # 5 минут для обработки изображения
    ):
        """
        Инициализация клиента.
        
        Args:
            base_url: Базовый URL API (по умолчанию из переменной окружения CUBICASA_API_URL)
            timeout: Таймаут запроса в секундах
        """
        config = load_config()
        self.base_url = base_url or os.getenv("CUBICASA_API_URL", "http://localhost:8000")
        self.timeout = timeout
        
        # Убираем завершающий слэш если есть
        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]
    
    async def process_image(
        self,
        image_bytes: bytes,
        order_id: Optional[str] = None,
        version_type: str = "ORIGINAL",
        px_per_meter: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Обработка изображения планировки через API.
        
        Args:
            image_bytes: Байты изображения
            order_id: ID заказа (опционально)
            version_type: Тип версии ("ORIGINAL" или "MODIFIED")
            px_per_meter: Пикселей на метр для масштабирования
            
        Returns:
            Dict с данными плана в формате 3Dmodel_schema.json
            
        Raises:
            CubiCasaProcessingError: При ошибке обработки
        """
        url = f"{self.base_url}/process"
        
        # Подготавливаем данные для multipart/form-data
        files = {
            "file": ("plan.png", image_bytes, "image/png")
        }
        
        data = {}
        if order_id:
            data["order_id"] = order_id
        if version_type:
            data["version_type"] = version_type
        if px_per_meter:
            data["px_per_meter"] = str(px_per_meter)
        
        try:
            # Настройки клиента
            client_kwargs = {"timeout": self.timeout}
            
            # Отключаем прокси для localhost (через переменные окружения)
            import os
            if "localhost" in self.base_url or "127.0.0.1" in self.base_url:
                # Сохраняем текущие настройки прокси
                old_no_proxy = os.environ.get("NO_PROXY", "")
                old_http_proxy = os.environ.get("HTTP_PROXY", "")
                old_https_proxy = os.environ.get("HTTPS_PROXY", "")
                
                # Отключаем прокси для localhost
                os.environ["NO_PROXY"] = "localhost,127.0.0.1"
                if "HTTP_PROXY" in os.environ:
                    del os.environ["HTTP_PROXY"]
                if "HTTPS_PROXY" in os.environ:
                    del os.environ["HTTPS_PROXY"]
            
            try:
                async with httpx.AsyncClient(**client_kwargs) as client:
                    response = await client.post(url, files=files, data=data)
                    response.raise_for_status()
                    return response.json()
            finally:
                # Восстанавливаем настройки прокси
                if "localhost" in self.base_url or "127.0.0.1" in self.base_url:
                    if old_no_proxy:
                        os.environ["NO_PROXY"] = old_no_proxy
                    else:
                        os.environ.pop("NO_PROXY", None)
                    if old_http_proxy:
                        os.environ["HTTP_PROXY"] = old_http_proxy
                    if old_https_proxy:
                        os.environ["HTTPS_PROXY"] = old_https_proxy
        except httpx.HTTPStatusError as e:
            error_detail = "Неизвестная ошибка"
            try:
                error_data = e.response.json()
                error_detail = error_data.get("detail", str(e))
            except:
                error_detail = e.response.text or str(e)
            
            raise CubiCasaProcessingError(
                f"Ошибка API CubiCasa5K (HTTP {e.response.status_code}): {error_detail}"
            ) from e
        except httpx.TimeoutException as e:
            raise CubiCasaProcessingError(
                f"Таймаут при обработке изображения (превышено {self.timeout} секунд)"
            ) from e
        except httpx.RequestError as e:
            raise CubiCasaProcessingError(
                f"Ошибка подключения к API CubiCasa5K: {str(e)}"
            ) from e
        except Exception as e:
            raise CubiCasaProcessingError(
                f"Неожиданная ошибка при обработке изображения: {str(e)}"
            ) from e
    
    async def health_check(self) -> bool:
        """
        Проверка доступности API.
        
        Returns:
            True если API доступен, False иначе
        """
        try:
            url = f"{self.base_url}/health"
            # Отключаем прокси для localhost
            import os
            if "localhost" in self.base_url or "127.0.0.1" in self.base_url:
                old_no_proxy = os.environ.get("NO_PROXY", "")
                os.environ["NO_PROXY"] = "localhost,127.0.0.1"
                if "HTTP_PROXY" in os.environ:
                    del os.environ["HTTP_PROXY"]
                if "HTTPS_PROXY" in os.environ:
                    del os.environ["HTTPS_PROXY"]
            
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    return True
            finally:
                if "localhost" in self.base_url or "127.0.0.1" in self.base_url:
                    if old_no_proxy:
                        os.environ["NO_PROXY"] = old_no_proxy
                    else:
                        os.environ.pop("NO_PROXY", None)
        except Exception:
            return False

