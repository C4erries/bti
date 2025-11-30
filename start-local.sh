#!/bin/bash

# Скрипт для локального запуска проекта без Docker

# Получаем абсолютный путь к директории скрипта
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Запуск проекта 'Умное БТИ' локально...${NC}"
echo ""

# Проверка существования директорий
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}✗ Ошибка: директория backend не найдена${NC}"
    exit 1
fi

if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}✗ Ошибка: директория frontend не найдена${NC}"
    exit 1
fi

# Проверка портов
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo -e "${RED}✗ Порт $port уже занят!${NC}"
        echo -e "${YELLOW}  Используйте ./stop.sh для освобождения портов${NC}"
        return 1
    fi
    return 0
}

if ! check_port 8000; then
    exit 1
fi

if ! check_port 5173; then
    exit 1
fi

if ! check_port 8001; then
    echo -e "${YELLOW}⚠ Порт 8001 занят (CubiCasa API). Продолжаем без CubiCasa...${NC}"
    CUBICASA_ENABLED=false
else
    CUBICASA_ENABLED=true
fi

# Запуск CubiCasa API (опционально)
if [ "$CUBICASA_ENABLED" = true ]; then
    echo -e "${YELLOW}📦 Запуск CubiCasa API (Docker)...${NC}"
    CUBICASA_DIR="$SCRIPT_DIR/ai/CubiCasa-docker"
    
    if [ -d "$CUBICASA_DIR" ] && command -v docker &> /dev/null; then
        cd "$CUBICASA_DIR"
        
        # Проверяем существует ли образ
        if ! docker images | grep -q "cubi-api"; then
            echo -e "${YELLOW}  Сборка Docker образа CubiCasa...${NC}"
            docker build -t cubi-api -f Dockerfile . > /tmp/bti-cubicasa-build.log 2>&1
        fi
        
        # Запускаем контейнер
        if docker ps -a | grep -q "bti-cubicasa"; then
            docker start bti-cubicasa > /dev/null 2>&1
        else
            docker run -d \
                --name bti-cubicasa \
                --publish 8001:8000 \
                --volume="$CUBICASA_DIR:/app" \
                -e MODEL_WEIGHTS_PATH=model_best_val_loss_var.pkl \
                -e DEVICE=cpu \
                cubi-api > /tmp/bti-cubicasa.log 2>&1
        fi
        
        # Проверка запуска
        sleep 5
        if docker ps | grep -q "bti-cubicasa"; then
            if curl -s http://localhost:8001/health > /dev/null 2>&1; then
                echo -e "${GREEN}✓ CubiCasa API запущен на порту 8001${NC}"
            else
                echo -e "${YELLOW}⚠ CubiCasa API запущен, но еще не готов${NC}"
            fi
        else
            echo -e "${YELLOW}⚠ Не удалось запустить CubiCasa API (продолжаем без него)${NC}"
            CUBICASA_ENABLED=false
        fi
    else
        echo -e "${YELLOW}⚠ CubiCasa API не найден или Docker не установлен (продолжаем без него)${NC}"
        CUBICASA_ENABLED=false
    fi
fi

# Запуск Backend
echo -e "${YELLOW}📦 Запуск Backend (FastAPI)...${NC}"
cd "$BACKEND_DIR"

# Проверка зависимостей
if ! python3 -c "import uvicorn" 2>/dev/null; then
    echo -e "${YELLOW}  Установка зависимостей backend...${NC}"
    pip3 install -q -r requirements.txt 2>&1 | grep -v "already satisfied" || true
fi

# Запуск backend в фоне
nohup python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > /tmp/bti-backend.log 2>&1 &
BACKEND_PID=$!

# Проверка запуска backend
sleep 3
if ps -p $BACKEND_PID > /dev/null 2>&1; then
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend запущен (PID: $BACKEND_PID)${NC}"
    else
        echo -e "${RED}✗ Backend запустился, но не отвечает${NC}"
        echo -e "${YELLOW}  Проверьте логи: tail -f /tmp/bti-backend.log${NC}"
    fi
else
    echo -e "${RED}✗ Не удалось запустить Backend${NC}"
    echo -e "${YELLOW}  Ошибки:${NC}"
    tail -10 /tmp/bti-backend.log 2>/dev/null || echo "  Логи недоступны"
    exit 1
fi

# Запуск Frontend
echo -e "${YELLOW}📦 Запуск Frontend (Vite)...${NC}"
cd "$FRONTEND_DIR"

# Проверка node_modules
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}  Установка зависимостей frontend...${NC}"
    npm install
fi

# Запуск frontend в фоне
if [ -f "node_modules/.bin/vite" ]; then
    nohup ./node_modules/.bin/vite --host 0.0.0.0 --port 5173 > /tmp/bti-frontend.log 2>&1 &
    FRONTEND_PID=$!
elif command -v npx &> /dev/null; then
    nohup npx vite --host 0.0.0.0 --port 5173 > /tmp/bti-frontend.log 2>&1 &
    FRONTEND_PID=$!
else
    echo -e "${RED}✗ Не найден Vite. Установите зависимости: cd frontend && npm install${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Проверка запуска frontend
sleep 5
if ps -p $FRONTEND_PID > /dev/null 2>&1; then
    if curl -s http://localhost:5173 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend запущен (PID: $FRONTEND_PID)${NC}"
    else
        echo -e "${YELLOW}⚠ Frontend запустился, но еще не готов (может занять время)${NC}"
    fi
else
    echo -e "${RED}✗ Не удалось запустить Frontend${NC}"
    echo -e "${YELLOW}  Ошибки:${NC}"
    tail -10 /tmp/bti-frontend.log 2>/dev/null || echo "  Логи недоступны"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Сохранение PID в файл для удобной остановки
echo "$BACKEND_PID" > /tmp/bti-backend.pid
echo "$FRONTEND_PID" > /tmp/bti-frontend.pid
if [ "$CUBICASA_ENABLED" = true ]; then
    echo "cubicasa" > /tmp/bti-cubicasa.pid
fi

echo ""
echo -e "${GREEN}✅ Сервисы запущены!${NC}"
echo ""
echo -e "${GREEN}📍 Backend:     http://localhost:8000${NC}"
echo -e "${GREEN}📍 Frontend:    http://localhost:5173${NC}"
echo -e "${GREEN}📍 API Docs:    http://localhost:8000/docs${NC}"
if [ "$CUBICASA_ENABLED" = true ]; then
    echo -e "${GREEN}📍 CubiCasa API: http://localhost:8001${NC}"
fi
echo ""
echo -e "${YELLOW}Для остановки выполните:${NC}"
echo -e "  ${YELLOW}./stop.sh${NC}"
echo ""
echo -e "${YELLOW}Или вручную:${NC}"
echo -e "  ${YELLOW}kill $BACKEND_PID $FRONTEND_PID${NC}"
echo ""
echo -e "${YELLOW}Логи:${NC}"
echo -e "  ${YELLOW}Backend:  tail -f /tmp/bti-backend.log${NC}"
echo -e "  ${YELLOW}Frontend: tail -f /tmp/bti-frontend.log${NC}"
echo ""

