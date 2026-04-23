import os
from dotenv import load_dotenv

load_dotenv()  # Загрузка из .env (локально)

def get_env(key: str, default=None, required=False):
    value = os.getenv(key, default)
    if required and not value:
        raise ValueError(f"❌ Ошибка: Переменная окружения {key} не задана!")
    return value

# Режим отладки (true для тестов на Render, false для лайва)
DEBUG = get_env("DEBUG", "false").lower() == "true"

# База данных
DATABASE_URL = get_env("DATABASE_URL", required=True)
REDIS_URL = get_env("REDIS_URL", "redis://localhost:6379/0")

# Telegram
BOT_TOKEN = get_env("BOT_TOKEN", required=True)
BOT_USERNAME = get_env("BOT_USERNAME", "botolinkpro")

# Web
APP_URL = get_env("APP_URL", "https://botolink.pro")
SECRET_KEY = get_env("SECRET_KEY", "dev-secret-key-change-me")

# --- STRIPE LOGIC ---
if DEBUG:
    # ТЕСТОВЫЙ РЕЖИМ (твои текущие тесты на Render)
    STRIPE_SECRET_KEY = get_env("STRIPE_TEST_SK", required=True)
    GUIDE_PRICE_ID = get_env("STRIPE_TEST_PRICE", required=True)
    STRIPE_WEBHOOK_SECRET = get_env("STRIPE_TEST_WEBHOOK_SECRET", "")
    print("🛠 Stripe: Работаем в TEST режиме (используем ключи sk_test_...)")
else:
    # БОЕВОЙ РЕЖИМ
    STRIPE_SECRET_KEY = get_env("STRIPE_SECRET_KEY", required=True)
    GUIDE_PRICE_ID = get_env("STRIPE_GUIDE_PRICE_ID", required=True)
    STRIPE_WEBHOOK_SECRET = get_env("STRIPE_WEBHOOK_SECRET", required=True)
    print("🚀 Stripe: Работаем в LIVE режиме (используем ключи sk_live_...)")

# Пробрасываем тестовые переменные как опциональные, чтобы импорты в других файлах не крашились
STRIPE_TEST_SK = get_env("STRIPE_TEST_SK", "")
STRIPE_TEST_PRICE = get_env("STRIPE_TEST_PRICE", "")
STRIPE_PUBLIC_KEY = get_env("STRIPE_PUBLIC_KEY", "")
# --------------------

# Секретный ключ для прямой ссылки на скачивание
DOWNLOAD_SECRET = get_env("DOWNLOAD_SECRET", required=True)

# Путь к PDF файлу гайда
GUIDE_PATH = get_env("GUIDE_PATH", "app_data/guide_vnt_2026.pdf")

# Админы
raw_admin_ids = get_env("ADMIN_IDS", "")
ADMIN_IDS = [int(i.strip()) for i in raw_admin_ids.split(",") if i.strip().isdigit()]

# Лимиты (те самые, из-за которых был ImportError)
FREE_LINKS_LIMIT = int(get_env("FREE_LINKS_LIMIT", 3))
PRO_LINKS_LIMIT = int(get_env("PRO_LINKS_LIMIT", 50))