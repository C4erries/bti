# Обработка планов из фотографий

Этот модуль предоставляет функциональность для обработки фотографий планировок через API CubiCasa5K и получения структурированных данных плана.

## Настройка

### 1. Запуск API CubiCasa5K

Перед использованием необходимо запустить API сервер CubiCasa5K. См. инструкции в `CubiCasa-docker/API_README.md`.

### 2. Настройка переменных окружения

Добавьте в файл `.env`:

```env
# URL API CubiCasa5K (по умолчанию: http://localhost:8000)
CUBICASA_API_URL=http://localhost:8000

# Таймаут запроса в секундах (по умолчанию: 300)
CUBICASA_TIMEOUT=300
```

## Использование

### Базовый пример

```python
from v2.app.services.plan_processing import process_plan_from_image
from v2.app.services.plan_processing import CubiCasaProcessingError

# Чтение изображения
with open("floorplan.png", "rb") as f:
    image_bytes = f.read()

try:
    # Обработка изображения
    plan = await process_plan_from_image(
        image_bytes=image_bytes,
        order_id="123e4567-e89b-12d3-a456-426614174000",  # Опционально
        version_type="ORIGINAL",
        px_per_meter=100.0  # Опционально
    )
    
    print(f"План обработан: {plan.id}")
    print(f"Элементов: {len(plan.plan.elements)}")
    
except CubiCasaProcessingError as e:
    print(f"Ошибка: {e}")
```

### Интеграция с анализом

После обработки изображения полученный план можно использовать для анализа:

```python
from v2.app.services.plan_processing import process_plan_from_image
from v2.app.services.analysis import analyze_plan

# Обработка изображения
plan = await process_plan_from_image(
    image_bytes=image_bytes,
    order_id="order-123"
)

# Анализ плана
summary, risks, alternatives = await analyze_plan(
    plan=plan,
    order_context={"order_id": plan.orderId},
    ai_rules=[],
    articles=[],
    user_profile=None
)

print(f"Резюме: {summary}")
print(f"Рисков: {len(risks)}")
```

### Использование в чате

План, полученный из фотографии, можно использовать в чате:

```python
from v2.app.services.plan_processing import process_plan_from_image
from v2.app.services.chat import process_chat_message
from v2.models.chat import ChatMessage

# Обработка изображения
plan = await process_plan_from_image(image_bytes=image_bytes)

# Чат с планом
message = ChatMessage(role="user", content="Какие проблемы в этой планировке?")
response = await process_chat_message(
    message=message,
    plan=plan,  # Используем план из фотографии
    order_context={"order_id": plan.orderId},
    chat_history=[],
    ai_rules=[],
    articles=[],
    user_profile=None
)

print(response.content)
```

## API

### `process_plan_from_image`

```python
async def process_plan_from_image(
    image_bytes: bytes,
    order_id: Optional[str] = None,
    version_type: str = "ORIGINAL",
    px_per_meter: Optional[float] = None,
    cubicasa_api_url: Optional[str] = None
) -> OrderPlanVersion
```

**Параметры:**
- `image_bytes`: Байты изображения планировки (PNG, JPG)
- `order_id`: ID заказа (опционально, будет сгенерирован UUID)
- `version_type`: Тип версии ("ORIGINAL" или "MODIFIED")
- `px_per_meter`: Пикселей на метр для масштабирования (опционально)
- `cubicasa_api_url`: URL API CubiCasa5K (опционально, по умолчанию из конфига)

**Возвращает:**
- `OrderPlanVersion`: Структурированный план в формате 3Dmodel_schema.json

**Исключения:**
- `CubiCasaProcessingError`: При ошибке обработки

### `CubiCasaClient`

Клиент для прямого взаимодействия с API:

```python
from v2.app.services.plan_processing import CubiCasaClient

client = CubiCasaClient(base_url="http://localhost:8000")

# Проверка доступности
is_healthy = await client.health_check()

# Обработка изображения
result = await client.process_image(
    image_bytes=image_bytes,
    order_id="order-123",
    version_type="ORIGINAL",
    px_per_meter=100.0
)
```

## Структура результата

Результат обработки - это объект `OrderPlanVersion`, который содержит:

- **plan.meta**: Метаданные плана (ширина, высота, масштаб)
- **plan.elements**: Элементы плана (стены, зоны)
  - Стены с проемами (окна, двери)
  - Зоны (комнаты: кухня, гостиная, спальня и т.д.)
- **plan.objects3d**: 3D объекты (окна, двери, мебель)

## Обработка ошибок

```python
from v2.app.services.plan_processing import CubiCasaProcessingError

try:
    plan = await process_plan_from_image(image_bytes=image_bytes)
except CubiCasaProcessingError as e:
    # Ошибка API CubiCasa5K
    print(f"Ошибка обработки: {e}")
except Exception as e:
    # Другие ошибки
    print(f"Неожиданная ошибка: {e}")
```

## Требования

- Запущенный API сервер CubiCasa5K (см. `CubiCasa-docker/API_README.md`)
- Установленная зависимость `httpx` (уже в `requirements.txt`)

