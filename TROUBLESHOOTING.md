# Решение проблем запуска

## Проблема: Backend не запускается

### Ошибка: `Extra inputs are not permitted [type=extra_forbidden]`

**Причина:** В `.env` файле есть переменные, которых нет в `Settings` (например, `EMBEDDING_MODEL`).

**Решение:** ✅ Исправлено - добавлен `extra="ignore"` в конфигурацию.

### Ошибка: `ModuleNotFoundError` или импорты

**Решение:**
```bash
cd backend
pip install -r requirements.txt
```

### Проверка запуска backend вручную:
```bash
cd backend
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Проблема: CubiCasa API не запускается

### Ошибка: `docker: invalid spec: too many colons`

**Причина:** Путь содержит двоеточие (например, `11:28:25` в имени директории).

**Решение:** ✅ Исправлено - используется абсолютный путь через `cd` и `pwd`.

### Ошибка: Docker не установлен

**Решение:**
- Установите Docker Desktop: https://www.docker.com/products/docker-desktop
- Или запустите без CubiCasa - проект будет работать, но обработка изображений будет недоступна

### Проверка CubiCasa вручную:
```bash
cd ai/CubiCasa-docker
docker build -t cubi-api -f Dockerfile .
docker run -d --name bti-cubicasa \
  --publish 8001:8000 \
  --volume="$(pwd):/app" \
  -e MODEL_WEIGHTS_PATH=model_best_val_loss_var.pkl \
  -e DEVICE=cpu \
  cubi-api

# Проверка
curl http://localhost:8001/health
```

### Если CubiCasa не нужен:
Проект будет работать без него, просто обработка изображений планов будет недоступна.

---

## Проблема: Порты заняты

### Ошибка: `Порт 8000 уже занят`

**Решение:**
```bash
# Остановить все процессы проекта
./stop.sh

# Или вручную освободить порт
lsof -ti:8000 | xargs kill
lsof -ti:8001 | xargs kill
lsof -ti:5173 | xargs kill
```

---

## Проверка работоспособности

### 1. Проверка Backend:
```bash
curl http://localhost:8000/health
# Должен вернуть: {"status":"ok"}
```

### 2. Проверка CubiCasa:
```bash
curl http://localhost:8001/health
# Должен вернуть JSON с информацией о модели
```

### 3. Проверка Frontend:
```bash
curl http://localhost:5173
# Должен вернуть HTML страницу
```

---

## Логи для отладки

### Backend:
```bash
tail -f /tmp/bti-backend.log
```

### Frontend:
```bash
tail -f /tmp/bti-frontend.log
```

### CubiCasa:
```bash
tail -f /tmp/bti-cubicasa.log
# Или
docker logs bti-cubicasa
```

---

## Частые проблемы

### 1. Backend падает при импорте AI модулей

**Решение:** AI модули опциональны. Если они недоступны, backend будет работать с fallback.

### 2. CubiCasa не отвечает

**Проверьте:**
- Контейнер запущен: `docker ps | grep bti-cubicasa`
- Порт доступен: `curl http://localhost:8001/health`
- Логи контейнера: `docker logs bti-cubicasa`

### 3. Gemini API не работает

**Проверьте:**
- Ключ установлен: `cat ai/_env | grep GEMINI_API_KEY`
- Ключ валидный (проверьте на https://makersuite.google.com/app/apikey)

---

## Полная переустановка

Если ничего не помогает:

```bash
# Остановить все
./stop.sh

# Переустановить зависимости backend
cd backend
pip install --upgrade -r requirements.txt

# Переустановить зависимости frontend
cd ../frontend
rm -rf node_modules
npm install

# Пересобрать CubiCasa образ
cd ../ai/CubiCasa-docker
docker build -t cubi-api -f Dockerfile .

# Запустить заново
cd ../..
./start-local.sh
```

