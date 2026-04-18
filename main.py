import os
import sys
import logging
import uvicorn
from dotenv import load_dotenv

# Добавляем пути, чтобы Python видел папки web и bot
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("BotoLinkPro")

# Импортируем FastAPI приложение
try:
    from web.main import app as application
    logger.info("✅ Успешно импортирован bot_app через web.main")
except ImportError as e:
    logger.error(f"❌ Не удалось импортировать FastAPI app: {e}")
    application = None


def start_app():
    """Запуск единого процесса: Сайт + Бот через Webhook"""
    # Hugging Face сам подставит 7860, локалка возьмет 8000
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"🌐 Запуск единого сервиса на порту {port}")
    
    # Передаем путь строкой "web.main:app".
    # Это надежнее для Docker и позволяет избежать проблем с областью видимости.
    uvicorn.run("web.main:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    # На Hugging Face аргументы обычно не передаются, поэтому будет "all"
    command = sys.argv[1] if len(sys.argv) > 1 else "all"

    if command == "all":
        start_app()
    
    elif command == "bot":
        try:
            import asyncio
            from bot.main import run_local
            logger.info("🤖 Запуск бота в режиме LOCAL POLLING...")
            asyncio.run(run_local())
        except Exception as e:
            logger.error(f"❌ Ошибка запуска бота: {e}")