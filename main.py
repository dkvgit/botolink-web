import os
import sys
import logging
import asyncio
import subprocess
from dotenv import load_dotenv
from web.main import app as application
# Добавляем путь, чтобы Python видел папки web и bot
sys.path.append(os.path.dirname(os.path.abspath(__file__)))



# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("BotoLinkPro")

# Экспортируем приложение для Railway, чтобы uvicorn нашел его в этом файле
try:
    from web.main import app as application
except ImportError:
    # Если запуск идет в режиме только бота и папка web не нужна
    application = None

def run_bot():
    """Запуск Telegram бота"""
    try:
        # Динамический импорт бота
        from bot.main import main as bot_main
        logger.info("🤖 Запуск Telegram бота...")
        asyncio.run(bot_main())
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта бота: {e}")
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен")
    except Exception as e:
        logger.exception(f"❌ Критическая ошибка бота: {e}")

def run_web():
    """Запуск веб-сервера (локально)"""
    try:
        import uvicorn
        # Берем порт из переменных окружения (важно для Railway) или 8000
        port = int(os.getenv("PORT", 8000))
        is_debug = os.getenv("DEBUG", "false").lower() == "true"

        logger.info(f"🌐 Запуск веб-сервера на порту {port} (Debug: {is_debug})")
        # Обращаемся к web.main:app
        uvicorn.run("web.main:app", host="0.0.0.0", port=port, reload=is_debug)
    except Exception as e:
        logger.exception(f"❌ Ошибка запуска веб-сервера: {e}")

def run_all():
    """Параллельный запуск бота и веб-сервера через subprocess"""
    logger.info("🚀 Запуск всех компонентов BotoLinkPro...")
    
    # Запускаем этот же файл с аргументом 'bot'
    bot_process = subprocess.Popen([sys.executable, sys.argv[0], "bot"])

    try:
        run_web()
    except KeyboardInterrupt:
        logger.info("🛑 Остановка...")
    finally:
        bot_process.terminate()
        bot_process.wait(timeout=5)
        logger.info("✅ Все процессы остановлены.")

if __name__ == "__main__":
    # Если аргументов нет, по умолчанию запускаем 'all'
    command = sys.argv[1] if len(sys.argv) > 1 else "all"

    if command == "bot":
        run_bot()
    elif command == "web":
        run_web()
    elif command == "all":
        run_all()
    else:
        print(f"Использование: python main.py [bot|web|all]")