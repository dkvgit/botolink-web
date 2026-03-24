# bot/bankworld.py

import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from bot.states import WAIT_METHOD_SELECTION, WAIT_FIELD_INPUT, SELECT_CATEGORY

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
# // bot/bankworld.py

# // bot/bankworld.py

async def start_filling(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает пошаговое заполнение выбранных методов"""
    query = update.callback_query
    
    print("\n" + "🚀" * 10 + " ВХОД В start_filling " + "🚀" * 10)
    
    # 1. Проверка выбранных методов
    selected = context.user_data.get('selected_methods', [])
    print(f"🔹 Выбрано ID методов: {selected}")
    
    if query:
        await query.answer()
    
    if not selected:
        print("❌ ОШИБКА: selected_methods пуст!")
        if query:
            await query.edit_message_text("❌ Вы не выбрали ни одного способа.")
        return WAIT_METHOD_SELECTION

    # 2. ФОРМИРУЕМ СТРУКТУРУ ИЗ ГЛОБАЛЬНОГО СЛОВАРЯ
    full_data = {}
    
    # Собираем все методы из COUNTRY_METHODS (он в этом же файле, импорт не нужен)
    all_known_methods = []
    for methods_list in COUNTRY_METHODS.values():
        all_known_methods.extend(methods_list)

    for m_id in selected:
        method_info = next((m for m in all_known_methods if m['id'] == m_id), None)
        
        if method_info:
            full_data[m_id] = {
                'name': method_info['name'],
                'fields': list(method_info['fields']), # Копируем список полей
                'data': {}
            }
        else:
            full_data[m_id] = {'name': m_id, 'fields': ['value'], 'data': {}}

    # 3. Инициализация состояния процесса
    context.user_data['selected_methods_full'] = full_data
    context.user_data['filling_queue'] = list(selected)
    context.user_data['collected_methods'] = {}
    context.user_data['current_field_index'] = 0 # Сбрасываем в 0 только ТУТ
    
    print(f"📝 Очередь создана: {context.user_data['filling_queue']}")

    # 4. Переходим к задаванию вопросов
    # Вызываем ask_next_method напрямую (она в этом же файле)
    try:
        # Передаем update (или query), ask_next_method разберется
        return await ask_next_method(update, context)
    except Exception as e:
        print(f"💥 ОШИБКА ПРИ ВЫЗОВЕ ask_next_method: {e}")
        import traceback
        traceback.print_exc()
        return ConversationHandler.END


async def process_field_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Принимает текст от юзера, валидирует и сохраняет в структуру метода."""
    print("\n" + "🔵" * 10 + " process_field_input " + "🔵" * 10)
    
    if not update.message or not update.message.text:
        return WAIT_FIELD_INPUT

    user_input = update.message.text.strip()
    
    # 1. Достаем текущее состояние из памяти
    queue = context.user_data.get('filling_queue')
    methods_dict = context.user_data.get('selected_methods_full', {})
    field_index = context.user_data.get('current_field_index', 0)
    
    if not queue or not methods_dict:
        print("🚨 ОШИБКА: Данные сессии потеряны!")
        await update.message.reply_text("❌ Сессия истекла. Начните заново.")
        return ConversationHandler.END

    current_method_id = queue[0]
    current_method = methods_dict.get(current_method_id)
    fields = current_method.get('fields', [])
    field_name = fields[field_index]

    # 2. ВАЛИДАЦИЯ (длина текста)
    limits = {"bank_name": 50, "card_number": 25, "phone": 20, "iban": 34}
    if len(user_input) > limits.get(field_name, 100):
        await update.message.reply_text(f"❌ Слишком длинно. Повторите ввод:")
        return WAIT_FIELD_INPUT

    # 3. СОХРАНЕНИЕ
    current_method['data'][field_name] = user_input
    print(f"💾 СОХРАНЕНО: {current_method_id} -> {field_name} = {user_input}")

    # 4. ЛОГИКА ПЕРЕКЛЮЧЕНИЯ
    # Если в текущем методе ЕЩЕ есть поля — просто увеличиваем индекс
    if field_index + 1 < len(fields):
        context.user_data['current_field_index'] = field_index + 1
        print(f"➡️ Переходим к следующему полю этого же метода (индекс {field_index + 1})")
    else:
        # Если поля кончились — выкидываем метод из очереди и сбрасываем индекс
        print(f"🏁 Метод {current_method_id} заполнен.")
        
        if 'collected_methods' not in context.user_data:
            context.user_data['collected_methods'] = {}
        
        # Копируем результат в итоговое хранилище
        context.user_data['collected_methods'][current_method_id] = current_method
        
        queue.pop(0) # Удаляем завершенный метод
        context.user_data['filling_queue'] = queue
        context.user_data['current_field_index'] = 0
        
        await update.message.reply_text(f"✅ Данные для <b>{current_method.get('name')}</b> приняты.", parse_mode='HTML')

    # 5. ВСЕГДА В КОНЦЕ вызываем ask_next_method (она сама решит, спросить новое поле или закончить)
    from bot.bankworld import ask_next_method
    return await ask_next_method(update, context)


# // bot/bankworld.py

async def ask_next_method(update_or_query, context):
    """Запрашивает данные для следующего поля или показывает итог"""
    queue = context.user_data.get('filling_queue', [])
    
    # 1. ФИНАЛ
    if not queue:
        from bot.bankworld import show_filling_complete
        return await show_filling_complete(update_or_query, context)
    
    current_method_id = queue[0]
    methods_full = context.user_data.get('selected_methods_full', {})
    method = methods_full.get(current_method_id)

    # 2. ОПРЕДЕЛЯЕМ ТЕКУЩЕЕ ПОЛЕ
    # МЫ БОЛЬШЕ НЕ СБРАСЫВАЕМ индекс в 0 здесь!
    # Индекс контролируется в process_field_input
    idx = context.user_data.get('current_field_index', 0)
    fields = method.get('fields', [])

    # Проверка на случай ошибки индексов
    if idx >= len(fields):
        print("⚠️ Индекс за границей, закрываем метод вручную")
        queue.pop(0)
        context.user_data['filling_queue'] = queue
        context.user_data['current_field_index'] = 0
        return await ask_next_method(update_or_query, context)

    current_field = fields[idx]
    display_name = FIELD_NAMES.get(current_field, current_field.upper())

    # 3. ТЕКСТ (Шаги)
    total = len(context.user_data.get('selected_methods', []))
    done = total - len(queue)
    
    text = (
        f"📝 <b>Заполнение: Метод {done + 1} из {total}</b>\n"
        f"───────────────────\n"
        f"Способ: <b>{method['name']}</b>\n"
        f"Поле {idx + 1} из {len(fields)}\n\n"
        f"👉 Введите <b>{display_name}</b>:"
    )

    # 4. ВЫВОД (Твой блок try-except хороший, оставляем)
    # Используем эффективный метод получения сообщения
    message = update_or_query.callback_query.message if hasattr(update_or_query, 'callback_query') and update_or_query.callback_query else update_or_query.message

    try:
        if hasattr(update_or_query, 'callback_query') and update_or_query.callback_query:
            await update_or_query.callback_query.edit_message_text(text, parse_mode='HTML')
        else:
            await message.reply_text(text, parse_mode='HTML')
    except Exception:
        await context.bot.send_message(chat_id=update_or_query.effective_chat.id, text=text, parse_mode='HTML')

    return WAIT_FIELD_INPUT

	# ============================================


async def process_field_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Принимает текст от юзера, валидирует и сохраняет в структуру метода.
    """
    print("\n" + "🔵" * 15)
    print("🚀 ВХОД В process_field_input")
    
    # 1. Базовая проверка сообщения
    if not update.message or not update.message.text:
        print("⚠️ Сообщение пустое или не содержит текст")
        return WAIT_FIELD_INPUT

    user_input = update.message.text.strip()
    print(f"📩 Юзер прислал текст: '{user_input}'")

    # 2. Проверка очереди
    queue = context.user_data.get('filling_queue')
    print(f"📋 Текущая очередь (filling_queue): {queue}")
    
    if not queue or len(queue) == 0:
        print("🚨 ОШИБКА: Очередь заполнения пуста!")
        await update.message.reply_text("❌ Сессия истекла. Начните заново: /addlink")
        return ConversationHandler.END

    # 3. Достаем данные текущего метода
    current_method_id = queue[0]
    methods_dict = context.user_data.get('selected_methods_full', {})
    current_method = methods_dict.get(current_method_id)
    
    print(f"🛠 Обработка метода: {current_method_id}")
    print(f"📦 Данные метода из selected_methods_full: {current_method}")

    if not current_method:
        print(f"🚨 ОШИБКА: Метод {current_method_id} не найден в словаре!")
        await update.message.reply_text("❌ Техническая ошибка. Начните заново.")
        return ConversationHandler.END

    # 4. Работа с полями (phone, bank_name и т.д.)
    fields = current_method.get('fields', [])
    field_index = context.user_data.get('current_field_index', 0)
    
    print(f"📑 Поля метода: {fields}")
    print(f"📍 Текущий индекс поля: {field_index}")

    if field_index >= len(fields):
        print("⚠️ Индекс превысил количество полей. Сбрасываем и идем дальше.")
        return await ask_next_method(update, context)

    field_name = fields[field_index]
    print(f"📝 Имя текущего поля: {field_name}")

    # 5. Валидация (лимиты)
    limits = {
        "bank_name": 50, "card_number": 25, "phone": 20,
        "iban": 34, "beneficiary": 60, "account_number": 30,
        "bik": 12, "swift": 15
    }
    max_len = limits.get(field_name, 100)
    
    if len(user_input) > max_len:
        print(f"❌ Валидация провалена: {len(user_input)} > {max_len}")
        await update.message.reply_text(f"❌ Слишком длинно (макс {max_len} симв.). Повторите:")
        return WAIT_FIELD_INPUT

    # 6. Сохранение данных внутрь объекта метода
    if 'data' not in current_method:
        current_method['data'] = {}
    
    current_method['data'][field_name] = user_input
    print(f"💾 СОХРАНЕНО: {current_method_id} -> {field_name} = {user_input}")

    # 7. Проверка: есть ли еще поля в ЭТОМ методе?
    if field_index + 1 < len(fields):
        context.user_data['current_field_index'] = field_index + 1
        next_field = fields[field_index + 1]
        
        # Пытаемся красиво назвать поле для юзера
        display_names = {"phone": "НОМЕР ТЕЛЕФОНА", "bank_name": "НАЗВАНИЕ БАНКА"}
        next_display = display_names.get(next_field, next_field.upper())
        
        print(f"➡️ Переходим к следующему полю: {next_field}")
        await update.message.reply_text(f"✅ Принято. Теперь введите <b>{next_display}</b>:", parse_mode='HTML')
        return WAIT_FIELD_INPUT

    # 8. Завершение метода (переход к следующему в очереди)
    print(f"🏁 Метод {current_method_id} полностью заполнен.")
    
    # Сохраняем готовый метод в итоговый список
    if 'collected_methods' not in context.user_data:
        context.user_data['collected_methods'] = {}
    
    context.user_data['collected_methods'][current_method_id] = current_method
    
    # Удаляем метод из очереди и сбрасываем индекс полей
    queue.pop(0)
    context.user_data['filling_queue'] = queue
    context.user_data['current_field_index'] = 0
    
    print(f"📉 Осталось методов в очереди: {len(queue)}")
    
    await update.message.reply_text(f"✅ Метод <b>{current_method.get('name')}</b> готов!", parse_mode='HTML')

    # Идем к следующему методу (или финишу)
    print("🔄 Вызываем ask_next_method...")
    return await ask_next_method(update, context)


# // bot/bankworld.py

async def db_save_methods(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет собранные данные в базу данных (JSON)"""
    query = update.callback_query
    await query.answer()
    
    collected = context.user_data.get('collected_methods', {})
    user_id = update.effective_user.id
    
    if not collected:
        await query.edit_message_text("❌ Ошибка: данные не найдены.")
        return ConversationHandler.END

    try:
        # Здесь должна быть твоя логика сохранения в БД (SQLAlchemy/и т.д.)
        # Например, преобразуем в JSON строку для хранения в одной колонке:
        import json
        methods_json = json.dumps(collected, ensure_ascii=False)
        
        print(f"💾 БАЗА ДАННЫХ: Сохраняем для юзера {user_id}: {methods_json}")
        
        # ТУТ ТВОЙ КОД ЗАПИСИ:
        # await db.update_user_bank_methods(user_id, methods_json)
        
        await query.edit_message_text(
            "✅ <b>Данные успешно сохранены!</b>\n\n"
            "Теперь они будут отображаться в твоем профиле и на странице оплаты.",
            parse_mode='HTML'
        )
        
    except Exception as e:
        print(f"💥 ОШИБКА СОХРАНЕНИЯ: {e}")
        await query.edit_message_text("❌ Произошла ошибка при сохранении в базу.")

    return ConversationHandler.END

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
import json # Добавь в начало файла или оставь здесь

async def save_all_methods(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет все выбранные методы в базу данных и завершает диалог"""
    query = update.callback_query
    await query.answer()
    
    print(f"💾 Начинаем сохранение. Методов к записи: {len(context.user_data.get('collected_methods', {}))}")
    
    collected = context.user_data.get('collected_methods', {})
    page_id = context.user_data.get('page_id')
    country = context.user_data.get('selected_country', '')
    
    # Импортируем конфиг
    from core.config import APP_URL
    base_url = APP_URL.rstrip('/')
    page_username = None
    
    # 1. ПОЛУЧЕНИЕ PAGE_ID И USERNAME (если их нет в context)
    from bot.utils import get_db_connection
    try:
        conn = await get_db_connection()
        if not page_id:
            user_id = update.effective_user.id
            page = await conn.fetchrow(
                "SELECT p.id, p.username FROM pages p JOIN users u ON u.id = p.user_id WHERE u.telegram_id = $1",
                user_id
            )
            if not page:
                await query.edit_message_text("❌ Ошибка: страница не найдена. Создайте её через /start")
                await conn.close()
                return ConversationHandler.END
            page_id = page['id']
            page_username = page['username']
        else:
            page = await conn.fetchrow("SELECT username FROM pages WHERE id = $1", page_id)
            page_username = page['username'] if page else None
    except Exception as e:
        print(f"❌ Ошибка БД при поиске страницы: {e}")
        await query.edit_message_text("❌ Ошибка базы данных.")
        return ConversationHandler.END

    # 2. ПРОЦЕСС СОХРАНЕНИЯ
    saved_count = 0
    errors = []
    saved_methods_info = []
    
    await query.edit_message_text("⏳ Сохраняем данные в базу...")
    
    try:
        # Получаем текущий макс. порядок сортировки
        max_sort = await conn.fetchval("SELECT COALESCE(MAX(sort_order), 0) FROM links WHERE page_id = $1", page_id)
        
        for method_id, method_info in collected.items():
            try:
                # Подготовка данных
                method_info['data']['country'] = country
                title = f"{method_info['name']}"[:255]
                
                # Логика иконки
                icon = 'card' if 'card' in method_id else 'iban' if 'iban' in method_id else 'account'
                
                # Уникальный ID для записи
                similar_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM links WHERE page_id = $1 AND link_type LIKE $2",
                    page_id, f"{method_id}%"
                )
                unique_id = f"{method_id}_{similar_count + 1}" if similar_count > 0 else method_id
                
                # JSON реквизитов
                pay_details_json = json.dumps(method_info['data'])

                # INSERT
                await conn.execute(
                    """
                    INSERT INTO links (page_id, title, url, icon, link_type, category,
                                       pay_details, sort_order, is_active, click_count, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, true, 0, NOW())
                    """,
                    page_id, title, "", icon[:100], unique_id[:50], 'transfers', pay_details_json, max_sort + saved_count + 1
                )
                
                saved_methods_info.append({'name': method_info['name'], 'details': method_info['data']})
                saved_count += 1
                
            except Exception as e:
                errors.append(f"{method_info.get('name', method_id)}: {str(e)}")

        await conn.close()
    except Exception as e:
        print(f"❌ Ошибка при записи ссылок: {e}")
        errors.append("Ошибка доступа к таблице ссылок")

    # 3. ФОРМИРОВАНИЕ ОТЧЕТА
    # Используем COUNTRY_NAMES для красивого вывода страны
    try:
        from bot.utils import COUNTRY_NAMES
    except:
        COUNTRY_NAMES = {}

    result_text = f"✅ <b>ГОТОВО! Сохранено: {saved_count}</b>\n"
    result_text += "───────────────────\n\n"
    
    for idx, item in enumerate(saved_methods_info, 1):
        det = item['details']
        result_text += f"{idx}. <b>{item['name']}</b>\n"
        if det.get('bank_name'): result_text += f"   🏦 {det['bank_name']}\n"
        if det.get('card_number'): result_text += f"   💳 <code>{det['card_number']}</code>\n"
        if det.get('iban'): result_text += f"   🌍 <code>{det['iban'][:8]}...</code>\n"
        result_text += "\n"

    if page_username:
        result_text += f"🔗 <b>Твоя страница:</b>\n<code>{base_url}/{page_username}</code>\n\n"

    # 4. ОЧИСТКА И ЗАВЕРШЕНИЕ
    keys_to_clear = ['selected_methods', 'filling_queue', 'collected_methods', 'current_method', 'selected_country']
    for key in keys_to_clear:
        context.user_data.pop(key, None)

    keyboard = [
        [InlineKeyboardButton("➕ Добавить еще", callback_data="add_link")],
        [InlineKeyboardButton("📋 Мои ссылки", callback_data="list_links")],
        [InlineKeyboardButton("🏠 Меню", callback_data="start")]
    ]

    await query.edit_message_text(result_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    
    print("🏁 Сохранение завершено, диалог закрыт.")
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
