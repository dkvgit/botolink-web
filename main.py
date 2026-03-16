# # для Python
import os
import sys
import logging
import asyncio
import threading
import uvicorn
from dotenv import load_dotenv

# Добавляем пути, чтобы модули 'web' и 'bot' были видны
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from web.main import app as application
from bot.main import application as bot_app

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("BotoLinkPro")

def run_bot_in_thread():
    # # Внутренняя функция для запуска цикла событий бота в отдельном потоке
    logger.info("🤖 Инициализация потока для Telegram бота...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Инициализируем и запускаем бота (polling или подготовка к webhook)
        loop.run_until_complete(bot_app.initialize())
        loop.run_until_complete(bot_app.start())
        
        # Если ты используешь Webhook, боту не нужно делать polling
        # Но для работы всех внутренних хендлеров updater должен быть запущен
        if bot_app.updater:
            loop.run_until_complete(bot_app.updater.start_polling())
            logger.info("✅ Бот запущен (Polling mode)")
        
        loop.run_forever()
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в потоке бота: {e}")
    finally:
        loop.close()

if __name__ == "__main__":
    # # Определяем порт Railway
    port = int(os.getenv("PORT", 8000))
    
    # # 1. Запускаем бота в фоновом потоке, чтобы он не блокировал Uvicorn
    bot_thread = threading.Thread(target=run_bot_in_thread, daemon=True)
    bot_thread.start()
    
    # # 2. Запускаем основной веб-сервер
    logger.info(f"🌐 Запуск веб-сервера на порту {port}...")
    try:
        # Используем объект application напрямую для стабильности на Railway
        uvicorn.run(application, host="0.0.0.0", port=port, log_level="info")
    except KeyboardInterrupt:
        logger.info("🛑 Остановка сервера пользователем")
    except Exception as e:
        logger.error(f"❌ Ошибка запуска Uvicorn: {e}")