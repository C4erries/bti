# Быстрый старт проекта "Умное БТИ"

## Вариант 1: Локальный запуск (рекомендуется для разработки)

### 1. Установка зависимостей

#### Backend:
```bash
cd backend
pip install -r requirements.txt
```

#### Frontend:
```bash
cd frontend
npm install
```

### 2. Настройка переменных окружения

#### Backend (.env файл уже создан из ai/_env):
Файл `backend/.env` уже содержит настройки из `ai/_env`:
- `GEMINI_API_KEY` - ключ для Gemini API
- `GEMINI_MODEL` - модель Gemini
- `CUBICASA_API_URL` - URL API CubiCasa (по умолчанию http://localhost:8000)
- `CUBICASA_TIMEOUT` - таймаут запросов (300 секунд)

#### Frontend:
Переменные окружения настраиваются автоматически через `vite.config.ts`.
API URL по умолчанию: `http://localhost:8000/api/v1`

### 3. Запуск через скрипт (самый простой способ)

```bash
# Сделать скрипт исполняемым (если еще не сделано)
chmod +x start-local.sh

# Запустить проект
./start-local.sh
```

Скрипт автоматически:
- Проверит порты 8000 и 5173
- Установит зависимости если нужно
- Запустит backend и frontend
- Покажет ссылки для доступа

**Доступ:**
- Backend API: http://localhost:8000
- Frontend: http://localhost:5173
- API Docs (Swagger): http://localhost:8000/docs

### 4. Ручной запуск

#### Backend:
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend (в другом терминале):
```bash
cd frontend
npm run dev
# или
npx vite --host 0.0.0.0 --port 5173
```

### 5. Остановка

```bash
./stop.sh
```

Или вручную:
```bash
# Найти процессы
lsof -ti:8000 | xargs kill
lsof -ti:5173 | xargs kill
```

---

## Вариант 2: Docker Compose

```bash
docker-compose up --build
```

**Доступ:**
- Backend: http://localhost:8000
- Frontend: http://localhost:5173

---

## Опционально: Запуск CubiCasa API для обработки изображений планов

Для работы функции обработки изображений планов через AI нужно запустить CubiCasa API:

```bash
cd ai/CubiCasa-docker

# С GPU (рекомендуется)
docker build -t cubi-api -f Dockerfile .
docker run --rm -it --init \
  --runtime=nvidia \
  --ipc=host \
  --publish 8001:8000 \
  --volume=$PWD:/app \
  -e NVIDIA_VISIBLE_DEVICES=0 \
  -e MODEL_WEIGHTS_PATH=model_best_val_loss_var.pkl \
  -e DEVICE=cuda \
  cubi-api

# Или на CPU
docker run --rm -it \
  --publish 8001:8000 \
  --volume=$PWD:/app \
  -e MODEL_WEIGHTS_PATH=model_best_val_loss_var.pkl \
  -e DEVICE=cpu \
  cubi-api
```

**Важно:** Если CubiCasa API запущен на другом порту (например, 8001), обновите `CUBICASA_API_URL` в `backend/.env`:
```env
CUBICASA_API_URL=http://localhost:8001
```

Проверка работоспособности:
```bash
curl http://localhost:8001/health
```

---

## Тестовые пользователи

После первого запуска создаются тестовые пользователи:

- **Клиент**: `client@example.com` / `client123`
- **Исполнитель**: `executor@example.com` / `executor123`
- **Администратор**: `admin@example.com` / `admin123`
- **Суперадмин**: `superadmin@example.com` / `superadmin123`

---

## Проверка работоспособности

1. Откройте http://localhost:5173
2. Войдите как клиент: `client@example.com` / `client123`
3. Проверьте создание заказа, просмотр планов, чат

### Проверка API напрямую:

```bash
# Health check
curl http://localhost:8000/health

# Логин
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"client@example.com","password":"client123"}'

# API документация
open http://localhost:8000/docs
```

---

## Логи

### При запуске через скрипт:
```bash
# Backend
tail -f /tmp/bti-backend.log

# Frontend
tail -f /tmp/bti-frontend.log
```

### При ручном запуске:
Логи выводятся в терминал, где запущен процесс.

---

## Решение проблем

### Порт занят
```bash
# Проверить что занимает порт
lsof -i :8000
lsof -i :5173

# Освободить порт
./stop.sh
```

### Backend не запускается
1. Проверьте установлены ли зависимости: `pip list | grep fastapi`
2. Проверьте логи: `tail -f /tmp/bti-backend.log`
3. Проверьте что база данных доступна: `ls backend/app.db`

### Frontend не запускается
1. Проверьте установлены ли зависимости: `ls frontend/node_modules`
2. Установите заново: `cd frontend && rm -rf node_modules && npm install`
3. Проверьте логи: `tail -f /tmp/bti-frontend.log`

### AI модули не работают
1. Проверьте что файл `ai/app/.env` существует и содержит `GEMINI_API_KEY`
2. Проверьте что ключ валидный
3. Проверьте логи backend на наличие ошибок импорта AI модулей

### CubiCasa API не отвечает
1. Проверьте что контейнер запущен: `docker ps | grep cubi`
2. Проверьте логи: `docker logs <container_id>`
3. Проверьте доступность: `curl http://localhost:8000/health`

---

## Структура проекта

```
bti/
├── backend/          # FastAPI backend
│   ├── app/         # Основной код
│   ├── .env         # Переменные окружения (создается из ai/_env)
│   └── requirements.txt
├── frontend/         # React + Vite frontend
│   ├── src/
│   └── package.json
├── ai/              # AI модули
│   ├── _env         # Исходный файл с переменными
│   ├── app/         # AI сервисы
│   └── CubiCasa-docker/  # Нейронная сеть для обработки планов
├── start-local.sh   # Скрипт запуска
└── stop.sh          # Скрипт остановки
```

---

## Дополнительная документация

- [AI Integration Guide](backend/AI_INTEGRATION.md) - Подробная документация по AI модулям
- [AI Modules README](ai/app/README.md) - Документация AI модулей
- [CubiCasa Integration](ai/app/INTEGRATION_GUIDE.md) - Интеграция CubiCasa API

