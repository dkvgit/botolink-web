# D:\aRabota\TelegaBoom\030_botolinkpro\bot\bank.py

import json
import logging
import re

from bot.states import *
from bot.states import (
    WAIT_REVOLUT_FULL, WAIT_REVOLUT_QUICK, WAIT_REVOLUT_CHOICE,
    WAIT_REVOLUT_BIC, WAIT_REVOLUT_CORRESPONDENT, WAIT_REVOLUT_ADDRESS,
    WAIT_REVOLUT_IBAN, WAIT_REVOLUT_BENEFICIARY, WAIT_REVOLUT_LOGIN,
    WAIT_WISE_FULL, WAIT_IDRAM, WAIT_TBCPAY, WAIT_CLICK, WAIT_PAYME,
    WAIT_KASPI, WAIT_MONOBANK, WAIT_VKPAY, WAIT_YOOMONEY,
    WAIT_PAYPAL, WAIT_SWIFT, WAIT_IBAN, SELECT_COUNTRY,
    WAIT_OTHER_DETAILS, CONFIRM_PAYMENT
)
from bot.utils import (
    check_subscription,
    get_or_create_user,
    log_error,
    error_handler,
    safe_callback,
    format_card,
    format_phone,
    clean_digits,
    get_db_connection
)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

logger = logging.getLogger(__name__)


# Находим функцию choose_country_from_constructor
# // bot/bank.py

async def choose_country_from_constructor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Переход из конструктора в банковский модуль.
    Мы НЕ заканчиваем диалог, а переводим его в стейт выбора стран/методов.
    """
    query = update.callback_query
    if query:
        await query.answer()
        print(f"💳 Переход в банки из конструктора: {query.data}")
    
    # 1. Импортируем ПРАВИЛЬНУЮ функцию из bankworld.py
    from bot.bankworld import show_country_methods
    
    # 2. Вызываем именно её (вместо choose_country)
    await show_country_methods(update, context)
    
    # 3. Получаем нужный стейт
    from bot.states import SELECT_CATEGORY
    
    print(f"🔄 Стейт изменен на: SELECT_CATEGORY ({SELECT_CATEGORY})")
    
    # 4. Возвращаем стейт для ConversationHandler
    return SELECT_CATEGORY

# Удали импорт и добавь функцию прямо в bank.py
async def get_user_page(conn, user_id: int):
	"""Получить страницу пользователя"""
	page = await conn.fetchrow(
		"SELECT * FROM pages WHERE user_id = (SELECT id FROM users WHERE telegram_id = $1)",
		user_id
	)
	return page


# ============================================
# ГЛАВНОЕ МЕНЮ ВЫБОРА СТРАНЫ
# ============================================

# // bot/bank.py

async def choose_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню выбора страны и сервисов (универсальный вызов)"""
    from telegram.ext import ConversationHandler
    
    # Логирование для отладки
    cb_data = update.callback_query.data if update.callback_query else "no_callback"
    print(f"\n" + "🌍" * 5 + " ВХОД В choose_country " + "🌍" * 5)
    print(f"🔹 Callback: {cb_data}")
    
    # Определяем способ ответа (редактирование или новое сообщение)
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        send_func = query.edit_message_text
    else:
        send_func = update.message.reply_text
    
    # Полная очистка временных данных перед новым выбором
    keys_to_clear = [
        'selected_methods', 'selected_methods_full', 'filling_queue',
        'collected_methods', 'current_method', 'selected_country',
        'current_field_index'
    ]
    for key in keys_to_clear:
        context.user_data.pop(key, None)
    
    text = (
        "🌍 *Как хотите получать переводы?*\n\n"
        "👇 *Выберите платежную систему или страну банка:*"
    )
    
    # Кнопки сервисов (по 3 в ряд)
    payment_wallet_buttons = [
        InlineKeyboardButton("🌐 PayPal", callback_data="method_paypal"),
        InlineKeyboardButton("🇪🇺 Wise", callback_data="method_wise"),
        InlineKeyboardButton("🇪🇺 Revolut", callback_data="method_revolut"),
        InlineKeyboardButton("🌐 SWIFT/IBAN", callback_data="method_swift"),
        InlineKeyboardButton("🇷🇺 ЮMoney", callback_data="method_yoomoney"),
        InlineKeyboardButton("🇷🇺 VK Pay", callback_data="method_vkpay"),
        InlineKeyboardButton("🇺🇦 Монобанк", callback_data="method_monobank"),
        InlineKeyboardButton("🇰🇿 Kaspi.kz", callback_data="method_kaspi"),
        InlineKeyboardButton("🇺🇿 Payme", callback_data="method_payme"),
        InlineKeyboardButton("🇺🇿 Click", callback_data="method_click"),
        InlineKeyboardButton("🇬🇪 TBC Pay", callback_data="method_tbcpay"),
        InlineKeyboardButton("🇦🇲 Idram", callback_data="method_idram"),
    ]
    
    # Кнопки стран (по 3 в ряд)
    bank_buttons = [
        InlineKeyboardButton("🇱🇹 Литва", callback_data="country_lithuania"),
        InlineKeyboardButton("🇱🇻 Латвия", callback_data="country_latvia"),
        InlineKeyboardButton("🇪🇪 Эстония", callback_data="country_estonia"),
        InlineKeyboardButton("🇺🇸 США", callback_data="country_usa"),
        InlineKeyboardButton("🇷🇺 Россия", callback_data="country_russia"),
        InlineKeyboardButton("🇺🇦 Украина", callback_data="country_ukraine"),
        InlineKeyboardButton("🇧🇾 Беларусь", callback_data="country_belarus"),
        InlineKeyboardButton("🇰🇿 Казахстан", callback_data="country_kazakhstan"),
        InlineKeyboardButton("🇦🇲 Армения", callback_data="country_armenia"),
        InlineKeyboardButton("🇦🇿 Азербайджан", callback_data="country_azerbaijan"),
        InlineKeyboardButton("🇬🇪 Грузия", callback_data="country_georgia"),
        InlineKeyboardButton("🇲🇩 Молдова", callback_data="country_moldova"),
        InlineKeyboardButton("🇺🇿 Узбекистан", callback_data="country_uzbekistan"),
        InlineKeyboardButton("🇹🇯 Таджикистан", callback_data="country_tajikistan"),
        InlineKeyboardButton("🇰🇬 Кыргызстан", callback_data="country_kyrgyzstan"),
        InlineKeyboardButton("🇹🇲 Туркменистан", callback_data="country_turkmenistan"),
        InlineKeyboardButton("🇻🇳 Вьетнам", callback_data="country_vietnam"),
    ]
    
    keyboard = []
    
    # Секция кошельков
    keyboard.append([InlineKeyboardButton("─── 👛 КОШЕЛЬКИ И СЕРВИСЫ ───", callback_data="ignore")])
    for i in range(0, len(payment_wallet_buttons), 3):
        keyboard.append(payment_wallet_buttons[i:i + 3])
    
    # Секция банков
    keyboard.append([InlineKeyboardButton("─── 🏦 БАНКИ ПО СТРАНАМ ───", callback_data="ignore")])
    for i in range(0, len(bank_buttons), 3):
        keyboard.append(bank_buttons[i:i + 3])
    
    # Кнопка возврата в общее меню категорий
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_categories")])
    
    await send_func(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    # Завершаем текущий ConversationHandler, чтобы передать управление
    # следующему хендлеру, который ловит country_ или method_
    return ConversationHandler.END


async def back_to_add_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()
	
	print(f"💳 bank.py получил: {update.callback_query.data}")
	
	from bot.link_constructor import add_link_start
	return await add_link_start(update, context)
	# НЕ НАДО END, потому что мы не в диалоге


# ============================================
# ФУНКЦИЯ: ЮMoney (Яндекс.Деньги)
# ============================================
async def method_yoomoney(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Показывает инструкцию и просит ввести номер кошелька"""
	query = update.callback_query
	print(f"🌍 method_yoomoney ВЫЗВАНА с data: {update.callback_query.data}")
	
	await query.answer()
	
	text = (
		"💳 ЮMoney (Яндекс.Деньги)\n\n"
		"✏️ Введите номер вашего кошелька\n\n"
		"📌 Например:\n"
		"• <code>410011234567890</code>\n"
		"• Или ссылка: <code>https://yoomoney.ru/to/410011234567890</code>\n\n"
		"👇 Жду ваш ввод в поле чата..."
	)
	
	keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_countries")]]
	
	await query.edit_message_text(
		text,
		reply_markup=InlineKeyboardMarkup(keyboard),
		parse_mode='HTML'
	)
	return WAIT_YOOMONEY


def clean_yoomoney_number(text: str) -> str:
	"""Извлекает номер кошелька из любого ввода"""
	text = text.strip()
	
	# Проверяем, не ссылка ли это на карту или телефон
	if "card" in text.lower() or "phone" in text.lower():
		return None  # или вызови ошибку
	
	# Ищем ссылку yoomoney.ru/to/
	if "yoomoney.ru/to/" in text:
		number = text.split("yoomoney.ru/to/")[-1]
	elif "money.yandex.ru/to/" in text:
		number = text.split("money.yandex.ru/to/")[-1]
	else:
		# Просто номер
		number = text
	
	# Убираем лишние символы, оставляем только цифры
	number = re.sub(r'[^\d]', '', number)
	
	# Проверяем, что номер начинается с 41001 (признак ЮMoney кошелька)
	if number.startswith('41001'):
		return number
	else:
		return None  # не похоже на ЮMoney кошелек


async def process_yoomoney_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Получает текст, очищает номер, формирует ссылку"""
	user_input = update.message.text
	
	# Очищаем номер
	number = clean_yoomoney_number(user_input)
	full_link = f"https://yoomoney.ru/to/{number}"
	
	context.user_data['payment_data'] = {
		'type': 'yoomoney',
		'raw_input': user_input,
		'number': number,
		'link': full_link,
		'payment_type': 'yoomoney'
	}
	
	# Показываем подтверждение
	await update.message.reply_text(
		f"✅ Проверьте данные:\n\n"
		f"Ссылка: <code>{full_link}</code>\n"
		f"Номер: <b>{number}</b>\n\n"
		f"👇 Всё верно?",
		reply_markup=InlineKeyboardMarkup([
			[
				InlineKeyboardButton("✅ Да", callback_data="confirm_yes"),
				InlineKeyboardButton("❌ Нет", callback_data="confirm_no")
			]
		]),
		parse_mode='HTML'
	)
	
	return CONFIRM_PAYMENT


# ============================================
# ФУНКЦИЯ: VK Pay
# ============================================
async def method_vkpay(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Показывает инструкцию и просит ввести ID или телефон VK"""
	query = update.callback_query
	print(f"🌍 method_vkpay ВЫЗВАНА с data: {update.callback_query.data}")
	
	await query.answer()
	
	text = (
		"💳 VK Pay (ВКонтакте\n\n"
		"✏️ Введите ваш VK ID или номер телефона\n\n"
		"📌 Например:\n"
		"• <code>id123456789</code>\n"
		"• <code>https://vk.com/id123456789</code>\n"
		"• <code>+79123456789</code>\n\n"
		"👇 Жду ваш ввод в поле чата..."
	)
	
	keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_countries")]]
	
	await query.edit_message_text(
		text,
		reply_markup=InlineKeyboardMarkup(keyboard),
		parse_mode='HTML'
	)
	return WAIT_VKPAY


def clean_vkpay_data(text: str) -> dict:
	"""Извлекает ID или телефон из ввода"""
	text = text.strip()
	
	# Ссылка на VK Pay (если есть такой формат)
	if "vk.com/pay" in text:
		if "to=" in text:
			phone = text.split("to=")[-1]
			phone = re.sub(r'[^\d+]', '', phone)
			return {"type": "phone", "value": phone}
	
	# Ссылка на профиль VK
	if "vk.com/" in text:
		parts = text.split("vk.com/")[-1]
		# Убираем возможные параметры после ?
		if "?" in parts:
			parts = parts.split("?")[0]
		if parts.startswith("id"):
			return {"type": "id", "value": parts.replace("id", "")}
		elif parts.startswith("public"):
			return {"type": "id", "value": parts.replace("public", "")}
		else:
			# Может быть короткая ссылка
			return {"type": "id", "value": parts}
	
	# Просто id123 или 123
	if text.startswith("id"):
		return {"type": "id", "value": text.replace("id", "")}
	
	# Телефон
	phone = re.sub(r'[^\d+]', '', text)
	if phone.startswith('+') or (phone.isdigit() and len(phone) >= 10):
		if not phone.startswith('+'):
			phone = '+' + phone
		return {"type": "phone", "value": phone}
	
	# Если цифры - считаем ID
	if text.isdigit():
		return {"type": "id", "value": text}
	
	return {"type": "unknown", "value": text}


async def process_vkpay_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Получает текст, очищает данные, формирует ссылку"""
	user_input = update.message.text
	
	# Очищаем данные
	data = clean_vkpay_data(user_input)
	
	if data["type"] == "id":
		full_link = f"https://vk.com/id{data['value']}"
		display = f"VK ID: {data['value']}"
	elif data["type"] == "phone":
		full_link = f"https://vk.com/pay?act=to&to={data['value']}"
		display = f"Телефон: {data['value']}"
	else:
		await update.message.reply_text(
			"❌ Не удалось распознать. Введите VK ID или номер телефона:"
		)
		return WAIT_VKPAY
	
	context.user_data['payment_data'] = {
		'type': 'vkpay',
		'raw_input': user_input,
		'clean_data': data,
		'link': full_link,
		'payment_type': 'vkpay'
	}
	
	await update.message.reply_text(
		f"✅ Проверьте данные:\n\n"
		f"Ссылка: <code>{full_link}</code>\n"
		f"{display}\n\n"
		f"👇 Всё верно?",
		reply_markup=InlineKeyboardMarkup([
			[
				InlineKeyboardButton("✅ Да", callback_data="confirm_yes"),
				InlineKeyboardButton("❌ Нет", callback_data="confirm_no")
			]
		]),
		parse_mode='HTML'
	)
	
	return CONFIRM_PAYMENT


# ============================================
# ФУНКЦИЯ: Монобанк (Украина)
# ============================================
async def method_monobank(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Показывает инструкцию и просит ввести номер карты"""
	query = update.callback_query
	print(f"🌍 method_monobank ВЫЗВАНА с data: {update.callback_query.data}")
	
	await query.answer()
	
	text = (
		"💳 Монобанк (Украина)\n\n"
		"✏️ Введите номер вашей карты\n\n"
		"📌 Например:\n"
		"• <code>5375411234567890</code>\n"
		"• Или ссылка на банку: <code>https://send.monobank.ua/jar/токен</code>\n\n"
		"👇 Жду ваш ввод в поле чата..."
	)
	
	keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_countries")]]
	
	await query.edit_message_text(
		text,
		reply_markup=InlineKeyboardMarkup(keyboard),
		parse_mode='HTML'
	)
	return WAIT_MONOBANK


def clean_monobank_data(text: str) -> dict:
	"""Извлекает номер карты или токен банки"""
	text = text.strip()
	
	# Ссылка на банку
	if "send.monobank.ua/jar/" in text:
		token = text.split("send.monobank.ua/jar/")[-1]
		return {"type": "jar", "value": token}
	
	# Номер карты (очищаем от пробелов)
	card = re.sub(r'[\s-]', '', text)
	if card.isdigit() and len(card) == 16:
		return {"type": "card", "value": card}
	
	return {"type": "unknown", "value": text}


async def process_monobank_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Получает текст, очищает данные, формирует ссылку"""
	user_input = update.message.text
	
	# Очищаем данные
	data = clean_monobank_data(user_input)
	
	if data["type"] == "card":
		full_link = f"https://monobank.ua/{data['value']}"
		display = f"Карта: {data['value'][:4]} **** **** {data['value'][-4:]}"
	elif data["type"] == "jar":
		full_link = f"https://send.monobank.ua/jar/{data['value']}"
		display = f"Банка: {data['value']}"
	else:
		await update.message.reply_text(
			"❌ Не удалось распознать. Введите номер карты (16 цифр) или ссылку на банку:"
		)
		return WAIT_MONOBANK
	
	context.user_data['payment_data'] = {
		'type': 'monobank',
		'raw_input': user_input,
		'clean_data': data,
		'link': full_link,
		'payment_type': 'monobank'
	}
	
	await update.message.reply_text(
		f"✅ Проверьте данные:\n\n"
		f"Ссылка: <code>{full_link}</code>\n"
		f"{display}\n\n"
		f"👇 Всё верно?",
		reply_markup=InlineKeyboardMarkup([
			[
				InlineKeyboardButton("✅ Да", callback_data="confirm_yes"),
				InlineKeyboardButton("❌ Нет", callback_data="confirm_no")
			]
		]),
		parse_mode='HTML'
	)
	
	return CONFIRM_PAYMENT


# ============================================
# ФУНКЦИЯ: Kaspi.kz (Казахстан)
# ============================================
async def method_kaspi(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Показывает инструкцию и просит ввести номер карты или телефона Kaspi"""
	query = update.callback_query
	print(f"🌍 method_kaspi ВЫЗВАНА с data: {update.callback_query.data}")
	
	await query.answer()
	
	text = (
		"💳 Kaspi.kz (Казахстан)\n\n"
		"✏️ Введите номер карты Kaspi или номер телефона\n\n"
		"📌 Например:\n"
		"• <code>5169497123456789</code> (карта)\n"
		"• <code>https://kaspi.kz/pay/77001234567</code> (ссылка)\n"
		"• <code>+77001234567</code> (телефон)\n\n"
		"👇 Жду ваш ввод в поле чата..."
	)
	
	keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_countries")]]
	
	await query.edit_message_text(
		text,
		reply_markup=InlineKeyboardMarkup(keyboard),
		parse_mode='HTML'
	)
	return WAIT_KASPI


def clean_kaspi_data(text: str) -> dict:
	"""Извлекает номер карты или телефон Kaspi"""
	text = text.strip()
	
	# Ссылка Kaspi на оплату по телефону
	if "kaspi.kz/pay/" in text:
		phone = text.split("kaspi.kz/pay/")[-1]
		if not phone.startswith('+'):
			phone = '+' + phone
		return {"type": "phone", "value": phone}
	
	# Ссылка Kaspi на карту (если есть такой формат)
	if "kaspi.kz/card/" in text:
		card = text.split("kaspi.kz/card/")[-1]
		card = re.sub(r'[^\d]', '', card)
		if len(card) == 16:
			return {"type": "card", "value": card}
	
	# Очищаем от лишних символов
	cleaned = re.sub(r'[\s-]', '', text)
	
	# Карта (16 цифр)
	if cleaned.isdigit() and len(cleaned) == 16:
		return {"type": "card", "value": cleaned}
	
	# Телефон
	phone = re.sub(r'[^\d+]', '', text)
	if phone.startswith('+7') or phone.startswith('8') or (phone.isdigit() and len(phone) >= 10):
		if not phone.startswith('+'):
			phone = '+7' + phone[-10:]
		return {"type": "phone", "value": phone}
	
	return {"type": "unknown", "value": text}


async def process_kaspi_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Получает текст, очищает данные, формирует ссылку"""
	user_input = update.message.text
	
	# Очищаем данные
	data = clean_kaspi_data(user_input)
	
	if data["type"] == "card":
		full_link = f"https://kaspi.kz/{data['value']}"
		display = f"Карта: {data['value'][:4]} **** **** {data['value'][-4:]}"
	elif data["type"] == "phone":
		full_link = f"https://kaspi.kz/pay/{data['value']}"
		display = f"Телефон: {data['value']}"
	else:
		await update.message.reply_text(
			"❌ Не удалось распознать. Введите номер карты (16 цифр) или номер телефона:"
		)
		return WAIT_KASPI
	
	context.user_data['payment_data'] = {
		'type': 'kaspi',
		'raw_input': user_input,
		'clean_data': data,
		'link': full_link,
		'payment_type': 'kaspi'
	}
	
	await update.message.reply_text(
		f"✅ Проверьте данные:\n\n"
		f"Ссылка: <code>{full_link}</code>\n"
		f"{display}\n\n"
		f"👇 Всё верно?",
		reply_markup=InlineKeyboardMarkup([
			[
				InlineKeyboardButton("✅ Да", callback_data="confirm_yes"),
				InlineKeyboardButton("❌ Нет", callback_data="confirm_no")
			]
		]),
		parse_mode='HTML'
	)
	
	return CONFIRM_PAYMENT


# ============================================
# ФУНКЦИЯ: Payme (Узбекистан)
# ============================================
async def method_payme(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Показывает инструкцию и просит ввести номер телефона Payme"""
	query = update.callback_query
	print(f"🌍 method_payme ВЫЗВАНА с data: {update.callback_query.data}")
	
	await query.answer()
	
	text = (
		"💳 Payme (Узбекистан)\n\n"
		"✏️ Введите ваш номер телефона для Payme\n\n"
		"📌 Например:\n"
		"• <code>+998901234567</code>\n"
		"• <code>https://payme.uz/998901234567</code>\n"
		"• <code>901234567</code>\n\n"
		"👇 Жду ваш ввод в поле чата..."
	)
	
	keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_countries")]]
	
	await query.edit_message_text(
		text,
		reply_markup=InlineKeyboardMarkup(keyboard),
		parse_mode='HTML'
	)
	return WAIT_PAYME


def clean_payme_phone(text: str) -> str:
	"""Извлекает номер телефона для Payme"""
	text = text.strip()
	
	# Проверяем, может это карта (16 цифр)
	cleaned = re.sub(r'[^\d]', '', text)
	if len(cleaned) == 16:
		# Если это карта, возвращаем как есть (потом process_payme_input поймет)
		return cleaned
	
	# Ссылка Payme на телефон
	if "payme.uz/" in text:
		phone = text.split("payme.uz/")[-1]
		# Убираем лишнее
		phone = re.sub(r'[^\d]', '', phone)
	else:
		# Просто телефон
		phone = cleaned
	
	# Добавляем +998 если нужно
	if len(phone) == 9 and phone.startswith('9'):
		phone = f"+998{phone}"
	elif len(phone) == 12 and phone.startswith('998'):
		phone = f"+{phone}"
	elif len(phone) == 10 and phone.startswith('8'):
		phone = f"+998{phone[1:]}"
	
	return phone


async def process_payme_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Получает текст, очищает номер, формирует ссылку"""
	user_input = update.message.text
	
	# Очищаем номер
	phone = clean_payme_phone(user_input)
	
	# Убираем + для ссылки если есть
	link_phone = phone.replace('+', '')
	full_link = f"https://payme.uz/{link_phone}"
	
	context.user_data['payment_data'] = {
		'type': 'payme',
		'raw_input': user_input,
		'phone': phone,
		'link': full_link,
		'payment_type': 'payme'
	}
	
	await update.message.reply_text(
		f"✅ Проверьте данные:\n\n"
		f"Ссылка: <code>{full_link}</code>\n"
		f"Телефон: <b>{phone}</b>\n\n"
		f"👇 Всё верно?",
		reply_markup=InlineKeyboardMarkup([
			[
				InlineKeyboardButton("✅ Да", callback_data="confirm_yes"),
				InlineKeyboardButton("❌ Нет", callback_data="confirm_no")
			]
		]),
		parse_mode='HTML'
	)
	
	return CONFIRM_PAYMENT


# ============================================
# ФУНКЦИЯ: Click (Узбекистан)
# ============================================
async def method_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Показывает инструкцию и просит ввести номер телефона Click"""
	query = update.callback_query
	print(f"🌍 method_click ВЫЗВАНА с data: {update.callback_query.data}")
	
	await query.answer()
	
	text = (
		"💳 Click (Узбекистан)\n\n"
		"✏️ Введите ваш номер телефона для Click\n\n"
		"📌 Например:\n"
		"• <code>+998901234567</code>\n"
		"• <code>https://click.uz/998901234567</code>\n"
		"• <code>901234567</code>\n\n"
		"👇 Жду ваш ввод в поле чата..."
	)
	
	keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_countries")]]
	
	await query.edit_message_text(
		text,
		reply_markup=InlineKeyboardMarkup(keyboard),
		parse_mode='HTML'
	)
	return WAIT_CLICK


def clean_click_phone(text: str) -> str:
	"""Извлекает номер телефона для Click"""
	text = text.strip()
	
	# Сначала проверяем, может это ссылка на карту (если есть такой формат)
	if "click.uz/card/" in text:
		card = text.split("click.uz/card/")[-1]
		card = re.sub(r'[^\d]', '', card)
		if len(card) == 16:
			return card  # или return f"+998{card[-9:]}" если карта привязана к телефону
	
	# Ссылка Click на телефон
	if "click.uz/" in text:
		phone = text.split("click.uz/")[-1]
		# Убираем лишнее
		phone = re.sub(r'[^\d]', '', phone)
	else:
		# Просто телефон
		phone = re.sub(r'[^\d]', '', text)
	
	# Добавляем +998 если нужно
	if len(phone) == 9 and phone.startswith('9'):
		phone = f"+998{phone}"
	elif len(phone) == 12 and phone.startswith('998'):
		phone = f"+{phone}"
	elif len(phone) == 10 and phone.startswith('8'):
		phone = f"+998{phone[1:]}"
	elif len(phone) == 16:
		# Если вдруг ввели карту без указания типа
		return phone
	
	return phone


async def process_click_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Получает текст, очищает номер, формирует ссылку"""
	user_input = update.message.text
	
	# Очищаем номер
	phone = clean_click_phone(user_input)
	
	# Убираем + для ссылки если есть
	link_phone = phone.replace('+', '')
	full_link = f"https://click.uz/{link_phone}"
	
	context.user_data['payment_data'] = {
		'type': 'click',
		'raw_input': user_input,
		'phone': phone,
		'link': full_link,
		'payment_type': 'click'
	}
	
	await update.message.reply_text(
		f"✅ Проверьте данные:\n\n"
		f"Ссылка: <code>{full_link}</code>\n"
		f"Телефон: <b>{phone}</b>\n\n"
		f"👇 Всё верно?",
		reply_markup=InlineKeyboardMarkup([
			[
				InlineKeyboardButton("✅ Да", callback_data="confirm_yes"),
				InlineKeyboardButton("❌ Нет", callback_data="confirm_no")
			]
		]),
		parse_mode='HTML'
	)
	
	return CONFIRM_PAYMENT


# ============================================
# ФУНКЦИЯ: TBC Pay (Грузия)
# ============================================
async def method_tbcpay(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Показывает инструкцию и просит ввести номер карты или телефона TBC Pay"""
	query = update.callback_query
	print(f"🌍 method_tbcpay ВЫЗВАНА с data: {update.callback_query.data}")
	
	await query.answer()
	
	text = (
		"💳 TBC Pay (Грузия)\n\n"
		"✏️ Введите номер вашей карты или телефона\n\n"
		"📌 Например:\n"
		"• <code>5589012345678901</code> (карта)\n"
		"• <code>https://tbcpay.ge/transfer?to=558901234</code>\n"
		"• <code>+995558901234</code> (телефон)\n\n"
		"👇 Жду ваш ввод в поле чата..."
	)
	
	keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_countries")]]
	
	await query.edit_message_text(
		text,
		reply_markup=InlineKeyboardMarkup(keyboard),
		parse_mode='HTML'
	)
	return WAIT_TBCPAY


def clean_tbcpay_data(text: str) -> dict:
	"""Извлекает номер карты или телефона TBC Pay"""
	text = text.strip()
	
	# Ссылка на перевод по телефону
	if "tbcpay.ge/transfer" in text:
		if "to=" in text:
			phone = text.split("to=")[-1]
			phone = re.sub(r'[^\d]', '', phone)
			return {"type": "phone", "value": phone}
	
	# Ссылка на карту (если есть такой формат)
	if "tbcpay.ge/card/" in text:
		card = text.split("tbcpay.ge/card/")[-1]
		card = re.sub(r'[^\d]', '', card)
		if len(card) == 16:
			return {"type": "card", "value": card}
	
	# Очищаем от лишних символов
	cleaned = re.sub(r'[\s-]', '', text)
	
	# Карта (16 цифр)
	if cleaned.isdigit() and len(cleaned) == 16:
		return {"type": "card", "value": cleaned}
	
	# Телефон
	phone = re.sub(r'[^\d+]', '', text)
	if phone.startswith('+995') or (phone.isdigit() and len(phone) >= 9):
		if not phone.startswith('+'):
			phone = '+995' + phone[-9:]
		return {"type": "phone", "value": phone}
	
	return {"type": "unknown", "value": text}


async def process_tbcpay_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Получает текст, очищает данные, формирует ссылку"""
	user_input = update.message.text
	
	# Очищаем данные
	data = clean_tbcpay_data(user_input)
	
	if data["type"] == "card":
		full_link = f"https://tbcpay.ge/card/{data['value']}"
		display = f"Карта: {data['value'][:4]} **** **** {data['value'][-4:]}"
	elif data["type"] == "phone":
		full_link = f"https://tbcpay.ge/transfer?to={data['value'].replace('+', '')}"
		display = f"Телефон: {data['value']}"
	else:
		await update.message.reply_text(
			"❌ Не удалось распознать. Введите номер карты (16 цифр) или номер телефона:"
		)
		return WAIT_TBCPAY
	
	context.user_data['payment_data'] = {
		'type': 'tbcpay',
		'raw_input': user_input,
		'clean_data': data,
		'link': full_link,
		'payment_type': 'tbcpay'
	}
	
	await update.message.reply_text(
		f"✅ Проверьте данные:\n\n"
		f"Ссылка: <code>{full_link}</code>\n"
		f"{display}\n\n"
		f"👇 Всё верно?",
		reply_markup=InlineKeyboardMarkup([
			[
				InlineKeyboardButton("✅ Да", callback_data="confirm_yes"),
				InlineKeyboardButton("❌ Нет", callback_data="confirm_no")
			]
		]),
		parse_mode='HTML'
	)
	
	return CONFIRM_PAYMENT


# ============================================
# ФУНКЦИЯ: Idram (Армения)
# ============================================
async def method_idram(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Показывает инструкцию и просит ввести номер карты или телефона Idram"""
	query = update.callback_query
	print(f"🌍 method_idram ВЫЗВАНА с data: {update.callback_query.data}")
	
	await query.answer()
	
	text = (
		"💳 Idram (Армения)\n\n"
		"✏️ Введите номер вашей карты или телефона\n\n"
		"📌 Например:\n"
		"• <code>1234567890123456</code> (карта)\n"
		"• <code>https://idram.am/transfer?to=77001234567</code>\n"
		"• <code>+374770012345</code> (телефон)\n\n"
		"👇 Жду ваш ввод в поле чата..."
	)
	
	keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_countries")]]
	
	await query.edit_message_text(
		text,
		reply_markup=InlineKeyboardMarkup(keyboard),
		parse_mode='HTML'
	)
	return WAIT_IDRAM


def clean_idram_data(text: str) -> dict:
	"""Извлекает номер карты или телефона Idram"""
	text = text.strip()
	
	# Ссылка на перевод по телефону
	if "idram.am/transfer" in text:
		if "to=" in text:
			phone = text.split("to=")[-1]
			phone = re.sub(r'[^\d]', '', phone)
			return {"type": "phone", "value": phone}
	
	# Ссылка на карту
	if "idram.am/card/" in text:
		card = text.split("idram.am/card/")[-1]
		card = re.sub(r'[^\d]', '', card)
		if len(card) == 16:
			return {"type": "card", "value": card}
	
	# Очищаем от лишних символов
	cleaned = re.sub(r'[\s-]', '', text)
	
	# Карта (16 цифр)
	if cleaned.isdigit() and len(cleaned) == 16:
		return {"type": "card", "value": cleaned}
	
	# Телефон
	phone = re.sub(r'[^\d+]', '', text)
	if phone.startswith('+374') or (phone.isdigit() and len(phone) >= 8):
		if not phone.startswith('+'):
			phone = '+374' + phone[-8:]
		return {"type": "phone", "value": phone}
	
	return {"type": "unknown", "value": text}


async def process_idram_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Получает текст, очищает данные, формирует ссылку"""
	user_input = update.message.text
	
	# Очищаем данные
	data = clean_idram_data(user_input)
	
	if data["type"] == "card":
		full_link = f"https://idram.am/card/{data['value']}"
		display = f"Карта: {data['value'][:4]} **** **** {data['value'][-4:]}"
	elif data["type"] == "phone":
		full_link = f"https://idram.am/transfer?to={data['value'].replace('+', '')}"
		display = f"Телефон: {data['value']}"
	else:
		await update.message.reply_text(
			"❌ Не удалось распознать. Введите номер карты (16 цифр) или номер телефона:"
		)
		return WAIT_IDRAM
	
	context.user_data['payment_data'] = {
		'type': 'idram',
		'raw_input': user_input,
		'clean_data': data,
		'link': full_link,
		'payment_type': 'idram'
	}
	
	await update.message.reply_text(
		f"✅ Проверьте данные:\n\n"
		f"Ссылка: <code>{full_link}</code>\n"
		f"{display}\n\n"
		f"👇 Всё верно?",
		reply_markup=InlineKeyboardMarkup([
			[
				InlineKeyboardButton("✅ Да", callback_data="confirm_yes"),
				InlineKeyboardButton("❌ Нет", callback_data="confirm_no")
			]
		]),
		parse_mode='HTML'
	)
	
	return CONFIRM_PAYMENT


# ============================================
# ПОДТВЕРЖДЕНИЕ И СОХРАНЕНИЕ
# ============================================


async def show_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Показать подтверждение введенных данных"""
	
	data = context.user_data.get('payment_data', {})
	payment_type = data.get('type', 'unknown')
	
	text = "🔍 <b>Проверьте данные:</b>\n\n"
	
	# Общие поля
	if 'link' in data:
		# Для Kaspi и других, где в ссылке есть +
		if payment_type in ['kaspi', 'payme', 'click'] and '+' in data['link']:
			clean_link = data['link'].replace('+', '')
			text += f"🔗 <b>Ссылка:</b> <code>{clean_link}</code>\n"
		else:
			text += f"🔗 <b>Ссылка:</b> <code>{data['link']}</code>\n"
	
	if 'username' in data:
		text += f"👤 <b>Username:</b> <code>{data['username']}</code>\n"
	
	if 'number' in data:
		text += f"🔢 <b>Номер:</b> <code>{data['number']}</code>\n"
	
	if 'phone' in data:
		text += f"📱 <b>Телефон:</b> <code>{data['phone']}</code>\n"
	
	if 'clean_data' in data and 'value' in data['clean_data']:
		text += f"📋 <b>Данные:</b> <code>{data['clean_data']['value']}</code>\n"
	
	# Специфичные для типа
	if payment_type == 'card' and 'card' in data:
		card = data['card']
		card_formatted = f"{card[:4]} {card[4:8]} {card[8:12]} {card[12:]}"
		text += f"💳 <b>Карта:</b> <code>{card_formatted}</code>\n"
	
	elif payment_type == 'iban' and 'iban' in data:
		text += f"🏦 <b>IBAN:</b> <code>{data['iban']}</code>\n"
	
	text += "\n✅ <b>Всё верно?</b>"
	
	# Клавиатура с кнопками подтверждения
	keyboard = [
		[
			InlineKeyboardButton("✅ Да", callback_data="confirm_yes"),
			InlineKeyboardButton("❌ Нет", callback_data="confirm_no")
		]
	]
	
	await update.message.reply_text(
		text,
		reply_markup=InlineKeyboardMarkup(keyboard),
		parse_mode='HTML'
	)
	return CONFIRM_PAYMENT


# ============================================
# ФУНКЦИЯ 1: PAYPAL ПОКАЗ ИНСТРУКЦИИ ДЛЯ PAYPAL
# ============================================
async def method_paypal(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Показывает пример ссылки и просит ввести username"""
	query = update.callback_query  # Нажатие на инлайн-кнопку
	
	print(f"🌍 method_paypal ВЫЗВАНА с data: {update.callback_query.data}")
	print("DEBUG: Кнопка PayPal нажата, функция вызвана!")
	print(f"🌍 bankworld.py method_paypal получил: {update.callback_query.data}")
	
	await query.answer()  # убрать часики
	
	text = (
		"💶 PayPal\n\n"
		"✏️ Введите в чат Ваш PayPal <b>username</b> или ссылку\n\n"
		"📌 Например:\n"
		"• <code>paypal.me/john123</code>\n"
		"• Или просто <b>username</b> <code>john123</code>\n\n"
		"👇 Жду ваш ввод в поле чата..."
	)
	
	# 🔥 КНОПКА НАЗАД ДОЛЖНА ВЕСТИ В ГЛАВНОЕ МЕНЮ ВЫБОРА СТРАН
	keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_countries")]]
	
	await query.edit_message_text(
		text,
		reply_markup=InlineKeyboardMarkup(keyboard),
		parse_mode='Html'
	)
	return WAIT_PAYPAL


# ============================================
# ФУНКЦИЯ 2: PAYPAL ОЧИСТКА USERNAME (ВСПОМОГАТЕЛЬНАЯ)
# ============================================
def clean_paypal_username(text: str) -> str:
	"""Извлекает чистый username из любого ввода (ссылка или текст)"""
	
	# Убираем пробелы по краям
	text = text.strip()
	
	# Приводим к нижнему регистру для удобства поиска, но оригинал для username сохраним отдельно
	text_lower = text.lower()
	
	# 1. Ищем все возможные варианты ссылок PayPal
	paypal_domains = ["paypal.me/", "paypal.com/", "www.paypal.com/", "paypal.com/paypalme/",
	                  "www.paypal.com/paypalme/"]
	
	username = None
	for domain in paypal_domains:
		if domain in text_lower:
			# Нашли домен, берем всё что после него
			username = text.split(domain, 1)[-1]  # Используем split по оригинальному тексту, чтобы сохранить регистр
			break
	
	# 2. Если не нашли через домены, но есть слеш — берем последнюю часть
	if username is None and "/" in text:
		username = text.split("/")[-1]
	
	# 3. Если ничего не подошло — считаем, что это просто имя
	if username is None:
		username = text
	
	# Финальная зачистка
	username = username.strip('/ ')
	username = username.lstrip('@')
	
	# Если после всех манипуляций осталась пустая строка — возвращаем оригинал
	if not username:
		username = text.strip('/ @')
	
	return username


# ============================================
# ФУНКЦИЯ 3: PAYPAL ОБРАБОТКА ВВОДА ПОЛЬЗОВАТЕЛЯ
# ============================================
async def process_paypal_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Получает текст, очищает username, показывает подтверждение"""
	
	# ✅ ИСПРАВЛЕНО: проверяем, что пришло сообщение
	if not update.message:
		print("❌ Ошибка: нет сообщения")
		return
	
	user_input = update.message.text
	print(f"💳 bank.py получил сообщение: {user_input}")
	
	# Очищаем username
	username = clean_paypal_username(user_input)
	
	# ФОРМИРУЕМ ПОЛНУЮ ССЫЛКУ (то, что пойдет в БД)
	full_link = f"https://paypal.me/{username}"
	
	# Сохраняем
	context.user_data['payment_data'] = {
		'type': 'paypal',
		'raw_input': user_input,  # что ввел пользователь (для отладки)
		'username': username,  # чистый username
		'link': full_link,  # ПОЛНАЯ ССЫЛКА - ЭТО В БАЗУ!
		'payment_type': 'paypal'
	}
	
	# 🔥 ПОКАЗЫВАЕМ ПОДТВЕРЖДЕНИЕ С КНОПКАМИ!
	await update.message.reply_text(
		f"✅ Проверьте данные:\n\n"
		f"Ссылка: <code>{full_link}</code>\n"
		f"Username: <b>{username}</b>\n\n"
		f"👇 Всё верно?",
		reply_markup=InlineKeyboardMarkup([
			[
				InlineKeyboardButton("✅ Да", callback_data="confirm_yes"),
				InlineKeyboardButton("❌ Нет", callback_data="confirm_no")
			]
		]),
		parse_mode='HTML'
	)
	
	return CONFIRM_PAYMENT


async def save_payment_to_db(update: Update, context: ContextTypes.DEFAULT_TYPE, data: dict):
	"""Сохраняет платежные данные в БД"""
	user_id = update.effective_user.id
	
	conn = await get_db_connection()
	try:
		# Получаем страницу пользователя
		page = await conn.fetchrow(
			"SELECT id FROM pages WHERE user_id = (SELECT id FROM users WHERE telegram_id = $1)",
			user_id
		)
		
		if not page:
			print("❌ Ошибка: страница не найдена")
			return
		
		# Получаем максимальный sort_order
		max_sort = await conn.fetchval(
			"SELECT COALESCE(MAX(sort_order), 0) FROM links WHERE page_id = $1",
			page['id']
		)
		
		# Получаем тип из данных
		payment_type = data.get('type', 'paypal')
		payment_name = payment_type.replace('_', ' ').title()
		
		# ===== ОПРЕДЕЛЯЕМ КАТЕГОРИЮ =====
		# Все банковские методы идут в категорию 'transfers'
		category = 'transfers'
		# =================================
		
		# ===== ОБРЕЗАЕМ ВСЕ СТРОКИ =====
		
		# 1. Title - обычно VARCHAR(255)
		if payment_name and len(payment_name) > 255:
			payment_name = payment_name[:255]
			print(f"⚠️ payment_name обрезан до 255 символов")
		
		# 2. URL - обычно VARCHAR(500) или TEXT
		url = data.get('link', '')
		if url and len(url) > 500:
			url = url[:500]
			print(f"⚠️ URL обрезан до 500 символов")
		
		# 3. Icon - обычно VARCHAR(100)
		if payment_type and len(payment_type) > 100:
			payment_type = payment_type[:100]
			print(f"⚠️ payment_type (icon) обрезан до 100 символов")
		
		# 4. link_type - обычно VARCHAR(50)
		link_type = payment_type
		if link_type and len(link_type) > 50:
			link_type = link_type[:50]
			print(f"⚠️ link_type обрезан до 50 символов")
		
		# 5. JSON данные - подготавливаем и обрезаем
		pay_details_json = json.dumps(data)
		if len(pay_details_json) > 10000:
			pay_details_json = pay_details_json[:10000]
			print(f"⚠️ pay_details JSON обрезан до 10000 символов")
		
		await conn.execute("""
                           INSERT INTO links (page_id, title, url, icon, link_type, category,
                                              pay_details, sort_order, is_active, click_count, created_at)
                           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, true, 0, NOW())
		                   """,
		                   page['id'],
		                   payment_name,
		                   url,
		                   payment_type,
		                   link_type,
		                   category,  # ← ТЕПЕРЬ ПЕРЕМЕННАЯ ОПРЕДЕЛЕНА!
		                   pay_details_json,
		                   max_sort + 1
		                   )
		
		print(f"✅ {payment_name} сохранен для пользователя {user_id}")
	
	except Exception as e:
		print(f"❌ Ошибка сохранения: {e}")
	finally:
		await conn.close()


# ============================================
# ФУНКЦИЯ: Обработка нажатия "❌ Нет, заново" (АВТОМАТ)
# ============================================
async def confirm_no(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Универсальная отмена - возврат к началу текущего метода"""
	query = update.callback_query
	await query.answer()
	
	# Получаем тип платежа ДО очистки!
	payment_data = context.user_data.get('payment_data', {})
	payment_type = payment_data.get('type')
	
	# Очищаем данные ПОСЛЕ того как получили тип
	context.user_data.pop('payment_data', None)
	
	if not payment_type:
		print("⚠️ confirm_no: нет payment_type, возврат в главное меню")
		return await choose_country(update, context)
	
	# АВТОМАТИЧЕСКИ вызываем method_ + payment_type
	method_name = f"method_{payment_type}"
	method_func = globals().get(method_name)
	
	if method_func and callable(method_func):
		print(f"✅ Автоматический возврат к {method_name}")
		return await method_func(update, context)
	else:
		print(f"⚠️ confirm_no: функция {method_name} не найдена, возврат в главное меню")
		return await choose_country(update, context)


async def confirm_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
	print(f"🔥 confirm_yes START: {context.user_data.get('payment_data', {})}")
	
	"""Подтверждение и сохранение в базу"""
	query = update.callback_query
	await query.answer()
	
	data = context.user_data.get('payment_data', {})
	print(f"🔥 confirm_yes DATA: {data}")
	
	# Сохраняем в базу
	await save_payment_to_db(update, context, data)
	
	# Определяем тип добавленного элемента
	payment_type = data.get('type', '')
	
	# Универсальные кошельки/сервисы
	wallets = ['paypal', 'yoomoney', 'vkpay', 'monobank', 'kaspi', 'payme', 'click', 'tbcpay', 'idram']
	
	if payment_type in wallets:
		add_button_text = "➕ Добавить другой кошелек"
	else:
		add_button_text = "➕ Добавить другой банк"
	
	# 🔥 КНОПКИ ДЛЯ ДАЛЬНЕЙШИХ ДЕЙСТВИЙ
	keyboard = [
		[
			InlineKeyboardButton("📋 Моя страница", callback_data="mysite"),
			InlineKeyboardButton(add_button_text, callback_data="transfers")
		],
		[
			InlineKeyboardButton("🏠 Главное меню", callback_data="start")
		]
	]
	
	await query.edit_message_text(
		"✅ *Готово! Ссылка добавлена!*\n\n"
		"━━━━━━━━━━━━━━━━━━━\n\n"
		"📌 *Что дальше?*\n"
		"• 👀 *Моя страница* - посмотреть как это выглядит\n"
		"• ➕ *Добавить еще* - продолжить добавлять кошельки/банки\n"
		"• 🏠 *Главное меню* - вернуться в начало\n\n"
		"━━━━━━━━━━━━━━━━━━━\n"
		"👇 *Выберите действие:*",
		reply_markup=InlineKeyboardMarkup(keyboard),
		parse_mode='Markdown'
	)
	
	# Очищаем временные данные
	context.user_data.pop('payment_data', None)
	context.user_data.pop('current_country', None)
	context.user_data.pop('current_state', None)
	
	return ConversationHandler.END


# ============================================
# ФУНКЦИЯ: ПОКАЗ ИНСТРУКЦИИ С ВЫБОРОМ ТИПА
# ============================================
async def method_revolut(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Показывает выбор типа реквизитов для Revolut"""
	
	print(f"🌍 method_revolut ВЫЗВАНА с data: {update.callback_query.data}")
	print(f"💳 bank.py получил: {update.callback_query.data}")
	
	print("DEBUG: Кнопка Revolut нажата, функция вызвана!")  # Добавь это
	query = update.callback_query
	await query.answer()
	
	text = (
		"🏦 Revolut\n\n"
		"⚡ <b>Быстрый перевод</b> - только логин\n\n"
		"или\n\n"
		"💳 <b>Полные реквизиты</b> - для SEPA переводов (6 шагов)\n\n"
		"👇 Выберите какой тип реквизитов добавить: 👇"
	)
	
	keyboard = [
		[
			InlineKeyboardButton("⚡ Быстрый перевод", callback_data="revolut_quick"),
			InlineKeyboardButton("💳 Полные реквизиты", callback_data="revolut_full")
		],
		[InlineKeyboardButton("◀️ Назад", callback_data="back_to_countries")]
	]
	
	await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
	return WAIT_REVOLUT_CHOICE


# ============================================
# ФУНКЦИЯ: ОБРАБОТКА ВЫБОРА ТИПА
# ============================================
async def revolut_choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Обрабатывает выбор между быстрым вводом и SEPA реквизитами"""
	query = update.callback_query
	await query.answer()
	
	print(f"💳 bank.py получил: {update.callback_query.data}")
	
	choice = query.data
	
	if choice == "revolut_quick":
		text = (
			"🏦 Revolut (быстрый вариант)\n\n"
			"✏️ Введите в чат Ваш Revolut <b>username</b> или ссылку\n\n"
			"👇 Жду ваш ввод в поле чата..."
		)
		keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="method_revolut")]]
		await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
		return WAIT_REVOLUT_QUICK
	
	else:
		text = (
			"🏦 Revolut (полные реквизиты)\n\n"
			"Сейчас я попрошу вас ввести все данные по порядку (6 шагов).\n\n"
			"👇 Нажмите <b>Начать ввод</b>, чтобы приступить"
		)
		keyboard = [
			[InlineKeyboardButton("✅ Начать ввод", callback_data="revolut_start_full")],
			[InlineKeyboardButton("◀️ Назад", callback_data="method_revolut")]
		]
		await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
		return WAIT_REVOLUT_FULL


# ============================================
# ФУНКЦИЯ: НАЧАЛО ПОЛНОГО ВВОДА
# ============================================
async def revolut_start_full(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Инициализирует процесс сбора полных реквизитов"""
	query = update.callback_query
	await query.answer()
	
	print(f"💳 bank.py получил: {update.callback_query.data}")
	
	context.user_data['revolut_data'] = {}
	
	text = (
		"🏦 Revolut - шаг 1/6\n\n"
		"✏️ Введите в чат Ваш Revolut <b>username</b> или ссылку\n\n"
		"📌 Например:\n"
		"• <code>revolut.me/john123</code>\n"
		"• Или просто <b>username</b> <code>john123</code>\n\n"
		"👇 Жду ваш ввод в поле чата..."
	)
	
	keyboard = [[InlineKeyboardButton("◀️ Начать заново", callback_data="method_revolut")]]
	await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
	return WAIT_REVOLUT_LOGIN


# ============================================
# ФУНКЦИЯ: ОБРАБОТКА ЛОГИНА (ШАГ 1/6)
# ============================================
async def process_revolut_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Чистит и сохраняет логин, переходит к Beneficiary"""
	if not update.message or not update.message.text:
		return WAIT_REVOLUT_LOGIN
	
	print(f"💳 bank.py получил: {update.callback_query.data}")
	
	user_input = update.message.text
	login = clean_revolut_login(user_input)
	
	# Проверка на пустой ввод после чистки
	if not login:
		await update.message.reply_text("❌ Не удалось распознать логин. Попробуйте еще раз.")
		return WAIT_REVOLUT_LOGIN
	
	if len(login) > 50:
		await update.message.reply_text("❌ Слишком длинный логин (макс. 50 символов)")
		return WAIT_REVOLUT_LOGIN
	
	# Инициализируем словарь, если его вдруг нет
	if 'revolut_data' not in context.user_data:
		context.user_data['revolut_data'] = {}
	
	context.user_data['revolut_data']['login'] = login
	
	text = (
		"🏦 Revolut - шаг 2/6\n\n"
		"Введите <b>Beneficiary</b> (получатель):\n\n"
		"📌 <b>Пример:</b>\n"
		"<code>John Johnson</code>\n\n"
		"👇 Жду ваш ввод в поле чата..."
	)
	
	await update.message.reply_text(
		text,
		reply_markup=InlineKeyboardMarkup([[
			InlineKeyboardButton("◀️ начать заново", callback_data="method_revolut")
		]]),
		parse_mode='HTML'
	)
	return WAIT_REVOLUT_BENEFICIARY


# ============================================
# ФУНКЦИЯ: ОБРАБОТКА БЫСТРОГО ВВОДА (QUICK)
# ============================================
async def process_revolut_quick_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Обрабатывает быстрый ввод логина и сразу на финал"""
	user_input = update.message.text
	login = user_input.strip().lstrip('@')
	
	print(f"💳 bank.py получил: {update.callback_query.data}")
	
	if len(login) > 50:
		await update.message.reply_text("❌ Слишком длинный Revtag (макс. 50 символов)")
		return WAIT_REVOLUT_QUICK
	
	full_link = f"https://revolut.me/{login}"
	context.user_data['payment_data'] = {
		'type': 'revolut',
		'login': login,
		'link': full_link,
		'payment_type': 'revolut'
	}
	
	await update.message.reply_text(
		f"✅ <b>Проверьте данные:</b>\n\nЛогин: <b>{login}</b>\nСсылка: {full_link}\n\n👇 Всё верно?",
		reply_markup=InlineKeyboardMarkup([
			[InlineKeyboardButton("✅ Да", callback_data="confirm_yes"),
			 InlineKeyboardButton("❌ Нет", callback_data="confirm_no")]
		]),
		parse_mode='HTML'
	)
	return CONFIRM_PAYMENT


# ============================================
# ФУНКЦИЯ: ОБРАБОТКА BENEFICIARY (шаг 3/6)
# ============================================
async def process_revolut_beneficiary(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Сохраняет получателя и просит IBAN"""
	beneficiary = update.message.text.strip()
	
	print(f"💳 bank.py получил: {update.callback_query.data}")
	
	if len(beneficiary) > 50:
		await update.message.reply_text("❌ Слишком длинное имя (макс. 50 символов)")
		return WAIT_REVOLUT_BENEFICIARY
	
	context.user_data['revolut_data']['beneficiary'] = beneficiary
	
	text = (
		"🏦 Revolut - шаг 3/6\n\n"
		"Введите <b>IBAN</b>:\n\n"
		"📌 <b>Пример:</b>\n"
		"<code>LT67 3250 0982 5028 7638</code>\n\n"
		"👇 Жду ваш ввод в поле чата..."
	)
	
	await update.message.reply_text(
		text,
		reply_markup=InlineKeyboardMarkup([[
			InlineKeyboardButton("◀️ Начать заново", callback_data="method_revolut")
		]]),
		parse_mode='HTML'
	)
	return WAIT_REVOLUT_IBAN


# ============================================
# ФУНКЦИЯ: ОБРАБОТКА IBAN (шаг 4/6)
# ============================================
async def process_revolut_iban(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Сохраняет IBAN и просит BIC/SWIFT"""
	iban = update.message.text.strip()
	
	print(f"💳 bank.py получил: {update.callback_query.data}")
	
	if len(iban) > 50:
		await update.message.reply_text("❌ Слишком длинный IBAN (макс. 50 символов)")
		return WAIT_REVOLUT_IBAN
	
	context.user_data['revolut_data']['iban'] = iban
	
	text = (
		"🏦 Revolut - шаг 4/6\n\n"
		"Введите <b>BIC/SWIFT</b>:\n\n"
		"📌 <b>Пример:</b>\n"
		"<code>REVOLT21</code>\n\n"
		"👇 Жду ваш ввод в поле чата..."
	)
	
	await update.message.reply_text(
		text,
		reply_markup=InlineKeyboardMarkup([[
			InlineKeyboardButton("◀️ Начать заново", callback_data="method_revolut")
		]]),
		parse_mode='HTML'
	)
	return WAIT_REVOLUT_BIC


# ============================================
# ФУНКЦИЯ: ОБРАБОТКА BIC (шаг 5/6)
# ============================================
async def process_revolut_bic(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Сохраняет BIC и просит корреспондента"""
	bic = update.message.text.strip()
	
	if len(bic) > 50:
		await update.message.reply_text("❌ Слишком длинный BIC (макс. 50 символов)")
		return WAIT_REVOLUT_BIC
	
	context.user_data['revolut_data']['bic'] = bic
	
	text = (
		"🏦 Revolut — шаг 5/6\n\n"
		"Введите <b>Correspondent BIC</b> (если есть):\n\n"
		"📌 <b>Пример:</b>\n"
		"<code>CHASDEFX</code>\n\n"
		"👇 Жду ваш ввод в поле чата..."
	)
	
	await update.message.reply_text(
		text,
		reply_markup=InlineKeyboardMarkup([
			[
				InlineKeyboardButton("⏭️ Пропустить", callback_data="revolut_skip_correspondent"),
				InlineKeyboardButton("◀️ Начать заново", callback_data="method_revolut")
			]
		]),
		parse_mode='HTML'
	)
	return WAIT_REVOLUT_CORRESPONDENT


# ============================================
# ФУНКЦИЯ: ПРОПУСК / ВВОД КОРРЕСПОНДЕНТА
# ============================================
async def process_revolut_correspondent(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Обрабатывает ввод корреспондента и переходит к адресу"""
	user_input = update.message.text.strip()
	if len(user_input) > 50:
		await update.message.reply_text("❌ Слишком длинно (макс. 50)")
		return WAIT_REVOLUT_CORRESPONDENT
	
	context.user_data['revolut_data']['correspondent'] = user_input
	
	# Переиспользуем текст из skip-функции для единообразия
	text = (
		"🏦 Revolut — шаг 6/6\n\n"
		"Введите <b>адрес банка</b> (если есть):\n\n"
		"📌 <b>Пример:</b>\n"
		"<code>Revolut Bank UAB, Konstitucijos ave. 21B, 08130 Vilnius, Lithuania</code>\n\n"
		"👇 Жду ваш ввод в поле чата..."
	)
	
	await update.message.reply_text(
		text,
		reply_markup=InlineKeyboardMarkup([
			[
				InlineKeyboardButton("⏭️ Пропустить", callback_data="revolut_skip_address"),
				InlineKeyboardButton("◀️ Начать заново", callback_data="method_revolut")
			]
		]),
		parse_mode='HTML'
	)
	return WAIT_REVOLUT_ADDRESS


# ============================================
# ФУНКЦИЯ: ОБРАБОТКА АДРЕСА (последний шаг)
# ============================================
async def process_revolut_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Сохраняет адрес и показывает подтверждение"""
	user_input = update.message.text.strip()
	
	# Защита от слишком длинного ввода
	if len(user_input) > 250:
		await update.message.reply_text(
			"❌ Слишком длинный адрес. Пожалуйста, введите короче (макс. 250 символов)"
		)
		return WAIT_REVOLUT_ADDRESS
	
	# Сохраняем адрес если ввели что-то осмысленное
	if user_input and user_input.lower() not in ['пропустить', 'skip', '-', 'нет']:
		context.user_data['revolut_data']['address'] = user_input
	
	# Подтягиваем все собранные данные
	data = context.user_data.get('revolut_data', {})
	full_link = f"https://revolut.me/{data.get('login', '')}"
	
	# Финальная упаковка данных в основной словарь платежа
	context.user_data['payment_data'] = {
		'type': 'revolut',
		'login': data.get('login', ''),
		'beneficiary': data.get('beneficiary', ''),
		'iban': data.get('iban', ''),
		'bic': data.get('bic', ''),
		'correspondent': data.get('correspondent', ''),
		'address': data.get('address', ''),
		'link': full_link,
		'payment_type': 'revolut'
	}
	
	# Формируем итоговый текст для проверки пользователем
	text = "✅ <b>Проверьте данные:</b>\n\n"
	text += f"🔗 Ссылка: {full_link}\n"
	text += f"👤 <b>Beneficiary:</b> {data.get('beneficiary', '')}\n"
	text += f"🏦 <b>IBAN:</b> {data.get('iban', '')}\n"
	text += f"🔑 <b>BIC:</b> {data.get('bic', '')}\n"
	
	if data.get('correspondent'):
		text += f"🔄 <b>Correspondent:</b> {data.get('correspondent')}\n"
	if data.get('address'):
		text += f"📍 <b>Адрес:</b> {data.get('address')}\n"
	
	text += f"\n👇 Всё верно?"
	
	await update.message.reply_text(
		text,
		reply_markup=InlineKeyboardMarkup([
			[
				InlineKeyboardButton("✅ Да", callback_data="confirm_yes"),
				InlineKeyboardButton("❌ Нет", callback_data="confirm_no")
			]
		]),
		parse_mode='HTML'
	)
	
	# Очищаем временный словарь
	context.user_data.pop('revolut_data', None)
	
	return CONFIRM_PAYMENT


async def revolut_ask_address_step(target):
	"""Вспомогательная функция для запроса адреса (шаг 6/6)"""
	
	# Используем твой оригинальный текст с примером
	text = (
		"🏦 Revolut — шаг 6/6\n\n"
		"Введите <b>адрес банка</b> (если есть):\n\n"
		"📌 <b>Пример:</b>\n"
		"<code>Revolut Bank UAB, Konstitucijos ave. 21B, 08130 Vilnius, Lithuania</code>\n\n"
		"👇 Жду ваш ввод в поле чата..."
	)
	
	# Кнопки: пропустить или начать всё сначала
	keyboard = [
		[InlineKeyboardButton("⏭️ Пропустить", callback_data="revolut_skip_address")],
		[InlineKeyboardButton("◀️ Начать заново", callback_data="method_revolut")]
	]
	
	# Проверяем, пришел вызов от сообщения (Message) или от кнопки (CallbackQuery)
	if hasattr(target, 'message') and target.message:
		await target.message.reply_text(
			text,
			reply_markup=InlineKeyboardMarkup(keyboard),
			parse_mode='HTML'
		)
	else:
		await target.edit_message_text(
			text,
			reply_markup=InlineKeyboardMarkup(keyboard),
			parse_mode='HTML'
		)
	
	return WAIT_REVOLUT_ADDRESS


# ============================================
# ФУНКЦИЯ: ФИНАЛИЗАЦИЯ (АДРЕС И ИТОГ)
# ============================================

async def revolut_skip_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Пропускает адрес и показывает итоговое подтверждение данных"""
	query = update.callback_query
	await query.answer()
	
	# Получаем накопленные данные (адрес будет отсутствовать)
	data = context.user_data.get('revolut_data', {})
	
	# Формируем стандартную ссылку Revolut на основе введенного логина
	full_link = f"https://revolut.me/{data.get('login', '')}"
	
	# Переносим всё в основной словарь для генерации чека
	context.user_data['payment_data'] = {
		'type': 'revolut',
		'login': data.get('login', ''),
		'beneficiary': data.get('beneficiary', ''),
		'iban': data.get('iban', ''),
		'bic': data.get('bic', ''),
		'correspondent': data.get('correspondent', ''),
		'address': None,  # Адрес пропущен пользователем
		'link': full_link,
		'payment_type': 'revolut'
	}
	
	# Формируем текст подтверждения (копия из основного процесса, но с пометкой об адресе)
	text = "✅ <b>Проверьте данные:</b>\n\n"
	text += f"🔗 Ссылка: {full_link}\n"
	text += f"👤 <b>Beneficiary:</b> {data.get('beneficiary', '')}\n"
	text += f"🏦 <b>IBAN:</b> {data.get('iban', '')}\n"
	text += f"🔑 <b>BIC:</b> {data.get('bic', '')}\n"
	
	if data.get('correspondent'):
		text += f"🔄 <b>Correspondent:</b> {data.get('correspondent')}\n"
	
	text += f"📍 <b>Адрес:</b> пропущен\n"
	text += f"\n👇 Всё верно?"
	
	# Отправляем инлайн-кнопки подтверждения
	await query.edit_message_text(
		text,
		reply_markup=InlineKeyboardMarkup([
			[
				InlineKeyboardButton("✅ Да", callback_data="confirm_yes"),
				InlineKeyboardButton("❌ Нет", callback_data="confirm_no")
			]
		]),
		parse_mode='HTML'
	)
	
	# Удаляем временный буфер данных
	context.user_data.pop('revolut_data', None)
	
	return CONFIRM_PAYMENT


# ============================================
# ФУНКЦИЯ: ОЧИСТКА LOGIN
# ============================================
def clean_revolut_login(text: str) -> str:
	"""Извлекает чистый логин из любого ввода (ссылка или текст)"""
	
	# Убираем пробелы по краям
	text = text.strip()
	
	# Список доменов для поиска логина внутри URL
	revolut_domains = [
		"revolut.me/",
		"revolut.com/",
		"www.revolut.me/",
		"revolut.com/pay/",
		"revolut.com/revolut.me/"
	]
	
	login = None
	text_lower = text.lower()
	
	# Проверяем наличие известных доменов в тексте
	for domain in revolut_domains:
		if domain in text_lower:
			# Сплитим по домену и забираем правую часть (сам логин)
			login = text.split(domain, 1)[-1]
			break
	
	# Если домен не найден, но есть слэш (например, просто ссылка без протокола)
	# забираем последнюю часть после последнего слэша
	if login is None and "/" in text:
		login = text.split("/")[-1]
	
	# Если выше ничего не сработало, считаем, что прислали голый логин
	if login is None:
		login = text
	
	# Финальная очистка: убираем слэши, пробелы и символ @, если они остались
	login = login.strip('/ ')
	login = login.lstrip('@')
	
	# Если в результате очистки получилась пустая строка, возвращаем исходный текст без мусора
	if not login:
		login = text.strip('/ @')
	
	return login


# ============================================
# ФУНКЦИЯ: ВСПОМОГАТЕЛЬНАЯ ДЛЯ ФИНАЛЬНОГО ОКНА
# ============================================
async def show_revolut_final(target, context: ContextTypes.DEFAULT_TYPE):
	"""Генерирует финальное сообщение из всех собранных данных"""
	data = context.user_data.get('revolut_data', {})
	full_link = f"https://revolut.me/{data.get('login', '')}"
	
	context.user_data['payment_data'] = {
		'type': 'revolut', 'login': data.get('login'), 'beneficiary': data.get('beneficiary'),
		'iban': data.get('iban'), 'bic': data.get('bic'), 'correspondent': data.get('correspondent'),
		'address': data.get('address'), 'link': full_link, 'payment_type': 'revolut'
	}
	
	text = f"✅ <b>Проверьте данные:</b>\n\n🔗 {full_link}\n👤 <b>Beneficiary:</b> {data.get('beneficiary', '')}\n🏦 <b>IBAN:</b> {data.get('iban', '')}\n🔑 <b>BIC:</b> {data.get('bic', '')}"
	if data.get('correspondent'): text += f"\n🔄 <b>Corr:</b> {data.get('correspondent')}"
	if data.get('address'): text += f"\n📍 <b>Addr:</b> {data.get('address')}"
	
	kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Да", callback_data="confirm_yes"),
	                            InlineKeyboardButton("❌ Нет", callback_data="confirm_no")]])
	
	if hasattr(target, 'message') and target.message:
		await target.message.reply_text(text, reply_markup=kb, parse_mode='HTML')
	else:
		await target.edit_message_text(text, reply_markup=kb, parse_mode='HTML')
	
	context.user_data.pop('revolut_data', None)
	return CONFIRM_PAYMENT


# ============================================
# ФУНКЦИЯ: ПРОПУСТИТЬ CORRESPONDENT (ПЕРЕХОД К АДРЕСУ)
# ============================================
async def revolut_skip_correspondent(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Пропускает ввод Correspondent BIC и переходит к шагу 6 (адрес)"""
	query = update.callback_query
	await query.answer()
	
	# Убеждаемся, что в данных стоит None или пусто для корреспондента
	if 'revolut_data' not in context.user_data:
		context.user_data['revolut_data'] = {}
	
	context.user_data['revolut_data']['correspondent'] = None
	
	# Вызываем вспомогательную функцию запроса адреса (шаг 6/6)
	# Передаем query, чтобы функция знала, что нужно редактировать сообщение
	return await revolut_ask_address_step(query)


# ============================================
# wise ФУНКЦИЯ: ПОКАЗ ИНСТРУКЦИИ С ВЫБОРОМ ТИПА
# ============================================
async def method_wise(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Показывает выбор типа реквизитов для wise"""
	
	print(f"🌍 method_wise ВЫЗВАНА с data: {update.callback_query.data}")
	print("DEBUG: Кнопка wise нажата, функция вызвана!")  # Добавь это
	query = update.callback_query
	await query.answer()
	
	text = (
		"🏦 Wise\n\n"
		"⚡ <b>Быстрый перевод</b> - только логин\n\n"
		"или\n\n"
		"💳 <b>Полные реквизиты</b> - для SEPA переводов (6 шагов)\n\n"
		"👇 Выберите какой тип реквизитов добавить: 👇"
	)
	
	keyboard = [
		[
			InlineKeyboardButton("⚡ Быстрый перевод", callback_data="wise_quick"),
			InlineKeyboardButton("💳 Полные реквизиты", callback_data="wise_full")
		],
		[InlineKeyboardButton("◀️ Назад", callback_data="back_to_countries")]
	]
	
	await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
	return WAIT_WISE_CHOICE


# ============================================
# wise ФУНКЦИЯ: ОБРАБОТКА ВЫБОРА ТИПА
# ============================================
async def wise_choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Обрабатывает выбор между быстрым вводом и SEPA реквизитами"""
	query = update.callback_query
	await query.answer()
	
	choice = query.data
	
	if choice == "wise_quick":
		text = (
			"🏦 Wise (быстрый вариант)\n\n"
			"✏️ Введите в чат Ваш Wise <b>username</b> или ссылку\n\n"
			"👇 Жду ваш ввод в поле чата..."
		)
		keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="method_wise")]]
		await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
		return WAIT_WISE_QUICK
	
	else:
		text = (
			"🏦 Wise (полные реквизиты)\n\n"
			"Сейчас я попрошу вас ввести все данные по порядку (6 шагов).\n\n"
			"👇 Нажмите <b>Начать ввод</b>, чтобы приступить"
		)
		keyboard = [
			[InlineKeyboardButton("✅ Начать ввод", callback_data="wise_start_full")],
			[InlineKeyboardButton("◀️ Назад", callback_data="method_wise")]
		]
		await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
		return WAIT_WISE_FULL


# ============================================
# wise ФУНКЦИЯ: НАЧАЛО ПОЛНОГО ВВОДА
# ============================================
async def wise_start_full(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Инициализирует процесс сбора полных реквизитов"""
	query = update.callback_query
	await query.answer()
	
	context.user_data['wise_data'] = {}
	
	text = (
		"🏦 Wise - шаг 1/6\n\n"
		"✏️ Введите в чат Ваш Wise <b>username</b> или ссылку\n\n"
		"📌 Например:\n"
		"• <code>wise.com/pay/me/john123</code>\n"
		"• Или просто <b>username</b> <code>john123</code>\n\n"
		"👇 Жду ваш ввод в поле чата..."
	)
	
	keyboard = [[InlineKeyboardButton("◀️ Начать заново", callback_data="method_wise")]]
	await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
	return WAIT_WISE_LOGIN


# ============================================
# wise ФУНКЦИЯ: ОБРАБОТКА ЛОГИНА (ШАГ 1/6)
# ============================================
async def process_wise_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Чистит и сохраняет логин, переходит к Beneficiary"""
	if not update.message or not update.message.text:
		return WAIT_WISE_LOGIN
	
	user_input = update.message.text
	login = clean_wise_login(user_input)
	
	# Проверка на пустой ввод после чистки
	if not login:
		await update.message.reply_text("❌ Не удалось распознать логин. Попробуйте еще раз.")
		return WAIT_WISE_LOGIN
	
	if len(login) > 50:
		await update.message.reply_text("❌ Слишком длинный логин (макс. 50 символов)")
		return WAIT_WISE_LOGIN
	
	# Инициализируем словарь, если его вдруг нет
	if 'wise_data' not in context.user_data:
		context.user_data['wise_data'] = {}
	
	context.user_data['wise_data']['login'] = login
	
	text = (
		"🏦 Wise - шаг 2/6\n\n"
		"Введите <b>получателя</b>:\n\n"
		"📌 <b>Пример:</b>\n"
		"<code>Deniss Kabakovs</code>\n\n"
		"👇 Жду ваш ввод в поле чата..."
	)
	
	await update.message.reply_text(
		text,
		reply_markup=InlineKeyboardMarkup([[
			InlineKeyboardButton("◀️ начать заново", callback_data="method_wise")
		]]),
		parse_mode='HTML'
	)
	return WAIT_WISE_BENEFICIARY


# ============================================
# wise ФУНКЦИЯ: ОБРАБОТКА БЫСТРОГО ВВОДА (QUICK)
# ============================================
async def process_wise_quick_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Обрабатывает быстрый ввод логина и сразу на финал"""
	user_input = update.message.text
	login = user_input.strip().lstrip('@')
	
	if len(login) > 50:
		await update.message.reply_text("❌ Слишком длинный Revtag (макс. 50 символов)")
		return WAIT_WISE_QUICK
	
	full_link = f"https://wise.com/pay/me/{login}"
	context.user_data['payment_data'] = {
		'type': 'wise',
		'login': login,
		'link': full_link,
		'payment_type': 'wise'
	}
	
	await update.message.reply_text(
		f"✅ <b>Проверьте данные:</b>\n\nЛогин: <b>{login}</b>\nСсылка: {full_link}\n\n👇 Всё верно?",
		reply_markup=InlineKeyboardMarkup([
			[InlineKeyboardButton("✅ Да", callback_data="confirm_yes"),
			 InlineKeyboardButton("❌ Нет", callback_data="confirm_no")]
		]),
		parse_mode='HTML'
	)
	return CONFIRM_PAYMENT


# ============================================
# ФУНКЦИЯ: ОБРАБОТКА BENEFICIARY (шаг 3/6)
# ============================================
async def process_wise_beneficiary(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Сохраняет получателя и просит IBAN"""
	beneficiary = update.message.text.strip()
	
	if len(beneficiary) > 50:
		await update.message.reply_text("❌ Слишком длинное имя (макс. 50 символов)")
		return WAIT_WISE_BENEFICIARY
	
	context.user_data['wise_data']['beneficiary'] = beneficiary
	
	text = (
		"🏦 Wise - шаг 3/6\n\n"
		"Введите <b>IBAN</b>:\n\n"
		"📌 <b>Пример:</b>\n"
		"<code>LT67 3250 0982 5028 7638</code>\n\n"
		"👇 Жду ваш ввод в поле чата..."
	)
	
	await update.message.reply_text(
		text,
		reply_markup=InlineKeyboardMarkup([[
			InlineKeyboardButton("◀️ Начать заново", callback_data="method_wise")
		]]),
		parse_mode='HTML'
	)
	return WAIT_WISE_IBAN


# ============================================
# ФУНКЦИЯ: ОБРАБОТКА IBAN (шаг 4/6)
# ============================================
async def process_wise_iban(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Сохраняет IBAN и просит BIC/SWIFT"""
	iban = update.message.text.strip()
	
	if len(iban) > 50:
		await update.message.reply_text("❌ Слишком длинный IBAN (макс. 50 символов)")
		return WAIT_WISE_IBAN
	
	context.user_data['wise_data']['iban'] = iban
	
	text = (
		"🏦 Wise - шаг 4/6\n\n"
		"Введите <b>BIC/SWIFT</b>:\n\n"
		"📌 <b>Пример:</b>\n"
		"<code>REVOLT21</code>\n\n"
		"👇 Жду ваш ввод в поле чата..."
	)
	
	await update.message.reply_text(
		text,
		reply_markup=InlineKeyboardMarkup([[
			InlineKeyboardButton("◀️ Начать заново", callback_data="method_wise")
		]]),
		parse_mode='HTML'
	)
	return WAIT_WISE_BIC


# ============================================
# wise ФУНКЦИЯ: ОБРАБОТКА BIC (шаг 5/6)
# ============================================
async def process_wise_bic(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Сохраняет BIC и просит корреспондента"""
	bic = update.message.text.strip()
	
	if len(bic) > 50:
		await update.message.reply_text("❌ Слишком длинный BIC (макс. 50 символов)")
		return WAIT_REVOLUT_BIC
	
	context.user_data['wise_data']['bic'] = bic
	
	text = (
		"🏦 Wise — шаг 5/6\n\n"
		"Введите <b>Correspondent BIC</b> (если есть):\n\n"
		"📌 <b>Пример:</b>\n"
		"<code>CHASDEFX</code>\n\n"
		"👇 Жду ваш ввод в поле чата..."
	)
	
	await update.message.reply_text(
		text,
		reply_markup=InlineKeyboardMarkup([
			[
				InlineKeyboardButton("⏭️ Пропустить", callback_data="wise_skip_correspondent"),
				InlineKeyboardButton("◀️ Начать заново", callback_data="method_wise")
			]
		]),
		parse_mode='HTML'
	)
	return WAIT_WISE_CORRESPONDENT


# ============================================
# wise ФУНКЦИЯ: ПРОПУСК / ВВОД КОРРЕСПОНДЕНТА
# ============================================
async def process_wise_correspondent(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Обрабатывает ввод корреспондента и переходит к адресу"""
	user_input = update.message.text.strip()
	if len(user_input) > 50:
		await update.message.reply_text("❌ Слишком длинно (макс. 50)")
		return WAIT_WISE_CORRESPONDENT
	
	context.user_data['wise_data']['correspondent'] = user_input
	
	# Переиспользуем текст из skip-функции для единообразия
	text = (
		"🏦 Wise — шаг 6/6\n\n"
		"Введите <b>адрес банка</b> (если есть):\n\n"
		"📌 <b>Пример:</b>\n"
		"<code>Wise, Rue du Trone 100, 3rd floor, Brussels, 1050, Belgium</code>\n\n"
		"👇 Жду ваш ввод в поле чата..."
	)
	
	await update.message.reply_text(
		text,
		reply_markup=InlineKeyboardMarkup([
			[
				InlineKeyboardButton("⏭️ Пропустить", callback_data="wise_skip_address"),
				InlineKeyboardButton("◀️ Начать заново", callback_data="method_wise")
			]
		]),
		parse_mode='HTML'
	)
	return WAIT_WISE_ADDRESS


# ============================================
# wise ФУНКЦИЯ: ОБРАБОТКА АДРЕСА (последний шаг)
# ============================================
async def process_wise_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Сохраняет адрес и показывает подтверждение"""
	user_input = update.message.text.strip()
	
	# Защита от слишком длинного ввода
	if len(user_input) > 250:
		await update.message.reply_text(
			"❌ Слишком длинный адрес. Пожалуйста, введите короче (макс. 250 символов)"
		)
		return WAIT_WISE_ADDRESS
	
	# Сохраняем адрес если ввели что-то осмысленное
	if user_input and user_input.lower() not in ['пропустить', 'skip', '-', 'нет']:
		context.user_data['wise_data']['address'] = user_input
	
	# Подтягиваем все собранные данные
	data = context.user_data.get('wise_data', {})
	full_link = f"https://wise.com/pay/me/{data.get('login', '')}"
	
	# Финальная упаковка данных в основной словарь платежа
	context.user_data['payment_data'] = {
		'type': 'wise',
		'login': data.get('login', ''),
		'beneficiary': data.get('beneficiary', ''),
		'iban': data.get('iban', ''),
		'bic': data.get('bic', ''),
		'correspondent': data.get('correspondent', ''),
		'address': data.get('address', ''),
		'link': full_link,
		'payment_type': 'wise'
	}
	
	# Формируем итоговый текст для проверки пользователем
	text = "✅ <b>Проверьте данные:</b>\n\n"
	text += f"🔗 Ссылка: {full_link}\n"
	text += f"👤 <b>Получатель:</b> {data.get('beneficiary', '')}\n"
	text += f"🏦 <b>IBAN:</b> {data.get('iban', '')}\n"
	text += f"🔑 <b>BIC:</b> {data.get('bic', '')}\n"
	
	if data.get('correspondent'):
		text += f"🔄 <b>Correspondent:</b> {data.get('correspondent')}\n"
	if data.get('address'):
		text += f"📍 <b>Адрес:</b> {data.get('address')}\n"
	
	text += f"\n👇 Всё верно?"
	
	await update.message.reply_text(
		text,
		reply_markup=InlineKeyboardMarkup([
			[
				InlineKeyboardButton("✅ Да", callback_data="confirm_yes"),
				InlineKeyboardButton("❌ Нет", callback_data="confirm_no")
			]
		]),
		parse_mode='HTML'
	)
	
	# Очищаем временный словарь
	context.user_data.pop('wise_data', None)
	
	return CONFIRM_PAYMENT


async def wise_ask_address_step(target):
	"""Вспомогательная функция для запроса адреса (шаг 6/6)"""
	
	# Используем твой оригинальный текст с примером
	text = (
		"🏦 Wise — шаг 6/6\n\n"
		"Введите <b>адрес банка</b> (если есть):\n\n"
		"📌 <b>Пример:</b>\n"
		"<code>Wise, Rue du Trone 100, 3rd floor, Brussels, 1050, Belgium</code>\n\n"
		"👇 Жду ваш ввод в поле чата..."
	)
	
	# Кнопки: пропустить или начать всё сначала
	keyboard = [
		[InlineKeyboardButton("⏭️ Пропустить", callback_data="wise_skip_address")],
		[InlineKeyboardButton("◀️ Начать заново", callback_data="method_wise")]
	]
	
	# Проверяем, пришел вызов от сообщения (Message) или от кнопки (CallbackQuery)
	if hasattr(target, 'message') and target.message:
		await target.message.reply_text(
			text,
			reply_markup=InlineKeyboardMarkup(keyboard),
			parse_mode='HTML'
		)
	else:
		await target.edit_message_text(
			text,
			reply_markup=InlineKeyboardMarkup(keyboard),
			parse_mode='HTML'
		)
	
	return WAIT_WISE_ADDRESS


# ============================================
# wise ФУНКЦИЯ: ФИНАЛИЗАЦИЯ (АДРЕС И ИТОГ)
# ============================================

async def wise_skip_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Пропускает адрес и показывает итоговое подтверждение данных"""
	query = update.callback_query
	await query.answer()
	
	# Получаем накопленные данные (адрес будет отсутствовать)
	data = context.user_data.get('wise_data', {})
	
	# Формируем стандартную ссылку Wise на основе введенного логина
	full_link = f"https://wise.com/pay/me/{data.get('login', '')}"
	
	# Переносим всё в основной словарь для генерации чека
	context.user_data['payment_data'] = {
		'type': 'wise',
		'login': data.get('login', ''),
		'beneficiary': data.get('beneficiary', ''),
		'iban': data.get('iban', ''),
		'bic': data.get('bic', ''),
		'correspondent': data.get('correspondent', ''),
		'address': None,  # Адрес пропущен пользователем
		'link': full_link,
		'payment_type': 'wise'
	}
	
	# Формируем текст подтверждения (копия из основного процесса, но с пометкой об адресе)
	text = "✅ <b>Проверьте данные:</b>\n\n"
	text += f"🔗 Ссылка: {full_link}\n"
	text += f"👤 <b>Получатель:</b> {data.get('beneficiary', '')}\n"
	text += f"🏦 <b>IBAN:</b> {data.get('iban', '')}\n"
	text += f"🔑 <b>BIC:</b> {data.get('bic', '')}\n"
	
	if data.get('correspondent'):
		text += f"🔄 <b>Correspondent:</b> {data.get('correspondent')}\n"
	
	text += f"📍 <b>Адрес:</b> пропущен\n"
	text += f"\n👇 Всё верно?"
	
	# Отправляем инлайн-кнопки подтверждения
	await query.edit_message_text(
		text,
		reply_markup=InlineKeyboardMarkup([
			[
				InlineKeyboardButton("✅ Да", callback_data="confirm_yes"),
				InlineKeyboardButton("❌ Нет", callback_data="confirm_no")
			]
		]),
		parse_mode='HTML'
	)
	
	# Удаляем временный буфер данных
	context.user_data.pop('wise_data', None)
	
	return CONFIRM_PAYMENT


# ============================================
# wise ФУНКЦИЯ: ОЧИСТКА LOGIN
# ============================================
def clean_wise_login(text: str) -> str:
	"""Извлекает чистый логин из любого ввода (ссылка или текст)"""
	
	# Убираем пробелы по краям
	text = text.strip()
	
	# Список доменов для поиска логина внутри URL
	wise_domains = [
		"wise.com/pay/me/",
		"wise.com/",
		"www.wise.me/",
		"wise.com/pay/",
		"wise.com/wise.me/"
	]
	
	login = None
	text_lower = text.lower()
	
	# Проверяем наличие известных доменов в тексте
	for domain in wise_domains:
		if domain in text_lower:
			# Сплитим по домену и забираем правую часть (сам логин)
			login = text.split(domain, 1)[-1]
			break
	
	# Если домен не найден, но есть слэш (например, просто ссылка без протокола)
	# забираем последнюю часть после последнего слэша
	if login is None and "/" in text:
		login = text.split("/")[-1]
	
	# Если выше ничего не сработало, считаем, что прислали голый логин
	if login is None:
		login = text
	
	# Финальная очистка: убираем слэши, пробелы и символ @, если они остались
	login = login.strip('/ ')
	login = login.lstrip('@')
	
	# Если в результате очистки получилась пустая строка, возвращаем исходный текст без мусора
	if not login:
		login = text.strip('/ @')
	
	return login


# ============================================
# wise ФУНКЦИЯ: ВСПОМОГАТЕЛЬНАЯ ДЛЯ ФИНАЛЬНОГО ОКНА
# ============================================
async def show_wise_final(target, context: ContextTypes.DEFAULT_TYPE):
	"""Генерирует финальное сообщение из всех собранных данных"""
	data = context.user_data.get('wise_data', {})
	full_link = f"https://wise.com/pay/me/{data.get('login', '')}"
	
	context.user_data['payment_data'] = {
		'type': 'wise', 'login': data.get('login'), 'beneficiary': data.get('beneficiary'),
		'iban': data.get('iban'), 'bic': data.get('bic'), 'correspondent': data.get('correspondent'),
		'address': data.get('address'), 'link': full_link, 'payment_type': 'wise'
	}
	
	text = f"✅ <b>Проверьте данные:</b>\n\n🔗 {full_link}\n👤 <b>Получатель:</b> {data.get('beneficiary', '')}\n🏦 <b>IBAN:</b> {data.get('iban', '')}\n🔑 <b>BIC:</b> {data.get('bic', '')}"
	if data.get('correspondent'): text += f"\n🔄 <b>Corr:</b> {data.get('correspondent')}"
	if data.get('address'): text += f"\n📍 <b>Addr:</b> {data.get('address')}"
	
	kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Да", callback_data="confirm_yes"),
	                            InlineKeyboardButton("❌ Нет", callback_data="confirm_no")]])
	
	if hasattr(target, 'message') and target.message:
		await target.message.reply_text(text, reply_markup=kb, parse_mode='HTML')
	else:
		await target.edit_message_text(text, reply_markup=kb, parse_mode='HTML')
	
	context.user_data.pop('wise_data', None)
	return CONFIRM_PAYMENT


# ============================================
# wise ФУНКЦИЯ: ПРОПУСТИТЬ CORRESPONDENT (ПЕРЕХОД К АДРЕСУ)
# ============================================
async def wise_skip_correspondent(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Пропускает ввод Correspondent BIC и переходит к шагу 6 (адрес)"""
	query = update.callback_query
	await query.answer()
	
	# Убеждаемся, что в данных стоит None или пусто для корреспондента
	if 'revolut_data' not in context.user_data:
		context.user_data['wise_data'] = {}
	
	context.user_data['wise_data']['correspondent'] = None
	
	# Вызываем вспомогательную функцию запроса адреса (шаг 6/6)
	# Передаем query, чтобы функция знала, что нужно редактировать сообщение
	return await revolut_ask_address_step(query)


async def method_swift(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()
	
	text = "🏦 **SWIFT реквизиты**\n\n"
	text += "📌 **Формат (можно скопировать):**\n"
	text += "```\n"
	text += "Получатель: \n"
	text += "IBAN: \n"
	text += "SWIFT/BIC: \n"
	text += "Банк: \n"
	text += "Адрес банка: \n"
	text += "```\n\n"
	text += "✏️ **Введи свои реквизиты**\n"
	text += "(в любом формате)"
	
	keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="country_swift")]]
	
	await query.edit_message_text(
		text,
		reply_markup=InlineKeyboardMarkup(keyboard),
		parse_mode='Markdown'
	)
	return WAIT_SWIFT


async def method_iban(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()
	
	text = "🏦 **IBAN**\n\n"
	text += "📌 **Пример:**\n"
	text += "`BE48 9677 8076 8827`\n\n"
	text += "✏️ **Введи свой IBAN:**"
	
	keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="country_swift")]]
	
	await query.edit_message_text(
		text,
		reply_markup=InlineKeyboardMarkup(keyboard),
		parse_mode='Markdown'
	)
	return WAIT_IBAN


# --- Другие страны ---
async def method_other_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Для других стран - свободный ввод"""
	# Эта функция вызывается из country_other
	pass


# ============================================
# ОБРАБОТЧИКИ ВВОДА ДАННЫХ
# ============================================

async def process_card_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Шаг 2: Универсальный приемщик (Текст банка или Номер карты)"""
    text = update.message.text.strip()
    state = context.user_data.get('current_state')
    
    # Если это ввод названия банка после телефона (СБП Россия)
    if state == WAIT_RUSSIA_DETAILS:
        data = context.user_data.get('payment_data', {})
        data['bank_name'] = text  # Дописываем банк к телефону
        context.user_data['payment_data'] = data
        
        # Теперь данные полные, вызываем подтверждение
        from bot.bank import show_confirmation
        return await show_confirmation(update, context)

    # Логика для обычных КАРТ (проверка 16 цифр)
    if "," in text:
       card, name = text.split(",", 1)
       card = card.strip().replace(" ", "")
       name = name.strip()
    else:
       card = text.strip().replace(" ", "")
       name = None
    
    card_clean = ''.join(filter(str.isdigit, card))
    
    if len(card_clean) != 16:
       await update.message.reply_text("❌ Номер карты должен содержать 16 цифр. Попробуйте еще:")
       return state
    
    context.user_data['payment_data'] = {
       'type': 'card',
       'card': card_clean,
       'name': name,
       'country': context.user_data.get('current_country')
    }
    
    from bot.bank import show_confirmation
    return await show_confirmation(update, context)

async def process_phone_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Шаг 1: Получаем телефон и переходим к вводу банка (СБП)"""
    text = update.message.text.strip()
    
    # Очистка номера
    phone = ''.join(filter(lambda x: x.isdigit() or x == '+', text))
    
    # Сохраняем во временный словарь
    context.user_data['payment_data'] = {
       'type': 'phone',
       'phone': phone,
       'country': context.user_data.get('current_country')
    }
    
    # Спрашиваем название банка
    await update.message.reply_text(
        "Введите название вашего банка (например: Сбербанк, Тинькофф, СБП):"
    )
    
    # Переходим в стейт ожидания названия банка
    return WAIT_RUSSIA_DETAILS

async def process_iban_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Обработка ввода IBAN"""
	text = update.message.text.strip()
	
	context.user_data['payment_data'] = {
		'type': 'iban',
		'iban': text,
		'country': context.user_data.get('current_country')
	}
	
	return await show_confirmation(update, context)


async def process_swift_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Обработка ввода SWIFT реквизитов"""
	text = update.message.text.strip()
	
	context.user_data['payment_data'] = {
		'type': 'swift',
		'raw': text,
		'country': context.user_data.get('current_country')
	}
	
	return await show_confirmation(update, context)


async def process_wise_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Обработка ввода Wise данных"""
	text = update.message.text.strip()
	
	context.user_data['payment_data'] = {
		'type': 'wise',
		'data': text,
		'country': 'international'
	}
	
	return await show_confirmation(update, context)


async def back_to_countries(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()
	
	# Просто показываем меню стран
	await choose_country(update, context)
	
	# ВАЖНО: НЕ завершаем диалог, а переходим в SELECT_COUNTRY
	return SELECT_COUNTRY  # ← ИСПРАВЛЕНО!


async def process_other_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Обработка ввода для 'Другой страны'"""
	text = update.message.text.strip()
	
	if not text:
		await update.message.reply_text("❌ Введите данные")
		return WAIT_OTHER_DETAILS
	
	context.user_data['payment_data'] = {
		'type': 'other',
		'raw': text,
		'country': 'other'
	}
	
	return await show_confirmation(update, context)
