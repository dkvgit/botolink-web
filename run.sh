#!/bin/bash

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Запуск botoLinkPro...${NC}"

# Проверка наличия .env
if [ ! -f .env ]; then
    echo -e "${RED}❌ Файл .env не найден!${NC}"
    echo "Создайте .env из .env.example"
    exit 1
fi

# Загрузка переменных
source .env

# Функция для проверки запущен ли процесс
check_process() {
    if pgrep -f "$1" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Запуск PostgreSQL (если локально)
if ! check_process "postgres"; then
    echo -e "${BLUE}📦 Запуск PostgreSQL...${NC}"
    sudo service postgresql start
fi

# Запуск Redis (если локально)
if ! check_process "redis-server"; then
    echo -e "${BLUE}📦 Запуск Redis...${NC}"
    sudo service redis-server start
fi

# Активация виртуального окружения
if [ ! -d "venv" ]; then
    echo -e "${BLUE}📦 Создание виртуального окружения...${NC}"
    python3 -m venv venv
fi

source venv/bin/activate

# Установка зависимостей
echo -e "${BLUE}📦 Установка зависимостей...${NC}"
pip install -r requirements.txt

# Применение миграций
echo -e "${BLUE}📦 Применение миграций...${NC}"
alembic upgrade head

# Заполнение иконок (если нужно)
echo -e "${BLUE}📦 Заполнение иконок...${NC}"
python -m core.seed_icons

# Запуск FastAPI в фоне
echo -e "${BLUE}🌐 Запуск веб-сервера...${NC}"
uvicorn web.main:app --host 0.0.0.0 --port 8000 --reload &
WEB_PID=$!
echo -e "${GREEN}✅ Веб-сервер запущен (PID: $WEB_PID)${NC}"

# Запуск Telegram бота
echo -e "${BLUE}🤖 Запуск Telegram бота...${NC}"
python bot/main.py &
BOT_PID=$!
echo -e "${GREEN}✅ Бот запущен (PID: $BOT_PID)${NC}"

# Запуск Celery (опционально)
if [ "$USE_CELERY" = "true" ]; then
    echo -e "${BLUE}⚙️ Запуск Celery worker...${NC}"
    celery -A tasks.analytics worker --loglevel=info &
    CELERY_PID=$!
    echo -e "${GREEN}✅ Celery запущен (PID: $CELERY_PID)${NC}"
fi

echo -e "${GREEN}✅ Все компоненты запущены!${NC}"
echo -e "${GREEN}📱 Веб-интерфейс: http://localhost:8000${NC}"
echo -e "${GREEN}🤖 Бот: @botolinkprobot${NC}"
echo ""
echo "Для остановки: pkill -f 'uvicorn|python bot/main.py|celery'"

# Ожидание завершения
wait $WEB_PID $BOT_PID