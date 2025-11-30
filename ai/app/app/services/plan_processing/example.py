"""
Пример использования сервиса обработки планов из фотографий.

Этот файл демонстрирует, как использовать сервис для обработки фотографий планировок.
"""

import asyncio
from pathlib import Path
from .processor import process_plan_from_image
from .cubicasa_client import CubiCasaProcessingError


async def example_process_plan_from_file():
    """Пример обработки плана из файла."""
    
    # Путь к изображению планировки
    image_path = Path("path/to/floorplan.png")
    
    # Читаем изображение
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    
    try:
        # Обрабатываем изображение
        plan = await process_plan_from_image(
            image_bytes=image_bytes,
            order_id="123e4567-e89b-12d3-a456-426614174000",  # Опционально
            version_type="ORIGINAL",
            px_per_meter=100.0  # Опционально, для масштабирования
        )
        
        print(f"План успешно обработан!")
        print(f"ID плана: {plan.id}")
        print(f"ID заказа: {plan.orderId}")
        print(f"Количество элементов: {len(plan.plan.elements)}")
        print(f"Количество 3D объектов: {len(plan.plan.objects3d or [])}")
        
        # Теперь можно использовать план для анализа
        # from v2.app.services.analysis import analyze_plan
        # summary, risks, alternatives = await analyze_plan(
        #     plan=plan,
        #     order_context={"order_id": plan.orderId},
        #     ai_rules=[],
        #     articles=[],
        #     user_profile=None
        # )
        
    except CubiCasaProcessingError as e:
        print(f"Ошибка обработки плана: {e}")
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")


async def example_process_plan_from_bytes():
    """Пример обработки плана из байтов (например, из HTTP запроса)."""
    
    # Предположим, что image_bytes получены из HTTP запроса
    # image_bytes = await request.read()
    
    # Для примера используем пустые байты
    image_bytes = b""
    
    try:
        plan = await process_plan_from_image(
            image_bytes=image_bytes,
            # order_id будет сгенерирован автоматически
            version_type="ORIGINAL"
        )
        
        print(f"План обработан: {plan.id}")
        
    except CubiCasaProcessingError as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    # Запуск примера
    asyncio.run(example_process_plan_from_file())

