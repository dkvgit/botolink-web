import os
import sys
import logging
import asyncio
import subprocess
import signal
from dotenv import load_dotenv


# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("BotoLinkPro")

def run_bot():
    """Запуск Telegram бота"""
    try:
        # Импортируем внутри функции, чтобы не грузить лишнее при запуске только WEB
        from bot.main import main as bot_main
        logger.info("🤖 Запуск Telegram бота...")
        asyncio.run(bot_main())
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта бота: {e}")
        print("Подсказка: pip install -r requirements.txt")
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.exception(f"❌ Критическая ошибка бота: {e}")

def run_web():
    """Запуск веб-сервера"""
    try:
        import uvicorn
        # reload=True лучше оставить только для разработки через переменную окружения
        is_debug = os.getenv("DEBUG", "false").lower() == "true"

        logger.info(f"🌐 Запуск веб-сервера на http://127.0.0.1:8000 (Debug: {is_debug})")
        uvicorn.run("web.main:app", host="127.0.0.1", port=8000, reload=is_debug)
    except ImportError:
        logger.error("❌ Ошибка: uvicorn или fastapi не установлены.")
    except Exception as e:
        logger.exception(f"❌ Ошибка запуска веб-сервера: {e}")

def run_all():
    """Запуск и бота, и веб-сервера параллельно"""
    logger.info("🚀 Запуск всех компонентов BotoLinkPro...")

    # Используем sys.executable для уверенности, что запустится тот же интерпретатор
    # Используем sys.argv[0], чтобы запустить этот же файл
    bot_process = subprocess.Popen([sys.executable, sys.argv[0], "bot"])

    try:
        # Веб-сервер запускаем в основном потоке
        run_web()
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки...")
    finally:
        logger.info("⏳ Завершение работы дочерних процессов...")
        # Сначала пробуем вежливо попросить бота закрыться
        bot_process.terminate()
        try:
            bot_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # Если не понял по-хорошему — закрываем принудительно
            bot_process.kill()
        logger.info("✅ Все процессы остановлены.")

if __name__ == "__main__":
    # Выбираем режим работы
    command = sys.argv[1] if len(sys.argv) > 1 else "all"

    if command == "bot":
        run_bot()
    elif command == "web":
        run_web()
    elif command == "all":
        run_all()
    else:
        print(f"Неизвестная команда: {command}")
        print("Использование: python main.py [bot|web|all]")