# Интеграция AI модулей

## Обзор

AI модули из директории `ai/` интегрированы в backend проект. Доступны следующие возможности:

1. **Обработка изображений планов** через CubiCasa API
2. **AI анализ планов** с выявлением рисков
3. **AI чат** с персонализированными рекомендациями

## Настройка

### Переменные окружения

Добавьте в `.env` файл backend:

```env
# AI настройки
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash
CUBICASA_API_URL=http://localhost:8000
CUBICASA_TIMEOUT=300.0

# Опциональные настройки
LOCAL_EMBEDDING_MODEL=all-MiniLM-L6-v2
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=200
RAG_TOP_K=5
CHAT_TEMPERATURE=0.7
CHAT_MAX_HISTORY=10
ANALYSIS_TEMPERATURE=0.3
ANALYSIS_TOP_K=10
```

### Запуск CubiCasa API

Для обработки изображений планов необходимо запустить CubiCasa Docker контейнер:

```bash
cd ai/CubiCasa-docker
docker build -t cubi-api -f Dockerfile .
docker run --rm -it --init --runtime=nvidia --ipc=host --publish 8000:8000 --volume=$PWD:/app -e NVIDIA_VISIBLE_DEVICES=0 cubi-api
```

## API Эндпоинты

### 1. Обработка изображения плана

**POST** `/api/v1/client/orders/{order_id}/plan/process-image`

Обрабатывает изображение плана через CubiCasa API и создает версию плана ORIGINAL.

**Параметры:**
- `file`: Изображение плана (multipart/form-data)
- `px_per_meter`: Опционально, пикселей на метр

**Пример:**
```bash
curl -X POST "http://localhost:8000/api/v1/client/orders/{order_id}/plan/process-image" \
  -H "Authorization: Bearer {token}" \
  -F "file=@floorplan.png" \
  -F "px_per_meter=100"
```

### 2. Принятие результата парсинга (существующий)

**POST** `/api/v1/client/orders/{order_id}/plan/parse-result`

Принимает результат парсинга от нейронки (может использоваться для ручной интеграции).

### 3. AI Чат

**POST** `/api/v1/client/chats/{chat_id}/messages`

Отправляет сообщение в чат. AI автоматически обрабатывает сообщение и отвечает.

**WebSocket:** `/api/v1/ws/chat/{chat_id}?token={jwt_token}`

Для real-time чата с AI.

## Использование в коде

### Обработка изображения плана

```python
from app.services import ai_integration_service

# Обработка изображения
result = await ai_integration_service.process_plan_image(
    image_bytes=image_bytes,
    order_id=order_id,
    version_type="ORIGINAL",
    px_per_meter=100.0
)
```

### Анализ плана

```python
from app.services import ai_integration_service

# Анализ плана
summary, risks, alternatives = await ai_integration_service.analyze_plan_with_ai(
    plan_data=plan_data,
    order_context={"order_id": str(order_id)},
    ai_rules=[],
    articles=[],
    user_profile=None
)
```

### Обработка чата

```python
from app.services import ai_integration_service

# Обработка сообщения чата
response = await ai_integration_service.process_chat_with_ai(
    message="Какие проблемы в этой планировке?",
    plan_data=plan_data,
    order_context={"order_id": str(order_id)},
    chat_history=[],
    ai_rules=[],
    articles=[],
    user_profile=None
)
```

## Структура интеграции

```
backend/app/services/
├── ai_integration_service.py  # Основной интеграционный сервис
└── chat_service.py            # Обновлен для использования AI

backend/app/core/
└── config.py                  # Добавлены AI настройки

backend/app/api/v1/endpoints/
├── client_orders.py          # Добавлен эндпоинт process-image
└── client_chats.py            # Обновлен для async AI
```

## Зависимости

Все необходимые зависимости добавлены в `backend/requirements.txt`:

- `google-genai>=0.2.0` - Gemini API
- `sentence-transformers>=2.2.0` - Локальные эмбеддинги
- `python-dotenv>=1.0.0` - Загрузка .env
- `numpy>=1.24.0` - Для работы с эмбеддингами
- `aiosqlite>=0.19.0` - Для RAG базы данных

## Обработка ошибок

Если AI модули недоступны, система автоматически использует fallback:

- **Чат**: Возвращает заглушку "AI stub: {message}"
- **Обработка планов**: Выбрасывает ошибку с понятным сообщением
- **Анализ**: Возвращает сообщение "AI analysis not available"

## Дополнительная документация

- [AI модули README](../ai/app/README.md)
- [Интеграция CubiCasa](../ai/app/INTEGRATION_GUIDE.md)
- [Обработка планов](../ai/app/PLAN_PROCESSING.md)

