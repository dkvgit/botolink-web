# # Файл: D:\aRabota\TelegaBoom\030_mylinkspace\admin_handlers.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.utils import get_db_connection, log_error
from core import config
import logging

logger = logging.getLogger("BotoLinkPro")

def is_admin(user_id: int) -> bool:
    # # Используем # для Python комментариев
    return user_id in config.ADMIN_IDS


async def admin_list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # # Список ВСЕХ пользователей с кнопками действий
    query = update.callback_query
    user_id = update.effective_user.id

    if not is_admin(user_id):
        if query:
            await query.answer("У вас нет прав!", show_alert=True)
        return

    if query:
        await query.answer()

    conn = await get_db_connection()
    try:
        # # Запрос через asyncpg
        users = await conn.fetch("""
            SELECT id, telegram_id, username, first_name, is_pro, is_admin
            FROM users
            ORDER BY id DESC
        """)

        text_header = f"👥 <b>Все пользователи ({len(users)}):</b>\n\n👇 Нажмите на пользователя для управления:"

        if not users:
            msg_text = "📭 Нет пользователей"
            if query: await query.edit_message_text(msg_text)
            else: await update.message.reply_text(msg_text)
            return

        keyboard = []
        for user in users:
            icon = "👑" if user['is_admin'] else "💎" if user['is_pro'] else "👤"
            raw_name = user['first_name'] or "No Name"
            name = raw_name[:15] + "..." if len(raw_name) > 15 else raw_name
            username = f"@{user['username']}" if user['username'] else "no username"
            btn_text = f"{icon} {name} | {username} | ID: {user['telegram_id']}"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"admin_user_{user['telegram_id']}")])

        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="start")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        if query:
            try:
                await query.edit_message_text(text_header, reply_markup=reply_markup, parse_mode='HTML')
            except Exception:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=text_header, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await update.message.reply_text(text_header, reply_markup=reply_markup, parse_mode='HTML')

    except Exception as e:
        await log_error(e, "в admin_list_users")
    finally:
        await conn.close()


async def admin_user_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # # Детальная информация о пользователе с кнопками действий
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        return

    tg_id = int(query.data.replace("admin_user_", ""))
    conn = await get_db_connection()

    try:
        # # Тянем инфу + счетчики страниц и ссылок
        user_data = await conn.fetchrow("""
            SELECT u.*,
                   (SELECT COUNT(id) FROM pages WHERE user_id = u.id) as pages_count,
                   (SELECT COUNT(id) FROM links WHERE page_id IN (SELECT id FROM pages WHERE user_id = u.id)) as links_count,
                   EXTRACT(DAY FROM (pro_expires_at - NOW())) as days_left
            FROM users u
            WHERE u.telegram_id = $1
        """, tg_id)

        if not user_data:
            await query.edit_message_text("❌ Пользователь не найден")
            return

        # # Сохраняем в контекст для последующих действий
        context.user_data['selected_user'] = tg_id
        context.user_data['selected_user_data'] = {
            'id': user_data['id'],
            'telegram_id': user_data['telegram_id'],
            'first_name': user_data['first_name']
        }

        pro_status = "💎 PRO" if user_data['is_pro'] else "🆓 Free"
        days_left_str = f" (осталось {int(user_data['days_left'])} дн.)" if user_data['is_pro'] and user_data['days_left'] else ""
        admin_status = "👑 Админ" if user_data['is_admin'] else ""
        reg_date = user_data['created_at'].strftime('%d.%m.%Y %H:%M') if user_data['created_at'] else "неизвестно"
        custom_username = user_data.get('custom_username') or "не установлено"

        msg = (
            f"<b>Информация о пользователе</b>\n\n"
            f"🆔 <b>Telegram ID:</b> <code>{user_data['telegram_id']}</code>\n"
            f"👤 <b>Имя:</b> {user_data['first_name']}\n"
            f"📛 <b>Username TG:</b> @{user_data['username'] or 'нет'}\n"
            f"🔤 <b>Имя страницы:</b> <code>{custom_username}</code>\n"
            f"📅 <b>Зарегистрирован:</b> {reg_date}\n"
            f"📊 <b>Статус:</b> {pro_status}{days_left_str} {admin_status}\n"
            f"📑 <b>Страниц:</b> {user_data['pages_count'] or 0}\n"
            f"🔗 <b>Ссылок:</b> {user_data['links_count'] or 0}\n"
        )

        if user_data['is_pro']:
            if user_data['pro_expires_at']:
                msg += f"⏳ <b>PRO до:</b> {user_data['pro_expires_at'].strftime('%d.%m.%Y')}\n"
            if user_data['subscribe_until']:
                msg += f"📅 <b>Подписка до:</b> {user_data['subscribe_until'].strftime('%d.%m.%Y')}\n"

        keyboard = [
            [InlineKeyboardButton("💎 Выдать PRO", callback_data="admin_give_pro_menu")],
            [InlineKeyboardButton("🚫 Забрать PRO", callback_data="admin_take_pro_now")],
            [InlineKeyboardButton("🗑 Удалить пользователя", callback_data="admin_delete_user_now")],
            [InlineKeyboardButton("◀️ Назад к списку", callback_data="admin_list_users")]
        ]

        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

    except Exception as e:
        await log_error(e, "в admin_user_detail")
    finally:
        await conn.close()


async def admin_give_pro_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # # Меню выбора срока PRO
    query = update.callback_query
    await query.answer()

    u_data = context.user_data.get('selected_user_data')
    if not u_data:
        await query.edit_message_text("❌ Выберите пользователя сначала")
        return

    keyboard = [
        [InlineKeyboardButton("📅 30 дней", callback_data="admin_give_pro_30")],
        [InlineKeyboardButton("📅 90 дней", callback_data="admin_give_pro_90")],
        [InlineKeyboardButton("📅 365 дней", callback_data="admin_give_pro_365")],
        [InlineKeyboardButton("◀️ Назад", callback_data=f"admin_user_{u_data['telegram_id']}")]
    ]

    await query.edit_message_text(
        f"💎 <b>Выдача PRO</b>\n\nПользователь: {u_data['first_name']}\nID: <code>{u_data['telegram_id']}</code>\n\nВыберите срок:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def admin_give_pro_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # # Выполнение выдачи PRO
    query = update.callback_query
    await query.answer()

    days = 30
    if "90" in query.data: days = 90
    elif "365" in query.data: days = 365

    u_data = context.user_data.get('selected_user_data')
    if not u_data: return

    conn = await get_db_connection()
    try:
        await conn.execute("""
            UPDATE users
            SET is_pro = true,
                pro_expires_at = NOW() + $1 * interval '1 day',
                subscribe_until = NOW() + $1 * interval '1 day'
            WHERE telegram_id = $2
        """, days, u_data['telegram_id'])

        await query.edit_message_text(
            f"✅ <b>PRO выдан на {days} дней!</b>\n\nЮзер: {u_data['first_name']}\nID: <code>{u_data['telegram_id']}</code>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ К пользователю", callback_data=f"admin_user_{u_data['telegram_id']}")]]),
            parse_mode='HTML'
        )
    finally:
        await conn.close()


async def admin_take_pro_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # # Забрать PRO
    query = update.callback_query
    await query.answer()
    u_data = context.user_data.get('selected_user_data')
    if not u_data: return

    conn = await get_db_connection()
    try:
        await conn.execute("UPDATE users SET is_pro = false, pro_expires_at = NULL, subscribe_until = NULL WHERE telegram_id = $1", u_data['telegram_id'])
        await query.edit_message_text(
            f"🚫 <b>PRO отозван!</b>\n\nПользователь: {u_data['first_name']}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ К пользователю", callback_data=f"admin_user_{u_data['telegram_id']}")]]),
            parse_mode='HTML'
        )
    finally:
        await conn.close()


async def admin_delete_user_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # # Удаление пользователя
    query = update.callback_query
    await query.answer()
    u_data = context.user_data.get('selected_user_data')
    if not u_data: return

    conn = await get_db_connection()
    try:
        # # Каскадное удаление вручную
        await conn.execute("DELETE FROM links WHERE page_id IN (SELECT id FROM pages WHERE user_id = $1)", u_data['id'])
        await conn.execute("DELETE FROM pages WHERE user_id = $1", u_data['id'])
        await conn.execute("DELETE FROM users WHERE id = $1", u_data['id'])

        context.user_data.pop('selected_user', None)
        context.user_data.pop('selected_user_data', None)

        await query.edit_message_text(
            f"✅ <b>Пользователь {u_data['first_name']} удален!</b>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ В админ-панель", callback_data="admin_list_users")]]),
            parse_mode='HTML'
        )
    finally:
        await conn.close()


async def check_is_admin(conn, tg_id: int) -> bool:
    # # Проверка прав: конфиг + база
    if tg_id in config.ADMIN_IDS:
        return True
    row = await conn.fetchrow("SELECT is_admin FROM users WHERE telegram_id = $1", tg_id)
    return bool(row and row['is_admin'] is True)