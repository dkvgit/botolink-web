import os
from dotenv import load_dotenv

load_dotenv()

def get_env(key: str, default=None, required=False):
    value = os.getenv(key, default)
    # Печатаем в логи Render, что мы пытаемся достать (без палева полных ключей)
    if value:
        print(f"✅ [CONFIG] {key} найдена (начинается на: {str(value)[:8]}...)")
    else:
        print(f"❓ [CONFIG] {key} НЕ найдена")
        
    if required and not value:
        raise ValueError(f"❌ Ошибка: Переменная окружения {key} не задана!")
    return value

# Сначала читаем DEBUG, чтобы понять режим
DEBUG_RAW = os.getenv("DEBUG", "false").lower()
DEBUG = DEBUG_RAW == "true"

print(f"--- ЗАПУСК (DEBUG={DEBUG}) ---")

# База и Бот (обязательны всегда)
DATABASE_URL = get_env("DATABASE_URL", required=True)
BOT_TOKEN = get_env("BOT_TOKEN", required=True)

# --- ЛОГИКА STRIPE ДЛЯ ТЕСТОВ НА RENDER ---
if DEBUG:
    # Если мы тестируем на Render (DEBUG=true), нам НУЖНЫ эти ключи
    STRIPE_SECRET_KEY = get_env("STRIPE_TEST_SK", required=True)
    GUIDE_PRICE_ID = get_env("STRIPE_TEST_PRICE", required=True)
    STRIPE_WEBHOOK_SECRET = get_env("STRIPE_TEST_WEBHOOK_SECRET", "")
else:
    # Если мы в LIVE
    STRIPE_SECRET_KEY = get_env("STRIPE_SECRET_KEY", required=True)
    GUIDE_PRICE_ID = get_env("STRIPE_GUIDE_PRICE_ID", required=True)
    STRIPE_WEBHOOK_SECRET = get_env("STRIPE_WEBHOOK_SECRET", required=True)

# Чтобы другие файлы не падали, если ищут TEST ключи в LIVE режиме
STRIPE_TEST_SK = os.getenv("STRIPE_TEST_SK", "")
STRIPE_TEST_PRICE = os.getenv("STRIPE_TEST_PRICE", "")

# Остальное
APP_URL = get_env("APP_URL", "https://botolink.pro")
DOWNLOAD_SECRET = get_env("DOWNLOAD_SECRET", required=True)
GUIDE_PATH = get_env("GUIDE_PATH", "app_data/guide_vnt_2026.pdf")

print("--- КОНФИГ ЗАГРУЖЕН УСПЕШНО ---")