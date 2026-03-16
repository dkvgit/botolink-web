# bot/handlers/templates.py
import logging

from bot.handlers import get_db_connection, check_subscription
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def templates_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Обработчик команды /templates - показать список шаблонов"""
	user_id = update.effective_user.id
	
	conn = await get_db_connection()
	try:
		# Получаем все активные шаблоны
		templates = await conn.fetch("""
                                     SELECT id, name, description, is_pro
                                     FROM templates
                                     WHERE is_active = true
                                     ORDER BY sort_order
		                             """)
		
		# Проверяем подписку пользователя
		is_pro_user = await check_subscription(user_id)
		
		# Создаем клавиатуру
		keyboard = []
		for t in templates:
			if t['is_pro'] and not is_pro_user:
				# PRO шаблон для обычного пользователя - показываем кнопку разблокировки
				button_text = f"⭐ {t['name']} (PRO)"
				callback_data = f"unlock_pro_{t['id']}"
			else:
				# Доступный шаблон (бесплатный или PRO для подписчика)
				button_text = f"✅ {t['name']}"
				if t['is_pro']:
					button_text = f"👑 {t['name']} (PRO)"
				callback_data = f"select_template_{t['id']}"
			
			keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
		
		# Добавляем кнопку "Назад"
		keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="profile")])
		
		reply_markup = InlineKeyboardMarkup(keyboard)
		
		# Статистика
		free_count = len([t for t in templates if not t['is_pro']])
		pro_count = len([t for t in templates if t['is_pro']])
		
		await update.message.reply_text(
			f"🎨 **Выбор шаблона страницы**\n\n"
			f"Доступно шаблонов: {len(templates)}\n"
			f"• Бесплатных: {free_count}\n"
			f"• PRO: {pro_count}\n\n"
			f"Выберите шаблон:",
			parse_mode='Markdown',
			reply_markup=reply_markup
		)
	
	except Exception as e:
		logger.error(f"Ошибка при показе шаблонов: {e}")
		await update.message.reply_text("❌ Ошибка при загрузке шаблонов")
	finally:
		await conn.close()


async def select_template_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Обработчик выбора шаблона"""
	query = update.callback_query
	await query.answer()
	
	template_id = int(query.data.split('_')[2])
	user_id = update.effective_user.id
	
	conn = await get_db_connection()
	try:
		# Получаем информацию о шаблоне
		template = await conn.fetchrow(
			"SELECT name, is_pro FROM templates WHERE id = $1",
			template_id
		)
		
		if not template:
			await query.edit_message_text("❌ Шаблон не найден")
			return
		
		# Получаем страницу пользователя
		page = await conn.fetchrow(
			"SELECT id FROM pages WHERE user_id = $1",
			user_id
		)
		
		if not page:
			await query.edit_message_text("❌ Страница не найдена")
			return
		
		# Обновляем шаблон страницы
		await conn.execute(
			"UPDATE pages SET template_id = $1 WHERE id = $2",
			template_id, page['id']
		)
		
		pro_emoji = "👑 " if template['is_pro'] else ""
		await query.edit_message_text(
			f"✅ Шаблон успешно изменен!\n\n"
			f"{pro_emoji}**{template['name']}**\n\n"
			f"Ваша страница: /mysite",
			parse_mode='Markdown'
		)
	
	except Exception as e:
		logger.error(f"Ошибка при выборе шаблона: {e}")
		await query.edit_message_text("❌ Ошибка при выборе шаблона")
	finally:
		await conn.close()


async def unlock_pro_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Обработчик кнопки разблокировки PRO шаблона"""
	query = update.callback_query
	await query.answer()
	
	template_id = int(query.data.split('_')[2])
	
	keyboard = [
		[InlineKeyboardButton("💳 Купить PRO на месяц", callback_data="buy_pro_month")],
		[InlineKeyboardButton("💳 Купить PRO на год (скидка 20%)", callback_data="buy_pro_year")],
		[InlineKeyboardButton("◀️ Назад к шаблонам", callback_data="back_to_templates")]
	]
	reply_markup = InlineKeyboardMarkup(keyboard)
	
	await query.edit_message_text(
		"⭐ **PRO шаблоны**\n\n"
		"Этот шаблон доступен только для PRO подписчиков.\n\n"
		"**Преимущества PRO:**\n"
		"• Все 7 премиум шаблонов\n"
		"• Приоритетная поддержка\n"
		"• Больше настроек\n\n"
		"Выберите тариф:",
		parse_mode='Markdown',
		reply_markup=reply_markup
	)
