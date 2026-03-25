# # D:\aRabota\TelegaBoom\030_mylinkspace\main.py
import os
import sys
import logging
import uvicorn
from dotenv import load_dotenv

# # Добавляем пути, чтобы Python видел папки web и bot
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# # Загружаем переменные окружения
load_dotenv()

# # Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("BotoLinkPro")

# # Импортируем FastAPI приложение
try:
    from web.main import app as application
except ImportError as e:
    logger.error(f"❌ Не удалось импортировать FastAPI app из web.main: {e}")
    application = None

def start_app():
    # // для Python
    # Запуск единого процесса (Web + Bot через lifespan в web/main.py)
    if not application:
        logger.critical("❌ Невозможно запустить сервер: приложение не импортировано.")
        return

    try:
        port = int(os.getenv("PORT", 8000))
        logger.info(f"🌐 Запуск единого сервиса на порту {port}")
        
        # Запускаем uvicorn. Бот включится сам через lifespan.
        uvicorn.run(application, host="0.0.0.0", port=port)
    except Exception as e:
        logger.exception(f"❌ Ошибка при старте сервиса: {e}")


if __name__ == "__main__":
    # # На Railway всегда будет срабатывать запуск "all"
    command = sys.argv[1] if len(sys.argv) > 1 else "all"

    # Если ты хочешь запускать ВСЁ (и сайт и бота) одной командой:
    if command == "all" or command == "web":
        # Это вызовет uvicorn.run(application)
        # А внутри application (в web/main.py) сработает наш @app.on_event("startup")
        # Которому пофиг, как его запустили — он сам увидит RUN_MODE=polling в .env
        start_app()
    
    elif command == "bot":
        # Режим только бота, если не нужен сайт
        try:
            import asyncio
            from bot.main import run_local
            logger.info("🤖 Запуск только бота в режиме Polling...")
            asyncio.run(run_local())
        except Exception as e:
            logger.error(f"❌ Ошибка запуска бота: {e}")