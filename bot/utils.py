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

# // D:\aRabota\TelegaBoom\030_mylinkspace\bot\utils.py

# // D:\aRabota\TelegaBoom\030_mylinkspace\bot\utils.py

import asyncpg
import asyncio

class SmartConnectionManager:
    """
    Умный менеджер: поддерживает и 'await get_db_connection()'
    и 'async with get_db_connection()'.
    """
    def __init__(self):
        # Импортируем URL из конфига
        from core.config import DATABASE_URL
        self.db_url = DATABASE_URL
        self.conn = None

    def _get_clean_url(self):
        """Очищает URL от префикса SQLAlchemy для работы с чистым asyncpg"""
        if self.db_url and "postgresql+asyncpg://" in self.db_url:
            # asyncpg не понимает префикс postgresql+asyncpg
            return self.db_url.replace("postgresql+asyncpg://", "postgresql://")
        return self.db_url

    def __await__(self):
        """Позволяет писать: conn = await get_db_connection()"""
        clean_url = self._get_clean_url()
        # Добавляем timeout=10, чтобы база не 'вешала' бота на Hugging Face
        return asyncpg.connect(clean_url, statement_cache_size=0, timeout=10).__await__()

    async def __aenter__(self):
        """Позволяет писать: async with get_db_connection() as conn:"""
        clean_url = self._get_clean_url()
        try:
            # Обязательно statement_cache_size=0 для работы через PgBouncer (Supabase)
            self.conn = await asyncpg.connect(clean_url, statement_cache_size=0, timeout=10)
            return self.conn
        except Exception as e:
            logger.error(f"❌ [DB ERROR] Ошибка подключения к Supabase: {e}")
            raise e

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрывает соединение после выхода из блока"""
        if self.conn:
            try:
                await self.conn.close()
            except Exception as e:
                logger.warning(f"⚠️ Ошибка при закрытии соединения БД: {e}")

def get_db_connection():
    """Универсальная функция подключения к БД"""
    return SmartConnectionManager()

async def get_or_create_user(conn, tg_id, username, first_name, last_name=None):
    # 1. Пытаемся обновить юзера.
    # Если юзер уже есть, UPDATE вернет его данные.
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
        # 2. Если не нашли — создаем нового юзера
        # Оборачиваем в try/except, чтобы избежать проблем при гонке запросов
        try:
            user = await conn.fetchrow("""
                INSERT INTO users (telegram_id, username, first_name, last_name, created_at)
                VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
                RETURNING *
            """, tg_id, username, first_name, last_name)
            
            # 3. Создаем страницу только для нового юзера
            # ВАЖНО: username для страницы не может быть None (если в БД NOT NULL)
            page_slug = username or f"id{tg_id}"
            
            await conn.execute("""
                INSERT INTO pages (user_id, slug, title, template_id)
                VALUES ($1, $2, $3, 1)
                ON CONFLICT (user_id) DO NOTHING
            """, user['id'], page_slug, f"Страница {first_name}")
            
        except Exception as e:
            # Если юзер нажал /start дважды очень быстро, может возникнуть ошибка уникальности
            # В таком случае просто пробуем достать его еще раз
            user = await conn.fetchrow("SELECT * FROM users WHERE telegram_id = $1", tg_id)

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