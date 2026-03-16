# # для Python
import os
import sys
import logging
import asyncio
import threading
import uvicorn
from dotenv import load_dotenv

# Настройка путей
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from web.main import app as web_application
# Импортируем твою функцию main, в которой лежат все регистрации хендлеров
from bot.main import main as start_bot_logic

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("BotoLinkPro")

def run_bot_thread():
    # # Создаем новый цикл событий для этого потока
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    logger.info("🤖 Запуск логики бота (регистрация хендлеров + polling)...")
    try:
        # Вызываем твою функцию main() из bot/main.py
        # Она сама сделает initialize, register handlers и start_polling
        loop.run_until_complete(start_bot_logic())
    except Exception as e:
        logger.error(f"❌ Ошибка в потоке бота: {e}")
    finally:
        loop.close()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    
    # 1. Запускаем твою функцию бота в отдельном потоке
    # Это позволит выполнить все твои принты и регистрации хендлеров
    bot_thread = threading.Thread(target=run_bot_thread, daemon=True)
    bot_thread.start()
    
    # 2. Запускаем веб-сервер
    logger.info(f"🌐 Запуск веб-сервера на порту {port}...")
    try:
        uvicorn.run(web_application, host="0.0.0.0", port=port, log_level="info")
    except Exception as e:
        logger.error(f"❌ Ошибка Uvicorn: {e}")