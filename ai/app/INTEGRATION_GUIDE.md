# Полное руководство по интеграции CubiCasa5K Docker API с проектом v2

Это руководство описывает полную интеграцию между Docker контейнером с API CubiCasa5K и проектом v2 для обработки фотографий планировок.

## Быстрый старт

1. **Запустите Docker контейнер:**
   ```bash
   cd CubiCasa-docker
   docker build -t cubi-api -f Dockerfile .
   docker run --rm -it --init --runtime=nvidia --ipc=host --publish 8000:8000 --volume=$PWD:/app -e NVIDIA_VISIBLE_DEVICES=0 cubi-api
   ```

2. **Настройте проект v2:**
   ```bash
   cd v2
   # Добавьте в .env: CUBICASA_API_URL=http://localhost:8000
   pip install -r requirements.txt
   ```

3. **Используйте в коде:**
   ```python
   from v2.app.services.plan_processing import process_plan_from_image
   
   with open("floorplan.png", "rb") as f:
       image_bytes = f.read()
   
   plan = await process_plan_from_image(image_bytes=image_bytes)
   ```

## Содержание

1. [Обзор архитектуры](#обзор-архитектуры)
2. [Установка и настройка](#установка-и-настройка)
3. [Запуск Docker контейнера](#запуск-docker-контейнера)
4. [Использование в проекте v2](#использование-в-проекте-v2)
5. [Примеры использования](#примеры-использования)
6. [Troubleshooting](#troubleshooting)
7. [API Reference](#api-reference)
8. [Переменные окружения](#переменные-окружения)
9. [Производительность](#производительность)
10. [Безопасность](#безопасность)
11. [Мониторинг и логирование](#мониторинг-и-логирование)
12. [Детальное описание компонентов](#детальное-описание-компонентов)
13. [Практические сценарии использования](#практические-сценарии-использования)
14. [Оптимизация производительности](#оптимизация-производительности)

---

## Обзор архитектуры

### Компоненты системы

```
┌─────────────────────────────────────────────────────────────┐
│                    Проект v2 (Python)                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  app/services/plan_processing/                      │   │
│  │  ├── cubicasa_client.py  (HTTP клиент)              │   │
│  │  └── processor.py        (Обработка результатов)    │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          │ HTTP POST /process                │
│                          ▼                                   │
└─────────────────────────────────────────────────────────────┘
                          │
                          │
┌─────────────────────────────────────────────────────────────┐
│           CubiCasa-docker (Docker контейнер)                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  FastAPI сервер (app.py)                              │   │
│  │  ├── /process  - обработка изображений               │   │
│  │  ├── /health   - проверка работоспособности          │   │
│  │  └── /         - корневой endpoint                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          │ PyTorch модель                    │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  CubiCasa5K модель (model_best_val_loss_var.pkl)     │   │
│  │  - Распознавание стен, комнат, окон, дверей          │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Поток данных

1. **Клиент (v2)** отправляет изображение планировки через HTTP POST запрос
2. **API сервер (Docker)** получает изображение и обрабатывает его через модель CubiCasa5K
3. **Модель** выполняет:
   - Сегментацию комнат
   - Обнаружение стен
   - Обнаружение окон и дверей
   - Генерацию полигонов
4. **API сервер** конвертирует результаты в формат `3Dmodel_schema.json`
5. **Клиент (v2)** получает структурированный план и может использовать его для анализа

---

## Установка и настройка

### Требования

- Docker с поддержкой NVIDIA (для GPU) или без (для CPU)
- Python 3.11+ для проекта v2
- Файл весов модели: `model_best_val_loss_var.pkl`

### 1. Подготовка Docker образа

```bash
# Перейдите в директорию CubiCasa-docker
cd CubiCasa-docker

# Соберите Docker образ
docker build -t cubi-api -f Dockerfile .
```

**Важно:** Убедитесь, что файл `model_best_val_loss_var.pkl` находится в директории `CubiCasa-docker/`.

### 2. Настройка проекта v2

#### Установка зависимостей

```bash
cd v2
pip install -r requirements.txt
```

#### Настройка переменных окружения

Создайте файл `.env` в директории `v2/`:

```env
# Обязательные настройки
GEMINI_API_KEY=your_gemini_api_key_here

# Настройки API CubiCasa5K
CUBICASA_API_URL=http://localhost:8000
CUBICASA_TIMEOUT=300

# Остальные настройки (опционально)
GEMINI_MODEL=gemini-2.0-flash
LOCAL_EMBEDDING_MODEL=all-MiniLM-L6-v2
```

---

## Запуск Docker контейнера

### Запуск с GPU (рекомендуется)

```bash
cd CubiCasa-docker

docker run --rm -it --init \
  --runtime=nvidia \
  --ipc=host \
  --publish 8000:8000 \
  --volume=$PWD:/app \
  -e NVIDIA_VISIBLE_DEVICES=0 \
  -e MODEL_WEIGHTS_PATH=model_best_val_loss_var.pkl \
  -e DEVICE=cuda \
  cubi-api
```

### Запуск на CPU

```bash
cd CubiCasa-docker

docker run --rm -it \
  --publish 8000:8000 \
  --volume=$PWD:/app \
  -e MODEL_WEIGHTS_PATH=model_best_val_loss_var.pkl \
  -e DEVICE=cpu \
  cubi-api
```

### Проверка работоспособности

После запуска контейнера проверьте доступность API:

```bash
# В другом терминале
curl http://localhost:8000/health
```

Должен вернуться ответ:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "device": "cuda"
}
```

---

## Использование в проекте v2

### Базовое использование

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
        order_id="order-123",  # Опционально
        version_type="ORIGINAL",
        px_per_meter=100.0  # Опционально
    )
    
    print(f"План обработан: {plan.id}")
    print(f"Элементов: {len(plan.plan.elements)}")
    
except CubiCasaProcessingError as e:
    print(f"Ошибка обработки: {e}")
```

### Интеграция с анализом планов

```python
from v2.app.services.plan_processing import process_plan_from_image
from v2.app.services.analysis import analyze_plan

# Обработка изображения
plan = await process_plan_from_image(
    image_bytes=image_bytes,
    order_id="order-123"
)

# Анализ плана на предмет рисков
summary, risks, alternatives = await analyze_plan(
    plan=plan,
    order_context={"order_id": plan.orderId},
    ai_rules=[],
    articles=[],
    user_profile=None
)

print(f"Резюме: {summary}")
print(f"Выявлено рисков: {len(risks)}")
```

### Использование в чате

```python
from v2.app.services.plan_processing import process_plan_from_image
from v2.app.services.chat import process_chat_message
from v2.models.chat import ChatMessage

# Обработка изображения
plan = await process_plan_from_image(image_bytes=image_bytes)

# Чат с планом
message = ChatMessage(
    role="user", 
    content="Какие проблемы в этой планировке?"
)

response = await process_chat_message(
    message=message,
    plan=plan,  # План из фотографии
    order_context={"order_id": plan.orderId},
    chat_history=[],
    ai_rules=[],
    articles=[],
    user_profile=None
)

print(response.content)
```

---

## Примеры использования

### Пример 1: Обработка одного изображения

```python
import asyncio
from pathlib import Path
from v2.app.services.plan_processing import process_plan_from_image

async def process_single_image():
    image_path = Path("Квартиры/1.jpg")
    
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    
    plan = await process_plan_from_image(
        image_bytes=image_bytes,
        order_id="test-order-001",
        px_per_meter=100.0
    )
    
    print(f"Обработано элементов: {len(plan.plan.elements)}")
    return plan

asyncio.run(process_single_image())
```

### Пример 2: Пакетная обработка

```python
import asyncio
from pathlib import Path
from v2.app.services.plan_processing import process_plan_from_image

async def process_batch():
    apartments_dir = Path("Квартиры")
    image_files = sorted(apartments_dir.glob("*.jpg"))
    
    results = []
    
    for image_file in image_files:
        print(f"Обработка: {image_file.name}")
        
        with open(image_file, "rb") as f:
            image_bytes = f.read()
        
        try:
            plan = await process_plan_from_image(
                image_bytes=image_bytes,
                order_id=f"order-{image_file.stem}"
            )
            results.append({
                "file": image_file.name,
                "plan_id": plan.id,
                "elements": len(plan.plan.elements),
                "success": True
            })
        except Exception as e:
            results.append({
                "file": image_file.name,
                "success": False,
                "error": str(e)
            })
    
    return results

results = asyncio.run(process_batch())
print(f"Обработано: {sum(1 for r in results if r['success'])}/{len(results)}")
```

### Пример 3: Сохранение результатов

```python
import json
from v2.app.services.plan_processing import process_plan_from_image

async def process_and_save():
    with open("floorplan.png", "rb") as f:
        image_bytes = f.read()
    
    plan = await process_plan_from_image(image_bytes=image_bytes)
    
    # Сохранение в JSON
    with open("plan_result.json", "w", encoding="utf-8") as f:
        json.dump(
            plan.model_dump(), 
            f, 
            indent=2, 
            ensure_ascii=False, 
            default=str
        )
    
    print("План сохранен в plan_result.json")
```

---

## Troubleshooting

### Проблема: API недоступен (502 Bad Gateway)

**Причина:** Запросы идут через прокси.

**Решение:** 
- Убедитесь, что в коде отключен прокси для localhost (уже реализовано в `cubicasa_client.py`)
- Проверьте, что контейнер запущен: `docker ps`
- Проверьте логи контейнера: `docker logs <container_id>`

### Проблема: Модель не загружается

**Причина:** Файл весов не найден.

**Решение:**
```bash
# Убедитесь, что файл существует
ls CubiCasa-docker/model_best_val_loss_var.pkl

# Проверьте переменную окружения в Docker
docker run ... -e MODEL_WEIGHTS_PATH=model_best_val_loss_var.pkl ...
```

### Проблема: CUDA недоступна

**Причина:** GPU не доступна или драйверы не установлены.

**Решение:**
- Используйте CPU режим: `-e DEVICE=cpu`
- Или установите nvidia-docker2 для GPU поддержки

### Проблема: Элементы плана пустые (0 элементов)

**Причина:** Модель не нашла стены/комнаты на изображении.

**Возможные причины:**
- Изображение низкого качества
- Планировка не соответствует обучающим данным
- Порог обнаружения слишком высокий

**Решение:**
- Проверьте качество изображения
- Попробуйте другое изображение
- Функция автоматически использует fallback на сегментационные маски

### Проблема: Таймаут при обработке

**Причина:** Обработка занимает слишком много времени.

**Решение:**
- Увеличьте таймаут в `.env`: `CUBICASA_TIMEOUT=600`
- Используйте GPU для ускорения обработки

### Проблема: Ошибка импорта модулей

**Причина:** Неправильные пути импорта.

**Решение:**
- Убедитесь, что запускаете скрипты из корня проекта
- Проверьте, что `v2` добавлен в `sys.path`

---

## API Reference

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
- `image_bytes` (bytes, обязательный): Байты изображения планировки
- `order_id` (str, опционально): ID заказа (UUID будет сгенерирован автоматически)
- `version_type` (str, опционально): Тип версии ("ORIGINAL" или "MODIFIED")
- `px_per_meter` (float, опционально): Пикселей на метр для масштабирования
- `cubicasa_api_url` (str, опционально): URL API (по умолчанию из конфига)

**Возвращает:**
- `OrderPlanVersion`: Структурированный план в формате 3Dmodel_schema.json

**Исключения:**
- `CubiCasaProcessingError`: При ошибке обработки через API

### `CubiCasaClient`

```python
class CubiCasaClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 300.0
    )
    
    async def process_image(
        self,
        image_bytes: bytes,
        order_id: Optional[str] = None,
        version_type: str = "ORIGINAL",
        px_per_meter: Optional[float] = None
    ) -> Dict[str, Any]
    
    async def health_check(self) -> bool
```

### Структура результата

Результат обработки - объект `OrderPlanVersion` со следующей структурой:

```python
{
    "id": "uuid",
    "orderId": "uuid",
    "versionType": "ORIGINAL" | "MODIFIED",
    "plan": {
        "meta": {
            "width": float,
            "height": float,
            "unit": "px",
            "scale": {
                "px_per_meter": float
            } | None,
            "ceiling_height_m": float | None
        },
        "elements": [
            {
                "id": "uuid",
                "type": "wall" | "zone",
                "geometry": {
                    "kind": "segment" | "polygon",
                    "points": [float, ...],
                    "openings": [...]  # только для walls
                },
                "zoneType": str  # только для zones
            }
        ],
        "objects3d": [
            {
                "id": "uuid",
                "type": "window" | "door" | "chair" | "table" | "bed",
                "position": {"x": float, "y": float, "z": float},
                "size": {"x": float, "y": float, "z": float}
            }
        ]
    },
    "createdAt": "ISO datetime"
}
```

---

## Переменные окружения

### Проект v2

| Переменная | Описание | По умолчанию |
|-----------|----------|--------------|
| `CUBICASA_API_URL` | URL API CubiCasa5K | `http://localhost:8000` |
| `CUBICASA_TIMEOUT` | Таймаут запроса (секунды) | `300` |
| `GEMINI_API_KEY` | API ключ Gemini (обязательно) | - |

### Docker контейнер

| Переменная | Описание | По умолчанию |
|-----------|----------|--------------|
| `MODEL_WEIGHTS_PATH` | Путь к файлу весов модели | `model_best_val_loss_var.pkl` |
| `DEVICE` | Устройство (cuda/cpu) | `cuda` |
| `PORT` | Порт API сервера | `8000` |

---

## Производительность

### Время обработки

- **С GPU:** ~5-15 секунд на изображение
- **С CPU:** ~30-60 секунд на изображение

### Рекомендации

1. Используйте GPU для ускорения обработки
2. Для пакетной обработки используйте асинхронные запросы
3. Увеличьте таймаут для больших изображений

### Оптимизация

```python
import asyncio
from v2.app.services.plan_processing import CubiCasaClient

async def process_multiple_concurrent():
    client = CubiCasaClient()
    
    # Параллельная обработка нескольких изображений
    tasks = []
    for image_file in image_files:
        with open(image_file, "rb") as f:
            image_bytes = f.read()
        tasks.append(client.process_image(image_bytes))
    
    results = await asyncio.gather(*tasks)
    return results
```

---

## Безопасность

### Рекомендации

1. **Не экспортируйте API наружу** без аутентификации
2. **Используйте HTTPS** в продакшене
3. **Ограничьте размер загружаемых файлов** в FastAPI
4. **Добавьте rate limiting** для предотвращения злоупотреблений

### Пример настройки безопасности в FastAPI

```python
from fastapi import Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1"]
)
```

---

## Мониторинг и логирование

### Логи Docker контейнера

```bash
# Просмотр логов
docker logs <container_id>

# Просмотр логов в реальном времени
docker logs -f <container_id>
```

### Логирование в проекте v2

```python
from v2.app.infrastructure.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger("plan_processing")

logger.info("Начало обработки плана")
logger.error("Ошибка обработки")
```

---

## Детальное описание компонентов

### CubiCasa-docker (API сервер)

#### Структура файлов

```
CubiCasa-docker/
├── Dockerfile              # Конфигурация Docker образа
├── app.py                  # FastAPI сервер
├── converter.py            # Конвертация результатов в 3Dmodel_schema.json
├── requirements.txt        # Python зависимости
├── model_best_val_loss_var.pkl  # Веса модели
└── floortrans/             # Библиотека для работы с моделью
    ├── models/             # Архитектуры моделей
    ├── post_prosessing.py  # Постобработка результатов
    └── ...
```

#### Процесс обработки изображения

1. **Прием запроса** (`app.py` → `process_image`)
   - Получение изображения через multipart/form-data
   - Валидация параметров

2. **Предобработка** (`load_and_preprocess_image`)
   - Декодирование изображения
   - Изменение размера до 512x512 с сохранением пропорций
   - Добавление padding
   - Нормализация: [0, 255] → [-1, 1]

3. **Предсказание модели** (`predict_image`)
   - Тестовая аугментация (4 поворота)
   - Предсказание для каждого поворота
   - Усреднение результатов
   - Разделение на heatmaps, rooms, icons

4. **Постобработка** (`get_polygons`)
   - Извлечение полигонов стен из heatmaps
   - Извлечение полигонов комнат из сегментации
   - Извлечение окон и дверей
   - Fallback на сегментационные маски при отсутствии полигонов

5. **Конвертация** (`convert_to_3dmodel_schema`)
   - Преобразование полигонов в формат 3Dmodel_schema.json
   - Создание элементов (стены, зоны)
   - Создание 3D объектов (окна, двери)

### Проект v2 (Клиент)

#### Структура модулей

```
v2/app/services/plan_processing/
├── __init__.py             # Экспорт функций
├── cubicasa_client.py      # HTTP клиент для API
└── processor.py            # Обработка и конвертация результатов
```

#### Процесс работы клиента

1. **Инициализация клиента** (`CubiCasaClient`)
   - Загрузка URL из конфига
   - Настройка таймаутов

2. **Отправка запроса** (`process_image`)
   - Подготовка multipart/form-data
   - Отправка HTTP POST запроса
   - Обработка прокси для localhost

3. **Обработка ответа** (`process_plan_from_image`)
   - Получение JSON ответа
   - Конвертация в `OrderPlanVersion`
   - Валидация структуры данных

---

## Практические сценарии использования

### Сценарий 1: Обработка загруженного пользователем изображения

```python
from fastapi import UploadFile
from v2.app.services.plan_processing import process_plan_from_image

async def handle_uploaded_plan(file: UploadFile, order_id: str):
    """Обработка загруженного пользователем плана"""
    
    # Читаем файл
    image_bytes = await file.read()
    
    # Обрабатываем
    plan = await process_plan_from_image(
        image_bytes=image_bytes,
        order_id=order_id,
        version_type="ORIGINAL"
    )
    
    # Сохраняем в базу данных или возвращаем клиенту
    return plan
```

### Сценарий 2: Пакетная обработка с прогресс-баром

```python
import asyncio
from tqdm import tqdm
from v2.app.services.plan_processing import process_plan_from_image

async def batch_process_with_progress(image_files: list):
    """Пакетная обработка с отображением прогресса"""
    
    results = []
    
    for image_file in tqdm(image_files, desc="Обработка"):
        with open(image_file, "rb") as f:
            image_bytes = f.read()
        
        try:
            plan = await process_plan_from_image(image_bytes=image_bytes)
            results.append({"file": image_file.name, "plan": plan, "success": True})
        except Exception as e:
            results.append({"file": image_file.name, "error": str(e), "success": False})
    
    return results
```

### Сценарий 3: Интеграция с веб-приложением

```python
from fastapi import FastAPI, File, UploadFile
from v2.app.services.plan_processing import process_plan_from_image
from v2.app.services.analysis import analyze_plan

app = FastAPI()

@app.post("/api/plans/process")
async def process_plan_endpoint(
    file: UploadFile = File(...),
    order_id: str = None
):
    """Endpoint для обработки плана из изображения"""
    
    image_bytes = await file.read()
    
    # Обработка изображения
    plan = await process_plan_from_image(
        image_bytes=image_bytes,
        order_id=order_id
    )
    
    # Анализ плана
    summary, risks, alternatives = await analyze_plan(
        plan=plan,
        order_context={"order_id": plan.orderId},
        ai_rules=[],
        articles=[],
        user_profile=None
    )
    
    return {
        "plan": plan.model_dump(),
        "analysis": {
            "summary": summary,
            "risks": [r.model_dump() for r in risks],
            "alternatives": alternatives
        }
    }
```

---

## Оптимизация производительности

### Кэширование результатов

```python
from functools import lru_cache
import hashlib

def get_image_hash(image_bytes: bytes) -> str:
    """Получение хеша изображения для кэширования"""
    return hashlib.md5(image_bytes).hexdigest()

# Кэширование результатов обработки
@lru_cache(maxsize=100)
async def cached_process_plan(image_hash: str, image_bytes: bytes):
    """Кэшированная обработка плана"""
    return await process_plan_from_image(image_bytes=image_bytes)
```

### Параллельная обработка

```python
import asyncio
from v2.app.services.plan_processing import CubiCasaClient

async def parallel_processing(image_files: list, max_concurrent: int = 3):
    """Параллельная обработка с ограничением количества одновременных запросов"""
    
    semaphore = asyncio.Semaphore(max_concurrent)
    client = CubiCasaClient()
    
    async def process_one(image_file):
        async with semaphore:
            with open(image_file, "rb") as f:
                image_bytes = f.read()
            return await client.process_image(image_bytes=image_bytes)
    
    tasks = [process_one(f) for f in image_files]
    return await asyncio.gather(*tasks)
```

---

## Дополнительные ресурсы

- [Документация CubiCasa5K](https://github.com/CubiCasa/CubiCasa5k)
- [FastAPI документация](https://fastapi.tiangolo.com/)
- [Docker документация](https://docs.docker.com/)
- [PyTorch документация](https://pytorch.org/docs/)

---

## Поддержка

При возникновении проблем:

1. Проверьте логи Docker контейнера: `docker logs <container_id>`
2. Проверьте логи проекта v2
3. Убедитесь, что все зависимости установлены
4. Проверьте доступность API через `/health` endpoint
5. Проверьте переменные окружения в `.env` файле

### Полезные команды

```bash
# Проверка статуса контейнера
docker ps

# Просмотр логов
docker logs -f <container_id>

# Проверка API
curl http://localhost:8000/health

# Пересборка образа
cd CubiCasa-docker
docker build -t cubi-api -f Dockerfile .
```

