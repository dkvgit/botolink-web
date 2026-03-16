import logging

from bot.utils import get_db_connection, get_or_create_user
from core.config import APP_URL, PRO_LINKS_LIMIT, FREE_LINKS_LIMIT
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

logger = logging.getLogger(__name__)


async def add_link_icon(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Финальное сохранение после выбора иконки"""
	query = update.callback_query
	await query.answer()
	
	icon = query.data.replace("icon_", "")
	
	title = context.user_data.get('link_title', 'Без названия')
	url = context.user_data.get('link_url', '')
	link_type = context.user_data.get('link_type', 'standard')
	category = context.user_data.get('link_category', 'other')
	
	conn = await get_db_connection()
	try:
		user_id = update.effective_user.id
		user_db_id = await conn.fetchval("SELECT id FROM users WHERE telegram_id = $1", user_id)
		page = await conn.fetchrow("SELECT id, username FROM pages WHERE user_id = $1", user_db_id)
		
		max_sort = await conn.fetchval(
			"SELECT COALESCE(MAX(sort_order), 0) FROM links WHERE page_id = $1",
			page['id']
		)
		
		await conn.execute("""
                           INSERT INTO links (page_id, title, url, icon, link_type,
                                              pay_details, sort_order, is_active, click_count, created_at)
                           VALUES ($1, $2, $3, $4, $5, $6, $7, true, 0, NOW())
		                   """, page['id'], title, url, icon, link_type, None, max_sort + 1)
		
		new_count = await conn.fetchval(
			"SELECT COUNT(*) FROM links WHERE page_id = $1 AND is_active = true",
			page['id']
		) or 0
		
		is_pro = await conn.fetchval("SELECT is_pro FROM users WHERE id = $1", user_db_id) or False
		limit = PRO_LINKS_LIMIT if is_pro else FREE_LINKS_LIMIT
		remaining = limit - new_count
		
		msg = f"✅ **Ссылка успешно добавлена!**\n\n"
		msg += f"📌 **Название:** {title}\n"
		msg += f"📊 **Использовано:** {new_count} из {limit}\n"
		msg += f"📈 **Осталось ссылок:** {remaining}"
		
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
		
		for key in ['link_category', 'link_type', 'link_info', 'link_title',
		            'link_url', 'link_description', 'finance_subtype', 'finance_tab']:
			context.user_data.pop(key, None)
	
	except Exception as e:
		logger.error(f"Ошибка сохранения: {e}", exc_info=True)
		await query.edit_message_text("❌ Ошибка при сохранении. Попробуй позже.")
	finally:
		await conn.close()
	
	return ConversationHandler.END
