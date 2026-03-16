# bot/handlers.py


import asyncio
import logging
import os
import re
import sys
import time
from io import BytesIO
from bot.utils import get_db_connection
import aiohttp
import asyncpg
import qrcode
import qrcode.constants
import telegram
from PIL import Image, ImageDraw
from bot.avatar_handler import setup_user_avatar
from bot.bank import method_paypal, method_revolut, method_wise, method_swift, revolut_choice_handler, choose_country, \
    back_to_countries, wise_choice_handler, method_idram, method_tbcpay, method_click, method_yoomoney, method_vkpay, \
    method_monobank, method_kaspi, method_payme
from bot.bankworld import show_country_methods, toggle_method
from bot.link_constructor import add_link_start, select_category, select_link_type
from bot.link_utils import add_link_icon
from bot.states import (
    SELECT_LINK_TYPE,  # <--- ДОБАВЬ ЭТО (стейт 10)
    SELECT_FINANCE_SUBTYPE,  # <--- И ЭТО (стейт 11)
    ADD_LINK_TITLE,
    ADD_LINK_URL,
    ADD_LINK_ICON,
    EDIT_LINK_TITLE,
    EDIT_LINK_URL,
    EDIT_LINK_ICON
)
from bot.utils import check_subscription, get_or_create_user
from core import config
from core.config import ADMIN_IDS
from core.config import APP_URL  # APP_URL уже импортируется, но убедитесь что он есть
from core.config import APP_URL
from core.config import DATABASE_URL, APP_URL, FREE_LINKS_LIMIT, PRO_LINKS_LIMIT
from core.database import engine  # Или тот путь, где у тебя лежит файл database.py
from core.models import SubscriptionStatus, PlanType
# Если еще не импортировал для других нужд
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler

# Настройка логгера (тоже вверху, под импортами)
# bot/handlers.py

# 1. Сначала логгер
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
# 2. Потом кэш для валют
currency_cache = {"rates": {}, "last_update": 0}


# 3. Сама функция получения курсов
async def get_rates():
	now = time.time()
	if currency_cache["rates"] and (now - currency_cache["last_update"]) < 3600:
		return currency_cache["rates"]
	try:
		async with aiohttp.ClientSession() as session:
			async with session.get("https://open.er-api.com/v6/latest/RUB") as resp:
				data = await resp.json()
				if data.get("result") == "success":
					rates = data["rates"]
					rates["USDT"] = rates.get("USD", 0)
					currency_cache["rates"] = rates
					currency_cache["last_update"] = now
					return rates
	except Exception as e:
		logger.error(f"Ошибка курсов: {e}")
	return currency_cache["rates"]


# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====




async def get_or_create_user_old(conn, tg_id, username, first_name, last_name=None):
	"""Получить или создать пользователя, синхронизируя статус админа и PRO"""
	
	# Определяем, является ли юзер админом по конфигу
	is_admin_flag = tg_id in config.ADMIN_IDS
	
	# ===== ОБРЕЗАЕМ ДЛИННЫЕ СТРОКИ =====
	
	# 1. Username - обычно VARCHAR(100)
	if username and len(username) > 100:
		username = username[:100]
		print(f"⚠️ Username обрезан до 100 символов")
	
	# 2. First name - обычно VARCHAR(100)
	if first_name and len(first_name) > 100:
		first_name = first_name[:100]
		print(f"⚠️ First name обрезан до 100 символов")
	
	# 3. Last name - обычно VARCHAR(100)
	if last_name and len(last_name) > 100:
		last_name = last_name[:100]
		print(f"⚠️ Last name обрезан до 100 символов")
	
	# 4. Для page_username - тоже VARCHAR(100)
	page_username = username or f"user_{tg_id}"
	if len(page_username) > 100:
		page_username = page_username[:100]
		print(f"⚠️ Page username обрезан до 100 символов")
	
	# 1. Пытаемся найти пользователя
	user = await conn.fetchrow("SELECT * FROM users WHERE telegram_id = $1", tg_id)
	
	if not user:
		# 2. Если пользователя нет, создаем его
		user = await conn.fetchrow("""
                                   INSERT INTO users (telegram_id, username, first_name, last_name,
                                                      language_code, is_admin, is_pro, created_at)
                                   VALUES ($1, $2, $3, $4, 'ru', $5, $6, NOW()) RETURNING *
		                           """,
		                           tg_id,
		                           username,  # обрезанный
		                           first_name,  # обрезанный
		                           last_name,  # обрезанный
		                           is_admin_flag,
		                           is_admin_flag)
		
		# 3. Создаем страницу для нового пользователя
		await conn.execute("""
                           INSERT INTO pages (user_id, username, title, template_id)
                           VALUES ($1, $2, $3, 1) ON CONFLICT (user_id) DO NOTHING
		                   """,
		                   user['id'],
		                   page_username,  # обрезанный
		                   f"Страница {first_name if first_name else ''}"[:100])  # обрезаем title страницы
		
		logger.info(f"✅ Создан новый пользователь: {tg_id} (Admin: {is_admin_flag})")
	else:
		# 4. Если пользователь есть, обновляем его профиль
		await conn.execute("""
                           UPDATE users
                           SET username   = $2,
                               first_name = $3,
                               last_name  = $4,
                               is_admin   = $5
                           WHERE telegram_id = $1
		                   """,
		                   tg_id,
		                   username,  # обрезанный
		                   first_name,  # обрезанный
		                   last_name,  # обрезанный
		                   is_admin_flag)
		
		# 5. ВАЖНО: Проверяем, есть ли у пользователя страница
		page = await conn.fetchrow("SELECT id FROM pages WHERE user_id = $1", user['id'])
		if not page:
			# Если страницы нет - создаем
			await conn.execute("""
                               INSERT INTO pages (user_id, username, title, template_id)
                               VALUES ($1, $2, $3, 1)
			                   """,
			                   user['id'],
			                   page_username,  # обрезанный
			                   f"Страница {first_name if first_name else ''}"[:100])  # обрезаем title страницы
			logger.info(f"✅ Создана недостающая страница для пользователя {tg_id}")
		
		# Если админ и не PRO - даем PRO
		if is_admin_flag and not user['is_pro']:
			await conn.execute("UPDATE users SET is_pro = true WHERE telegram_id = $1", tg_id)
			logger.info(f"✅ Админу {tg_id} выдан PRO-статус")
		
		# Обновляем объект user после изменений
		user = await conn.fetchrow("SELECT * FROM users WHERE telegram_id = $1", tg_id)
	
	return user


# Файл: D:\aRabota\TelegaBoom\030_botolinkpro\bot\handlers.py

# Файл: bot/handlers.py

# bot/utils.py или bot/database.py

# Убедись, что этот импорт есть в файле!


async def check_subscription_old(conn, user_id: int):
	"""
    Универсальная проверка: берет данные напрямую из public.users.
    """
	sql_query = """
                SELECT is_pro,
                       pro_expires_at,
                       EXTRACT(EPOCH FROM (pro_expires_at - NOW())) as seconds_left
                FROM users
                WHERE telegram_id = $1 \
	            """
	
	logger.info(f"🔍 check_subscription: запрос для user_id={user_id}")
	
	row = await conn.fetchrow(sql_query, user_id)
	logger.info(f"🔍 check_subscription: row={row}")
	
	if not row:
		logger.warning(f"🔍 check_subscription: пользователь не найден")
		return {'active': False, 'days_left': 0, 'time_left_str': "не найден"}
	
	try:
		is_pro = row['is_pro']
		seconds = row['seconds_left']
		logger.info(f"🔍 check_subscription: is_pro={is_pro}, seconds={seconds}")
	except Exception as e:
		logger.error(f"🔍 check_subscription: ошибка доступа к данным: {e}")
		is_pro = getattr(row, 'is_pro', False)
		seconds = getattr(row, 'seconds_left', 0)
	
	if not is_pro:
		logger.info(f"🔍 check_subscription: is_pro=False")
		return {'active': False, 'days_left': 0, 'time_left_str': "не активна"}
	
	if seconds is not None and seconds < 0:
		logger.info(f"🔍 check_subscription: истекла (seconds={seconds})")
		return {'active': False, 'days_left': 0, 'time_left_str': "истекла"}
	
	safe_seconds = seconds if seconds is not None else 3153600000
	days = int(safe_seconds) // 86400
	
	result = {
		'active': True,
		'days_left': days,
		'time_left_str': f"{days} дн." if days > 0 else "меньше дня"
	}
	logger.info(f"🔍 check_subscription: результат={result}")
	return result


async def get_user_page(conn, user_id: int):
	"""Получить страницу пользователя"""
	return await conn.fetchrow("""
                               SELECT p.*,
                                      (SELECT COUNT(*) FROM links WHERE page_id = p.id) as links_count
                               FROM pages p
                               WHERE p.user_id = $1
	                           """, user_id)


async def get_user_links(conn, page_id: int):
	"""Получить ссылки пользователя"""
	return await conn.fetch("""
                            SELECT *
                            FROM links
                            WHERE page_id = $1
                              AND is_active = true
                            ORDER BY sort_order
	                        """, page_id)


# ===== БАЗОВЫЕ ОБРАБОТЧИКИ =====

from core.database import engine
from core.config import ADMIN_IDS
import logging

logger = logging.getLogger(__name__)


# Название файла: web/bot/handlers.py

# bot/main.py

# // bot/main.py

async def start_handler(update, context):
    # # Используем # для Python комментариев
    from bot.utils import get_or_create_user, get_db_connection, check_subscription
    from bot.avatar_handler import setup_user_avatar
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    import logging
    import os
    import traceback

    logger = logging.getLogger("BotoLinkPro")
    user = update.effective_user
    if not user:
        return
    
    # # Лог для проверки в панели Railway
    print(f"\n--- [DEBUG] START HANDLER запущен для юзера: {user.id} ---")

    was_deleted = False

    # # 1. Очистка старых сообщений
    if 'last_success_msg_id' in context.user_data:
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=context.user_data['last_success_msg_id']
            )
            was_deleted = True
            print(f"--- [DEBUG] Старое сообщение {context.user_data['last_success_msg_id']} удалено")
        except Exception as e:
            print(f"--- [DEBUG] Не удалось удалить сообщение: {e}")
        context.user_data.pop('last_success_msg_id', None)

    conn = None
    try:
        conn = await get_db_connection()
        print("--- [DEBUG] 1. Соединение с БД установлено")
        
        # # Синхронизируем пользователя
        db_user = await get_or_create_user(
            conn, user.id, user.username, user.first_name, user.last_name
        )
        
        # # 2. ПРОВЕРЯЕМ ПОДПИСКУ
        sub_status = await check_subscription(conn, user.id)
        
        if sub_status['active']:
            status_text = f"💎 <b>Статус:</b> PRO ({sub_status['time_left_str']})"
        else:
            status_text = "💡 <b>Статус:</b> Бесплатный"

        current_name = db_user['first_name'] or user.username or f"ID_{user.id}"
        page_title = f"Страница {current_name}"
        
        await conn.execute(
            "UPDATE pages SET title = $1 WHERE user_id = $2",
            page_title, db_user['id']
        )

        # # Аватар
        try:
            await setup_user_avatar(user.id, context.bot, conn)
            print("--- [DEBUG] 2. Аватар обработан")
        except Exception as e:
            print(f"--- [DEBUG] Ошибка аватара (не критично): {e}")

        page = await conn.fetchrow("""
            SELECT p.*, t.name as template_name, t.is_pro as template_is_pro
            FROM pages p
            LEFT JOIN templates t ON p.template_id = t.id
            WHERE p.user_id = $1
        """, db_user['id'])

        if not page:
            page_username = user.username or f"user_{user.id}"
            page = await conn.fetchrow("""
                INSERT INTO pages (user_id, username, title, template_id)
                VALUES ($1, $2, $3, 1) RETURNING *
            """, db_user['id'], page_username, page_title)

        links_count = await conn.fetchval(
            "SELECT COUNT(*) FROM links WHERE page_id = $1 AND is_active = true",
            page['id']
        ) or 0

        # # БЕРЕМ URL ИЗ ENV
        base_url = os.getenv("APP_URL", "https://botolink-web-production-b49b.up.railway.app").rstrip('/')

        text_msg = (
            f"👋 Привет, <b>{db_user['first_name']}</b>!\n"
            f"Твоя главная команда: /start\n\n"
            f"📌 <b>Твоя страница уже работает:</b>\n"
            f"👉 <a href='{base_url}/{page['username']}'>{base_url}/{page['username']}</a>\n\n"
            f"🎨 <b>Шаблон:</b> {page['template_name'] or 'Классический'} {'(⭐ PRO)' if page.get('template_is_pro') else '(🆓 Бесплатный)'}\n"
            f"🔗 <b>Ссылок:</b> {links_count}\n"
            f"👀 <b>Просмотров:</b> {page['view_count'] or 0}\n"
            f"────────────────────\n"
            f"{status_text}\n\n"
            f"Что хочешь сделать?"
        )

        keyboard = [
            [InlineKeyboardButton("📋 Моя страница", callback_data="mysite"),
             InlineKeyboardButton("🔳 QR-код", callback_data="qr")],
            [InlineKeyboardButton("🔗 Изменить адрес (URL)", callback_data="change_nick")],
            [InlineKeyboardButton("🔗 Управление ссылками", callback_data="links"),
             InlineKeyboardButton("➕ Добавить ссылку", callback_data="add_link")],
            [InlineKeyboardButton("🎨 Выбрать шаблон", callback_data="templates_menu"),
             InlineKeyboardButton("📊 Статистика", callback_data="stats")],
            [InlineKeyboardButton("⚙️ Профиль", callback_data="profile")]
        ]

        # # Проверка админа через переменную окружения
        raw_admins = os.getenv("ADMIN_IDS", "")
        admin_list = [a.strip() for a in raw_admins.split(',') if a.strip()]
        if str(user.id) in admin_list:
            keyboard.append([InlineKeyboardButton("👑 АДМИН-ПАНЕЛЬ", callback_data="admin_list_users")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        # # Логика отправки
        if update.callback_query and not was_deleted:
            sent_msg = await update.callback_query.edit_message_text(
                text=text_msg, reply_markup=reply_markup, parse_mode='HTML', disable_web_page_preview=True
            )
        else:
            if update.callback_query:
                await update.callback_query.answer()
            
            sent_msg = await update.message.reply_text(
                text=text_msg, reply_markup=reply_markup, parse_mode='HTML', disable_web_page_preview=True
            )
        
        context.user_data['last_success_msg_id'] = sent_msg.message_id
        print("--- [DEBUG] !!! ВСЁ ОК, СООБЩЕНИЕ ОТПРАВЛЕНО ---")

    except Exception as e:
        print(f"--- [DEBUG] !!! КРИТИЧЕСКАЯ ОШИБКА В START_HANDLER: {e}")
        traceback.print_exc()
        logger.error(f"❌ Ошибка в start_handler: {e}", exc_info=True)
    finally:
        if conn:
            await conn.close()
            print("--- [DEBUG] 8. Соединение закрыто")
		    
		    
		    
		    
# bot/handlers.py

async def change_nick_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Отмена смены ника и возврат в ГЛАВНОЕ МЕНЮ"""
	user = update.effective_user
	
	print(f"🔥🔥🔥 button_handler получил: {update.callback_query.data}")
	
	# 1. Очищаем временные данные, если они были
	context.user_data.pop('pending_new_nick', None)
	
	# 2. Получаем соединение для проверки статуса (для отрисовки кнопок)
	conn = await get_db_connection()
	try:
		# Используем нашу новую универсальную функцию!
		sub_status = await check_subscription(conn, user.id)
		is_pro = sub_status.get('active', False)
		is_admin = user.id in ADMIN_IDS
		
		# Создаем ПРАВИЛЬНУЮ клавиатуру
		reply_markup = main_menu_keyboard(is_pro=is_pro, is_admin=is_admin)
		
		text_msg = "❌ Изменение адреса отменено.\n\nВозвращаюсь в главное меню..."
		
		if update.callback_query:
			await update.callback_query.edit_message_text(text_msg, reply_markup=reply_markup)
		else:
			await update.message.reply_text(text_msg, reply_markup=reply_markup)
	
	finally:
		await conn.close()
	
	return ConversationHandler.END


# bot/handlers.py

async def change_username_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	user_id = update.effective_user.id
	
	if query:
		await query.answer()
	
	logger.info(f"Пользователь {user_id} начал процесс смены ника")
	
	current_nick = "не установлен"
	async with engine.begin() as conn:
		result = await conn.execute(
			text("SELECT username FROM pages WHERE user_id = (SELECT id FROM users WHERE telegram_id = :tid)"),
			{"tid": user_id}
		)
		row = result.fetchone()
		if row and row.username:
			current_nick = row.username
	
	# Используем HTML вместо Markdown, чтобы избежать ошибок парсинга символа "_"
	text_msg = (
		"<b>🔗 Настройка адреса твоей страницы</b>\n\n"
		f"Сейчас твоя ссылка: <code>http://localhost:8000/{current_nick}</code>\n\n"
		"Ты можешь заменить скучный ID на красивое имя!\n"
		"Например, если введешь <b>flowers</b>, ссылка станет:\n"
		"└ <code>http://localhost:8000/flowers</code>\n\n"
		"📝 <b>Пришли мне новое имя:</b>\n"
		"— Только латинские буквы (a-z), цифры и _\n"
		"— Длина от 3 до 25 символов\n\n"
		"⚠️ <b>Важно:</b> после смены старая ссылка перестанет открываться!\n"
		"————————————————————\n"
		"Для отмены нажми 👉 /cancel"
	)
	
	try:
		if query:
			await query.edit_message_text(
				text=text_msg,
				parse_mode='HTML'  # МЕНЯЕМ НА HTML
			)
		else:
			await update.message.reply_text(
				text=text_msg,
				parse_mode='HTML'  # МЕНЯЕМ НА HTML
			)
	except Exception as e:
		logger.error(f"Ошибка в change_username_start: {e}")
		# Если всё равно упало, отправляем как чистый текст без разметки
		await context.bot.send_message(
			chat_id=user_id,
			text=text_msg.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", "")
		)
	
	return "WAITING_FOR_NICKNAME"


async def change_nick_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Начало смены ника (адреса страницы)"""
	print(f"🔥🔥🔥 button_handler получил: {update.callback_query.data}")
	# Получаем текущий username пользователя
	user = update.effective_user
	conn = await get_db_connection()
	try:
		db_user = await get_or_create_user(conn, user.id, user.username, user.first_name)
		page = await get_user_page(conn, db_user['id'])
		current_username = page['username']
	finally:
		await conn.close()
	
	# Формируем текущую ссылку
	base_url = "http://localhost:8000"  # или APP_URL из конфига
	current_url = f"{base_url}/{current_username}"
	
	text_msg = (
		"🔗 **Настройка адреса твоей страницы**\n\n"
		f"Сейчас твоя ссылка выглядит так:\n"
		f"└ `{current_url}`\n\n"
		"Ты можешь заменить скучный id на красивое имя!\n"
		"Например, если введешь `flowers`, ссылка станет:\n"
		"└ `http://localhost:8000/flowers`\n\n"
		"📝 **Пришли мне новое имя:**\n"
		"— Используй только латинские буквы (a-z), цифры и _\n"
		"— Длина от 3 до 20 символов\n\n"
		"⚠️ **Важно:** после смены старая ссылка перестанет открываться!\n\n"
		"————————————————————\n"
		"Для отмены нажми 👉 /cancel"
	)
	
	# Отправляем сообщение
	if update.callback_query:
		await update.callback_query.edit_message_text(
			text=text_msg,
			parse_mode='Markdown'
		)
	else:
		await update.message.reply_text(
			text_msg,
			parse_mode='Markdown'
		)
	
	return "WAITING_FOR_NICK"


# Function: pro_info_callback
# Название файла: bot/handlers.py

async def pro_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Показывает отличия платной и бесплатной версии"""
	query = update.callback_query
	
	# # Логируем нажатие для отладки
	print(f"🔥🔥🔥 pro_info_callback получил: {query.data}")
	
	await query.answer()
	
	text = (
		"💎 **ВОЗМОЖНОСТИ BotoLinkPro**\n\n"
		"⚪️ **БЕСПЛАТНАЯ ВЕРСИЯ:**\n"
		"- Только ссылки (лимит: 3 шт)\n"
		"- 3 базовых шаблона оформления\n"
		"- QR-код вашей страницы\n"
		"- Общая статистика просмотров\n\n"
		"👑 **PRO ПОДПИСКА:**\n"
		"- Ссылки, донаты, банковские карты, крипто-кошельки\n"
		"- Увеличенный лимит ссылок: **до 50 шт.**\n"
		"- Доступ ко всем **премиум-шаблонам**\n"
		"- Собственный настраиваемый QR-код (добавление надписи)\n"
		"- Детальная аналитика по кликам (скоро)\n"
		"- Приоритетная поддержка\n"
		"- Премиум функции будут добавляться со временем\n\n"
		"✨ _PRO-версия - это максимум инструментов для вашего бренда!_"
	)
	
	keyboard = [
		[InlineKeyboardButton("💳 Купить PRO подписку", callback_data="upgrade")],
		[InlineKeyboardButton("👨‍💻 Личный дизайн под ключ", url="https://t.me/dekavetel")],
		[InlineKeyboardButton("◀️ Назад в меню", callback_data="start")]
	]
	
	try:
		await query.edit_message_text(
			text=text,
			reply_markup=InlineKeyboardMarkup(keyboard),
			parse_mode='Markdown'
		)
	except Exception as e:
		logger.error(f"Ошибка в pro_info_callback: {e}")


# Function: save_new_nickname
async def save_new_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE):
	# Добавляем проверку, если вдруг пришло не текстовое сообщение
	if not update.message or not update.message.text:
		return "WAITING_FOR_NICKNAME"
	
	new_nick = update.message.text.strip().lower()
	user_id = update.effective_user.id
	
	# 1. Валидация (только латиница, цифры и подчеркивание)
	if not re.match(r"^[a-z0-9_]{3,25}$", new_nick):
		await update.message.reply_text(
			"❌ **Ошибка в формате!**\n\n"
			"Используй только латинские буквы (a-z), цифры и `_`.\n"
			"Длина: от 3 до 25 символов.",
			parse_mode='Markdown'
		)
		return "WAITING_FOR_NICKNAME"
	
	# Запрещенные системные имена
	forbidden = ['admin', 'api', 'static', 'login', 'help', 'root']
	if new_nick in forbidden:
		await update.message.reply_text("🚫 этот адрес зарезервирован. Выбери другой!")
		return "WAITING_FOR_NICKNAME"
	
	async with engine.begin() as conn:
		# 2. Проверка на занятости в базе
		check = await conn.execute(
			text("SELECT user_id FROM pages WHERE username = :n"),
			{"n": new_nick}
		)
		if check.fetchone():
			await update.message.reply_text("🚫 Этот адрес уже занят другим пользователем!")
			return "WAITING_FOR_NICKNAME"
		
		# 3. Обновление ника в таблице pages
		await conn.execute(text("""
                                UPDATE pages
                                SET username = :n
                                WHERE user_id = (SELECT id FROM users WHERE telegram_id = :tid)
		                        """), {"n": new_nick, "tid": user_id})
	
	# 4. Финальный ответ + Кнопка возврата
	# Вместо того чтобы просто слать текст, мы сразу даем юзеру подтверждение
	# и возвращаем его в главное меню через start_handler
	
	await update.message.reply_text(
		f"🎉 **Готово! Адрес успешно изменен.**\n\n"
		f"Твоя страница теперь здесь:\n"
		f"👉 `http://localhost:8000/{new_nick}`\n\n"
		f"⚠️ Старая ссылка больше не работает.",
		parse_mode='Markdown'
	)
	
	# Вызываем start_handler, чтобы обновить главное меню у юзера
	await start_handler(update, context)
	
	# ПРАВИЛЬНЫЙ ВЫХОД из ConversationHandler
	return ConversationHandler.END


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Обработчик команды /help"""
	text = "❓ Помощь\n\n"
	text += "/start - Главное меню\n"
	text += "/mysite - Моя страница\n"
	text += "/qr - QR-код страницы\n"
	text += "/links - Управление ссылками\n"
	text += "/addlink - Добавить ссылку\n"
	text += "/stats - Статистика\n"
	text += "/upgrade - Управление подпиской\n"
	text += "/profile - Профиль\n"
	text += "/help - Это меню"
	
	await update.message.reply_text(text)


async def mysite_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""
    try1_stmt ::= try ":" suite
                 (except_clause ":" suite)+
                 ["else" ":" suite]
                 ["finally" ":" suite]
    """
	# 1. Сначала чистим уведомления (не критично, если упадет, поэтому в try не пихаем)
	if 'last_success_msg_id' in context.user_data:
		try:
			await context.bot.delete_message(
				chat_id=update.effective_chat.id,
				message_id=context.user_data.pop('last_success_msg_id')
			)
		except:
			pass
	
	user = update.effective_user
	conn = await get_db_connection()
	
	try:
		# ОСНОВНОЙ БЛОК (suite)
		db_user = await get_or_create_user(conn, user.id, user.username, user.first_name)
		page = await get_user_page(conn, db_user['id'])
		links = await get_user_links(conn, page['id'])
		
		# Логика данных
		v_count = page.get('view_count') or 0
		c_count = sum(link.get('click_count', 0) for link in links)
		url = f"{APP_URL}/{page['username']}"
		
		text = (
			f"📋 **Моя страница**\n\n"
			f"🌐 **Ссылка:** [{url}]({url})\n"
			f"────────────────────\n"
			f"👀 Просмотров: `{v_count}`\n"
			f"🔗 Кликов: `{c_count}`\n"
			f"📌 Ссылок: `{len(links)}`"
		)
		
		# Защита от кривых URL для кнопок
		btn_url = url if "localhost" not in url else "https://t.me/bot"
		
		keyboard = InlineKeyboardMarkup([
			[InlineKeyboardButton("👀 Смотреть", url=btn_url)],
			[InlineKeyboardButton("🔳 QR-код", callback_data="qr")],
			[InlineKeyboardButton("✏️ Редакт.", callback_data="edit_page")],
			[InlineKeyboardButton("◀️ Назад", callback_data="start")]
		])
		
		# Отправка
		if update.callback_query:
			await update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
		else:
			await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')
	
	except Exception as e:
		# ОБРАБОТЧИК ИСКЛЮЧЕНИЙ (except_clause)
		logger.error(f"Error in mysite_handler: {e}")
		error_msg = "❌ Ошибка загрузки страницы"
		if update.callback_query:
			await update.callback_query.edit_message_text(error_msg)
		else:
			await update.message.reply_text(error_msg)
	
	finally:
		# ОЧИСТКА (cleanup code)
		# Этот блок выполнится ВСЕГДА: и при успехе, и при ошибке
		await conn.close()


# bot/handlers.py

async def qr_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Генерация QR-кода с логикой PRO-статуса и полным набором кнопок"""
	user = update.effective_user
	conn = await get_db_connection()
	
	try:
		# 1. ПОЛУЧАЕМ СВЕЖИЕ ДАННЫЕ
		db_user = await conn.fetchrow(
			"SELECT id, is_pro FROM users WHERE telegram_id = $1",
			user.id
		)
		if not db_user:
			db_user = await get_or_create_user(conn, user.id, user.username, user.first_name)
		
		sub = await check_subscription(conn, user.id)
		is_pro = sub['active']
		page = await get_user_page(conn, db_user['id'])
		
		# ===== НОВЫЙ БЛОК: ОБРАБОТКА ВЫБОРА ТИПА QR =====
		if update.callback_query:
			if update.callback_query.data == "qr_with_text":
				context.user_data['waiting_for_qr_text'] = True
				await update.callback_query.edit_message_text(
					"📝 **Введите текст для вашего QR-кода**\n\n"
					"Пришлите фразу (до 25 символов), которая будет написана под картинкой.\n"
					"Отправьте /cancel чтобы отменить.",
					parse_mode='Markdown',
					reply_markup=InlineKeyboardMarkup([
						[InlineKeyboardButton("◀️ Отмена", callback_data="qr")]
					])
				)
				return
			
			elif update.callback_query.data == "qr_standard":
				context.user_data.pop('temp_qr_text', None)
				# Генерируем обычный QR без текста
				# Дальше код пойдет как обычно
		
		# --- БЛОК 1: МЕНЮ ВЫБОРА ДЛЯ PRO ---
		if is_pro and update.callback_query and update.callback_query.data == "qr":
			keyboard = [
				[InlineKeyboardButton("✨ С надписью (PRO)", callback_data="qr_with_text")],
				[InlineKeyboardButton("🖼 Обычный", callback_data="qr_standard")],
				[InlineKeyboardButton("◀️ Назад", callback_data="start")]
			]
			await update.callback_query.edit_message_text(
				"🌟 **У вас PRO-статус!**\n\nВы можете сгенерировать обычный QR или добавить персональную надпись под кодом.",
				reply_markup=InlineKeyboardMarkup(keyboard),
				parse_mode='Markdown'
			)
			return
		
		# --- БЛОК 2: ГЕНЕРАЦИЯ КАРТИНКИ ---
		clean_base_url = APP_URL.strip().replace(" ", "")
		page_url = f"{clean_base_url}/{page['username']}"
		
		qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
		qr.add_data(page_url)
		qr.make(fit=True)
		qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
		
		# Вставка логотипа
		logo_path = r"D:\aRabota\TelegaBoom\030_botolinkpro\favicon_io\android-chrome-192x192.png"
		if os.path.exists(logo_path):
			try:
				logo = Image.open(logo_path).convert('RGBA')
				qr_w, qr_h = qr_img.size
				ts = int(qr_w * 0.2)
				logo = logo.resize((ts, ts), Image.Resampling.LANCZOS)
				mask = Image.new('L', (ts, ts), 0)
				ImageDraw.Draw(mask).ellipse((0, 0, ts, ts), fill=255)
				qr_img.paste(logo, ((qr_w - ts) // 2, (qr_h - ts) // 2), mask)
			except Exception as e:
				logger.warning(f"Logo paste error: {e}")
		
		# --- БЛОК 3: ОТРИСОВКА ТЕКСТА (Для PRO) ---
		user_text = context.user_data.pop('temp_qr_text', None)
		if user_text and is_pro:
			from PIL import ImageFont
			w, h = qr_img.size
			new_img = Image.new('RGB', (w, h + 60), 'white')
			new_img.paste(qr_img, (0, 0))
			draw = ImageDraw.Draw(new_img)
			try:
				font = ImageFont.truetype("arial.ttf", 26)
			except:
				font = ImageFont.load_default()
			
			bbox = draw.textbbox((0, 0), user_text, font=font)
			tx = (w - (bbox[2] - bbox[0])) // 2
			draw.text((tx, h + 5), user_text, fill="black", font=font)
			qr_img = new_img
		
		# --- БЛОК 4: СОХРАНЕНИЕ ---
		bio = BytesIO()
		bio.name = 'qrcode.png'
		qr_img.save(bio, 'PNG')
		bio.seek(0)
		
		# --- БЛОК 5: ПОДПИСЬ И КНОПКИ ---
		caption = f"🔳 **Ваш QR-код готов!**\n\n🔗 **Ссылка:**\n`{page_url}`"
		keyboard_btns = []
		
		if is_pro:
			if user_text:
				keyboard_btns.append([InlineKeyboardButton("✍️ Изменить текст", callback_data="qr_with_text")])
				keyboard_btns.append([InlineKeyboardButton("🖼 Без текста", callback_data="qr_standard")])
			else:
				keyboard_btns.append([InlineKeyboardButton("✨ Добавить надпись", callback_data="qr_with_text")])
		else:
			caption += "\n\n👑 *В PRO-версии можно добавить свой текст под QR (до 30 симв.)!*"
			keyboard_btns.append([InlineKeyboardButton("💎 Подключить PRO", callback_data="upgrade")])
		
		keyboard_btns.append([
			InlineKeyboardButton("📥 Скачать", callback_data="download_qr"),
			InlineKeyboardButton("📤 Поделиться", callback_data="share_qr")
		])
		keyboard_btns.append([InlineKeyboardButton("🏠 В меню", callback_data="start")])
		
		# --- БЛОК 6: ОТПРАВКА ---
		if update.callback_query:
			try:
				await update.callback_query.message.delete()
			except:
				pass
			await context.bot.send_photo(
				chat_id=update.effective_chat.id,
				photo=bio,
				caption=caption,
				reply_markup=InlineKeyboardMarkup(keyboard_btns),
				parse_mode='Markdown'
			)
		else:
			await update.message.reply_photo(
				photo=bio,
				caption=caption,
				reply_markup=InlineKeyboardMarkup(keyboard_btns),
				parse_mode='Markdown'
			)
	
	except Exception as e:
		logger.error(f"Error in qr_handler: {e}", exc_info=True)
		await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Ошибка при генерации QR-кода.")
	finally:
		await conn.close()


# Вспомогательная функция для удаления временного файла
async def delete_temp_file(file_path: str, delay: int = 60):
	"""Удаляет временный файл через указанную задержку"""
	await asyncio.sleep(delay)
	try:
		if os.path.exists(file_path):
			os.unlink(file_path)
			logger.info(f"Временный файл удален: {file_path}")
	except Exception as e:
		logger.error(f"Ошибка при удалении временного файла: {e}")


async def links_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Обработчик управления ссылками (команда /links и кнопка)"""
	
	print(f"🔥🔥🔥 button_handler получил: {update.callback_query.data}")
	
	# 1. Очистка старых сообщений (твоя логика)
	if 'last_success_msg_id' in context.user_data:
		try:
			await context.bot.delete_message(
				chat_id=update.effective_chat.id,
				message_id=context.user_data['last_success_msg_id']
			)
		except:
			pass
		context.user_data.pop('last_success_msg_id', None)
	
	user = update.effective_user
	conn = await get_db_connection()
	
	try:
		db_user = await get_or_create_user(conn, user.id, user.username, user.first_name)
		page = await get_user_page(conn, db_user['id'])
		links = await get_user_links(conn, page['id'])
		
		# 2. Формируем список ссылок для текста
		links_preview = ""
		if links:
			for i, link in enumerate(links[:3], 1):
				# Делаем заголовок ссылки кликабельным, если есть url
				url = link.get('url', '#')
				links_preview += f"{i}. [{link['title']}]({url}) — `{link['click_count']}` 👆\n"
			if len(links) > 3:
				links_preview += f"   ...и еще {len(links) - 3} шт.\n"
		else:
			links_preview = "У вас пока нет ссылок. Добавьте свою первую ссылку! ✨"
		
		# 3. Собираем текст (в твоем стиле со скобками)
		text = (
			f"🔗 **Управление ссылками**\n\n"
			f"📊 Всего ссылок: `{len(links)}`/10\n"
			f"────────────────────\n"
			f"{links_preview}\n"
			f"────────────────────\n"
			f"Выберите действие ниже:"
		)
		
		# 4. Клавиатура
		keyboard = [[InlineKeyboardButton("➕ Добавить ссылку", callback_data="add_link")]]
		if links:
			keyboard.append([InlineKeyboardButton("📋 Список ссылок", callback_data="list_links")])
		keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="start")])
		
		# 5. УНИВЕРСАЛЬНАЯ ОТПРАВКА (кнопка ИЛИ команда)
		if update.callback_query:
			await update.callback_query.edit_message_text(
				text,
				reply_markup=InlineKeyboardMarkup(keyboard),
				parse_mode='Markdown',
				disable_web_page_preview=True  # Чтобы не всплывали превью всех ссылок
			)
		else:
			await update.message.reply_text(
				text,
				reply_markup=InlineKeyboardMarkup(keyboard),
				parse_mode='Markdown',
				disable_web_page_preview=True
			)
	
	finally:
		await conn.close()


async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Обработчик команды /stats - показать статистику"""
	
	# Удаляем предыдущее сообщение с подтверждением, если оно есть
	if 'last_success_msg_id' in context.user_data:
		try:
			await context.bot.delete_message(
				chat_id=update.effective_chat.id,
				message_id=context.user_data['last_success_msg_id']
			)
		except:
			pass
		context.user_data.pop('last_success_msg_id', None)
	
	user = update.effective_user
	
	conn = await get_db_connection()
	try:
		db_user = await get_or_create_user(conn, user.id, user.username, user.first_name)
		page = await get_user_page(conn, db_user['id'])
		links = await get_user_links(conn, page['id'])
		
		# Считаем статистику
		total_clicks = sum(link.get('click_count') or 0 for link in links)
		view_count = page['view_count'] if page['view_count'] is not None else 0
		
		# Формируем текст
		text = f"📊 **Статистика**\n\n"
		text += f"👀 **Просмотры страницы:** {view_count}\n"
		text += f"🔗 **Всего кликов:** {total_clicks}\n"
		text += f"📌 **Всего ссылок:** {len(links)}\n\n"
		
		if links:
			# Сортируем ссылки по кликам (заменяем None на 0)
			sorted_links = sorted(links, key=lambda x: x.get('click_count') or 0, reverse=True)
			
			text += "🏆 **Топ ссылок:**\n"
			for i, link in enumerate(sorted_links[:5], 1):
				clicks = link.get('click_count') or 0
				text += f"{i}. {link['title']} - {clicks} шт\n"  # ← убрал 👆, добавил "шт"
			
			# Средняя статистика
			if len(links) > 0:
				avg_clicks = total_clicks / len(links)
				text += f"\n📈 **Среднее:** {avg_clicks:.1f} кликов на ссылку"
		else:
			text += "❌ У вас пока нет ссылок\n"
			text += "➕ Добавьте ссылку чтобы начать собирать статистику"
		
		# Кнопки
		keyboard = [
			# [InlineKeyboardButton("🔄 Подробная статистика", callback_data="stats")],
			[InlineKeyboardButton("◀️ Назад", callback_data="start")]
		]
		
		# Отправляем или редактируем
		if update.callback_query:
			await update.callback_query.edit_message_text(
				text=text,
				parse_mode='Markdown',
				reply_markup=InlineKeyboardMarkup(keyboard)
			)
		else:
			await update.message.reply_text(
				text=text,
				parse_mode='Markdown',
				reply_markup=InlineKeyboardMarkup(keyboard)
			)
	
	except Exception as e:
		logger.error(f"Ошибка в stats_handler: {e}")
		error_text = "❌ Ошибка при загрузке статистики"
		
		if update.callback_query:
			await update.callback_query.edit_message_text(error_text)
		else:
			await update.message.reply_text(error_text)
	finally:
		await conn.close()


# Файл: bot/handlers.py

from sqlalchemy import text
from core.database import engine


async def upgrade_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Единый обработчик системы оплаты и тарифов (Полностью переведен на HTML)"""
	query = update.callback_query
	user = update.effective_user
	
	if query:
		await query.answer()
	
	async with engine.begin() as conn:
		try:
			res = await conn.execute(
				text("SELECT id FROM users WHERE telegram_id = :tid"),
				{"tid": user.id}
			)
			db_user = res.fetchone()
			
			if not db_user:
				return await start_handler(update, context)
			
			sub_status = await check_subscription(conn, user.id)
			
			prices_usd = {"1m": 5, "3m": 12, "6m": 22, "12m": 40, "life": 150}
			tier_names = {
				"1m": "1 МЕСЯЦ", "3m": "3 МЕСЯЦА", "6m": "6 МЕСЯЦЕВ",
				"12m": "1 ГОД", "life": "ПОЖИЗНЕННО"
			}
			
			selected_tier = context.user_data.get('selected_tier', '1m')
			payment_view = context.user_data.get('payment_view', 'main')
			
			if query:
				if query.data.startswith("upg_"):
					selected_tier = query.data.replace("upg_", "")
					context.user_data['selected_tier'] = selected_tier
					payment_view = 'main'
				elif query.data == "show_methods":
					payment_view = 'select_method'
				elif query.data in ["pay_rf", "pay_kz", "pay_uz", "pay_crypto"]:
					payment_view = query.data
				elif query.data == "back_to_upgrade":
					payment_view = 'main'
				context.user_data['payment_view'] = payment_view
			
			usd_amount = prices_usd.get(selected_tier, 5)
			rates = await get_rates()
			base_usd_rate = rates.get("USD", 1.0)
			current_tier_name = tier_names.get(selected_tier, "1 МЕСЯЦ")
			
			currencies = {
				"RUB": ("₽", "РФ"), "UAH": ("₴", "Украина"), "KZT": ("₸", "Казахстан"),
				"UZS": ("so'm", "Узбекистан"), "BYN": ("Br", "Беларусь")
			}
			
			price_lines = []
			for code, (symbol, label) in currencies.items():
				if code in rates:
					val = int(round(usd_amount * (rates[code] / base_usd_rate)))
					# ИСПРАВЛЕНО под HTML: <b> вместо ** и <i> вместо _
					price_lines.append(f"├ <b><code>{val:,}</code></b> {symbol} — <i>{label}</i>")
			price_text = "\n".join(price_lines)
			
			if payment_view.startswith("pay_"):
				context.user_data['waiting_for_photo'] = True
				context.user_data['selected_plan'] = current_tier_name
				# ИСПРАВЛЕНО под HTML: <b> вместо **
				wallets = {
					"pay_rf": "🇷🇺 <b>РФ (Т-Банк / СБП):</b>\n<code>+79000000000</code> (Иван И.)",
					"pay_kz": "🇰🇿 <b>Казахстан (Kaspi):</b>\n<code>+77000000000</code> (Иван И.)",
					"pay_uz": "🇺🇿 <b>Узбекистан (UzCard):</b>\n<code>8600000000000000</code> (Иван И.)",
					"pay_crypto": "💎 <b>Crypto (USDT TRC20):</b>\n<code>TYourCryptoAddressHere...</code>"
				}
				method_info = wallets.get(payment_view, "Реквизиты не найдены")
				text_msg = (
					f"✅ <b>РЕКВИЗИТЫ ДЛЯ ОПЛАТЫ</b>\n\n{method_info}\n\n"
					f"📌 <b>Тариф:</b> <code>{current_tier_name}</code>\n"
					f"💰 <b>Сумма:</b> <code>{int(usd_amount)}$</code> (или эквивалент)\n\n"
					f"📸 <b>ИНСТРУКЦИЯ:</b>\n1. Переведите сумму.\n2. <b>Пришлите скриншот чека</b>.\n\n"
					f"⏳ <i>Активация в течение 30 минут.</i>"
				)
				keyboard = [
					[InlineKeyboardButton("◀️ Выбрать другой способ", callback_data="show_methods")],
					[InlineKeyboardButton("🏠 В главное меню", callback_data="start")]
				]
			elif payment_view == 'select_method':
				# ИСПРАВЛЕНО под HTML: <b> вместо **
				text_msg = f"💳 <b>ВЫБЕРИТЕ СПОСОБ ОПЛАТЫ</b>\nТариф: <b><code>{current_tier_name}</code></b>\n\nНажмите кнопку ниже:"
				keyboard = [
					[InlineKeyboardButton("🇷🇺 Карта РФ / СБП", callback_data="pay_rf")],
					[InlineKeyboardButton("🇰🇿 Kaspi / КZ", callback_data="pay_kz"),
					 InlineKeyboardButton("🇺🇿 UzCard / UZ", callback_data="pay_uz")],
					[InlineKeyboardButton("💎 Crypto (USDT)", callback_data="pay_crypto")],
					[InlineKeyboardButton("◀️ Назад к тарифам", callback_data="back_to_upgrade")]
				]
			else:
				status_icon = "💎" if sub_status['active'] else "🆓"
				status_text = f"Ваш статус: {'PRO' if sub_status['active'] else 'Бесплатный'}"
				# ПОЛНОСТЬЮ НА HTML
				text_msg = (
					f"{status_icon} <b>{status_text}</b>\n\n🌍 <b>ОРИЕНТИРОВОЧНЫЕ ЦЕНЫ:</b>\n{price_text}\n"
					f"────────────────────\n\n🚀 <b>ПРЕИМУЩЕСТВА PRO:</b>\n• Лимит ссылок: <b>до 25 шт.</b>\n"
					f"• Доступ ко всем премиум-шаблонам\n• Отключение логотипа\n\n"
					f"💳 <b>ВЫБРАН ТАРИФ:</b> <code>{current_tier_name}</code> — <b><code>{int(usd_amount)}$</code></b>\n\n"
					f"<b>Выберите срок подписки или перейдите к оплате 👇</b>"
				)
				keyboard = [
					[InlineKeyboardButton("1 мес", callback_data="upg_1m"),
					 InlineKeyboardButton("3 мес", callback_data="upg_3m"),
					 InlineKeyboardButton("6 мес", callback_data="upg_6m")],
					[InlineKeyboardButton("1 год", callback_data="upg_12m"),
					 InlineKeyboardButton("🔥 Навсегда", callback_data="upg_life")],
					[InlineKeyboardButton("💎 ВЫБРАТЬ СПОСОБ ОПЛАТЫ", callback_data="show_methods")],
					[InlineKeyboardButton("◀️ Назад", callback_data="start")]
				]
			
			reply_markup = InlineKeyboardMarkup(keyboard)
			
			# --- УНИВЕРСАЛЬНАЯ ОТПРАВКА ---
			if query:
				if query.message.photo:
					await query.message.delete()
					await context.bot.send_message(chat_id=user.id, text=text_msg, reply_markup=reply_markup,
					                               parse_mode='HTML')
				else:
					try:
						await query.edit_message_text(text_msg, reply_markup=reply_markup, parse_mode='HTML')
					except Exception as e:
						if "Message is not modified" not in str(e):
							await context.bot.send_message(chat_id=user.id, text=text_msg, reply_markup=reply_markup,
							                               parse_mode='HTML')
			else:
				await update.message.reply_text(text_msg, reply_markup=reply_markup, parse_mode='HTML')
		
		except Exception as e:
			logger.error(f"Ошибка в upgrade_handler: {e}", exc_info=True)
			await update.effective_message.reply_text(f"❌ Ошибка при загрузке тарифов.")


async def check_link_limit_warning(conn, tg_id: int):
	"""
    Проверяет лимиты по TELEGRAM_ID и возвращает (is_blocked, warning_message)
    """
	# Исправлено: ищем по u.telegram_id, так как ты передаешь его из хендлера
	data = await conn.fetchrow("""
                               SELECT u.is_pro,
                                      (SELECT COUNT(*)
                                       FROM links l
                                                JOIN pages p ON l.page_id = p.id
                                       WHERE p.user_id = u.id
                                         AND l.is_active = true) as links_count
                               FROM users u
                               WHERE u.telegram_id = $1
	                           """, tg_id)
	
	if not data:
		# Если юзер не найден — логируем это, чтобы не гадать
		print(f"DEBUG: Юзер с tg_id {tg_id} не найден в БД!")
		return False, None
	
	is_pro = data['is_pro']
	current_count = int(data['links_count'])
	max_links = 50 if is_pro else 3
	
	# ДЕБАГ В КОНСОЛЬ (потом удалишь)
	print(f"DEBUG: Юзер {tg_id} | PRO: {is_pro} | Ссылок: {current_count}")
	
	# Блокировка
	if current_count >= max_links:
		return True, f"❌ Лимит исчерпан ({current_count}/{max_links}). Удалите старые ссылки или купите PRO."
	
	# ПРЕДУПРЕЖДЕНИЕ
	if not is_pro and current_count == 2:
		return False, "⚠️ Внимание! Это ваша последняя бесплатная ссылка (2 из 3 использовано)."
	
	return False, None


# Название файла: bot/handlers.py


# ===== ДОБАВЛЕНИЕ ССЫЛКИ =====

# bot/handlers.py

async def add_link_start_old(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Начало добавления ссылки с PRO-фичей и кнопкой Назад"""
	query = update.callback_query
	user = update.effective_user
	conn = await get_db_connection()
	
	try:
		# --- 1. ОЧИСТКА ---
		qr_msg_id = context.user_data.get('last_qr_msg_id')
		if qr_msg_id:
			try:
				await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=qr_msg_id)
				context.user_data.pop('last_qr_msg_id', None)
			except Exception:
				pass
		
		# КРИТИЧНО: Удаляем старое только если это НЕ возврат по кнопке "Назад"
		# Если query.data == "back_to_link_type", мы оставляем сообщение живым для edit_message_text
		is_back_button = query and query.data == "back_to_link_type"
		
		if query and not is_back_button:
			try:
				await query.message.delete()
				query = None  # Обнуляем, чтобы ниже сработал send_message вместо edit
			except Exception:
				pass
		
		# --- 2. ЛОГИКА ЛИМИТОВ И СТАТУСА ---
		db_user = await get_or_create_user(conn, user.id, user.username, user.first_name)
		page = await conn.fetchrow("SELECT id FROM pages WHERE user_id = $1", db_user['id'])
		
		if not page:
			await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Сначала создайте страницу!")
			return ConversationHandler.END
		
		sub_status = await check_subscription(conn, user.id)
		is_pro = sub_status.get('active', False)
		
		current_count = await conn.fetchval(
			"SELECT COUNT(*) FROM links WHERE page_id = $1 AND is_active = true",
			page['id']
		) or 0
		
		max_limit = 50 if is_pro else 3
		remains = max_limit - current_count
		limit_indicator = "💎 PRO" if is_pro else "💡 Бесплатный"
		limit_text = f"{limit_indicator} статус: {current_count}/{max_limit} (Осталось: <b>{remains}</b>)"
		
		# --- 3. ПРОВЕРКА ЛИМИТА ---
		if remains <= 0:
			text_limit = (f"❌ <b>Лимит ссылок исчерпан!</b>\n\n{limit_text}\n\n"
			              "Удалите старые ссылки или подключите <b>PRO-статус</b>.")
			keyboard = [[InlineKeyboardButton("💎 Узнать про PRO", callback_data="pro_info")],
			            [InlineKeyboardButton("◀️ Назад", callback_data="links")]]
			
			if query:
				await query.edit_message_text(text=text_limit, reply_markup=InlineKeyboardMarkup(keyboard),
				                              parse_mode="HTML")
			else:
				await context.bot.send_message(chat_id=update.effective_chat.id, text=text_limit,
				                               reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
			return ConversationHandler.END
		
		# --- 4. СБРОС ДАННЫХ ВВОДА ---
		for key in ['new_link_title', 'new_link_url', 'new_link_icon', 'link_type']:
			context.user_data.pop(key, None)
		
		# --- 5. РАЗВИЛКА ДЛЯ PRO ---
		if is_pro:
			text_pro = (
				f"{limit_text}\n"
				f"────────────────────\n\n"
				f"🚀 <b>Добавление новой ссылки (PRO)</b>\n"
				f"Выберите действие:"
			)
			keyboard = [
				[InlineKeyboardButton("🌐 Обычная ссылка", callback_data="type_std")],
				[InlineKeyboardButton("💳 Реквизиты (Карты, Крипто)", callback_data="type_fin")],
				[InlineKeyboardButton("📋 Список ссылок", callback_data="list_links")],  # <-- ДОБАВИЛИ
				[InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
			]
			
			if query:
				msg = await query.edit_message_text(text=text_pro, reply_markup=InlineKeyboardMarkup(keyboard),
				                                    parse_mode="HTML")
			else:
				msg = await context.bot.send_message(chat_id=update.effective_chat.id, text=text_pro,
				                                     reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
			
			context.user_data['last_menu_msg_id'] = msg.message_id
			return SELECT_LINK_TYPE
		
		# --- 6. ДЛЯ ОБЫЧНЫХ ЮЗЕРОВ ---
		context.user_data['link_type'] = 'standard'
		text_step1 = (
			f"{limit_text}\n"
			f"────────────────────\n\n"
			"📝 <b>Шаг 1 из 3: Введите название ссылки</b>\n\n"
			"Например: <i>Мой Instagram</i>"
		)
		
		keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel")]]
		
		if query:
			msg = await query.edit_message_text(text=text_step1, reply_markup=InlineKeyboardMarkup(keyboard),
			                                    parse_mode="HTML")
		else:
			msg = await context.bot.send_message(chat_id=update.effective_chat.id, text=text_step1,
			                                     reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
		
		context.user_data['last_menu_msg_id'] = msg.message_id
		return ADD_LINK_TITLE
	
	except Exception as e:
		logger.error(f"Error in add_link_start: {e}", exc_info=True)
		return ConversationHandler.END
	finally:
		await conn.close()


async def save_new_link_to_db(conn, page_id, title, url, icon, link_type):
	"""Вспомогательная функция для сохранения ссылки в БД"""
	return await conn.execute(
		"INSERT INTO links (page_id, title, url, icon, link_type, is_active) VALUES ($1, $2, $3, $4, $5, true)",
		page_id, title, url, icon, link_type
	)


async def select_link_type_handler_old(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Обработчик выбора типа ссылки для PRO (Обычная или Реквизиты)"""
	query = update.callback_query
	
	print(f"🔥🔥🔥 button_handler получил: {update.callback_query.data}")
	
	await query.answer()
	
	choice = query.data  # "type_std" или "type_fin"
	
	if choice == "type_std":
		# Юзер выбрал обычную ссылку
		context.user_data['link_type'] = 'standard'
		
		# ДОБАВЛЯЕМ КНОПКУ НАЗАД: чтобы юзер мог передумать и выбрать крипту
		keyboard = [
			[InlineKeyboardButton("◀️ Назад к выбору типа", callback_data="back_to_link_type")],
			[InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
		]
		
		await query.edit_message_text(
			"📝 <b>Шаг 1 из 3: Введите название ссылки</b>\n"
			"(Например: <i>Мой Instagram</i> или <i>Личный сайт</i>)",
			reply_markup=InlineKeyboardMarkup(keyboard),
			parse_mode='HTML'
		)
		return ADD_LINK_TITLE
	
	elif choice == "type_fin":
		# Юзер выбрал реквизиты -> показываем подменю
		context.user_data['link_type'] = 'finance'
		
		keyboard = [
			[InlineKeyboardButton("💳 Банковская карта", callback_data="fin_card")],
			[InlineKeyboardButton("₿ Bitcoin (BTC)", callback_data="fin_btc")],
			[InlineKeyboardButton("💎 USDT (TRC20)", callback_data="fin_usdt")],
			# Исправлено: Назад вернет к выбору Ссылка/Реквизиты
			[InlineKeyboardButton("◀️ Назад", callback_data="back_to_link_type")]
		]
		
		await query.edit_message_text(
			"💳 <b>ВЫБОР ПЛАТЕЖНОЙ СИСТЕМЫ</b>\n\n"
			"Бот автоматически подберет подходящую иконку для выбранного типа.",
			reply_markup=InlineKeyboardMarkup(keyboard),
			parse_mode='HTML'
		)
		# Исправлено: возвращаем константу без кавычек
		return SELECT_FINANCE_SUBTYPE


async def format_currency_block(rub_amount):
	rates = await get_rates()
	
	# Список валют
	currencies = {
		"USD": ("$", "USD"),
		"EUR": ("€", "EUR"),
		"RUB": ("₽", "Россия"),
		"UAH": ("₴", "Украина"),
		"KZT": ("₸", "Казахстан"),
		"BYN": ("BYN", "Беларусь"),
		"GEL": ("₾", "Грузия"),
		"AMD": ("֏", "Армения"),
		"PLN": ("zł", "Польша"),
		"UZS": ("so'm", "Узбекистан"),
	}
	
	if not rates:
		return "❌ Курсы валют временно недоступны"
	
	res = []
	
	# 1. Сначала выводим блок USD и EUR
	for code in ["USD", "EUR"]:
		if code in rates:
			val = rub_amount * rates[code]
			res.append(f"💰 **{val:,.2f} {currencies[code][0]}** — _{currencies[code][1]}_")
	
	# 2. Добавляем разделитель после Евро
	res.append("────────────────────")
	
	# 3. Выводим всё остальное (кроме USD и EUR, которые уже в топе)
	for code, (symbol, label) in currencies.items():
		if code in ["USD", "EUR"] or code not in rates:
			continue
		
		val = rub_amount * rates[code]
		
		# Округление для "крупных" валют
		if code in ["UZS", "AMD", "KZT", "RUB"]:
			fmt_val = f"{val:,.0f}"
		else:
			fmt_val = f"{val:,.2f}"
		
		res.append(f"├ {fmt_val} {symbol} — _{label}_")
	
	return "\n".join(res)


async def add_link_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Получаем название ссылки (шаг 2)"""
	context.user_data['link_title'] = update.message.text
	
	print(f"🔥🔥🔥 button_handler получил: {update.callback_query.data}")
	
	text = (
		f"✅ Название сохранено: {update.message.text}\n\n"
		f"🔗 **Шаг 2 из 3:** Теперь введите URL или текст ссылки\n\n"
		f"Что можно вставить:\n"
		f"• https://instagram.com/username\n"
		f"• 4276 1234 5678 9012 (номер карты)\n"
		f"• 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa (BTC)\n"
		f"• @username (Telegram)\n\n"
		f"Просто отправьте текст или ссылку\n\n"
		f"❌ /cancel - отмена"
	)
	
	await update.message.reply_text(text)
	return ADD_LINK_URL


async def cancel_add_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Отмена добавления ссылки - возврат по стеку без лишнего мусора"""
	query = update.callback_query
	await query.answer()
	
	# Очищаем временные данные
	for key in ['link_title', 'link_url', 'link_icon']:
		context.user_data.pop(key, None)
	
	previous_menu = context.user_data.get('previous_menu', 'start')
	
	conn = await get_db_connection()
	try:
		user_id = update.effective_user.id
		# Используем BIGINT для надежности
		db_user = await get_or_create_user(conn, user_id, None, None)
		page = await get_user_page(conn, db_user['id'])
		
		if previous_menu == 'links':
			# --- МЕНЮ ССЫЛОК ---
			links = await get_user_links(conn, page['id'])
			keyboard = [[InlineKeyboardButton("➕ Добавить ссылку", callback_data="add_link")]]
			if links:
				keyboard.append([InlineKeyboardButton("📋 Список ссылок", callback_data="list_links")])
			keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="start")])
			
			text = f"🔗 **Управление ссылками**\n\nВсего ссылок: {len(links)}"
			await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
		
		else:
			# --- ГЛАВНОЕ МЕНЮ ---
			sub = await check_subscription(conn, user_id)
			
			# Чистая логика статуса без триалов
			if sub and sub.get('active'):
				status_text = f"💎 **PRO статус: {sub.get('time_left_str', 'активен')}**"
			else:
				status_text = "🆓 **Тариф: Бесплатный**"
			
			view_count = page['view_count'] or 0
			
			keyboard = [
				[InlineKeyboardButton("📋 Моя страница", callback_data="mysite"),
				 InlineKeyboardButton("🔳 QR-код", callback_data="qr")],
				[InlineKeyboardButton("🔗 Ссылки", callback_data="links"),
				 InlineKeyboardButton("➕ Добавить", callback_data="add_link")],
				[InlineKeyboardButton("🎨 Шаблоны", callback_data="templates_menu"),
				 InlineKeyboardButton("📊 Статистика", callback_data="stats")],
				[InlineKeyboardButton("💳 Подписка", callback_data="upgrade"),
				 InlineKeyboardButton("⚙️ Профиль", callback_data="profile")],
				[InlineKeyboardButton("❓ Помощь", callback_data="help")]
			]
			
			text = (
				f"👋 **Привет, {update.effective_user.first_name}!**\n\n"
				f"📌 Страница: `/{page['username']}`\n"
				f"🔗 Ссылок: {len(await get_user_links(conn, page['id']))}\n"
				f"👀 Просмотров: {view_count}\n\n"
				f"{status_text}\n"
				f"────────────────────\n"
				f"Что настроим сегодня?"
			)
			
			await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
	
	except Exception as e:
		logger.error(f"Ошибка в cancel_add_link: {e}")
		await query.edit_message_text("❌ Ошибка при возврате в меню.")
	finally:
		await conn.close()
	
	return ConversationHandler.END


async def debug_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Отлавливает вообще всё"""
	print(f"🔥 DEBUG: Получено сообщение: {update.message.text if update.message else 'Нет сообщения'}")
	print(f"🔥 DEBUG: User data: {context.user_data}")
	await update.message.reply_text(f"DEBUG: {update.message.text}")
	return ADD_LINK_TITLE  # Важно!


# bot/handlers.py

async def add_link_icon_old(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Финальное сохранение после выбора иконки"""
	query = update.callback_query
	await query.answer()
	
	# Получаем иконку из кнопки
	icon = query.data.replace("icon_", "")
	
	# Получаем данные из контекста (НОВЫЙ конструктор)
	title = context.user_data.get('link_title', 'Без названия')
	url = context.user_data.get('link_url', '')
	link_type = context.user_data.get('link_type', 'standard')
	category = context.user_data.get('link_category', 'other')
	description = context.user_data.get('link_description')
	finance_subtype = context.user_data.get('finance_subtype')
	finance_tab = context.user_data.get('finance_tab')
	
	# Формируем pay_details для финансовых ссылок
	pay_details = None
	# ... тут логика формирования pay_details из finish_link_creation ...
	
	conn = await get_db_connection()
	try:
		# Получаем ID пользователя в базе
		user_id = update.effective_user.id
		user_db_id = await conn.fetchval("SELECT id FROM users WHERE telegram_id = $1", user_id)
		
		# Получаем страницу
		page = await conn.fetchrow("SELECT id, username FROM pages WHERE user_id = $1", user_db_id)
		
		# Получаем максимальный sort_order
		max_sort = await conn.fetchval(
			"SELECT COALESCE(MAX(sort_order), 0) FROM links WHERE page_id = $1",
			page['id']
		)
		
		# Вставляем ссылку
		await conn.execute("""
                           INSERT INTO links (page_id, title, url, icon, link_type,
                                              pay_details, sort_order, is_active, click_count, created_at)
                           VALUES ($1, $2, $3, $4, $5, $6, $7, true, 0, NOW())
		                   """, page['id'], title, url, icon, link_type,
		                   pay_details, max_sort + 1)
		
		# Получаем актуальное количество ссылок
		new_count = await conn.fetchval(
			"SELECT COUNT(*) FROM links WHERE page_id = $1 AND is_active = true",
			page['id']
		) or 0
		
		# Проверяем PRO статус для лимита
		is_pro = await conn.fetchval("SELECT is_pro FROM users WHERE id = $1", user_db_id) or False
		limit = PRO_LINKS_LIMIT if is_pro else FREE_LINKS_LIMIT
		remaining = limit - new_count
		
		# Формируем сообщение
		msg = f"✅ **Ссылка успешно добавлена!**\n\n"
		msg += f"📌 **Название:** {title}\n"
		msg += f"📊 **Использовано:** {new_count} из {limit}\n"
		msg += f"📈 **Осталось:** {remaining}"
		
		keyboard = [
			[
				InlineKeyboardButton("👁 Моя страница", callback_data="mysite"),
				InlineKeyboardButton("➕ Еще одну", callback_data="add_link")
			],
			[InlineKeyboardButton("🏠 В меню", callback_data="start")]
		]
		
		await query.edit_message_text(
			msg,
			reply_markup=InlineKeyboardMarkup(keyboard),
			parse_mode='Markdown'
		)
		
		# Очищаем данные
		for key in ['link_category', 'link_type', 'link_info', 'link_title',
		            'link_url', 'link_description', 'finance_subtype', 'finance_tab']:
			context.user_data.pop(key, None)
	
	except Exception as e:
		logger.error(f"Ошибка сохранения: {e}", exc_info=True)
		await query.edit_message_text("❌ Ошибка при сохранении. Попробуй позже.")
	finally:
		await conn.close()
	
	return ConversationHandler.END


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	data = query.data
	state = context.user_data.get('_state')
	user = update.effective_user
	
	# ===== ПРОВЕРКА ФЛАГА goto_banks =====
	if context.user_data.get('goto_banks'):
		print(f"🏦 ОБНАРУЖЕН ФЛАГ goto_banks, перенаправляем в банковский раздел")
		# Очищаем флаг
		context.user_data.pop('goto_banks', None)
		# Убираем лишние ключи
		context.user_data.pop('link_category', None)
		# Перенаправляем в банковский раздел
		from bot.bank import choose_country
		await query.answer()
		return await choose_country(update, context)
	# ======================================
	
	if data.startswith("type_"):
		print(f"🔧 ВЫЗЫВАЕМ select_link_type для {data}")
		try:
			result = await select_link_type(update, context)
			print(f"✅ select_link_type вернул {result}")
			return result
		except Exception as e:
			print(f"❌ ОШИБКА в select_link_type: {e}")
			return
	
	print(f"🔥🔥🔥 button_handler получил: {data}")
	print(f"📍 Текущее состояние диалога: {state}")
	print(f"🎯 Активные диалоги: {context.user_data.keys()}")
	
	if state:
		print(f"⏭️ Активен диалог {state}, пропускаем")
		return
	
	# ПРОПУСКАЕМ ТОЛЬКО ТО, ЧТО НЕ ДОЛЖНО ОБРАБАТЫВАТЬСЯ ЗДЕСЬ
	if data.startswith(('choice_', 'skip_step', 'back_to_previous', 'back_to_types', 'add_link')):
		print(f"⏭️ Пропускаем кнопку: {data}")
		return
	
	# ===== ОБРАБОТКА КАТЕГОРИЙ =====
	if data.startswith("cat_"):
		print(f"📁 ОБРАБАТЫВАЕМ категорию: {data}")
		await query.answer()
		return await select_category(update, context)
	
	# В начале функции, после обработки type_ и cat_
	elif query.data == "qr_with_text":
		context.user_data['waiting_for_qr_text'] = True
		await query.answer()
		await context.bot.send_message(
			chat_id=update.effective_chat.id,
			text="📝 **Введите текст для вашего QR-кода**\n\n"
			     "Пришлите фразу (до 25 символов), которая будет написана под картинкой.",
			parse_mode='Markdown',
			reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Отмена", callback_data="qr")]])
		)
		return
	
	# ===== БАНКОВСКИЕ МЕТОДЫ =====
	if query.data == "method_paypal":
		return await method_paypal(update, context)
	elif query.data == "method_wise":
		return await method_wise(update, context)
	elif query.data == "method_revolut":
		return await method_revolut(update, context)
	elif query.data == "method_swift":
		return await method_swift(update, context)
	elif query.data == "revolut_quick":
		return await revolut_choice_handler(update, context)
	elif query.data == "revolut_full":
		return await revolut_choice_handler(update, context)
	elif query.data == "wise_quick":
		return await wise_choice_handler(update, context)
	elif query.data == "wise_full":
		return await wise_choice_handler(update, context)
	elif query.data == "method_yoomoney":
		print(f"🚫 ВЫЗЫВАЕМ method_yoomoney напрямую")
		return await method_yoomoney(update, context)
	elif query.data == "method_vkpay":
		print(f"🚫 ВЫЗЫВАЕМ method_vkpay напрямую")
		return await method_vkpay(update, context)
	elif query.data == "method_monobank":
		print(f"🚫 ВЫЗЫВАЕМ method_monobank напрямую")
		return await method_monobank(update, context)
	elif query.data == "method_kaspi":
		print(f"🚫 ВЫЗЫВАЕМ method_kaspi напрямую")
		return await method_kaspi(update, context)
	elif query.data == "method_payme":
		print(f"🚫 ВЫЗЫВАЕМ method_payme напрямую")
		return await method_payme(update, context)
	elif query.data == "method_click":
		print(f"🚫 ВЫЗЫВАЕМ method_click напрямую")
		return await method_click(update, context)
	elif query.data == "method_tbcpay":
		print(f"🚫 ВЫЗЫВАЕМ method_tbcpay напрямую")
		return await method_tbcpay(update, context)
	elif query.data == "method_idram":
		print(f"🚫 ВЫЗЫВАЕМ method_idram напрямую")
		return await method_idram(update, context)
	elif query.data.startswith("country_"):
		return await show_country_methods(update, context)
	
	
	elif query.data == "back_to_countries":
		return await back_to_countries(update, context)
	elif query.data.startswith("method_"):
		print(f"🚫 ВЫЗЫВАЕМ toggle_method для {query.data}")
		return await toggle_method(update, context)
	# ==============================================
	
	# ===== ПРОПУСК ВСЕХ БАНКОВСКИХ КНОПОК =====
	bank_buttons = [
		"method_paypal", "method_wise", "method_revolut", "method_swift",
		"method_iban", "method_yoomoney", "method_vkpay", "method_monobank",
		"method_kaspi", "method_payme", "method_click", "method_tbcpay",
		"method_idram",
		# ДОБАВЬ НОВЫЕ:
		"method_russia_yoomoney", "method_russia_vkpay",
		"method_ukraine_monobank", "method_kazakhstan_kaspi",
		"method_uzbekistan_payme", "method_uzbekistan_click",
		"method_georgia_tbcpay", "method_armenia_idram"
	]
	
	if query.data in bank_buttons or \
			query.data.startswith(("country_", "back_to_countries", "transfers")):
		print(f"🚫 ПРОПУСКАЕМ банковскую кнопку: {query.data}")
		await query.answer()
		return
	# ================================================
	
	# Заглушка для разделителей
	if query.data == "noop":
		await query.answer()
		return
	
	# ===== НОВАЯ СЕКЦИЯ: ОБРАБОТКА КАТЕГОРИЙ =====
	if query.data.startswith("cat_"):
		print(f"📁 ОБРАБАТЫВАЕМ категорию: {query.data}")
		await query.answer()
		return await select_category(update, context)
	
	# ===== НОВАЯ СЕКЦИЯ: ОБРАБОТКА ТИПОВ =====
	if query.data.startswith("type_"):
		print(f"🔧 ОБРАБАТЫВАЕМ тип: {query.data}")
		await query.answer()
		return await select_link_type(update, context)
	
	# В button_handler, в самом начале, добавьте:
	if data.startswith(('fin_sub_', 'choice_', 'skip_step', 'back_to_previous', 'back_to_types')):
		print(f"⏭️ Пропускаем кнопку диалога: {data}")
		return
	
	# ПРОПУСКАЕМ КНОПКИ НОВОГО КОНСТРУКТОРА, НО НЕ ДЛЯ КРИПТЫ
	if data.startswith(('cat_', 'type_', 'choice_', 'back_to_previous', 'back_to_types')):
		if data in ['cat_wallets', 'cat_stocks'] or data.startswith('type_'):
			print(f"🔓 НЕ пропускаем крипто-кнопку: {data}")
			# НЕ ВОЗВРАЩАЕМ - идем дальше
		else:
			print(f"⏭️ Пропускаем кнопку конструктора: {data}")
			return
	
	# Пропускаем callback'и конструктора, НО НЕ ДЛЯ КРИПТЫ
	if data.startswith(('cat_', 'type_', 'choice_', 'skip_step', 'back_to_', 'add_link')):
		if data in ['cat_wallets', 'cat_stocks'] or data.startswith('type_'):
			print(f"🔓 НЕ пропускаем крипто-кнопку: {data}")
			# НЕ ВОЗВРАЩАЕМ - идем дальше
		else:
			print(f"⏭️ Пропускаем кнопку конструктора: {data}")
			return
	
	# После обработки cat_, добавить обработку type_
	if query.data.startswith("type_"):
		print(f"🔧 ОБРАБАТЫВАЕМ тип: {query.data}")
		await query.answer()
		# Здесь нужно вызвать функцию обработки типа
		return await select_link_type(update, context)  # или аналогичную
	
	# --- 1. ЛОГИКА АДМИНИСТРИРОВАНИЯ ---
	if query.data.startswith("adm_"):
		if user.id not in ADMIN_IDS:
			await query.answer("У тебя нет прав админа!", show_alert=True)
			return
		
		if query.data.startswith("adm_app_"):  # ОДОБРЕНИЕ
			parts = query.data.split("_")
			target_id = int(parts[2])
			tier = parts[3]
			days_map = {"1m": 31, "3m": 93, "6m": 186, "12m": 366, "life": 36500}
			days = days_map.get(tier, 31)
			
			conn = await get_db_connection()
			try:
				await conn.execute("""
                                   UPDATE users
                                   SET pro_expires_at = CASE
                                                            WHEN pro_expires_at > CURRENT_TIMESTAMP
                                                                THEN pro_expires_at + ($1 || ' days')::INTERVAL
                        ELSE CURRENT_TIMESTAMP + ($1 || ' days'):: INTERVAL
                                   END
                                   ,
                    is_pro = true
                    WHERE id =
                                   $2
                                   :
                                   :
                                   BIGINT
				                   """, days, target_id)
				
				await query.edit_message_caption(
					caption=query.message.caption + "\n\n✅ **АКТИВИРОВАНО**",
					reply_markup=None
				)
				await context.bot.send_message(
					chat_id=target_id,
					text="🚀 **PRO-статус активирован!**",
					parse_mode='Markdown'
				)
			finally:
				await conn.close()
			return
		
		elif query.data.startswith("adm_dec_"):  # ОТКАЗ
			target_id = int(query.data.split("_")[2])
			await query.edit_message_caption(
				caption=query.message.caption + "\n\n❌ **ОТКЛОНЕНО**",
				reply_markup=None
			)
			await context.bot.send_message(
				chat_id=target_id,
				text="❌ **Ваш чек отклонен.**",
				parse_mode='Markdown'
			)
			return
	
	# Если это кнопка для входа в диалог — не трогаем
	if query.data.startswith(("edit_title_", "edit_url_", "edit_icon_")) or \
			query.data in ["edit_title", "edit_url", "edit_icon"]:
		return
	
	# ОТЛАДКА
	state = context.user_data.get('_state')
	logger.info(f"!!! НАЖАТА КНОПКА: {query.data} (state={state})")
	
	# 2. ПРЯМАЯ ПЕРЕАДРЕСАЦИЯ НА ДРУГИЕ ХЕНДЛЕРЫ
	
	if query.data == "templates_menu":
		await query.answer()
		return await templates_command(update, context)
	elif query.data == "qr":
		await query.answer()
		return await qr_handler(update, context)
	
	# --- ОБРАБОТЧИК ДЛЯ КНОПКИ "ОБЫЧНЫЙ" ---
	elif query.data == "qr_standard":
		await query.answer()
		context.user_data['temp_qr_text'] = None
		return await qr_handler(update, context)
	
	elif query.data == "qr_with_text":
		context.user_data['waiting_for_qr_text'] = True
		await query.edit_message_text(
			"📝 **Введите текст для вашего QR-кода**\n\n"
			"Пришлите фразу (до 25 символов), которая будет написана под картинкой.",
			parse_mode='Markdown',
			reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Отмена", callback_data="qr")]])
		)
		await query.answer()
		return  # Добавлен return для предотвращения дальнейшей обработки
	
	# Обработка входа в апгрейд, переключения тарифов И вызова реквизитов
	elif query.data == "upgrade" or query.data.startswith("upg_") or query.data == "show_wallets":
		await query.answer()
		return await upgrade_handler(update, context)
	
	# 3. ПОДКЛЮЧЕНИЕ К БД ДЛЯ ОСНОВНОЙ ЛОГИКИ
	conn = await get_db_connection()
	try:
		db_user = await get_or_create_user(conn, user.id, user.username, user.first_name)
		page = await get_user_page(conn, db_user['id'])
		
		# --- ОБРАБОТЧИК КОПИРОВАНИЯ URL ---
		if query.data == "copy_url":
			await query.answer()
			clean_base_url = APP_URL.strip().replace(" ", "")
			page_url = f"{clean_base_url}/{page['username']}"
			msg = await query.message.reply_text(
				f"📋 `{page_url}`\n\nНажмите на ссылку выше, чтобы скопировать.",
				parse_mode='Markdown'
			)
			if 'qr_messages' not in context.user_data:
				context.user_data['qr_messages'] = []
			context.user_data['qr_messages'].append(msg.message_id)
			return
		
		# --- ОБРАБОТЧИК СКАЧИВАНИЯ QR (PNG) ---
		elif query.data == "download_qr":
			await query.answer()
			clean_base_url = APP_URL.strip().replace(" ", "")
			page_url = f"{clean_base_url}/{page['username']}"
			qr = qrcode.QRCode(version=1, box_size=10, border=4)
			qr.add_data(page_url)
			qr.make(fit=True)
			qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
			bio = BytesIO()
			bio.name = f'qrcode_{page["username"]}.png'
			qr_img.save(bio, 'PNG')
			bio.seek(0)
			msg = await query.message.reply_document(
				document=bio, filename=bio.name,
				caption=f"📥 QR-код для {page['username']}"
			)
			if 'qr_messages' not in context.user_data:
				context.user_data['qr_messages'] = []
			context.user_data['qr_messages'].append(msg.message_id)
			return
		
		# --- ОБРАБОТЧИК ПОДЕЛИТЬСЯ (SHARE) ---
		elif query.data == "share_qr":
			await query.answer()
			clean_base_url = APP_URL.strip().replace(" ", "")
			page_url = f"{clean_base_url}/{page['username']}"
			share_text = f"Посмотри мою страницу в BotoLinkPro: {page_url}"
			
			share_keyboard = [
				[
					InlineKeyboardButton("📤 В другой чат", switch_inline_query=share_text),
					InlineKeyboardButton("👤 Другу", url=f"https://t.me/share/url?url={page_url}")
				],
				[InlineKeyboardButton("🏠 В главное меню", callback_data="start")]
			]
			
			msg = await query.message.reply_text(
				f"📤 **Поделиться страницей**\n\nВы можете отправить ссылку в другой чат или личному контакту.",
				parse_mode='Markdown',
				reply_markup=InlineKeyboardMarkup(share_keyboard)
			)
			
			if 'qr_messages' not in context.user_data:
				context.user_data['qr_messages'] = []
			context.user_data['qr_messages'].append(query.message.message_id)
			context.user_data['qr_messages'].append(msg.message_id)
			return
		
		# ОБРАБОТКА КНОПКИ "Я ОПЛАТИЛ"
		elif query.data == "check_payment":
			await query.answer()
			context.user_data['waiting_for_receipt'] = True
			text = (
				"📸 **Отправьте скриншот чека**\n\n"
				"Пожалуйста, пришлите фото или файл подтверждения оплаты прямо в этот чат.\n"
				"Как только модератор проверит его, вам придет уведомление! 🚀"
			)
			keyboard = [[InlineKeyboardButton("◀️ Отмена", callback_data="upgrade")]]
			await query.edit_message_text(
				text,
				reply_markup=InlineKeyboardMarkup(keyboard),
				parse_mode='Markdown'
			)
			return
		
		# --- ГЛАВНОЕ МЕНЮ (START / НАЗАД) ---
		elif query.data == "start":
			await query.answer()
			if 'qr_messages' in context.user_data:
				for msg_id in context.user_data['qr_messages']:
					try:
						await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg_id)
					except:
						pass
				context.user_data.pop('qr_messages', None)
			
			if query.message.photo:
				try:
					await query.message.delete()
				except:
					pass
			await start_handler(update, context)
			return
		
		elif query.data == "mysite":
			await query.answer()
			sub = await check_subscription(conn, user.id)
			page = await get_user_page(conn, db_user['id'])
			current_template = "Classic" if page['template_id'] == 1 else "Royal"
			links = await get_user_links(conn, page['id'])
			total_clicks = sum(link['click_count'] for link in links)
			full_url = f"{APP_URL}/{page['username']}"
			
			text = (
				f"📋 **Ваша страница уже работает**\n\n"
				f"🌐 Ссылка: [{full_url}]({full_url})\n"
				f"🎨 Шаблон: **{current_template}**\n"
				f"📊 Текущий Статус: {'💎 PRO' if sub['active'] else '🆓 Бесплатный'}\n"
				f"────────────────────\n"
				f"👀 Просмотров: {page['view_count'] or 0}\n"
				f"🔗 Кликов: {total_clicks}\n"
				f"📌 Ссылок: {len(links)}"
			)
			keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="start")]]
			await query.edit_message_text(
				text,
				reply_markup=InlineKeyboardMarkup(keyboard),
				parse_mode='Markdown'
			)
			return
		
		# --- СПИСОК ССЫЛОК (LINKS) ---
		elif query.data == "links":
			await query.answer()
			links = await get_user_links(conn, page['id'])
			used = len(links)
			user_id = update.effective_user.id
			is_pro = await conn.fetchval("SELECT is_pro FROM users WHERE telegram_id = $1", user_id) or False
			limit = PRO_LINKS_LIMIT if is_pro else FREE_LINKS_LIMIT
			remaining = limit - used
			
			keyboard = [[InlineKeyboardButton("➕ Добавить ссылку", callback_data="add_link")]]
			if links:
				keyboard.append([InlineKeyboardButton("📋 Список ссылок", callback_data="list_links")])
				keyboard.append([InlineKeyboardButton("🗑️ Удалить все ссылки", callback_data="delete_all_links")])
			keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="start")])
			
			text = f"🔗 **Управление ссылками**\n\n"
			text += f"📊 Использовано: {used} из {limit}\n"
			text += f"📈 Осталось: {remaining}\n\n"
			
			if links:
				text += "**Последние ссылки:**\n"
				for i, link in enumerate(links[:5], 1):
					text += f"{i}. {link['title']} ({link['click_count']} 👁)\n"
			
			await query.edit_message_text(
				text,
				reply_markup=InlineKeyboardMarkup(keyboard),
				parse_mode='Markdown'
			)
		
		elif query.data == "delete_all_links":
			logger.info(f"🔥🔥🔥 НАЖАТО delete_all_links")
			await query.answer()
			keyboard = [
				[
					InlineKeyboardButton("✅ Да, удалить все", callback_data="confirm_delete_all"),
					InlineKeyboardButton("❌ Нет", callback_data="links")
				]
			]
			await query.edit_message_text(
				"⚠️ **Ты уверен, что хочешь удалить ВСЕ ссылки?**\n\nЭто действие нельзя отменить!",
				reply_markup=InlineKeyboardMarkup(keyboard),
				parse_mode='Markdown'
			)
		
		elif query.data == "confirm_delete_all":
			await query.answer()
			logger.info(f"🔥 Удаляем все ссылки для page_id={page['id']}")
			result = await conn.execute("DELETE FROM links WHERE page_id = $1", page['id'])
			logger.info(f"🔥 Результат удаления: {result}")
			await query.edit_message_text(
				"✅ **Все ссылки удалены!**",
				reply_markup=InlineKeyboardMarkup([
					[InlineKeyboardButton("◀️ Назад", callback_data="links")]
				]),
				parse_mode='Markdown'
			)
		
		# Название файла: bot/handlers.py
		
		# # --- ПРОФИЛЬ ---
		elif query.data == "profile":
			# # Вместо того чтобы писать тут 20 строк текста, просто зовем функцию:
			await conn.close()  # Закрываем старое соединение диспетчера
			return await profile_handler(update, context)
		
		elif query.data == "confirm_self_delete":
			# # Закрываем conn перед уходом, чтобы finally в button_handler не ругался
			await conn.close()
			return await confirm_self_delete(update, context)
		
		elif query.data == "execute_self_delete":
			await conn.close()
			return await execute_self_delete(update, context)
		
		# --- СТАТИСТИКА ---
		elif query.data == "stats":
			await query.answer()
			links = await get_user_links(conn, page['id'])
			total_clicks = sum(link['click_count'] for link in links)
			text = f"📊 **Статистика**\n\n👀 Просмотры: {page['view_count'] or 0}\n🔗 Клики: {total_clicks}\n\n"
			if links:
				text += "🔝 Топ ссылок:\n"
				for link in sorted(links, key=lambda x: x['click_count'], reverse=True)[:3]:
					text += f"• {link['title']}: {link['click_count']}\n"
			keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="start")]]
			await query.edit_message_text(
				text,
				reply_markup=InlineKeyboardMarkup(keyboard),
				parse_mode='Markdown'
			)
	
	except Exception as e:
		logger.error(f"Ошибка в button_handler: {e}")
		try:
			# Пытаемся ответить пользователю об ошибке
			await query.edit_message_text("❌ Произошла ошибка. Нажмите /start")
		except:
			pass
	finally:
		# Проверяем, не закрыто ли соединение уже, чтобы не поймать ошибку в finally
		if not conn.is_closed():
			await conn.close()


# Название файла: bot/handlers.py

# Название файла: bot/handlers.py

# Название файла: bot/handlers.py

async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # # Обработчик профиля: команда /profile или кнопка
    query = update.callback_query
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # # 1. Удаляем старые уведомления об успехе
    if 'last_success_msg_id' in context.user_data:
        try:
            await context.bot.delete_message(
                chat_id=chat_id,
                message_id=context.user_data['last_success_msg_id']
            )
        except Exception:
            pass
        context.user_data.pop('last_success_msg_id', None)
    
    conn = await get_db_connection()
    try:
        # # ПЕРЕДАЕМ 5 АРГУМЕНТОВ (добавили user.last_name)
        db_user = await get_or_create_user(conn, user.id, user.username, user.first_name, user.last_name)
        
        # # Важно: убедись, что get_user_page переписана на asyncpg!
        page = await get_user_page(conn, db_user['id'])
        
        sub_status = await check_subscription(conn, user.id)
        
        if sub_status['active']:
            days = sub_status.get('days_left', 0)
            plan = f"💎 PRO ({days} дн.)"
        else:
            plan = "💡 Бесплатный"
        
        # # Перешли на HTML, чтобы не ловить ошибки Markdown на нижних подчеркиваниях в никах
        page_link = f"/{page['username']}" if page else "не создана"
        text = (
            f"<b>⚙️ Профиль</b>\n\n"
            f"🆔 ID: <code>{user.id}</code>\n"
            f"👤 Имя: {user.first_name}\n"
            f"📛 Username: @{user.username or 'не указан'}\n"
            f"🌐 Страница: <code>{page_link}</code>\n"
            f"💳 Тариф: <b>{plan}</b>\n"
            f"📅 Регистрация: {db_user['created_at'].strftime('%d.%m.%Y')}"
        )
        
        keyboard = [
            [InlineKeyboardButton("🗑 Удалить мой аккаунт", callback_data="confirm_self_delete")],
            [InlineKeyboardButton("◀️ Назад", callback_data="start")],
        ]
        markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            await query.answer()
            try:
                await query.edit_message_text(text, reply_markup=markup, parse_mode='HTML')
            except Exception:
                await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=markup, parse_mode='HTML')
        else:
            await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=markup, parse_mode='HTML')
    
    except Exception as e:
        await log_error(e, "в profile_handler") # # Используем нашу общую функцию логирования
        error_msg = "❌ Произошла ошибка при загрузке профиля."
        if query:
            await query.message.reply_text(error_msg)
        else:
            await update.message.reply_text(error_msg)
    finally:
        await conn.close()

async def confirm_self_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Шаг 1: Запрос подтверждения удаления"""
	query = update.callback_query
	await query.answer()
	
	keyboard = [
		[InlineKeyboardButton("🔥 ДА, УДАЛИТЬ НАВСЕГДА", callback_data="execute_self_delete")],
		[InlineKeyboardButton("◀️ Отмена", callback_data="profile")]
	]
	
	await query.edit_message_text(
		"⚠️ **ВНИМАНИЕ! УДАЛЕНИЕ АККАУНТА**\n\n"
		"Это действие **необратимо**. Будут удалены:\n"
		"• Ваш профиль и все настройки\n"
		"• Все ваши страницы и ссылки\n"
		"• Ваша PRO-подписка\n\n"
		"Вы уверены, что хотите продолжить?",
		reply_markup=InlineKeyboardMarkup(keyboard),
		parse_mode='Markdown'
	)


async def execute_self_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Шаг 2: Выполнение удаления через SQLAlchemy engine"""
	query = update.callback_query
	tg_id = update.effective_user.id
	
	# // Используем engine из админки
	from admin_handlers import engine
	from sqlalchemy import text
	
	try:
		async with engine.begin() as db_conn:
			# // 1. Получаем ID
			result = await db_conn.execute(
				text("SELECT id FROM users WHERE telegram_id = :tid"),
				{"tid": tg_id}
			)
			user_row = result.fetchone()
			
			if not user_row:
				await query.edit_message_text("❌ Пользователь не найден.")
				return
			
			u_id = user_row.id
			
			# // 2. Чистим Links -> Pages -> Users
			await db_conn.execute(
				text("DELETE FROM links WHERE page_id IN (SELECT id FROM pages WHERE user_id = :uid)"),
				{"uid": u_id}
			)
			await db_conn.execute(text("DELETE FROM pages WHERE user_id = :uid"), {"uid": u_id})
			await db_conn.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": u_id})
		
		await query.answer("Аккаунт удален", show_alert=True)
		await query.edit_message_text(
			"👋 **Ваш аккаунт успешно удален.**\n\n"
			"Все данные стерты. Чтобы начать заново, напишите /start",
			parse_mode='Markdown'
		)
	
	except Exception as e:
		logger.error(f"Ошибка при самоудалении {tg_id}: {e}")
		await query.edit_message_text("❌ Ошибка при удалении. Обратитесь в поддержку.")


async def receipt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
	# Проверяем флаг ожидания чека
	if not context.user_data.get('waiting_for_receipt'):
		return
	
	user = update.effective_user
	if not update.message.photo:
		return
	
	photo = update.message.photo[-1]
	context.user_data['receipt_sent'] = True
	context.user_data['waiting_for_receipt'] = False
	
	# Сообщение юзеру
	await update.message.reply_text(
		"✅ **Чек отправлен модераторам!**\n"
		"Обычно проверка занимает до 30 минут. Мы пришлем уведомление сразу после активации PRO."
	)
	
	# Информация для админов
	tier = context.user_data.get('selected_tier', '1m')
	caption = (
		f"💰 **НОВЫЙ ЧЕК: {tier}**\n"
		f"────────────────────\n"
		f"👤 Юзер: @{user.username or 'скрыт'}\n"
		f"🆔 ID: `{user.id}`\n"
		f"────────────────────\n"
		f"Проверьте баланс и нажмите кнопку:"
	)
	
	admin_kb = InlineKeyboardMarkup([
		[
			InlineKeyboardButton("✅ Одобрить", callback_data=f"adm_app_{user.id}_{tier}"),
			InlineKeyboardButton("❌ Отказ", callback_data=f"adm_dec_{user.id}")
		]
	])
	
	# Рассылка всем админам из твоего core.config
	for admin_id in ADMIN_IDS:
		try:
			await context.bot.send_photo(
				chat_id=admin_id,
				photo=photo.file_id,
				caption=caption,
				reply_markup=admin_kb,
				parse_mode='Markdown'
			)
		except Exception as e:
			logger.error(f"Ошибка отправки чека админу {admin_id}: {e}")


async def list_links_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	"""Показать список всех ссылок с кнопками управления"""
	
	# Удаляем предыдущее сообщение с подтверждением, если оно есть
	if 'last_success_msg_id' in context.user_data:
		try:
			await context.bot.delete_message(
				chat_id=update.effective_chat.id,
				message_id=context.user_data['last_success_msg_id']
			)
		except:
			pass
		context.user_data.pop('last_success_msg_id', None)
	
	query = update.callback_query
	await query.answer()
	
	user = update.effective_user
	conn = await get_db_connection()
	
	try:
		db_user = await get_or_create_user(conn, user.id, user.username, user.first_name)
		
		# ИСПРАВЛЕНИЕ: Проверяем наличие страницы
		page = await get_user_page(conn, db_user['id'])
		
		if not page:
			# Если страницы нет, предлагаем создать
			keyboard = [[InlineKeyboardButton("🚀 Создать страницу", callback_data="start")]]
			await query.edit_message_text(
				"❌ У вас еще нет страницы.\n\nНажмите /start чтобы создать!",
				reply_markup=InlineKeyboardMarkup(keyboard)
			)
			return
		
		links = await get_user_links(conn, page['id'])
		
		if not links:
			keyboard = [[InlineKeyboardButton("➕ Добавить ссылку", callback_data="add_link")],
			            [InlineKeyboardButton("◀️ Назад", callback_data="links")]]
			await query.edit_message_text(
				"📋 У вас пока нет ссылок.\n\nДобавьте свою первую ссылку!",
				reply_markup=InlineKeyboardMarkup(keyboard)
			)
			return
		
		# Создаем список ссылок с кнопками для каждой
		text = "🔗 <b>Ваши ссылки:</b>\n\n"
		keyboard = []
		
		for i, link in enumerate(links, 1):
			# Безопасно обрабатываем URL
			url_display = link['url']
			if url_display and len(url_display) > 50:
				url_display = url_display[:50] + '...'
			
			text += f"{i}. <b>{link['title']}</b>\n"
			text += f"   <code>{url_display}</code>\n"
			text += f"   👆 Кликов: {link['click_count']}\n\n"
			
			# Кнопки для каждой ссылки
			keyboard.append([
				InlineKeyboardButton(f"✏️ {link['title'][:15]}", callback_data=f"edit_link_{link['id']}")
			])
		
		# Добавляем кнопки управления
		keyboard.append([InlineKeyboardButton("➕ Добавить ссылку", callback_data="add_link")])
		keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="links")])
		
		await query.edit_message_text(
			text,
			reply_markup=InlineKeyboardMarkup(keyboard),
			parse_mode='HTML'
		)
	
	except Exception as e:
		logger.error(f"Ошибка в list_links_handler: {e}", exc_info=True)
		try:
			await query.edit_message_text("❌ Произошла ошибка. Попробуйте позже.")
		except:
			pass
	finally:
		await conn.close()


async def edit_link_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Меню редактирования конкретной ссылки"""
	
	# Удаляем предыдущее сообщение с подтверждением, если оно есть
	if 'last_success_msg_id' in context.user_data:
		try:
			await context.bot.delete_message(
				chat_id=update.effective_chat.id,
				message_id=context.user_data['last_success_msg_id']
			)
		except:
			pass
		context.user_data.pop('last_success_msg_id', None)
	
	query = update.callback_query
	await query.answer()
	
	# Получаем ID ссылки из callback_data
	link_id = int(query.data.replace("edit_link_", ""))
	context.user_data['editing_link_id'] = link_id
	context.user_data['editing_link'] = True
	
	conn = await get_db_connection()
	try:
		link = await conn.fetchrow("SELECT * FROM links WHERE id = $1", link_id)
		
		if not link:
			await query.edit_message_text("❌ Ссылка не найдена")
			return
		
		text = f"🔗 <b>Редактирование ссылки</b>\n\n"
		text += f"📝 <b>Название:</b> {link['title']}\n"
		text += f"🔗 <b>URL:</b> <code>{link['url']}</code>\n"
		text += f"🎨 <b>Иконка:</b> {link['icon']}\n"
		text += f"👆 <b>Кликов:</b> {link['click_count']}\n\n"
		text += "<b>Что хотите изменить?</b>"
		
		keyboard = [
			[InlineKeyboardButton("📝 Изменить название / заголовок", callback_data=f"edit_title_{link_id}")],
			[InlineKeyboardButton("🔗 Изменить URL / текст", callback_data=f"edit_url_{link_id}")],
			# [InlineKeyboardButton("🎨 Изменить иконку", callback_data=f"edit_icon_{link_id}")],
			[InlineKeyboardButton("⬆️ Переместить вверх", callback_data=f"move_up_{link_id}")],
			[InlineKeyboardButton("⬇️ Переместить вниз", callback_data=f"move_down_{link_id}")],
			[InlineKeyboardButton("❌ Удалить ссылку", callback_data=f"delete_{link_id}")],
			[InlineKeyboardButton("◀️ Назад к списку", callback_data="list_links")],
		]
		
		try:
			await query.edit_message_text(
				text,
				reply_markup=InlineKeyboardMarkup(keyboard),
				parse_mode='HTML'
			)
		except Exception as e:
			logger.error(f"Ошибка при редактировании: {e}")
			await query.message.reply_text("❌ Ошибка, но ссылка найдена. Попробуйте еще раз.")
	
	except Exception as e:
		logger.error(f"Ошибка в edit_link_menu: {e}")
		await query.edit_message_text("❌ Произошла ошибка")
	finally:
		await conn.close()


# Название файла: bot/handlers.py

# Название файла: bot/handlers.py

async def templates_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # # Используем # для Python комментариев
    
    is_callback = update.callback_query is not None
    user_id = update.effective_user.id
    
    if not is_callback:
       if 'last_success_msg_id' in context.user_data:
          try:
             await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=context.user_data['last_success_msg_id'])
          except: pass
          context.user_data.pop('last_success_msg_id', None)
    
    if is_callback:
       await update.callback_query.answer()
    
    conn = await get_db_connection()
    try:
       # # Тянем шаблоны
       templates = await conn.fetch("SELECT id, name, is_pro FROM templates WHERE is_active = true ORDER BY sort_order")
       
       await get_or_create_user(conn, user_id, update.effective_user.username, update.effective_user.first_name, update.effective_user.last_name)
       
       sub_status = await check_subscription(conn, user_id)
       is_pro_user = sub_status.get('active', False)
       
       # # СТРОГОЕ РАЗДЕЛЕНИЕ (проверяем на True/False)
       free_templates = [t for t in templates if not t['is_pro']]
       pro_templates = [t for t in templates if t['is_pro']]
       
       keyboard = []
       
       # # --- БЕСПЛАТНЫЕ ---
       if free_templates:
          keyboard.append([InlineKeyboardButton("📁 БЕСПЛАТНЫЕ", callback_data="noop")])
          row = []
          for i, t in enumerate(free_templates):
             row.append(InlineKeyboardButton(f"✅ {t['name']}", callback_data=f"select_template_{t['id']}"))
             if len(row) == 2 or i == len(free_templates) - 1:
                keyboard.append(row)
                row = []
       
       # # --- PREMIUM ---
       if pro_templates:
          header = "💎 ВАШ ПРЕМИУМ" if is_pro_user else "⭐ PREMIUM 🔒"
          keyboard.append([InlineKeyboardButton(header, callback_data="noop")])
          row = []
          for i, t in enumerate(pro_templates):
             if is_pro_user:
                btn_text = f"💎 {t['name']}"
                cb_data = f"select_template_{t['id']}"
             else:
                btn_text = f"⭐ {t['name']} 🔒"
                cb_data = f"unlock_pro_{t['id']}"
             
             row.append(InlineKeyboardButton(btn_text, callback_data=cb_data))
             if len(row) == 2 or i == len(pro_templates) - 1:
                keyboard.append(row)
                row = []

       keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="start")])
       
       text = (
           f"🎨 <b>Выбор шаблона страницы</b>\n\n"
           f"Статус: <b>{'💎 PRO' if is_pro_user else '💡 Бесплатный'}</b>\n"
           f"────────────────────\n"
           f"Выбирай любой из доступных вариантов:"
       )
       
       reply_markup = InlineKeyboardMarkup(keyboard)
       
       if is_callback:
          await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='HTML')
       else:
          sent_msg = await update.message.reply_text(text=text, reply_markup=reply_markup, parse_mode='HTML')
          context.user_data['last_success_msg_id'] = sent_msg.message_id
          
    finally:
       await conn.close()
	    
async def edit_link_title_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Начало редактирования названия ссылки"""
	query = update.callback_query
	await query.answer()
	
	# Получаем ID ссылки из callback_data (формат: edit_title_123)
	link_id = int(query.data.split('_')[2])
	
	# Сохраняем ID ссылки в user_data
	context.user_data['editing_link_id'] = link_id
	
	# Получаем текущее название из БД
	conn = await get_db_connection()
	try:
		link = await conn.fetchrow("SELECT title FROM links WHERE id = $1", link_id)
		current_title = link['title'] if link else "неизвестно"
	finally:
		await conn.close()
	
	await query.edit_message_text(
		f"✏️ Редактирование названия ссылки\n\n"
		f"Текущее название: **{current_title}**\n\n"
		f"Отправьте новое название ссылки:",
		parse_mode='Markdown'
	)
	
	return EDIT_LINK_TITLE  # Переходим в состояние ожидания названия


async def edit_link_title_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Сохранение нового названия ссылки"""
	user_id = update.effective_user.id
	new_title = update.message.text
	
	# Проверка на слишком длинное название
	if len(new_title) > 100:
		await update.message.reply_text(
			"❌ Название слишком длинное! Максимум 100 символов.\n"
			"Попробуйте еще раз или используйте /cancel"
		)
		return EDIT_LINK_TITLE  # Остаемся в том же состоянии
	
	# Получаем ID ссылки из context.user_data
	link_id = context.user_data.get('editing_link_id')
	
	if not link_id:
		await update.message.reply_text("❌ Ошибка: не найден ID ссылки")
		return ConversationHandler.END
	
	conn = await get_db_connection()
	try:
		# Обновляем название в БД
		await conn.execute(
			"UPDATE links SET title = $1 WHERE id = $2",
			new_title, link_id
		)
		
		await update.message.reply_text(
			f"✅ Название успешно изменено на: **{new_title}**",
			parse_mode='Markdown'
		)
		
		# Очищаем данные
		context.user_data.pop('editing_link_id', None)
		
		# Показываем обновленное меню ссылки
		await show_link_menu(update, context, link_id)
	
	except Exception as e:
		logger.error(f"Ошибка при редактировании названия: {e}")
		await update.message.reply_text(f"❌ Ошибка при сохранении: {e}")
	finally:
		await conn.close()
	
	return ConversationHandler.END  # Явно завершаем диалог


async def show_link_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, link_id: int):
	"""Вспомогательная функция для показа меню ссылки"""
	conn = await get_db_connection()
	try:
		link = await conn.fetchrow(
			"SELECT l.*, i.font_awesome_class as icon_class "
			"FROM links l "
			"LEFT JOIN icons i ON i.icon_code = l.icon "
			"WHERE l.id = $1",
			link_id
		)
		
		if not link:
			await update.message.reply_text("❌ Ссылка не найдена")
			return
		
		# Создаем клавиатуру для управления ссылкой
		keyboard = [
			[InlineKeyboardButton("✏️ Изменить название / заголовок", callback_data=f"edit_title_{link_id}")],
			[InlineKeyboardButton("🔗 Изменить URL / текст", callback_data=f"edit_url_{link_id}")],
			# [InlineKeyboardButton("🎨 Изменить иконку", callback_data=f"edit_icon_{link_id}")],
			[InlineKeyboardButton("⬆️ Переместить вверх", callback_data=f"move_up_{link_id}")],
			[InlineKeyboardButton("⬇️ Переместить вниз", callback_data=f"move_down_{link_id}")],
			[InlineKeyboardButton("🗑 Удалить", callback_data=f"delete_{link_id}")],
			[InlineKeyboardButton("◀️ Назад к списку", callback_data="list_links")]
		]
		reply_markup = InlineKeyboardMarkup(keyboard)
		
		icon_display = link['icon_class'] if link['icon_class'] else "🔗"
		await update.message.reply_text(
			f"**Управление ссылкой**\n\n"
			f"{icon_display} **{link['title']}**\n"
			f"`{link['url']}`\n\n"
			f"Выберите действие:",
			parse_mode='Markdown',
			reply_markup=reply_markup
		)
	finally:
		await conn.close()


# ===== РЕДАКТИРОВАНИЕ URL =====
async def edit_link_url_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()
	
	# Парсим ID ссылки
	link_id = int(query.data.split('_')[-1])
	context.user_data['editing_link_id'] = link_id
	context.user_data['last_menu_msg_id'] = query.message.message_id
	
	# Получаем текущие данные, чтобы показать их юзеру
	conn = await get_db_connection()
	link = await conn.fetchrow("SELECT * FROM links WHERE id = $1", link_id)
	await conn.close()
	
	# Формируем текст так, чтобы инфа ОСТАЛАСЬ на экране
	text = (
		f"🔗 **Редактирование ссылки**\n"
		f"————————————————————\n"
		f"📝 Название: **{link['title']}**\n"
		f"🔗 Текущий URL: `{link['url']}`\n"
		f"————————————————————\n\n"
		f"✏️ **Введите НОВЫЙ URL для этой ссылки:**\n"
		f"_(просто отправьте сообщение с адресом)_"
	)
	
	# Оставляем только кнопку отмены
	keyboard = [[InlineKeyboardButton("❌ Отмена (назад)", callback_data=f"edit_link_{link_id}")]]
	
	await query.edit_message_text(
		text=text,
		reply_markup=InlineKeyboardMarkup(keyboard),
		parse_mode="Markdown"
	)
	return EDIT_LINK_URL


async def edit_link_url_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
	new_url = update.message.text
	link_id = context.user_data.get('editing_link_id')
	last_msg_id = context.user_data.get('last_menu_msg_id')
	
	# Удаляем сообщение пользователя (чтобы не мусорить)
	try:
		await update.message.delete()
	except:
		pass
	
	conn = await get_db_connection()
	try:
		# Обновляем URL
		await conn.execute("UPDATE links SET url = $1 WHERE id = $2", new_url, link_id)
		link = await conn.fetchrow("SELECT * FROM links WHERE id = $1", link_id)
		
		# Возвращаем полное меню в ТО ЖЕ САМОЕ сообщение
		text = (
			f"✅ **URL успешно изменен!**\n\n"
			f"📝 **Название:** {link['title']}\n"
			f"🔗 **URL:** {link['url']}\n"
			f"🎨 **Иконка:** {link['icon']}\n"
			f"👆 **Кликов:** {link['click_count']}\n\n"
			f"**Что еще изменить?**"
		)
		
		keyboard = [
			[InlineKeyboardButton("📝 Изменить название / заголовок", callback_data=f"edit_title_{link_id}")],
			[InlineKeyboardButton("🔗 Изменить URL / текст", callback_data=f"edit_url_{link_id}")],
			# [InlineKeyboardButton("🎨 Изменить иконку", callback_data=f"edit_icon_{link_id}")],
			[InlineKeyboardButton("◀️ Назад к списку", callback_data="list_links")],
		]
		
		await context.bot.edit_message_text(
			chat_id=update.effective_chat.id,
			message_id=last_msg_id,
			text=text,
			reply_markup=InlineKeyboardMarkup(keyboard),
			parse_mode="Markdown"
		)
	
	finally:
		await conn.close()
	
	return ConversationHandler.END


# ===== РЕДАКТИРОВАНИЕ ИКОНКИ =====


async def edit_link_icon_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Начало редактирования иконки"""
	query = update.callback_query
	await query.answer()
	
	link_id = context.user_data.get('editing_link_id')
	
	if not link_id:
		try:
			link_id = int(query.data.replace("edit_icon_", ""))
			context.user_data['editing_link_id'] = link_id
		except:
			await query.edit_message_text("❌ Ошибка: не найден ID ссылки")
			return ConversationHandler.END
	
	conn = await get_db_connection()
	try:
		icons = await conn.fetch("SELECT icon_code, name FROM icons WHERE is_active = true LIMIT 8")
		
		keyboard = []
		row = []
		for i, icon in enumerate(icons):
			btn = InlineKeyboardButton(icon['name'], callback_data=f"change_icon_{icon['icon_code']}")
			row.append(btn)
			if (i + 1) % 2 == 0:
				keyboard.append(row)
				row = []
		if row:
			keyboard.append(row)
		
		keyboard.append([InlineKeyboardButton("◀️ Отмена", callback_data=f"edit_link_{link_id}")])
		
		await query.edit_message_text(
			"🎨 Выберите иконку:",
			reply_markup=InlineKeyboardMarkup(keyboard)
		)
	finally:
		await conn.close()
	
	return EDIT_LINK_ICON


async def edit_link_icon_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Сохранение новой иконки"""
	query = update.callback_query
	await query.answer()
	
	new_icon = query.data.replace("change_icon_", "")
	link_id = context.user_data.get('editing_link_id')
	
	conn = await get_db_connection()
	try:
		await conn.execute(
			"UPDATE links SET icon = $1 WHERE id = $2",
			new_icon, link_id
		)
		
		keyboard = [
			[InlineKeyboardButton("✏️ Изменить название / заголовок", callback_data=f"edit_title_{link_id}")],
			[InlineKeyboardButton("🔗 Изменить URL / текст", callback_data=f"edit_url_{link_id}")],
			[InlineKeyboardButton("⬆️ Вверх", callback_data=f"move_up_{link_id}")],
			[InlineKeyboardButton("⬇️ Вниз", callback_data=f"move_down_{link_id}")],
			[InlineKeyboardButton("❌ Удалить", callback_data=f"delete_{link_id}")],
			[InlineKeyboardButton("◀️ К списку", callback_data="list_links")],
		]
		
		await query.edit_message_text(
			f"✅ Иконка изменена на {new_icon}\n\nЧто дальше?",
			reply_markup=InlineKeyboardMarkup(keyboard)
		)
	finally:
		await conn.close()
	
	return ConversationHandler.END


# ===== ПЕРЕМЕЩЕНИЕ =====
async def move_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Переместить ссылку и показать меню"""
	query = update.callback_query
	await query.answer()
	
	# Парсим данные
	parts = query.data.split('_')
	direction = parts[1]  # up или down
	link_id = int(parts[2])
	
	conn = await get_db_connection()
	try:
		# Получаем информацию о ссылке
		link = await conn.fetchrow("SELECT * FROM links WHERE id = $1", link_id)
		
		if not link:
			await query.edit_message_text("❌ Ссылка не найдена")
			return
		
		current_sort = link['sort_order']
		page_id = link['page_id']
		
		# Логика перемещения (та же, что выше)
		if direction == 'up' and current_sort > 0:
			await conn.execute("""
                               UPDATE links
                               SET sort_order =
                                       CASE
                                           WHEN id = $1 THEN sort_order - 1
                                           WHEN sort_order = $2 - 1 THEN sort_order + 1
                                           END
                               WHERE page_id = $3
                                 AND sort_order IN ($2, $2 - 1)
			                   """, link_id, current_sort, page_id)
		elif direction == 'down':
			# Проверяем, есть ли ссылка снизу
			max_sort = await conn.fetchval(
				"SELECT MAX(sort_order) FROM links WHERE page_id = $1",
				page_id
			)
			if current_sort < max_sort:
				await conn.execute("""
                                   UPDATE links
                                   SET sort_order =
                                           CASE
                                               WHEN id = $1 THEN sort_order + 1
                                               WHEN sort_order = $2 + 1 THEN sort_order - 1
                                               END
                                   WHERE page_id = $3
                                     AND sort_order IN ($2, $2 + 1)
				                   """, link_id, current_sort, page_id)
		
		# Получаем обновленные данные ссылки
		updated_link = await conn.fetchrow(
			"SELECT l.*, i.font_awesome_class as icon_class "
			"FROM links l "
			"LEFT JOIN icons i ON i.icon_code = l.icon "
			"WHERE l.id = $1",
			link_id
		)
		
		# Показываем меню ссылки
		icon_display = updated_link['icon_class'] if updated_link['icon_class'] else "🔗"
		keyboard = [
			[InlineKeyboardButton("✏️ Изменить название / заголовок", callback_data=f"edit_title_{link_id}")],
			[InlineKeyboardButton("🔗 Изменить URL / текст", callback_data=f"edit_url_{link_id}")],
			# [InlineKeyboardButton("🎨 Изменить иконку", callback_data=f"edit_icon_{link_id}")],
			[InlineKeyboardButton("◀️ К списку", callback_data="list_links")],
		]
		
		await query.edit_message_text(
			f"✅ Ссылка перемещена {direction}\n\n"
			f"{icon_display} **{updated_link['title']}**\n"
			f"`{updated_link['url']}`\n\n"
			f"Что дальше?",
			parse_mode='Markdown',
			reply_markup=InlineKeyboardMarkup(keyboard)
		)
	
	except Exception as e:
		logger.error(f"Ошибка при перемещении: {e}")
		await query.edit_message_text(f"❌ Ошибка: {e}")
	finally:
		await conn.close()


# ===== УДАЛЕНИЕ =====
async def delete_link_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()  # <-- ОБЯЗАТЕЛЬНО добавить!
	
	print(f"=== delete_link_confirm ВЫЗВАНА! ===")
	
	if query.data == "delete_all_links":  # пропускаем
		print("Пропуск delete_all_links")
		return
	
	link_id = int(query.data.replace("delete_", ""))
	print(f"ID ссылки для подтверждения: {link_id}")
	
	keyboard = [
		[
			InlineKeyboardButton("✅ Да", callback_data=f"confirm_delete_{link_id}"),
			InlineKeyboardButton("❌ Нет", callback_data=f"edit_link_{link_id}")
		]
	]
	
	await query.edit_message_text(
		"⚠️ Удалить ссылку?",
		reply_markup=InlineKeyboardMarkup(keyboard)
	)


async def delete_all_links_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()
	
	print("=== delete_all_links_confirm ВЫЗВАНА ===")
	
	# Получаем данные пользователя
	user = update.effective_user
	telegram_id = user.id
	username = user.username
	first_name = user.first_name
	
	conn = await get_db_connection()
	try:
		# ИСПОЛЬЗУЕМ существующую функцию get_or_create_user
		db_user = await get_or_create_user(
			conn,
			telegram_id,
			username,
			first_name
		)
		
		# Теперь получаем page_id через users.id
		page_id = await conn.fetchval(
			"SELECT id FROM pages WHERE user_id = $1",
			db_user['id']  # Важно! Используем users.id, а не telegram_id
		)
		
		print(f"Найден page_id: {page_id}")
		
		if not page_id:
			await query.edit_message_text("❌ Ошибка: страница не найдена")
			return
		
		# Сохраняем для следующего шага
		context.user_data['deleting_all_page_id'] = page_id
		
		# Показываем подтверждение
		keyboard = [
			[
				InlineKeyboardButton("⚠️ ДА, удалить все", callback_data="confirm_delete_all"),
				InlineKeyboardButton("❌ Нет, отмена", callback_data="list_links")
			]
		]
		
		await query.edit_message_text(
			"🚨 **ВНИМАНИЕ!**\n\nВы действительно хотите **удалить ВСЕ ссылки**?",
			reply_markup=InlineKeyboardMarkup(keyboard),
			parse_mode="Markdown"
		)
	finally:
		await conn.close()


async def delete_all_links_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Окончательное удаление ВСЕХ ссылок"""
	query = update.callback_query
	await query.answer()
	
	print("=== delete_all_links_execute ВЫЗВАНА ===")
	
	# Получаем page_id из сохраненного контекста
	page_id = context.user_data.get('deleting_all_page_id')
	
	if not page_id:
		await query.edit_message_text("❌ Ошибка: страница не найдена")
		return
	
	conn = await get_db_connection()
	try:
		# Сначала посчитаем, сколько ссылок удаляем
		count = await conn.fetchval("SELECT COUNT(*) FROM links WHERE page_id = $1", page_id)
		
		# Удаляем все ссылки для этой страницы
		await conn.execute("DELETE FROM links WHERE page_id = $1", page_id)
		
		# Очищаем сохраненные данные
		context.user_data.pop('deleting_all_page_id', None)
		
		await query.edit_message_text(
			f"✅ **Удалено {count} ссылок!**\n\nВсе ссылки были успешно удалены.\n\nЧто дальше?",
			reply_markup=InlineKeyboardMarkup([
				[InlineKeyboardButton("➕ Добавить новую ссылку", callback_data="add_link")],
				[InlineKeyboardButton("◀️ В главное меню", callback_data="start")]
			]),
			parse_mode="Markdown"
		)
	except Exception as e:
		print(f"Ошибка при удалении всех ссылок: {e}")
		await query.edit_message_text(
			"❌ Произошла ошибка при удалении ссылок",
			reply_markup=InlineKeyboardMarkup([
				[InlineKeyboardButton("◀️ Назад", callback_data="list_links")]
			])
		)
	finally:
		await conn.close()


async def get_page_id_from_user(user_id: int):
	"""Получает page_id по user_id"""
	conn = await get_db_connection()
	try:
		page_id = await conn.fetchval("SELECT id FROM pages WHERE user_id = $1", user_id)
		return page_id
	finally:
		await conn.close()


async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Показывает категории иконок"""
	
	# ===== ДИАГНОСТИКА =====
	print("\n" + "🔥" * 50)
	print("🔥 show_categories ВЫЗВАНА!")
	print(f"🔥 callback_data: {update.callback_query.data}")
	print(f"🔥 user_data keys: {list(context.user_data.keys())}")
	print(f"🔥 _state: {context.user_data.get('_state')}")
	print(f"🔥 _conversation: {context.user_data.get('_conversation')}")
	print("🔥" * 50 + "\n")
	# ========================
	"""Показывает категории иконок"""
	query = update.callback_query
	await query.answer()
	
	conn = await get_db_connection()
	try:
		# Берем уникальные категории
		categories = await conn.fetch("SELECT DISTINCT category FROM icons WHERE is_active = true ORDER BY category")
		
		keyboard = []
		row = []
		for res in categories:
			cat = res['category']
			row.append(InlineKeyboardButton(f"📁 {cat}", callback_data=f"cat_{cat}"))
			if len(row) == 2:
				keyboard.append(row)
				row = []
		if row: keyboard.append(row)
		keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="links")])
		
		await query.edit_message_text(
			
			"🎨 **Выбери категорию иконок:**",
			
			reply_markup=InlineKeyboardMarkup(keyboard),
			parse_mode="Markdown"
		)
	finally:
		await conn.close()
	
	# ===== ОБРАБОТЧИКИ ШАБЛОНОВ =====
	
	# Заглушка для разделителей
	if query.data == "noop":
		await query.answer()
		return


async def select_template_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()
	
	try:
		template_id = int(query.data.split('_')[2])
		telegram_id = update.effective_user.id
		
		conn = await get_db_connection()
		try:
			# 1. Проверяем существование шаблона
			template = await conn.fetchrow(
				"SELECT id, name, is_pro FROM templates WHERE id = $1",
				template_id
			)
			
			if not template:
				await query.edit_message_text("❌ Ошибка: Шаблон не найден.")
				return
			
			# 2. Обновляем template_id в таблице pages одним запросом через подзапрос
			# Это связывает telegram_id из users с записью в pages
			result = await conn.execute("""
                                        UPDATE pages
                                        SET template_id = $1
                                        WHERE user_id = (SELECT id FROM users WHERE telegram_id = $2)
			                            """, template_id, telegram_id)
			
			if result == "UPDATE 0":
				await query.edit_message_text("❌ Ошибка: Страница не создана.")
				return
			
			# 3. Ответ пользователю
			pro_emoji = "👑 " if template['is_pro'] else "🎨 "
			
			menu_keyboard = [
				[InlineKeyboardButton("◀️ К шаблонам", callback_data="templates_menu")],
				[InlineKeyboardButton("🏠 В главное меню", callback_data="start")]
			]
			
			await query.edit_message_text(
				text=f"✅ {pro_emoji}**{template['name']}** успешно установлен!\n\nПроверь свой сайт.",
				parse_mode='Markdown',
				reply_markup=InlineKeyboardMarkup(menu_keyboard)
			)
		
		except Exception as e:
			logger.error(f"DB Error: {e}")
			await query.edit_message_text("❌ Ошибка базы данных.")
		finally:
			await conn.close()
	
	except Exception as e:
		logger.error(f"General Error: {e}")
		await query.edit_message_text("❌ Ошибка при выборе.")


async def unlock_pro_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Обработчик кнопки разблокировки PRO шаблона"""
	query = update.callback_query
	await query.answer()
	
	# Проверяем формат данных
	parts = query.data.split('_')
	if len(parts) >= 3 and parts[0] == 'unlock' and parts[1] == 'pro':
		template_id = int(parts[2])
		context.user_data['pro_template_id'] = template_id
	
	keyboard = [
		[InlineKeyboardButton("💳 PRO на месяц (300₽)", callback_data="buy_monthly")],
		[InlineKeyboardButton("💳 PRO на год (3000₽, скидка 17%)", callback_data="buy_yearly")],
		[InlineKeyboardButton("◀️ Назад к шаблонам", callback_data="templates_menu")]
	]
	reply_markup = InlineKeyboardMarkup(keyboard)
	
	await query.edit_message_text(
		"⭐ **Оформление PRO подписки**\n\n"
		"**Тарифы:**\n"
		"• Месяц — 300₽\n"
		"• Год — 3000₽ (экономия 600₽)\n\n"
		"**Преимущества PRO:**\n"
		"✅ Все 7 премиум шаблонов\n"
		"✅ Приоритетная поддержка\n"
		"✅ Больше настроек\n"
		"✅ Без рекламы\n\n"
		"Выберите тариф:",
		parse_mode='Markdown',
		reply_markup=reply_markup
	)


# ===== ОБРАБОТЧИКИ ДЛЯ ДОБАВЛЕНИЯ ССЫЛКИ =====


async def add_link_title_invalid(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Обработка некорректного ввода названия"""
	await update.message.reply_text(
		"❌ Пожалуйста, отправьте **текстовое сообщение** с названием ссылки.\n"
		"Используйте /cancel для отмены."
	)
	return ADD_LINK_TITLE  # Остаемся в том же состоянии


# Добавьте в bot/handlers.py

async def add_link_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Получаем название ссылки (шаг 1/3)"""
	logger.info(f"📝 add_link_title вызван с текстом: {update.message.text}")
	
	# Проверяем, что это текстовое сообщение
	if not update.message or not update.message.text:
		await update.message.reply_text(
			"❌ Пожалуйста, отправьте **текстовое сообщение** с названием ссылки.",
			parse_mode='HTML'
		)
		return ADD_LINK_TITLE
	
	# Сохраняем название
	title = update.message.text.strip()
	
	# Проверки
	if not title:
		await update.message.reply_text("❌ Название не может быть пустым. Введите название ссылки:")
		return ADD_LINK_TITLE
	
	if len(title) > 50:
		await update.message.reply_text(
			"❌ Слишком длинное название! Максимум 50 символов.\nПопробуйте еще раз:"
		)
		return ADD_LINK_TITLE
	
	# Сохраняем в user_data
	context.user_data['new_link_title'] = title
	logger.info(f"✅ Сохранено название: {title}")
	
	# Определяем следующий шаг
	link_type = context.user_data.get('link_type', 'standard')
	
	if link_type == 'finance':
		await update.message.reply_text(
			"💰 <b>Шаг 2 из 2:</b> Отправьте номер карты или кошелька.\n"
			"Примеры:\n"
			"• 1234 5678 9012 3456 (карта)\n"
			"• 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa (BTC)\n"
			"• TXqwZ3L8z9YpXnRkQv2M4N6bVcF7dG1hJk (USDT)",
			parse_mode='HTML'
		)
		return ADD_LINK_URL
	else:
		await update.message.reply_text(
			"🔗 <b>Шаг 2 из 3:</b> Отправьте ссылку.\n"
			"Примеры:\n"
			"• https://instagram.com/username\n"
			"• vk.com/id123 (я сам добавлю https://)",
			parse_mode='HTML'
		)
		return ADD_LINK_URL


async def add_link_url_invalid(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Обработка некорректного ввода URL"""
	await update.message.reply_text(
		"❌ Пожалуйста, отправьте **корректный URL** ссылки.\n"
		"Например: https://t.me/yourchannel или https://example.com\n"
		"Используйте /cancel для отмены."
	)
	return ADD_LINK_URL  # Остаемся в том же состоянии


# ===== ОБРАБОТЧИКИ ДЛЯ РЕДАКТИРОВАНИЯ НАЗВАНИЯ =====

async def edit_link_title_invalid(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Обработка некорректного ввода при редактировании названия"""
	await update.message.reply_text(
		"❌ Пожалуйста, отправьте **текстовое сообщение** с новым названием ссылки.\n"
		"Или используйте /cancel для отмены."
	)
	return EDIT_LINK_TITLE  # Остаемся в том же состоянии


# ===== ОБРАБОТЧИКИ ДЛЯ РЕДАКТИРОВАНИЯ URL =====

async def edit_link_url_invalid(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Обработка некорректного ввода при редактировании URL"""
	await update.message.reply_text(
		"❌ Пожалуйста, отправьте **корректный URL**.\n"
		"Например: https://example.com или https://t.me/channel\n"
		"Или используйте /cancel для отмены."
	)
	return EDIT_LINK_URL  # Остаемся в том же состоянии


# ===== УЛУЧШЕННЫЙ ОБРАБОТЧИК ОТМЕНЫ =====

# bot/handlers.py

# Название файла: bot/handlers.py

# Название файла: bot/handlers.py

async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Отмена текущего действия с возвратом в ПРАВИЛЬНОЕ меню"""
	
	# # ===== ОТЛАДКА =====
	current_state = context.user_data.get('_state')
	conversation_name = context.user_data.get('_conversation')
	print(f"\n🔍 cancel_handler ВЫЗВАН")
	print(f"🔍 ДИАЛОГ: {conversation_name}")
	print(f"🔍 СОСТОЯНИЕ: {current_state}")
	if update.callback_query:
		print(f"🔍 callback_data: {update.callback_query.data}")
	print("=" * 40)
	# # ===================
	
	user = update.effective_user
	
	# # ОПРЕДЕЛЯЕМ ТЕКУЩИЙ ДИАЛОГ
	logger.info(f"❌ CANCEL в диалоге: {conversation_name}")
	
	# # 1. Очищаем мусор
	keys_to_clear = ['editing_link_id', 'new_link_title', 'new_link_url',
	                 'selected_methods', 'filling_queue', 'collected_methods',
	                 'current_method', 'selected_country', '_state', '_conversation']
	for key in keys_to_clear:
		context.user_data.pop(key, None)
	
	# # 2. Показываем соответствующее меню без лишнего пиздежа
	if update.callback_query:
		await update.callback_query.answer()
		
		if conversation_name == "bank_world_conversation":
			from bot.bank import choose_country
			await choose_country(update, context)
		else:
			# // Сразу кидаем в старт
			from bot.handlers import start_handler
			await start_handler(update, context)
	else:
		# // Если ввел /cancel текстом — просто молча редиректим на старт
		from bot.handlers import start_handler
		await start_handler(update, context)
	
	logger.info(f"Пользователь {user.id} отменил действие")
	return ConversationHandler.END


# --- Новые обработчики покупки ---

async def buy_monthly_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
	# 1. Захватываем объект нажатия кнопки
	query = update.callback_query
	
	# 2. Отвечаем Телеграму, что нажатие принято (убираем "часики")
	await query.answer()
	
	# 3. Создаем кнопки для этого конкретного экрана
	keyboard = [
		[InlineKeyboardButton("✅ Оплачено (тест)", callback_data="activate_pro")],
		[InlineKeyboardButton("◀️ Назад", callback_data="upgrade")]
	]
	reply_markup = InlineKeyboardMarkup(keyboard)
	
	# 4. Меняем старое меню на экран оплаты
	await query.edit_message_text(
		"💳 **Оплата PRO: 1 месяц**\n\n"
		"Сумма: **$5**\n\n"
		"🔗 [Оплатить через Stripe](https://buy.stripe.com/14AbJ3djxdf0fHq4sI1B600)\n\n"
		"После оплаты нажмите кнопку ниже:",
		parse_mode='Markdown',
		reply_markup=reply_markup
	)


async def buy_3_months_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()
	
	keyboard = [
		[InlineKeyboardButton("📸 Отправить скриншот чека", callback_data="send_receipt")],
		[InlineKeyboardButton("◀️ Назад", callback_data="upgrade")]
	]
	
	await query.edit_message_text(
		"💳 **Оплата PRO: 3 месяца**\n\nСумма: **$12**\n\n"
		"🔗 [Оплатить через Stripe](https://stripe.com/pay/...)\n\n"
		"После оплаты нажмите кнопку ниже:",
		parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard)
	)


async def buy_6_months_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()
	
	keyboard = [[InlineKeyboardButton("✅ Оплачено (тест)", callback_data="activate_pro")],
	            [InlineKeyboardButton("◀️ Назад", callback_data="upgrade")]]
	
	await query.edit_message_text(
		"💳 **Оплата PRO: 6 месяцев**\n\nСумма: **$22**\n\n"
		"🔗 [Оплатить через Stripe](https://stripe.com/pay/...)\n\n"
		"После оплаты нажмите кнопку ниже:",
		parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard)
	)


async def buy_yearly_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()
	
	keyboard = [[InlineKeyboardButton("✅ Оплачено (тест)", callback_data="activate_pro")],
	            [InlineKeyboardButton("◀️ Назад", callback_data="upgrade")]]
	
	await query.edit_message_text(
		"💳 **Оплата PRO: 1 год**\n\nСумма: **$40**\n\n"
		"🔗 [Оплатить через Stripe](https://stripe.com/pay/...)\n\n"
		"После оплаты нажмите кнопку ниже:",
		parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard)
	)


async def buy_life_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()
	
	keyboard = [[InlineKeyboardButton("✅ Оплачено (тест)", callback_data="activate_pro")],
	            [InlineKeyboardButton("◀️ Назад", callback_data="upgrade")]]
	
	await query.edit_message_text(
		"👑 **ПОЖИЗНЕННЫЙ PRO ДОСТУП**\n\nСумма: **$150**\n\n"
		"🔗 [Оплатить через Stripe](https://stripe.com/pay/...)\n\n"
		"Это единоразовый платеж. Все функции навсегда!",
		parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard)
	)


async def send_receipt_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()
	
	# Включаем состояние ожидания фото в памяти бота
	context.user_data['waiting_for_photo'] = True
	
	await query.edit_message_text(
		"📝 **Инструкция:**\n\n"
		"1. Сделайте скриншот чека об оплате.\n"
		"2. **Просто прикрепите и отправьте его в этот чат**, как обычное фото.\n\n"
		"После отправки я передам его администратору на проверку.",
		parse_mode='Markdown'
	)


async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Ловит текст для QR-кода от PRO юзеров"""
	if context.user_data.get('waiting_for_qr_text'):
		user_text = update.message.text
		
		# УВЕЛИЧИВАЕМ ЛИМИТ ДО 30 ЗНАКОВ
		if len(user_text) > 30:
			await update.message.reply_text("❌ Текст слишком длинный (макс. 30 симв.). Попробуйте короче!")
			return
		
		# Удаляем сообщение пользователя с текстом для чистоты чата (опционально, но красиво)
		try:
			await update.message.delete()
		except:
			pass
		
		context.user_data['waiting_for_qr_text'] = False
		context.user_data['temp_qr_text'] = user_text  # Сохраняем текст для PIL
		
		# Сразу вызываем генерацию нового QR
		return await qr_handler(update, context)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
	# 1. Проверяем, ждем ли мы вообще фото от этого юзера
	if not context.user_data.get('waiting_for_photo'):
		return
	
	user = update.effective_user
	photo_file = update.message.photo[-1].file_id
	
	# Достаем тариф, который юзер выбрал в upgrade_handler
	selected_plan = context.user_data.get('selected_plan', '1m')
	
	# 2. Сразу подтверждаем юзеру
	await update.message.reply_text(
		"✅ **Чек получен и отправлен на проверку!**\n"
		"Обычно это занимает от 5 до 30 минут. Мы пришлем уведомление."
	)
	
	# 3. Выключаем режим ожидания фото
	context.user_data['waiting_for_photo'] = False
	
	# 4. Формируем кнопки для админов
	# ВАЖНО: В callback_data теперь пишем и ID юзера, и сам тариф!
	keyboard = [
		[
			InlineKeyboardButton(f"✅ Одобрить {selected_plan}",
			                     callback_data=f"admin_approve_{user.id}_{selected_plan}"),
			InlineKeyboardButton("❌ Отклонить", callback_data=f"admin_reject_{user.id}")
		]
	]
	reply_markup = InlineKeyboardMarkup(keyboard)
	
	# 5. ПЕРЕСЫЛАЕМ ЧЕК АДМИНАМ
	for admin_id in ADMIN_IDS:
		try:
			await context.bot.send_photo(
				chat_id=admin_id,
				photo=photo_file,
				caption=(
					f"💰 **Новая оплата!**\n\n"
					f"👤 Юзер: @{user.username or 'без юзернейма'}\n"
					f"🆔 ID: `{user.id}`\n"
					f"📅 Тариф: **{selected_plan}**"
				),
				reply_markup=reply_markup,
				parse_mode='Markdown'
			)
		except Exception as e:
			logger.error(f"Не удалось отправить чек админу {admin_id}: {e}")


# bot/admin_handlers.py (или где у тебя обработка колбэков)

async def admin_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()
	
	# Разбираем данные: admin_payment_approve_USERID_PLAN
	# Структура: ['admin', 'payment', 'approve/reject', 'target_user_id', 'plan']
	data = query.data.split('_')
	action = data[2]  # approve или reject
	target_tg_id = int(data[3])
	
	conn = await get_db_connection()
	try:
		if action == "approve":
			plan = data[4] if len(data) > 4 else "1m"
			
			# 1. Считаем дни
			days = 31
			if "3m" in plan:
				days = 93
			elif "6m" in plan:
				days = 186
			elif "12m" in plan or "1y" in plan:
				days = 366
			elif "life" in plan:
				days = 36500  # 100 лет
			
			# 2. ОБНОВЛЯЕМ ТАБЛИЦУ USERS (Напрямую!)
			# Ставим флаг и дату окончания. Также обновляем subscribe_until для совместимости
			await conn.execute("""
                               UPDATE users
                               SET is_pro         = true,
                                   pro_expires_at = NOW() + interval '1 day' * $2, subscribe_until = NOW() + interval '1 day' * $2
                               WHERE telegram_id = $1
			                   """, target_tg_id, days)
			
			# 3. Уведомляем пользователя
			try:
				await context.bot.send_message(
					chat_id=target_tg_id,
					text=(
						"👑 <b>PRO-статус активирован!</b>\n\n"
						"Спасибо за поддержку сервиса! Теперь тебе доступны:\n"
						"✅ Неограниченные ссылки\n"
						"💳 Финансовые реквизиты (Карты/Крипта)\n"
						"✨ Текст под QR-кодом\n"
						"🎨 Премиум шаблоны"
					),
					parse_mode='HTML'
				)
			except Exception as e:
				logger.warning(f"Не удалось отправить сообщение юзеру {target_tg_id}: {e}")
			
			# 4. Обновляем сообщение у админа
			new_caption = query.message.caption + "\n\n✅ <b>ПОДТВЕРЖДЕНО</b> (Статус выдан)"
			await query.edit_message_caption(caption=new_caption, parse_mode='HTML')
		
		elif action == "reject":
			try:
				await context.bot.send_message(
					chat_id=target_tg_id,
					text="❌ <b>Ваш платеж не прошел проверку.</b>\n\nЕсли это ошибка, свяжитесь с поддержкой.",
					parse_mode='HTML'
				)
			except:
				pass
			
			new_caption = query.message.caption + "\n\n❌ <b>ОТКЛОНЕНО</b>"
			await query.edit_message_caption(caption=new_caption, parse_mode='HTML')
	
	except Exception as e:
		logger.error(f"Ошибка в admin_payment_callback: {e}", exc_info=True)
		await query.message.reply_text(f"❌ Ошибка при активации: {e}")
	finally:
		await conn.close()


async def admin_approve_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	user_id_to_approve = int(query.data.split("_")[-1])
	caption = query.message.caption or ""
	
	# Определяем интервал (код остается прежним)
	if "1 месяц" in caption:
		interval = "1 month"
	elif "3 месяца" in caption:
		interval = "3 months"
	elif "6 месяцев" in caption:
		interval = "6 months"
	elif "1 год" in caption:
		interval = "1 year"
	elif "Пожизненно" in caption:
		interval = "100 years"
	else:
		interval = "1 month"
	
	conn = await get_db_connection()
	try:
		# --- ВОТ ЭТОТ БЛОК (ИСПРАВЛЕННЫЙ) ---
		await conn.execute(
			f"UPDATE users SET "
			f"is_pro = true, "
			f"pro_expires_at = CASE "
			f"    WHEN pro_expires_at > CURRENT_TIMESTAMP THEN pro_expires_at + INTERVAL '{interval}' "
			f"    ELSE CURRENT_TIMESTAMP + INTERVAL '{interval}' "
			f"END "
			f"WHERE telegram_id = $1",
			user_id_to_approve
		)  # ------------------------------------
		
		# Возвращаем шаблон, если он был сохранен
		last_pro = await conn.fetchval(
			"SELECT last_pro_template_id FROM users WHERE telegram_id = $1",
			user_id_to_approve
		)
		if last_pro:
			await conn.execute(
				"UPDATE pages SET template_id = $1 WHERE user_id = (SELECT id FROM users WHERE telegram_id = $2)",
				last_pro, user_id_to_approve
			)
			await conn.execute("UPDATE users SET last_pro_template_id = NULL WHERE telegram_id = $1",
			                   user_id_to_approve)
		
		# Уведомления
		await context.bot.send_message(
			chat_id=user_id_to_approve,
			text=f"💎 **PRO-статус активирован!**\nСрок: {interval.replace('month', 'мес').replace('year', 'год')}"
		)
		
		await query.edit_message_caption(
			caption=caption + f"\n\n✅ **АКТИВИРОВАНО (is_pro=true)**",
			reply_markup=None
		)
	
	except Exception as e:
		logger.error(f"Ошибка активации: {e}")
	finally:
		await conn.close()


async def activate_pro_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Активация PRO подписки (после оплаты)"""
	query = update.callback_query
	await query.answer()
	
	user_id = update.effective_user.id
	
	conn = await get_db_connection()
	try:
		# Активируем PRO подписку на 30 дней
		await conn.execute("""
                           UPDATE users
                           SET is_pro         = true,
                               pro_expires_at = NOW() + INTERVAL '30 days'
                           WHERE telegram_id = $1
		                   """, user_id)
		
		# Если пользователь хотел конкретный шаблон
		template_id = context.user_data.get('pro_template_id')
		
		if template_id:
			# Применяем шаблон
			page = await conn.fetchrow("SELECT id FROM pages WHERE user_id = $1", user_id)
			if page:
				await conn.execute(
					"UPDATE pages SET template_id = $1 WHERE id = $2",
					template_id, page['id']
				)
			
			await query.edit_message_text(
				"✅ **Поздравляем!**\n\n"
				"PRO подписка активирована!\n"
				"Выбранный шаблон применен к вашей странице.\n\n"
				"Посмотреть: /mysite",
				parse_mode='Markdown'
			)
		else:
			await query.edit_message_text(
				"✅ **Поздравляем!**\n\n"
				"PRO подписка активирована!\n"
				"Теперь вам доступны все премиум шаблоны.\n\n"
				"Выбрать шаблон: /templates",
				parse_mode='Markdown'
			)
	
	except Exception as e:
		logger.error(f"Ошибка активации PRO: {e}")
		await query.edit_message_text("❌ Ошибка активации подписки")
	finally:
		await conn.close()


# bot/handlers.py (или где у тебя лежат клавиатуры)

def main_menu_keyboard(is_pro: bool = False, is_admin: bool = False):
	"""Универсальная клавиатура главного меню (соответствует start_handler)"""
	keyboard = [
		[
			InlineKeyboardButton("📋 Моя страница", callback_data="mysite"),
			InlineKeyboardButton("🔳 QR-код", callback_data="qr")
		],
		[
			# Кнопка смены ника, которую мы добавили
			InlineKeyboardButton("🔗 Изменить адрес (URL)", callback_data="change_nick")
		],
		[
			InlineKeyboardButton("🔗 Управление ссылками", callback_data="links"),
			InlineKeyboardButton("➕ Добавить ссылку", callback_data="add_link")
		],
		[
			InlineKeyboardButton("🎨 Выбрать шаблон", callback_data="templates_menu"),
			InlineKeyboardButton("📊 Статистика", callback_data="stats")
		],
		[
			# Динамические кнопки в зависимости от PRO
			InlineKeyboardButton("💎 ВОЗМОЖНОСТИ PRO" if not is_pro else "✨ Твой PRO активен", callback_data="pro_info"),
			InlineKeyboardButton("💳 Купить подписку", callback_data="upgrade")
		],
		[
			InlineKeyboardButton("⚙️ Профиль", callback_data="profile"),
			InlineKeyboardButton("❓ Заказать шаблон", url="https://t.me/dekavetel")
		]
	]
	
	if is_admin:
		keyboard.append([InlineKeyboardButton("👑 АДМИН-ПАНЕЛЬ", callback_data="admin_list_users")])
	
	return InlineKeyboardMarkup(keyboard)


async def test_edit_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Тестовый прямой обработчик"""
	print("🔥🔥🔥 TEST_EDIT_TITLE ВЫЗВАН!", file=sys.stderr)
	print(f"🔥 Текст: {update.message.text}", file=sys.stderr)
	await update.message.reply_text(f"ТЕСТ: получил {update.message.text}")


# ===== НОВЫЙ ДИСПЕТЧЕР ДЛЯ ДОБАВЛЕНИЯ ССЫЛОК =====
async def add_link_dispatcher(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Диспетчер: выбирает старый или новый конструктор в зависимости от PRO-статуса"""
	query = update.callback_query
	user = update.effective_user
	
	conn = await get_db_connection()
	try:
		# Проверяем PRO-статус
		sub_status = await check_subscription(conn, user.id)
		is_pro = sub_status.get('active', False)
		
		if is_pro:
			# Для PRO - новый конструктор с категориями
			from bot.link_constructor import add_link_start as pro_add_link_start
			return await pro_add_link_start(update, context)
		else:
			# Для бесплатных - старый конструктор
			return await add_link_old(update, context)
	finally:
		await conn.close()


# ===== СТАРЫЙ КОНСТРУКТОР (ПЕРЕИМЕНОВАН) =====
async def add_link_old(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Старый конструктор для бесплатных пользователей (только обычные ссылки)"""
	# Весь код из твоей старой add_link_start
	query = update.callback_query
	user = update.effective_user
	conn = await get_db_connection()
	
	try:
		# --- 1. ОЧИСТКА ---
		qr_msg_id = context.user_data.get('last_qr_msg_id')
		if qr_msg_id:
			try:
				await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=qr_msg_id)
				context.user_data.pop('last_qr_msg_id', None)
			except Exception:
				pass
		
		is_back_button = query and query.data == "back_to_link_type"
		
		if query and not is_back_button:
			try:
				await query.message.delete()
				query = None
			except Exception:
				pass
		
		# --- 2. ЛОГИКА ЛИМИТОВ И СТАТУСА ---
		db_user = await get_or_create_user(conn, user.id, user.username, user.first_name)
		page = await conn.fetchrow("SELECT id FROM pages WHERE user_id = $1", db_user['id'])
		
		if not page:
			await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Сначала создайте страницу!")
			return ConversationHandler.END
		
		sub_status = await check_subscription(conn, user.id)
		is_pro = sub_status.get('active', False)
		
		current_count = await conn.fetchval(
			"SELECT COUNT(*) FROM links WHERE page_id = $1 AND is_active = true",
			page['id']
		) or 0
		
		max_limit = 50 if is_pro else 3
		remains = max_limit - current_count
		limit_indicator = "💎 PRO" if is_pro else "💡 Бесплатный"
		limit_text = f"{limit_indicator} статус: {current_count}/{max_limit} (Осталось: <b>{remains}</b>)"
		
		# --- 3. ПРОВЕРКА ЛИМИТА ---
		if remains <= 0:
			text_limit = (f"❌ <b>Лимит ссылок исчерпан!</b>\n\n{limit_text}\n\n"
			              f"Удалите старые ссылки или подключите <b>PRO-статус</b>.")
			keyboard = [[InlineKeyboardButton("💎 Узнать про PRO", callback_data="pro_info")],
			            [InlineKeyboardButton("◀️ Назад", callback_data="links")]]
			
			if query:
				await query.edit_message_text(text=text_limit, reply_markup=InlineKeyboardMarkup(keyboard),
				                              parse_mode="HTML")
			else:
				await context.bot.send_message(chat_id=update.effective_chat.id, text=text_limit,
				                               reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
			return ConversationHandler.END
		
		# --- 4. СБРОС ДАННЫХ ВВОДА ---
		for key in ['new_link_title', 'new_link_url', 'new_link_icon', 'link_type']:
			context.user_data.pop(key, None)
		
		# --- 5. ДЛЯ ОБЫЧНЫХ ЮЗЕРОВ (всегда standard) ---
		context.user_data['link_type'] = 'standard'
		text_step1 = (
			f"{limit_text}\n"
			f"────────────────────\n\n"
			"📝 <b>Шаг 1 из 3: Введите название ссылки</b>\n\n"
			"Например: <i>Мой Instagram</i>"
		)
		
		keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel")]]
		
		if query:
			msg = await query.edit_message_text(text=text_step1, reply_markup=InlineKeyboardMarkup(keyboard),
			                                    parse_mode="HTML")
		else:
			msg = await context.bot.send_message(chat_id=update.effective_chat.id, text=text_step1,
			                                     reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
		
		context.user_data['last_menu_msg_id'] = msg.message_id
		return ADD_LINK_TITLE
	
	except Exception as e:
		logger.error(f"Error in add_link_old: {e}", exc_info=True)
		return ConversationHandler.END
	finally:
		await conn.close()
