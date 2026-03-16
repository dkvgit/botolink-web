# # для Python
import os
import sys
import logging
import asyncio
import threading
from dotenv import load_dotenv

# Добавляем пути, чтобы Python видел папки web и bot
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("BotoLinkPro")

# Экспортируем приложение для Railway
try:
    from web.main import app as application
except ImportError:
    logger.error("❌ Не удалось импортировать FastAPI app из web.main")
    application = None

def run_bot():
    """Запуск Telegram бота"""
    try:
        from bot.main import main as bot_main
        logger.info("🤖 Инициализация Telegram бота...")
        # Создаем новый цикл событий для отдельного потока
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot_main())
    except Exception as e:
        logger.exception(f"❌ Критическая ошибка бота: {e}")

def run_web():
    """Запуск веб-сервера (Uvicorn)"""
    try:
        import uvicorn
        port = int(os.getenv("PORT", 8000))
        logger.info(f"🌐 Запуск веб-сервера на порту {port}")
        # Передаем объект application напрямую, чтобы избежать проблем с ASGI lifespan
        uvicorn.run(application, host="0.0.0.0", port=port)
    except Exception as e:
        logger.exception(f"❌ Ошибка запуска веб-сервера: {e}")

def run_all_railway():
    """Запуск бота в потоке и сервера в основном процессе"""
    logger.info("🚀 Запуск всех компонентов BotoLinkPro...")
    
    # Запускаем бота фоновым потоком (надежнее subprocess на Railway)
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    # Запускаем веб-сервер в основном потоке
    run_web()

if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "all"

    if command == "bot":
        from bot.main import main as bot_main
        asyncio.run(bot_main())
    elif command == "web":
        run_web()
    elif command == "all":
        run_all_railway()
    else:
        print(f"Использование: python main.py [bot|web|all]")