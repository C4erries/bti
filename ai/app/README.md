# AI-ассистент для анализа планировок v2

Версия 2 AI-ассистента для анализа планировок помещений с улучшенной архитектурой и поддержкой персонализированных рекомендаций.

## Основные возможности

- **Обработка фотографий планировок** через API CubiCasa5K с автоматическим распознаванием стен, комнат, окон и дверей
- **Чат-бот** с персонализированными рекомендациями на основе профиля пользователя
- **Анализ JSON плана помещения** с выявлением рисков
- **RAG (Retrieval Augmented Generation)** с поддержкой правил и статей закона
- **Генерация эмбеддингов** для всех типов данных (план, профиль пользователя, правила, статьи)

## Интеграция с CubiCasa5K

Проект интегрирован с Docker API сервером CubiCasa5K для обработки фотографий планировок. Подробное руководство по настройке и использованию см. в [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md).

## Структура проекта

```
v2/
├── app/                        # Основной код приложения
│   ├── infrastructure/         # Инфраструктурный слой
│   │   ├── config.py          # Типизированная конфигурация
│   │   ├── gemini_client.py   # Клиент для работы с Gemini API
│   │   └── logging_config.py  # Настройка логирования
│   └── services/               # Бизнес-логика
│       ├── embedding/         # Сервисы эмбеддингов
│       ├── rag/               # RAG сервис
│       ├── analysis/          # Анализ планировок
│       ├── chat/              # Чат-бот
│       └── plan_processing/   # Обработка планов из фотографий
├── models/                      # Pydantic-модели
│   ├── chat.py                # Схемы чата
│   ├── user.py                # Схемы профиля пользователя
│   ├── plan.py                # Схемы планов
│   └── risks.py               # Схемы рисков
└── tests/                      # Тесты
```

## Установка

### Требования

- Python 3.11 или выше
- API ключ Gemini (получить можно на [Google AI Studio](https://makersuite.google.com/app/apikey))

### Установка зависимостей

```bash
# Установка основных зависимостей
pip install -r requirements.txt

# Для разработки (включая тесты)
pip install -r requirements-dev.txt
```

### Настройка окружения

Создайте файл `.env` в корне проекта `v2/` со следующим содержимым:

```env
# ============================================
# ОБЯЗАТЕЛЬНЫЕ ПЕРЕМЕННЫЕ
# ============================================

# API ключ Gemini (обязательно)
# Получить можно на: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_api_key_here

# ============================================
# НАСТРОЙКИ МОДЕЛЕЙ (опционально)
# ============================================

# Модель Gemini для генерации текста
# Доступные: gemini-2.5-pro, gemini-2.5-flash, gemini-2.5-flash-lite,
#           gemini-2.0-flash, gemini-2.0-flash-lite
# По умолчанию: gemini-2.0-flash
GEMINI_MODEL=gemini-2.0-flash

# Модель для локальных эмбеддингов (sentence-transformers)
# По умолчанию: all-MiniLM-L6-v2
LOCAL_EMBEDDING_MODEL=all-MiniLM-L6-v2

# ============================================
# НАСТРОЙКИ RAG (опционально)
# ============================================

# Размер чанка текста для RAG (по умолчанию: 1000)
RAG_CHUNK_SIZE=1000

# Перекрытие между чанками (по умолчанию: 200)
RAG_CHUNK_OVERLAP=200

# Количество релевантных чанков для поиска (по умолчанию: 5)
RAG_TOP_K=5

# ============================================
# НАСТРОЙКИ ЧАТА (опционально)
# ============================================

# Температура для генерации ответов (по умолчанию: 0.7)
CHAT_TEMPERATURE=0.7

# Максимальное количество сообщений в истории (по умолчанию: 10)
CHAT_MAX_HISTORY=10

# ============================================
# НАСТРОЙКИ АНАЛИЗА (опционально)
# ============================================

# Температура для анализа планов (по умолчанию: 0.3)
ANALYSIS_TEMPERATURE=0.3

# Количество релевантных чанков для анализа (по умолчанию: 10)
ANALYSIS_TOP_K=10

# ============================================
# НАСТРОЙКИ API CUBICASA5K (опционально)
# ============================================

# URL API CubiCasa5K для обработки изображений планировок
# По умолчанию: http://localhost:8000
CUBICASA_API_URL=http://localhost:8000

# Таймаут запроса к API CubiCasa5K в секундах (по умолчанию: 300)
CUBICASA_TIMEOUT=300
```

**Важно:** 
- Файл `.env` уже добавлен в `.gitignore` и не будет закоммичен в репозиторий
- Все переменные, кроме `GEMINI_API_KEY`, имеют значения по умолчанию и опциональны
- Если переменная не указана, будет использовано значение по умолчанию

## Использование

### Инициализация

```python
from v2.app.infrastructure import load_config, setup_logging
from v2.models.chat import ChatMessage
from v2.models.user import UserProfile, FamilyComposition, Lifestyle, UserPreferences
from v2.models.plan import KanvaPlan
from v2.app.services.chat import process_chat_message

# Настройка логирования
setup_logging()

# Загрузка конфигурации
config = load_config()
```

### Чат с персонализированными рекомендациями

```python
# Создание профиля пользователя
user_profile = UserProfile(
    family_composition=FamilyComposition(adults=2, children=[]),
    lifestyle=Lifestyle(work_from_home=True, hobbies=["чтение", "йога"]),
    preferences=UserPreferences(style="минимализм", priorities=["комфорт", "функциональность"])
)

# Создание сообщения
message = ChatMessage(role="user", content="Какие требования к планировке квартиры?")

# Обработка сообщения
response = await process_chat_message(
    message=message,
    plan=None,  # Опционально: план помещения
    order_context={"order_id": "123"},
    chat_history=[],
    ai_rules=[
        {
            "id": "rule_1",
            "title": "Правило планировки",
            "description": "Описание правила",
            "content": "Содержание правила"
        }
    ],
    articles=[
        {
            "id": "article_1",
            "title": "Статья закона",
            "article_number": "1",
            "content": "Содержание статьи",
            "law_name": "Жилищный кодекс"
        }
    ],
    user_profile=user_profile  # Профиль для персонализации
)

print(response.content)
```

### Обработка фотографии планировки

```python
from v2.app.services.plan_processing import process_plan_from_image
from v2.app.services.plan_processing import CubiCasaProcessingError

# Чтение изображения планировки
with open("floorplan.png", "rb") as f:
    image_bytes = f.read()

try:
    # Обработка изображения через API CubiCasa5K
    plan = await process_plan_from_image(
        image_bytes=image_bytes,
        order_id="123e4567-e89b-12d3-a456-426614174000",  # Опционально
        version_type="ORIGINAL",
        px_per_meter=100.0  # Опционально, для масштабирования
    )
    
    print(f"План успешно обработан!")
    print(f"ID плана: {plan.id}")
    print(f"Количество элементов: {len(plan.plan.elements)}")
    print(f"Количество 3D объектов: {len(plan.plan.objects3d or [])}")
    
    # Теперь можно использовать план для анализа
    # summary, risks, alternatives = await analyze_plan(...)
    
except CubiCasaProcessingError as e:
    print(f"Ошибка обработки плана: {e}")
```

**Важно:** Для работы этого функционала необходимо запустить API сервер CubiCasa5K (см. `CubiCasa-docker/API_README.md`).

### Анализ JSON плана помещения

```python
from v2.app.services.analysis import analyze_plan
from v2.models.plan import KanvaPlan

# Загрузка плана из JSON
plan_data = {...}  # JSON данные плана
plan = KanvaPlan(**plan_data)

# Анализ плана
summary, risks, alternatives = await analyze_plan(
    plan=plan,
    order_context={"order_id": "123"},
    ai_rules=[...],  # Список правил
    articles=[...],  # Список статей закона
    user_profile=user_profile  # Опционально: для персонализации
)

print(f"Резюме: {summary}")
print(f"Выявлено рисков: {len(risks)}")
for risk in risks:
    print(f"- {risk.type}: {risk.description} (серьезность: {risk.severity})")
```

### Генерация эмбеддингов

```python
from v2.app.services.embedding import (
    generate_embedding,
    generate_embedding_for_plan,
    generate_embedding_for_user_profile
)

# Эмбеддинг для текста
text_embedding = await generate_embedding("Текст для эмбеддинга")

# Эмбеддинг для плана
plan_embedding = await generate_embedding_for_plan(plan)

# Эмбеддинг для профиля пользователя
profile_embedding = await generate_embedding_for_user_profile(user_profile)
```

### RAG с правилами и статьями закона

```python
from v2.app.services.rag import build_rag_index, retrieve_relevant_chunks
from v2.app.services.embedding import generate_embedding

# Построение индекса
rag_index = await build_rag_index(
    rules=[
        {
            "id": "rule_1",
            "title": "Правило",
            "description": "Описание",
            "content": "Содержание",
            "regulation_reference": "Ссылка на документ"
        }
    ],
    articles=[
        {
            "id": "article_1",
            "title": "Статья",
            "article_number": "1",
            "content": "Содержание статьи",
            "law_name": "Название закона"
        }
    ]
)

# Поиск релевантных чанков
query = "требования к планировке"
query_embedding = await generate_embedding(query)
relevant_chunks = await retrieve_relevant_chunks(query_embedding, rag_index, top_k=5)

for chunk in relevant_chunks:
    print(chunk)
```

## Конфигурация

Создайте файл `.env` в корне проекта:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash

# Настройки эмбеддингов
EMBEDDING_PROVIDER=local  # "local" (sentence-transformers) или "gemini" (API)
LOCAL_EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_MODEL=models/embedding-001

# Настройки RAG
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=200
RAG_TOP_K=5

# Настройки чата
CHAT_TEMPERATURE=0.7
CHAT_MAX_HISTORY=10

# Настройки анализа
ANALYSIS_TEMPERATURE=0.3
ANALYSIS_TOP_K=10
```

## Тестирование

```bash
pytest v2/tests/
```

## Документация

- **[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)** - Полное руководство по интеграции CubiCasa5K Docker API с проектом v2
- **[PLAN_PROCESSING.md](PLAN_PROCESSING.md)** - Документация по обработке планов из фотографий

## Основные улучшения v2

1. **Типизированная конфигурация** через Pydantic
2. **Структурированное логирование** для отладки
3. **Поддержка эмбеддингов для всех типов данных** (план, профиль пользователя)
4. **Персонализированные рекомендации** на основе профиля пользователя
5. **Улучшенная архитектура** с четким разделением слоев
6. **Полная типизация** всех функций и классов
7. **Интеграция с CubiCasa5K** для обработки фотографий планировок

