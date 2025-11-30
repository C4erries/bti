#!/bin/bash

# Скрипт для остановки всех процессов проекта "Умное БТИ"

echo "🛑 Остановка всех процессов проекта..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для остановки процессов по имени
stop_processes() {
    local pattern=$1
    local name=$2
    
    echo -e "${YELLOW}Поиск процессов: $name...${NC}"
    
    # Находим PID процессов
    PIDS=$(ps aux | grep -E "$pattern" | grep -v grep | awk '{print $2}')
    
    if [ -z "$PIDS" ]; then
        echo -e "${GREEN}✓ $name: процессы не найдены${NC}"
        return 0
    fi
    
    # Останавливаем процессы
    for PID in $PIDS; do
        echo -e "${YELLOW}  Остановка процесса $PID ($name)...${NC}"
        kill $PID 2>/dev/null
    done
    
    # Ждем немного и проверяем
    sleep 1
    
    # Если процессы еще живы, убиваем принудительно
    REMAINING=$(ps aux | grep -E "$pattern" | grep -v grep | awk '{print $2}')
    if [ ! -z "$REMAINING" ]; then
        for PID in $REMAINING; do
            echo -e "${RED}  Принудительная остановка процесса $PID...${NC}"
            kill -9 $PID 2>/dev/null
        done
        sleep 1
    fi
    
    # Финальная проверка
    FINAL=$(ps aux | grep -E "$pattern" | grep -v grep | awk '{print $2}')
    if [ -z "$FINAL" ]; then
        echo -e "${GREEN}✓ $name: все процессы остановлены${NC}"
    else
        echo -e "${RED}✗ $name: некоторые процессы не удалось остановить${NC}"
    fi
}

# Остановка процессов по сохраненным PID
echo ""
echo -e "${YELLOW}Проверка сохраненных PID...${NC}"

if [ -f /tmp/bti-backend.pid ]; then
    BACKEND_PID=$(cat /tmp/bti-backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}  Остановка Backend (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID 2>/dev/null
        sleep 1
        if ps -p $BACKEND_PID > /dev/null 2>&1; then
            kill -9 $BACKEND_PID 2>/dev/null
        fi
        echo -e "${GREEN}✓ Backend остановлен${NC}"
    fi
    rm -f /tmp/bti-backend.pid
fi

if [ -f /tmp/bti-frontend.pid ]; then
    FRONTEND_PID=$(cat /tmp/bti-frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}  Остановка Frontend (PID: $FRONTEND_PID)...${NC}"
        kill $FRONTEND_PID 2>/dev/null
        sleep 1
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            kill -9 $FRONTEND_PID 2>/dev/null
        fi
        echo -e "${GREEN}✓ Frontend остановлен${NC}"
    fi
    rm -f /tmp/bti-frontend.pid
fi

# Остановка Docker контейнеров (если запущены)
echo ""
echo -e "${YELLOW}Проверка Docker контейнеров...${NC}"
if command -v docker-compose &> /dev/null; then
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    cd "$SCRIPT_DIR"
    if docker-compose ps 2>/dev/null | grep -q "Up"; then
        echo -e "${YELLOW}Остановка Docker контейнеров...${NC}"
        docker-compose down 2>/dev/null
        echo -e "${GREEN}✓ Docker контейнеры остановлены${NC}"
    else
        echo -e "${GREEN}✓ Docker контейнеры не запущены${NC}"
    fi
fi

# Остановка Backend (uvicorn)
echo ""
stop_processes "uvicorn.*app.main:app|python.*uvicorn" "Backend (FastAPI/Uvicorn)"

# Остановка Frontend (vite)
echo ""
stop_processes "vite.*--port 5173|node.*vite" "Frontend (Vite)"

# Остановка процессов на портах проекта
echo ""
echo -e "${YELLOW}Проверка портов 8000 и 5173...${NC}"

# Порт 8000 (Backend)
PORT_8000=$(lsof -ti:8000 2>/dev/null)
if [ ! -z "$PORT_8000" ]; then
    echo -e "${YELLOW}  Освобождение порта 8000...${NC}"
    kill $PORT_8000 2>/dev/null
    sleep 1
    REMAINING_8000=$(lsof -ti:8000 2>/dev/null)
    if [ ! -z "$REMAINING_8000" ]; then
        kill -9 $REMAINING_8000 2>/dev/null
    fi
    echo -e "${GREEN}✓ Порт 8000 освобожден${NC}"
else
    echo -e "${GREEN}✓ Порт 8000 свободен${NC}"
fi

# Порт 5173 (Frontend)
PORT_5173=$(lsof -ti:5173 2>/dev/null)
if [ ! -z "$PORT_5173" ]; then
    echo -e "${YELLOW}  Освобождение порта 5173...${NC}"
    kill $PORT_5173 2>/dev/null
    sleep 1
    REMAINING_5173=$(lsof -ti:5173 2>/dev/null)
    if [ ! -z "$REMAINING_5173" ]; then
        kill -9 $REMAINING_5173 2>/dev/null
    fi
    echo -e "${GREEN}✓ Порт 5173 освобожден${NC}"
else
    echo -e "${GREEN}✓ Порт 5173 свободен${NC}"
fi

echo ""
echo -e "${GREEN}✅ Все процессы проекта остановлены!${NC}"
echo ""

