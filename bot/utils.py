# # bot/utils.py

import logging
import traceback
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
import asyncpg
from core.config import DATABASE_URL

logger = logging.getLogger("BotoLinkPro")

# # ============================================
# # РАБОТА С БАЗОЙ ДАННЫХ
# # ============================================

async def get_db_connection():
    # # для Python
    # # Используем данные для Supabase через Connection Pooler (порт 6543)
    config = {
        "user": "postgres.jqvynmpkdjtalsrhvvov",
        "password": "UqyVWSwMA4yvwep6",
        "host": "aws-1-ap-southeast-2.pooler.supabase.com",
        "port": 6543,
        "database": "postgres",
        "ssl": "require",
        "statement_cache_size": 0,
        "timeout": 30
    }

    try:
        conn = await asyncpg.connect(**config)
        return conn
    except asyncpg.exceptions.InvalidPasswordError:
        print("❌ Пароль еще не обновился в пулере. Подожди 60 секунд...")
        raise
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        raise e


# # bot/utils.py

async def get_or_create_user(conn, tg_id, username, first_name, last_name=None):
    # # last_name=None делает аргумент необязательным.
    # # Теперь можно вызывать и с 4, и с 5 аргументами!

    # # 1. Пытаемся обновить юзера (используем COALESCE для last_name, чтобы не затереть старое пустотой)
    user = await conn.fetchrow("""
        UPDATE users
        SET username = $2,
            first_name = $3,
            last_name = $4,
            last_activity = CURRENT_TIMESTAMP
        WHERE telegram_id = $1
        RETURNING *
    """, tg_id, username, first_name, last_name)
    
    if not user:
        # # 2. Если не нашли — создаем нового
        user = await conn.fetchrow("""
            INSERT INTO users (telegram_id, username, first_name, last_name, created_at)
            VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
            RETURNING *
        """, tg_id, username, first_name, last_name)
        
        # # 3. Создаем страницу для новичка
        await conn.execute("""
            INSERT INTO pages (user_id, username, title, template_id)
            VALUES ($1, $2, $3, 1) ON CONFLICT (user_id) DO NOTHING
        """, user['id'], username or f"user_{tg_id}", f"Страница {first_name}")

    # # 4. Страховка: проверяем наличие страницы
    page_exists = await conn.fetchval("SELECT 1 FROM pages WHERE user_id = $1", user['id'])
    if not page_exists:
        await conn.execute("""
            INSERT INTO pages (user_id, username, title, template_id)
            VALUES ($1, $2, $3, 1)
        """, user['id'], username or f"user_{tg_id}", f"Страница {first_name}")
    
    return user




async def check_subscription(conn, user_id: int):
    # # user_id здесь — это telegram_id пользователя
    # # Достаем данные именно из таблицы users, как в твоем дампе
    sql_query = """
                SELECT
                    is_pro,
                    pro_expires_at,
                    is_admin,
                    EXTRACT(EPOCH FROM (pro_expires_at - NOW())) as seconds_left
                FROM public.users
                WHERE telegram_id = $1
                """
    
    row = await conn.fetchrow(sql_query, user_id)
    
    # # Отладка в консоль PyCharm (поможет понять, видит ли бот юзера)
    print(f"--- DEBUG SUB: TG_ID {user_id} ---")
    if row:
        print(f"DB Data: is_pro={row['is_pro']}, is_admin={row['is_admin']}, seconds={row['seconds_left']}")
    else:
        print("DB Data: User NOT FOUND in database!")

    if not row:
        return {'active': False, 'days_left': 0, 'time_left_str': "не активна"}

    # # Если админ — даем PRO автоматом
    if row['is_admin'] is True:
        return {'active': True, 'days_left': 999, 'time_left_str': "безлимитно"}

    # # Проверяем флаг PRO
    if not row['is_pro']:
        return {'active': False, 'days_left': 0, 'time_left_str': "не активна"}
    
    # # Проверяем время (если seconds_left < 0, значит подписка протухла)
    seconds = row['seconds_left']
    if seconds is not None and seconds < 0:
        return {'active': False, 'days_left': 0, 'time_left_str': "истекла"}
    
    # # Если даты нет, но is_pro=True — считаем активной (вечной)
    if seconds is None:
        return {'active': True, 'days_left': 365, 'time_left_str': "активна"}
        
    days = int(seconds) // 86400
    
    return {
        'active': True,
        'days_left': days,
        'time_left_str': f"{days} дн." if days > 0 else "меньше дня"
    }

# # ============================================
# # ОБРАБОТКА ОШИБОК И ЛОГИРОВАНИЕ
# # ============================================

async def log_error(error, context_info=""):
    # # Логирует ошибку с трассировкой стека
    tb_list = traceback.format_exception(None, error, error.__traceback__)
    tb_string = "".join(tb_list)
    logger.error(f"❌ Ошибка {context_info}: {error}\n{tb_string}")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    # # Глобальный обработчик ошибок для PTB
    logger.error("Exception while handling an update:", exc_info=context.error)
    
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Произошла внутренняя ошибка. Мы уже работаем над её исправлением."
        )


def safe_callback(func):
    # # Декоратор для безопасного выполнения callback функций
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            return await func(update, context)
        except Exception as e:
            await log_error(e, f"в {func.__name__}")
            try:
                if update.callback_query:
                    await update.callback_query.answer("❌ Произошла ошибка")
                elif update.message:
                    await update.message.reply_text("❌ Произошла ошибка")
            except:
                pass
            return None
    return wrapper


# # ============================================
# # ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# # ============================================

def format_card(card_number: str) -> str:
    card = ''.join(filter(str.isdigit, card_number))
    if len(card) == 16:
        return f"{card[:4]} {card[4:8]} {card[8:12]} {card[12:]}"
    return card_number

def format_phone(phone: str) -> str:
    return ''.join(filter(lambda x: x.isdigit() or x == '+', phone))

def clean_digits(text: str) -> str:
    return ''.join(filter(str.isdigit, text))


# # ============================================
# # ЭКСПОРТ
# # ============================================
__all__ = [
    'get_db_connection',
    'check_subscription',
    'get_or_create_user',
    'log_error',
    'error_handler',
    'safe_callback',
    'format_card',
    'format_phone',
    'clean_digits'
]