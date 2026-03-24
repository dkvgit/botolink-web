# bot/bankworld.py

import json
import logging

from bot.states import (
	WAIT_METHOD_SELECTION,
	WAIT_FILLING_DATA,
	WAIT_FIELD_INPUT,
	WAIT_FINAL_CONFIRM
)
from core.config import APP_URL  # Импортируем из config
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
	ConversationHandler,
	CallbackQueryHandler,
	MessageHandler,
	filters,
	ContextTypes
)

# Настройка логирования
logger = logging.getLogger(__name__)

# ============================================
# СЛОВАРЬ МЕТОДОВ ПО СТРАНАМ
# ============================================
COUNTRY_METHODS = {
	# 🌍 УНИВЕРСАЛЬНЫЕ МЕТОДЫ (без привязки к стране)
	"universal": [
		{"id": "yoomoney", "name": "🇷🇺 ЮMoney", "fields": ["wallet"]},
		{"id": "vkpay", "name": "🇷🇺 VK Pay", "fields": ["phone", "vk_id"]},
		{"id": "paypal", "name": "🌐 PayPal", "fields": ["username"]},
		{"id": "wise", "name": "🇪🇺 Wise", "fields": ["email", "iban"]},
		{"id": "revolut", "name": "🇪🇺 Revolut", "fields": ["tag", "iban"]},
		{"id": "monobank", "name": "🇺🇦 Монобанк", "fields": ["card"]},
		{"id": "kaspi", "name": "🇰🇿 Kaspi.kz", "fields": ["card", "phone"]},
		{"id": "payme", "name": "🇺🇿 Payme", "fields": ["phone"]},
		{"id": "click", "name": "🇺🇿 Click", "fields": ["phone"]},
		{"id": "tbcpay", "name": "🇬🇪 TBC Pay", "fields": ["card", "phone"]},
		{"id": "idram", "name": "🇦🇲 Idram", "fields": ["card", "phone"]}
	],
	
	# 🇪🇺 ПРИБАЛТИКА (SEPA)
	"lithuania": [
		{"id": "card_lithuania", "name": "Банковская карта", "fields": ["card_number"]},
		{"id": "iban_lithuania", "name": "Банковский счет (SEPA)", "fields": ["iban", "bic", "beneficiary"]}
	],
	"latvia": [
		{"id": "card_latvia", "name": "Банковская карта", "fields": ["card_number"]},
		{"id": "iban_latvia", "name": "Банковский счет (SEPA)", "fields": ["iban", "bic", "beneficiary"]}
	],
	"estonia": [
		{"id": "card_estonia", "name": "Банковская карта", "fields": ["card_number"]},
		{"id": "iban_estonia", "name": "Банковский счет (SEPA)", "fields": ["iban", "bic", "beneficiary"]}
	],
	
	# 🇺🇸 США
	"usa": [
		{"id": "card_usa", "name": "Карта (+ ZIP)", "fields": ["card_number", "card_holder", "zip"]},
		{"id": "ach_usa", "name": "ACH (местный)", "fields": ["routing", "account", "beneficiary"]},
		{"id": "wire_usa", "name": "Wire (международный)", "fields": ["swift", "account", "beneficiary"]}
	],
	
	# 🇷🇺 РОССИЯ
	"russia": [
		{"id": "card_russia", "name": "Банковская карта", "fields": ["card_number"]},
		{"id": "phone_russia", "name": "По номеру телефона (СБП)", "fields": ["phone"]},
		{"id": "account_russia", "name": "Банковский счет", "fields": ["account_number", "bik", "beneficiary"]}
	],
	
	# 🇺🇦 УКРАИНА
	"ukraine": [
		{"id": "card_ukraine", "name": "Банковская карта", "fields": ["card_number"]},
		{"id": "iban_ukraine", "name": "IBAN счет", "fields": ["iban", "beneficiary"]}
	],
	
	# 🇧🇾 БЕЛАРУСЬ
	"belarus": [
		{"id": "card_belarus", "name": "Банковская карта", "fields": ["card_number"]},
		{"id": "iban_belarus", "name": "IBAN счет", "fields": ["iban", "bic", "beneficiary"]}
	],
	
	# 🇰🇿 КАЗАХСТАН
	"kazakhstan": [
		{"id": "card_kazakhstan", "name": "Банковская карта", "fields": ["card_number"]},
		{"id": "iban_kazakhstan", "name": "IBAN счет", "fields": ["iban", "bic", "beneficiary"]}
	],
	
	# 🇦🇲 АРМЕНИЯ
	"armenia": [
		{"id": "card_armenia", "name": "Банковская карта", "fields": ["card_number"]},
		{"id": "account_armenia", "name": "🏦 Банковский счет", "fields": ["account", "bic", "beneficiary"]}
	],
	
	# 🇦🇿 АЗЕРБАЙДЖАН
	"azerbaijan": [
		{"id": "card_azerbaijan", "name": "Банковская карта", "fields": ["card_number"]},
		{"id": "iban_azerbaijan", "name": "IBAN счет", "fields": ["iban", "bic", "beneficiary"]}
	],
	
	# 🇬🇪 ГРУЗИЯ
	"georgia": [
		{"id": "card_georgia", "name": "Банковская карта", "fields": ["card_number"]},
		{"id": "iban_georgia", "name": "IBAN счет", "fields": ["iban", "bic", "beneficiary"]}
	],
	
	# 🇲🇩 МОЛДОВА
	"moldova": [
		{"id": "card_moldova", "name": "Банковская карта", "fields": ["card_number"]},
		{"id": "iban_moldova", "name": "IBAN счет", "fields": ["iban", "bic", "beneficiary"]}
	],
	
	# 🇺🇿 УЗБЕКИСТАН
	"uzbekistan": [
		{"id": "card_uzbekistan", "name": "Банковская карта", "fields": ["card_number"]},
		{"id": "phone_uzbekistan", "name": "По номеру телефона", "fields": ["phone"]},
		{"id": "account_uzbekistan", "name": "Банковский счет", "fields": ["account", "mfo", "beneficiary"]}
	],
	
	# 🇹🇯 ТАДЖИКИСТАН
	"tajikistan": [
		{"id": "card_tajikistan", "name": "Банковская карта", "fields": ["card_number"]},
		{"id": "account_tajikistan", "name": "Банковский счет", "fields": ["account", "bic", "beneficiary"]}
	],
	
	# 🇰🇬 КЫРГЫЗСТАН
	"kyrgyzstan": [
		{"id": "card_kyrgyzstan", "name": "Банковская карта", "fields": ["card_number"]},
		{"id": "account_kyrgyzstan", "name": "Банковский счет", "fields": ["account", "bic", "beneficiary"]}
	],
	
	# 🇹🇲 ТУРКМЕНИСТАН
	"turkmenistan": [
		{"id": "card_turkmenistan", "name": "Банковская карта", "fields": ["card_number"]},
		{"id": "account_turkmenistan", "name": "Банковский счет", "fields": ["account", "bic", "beneficiary"]}
	],
	
	# 🇻🇳 ВЬЕТНАМ
	"vietnam": [
		{"id": "non_res_vietnam", "name": "Счет нерезидента", "fields": ["account_number"]},
		{"id": "card_vietnam", "name": "Банковская карта", "fields": ["card_number"]},
		{"id": "account_vietnam", "name": "Банковский счет", "fields": ["account", "bic", "beneficiary"]}
	]
}
# ============================================
# НАЗВАНИЯ СТРАН ДЛЯ ОТОБРАЖЕНИЯ
# ============================================
COUNTRY_NAMES = {
	"universal": "🌍 Универсальные сервисы",  # Добавь это
	"lithuania": "🇱🇹 Литва",
	"latvia": "🇱🇻 Латвия",
	"estonia": "🇪🇪 Эстония",
	"usa": "🇺🇸 США",
	"russia": "🇷🇺 Россия",
	"ukraine": "🇺🇦 Украина",
	"belarus": "🇧🇾 Беларусь",
	"kazakhstan": "🇰🇿 Казахстан",
	"armenia": "🇦🇲 Армения",
	"azerbaijan": "🇦🇿 Азербайджан",
	"georgia": "🇬🇪 Грузия",
	"moldova": "🇲🇩 Молдова",
	"uzbekistan": "🇺🇿 Узбекистан",
	"tajikistan": "🇹🇯 Таджикистан",
	"kyrgyzstan": "🇰🇬 Кыргызстан",
	"turkmenistan": "🇹🇲 Туркменистан",
	"vietnam": "🇻🇳 Вьетнам"
}

# ============================================
# НАЗВАНИЯ ПОЛЕЙ ДЛЯ ОТОБРАЖЕНИЯ
# ============================================
FIELD_NAMES = {
	"card_number": "Номер карты",
	"card_holder": "Имя держателя",
	"phone": "Номер телефона",
	"account_number": "Номер счета",
	"account": "Номер счета",
	"bik": "БИК",
	"iban": "IBAN",
	"bic": "BIC",
	"beneficiary": "Получатель",
	"bank_name": "Название банка",
	"routing": "Routing Number",
	"swift": "SWIFT код",
	"zip": "ZIP код",
	"mfo": "МФО"
}

# ============================================
# ПРИМЕРЫ ДЛЯ ПОЛЕЙ
# ============================================
FIELD_EXAMPLES = {
	"card_number": "Пример: 1234 5678 9012 3456",
	"phone": "Пример: +79123456789",
	"account_number": "Пример: 40817810000000012345",
	"account": "Пример: 40817810000000012345",
	"bik": "Пример: 044525225",
	"iban": "Пример: LT67 3250 0982 5028 7638",
	"bic": "Пример: REVOLT21",
	"beneficiary": "Пример: Ivan Petrov",
	"bank_name": "Пример: Сбербанк",
	"routing": "Пример: 021000021",
	"swift": "Пример: CHASUS33",
	"zip": "Пример: 10001",
	"mfo": "Пример: 12345"
}


# ============================================
# СОЗДАНИЕ CONVERSATIONHANDLER
# ============================================


# Обработчик для всех country_* кнопок
async def handle_country_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()
	
	print(f"🌍 bankworld.py получил: {update.callback_query.data}")
	
	country = query.data.replace("country_", "")  # получаем "lithuania", "latvia" и т.д.
	
	# Сохраняем выбранную страну
	context.user_data['selected_country'] = country
	
	# Вызываем функцию из bankworld.py для показа методов
	return await show_country_methods(update, context)


async def show_country_methods(update: Update, context: ContextTypes.DEFAULT_TYPE):
	# show_country_methods
	"""Показывает доступные методы для выбранной страны с чекбоксами"""
	query = update.callback_query
	await query.answer()
	
	print(f"🌍 bankworld.py получил: {update.callback_query.data}")
	
	print(f"🔥 callback_data: {query.data}")
	
	# Если это кнопка "Назад" - просто возвращаемся в меню выбора стран
	if query.data == "back_to_countries":
		from bot.bank import choose_country
		return await choose_country(update, context)  # ✅ добавили return
	
	# Получаем страну из callback ИЛИ из user_data
	if query.data.startswith("country_"):
		country = query.data.replace("country_", "")
		context.user_data['selected_country'] = country
	else:
		# Если вызов из toggle_method - берем страну из user_data
		country = context.user_data.get('selected_country')
	
	# Если страны нет - выходим
	if not country:
		await query.edit_message_text("❌ Ошибка: страна не выбрана")
		return WAIT_METHOD_SELECTION
	
	# Берем методы для этой страны
	methods = COUNTRY_METHODS.get(country, [])
	selected = context.user_data.get('selected_methods', [])
	
	# Название страны из COUNTRY_NAMES
	country_display = COUNTRY_NAMES.get(country, country.upper())
	
	text = f"<b>📍 {country_display}</b>\n"
	text += "───────────────────\n"
	text += "<b>Выберите способы получения переводов:</b>\n\n"
	text += "• Можно выбрать <b>сразу несколько</b> вариантов\n"
	text += "• Нажмите на нужный пункт, чтобы отметить его (✔️)\n"
	text += "• Когда закончите выбор — нажмите кнопку <b>«Далее»</b>\n\n"
	text += "👇 <b>Доступные методы:</b>"
	
	if not methods:
		text += "❌ Для этой страны пока нет доступных методов"
		keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_countries")]]
		await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
		return WAIT_METHOD_SELECTION
	
	keyboard = []
	for method in methods:
		prefix = "✅ " if method['id'] in selected else ""
		button_text = f"{prefix}{method['name']}"
		keyboard.append([
			InlineKeyboardButton(button_text, callback_data=f"method_{country}_{method['id']}")
		])
	
	if selected:
		keyboard.append([InlineKeyboardButton(" Далее  ➡️➡️➡️", callback_data="start_filling")])
	else:
		keyboard.append([InlineKeyboardButton("👆 Отметь нужные 👆", callback_data="ignore")])
	
	keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_countries")])
	
	await query.edit_message_text(
		text=text,
		reply_markup=InlineKeyboardMarkup(keyboard),
		parse_mode='HTML'
	)
	
	return WAIT_METHOD_SELECTION


async def toggle_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Обрабатывает выбор/отмену метода"""
	query = update.callback_query
	
	print(f"🌍 bankworld.py получил: {update.callback_query.data}")
	print(f"🔥 callback_data: {query.data}")
	
	await query.answer()
	
	# Инициализируем переменные
	country = None
	method_id = None
	
	# Парсим callback_data
	if query.data.startswith("method_"):
		# Убираем "method_" и получаем остаток
		rest = query.data[7:]  # убираем "method_"
		print(f"🔍 rest после method_: {rest}")
		
		# Разделяем на страну и method_id
		underscore_index = rest.find('_')
		if underscore_index != -1:
			# Формат: method_страна_метод (например method_russia_card)
			country = rest[:underscore_index]
			method_id = rest[underscore_index + 1:]
			print(f"🔍 Найден формат со страной: country={country}, method_id={method_id}")
		else:
			# Формат: method_метод (без страны - например method_yoomoney, method_vkpay)
			country = "universal"  # или None, но для логики лучше задать значение
			method_id = rest
			print(f"🔍 Найден универсальный метод без страны: method_id={method_id}")
	
	# Проверяем, что удалось распарсить
	if not method_id:
		print(f"❌ Не удалось распарсить method_id из callback_data: {query.data}")
		return await show_country_methods(update, context)
	
	# Для универсальных методов без страны
	if country == "universal":
		context.user_data['selected_country'] = "universal"
		print(f"🌍 Универсальный метод, страна не указана")
	else:
		context.user_data['selected_country'] = country
	
	selected = context.user_data.get('selected_methods', [])
	
	# Для универсальных методов используем просто method_id
	# Для методов со страной используем полный method_id
	if country == "universal":
		method_key = method_id
		print(f"🔑 Ключ для универсального метода: {method_key}")
	else:
		method_key = method_id
		print(f"🔑 Ключ для метода со страной: {method_key}")
	
	if method_key in selected:
		selected.remove(method_key)
		print(f"❌ Убрали метод: {method_key}")
	else:
		selected.append(method_key)
		print(f"✅ Добавили метод: {method_key}")
	
	context.user_data['selected_methods'] = selected
	print(f"📋 Текущие методы ({len(selected)}): {selected}")
	print(f"🌍 Текущая страна: {context.user_data.get('selected_country')}, метод: {method_id}")
	
	# Важно: возвращаем show_country_methods для обновления отображения
	state = await show_country_methods(update, context)
	return state


# ============================================
# ФУНКЦИИ ПОМОЩНИКИ
# ============================================
def get_method_info(country: str, method_id: str) -> dict:
	"""Возвращает информацию о методе по стране и ID"""
	
	methods = COUNTRY_METHODS.get(country, [])
	for method in methods:
		if method['id'] == method_id:
			return method
	return None


def get_field_display_name(field: str) -> str:
	"""Возвращает человеческое название поля"""
	return FIELD_NAMES.get(field, field)


def get_field_example(field: str) -> str:
	"""Возвращает пример для поля"""
	return FIELD_EXAMPLES.get(field, "")


# ============================================
# ШАГ 3: НАЧАЛО ЗАПОЛНЕНИЯ ДАННЫХ
# ============================================
async def start_filling(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает пошаговое заполнение выбранных методов"""
    query = update.callback_query
    
    print(f"🌍 bankworld.py получил: {update.callback_query.data}")
    print(f"🔥 callback_data: {query.data}")
    
    # Проверяем активный диалог
    current_conv = context.user_data.get('conversation_key')
    print(f"🔍 Активный диалог: {current_conv}")
    print(f"🔍 Все user_data keys: {list(context.user_data.keys())}")
    
    await query.answer()
    
    selected_methods = context.user_data.get('selected_methods', [])
    
    if not selected_methods:
        await query.edit_message_text("❌ Вы не выбрали ни одного способа")
        print(f"🔵 start_filling ВОЗВРАЩАЕТ: {WAIT_METHOD_SELECTION}")
        return WAIT_METHOD_SELECTION
    
    # Создаем очередь для заполнения
    context.user_data['filling_queue'] = selected_methods.copy()
    context.user_data['collected_methods'] = {}  # Сюда сохраним все данные
    context.user_data['current_field_index'] = 0  # Добавляем для безопасности
    
    # Начинаем с первого метода и возвращаем результат
    result = await ask_next_method(query, context)
    print(f"🔵 start_filling ВОЗВРАЩАЕТ: {result}")
    return result  # Возвращаем WAIT_FIELD_INPUT





async def ask_next_method(query_or_update, context):
    """Запрашивает данные для следующего метода или показывает итог"""
    queue = context.user_data.get('filling_queue', [])
    
    # 1. ЕСЛИ ОЧЕРЕДЬ ПУСТА — ПОКАЗЫВАЕМ ФИНАЛЬНЫЙ ЭКРАН
    if not queue:
        print("🏁 Очередь пуста, переходим к финалу")
        # Убедись, что show_filling_complete возвращает WAIT_FINAL_CONFIRM (503)
        return await show_filling_complete(query_or_update, context)
    
    # 2. БЕРЕМ ТЕКУЩИЙ МЕТОД
    current_method_id = queue[0]
    country = context.user_data.get('selected_country')
    
    # Ищем инфо о методе в COUNTRY_METHODS
    method_info = None
    for m in COUNTRY_METHODS.get(country, []):
        if m['id'] == current_method_id:
            method_info = m
            break
    
    if not method_info:
        print(f"⚠️ Метод {current_method_id} не найден для страны {country}")
        if queue: queue.pop(0)
        return await ask_next_method(query_or_update, context)
    
    # 3. ПОДГОТОВКА ПОЛЕЙ
    # Создаем копию списка полей, чтобы не мутировать исходный COUNTRY_METHODS
    all_fields = list(method_info.get('fields', []))
    
    # Если это банковский перевод и нет поля bank_name — добавляем
    if "bank_name" not in all_fields and method_info.get('type') == 'bank':
        all_fields.insert(0, "bank_name")
    
    # Сохраняем структуру текущего процесса
    context.user_data['current_method'] = {
        'id': current_method_id,
        'name': method_info['name'],
        'fields': all_fields,
        'data': {}
    }
    context.user_data['current_field_index'] = 0  # СТРОГО СБРАСЫВАЕМ НА 0
    
    # 4. ФОРМИРУЕМ ТЕКСТ
    total_methods = len(context.user_data.get('selected_methods', []))
    # Сколько методов уже НЕ в очереди + текущий
    current_step = total_methods - len(queue) + 1
    
    first_field = all_fields[0]
    # Используем FIELD_NAMES из твоего файла
    display_name = FIELD_NAMES.get(first_field, first_field.replace('_', ' '))
    
    text = (
        f"📝 <b>Заполнение данных: Шаг {current_step} из {total_methods}</b>\n"
        f"───────────────────\n"
        f"Метод: <b>{method_info['name']}</b>\n"
        f"Полей к заполнению: {len(all_fields)}\n\n"
        f"👉 Введите <b><code>{display_name.upper()}</code></b> в чат:"
    )
    
    # 5. ОТПРАВКА (Обработка и callback_query, и обычного сообщения)
    try:
        if hasattr(query_or_update, 'callback_query') and query_or_update.callback_query:
            await query_or_update.callback_query.edit_message_text(text, parse_mode='HTML')
        elif hasattr(query_or_update, 'message') and query_or_update.message:
            await query_or_update.message.reply_text(text, parse_mode='HTML')
        else:
            # Универсальный вариант для context или update
            await context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode='HTML')
    except Exception as e:
        print(f"⚠️ Ошибка вывода в ask_next_method: {e}")
        # Если edit не сработал (например, текст тот же), пробуем ответить новым сообщением
        await context.bot.send_message(chat_id=context._chat_id, text=text, parse_mode='HTML')
    
    print(f"🔵 ask_next_method: ждем поле {first_field} (стейт 502)")
    return WAIT_FIELD_INPUT


	# ============================================


async def process_field_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Перед тем как что-то делать, берем текст от юзера
    user_input = update.message.text.strip() if update.message.text else ""
    
    print("\n" + "🔵" * 10)
    print(f"📥 ВВОД ПОЛЯ: '{user_input[:20]}...'")
    
    # ПРОВЕРКА ДАННЫХ В ОЧЕРЕДИ
    # Вместо мифического 'state' проверяем наличие очереди заполнения
    queue = context.user_data.get('filling_queue')
    if not queue:
        print("⚠️ Очередь заполнения пуста или отсутствует")
        await update.message.reply_text("❌ Данные сессии потеряны. Начните заново через /addlink")
        return ConversationHandler.END

    # Берем текущий метод из очереди (не удаляя его пока)
    current_method_id = queue[0]
    
    # Получаем данные текущего метода (они должны быть в context.user_data)
    # Предполагаем, что ты хранишь структуру методов в 'methods_data'
    methods_dict = context.user_data.get('selected_methods_full', {})
    current_method = methods_dict.get(current_method_id)

    if not current_method:
        print(f"❌ Метод {current_method_id} не найден в selected_methods_full")
        await update.message.reply_text("❌ Ошибка структуры данных. Начните заново.")
        return ConversationHandler.END

    fields = current_method.get('fields', [])
    field_index = context.user_data.get('current_field_index', 0)
    
    if field_index >= len(fields):
        print(f"❌ Индекс {field_index} вышел за пределы полей {len(fields)}")
        return await ask_next_method(update, context)

    field_name = fields[field_index]
    print(f"📝 Обрабатываем: {field_name} (индекс {field_index})")

    # --- ВАЛИДАЦИЯ ДЛИНЫ ВВОДА ---
    limits = {
        "bank_name": 50, "card_number": 25, "phone": 20,
        "iban": 34, "beneficiary": 60, "account_number": 30,
        "bik": 12, "swift": 15
    }
    max_len = limits.get(field_name, 100)
    
    if not user_input:
        await update.message.reply_text("❌ Поле не может быть пустым. Введите данные:")
        return WAIT_FIELD_INPUT

    if len(user_input) > max_len:
        await update.message.reply_text(
            f"❌ Слишком длинный текст (макс. {max_len} симв.).\nПопробуйте еще раз:"
        )
        return WAIT_FIELD_INPUT

    # --- СОХРАНЕНИЕ ---
    if 'data' not in current_method:
        current_method['data'] = {}
    
    current_method['data'][field_name] = user_input
    print(f"💾 Сохранено в {current_method_id}: {field_name} = {user_input[:20]}")

    # --- ПРОВЕРКА: ЕСТЬ ЛИ ЕЩЕ ПОЛЯ В ЭТОМ МЕТОДЕ? ---
    if field_index + 1 < len(fields):
        context.user_data['current_field_index'] = field_index + 1
        next_field = fields[field_index + 1]
        
        # Используем твой FIELD_NAMES (убедись, что он импортирован)
        from bot.utils import FIELD_NAMES # Пример импорта, проверь у себя
        next_display = FIELD_NAMES.get(next_field, next_field.replace('_', ' '))
        
        await update.message.reply_text(
            f"✅ Сохранено. Теперь введите <b>{next_display.upper()}</b>:",
            parse_mode='HTML'
        )
        return WAIT_FIELD_INPUT

    # --- ЗАВЕРШЕНИЕ ТЕКУЩЕГО МЕТОДА ---
    print(f"🏁 Метод {current_method_id} полностью заполнен")
    
    # Перекладываем в "готовое"
    if 'collected_methods' not in context.user_data:
        context.user_data['collected_methods'] = {}
    
    context.user_data['collected_methods'][current_method_id] = current_method
    
    # Убираем метод из очереди
    queue.pop(0)
    context.user_data['filling_queue'] = queue
    context.user_data['current_field_index'] = 0 # Сбрасываем индекс для следующего метода
    
    await update.message.reply_text(
        f"✅ Данные для <b>{current_method.get('name', current_method_id)}</b> приняты!",
        parse_mode='HTML'
    )
    
    # Переход к следующему методу в очереди или к финалу
    return await ask_next_method(update, context)



# ============================================
# ЗАВЕРШЕНИЕ ЗАПОЛНЕНИЯ
# ============================================
async def show_filling_complete(update_or_query, context):
    """Показывает итог с реквизитами и запрашивает подтверждение"""
    collected = context.user_data.get('collected_methods', {})
    
    # 1. Если вдруг данных нет (защита от багов)
    if not collected:
        print("⚠️ show_filling_complete: данные 'collected_methods' пусты")
        text = "❌ <b>Данные не найдены или сессия истекла.</b>"
        keyboard = [[InlineKeyboardButton("◀️ В начало", callback_data="back_to_categories")]]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        if hasattr(update_or_query, 'message') and update_or_query.message:
            await update_or_query.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await update_or_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return ConversationHandler.END

    # 2. Формируем красивый отчет
    text = "✅ <b>Все данные собраны!</b>\n"
    text += "───────────────────\n"
    text += "📋 <b>Проверьте введенные данные:</b>\n\n"
    
    # Расширенный словарь имен полей (можно вынести в utils.py)
    friendly_names = {
        "bank_name": "🏦 Банк",
        "card_number": "💳 Карта",
        "phone": "📱 Телефон",
        "account_number": "📄 Счет",
        "bik": "🆔 БИК",
        "iban": "🌍 IBAN",
        "bic": "🔑 BIC/SWIFT",
        "beneficiary": "👤 Получатель",
        "routing": "🔄 Routing",
        "swift": "⚡ SWIFT",
        "zip": "📮 ZIP код",
        "mfo": "🏦 МФО"
    }
    
    for method_id, method_info in collected.items():
        text += f"🔹 <b>{method_info['name'].upper()}</b>\n"
        
        # Данные из метода
        data = method_info.get('data', {})
        
        # Сначала выводим название банка, если оно есть
        if "bank_name" in data:
            text += f"  • {friendly_names['bank_name']}: <code>{data['bank_name']}</code>\n"
        
        # Выводим остальные поля
        for field, value in data.items():
            if field == "bank_name": continue
            display = friendly_names.get(field, field.replace('_', ' ').capitalize())
            text += f"  • {display}: <code>{value}</code>\n"
        text += "\n"
    
    text += "───────────────────\n"
    text += "👇 <b>Все данные верны?</b>"
    
    # Кнопки финализации
    keyboard = [[
        InlineKeyboardButton("✅ Да, сохранить", callback_data="save_all_methods"),
        InlineKeyboardButton("❌ Нет, заново", callback_data="restart_filling")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # 3. Отправка пользователю
    try:
        if hasattr(update_or_query, 'callback_query') and update_or_query.callback_query:
            await update_or_query.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        elif hasattr(update_or_query, 'message') and update_or_query.message:
            await update_or_query.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
        else:
            # Если вызвано из MessageHandler после последнего поля
            await context.bot.send_message(
                chat_id=context._chat_id or update_or_query.effective_chat.id,
                text=text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
    except Exception as e:
        print(f"⚠️ Ошибка вывода финала: {e}")
        # Запасной вариант - новое сообщение
        await context.bot.send_message(
            chat_id=context._chat_id or update_or_query.effective_chat.id,
            text=text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    print("🔵 Финальный экран показан. Ждем стейт 503 (WAIT_FINAL_CONFIRM)")
    return WAIT_FINAL_CONFIRM

# ============================================
# ВСПОМОГАТЕЛЬНАЯ: ГЕНЕРАЦИЯ ССЫЛКИ
# ============================================
def generate_payment_link(method_id: str, data: dict) -> str:
	"""Генерирует ссылку для перевода на основе данных"""
	
	# Для карт (все страны)
	if method_id.startswith('card_') or method_id == "card":
		card = data.get('card_number', '').replace(' ', '')
		return f"card://{card}"
	
	# Для телефонов (все страны)
	elif method_id.startswith('phone_') or method_id == "phone":
		phone = data.get('phone', '').replace('+', '').replace(' ', '')
		return f"tel://{phone}"
	
	# Для IBAN (все страны)
	elif method_id.startswith('iban_') or method_id == "iban":
		iban = data.get('iban', '').replace(' ', '')
		return f"iban://{iban}"
	
	# Для счетов (все страны)
	elif method_id.startswith('account_') or method_id == "account":
		account = data.get('account', '')
		return f"account://{account}"
	
	# Для ACH (США)
	elif method_id == "ach_usa" or method_id == "ach":
		routing = data.get('routing', '')
		account = data.get('account', '')
		return f"ach://{routing}/{account}"
	
	# Для Wire (США)
	elif method_id == "wire_usa" or method_id == "wire":
		swift = data.get('swift', '')
		account = data.get('account', '')
		return f"wire://{swift}/{account}"
	
	# По умолчанию возвращаем пустую строку
	return ""


# ============================================
# РЕДАКТИРОВАНИЕ МЕТОДОВ
# ============================================
async def edit_methods(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Возвращает к выбору методов для редактирования"""
	query = update.callback_query
	await query.answer()
	
	print(f"🌍 bankworld.py получил: {update.callback_query.data}")
	
	# Показываем выбранные методы с возможностью убрать галочки
	country = context.user_data.get('selected_country')
	methods = COUNTRY_METHODS.get(country, [])
	selected = context.user_data.get('selected_methods', [])
	collected = context.user_data.get('collected_methods', {})
	
	text = f"{COUNTRY_NAMES.get(country, country)}\n\n"
	text += "✏️ <b>Редактирование</b>\n"
	text += "Уберите галочки чтобы удалить метод:\n\n"
	
	keyboard = []
	
	for method in methods:
		method_id = method['id']
		prefix = "✅" if method_id in selected else "⬜"
		
		# Если метод уже заполнен, показываем это
		if method_id in collected:
			button_text = f"{prefix} {method['name']} (данные есть)"
		else:
			button_text = f"{prefix} {method['name']}"
		
		keyboard.append([
			InlineKeyboardButton(button_text, callback_data=f"edit_toggle_{method_id}")
		])
	
	keyboard.append([InlineKeyboardButton("➡️ Продолжить", callback_data="continue_after_edit")])
	keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_final")])
	
	await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
	print(f"🔵 show_country_methods ВОЗВРАЩАЕТ: {WAIT_METHOD_SELECTION}")
	
	return WAIT_METHOD_SELECTION


# ============================================
# ОБРАБОТКА РЕДАКТИРОВАНИЯ
# ============================================
async def edit_toggle_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Убирает или добавляет метод при редактировании"""
	query = update.callback_query
	await query.answer()
	
	print(f"🌍 bankworld.py получил: {update.callback_query.data}")
	
	method_id = query.data.replace("edit_toggle_", "")
	selected = context.user_data.get('selected_methods', [])
	collected = context.user_data.get('collected_methods', {})
	
	if method_id in selected:
		# Убираем метод
		selected.remove(method_id)
		# Если метод был заполнен - удаляем его данные
		if method_id in collected:
			del collected[method_id]
	else:
		# Добавляем метод
		selected.append(method_id)
	
	context.user_data['selected_methods'] = selected
	context.user_data['collected_methods'] = collected
	
	# Обновляем отображение
	await edit_methods(update, context)
	return WAIT_METHOD_SELECTION


# ============================================
# ПРОДОЛЖИТЬ ПОСЛЕ РЕДАКТИРОВАНИЯ
# ============================================
async def continue_after_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Продолжает заполнение после редактирования"""
	query = update.callback_query
	await query.answer()
	
	print(f"🌍 bankworld.py получил: {update.callback_query.data}")
	
	selected = context.user_data.get('selected_methods', [])
	collected = context.user_data.get('collected_methods', {})
	
	# Проверяем, все ли выбранные методы уже заполнены
	unfilled = [m for m in selected if m not in collected]
	
	if unfilled:
		# Есть незаполненные методы - продолжаем заполнение
		context.user_data['filling_queue'] = unfilled
		await ask_next_method(query, context)
		return WAIT_FILLING_DATA
	else:
		# Все заполнено - показываем финал
		return await show_filling_complete(query, context)


# ============================================
# СОХРАНЕНИЕ ВСЕХ МЕТОДОВ В БАЗУ (ИСПРАВЛЕННАЯ)
# ============================================
async def save_all_methods(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Сохраняет все выбранные методы в базу данных"""
	query = update.callback_query
	await query.answer()
	
	print(f"🌍 bankworld.py получил: {update.callback_query.data}")
	
	collected = context.user_data.get('collected_methods', {})
	page_id = context.user_data.get('page_id')
	country = context.user_data.get('selected_country', '')
	
	# Базовый URL из конфига
	from core.config import APP_URL
	base_url = APP_URL.rstrip('/')
	page_username = None
	page_url = None
	
	# Если нет page_id - пробуем получить из базы
	if not page_id:
		try:
			from bot.utils import get_db_connection
			
			conn = await get_db_connection()
			
			# Получаем страницу пользователя
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
			
			if not page:
				await query.edit_message_text(
					"❌ Ошибка: страница не найдена.\n"
					"Пожалуйста, сначала создайте страницу через /start"
				)
				await conn.close()
				return ConversationHandler.END
			
			page_id = page['id']
			page_username = page['username']
			context.user_data['page_id'] = page_id
			context.user_data['page_username'] = page_username
			await conn.close()
			page_url = f"{base_url}/{page_username}"
		
		except Exception as e:
			logger.error(f"Ошибка получения page_id: {e}")
			await query.edit_message_text(
				"❌ Ошибка: не удалось получить ID страницы.\n"
				"Пожалуйста, сначала создайте страницу через /start"
			)
			return ConversationHandler.END
	else:
		# Если page_id уже есть, получаем username
		try:
			from bot.utils import get_db_connection
			conn = await get_db_connection()
			page = await conn.fetchrow(
				"SELECT username FROM pages WHERE id = $1",
				page_id
			)
			if page:
				page_username = page['username']
				page_url = f"{base_url}/{page_username}"
			await conn.close()
		except Exception as e:
			logger.error(f"Ошибка получения username: {e}")
			page_username = None
	
	# Проверяем, есть ли данные для сохранения
	if not collected:
		await query.edit_message_text("❌ Нет данных для сохранения")
		return ConversationHandler.END
	
	saved_count = 0
	errors = []
	saved_methods_info = []
	
	await query.edit_message_text("⏳ Сохраняем данные в базу...")
	
	try:
		from bot.utils import get_db_connection
		
		conn = await get_db_connection()
		
		# Получаем максимальный sort_order
		max_sort = await conn.fetchval(
			"SELECT COALESCE(MAX(sort_order), 0) FROM links WHERE page_id = $1",
			page_id
		)
		
		for method_id, method_info in collected.items():
			try:
				# Добавляем страну в JSON данные
				method_info['data']['country'] = country
				
				# Формируем название для title
				title = f"{method_info['name']}"
				
				# ОБРЕЗАЕМ TITLE (обычно VARCHAR(255))
				if title and len(title) > 255:
					title = title[:255]
					print(f"⚠️ Title обрезан до 255 символов")
				
				# Определяем иконку в зависимости от типа метода
				if method_id.startswith('card_'):
					icon = 'card'
				elif method_id.startswith('iban_'):
					icon = 'iban'
				elif method_id.startswith('phone_'):
					icon = 'phone'
				elif method_id.startswith('account_') or method_id.startswith(
						'non_res_') or method_id == 'non_res_vietnam':
					icon = 'account'  # для всех счетов одна иконка
				elif method_id.startswith('account_'):
					icon = 'account'
				elif method_id.startswith('ach_'):
					icon = 'ach'
				elif method_id.startswith('wire_'):
					icon = 'wire'
				else:
					icon = method_id  # для старых типов (card, iban, phone)
				
				# ОБРЕЗАЕМ ICON (обычно VARCHAR(100))
				if icon and len(icon) > 100:
					icon = icon[:100]
					print(f"⚠️ Icon обрезана до 100 символов")
				
				# Проверяем, сколько уже таких методов (для создания уникального link_type)
				similar_count = await conn.fetchval(
					"""
                    SELECT COUNT(*)
                    FROM links
                    WHERE page_id = $1
                      AND link_type LIKE $2
					""",
					page_id, f"{method_id}%"
				)
				
				# Если уже есть такие методы - добавляем суффикс
				if similar_count > 0:
					unique_method_id = f"{method_id}_{similar_count + 1}"
				else:
					unique_method_id = method_id
				
				# ОБРЕЗАЕМ UNIQUE_METHOD_ID (обычно VARCHAR(50))
				if unique_method_id and len(unique_method_id) > 50:
					unique_method_id = unique_method_id[:50]
					print(f"⚠️ unique_method_id обрезан до 50 символов")
				
				# ПОДГОТАВЛИВАЕМ JSON ДАННЫЕ
				pay_details_json = json.dumps(method_info['data'])
				# ОБРЕЗАЕМ JSON если нужно (для TEXT поля обычно 5000-10000)
				if len(pay_details_json) > 10000:
					pay_details_json = pay_details_json[:10000]
					print(f"⚠️ pay_details JSON обрезан до 10000 символов")
				
				# Вставляем новую запись ВСЕГДА (без проверки на существование!)
				await conn.execute(
					"""
                    INSERT INTO links (page_id, title, url, icon, link_type, category,
                                       pay_details, sort_order, is_active, click_count, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, true, 0, NOW())
					""",
					page_id,
					title,  # обрезанный
					"",  # url пустой, ок
					icon,  # обрезанный
					unique_method_id,  # обрезанный
					'transfers',  # категория фиксированная
					pay_details_json,  # обрезанный JSON
					max_sort + saved_count + 1
				)
				logger.info(f"✅ Сохранен метод: {title} (тип: {unique_method_id})")
				action = "добавлен"
				
				# Сохраняем информацию для отчета
				saved_methods_info.append({
					'name': method_info['name'],
					'action': action,
					'details': method_info['data']
				})
				
				saved_count += 1
			
			except Exception as e:
				errors.append(f"{method_info['name']}: {str(e)}")
				logger.error(f"Error saving method {method_id}: {e}")
		
		await conn.close()
	except Exception as e:
		logger.error(f"Database error: {e}")
		errors.append(f"Ошибка базы данных: {str(e)}")
	
	# Очищаем временные данные
	keys_to_clear = ['selected_methods', 'filling_queue', 'collected_methods', 'current_method', 'selected_country']
	for key in keys_to_clear:
		context.user_data.pop(key, None)
	
	# ФОРМИРУЕМ КРАСИВЫЙ ОТЧЕТ
	if errors:
		result_text = f"⚠️ <b>Сохранено с ошибками:</b>\n✅ Успешно: {saved_count}\n❌ Ошибки:\n" + "\n".join(errors[:3])
		if len(errors) > 3:
			result_text += f"\n...и еще {len(errors) - 3} ошибок"
	else:
		# Заголовок
		result_text = f"✅ <b>ГОТОВО! Сохранено {saved_count} способ(а) получения</b>\n"
		result_text += "───────────────────\n\n"
		
		# Детальный отчет по каждому методу
		result_text += "📋 <b>Добавленные реквизиты:</b>\n\n"
		
		for idx, item in enumerate(saved_methods_info, 1):
			# Название метода с действием
			result_text += f"{idx}. <b>{item['name']}</b> <i>({item['action']})</i>\n"
			
			# Детали в зависимости от типа
			details = item['details']
			
			# Банк
			if details.get('bank_name'):
				result_text += f"   🏦 <b>Банк:</b> {details['bank_name']}\n"
			
			# Карта
			if details.get('card_number'):
				card = details['card_number'].replace(' ', '')
				if len(card) == 16:
					card_formatted = f"{card[:4]} {card[4:8]} {card[8:12]} {card[12:]}"
				else:
					card_formatted = card
				result_text += f"   💳 <b>Карта:</b> <code>{card_formatted}</code>\n"
			
			# IBAN
			if details.get('iban'):
				iban = details['iban']
				if len(iban) > 8:
					iban_short = f"{iban[:8]}...{iban[-4:]}"
				else:
					iban_short = iban
				result_text += f"   🏛 <b>IBAN:</b> <code>{iban_short}</code>\n"
			
			# BIC
			if details.get('bic'):
				result_text += f"   🔑 <b>BIC:</b> <code>{details['bic']}</code>\n"
			
			# Beneficiary
			if details.get('beneficiary'):
				result_text += f"   👤 <b>Получатель:</b> {details['beneficiary']}\n"
			
			# Телефон
			if details.get('phone'):
				result_text += f"   📱 <b>Телефон:</b> <code>{details['phone']}</code>\n"
			
			# Страна
			if details.get('country'):
				country_display = COUNTRY_NAMES.get(details['country'], details['country'])
				result_text += f"   🌍 <b>Страна:</b> {country_display}\n"
			
			result_text += "\n"
		
		result_text += "───────────────────\n"
		
		# ССЫЛКА НА СТРАНИЦУ - только текст
		if page_username:
			page_url = f"{base_url}/{page_username}"
			result_text += f"🔗 <b>Твоя страница:</b>\n"
			result_text += f"<code>{page_url}</code>\n\n"
			result_text += "👉 Скопируй ссылку и открой в браузере!\n\n"
		else:
			result_text += "⚠️ <b>Страница не найдена</b>\n"
			result_text += "Сначала создай страницу через /start\n\n"
		
		result_text += "👇 <b>Выбери действие:</b>"
	
	# КНОПКИ - ТОЛЬКО CALLBACK
	keyboard = [
		[InlineKeyboardButton("➕ Добавить еще ссылку", callback_data="add_link")],
		[InlineKeyboardButton("📋 Список всех ссылок", callback_data="list_links")],
		[InlineKeyboardButton("🏠 Главное меню", callback_data="start")]
	]
	
	await query.edit_message_text(
		result_text,
		reply_markup=InlineKeyboardMarkup(keyboard),
		parse_mode='HTML'
	)
	
	return ConversationHandler.END


async def restart_filling(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Полностью перезапускает процесс заполнения для текущей страны"""
	query = update.callback_query
	await query.answer()
	
	print(f"🌍 bankworld.py получил: {update.callback_query.data}")
	
	# Сохраняем выбранную страну
	selected_country = context.user_data.get('selected_country')
	
	# Очищаем все временные данные, связанные с заполнением
	keys_to_clear = [
		'selected_methods',  # выбранные методы
		'filling_queue',  # очередь заполнения
		'collected_methods',  # собранные данные
		'current_method',  # текущий метод
		'current_field_index',  # индекс текущего поля
		'payment_data',  # платежные данные
		'revolut_data',  # данные Revolut
		'wise_data'  # данные Wise
	]
	
	for key in keys_to_clear:
		context.user_data.pop(key, None)
	
	# Восстанавливаем страну, если она была
	if selected_country:
		context.user_data['selected_country'] = selected_country
		logger.info(f"🔄 Перезапуск заполнения для страны: {selected_country}")
	
	# Возвращаемся к выбору методов для этой страны
	return await show_country_methods(update, context)


# ============================================
# ОТМЕНА ВСЕГО ПРОЦЕССА
# ============================================
async def cancel_filling(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Отменяет весь процесс"""
	query = update.callback_query
	await query.answer()
	
	print(f"🌍 bankworld.py получил: {update.callback_query.data}")
	
	# Очищаем все данные
	context.user_data.pop('selected_methods', None)
	context.user_data.pop('filling_queue', None)
	context.user_data.pop('collected_methods', None)
	context.user_data.pop('current_method', None)
	context.user_data.pop('selected_country', None)
	
	await query.edit_message_text(
		"❌ Процесс добавления способов получения отменен.\n\n"
		"Можете начать заново командой /add_payment"
	)
	
	return ConversationHandler.END
