
# core/config.py

import os
from dotenv import load_dotenv
import urllib.parse

load_dotenv()  # Это загружает переменные из .env файла

def get_env(key: str, default=None, required=False):
    value = os.getenv(key, default)
    if required and not value:
        raise ValueError(f"❌ Ошибка: Переменная окружения {key} не задана!")
    return value

# Режим отладки
DEBUG = get_env("DEBUG", "false").lower() == "true"


# База данных - берем из переменных окружения
DATABASE_URL = get_env("DATABASE_URL", required=True)

REDIS_URL = get_env("REDIS_URL", "redis://localhost:6379/0")

# Telegram (Токен обязателен!)
BOT_TOKEN = get_env("BOT_TOKEN", required=True)
BOT_USERNAME = get_env("BOT_USERNAME", "botolinkpro")

# Web
APP_URL = get_env("APP_URL", "http://localhost:8000")
SECRET_KEY = get_env("SECRET_KEY", "dev-secret-key-change-me")

# Stripe
STRIPE_PUBLIC_KEY = get_env("STRIPE_PUBLIC_KEY", "")
STRIPE_SECRET_KEY = get_env("STRIPE_SECRET_KEY", "")

# Админы
raw_admin_ids = get_env("ADMIN_IDS", "")
ADMIN_IDS = [int(i.strip()) for i in raw_admin_ids.split(",") if i.strip().isdigit()]

# Лимиты
FREE_LINKS_LIMIT = int(get_env("FREE_LINKS_LIMIT", 3))
PRO_LINKS_LIMIT = int(get_env("PRO_LINKS_LIMIT", 50))