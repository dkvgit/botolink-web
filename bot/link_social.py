# D:\aRabota\TelegaBoom\030_botolinkpro\bot\link_social.py

import json
import logging

from bot.handlers import main_menu_keyboard
from bot.link_constructor import SOCIAL_PARSERS
from bot.states import WAIT_SOCIAL_STEP1, WAIT_SOCIAL_URL, WAIT_TELEGRAM_STEP3, WAIT_TELEGRAM_STEP2, WAIT_TELEGRAM_STEP1
# Импорты из других модулей бота
from bot.utils import get_db_connection
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

# Настройка логирования
logger = logging.getLogger(__name__)

# ============================================
# СЛОВАРЬ С НАСТРОЙКАМИ ДЛЯ КАЖДОГО ТИПА СОЦСЕТЕЙ
# ============================================
SOCIAL_CONFIG = {
	'youtube': {
		'name': 'YouTube',
		'steps': 2,  # 2 шага: название канала → URL
		'step1_prompt': 'название канала',
		'step1_example': 'Иван Иванов / @durov / Мой блог',
		'step2_prompt': 'ссылку на канал',
		'step2_example': 'https://youtube.com/@username',
		'field_name': 'channel_name'  # как сохранять в pay_details
	},
	'telegram': {
		'name': 'Telegram',
		'steps': 3,
		'step1_prompt': 'выберите тип',
		'step1_example': '1, 2 или 3',
		'step2_prompt': 'username или ссылку',
		'step2_example': '@durov / https://t.me/durov',
		'step3_prompt': 'название (можно пропустить)',
		'step3_example': 'Мой канал',
		'field_name': 'telegram_data'
	},
	'tiktok': {
		'name': 'TikTok',
		'steps': 2,
		'step1_prompt': 'никнейм',
		'step1_example': '@username / имя пользователя',
		'step2_prompt': 'ссылку на TikTok',
		'step2_example': 'https://tiktok.com/@username',
		'field_name': 'username'
	},
	'vk': {
		'name': 'VK',
		'steps': 2,
		'step1_prompt': 'ID или короткое имя',
		'step1_example': 'id123456 / durov',
		'step2_prompt': 'ссылку на VK',
		'step2_example': 'https://vk.com/durov',
		'field_name': 'page_id'
	},
	'instagram': {
		'name': 'Instagram',
		'steps': 2,
		'step1_prompt': 'username',
		'step1_example': '@username / имя профиля',
		'step2_prompt': 'ссылку на Instagram',
		'step2_example': 'https://instagram.com/username',
		'field_name': 'username'
	},
	'ok': {
		'name': 'Одноклассники',
		'steps': 2,
		'step1_prompt': 'ID или имя',
		'step1_example': 'profile/123456 / @username',
		'step2_prompt': 'ссылку на OK',
		'step2_example': 'https://ok.ru/profile/123456',
		'field_name': 'profile_id'
	},
	'facebook': {
		'name': 'Facebook',
		'steps': 2,
		'step1_prompt': 'имя страницы или ID',
		'step1_example': 'durov / profile.php?id=123',
		'step2_prompt': 'ссылку на Facebook',
		'step2_example': 'https://facebook.com/durov',
		'field_name': 'page_name'
	},
	'twitter': {
		'name': 'Twitter/X',
		'steps': 2,
		'step1_prompt': 'username',
		'step1_example': '@username / имя профиля',
		'step2_prompt': 'ссылку на Twitter',
		'step2_example': 'https://twitter.com/username',
		'field_name': 'username'
	},
	# Для остальных соцсетей можно сделать 1 шаг (сразу ссылку)
	'twitch': {'name': 'Twitch', 'steps': 1, 'prompt': 'ссылку на канал', 'example': 'https://twitch.tv/username'},
	'rutube': {'name': 'Rutube', 'steps': 1, 'prompt': 'ссылку на канал', 'example': 'https://rutube.ru/channel/'},
	'dzen': {'name': 'Дзен', 'steps': 1, 'prompt': 'ссылку на канал', 'example': 'https://dzen.ru/id'},
	'snapchat': {'name': 'Snapchat', 'steps': 1, 'prompt': 'ссылку на профиль', 'example': 'https://snapchat.com/add/'},
	'likee': {'name': 'Likee', 'steps': 1, 'prompt': 'ссылку на профиль', 'example': 'https://likee.com/@'},
	'threads': {'name': 'Threads', 'steps': 1, 'prompt': 'ссылку на профиль', 'example': 'https://threads.net/@'},
}


async def start_social_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Начало добавления соцсети (вызывается из cat_social)"""
	query = update.callback_query
	await query.answer()
	
	print(f"🔥🔥🔥 start_social_add ВЫЗВАНА с data: {update.callback_query.data}")
	
	# Получаем данные из callback (например "type_youtube")
	data = query.data
	
	# ЕСЛИ ЭТО ПРОСТО ВОЗВРАТ В МЕНЮ СОЦСЕТЕЙ
	if data == "cat_social":
		# Показываем меню выбора соцсетей
		from bot.handlers import show_categories
		return await show_categories(update, context)
	
	if data.startswith('type_'):
		link_type = data.replace('type_', '')  # type_youtube → youtube
	elif data.startswith('social_'):
		link_type = data.replace('social_', '')
	else:
		link_type = context.user_data.get('temp_link_type')
	
	if not link_type:
		await query.edit_message_text("❌ Ошибка: тип не указан")
		return ConversationHandler.END
	
	# Сохраняем в user_data
	context.user_data['link_category'] = 'social'
	context.user_data['link_type'] = link_type
	context.user_data['social_step'] = 1
	
	# Получаем конфиг для этого типа
	config = SOCIAL_CONFIG.get(link_type, {
		'name': link_type.capitalize(),
		'steps': 1,
		'prompt': 'ссылку',
		'example': 'https://...'
	})
	
	context.user_data['social_config'] = config
	
	# Формируем текст и клавиатуру в зависимости от количества шагов
	if config['steps'] == 2:
		text = (
			f"📱 **{config['name']}**\n\n"
			f"✏️ **ШАГ 1 из 2:** Введите {config['step1_prompt']}\n\n"
			f"📌 Например:\n"
			f"• `{config['step1_example']}`\n\n"
			f"👇 Жду ваш ввод в поле чата..."
		)
		keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="cat_social")]]
		next_state = WAIT_SOCIAL_STEP1
	
	elif config['steps'] == 3:
		# Для Telegram с 3 шагами - КНОПКИ
		text = (
			f"📱 **{config['name']}**\n\n"
			f"✏️ **ШАГ 1 из 3:** Выберите тип:"
		)
		keyboard = [
			[
				InlineKeyboardButton("👤 Личный аккаунт", callback_data="telegram_type_personal"),
				InlineKeyboardButton("👥 Группа/чат", callback_data="telegram_type_group")
			],
			[
				InlineKeyboardButton("📢 Канал", callback_data="telegram_type_channel")
			],
			[InlineKeyboardButton("◀️ Назад", callback_data="cat_social")]
		]
		next_state = WAIT_TELEGRAM_STEP1
	
	else:
		# Для соцсетей с 1 шагом
		text = (
			f"📱 **{config['name']}**\n\n"
			f"✏️ Введите {config['prompt']}\n\n"
			f"📌 Например:\n"
			f"• `{config['example']}`\n\n"
			f"👇 Жду ваш ввод в поле чата..."
		)
		keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="cat_social")]]
		next_state = WAIT_SOCIAL_URL
	
	# Отправляем сообщение с клавиатурой
	await query.edit_message_text(
		text,
		reply_markup=InlineKeyboardMarkup(keyboard),
		parse_mode='Markdown'
	)
	
	return next_state


async def telegram_type_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Обработка выбора типа Telegram"""
	query = update.callback_query
	await query.answer()
	
	type_map = {
		'telegram_type_personal': 'personal',
		'telegram_type_group': 'group',
		'telegram_type_channel': 'channel'
	}
	
	tg_type = type_map[query.data]
	context.user_data['telegram_type'] = tg_type
	
	prompts = {
		'personal': "Введите username (например: @durov или просто durov):",
		'group': "Введите ссылку на группу или чат:\n• https://t.me/chatname\n• https://t.me/joinchat/abc123\n• @chatname",
		'channel': "Введите ссылку на канал:\n• https://t.me/channelname\n• @channelname\n• просто channelname"
	}
	
	await query.edit_message_text(
		f"📱 **Telegram | {tg_type.capitalize()}**\n\n"
		f"{prompts[tg_type]}",
		reply_markup=InlineKeyboardMarkup([
			[InlineKeyboardButton("◀️ Назад к выбору типа", callback_data="back_telegram_type")]
		]),
		parse_mode='Markdown'
	)
	
	return WAIT_TELEGRAM_STEP2


async def process_social_step1(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Обработка первого шага для соцсетей (например название канала)"""
	user_input = update.message.text.strip()
	
	config = context.user_data.get('social_config', {})
	link_type = context.user_data.get('link_type')
	
	# Сохраняем первый шаг
	field_name = config.get('field_name', 'step1_value')
	if 'social_data' not in context.user_data:
		context.user_data['social_data'] = {}
	
	context.user_data['social_data'][field_name] = user_input
	
	# Переходим ко второму шагу - запрос URL
	text = (
		f"📱 **{config['name']}**\n\n"
		f"✅ {config['step1_prompt'].capitalize()}: **{user_input}**\n\n"
		f"✏️ **ШАГ 2 из 2:** Теперь введите {config['step2_prompt']}\n\n"
		f"📌 Например:\n"
		f"• `{config['step2_example']}`\n\n"
		f"👇 Введите ссылку:"
	)
	
	keyboard = [
		[InlineKeyboardButton("◀️ Назад", callback_data="back_social_step1")],
		[InlineKeyboardButton("🏠 В начало", callback_data="start_over")]
	]
	
	await update.message.reply_text(
		text,
		reply_markup=InlineKeyboardMarkup(keyboard),
		parse_mode='Markdown'
	)
	
	return WAIT_SOCIAL_URL


def is_valid_social_url(url: str, link_type: str, original_input: str) -> bool:
	"""Проверяет, похожа ли ссылка на настоящую соцсеть"""
	
	# Слишком короткий ввод
	if len(original_input) < 3:
		return False
	
	# Проверка для YouTube
	if link_type == 'youtube':
		# Допустимые форматы для YouTube
		valid_patterns = [
			'youtube.com/@',
			'youtube.com/channel/',
			'youtube.com/user/',
			'youtu.be/',
			'/@'
		]
		# Проверяем что это не ссылка на видео
		if 'watch?v=' in url or '/shorts/' in url:
			return False
		# Если есть хотя бы один из допустимых паттернов
		for pattern in valid_patterns:
			if pattern in url:
				return True
		# Если это просто @username или username
		if original_input.startswith('@') or (
				'.' not in original_input and '/' not in original_input and len(original_input) > 2):
			return True
		return False
	
	# Проверка для Telegram
	if link_type == 'telegram':
		valid_patterns = ['t.me/', 'telegram.org/']
		for pattern in valid_patterns:
			if pattern in url:
				return True
		if original_input.startswith('@') or (
				'.' not in original_input and '/' not in original_input and len(original_input) > 2):
			return True
		return False
	
	# Проверка для Instagram
	if link_type == 'instagram':
		if 'instagram.com/' in url:
			return True
		if original_input.startswith('@') or (
				'.' not in original_input and '/' not in original_input and len(original_input) > 2):
			return True
		return False
	
	# Проверка для TikTok
	if link_type == 'tiktok':
		if 'tiktok.com/' in url:
			return True
		if original_input.startswith('@') or (
				'.' not in original_input and '/' not in original_input and len(original_input) > 2):
			return True
		return False
	
	# Проверка для VK
	if link_type == 'vk':
		valid_patterns = ['vk.com/', 'vk.ru/']
		for pattern in valid_patterns:
			if pattern in url:
				return True
		if original_input.startswith(('id', 'public', 'club')) or (
				'.' not in original_input and '/' not in original_input and len(original_input) > 2):
			return True
		return False
	
	# Для остальных соцсетей - базовая проверка
	if any(domain in url for domain in ['.com', '.ru', '.org', '.net', '.io']):
		return True
	if original_input.startswith('@') or (
			'.' not in original_input and '/' not in original_input and len(original_input) > 2):
		return True
	
	# Если ссылка начинается с http и содержит точку
	if url.startswith(('http://', 'https://')) and '.' in url:
		return True
	
	# По умолчанию отклоняем сомнительные вводы
	if len(original_input) > 5 and ' ' not in original_input:
		return True
	
	return False


async def process_social_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Обработка URL для соцсети и сохранение в БД"""
	user_input = update.message.text.strip()
	
	link_type = context.user_data.get('link_type')
	
	# Выбираем парсер в зависимости от типа соцсети
	parser = SOCIAL_PARSERS.get(link_type)
	
	if parser:
		# Используем специальный парсер
		parsed = parser(user_input)
		url = parsed['url']
		display_url = parsed.get('display', url)
		
		# ВАЛИДАЦИЯ: проверяем что ссылка похожа на настоящую
		if not is_valid_social_url(url, link_type, user_input):
			# Отправляем сообщение об ошибке с просьбой ввести корректные данные
			await update.message.reply_text(
				f"❌ Введенные данные не похожи на правильную ссылку для {link_type}.\n\n"
				f"Пожалуйста, введите корректную ссылку или имя пользователя:\n"
				f"• Полная ссылка: https://...\n"
				f"• Имя пользователя: @username\n"
				f"• Просто username",
				reply_markup=InlineKeyboardMarkup([
					[InlineKeyboardButton("◀️ Назад к вводу", callback_data="back_social_step1")]
				])
			)
			return WAIT_SOCIAL_URL
	else:
		# Базовый парсер (как было раньше)
		url = user_input
		if not url.startswith(('http://', 'https://')):
			if url.startswith('@'):
				username = url.replace('@', '')
				if link_type == 'telegram':
					url = f"https://t.me/{username}"
				elif link_type == 'youtube':
					url = f"https://youtube.com/@{username}"
				else:
					url = f"https://{url}"
			elif '.' not in url and link_type in ['instagram', 'twitter', 'tiktok']:
				username = url.replace('@', '')
				domain = {
					'instagram': 'instagram.com',
					'twitter': 'twitter.com',
					'tiktok': 'tiktok.com',
					'youtube': 'youtube.com/@',
					'telegram': 't.me'
				}.get(link_type, '')
				
				if link_type == 'youtube':
					url = f"https://youtube.com/@{username}"
				elif domain:
					url = f"https://{domain}/{username}"
				else:
					url = f"https://{url}"
			else:
				url = f"https://{url}"
		display_url = url
		
		# Базовая валидация для случаев без парсера
		if not is_valid_social_url(url, link_type, user_input):
			await update.message.reply_text(
				f"❌ Введенные данные не похожи на правильную ссылку для {link_type}.\n\n"
				f"Пожалуйста, введите корректную ссылку или имя пользователя:",
				reply_markup=InlineKeyboardMarkup([
					[InlineKeyboardButton("◀️ Назад к вводу", callback_data="back_social_step1")]
				])
			)
			return WAIT_SOCIAL_URL
	
	# Специальная проверка для YouTube - не пропускать ссылки на видео
	if link_type == 'youtube':
		if 'watch?v=' in url or 'youtu.be/' in url or '/shorts/' in url:
			await update.message.reply_text(
				f"❌ Это ссылка на ВИДЕО, а нам нужна ссылка на КАНАЛ.\n\n"
				f"Пожалуйста, введите ссылку на канал YouTube:\n"
				f"• `https://youtube.com/@username`\n"
				f"• `@username`\n"
				f"• просто `username`",
				reply_markup=InlineKeyboardMarkup([
					[InlineKeyboardButton("◀️ Назад к вводу", callback_data="back_social_step1")]
				])
			)
			return WAIT_SOCIAL_URL
	
	# Собираем pay_details
	pay_details = {}
	social_data = context.user_data.get('social_data', {})
	
	# Добавляем все собранные данные в pay_details
	for key, value in social_data.items():
		pay_details[key] = value
	
	# Добавляем информацию из парсера если есть
	if parser and 'value' in parsed:
		pay_details['parsed_value'] = parsed['value']
		pay_details['input_type'] = parsed['type']
	
	# Если есть конфиг с field_name, но данных нет, добавляем пустое
	config = context.user_data.get('social_config', {})
	if config.get('steps') == 2 and config.get('field_name'):
		field_name = config['field_name']
		if field_name not in pay_details:
			pay_details[field_name] = ''
	
	# Название для ссылки (title) - ИСПРАВЛЕНО
	if link_type == 'youtube':
		# Для YouTube всегда ставим "YouTube" как название
		title = "YouTube"
	# Название канала уже в pay_details, его не пихаем в title
	else:
		# Для других соцсетей используем название соцсети
		base_name = config.get('name', link_type.capitalize())
		title = base_name
	# Если есть дополнительные данные, сохраняем их только в pay_details
	
	# ========== ИСПРАВЛЕННЫЙ БЛОК СОХРАНЕНИЯ В БД ==========
	# Сохраняем в БД - ИСПРАВЛЕНО (ДОБАВЛЯЕМ await)
	conn = await get_db_connection()  # ОБЯЗАТЕЛЬНО await!
	try:
		# Для asyncpg используем execute без курсора
		# Получаем категорию из контекста (если нет - social)
		category = context.user_data.get('link_category', 'social')
		
		await conn.execute("""
                           INSERT INTO links
                           (page_id, title, url, icon, sort_order, is_active, created_at, link_type, pay_details,
                            category)
                           VALUES ($1, $2, $3, $4,
                                   COALESCE((SELECT MAX(sort_order) + 1 FROM links WHERE page_id = $5), 1),
                                   true, NOW(), $6, $7, $8 ← теперь $8 для категории)
		                   """,
		                   context.user_data['page_id'],
		                   title,
		                   url,
		                   link_type,
		                   context.user_data['page_id'],
		                   link_type,
		                   json.dumps(pay_details, ensure_ascii=False) if pay_details else None,
		                   category
		                   )
		
		# Формируем сообщение об успехе
		success_text = f"✅ {config.get('name', 'Соцсеть')} добавлена!\n\n"
		success_text += f"📌 Название: {title}\n"
		success_text += f"🔗 Ссылка: {url}\n"
		
		if parser and 'display' in parsed:
			success_text += f"📋 Распознано: {parsed['display']}\n"
		
		# Показываем только название канала, без служебной информации
		if pay_details.get('channel_name'):
			success_text += f"📋 Название канала: {pay_details['channel_name']}\n"
		
		# Добавляем ссылку на страницу где можно посмотреть
		from core.config import APP_URL
		base_url = APP_URL.rstrip('/')
		page_username = context.user_data.get('page_username')
		
		if page_username:
			page_url = f"{base_url}/{page_username}"
			success_text += f"\n👀 Посмотреть на странице:\n{page_url}\n"
		else:
			# Если нет username, пробуем получить из базы
			try:
				user_id = update.effective_user.id
				page = await conn.fetchrow(
					"""
                    SELECT p.id, p.username
                    FROM pages p
                             JOIN users u ON u.id = p.user_id
                    WHERE u.telegram_id = $1
					""",
					user_id
				)
				if page:
					page_username = page['username']
					page_url = f"{base_url}/{page_username}"
					success_text += f"\n👀 Посмотреть на странице:\n{page_url}\n"
					# Сохраняем для будущих использований
					context.user_data['page_username'] = page_username
			except Exception as e:
				logger.error(f"Ошибка при получении страницы: {e}")
		
		await update.message.reply_text(
			success_text,
			reply_markup=main_menu_keyboard()
		)
		
		# Очищаем временные данные
		context.user_data.pop('social_data', None)
		context.user_data.pop('social_config', None)
		context.user_data.pop('social_step', None)
		
		return ConversationHandler.END
	
	except Exception as e:
		logger.error(f"Ошибка при сохранении соцсети: {e}")
		await update.message.reply_text(f"❌ Ошибка при сохранении: {e}")
		return ConversationHandler.END
	finally:
		await conn.close()  # тоже await


# ========== КОНЕЦ ИСПРАВЛЕННОГО БЛОКА ==========


async def back_to_social_step1(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Возврат к первому шагу"""
	query = update.callback_query
	await query.answer()
	
	config = context.user_data.get('social_config', {})
	
	text = (
		f"📱 **{config['name']}**\n\n"
		f"✏️ **ШАГ 1 из 2:** Введите {config['step1_prompt']}\n\n"
		f"📌 Например:\n"
		f"• `{config['step1_example']}`\n\n"
		f"👇 Жду ваш ввод в поле чата..."
	)
	
	keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="cat_social")]]
	
	await query.edit_message_text(
		text,
		reply_markup=InlineKeyboardMarkup(keyboard),
		parse_mode='Markdown'
	)
	
	return WAIT_SOCIAL_STEP1


async def back_to_telegram_step1(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Возврат к первому шагу Telegram (выбор типа)"""
	query = update.callback_query
	await query.answer()
	
	# Очищаем сохраненные данные Telegram
	context.user_data.pop('telegram_type', None)
	context.user_data.pop('telegram_parsed', None)
	
	# Показываем первый шаг заново
	text = (
		"📱 **Telegram**\n\n"
		"Что вы хотите добавить?\n\n"
		"1️⃣ Личный аккаунт / бот\n"
		"2️⃣ Группа / чат\n"
		"3️⃣ Канал\n\n"
		"👇 Введите цифру (1, 2 или 3):"
	)
	
	keyboard = [[InlineKeyboardButton("◀️ Назад к соцсетям", callback_data="cat_social")]]
	
	await query.edit_message_text(
		text,
		reply_markup=InlineKeyboardMarkup(keyboard),
		parse_mode='Markdown'
	)
	
	return WAIT_TELEGRAM_STEP1


async def process_telegram_step1(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""ШАГ 1 для Telegram: выбор типа (личный, группа, канал)"""
	user_input = update.message.text.strip()
	
	# Проверяем что ввел пользователь (1, 2 или 3)
	if user_input not in ['1', '2', '3']:
		await update.message.reply_text(
			"❌ Введите 1, 2 или 3:\n\n"
			"1️⃣ Личный аккаунт / бот\n"
			"2️⃣ Группа / чат\n"
			"3️⃣ Канал"
		)
		return WAIT_SOCIAL_STEP1
	
	# Сохраняем выбор
	type_map = {
		'1': 'personal',
		'2': 'group',
		'3': 'channel'
	}
	context.user_data['telegram_type'] = type_map[user_input]
	
	# Разные подсказки для разных типов
	prompts = {
		'personal': "Введите username (например: @durov или просто durov):",
		'group': "Введите ссылку на группу или чат:\n• https://t.me/chatname\n• https://t.me/joinchat/abc123\n• @chatname",
		'channel': "Введите ссылку на канал:\n• https://t.me/channelname\n• @channelname\n• просто channelname"
	}
	
	await update.message.reply_text(
		f"📱 **Telegram | {type_map[user_input].capitalize()}**\n\n"
		f"{prompts[type_map[user_input]]}"
	)
	
	return WAIT_TELEGRAM_STEP2  # новое состояние


async def process_telegram_step2(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""ШАГ 2 для Telegram: обработка username/ссылки"""
	user_input = update.message.text.strip()
	tg_type = context.user_data.get('telegram_type')
	
	# Парсим в зависимости от типа
	parsed = parse_telegram_input(user_input, tg_type)
	
	if not parsed['valid']:
		await update.message.reply_text(
			f"❌ Неправильный формат для {tg_type}.\n\n"
			f"{parsed['hint']}",
			reply_markup=InlineKeyboardMarkup([
				[InlineKeyboardButton("◀️ Назад", callback_data="back_telegram_step1")]
			])
		)
		return WAIT_TELEGRAM_STEP2
	
	# Сохраняем данные
	context.user_data['telegram_parsed'] = parsed
	
	# ШАГ 3: спрашиваем название с кнопкой "Пропустить"
	keyboard = [[InlineKeyboardButton("⏭️ Пропустить", callback_data="skip_telegram_title")]]
	
	await update.message.reply_text(
		f"✅ Данные приняты!\n\n"
		f"🔗 Ссылка: {parsed['url']}\n"
		f"📌 Username: @{parsed.get('username', '')}\n\n"
		f"📝 Введите название для этого Telegram (или нажмите кнопку ниже):",
		reply_markup=InlineKeyboardMarkup(keyboard)
	)
	
	return WAIT_TELEGRAM_STEP3


async def skip_telegram_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Пропустить ввод названия"""
	query = update.callback_query
	await query.answer()
	
	# Вместо ввода названия, сразу сохраняем с пропуском
	context.user_data['skip_title'] = True
	
	# Собираем все данные
	tg_type = context.user_data.get('telegram_type')
	parsed = context.user_data.get('telegram_parsed', {})
	
	# Данные для pay_details
	pay_details = {
		'telegram_type': tg_type,
		'url': parsed['url']
	}
	
	if parsed.get('username'):
		pay_details['username'] = parsed['username']
	
	if parsed.get('invite_link'):
		pay_details['invite_link'] = parsed['invite_link']
	
	# НАЗВАНИЕ ДЛЯ ССЫЛКИ - всегда просто "Telegram"
	link_title = "Telegram"
	
	# ===== СОХРАНЕНИЕ В БД =====
	conn = await get_db_connection()
	try:
		await conn.execute("""
                           INSERT INTO links
                           (page_id, title, url, icon, sort_order, is_active, created_at, link_type, pay_details,
                            category)
                           VALUES ($1, $2, $3, $4,
                                   COALESCE((SELECT MAX(sort_order) + 1 FROM links WHERE page_id = $5), 1),
                                   true, NOW(), $6, $7, 'social')
		                   """,
		                   context.user_data['page_id'],
		                   link_title,  # теперь просто "Telegram"
		                   parsed['url'],
		                   'telegram',
		                   context.user_data['page_id'],
		                   'telegram',
		                   json.dumps(pay_details, ensure_ascii=False) if pay_details else None
		                   )
		
		success_text = f"✅ Telegram добавлен!\n\n"
		success_text += f"📌 Название: {link_title}\n"  # будет "Telegram"
		success_text += f"🔗 Ссылка: {parsed['url']}\n"
		
		if parsed.get('username'):
			success_text += f"📋 Username: @{parsed['username']}\n"  # отдельно username
		
		from core.config import APP_URL
		base_url = APP_URL.rstrip('/')
		page_username = context.user_data.get('page_username')
		
		if page_username:
			page_url = f"{base_url}/{page_username}"
			success_text += f"\n👀 Посмотреть на странице:\n{page_url}\n"
		
		await query.edit_message_text(
			success_text,
			reply_markup=main_menu_keyboard()
		)
		
		# Очищаем данные
		context.user_data.pop('telegram_type', None)
		context.user_data.pop('telegram_parsed', None)
		
		return ConversationHandler.END
	
	except Exception as e:
		logger.error(f"Ошибка при сохранении Telegram: {e}")
		await query.edit_message_text(f"❌ Ошибка при сохранении: {e}")
		return ConversationHandler.END
	finally:
		await conn.close()


def parse_telegram_input(text: str, tg_type: str) -> dict:
	"""Парсит ввод для Telegram с учетом типа"""
	text = text.strip()
	
	result = {
		'valid': False,
		'url': '',
		'username': '',
		'invite_link': '',
		'hint': ''
	}
	
	# Для личного аккаунта
	if tg_type == 'personal':
		# Убираем @ если есть
		username = text.replace('@', '').split('/')[-1]
		# Проверяем что только буквы и цифры
		if username.replace('_', '').isalnum():
			result['valid'] = True
			result['url'] = f"https://t.me/{username}"
			result['username'] = username
		else:
			result['hint'] = "Username должен содержать только буквы, цифры и _"
	
	# Для группы/чата
	elif tg_type == 'group':
		if 'joinchat/' in text:
			# Invite link
			invite = text.split('joinchat/')[-1].split('?')[0]
			result['valid'] = True
			result['url'] = f"https://t.me/joinchat/{invite}"
			result['invite_link'] = invite
		elif 't.me/' in text:
			username = text.split('t.me/')[-1].split('/')[0].split('?')[0]
			result['valid'] = True
			result['url'] = f"https://t.me/{username}"
			result['username'] = username
		elif text.startswith('@'):
			username = text[1:]
			result['valid'] = True
			result['url'] = f"https://t.me/{username}"
			result['username'] = username
		else:
			result['hint'] = "Введите ссылку вида https://t.me/chatname или https://t.me/joinchat/abc123"
	
	# Для канала
	elif tg_type == 'channel':
		if 't.me/' in text:
			username = text.split('t.me/')[-1].split('/')[0].split('?')[0]
			result['valid'] = True
			result['url'] = f"https://t.me/{username}"
			result['username'] = username
		elif text.startswith('@'):
			username = text[1:]
			result['valid'] = True
			result['url'] = f"https://t.me/{username}"
			result['username'] = username
		elif text.replace('_', '').isalnum():
			result['valid'] = True
			result['url'] = f"https://t.me/{text}"
			result['username'] = text
		else:
			result['hint'] = "Введите username канала (@channel или просто channel)"
	
	return result


async def process_telegram_step3(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""ШАГ 3: сохраняем название (опционально)"""
	
	# Проверяем, может быть это не сообщение, а callback от кнопки
	if update.callback_query:
		# Если пришел callback - значит нажали кнопку пропуска
		query = update.callback_query
		await query.answer()
		title = None
		# Отвечаем в том же сообщении
		reply_func = query.edit_message_text
	else:
		# Обычное текстовое сообщение
		user_input = update.message.text.strip()
		
		# Если пользователь ввел /skip - пропускаем
		if user_input == '/skip':
			title = None
		else:
			title = user_input
		reply_func = update.message.reply_text
	
	# Собираем все данные
	tg_type = context.user_data.get('telegram_type')
	parsed = context.user_data.get('telegram_parsed', {})
	
	# Данные для pay_details
	pay_details = {
		'telegram_type': tg_type,
		'url': parsed['url']
	}
	
	# Добавляем username если есть
	if parsed.get('username'):
		pay_details['username'] = parsed['username']
	
	# Добавляем название если ввели
	if title:
		pay_details['title'] = title
	
	# Добавляем invite link если есть
	if parsed.get('invite_link'):
		pay_details['invite_link'] = parsed['invite_link']
	
	# Название для ссылки (title в БД)
	if title:
		# Если пользователь ввел название - используем только его
		link_title = title
	else:
		# Если не ввел - берем стандартное название для типа
		type_titles = {
			'personal': 'Telegram Личный',
			'group': 'Telegram Группа',
			'channel': 'Telegram Канал'
		}
		link_title = type_titles.get(tg_type, 'Telegram')
	
	# ===== СОХРАНЕНИЕ В БД =====
	conn = await get_db_connection()
	try:
		await conn.execute("""
                           INSERT INTO links
                           (page_id, title, url, icon, sort_order, is_active, created_at, link_type, pay_details,
                            category)
                           VALUES ($1, $2, $3, $4,
                                   COALESCE((SELECT MAX(sort_order) + 1 FROM links WHERE page_id = $5), 1),
                                   true, NOW(), $6, $7, 'social')
		                   """,
		                   context.user_data['page_id'],
		                   link_title,
		                   parsed['url'],
		                   'telegram',  # icon
		                   context.user_data['page_id'],
		                   'telegram',
		                   json.dumps(pay_details, ensure_ascii=False) if pay_details else None
		                   )
		
		# Формируем сообщение об успехе
		success_text = f"✅ Telegram добавлен!\n\n"
		success_text += f"📌 Название: {link_title}\n"
		success_text += f"🔗 Ссылка: {parsed['url']}\n"
		
		if parsed.get('username'):
			success_text += f"📋 Username: @{parsed['username']}\n"
		
		# Добавляем ссылку на страницу где можно посмотреть
		from core.config import APP_URL
		base_url = APP_URL.rstrip('/')
		page_username = context.user_data.get('page_username')
		
		if page_username:
			page_url = f"{base_url}/{page_username}"
			success_text += f"\n👀 Посмотреть на странице:\n{page_url}\n"
		
		# Отправляем ответ (через reply_text или edit_message_text)
		await reply_func(
			success_text,
			reply_markup=main_menu_keyboard()
		)
		
		# Очищаем временные данные
		context.user_data.pop('telegram_type', None)
		context.user_data.pop('telegram_parsed', None)
		context.user_data.pop('social_data', None)
		context.user_data.pop('social_config', None)
		
		return ConversationHandler.END
	
	except Exception as e:
		logger.error(f"Ошибка при сохранении Telegram: {e}")
		await reply_func(f"❌ Ошибка при сохранении: {e}")
		return ConversationHandler.END
	finally:
		await conn.close()


async def back_to_telegram_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Возврат к выбору типа Telegram"""
	query = update.callback_query
	await query.answer()
	
	# ОЧИЩАЕМ старые данные Telegram
	context.user_data.pop('telegram_type', None)
	context.user_data.pop('telegram_parsed', None)
	
	text = (
		f"📱 **Telegram**\n\n"
		f"✏️ **ШАГ 1 из 3:** Выберите тип:"
	)
	
	keyboard = [
		[
			InlineKeyboardButton("👤 Личный аккаунт", callback_data="telegram_type_personal"),
			InlineKeyboardButton("👥 Группа/чат", callback_data="telegram_type_group")
		],
		[
			InlineKeyboardButton("📢 Канал", callback_data="telegram_type_channel")
		],
		[InlineKeyboardButton("◀️ Назад к соцсетям", callback_data="cat_social")]
	]
	
	await query.edit_message_text(
		text,
		reply_markup=InlineKeyboardMarkup(keyboard),
		parse_mode='Markdown'
	)
	
	return WAIT_TELEGRAM_STEP1


async def back_to_telegram_step2(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Возврат ко второму шагу Telegram"""
	query = update.callback_query
	await query.answer()
	
	tg_type = context.user_data.get('telegram_type')
	
	prompts = {
		'personal': (
			"👤 **Личный аккаунт или бот**\n\n"
			"📝 Введи username:\n"
			"• `@durov`\n"
			"• `durov`\n"
			"• `https://t.me/durov`\n\n"
			"👇 Жду твой username:"
		),
		'group': (
			"👥 **Группа или чат**\n\n"
			"🔗 Введи ссылку на группу:\n"
			"• `https://t.me/chatname` — открытая группа\n"
			"• `https://t.me/joinchat/abc123` — приватная (invite link)\n"
			"• `@chatname`\n\n"
			"👇 Кидай ссылку:"
		),
		'channel': (
			"📢 **Канал**\n\n"
			"📎 Введи ссылку на канал:\n"
			"• `https://t.me/channelname`\n"
			"• `@channelname`\n"
			"• просто `channelname`\n\n"
			"👇 Ссылочку сюда:"
		)
	}
	
	# Кнопка назад к выбору типа
	keyboard = [[InlineKeyboardButton("◀️ Назад к выбору типа", callback_data="back_telegram_type")]]
	
	await query.edit_message_text(
		prompts.get(tg_type, prompts['personal']),
		reply_markup=InlineKeyboardMarkup(keyboard),
		parse_mode='Markdown'
	)
	
	return WAIT_TELEGRAM_STEP2
