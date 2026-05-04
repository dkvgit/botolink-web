# bot/bankworld.py

import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from bot.states import WAIT_METHOD_SELECTION, WAIT_FIELD_INPUT, SELECT_CATEGORY

# В самом начале файла bot/bankworld.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
# Убедись, что здесь НЕТ строки: from bot.bank import choose_country

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
# // bot/bankworld.py

# Словарь для автоматической генерации меток (labels)
FIELD_NAMES = {
    "full_name": "👤 Имя и Фамилия",  # <-- ДОБАВЬ ЭТУ СТРОКУ
    "bank_name": "🏦 Название банка",
    "card_number": "💳 Номер карты",
    "card_holder": "👤 Имя на карте",
    "iban": "🌐 IBAN счет",
    "bic": "🔑 BIC/SWIFT код",
    "beneficiary": "👤 ФИО получателя",
    "wallet": "👛 Номер кошелька",
    "phone": "📱 Номер телефона",
    "vk_id": "🆔 VK ID",
    "username": "👤 Username",
    "email": "📧 Email",
    "tag": "🏷️ Revolut Tag",
    "routing": "🔢 Routing Number",
    "account": "📑 Номер счета",
    "account_number": "📑 Номер счета",
    "zip": "📮 ZIP-код",
    "swift": "🌍 SWIFT код",
    "bik": "🏢 БИК",
    "mfo": "🏢 МФО",
    "card": "💳 Номер карты"
}

# // bot/bankworld.py

def f(field_id):
    """Превращает 'bank_name' в {'id': 'bank_name', 'label': '🏦 Название банка'}"""
    return {
        "id": field_id,
        "label": FIELD_NAMES.get(field_id, field_id.replace('_', ' ').capitalize())
    }

# // bot/bankworld.py

COUNTRY_METHODS = {
    "universal": [
        {"id": "yoomoney", "name": "🇷🇺 ЮMoney", "fields": [f("wallet")]},
        {"id": "vkpay", "name": "🇷🇺 VK Pay", "fields": [f("phone"), f("vk_id")]},
        {"id": "paypal", "name": "🌐 PayPal", "fields": [f("username")]},
        {"id": "wise", "name": "🇪🇺 Wise", "fields": [f("email"), f("iban")]},
        {"id": "revolut", "name": "🇪🇺 Revolut", "fields": [f("tag"), f("iban")]},
        {"id": "monobank", "name": "🇺🇦 Монобанк", "fields": [f("card")]},
        {"id": "kaspi", "name": "🇰🇿 Kaspi.kz", "fields": [f("card"), f("phone")]},
        {"id": "payme", "name": "🇺🇿 Payme", "fields": [f("phone")]},
        {"id": "click", "name": "🇺🇿 Click", "fields": [f("phone")]},
        {"id": "tbcpay", "name": "🇬🇪 TBC Pay", "fields": [f("card"), f("phone")]},
        {"id": "idram", "name": "🇦🇲 Idram", "fields": [f("card"), f("phone")]}
    ],
    "lithuania": [
        {"id": "card_lithuania", "name": "Банковская карта", "fields": [f("bank_name"), f("card_number")]},
        {"id": "iban_lithuania", "name": "Банковский счет (SEPA)", "fields": [f("bank_name"), f("iban"), f("bic"), f("beneficiary")]}
    ],
    "latvia": [
        {"id": "card_latvia", "name": "Банковская карта", "fields": [f("bank_name"), f("card_number")]},
        {"id": "iban_latvia", "name": "Банковский счет (SEPA)", "fields": [f("bank_name"), f("iban"), f("bic"), f("beneficiary")]}
    ],
    "estonia": [
        {"id": "card_estonia", "name": "Банковская карта", "fields": [f("bank_name"), f("card_number")]},
        {"id": "iban_estonia", "name": "Банковский счет (SEPA)", "fields": [f("bank_name"), f("iban"), f("bic"), f("beneficiary")]}
    ],
    "usa": [
        {"id": "card_usa", "name": "Карта (+ ZIP)", "fields": [f("bank_name"), f("card_number"), f("card_holder"), f("zip")]},
        {"id": "ach_usa", "name": "ACH (местный)", "fields": [f("bank_name"), f("routing"), f("account"), f("beneficiary")]},
        {"id": "wire_usa", "name": "Wire (международный)", "fields": [f("bank_name"), f("swift"), f("account"), f("beneficiary")]}
    ],
    "russia": [
        {"id": "card_russia", "name": "Банковская карта", "fields": [f("bank_name"), f("card_number")]},
        {"id": "phone_russia", "name": "По номеру телефона (СБП)", "fields": [f("bank_name"), f("phone")]},
        {"id": "account_russia", "name": "Банковский счет", "fields": [f("bank_name"), f("account_number"), f("bik"), f("beneficiary")]}
    ],
    "ukraine": [
        {"id": "card_ukraine", "name": "Банковская карта", "fields": [f("bank_name"), f("card_number")]},
        {"id": "iban_ukraine", "name": "IBAN счет", "fields": [f("bank_name"), f("iban"), f("beneficiary")]}
    ],
    "belarus": [
        {"id": "card_belarus", "name": "Банковская карта", "fields": [f("bank_name"), f("card_number")]},
        {"id": "iban_belarus", "name": "IBAN счет", "fields": [f("bank_name"), f("iban"), f("bic"), f("beneficiary")]}
    ],
    "kazakhstan": [
        {"id": "card_kazakhstan", "name": "Банковская карта", "fields": [f("bank_name"), f("card_number")]},
        {"id": "iban_kazakhstan", "name": "IBAN счет", "fields": [f("bank_name"), f("iban"), f("bic"), f("beneficiary")]}
    ],
    "armenia": [
        {"id": "card_armenia", "name": "Банковская карта", "fields": [f("bank_name"), f("card_number")]},
        {"id": "account_armenia", "name": "🏦 Банковский счет", "fields": [f("bank_name"), f("account"), f("bic"), f("beneficiary")]}
    ],
    "azerbaijan": [
        {"id": "card_azerbaijan", "name": "Банковская карта", "fields": [f("bank_name"), f("card_number")]},
        {"id": "iban_azerbaijan", "name": "IBAN счет", "fields": [f("bank_name"), f("iban"), f("bic"), f("beneficiary")]}
    ],
    "georgia": [
        {"id": "card_georgia", "name": "Банковская карта", "fields": [f("bank_name"), f("card_number")]},
        {"id": "iban_georgia", "name": "IBAN счет", "fields": [f("bank_name"), f("iban"), f("bic"), f("beneficiary")]}
    ],
    "moldova": [
        {"id": "card_moldova", "name": "Банковская карта", "fields": [f("bank_name"), f("card_number")]},
        {"id": "iban_moldova", "name": "IBAN счет", "fields": [f("bank_name"), f("iban"), f("bic"), f("beneficiary")]}
    ],
    "uzbekistan": [
        {"id": "card_uzbekistan", "name": "Банковская карта", "fields": [f("bank_name"), f("card_number")]},
        {"id": "phone_uzbekistan", "name": "По номеру телефона", "fields": [f("bank_name"), f("phone")]},
        {"id": "account_uzbekistan", "name": "Банковский счет", "fields": [f("bank_name"), f("account"), f("mfo"), f("beneficiary")]}
    ],
    "tajikistan": [
        {"id": "card_tajikistan", "name": "Банковская карта", "fields": [f("bank_name"), f("card_number")]},
        {"id": "account_tajikistan", "name": "Банковский счет", "fields": [f("bank_name"), f("account"), f("bic"), f("beneficiary")]}
    ],
    "kyrgyzstan": [
        {"id": "card_kyrgyzstan", "name": "Банковская карта", "fields": [f("bank_name"), f("card_number")]},
        {"id": "account_kyrgyzstan", "name": "Банковский счет", "fields": [f("bank_name"), f("account"), f("bic"), f("beneficiary")]}
    ],
    "turkmenistan": [
        {"id": "card_turkmenistan", "name": "Банковская карта", "fields": [f("bank_name"), f("card_number")]},
        {"id": "account_turkmenistan", "name": "Банковский счет", "fields": [f("bank_name"), f("account"), f("bic"), f("beneficiary")]}
    ],
    "vietnam": [
        {"id": "non_res_vietnam", "name": "Счет нерезидента", "fields": [
            f("full_name"),
            f("account_number")
        ]},
        {"id": "card_vietnam", "name": "Банковская карта", "fields": [f("bank_name"), f("card_number")]},
        {"id": "account_vietnam", "name": "Банковский счет", "fields": [f("bank_name"), f("account"), f("bic"), f("beneficiary")]}
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
# Справочник красивых названий для логов и превью
FIELD_NAMES = {
    "bank_name": "🏦 Банк",
    "card_number": "💳 Номер карты",
    "iban": "🌐 IBAN",
    "bic": "🔑 BIC/SWIFT",
    "beneficiary": "👤 Получатель",
    "wallet": "👛 Кошелек",
    "phone": "📱 Телефон",
    "vk_id": "🆔 VK ID",
    "username": "👤 Username",
    "email": "📧 Email",
    "tag": "🏷️ Tag",
    "routing": "🔢 Routing Number",
    "account": "📑 Номер счета",
    "account_number": "📑 Номер счета",
    "zip": "📮 ZIP-код",
    "swift": "🌍 SWIFT",
    "bik": "🏢 БИК",
    "mfo": "🏢 МФО"
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


# // bot/bankworld.py

# // bot/bankworld.py

# // bot/bankworld.py

async def show_country_methods(update, context):
    """
    Показывает доступные методы для выбранной страны с улучшенным UI и чекбоксами.
    """
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from bot.bankworld import COUNTRY_METHODS, COUNTRY_NAMES
    
    query = update.callback_query
    
    # 1. Определяем страну
    if query and query.data.startswith("country_"):
        country = query.data.replace("country_", "")
        context.user_data['selected_country'] = country
    else:
        country = context.user_data.get('selected_country')
    
    if not country:
        print("⚠️ Ошибка: Страна не выбрана")
        return 20

    # 2. Получаем данные
    methods = COUNTRY_METHODS.get(country, [])
    selected = context.user_data.get('selected_methods', [])
    # Делаем название страны КРАСИВЫМ и Капсом
    country_display = COUNTRY_NAMES.get(country, country).upper()
    
    # 3. ФОРМИРУЕМ ТЕКСТ (Информативный блок)
    text = (
        f"📍 <b>СТРАНА: {country_display}</b>\n"
        f"────────────────────\n"
        f"Выберите способы оплаты, которые будут отображаться на вашем сайте:\n\n"
        f"💡 <i>Нажмите на кнопку, чтобы добавить метод. Повторное нажатие уберет его.</i>"
    )

    # 4. ФОРМИРУЕМ КНОПКИ
    keyboard = []
    for method in methods:
        m_id = method['id']
        # ✅ Понятный префикс: галочка или пустой квадрат
        prefix = "✅ " if m_id in selected else "⬜️ "
        
        keyboard.append([
            InlineKeyboardButton(
                f"{prefix}{method['name']}",
                callback_data=f"toggle_{m_id}"
            )
        ])
    
    # 5. КНОПКИ УПРАВЛЕНИЯ
    control_buttons = []
    
    # Кнопка "Далее" только если что-то выбрано, чтобы не слать пустые формы
    if selected:
        text += f"\n\nВыбрано методов: <b>{len(selected)}</b>"
        keyboard.append([InlineKeyboardButton("🚀 ПРОДОЛЖИТЬ ЗАПОЛНЕНИЕ", callback_data="start_filling")])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад к выбору стран", callback_data="back_to_countries")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    # 6. ВЫВОД
    if query:
        try:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        except Exception as e:
            # Если текст не изменился (юзер тыкнул ту же кнопку), просто игнорим ошибку
            pass
            
    return 20 # Состояние SELECT_CATEGORY / WAIT_METHOD_SELECTION



# D:\aRabota\TelegaBoom\030_mylinkspace\bot\bankworld.py
from bot.bankper import start_bank_config_flow, BANK_PER_CONFIG

# // bot/handlers.py

# // bot/handlers.py

# // bot/handlers.py

# // bot/handlers.py

async def toggle_method(update, context):
    """Меняет статус выбора метода (выбран/не выбран)"""
    query = update.callback_query
    await query.answer()
    
    # 1. Извлекаем ID (отрезаем toggle_)
    method_id = query.data.replace("toggle_", "")
    
    # 2. Инициализация списка, если его нет
    if 'selected_methods' not in context.user_data:
        context.user_data['selected_methods'] = []
    
    selected = context.user_data['selected_methods']

    # 3. Переключаем состояние (важно: работаем со списком напрямую)
    if method_id in selected:
        selected.remove(method_id)
        print(f"🔘 [TOGGLE] Убрали: {method_id}")
    else:
        selected.append(method_id)
        print(f"🔘 [TOGGLE] Добавили: {method_id}")

    # Сохраняем обновленный список обратно
    context.user_data['selected_methods'] = selected
    
    # 4. Перерисовываем меню
    from bot.bankworld import show_country_methods
    await show_country_methods(update, context)
    
    # Возвращаем 20, чтобы остаться в этом же блоке хендлеров!
    return 20

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

# // bot/bankworld.py

async def start_filling(update, context):
    """Начинает пошаговое заполнение выбранных методов"""
    query = update.callback_query
    
    print("\n" + "🚀" * 10 + " ВХОД В start_filling " + "🚀" * 10)
    
    # 1. Проверка выбранных методов
    selected_ids = context.user_data.get('selected_methods', [])
    print(f"🔹 Выбрано ID методов: {selected_ids}")
    
    if query:
        await query.answer()
    
    if not selected_ids:
        print("❌ ОШИБКА: selected_methods пуст!")
        if query:
            await query.edit_message_text("❌ Вы не выбрали ни одного способа.")
        return 20

    # 2. СОБИРАЕМ ПОЛНЫЕ ОБЪЕКТЫ МЕТОДОВ ДЛЯ ОЧЕРЕДИ
    # Собираем плоский список всех доступных методов из всех стран
    all_known_methods = []
    for methods_list in COUNTRY_METHODS.values():
        all_known_methods.extend(methods_list)

    filling_queue = []
    for m_id in selected_ids:
        # Ищем полный объект метода (с полями-словарями)
        method_info = next((m for m in all_known_methods if m['id'] == m_id), None)
        
        if method_info:
            # Важно: копируем объект, чтобы не испортить глобальный конфиг
            filling_queue.append({
                'id': method_info['id'],
                'name': method_info['name'],
                'fields': list(method_info['fields']) # Тут уже лежат {'id':..., 'label':...}
            })
        else:
            # Фолбэк на случай, если метод не найден (не должно случаться)
            filling_queue.append({
                'id': m_id,
                'name': m_id.upper(),
                'fields': [{"id": "value", "label": "Данные"}]
            })

    # 3. Инициализация состояния процесса
    context.user_data['filling_queue'] = filling_queue # ТЕПЕРЬ ТУТ СПИСОК СЛОВАРЕЙ
    context.user_data['collected_methods'] = {}
    context.user_data['current_field_index'] = 0
    
    print(f"📝 Очередь создана: {[m['id'] for m in filling_queue]}")

    # 4. Переходим к задаванию вопросов
    try:
        from bot.bankworld import ask_next_method
        return await ask_next_method(update, context)
    except Exception as e:
        print(f"💥 ОШИБКА ПРИ ВЫЗОВЕ ask_next_method: {e}")
        import traceback
        traceback.print_exc()
        return -1 # ConversationHandler.END



# // bot/bankworld.py

# // bot/bankworld.py

# // bot/bankworld.py

async def ask_next_method(update_or_query, context):
    """Запрашивает данные для следующего поля с улучшенным UI"""
    from bot.bankworld import FIELD_NAMES, FIELD_EXAMPLES
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    queue = context.user_data.get('filling_queue', [])
    
    if not queue:
        from bot.bankworld import show_filling_complete
        return await show_filling_complete(update_or_query, context)
    
    current_method = queue[0]
    method_name = current_method.get('name', 'Метод').upper()
    fields = current_method.get('fields', [])
    idx = context.user_data.get('current_field_index', 0)

    if idx >= len(fields):
        queue.pop(0)
        context.user_data['filling_queue'] = queue
        context.user_data['current_field_index'] = 0
        return await ask_next_method(update_or_query, context)

    current_field_obj = fields[idx]
    field_id = current_field_obj.get('id')
    field_label = current_field_obj.get('label') or FIELD_NAMES.get(field_id, "Данные")
    
    all_selected = context.user_data.get('selected_methods', [])
    total_methods = len(all_selected)
    current_num = total_methods - len(queue) + 1
    progress_bar = "🟦" * current_num + "⬜" * (total_methods - current_num)

    text = (
        f"📊 <b>Общий прогресс: {current_num} из {total_methods}</b>\n"
        f"{progress_bar}\n"
        f"────────────────────\n"
        f"🛠 <b>Настройка:</b> <u>{method_name}</u>\n\n"
        f"❓ <b>Введите {field_label}:</b>\n"
        f"<i>(Поле {idx + 1} из {len(fields)})</i>\n"
    )

    raw_ex = FIELD_EXAMPLES.get(field_id, "")
    if raw_ex:
        clean_ex = raw_ex.replace("Пример:", "").strip()
        text += f"\n💡 <i>Пример: {clean_ex}</i>"

    text += "\n\n👇 <b>Напишите ответ в чат:</b>"

    # ИСПРАВЛЕНО: callback_data вместо callback_query
    keyboard = [[InlineKeyboardButton("❌ Отменить заполнение", callback_data="back_to_countries")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    chat_id = update_or_query.effective_chat.id
    
    try:
        if hasattr(update_or_query, 'callback_query') and update_or_query.callback_query:
            await update_or_query.callback_query.edit_message_text(
                text, parse_mode='HTML', reply_markup=reply_markup
            )
        else:
            await context.bot.send_message(
                chat_id=chat_id, text=text, parse_mode='HTML', reply_markup=reply_markup
            )
    except Exception as e:
        await context.bot.send_message(
            chat_id=chat_id, text=text, parse_mode='HTML', reply_markup=reply_markup
        )

    return 502

# // bot/bankworld.py

# Словарь маппинга популярных банков (СНГ, Прибалтика, США)
# Ключ: что ищем в вводе пользователя (нижний регистр)
# Значение: имя файла в /static/icons/ (без .png)
BANK_ICONS_MAP = {
    # --- РОССИЯ ---
    "сбер": "sberbank", "sber": "sberbank",
    "тинькофф": "tinkoff", "tinkoff": "tinkoff", "т-банк": "tinkoff", "t-bank": "tinkoff",
    "альфа": "alfabank", "alfa": "alfabank",
    "втб": "vtb", "vtb": "vtb",
    "райф": "raiffeisen", "raif": "raiffeisen",
    "газпром": "gazprombank", "гпб": "gazprombank",
    "открытие": "otkritie", "совком": "sovcombank", "халва": "sovcombank",
    "почта": "pochtabank", "озон": "ozon",

    # --- УКРАИНА ---
    "приват": "privatbank", "privat": "privatbank",
    "моно": "monobank", "mono": "monobank",
    "ощад": "oschadbank", "oschad": "oschadbank",
    "пумб": "pumb", "рада": "radabank",

    # --- КАЗАХСТАН ---
    "каспи": "kaspi", "kaspi": "kaspi",
    "халык": "halykbank", "halyk": "halykbank", "народный": "halykbank",
    "центркредит": "bcc", "bcc": "bcc",
    "форте": "fortebank", "forte": "fortebank",
    "джусан": "jusan", "bereke": "bereke",

    # --- БЕЛАРУСЬ ---
    "беларусбанк": "belarusbank", "мтб": "mtbank", "mtb": "mtbank",
    "белагро": "belagroprom", "приор": "priorbank",

    # --- ПРИБАЛТИКА ---
    "swed": "swedbank", "свед": "swedbank",
    "seb": "seb", "себ": "seb",
    "citadele": "citadele", "цитаделе": "citadele",
    "luminor": "luminor", "люминор": "luminor",
    "siauliu": "siauliu", "lvh": "lvh",

    # --- СРЕДНЯЯ АЗИЯ / КАВКАЗ ---
    "узкард": "uzcard", "humo": "humo", "капиталбанк": "kapitalbank",
    "мбанк": "mbank", "mbank": "mbank", "ориён": "orionbank", "алиф": "alifbank",
    "tbc": "tbc", "bog": "bog", "bank of georgia": "bog",

    # --- США ---
    "chase": "chase", "чейз": "chase",
    "bank of america": "boa", "bofa": "boa", "боа": "boa",
    "wells fargo": "wellsfargo", "велс": "wellsfargo",
    "citibank": "citibank", "citi": "citibank", "сити": "citibank",
    "capital one": "capitalone", "us bank": "usbank", "pnc": "pnc"
}

# // bot/bankworld.py

async def process_field_input(update, context):
    """
    Принимает текст от юзера, валидирует и сохраняет с улучшенным UI.
    """
    from bot.bankworld import FIELD_NAMES, ask_next_method, FIELD_EXAMPLES, BANK_ICONS_MAP
    
    if not update.message or not update.message.text:
        return 502

    user_input = update.message.text.strip()
    
    queue = context.user_data.get('filling_queue')
    if not queue or len(queue) == 0:
        await update.message.reply_text("❌ Сессия истекла. Начните заново: /start")
        return -1

    current_method = queue[0]
    current_method_id = current_method.get('id')
    fields = current_method.get('fields', [])
    field_index = context.user_data.get('current_field_index', 0)

    if field_index >= len(fields):
        return await ask_next_method(update, context)

    current_field_obj = fields[field_index]
    field_id = current_field_obj.get('id')
    
    # 1. Валидация
    limits = {"bank_name": 50, "card_number": 25, "phone": 20, "iban": 34, "beneficiary": 60}
    max_len = limits.get(field_id, 100)
    if len(user_input) > max_len:
        await update.message.reply_text(f"⚠️ <b>Ошибка: Текст слишком длинный!</b>\nМаксимум: {max_len} симв. Попробуйте еще раз:", parse_mode='HTML')
        return 502

    # 2. Сохранение и иконка
    if 'data' not in current_method:
        current_method['data'] = {}
    
    current_method['data'][field_id] = user_input

    if field_id == "bank_name":
        input_lower = user_input.lower()
        for key, icon_file in BANK_ICONS_MAP.items():
            if key in input_lower:
                current_method['data']['icon'] = f"/static/icons/{icon_file}.png"
                break

    queue[0] = current_method
    context.user_data['filling_queue'] = queue

    # 3. Переход к следующему шагу с УЛУЧШЕННЫМ UI
    if field_index + 1 < len(fields):
        context.user_data['current_field_index'] = field_index + 1
        next_field = fields[field_index + 1]
        next_label = next_field.get('label')
        next_id = next_field.get('id')
        
        # Считаем прогресс (например: Шаг 2 из 4)
        current_step = field_index + 2
        total_steps = len(fields)
        progress_bar = "🔵" * current_step + "⚪" * (total_steps - current_step)

        # ФОРМИРУЕМ ИНФОРМАТИВНЫЙ ОТВЕТ
        response_text = (
            f"✅ <b>Записано:</b> <code>{user_input}</code>\n"
            f"────────────────────\n"
            f"📝 <b>Шаг {current_step}/{total_steps}</b>\n"
            f"{progress_bar}\n\n"
            f"👉 Пожалуйста, введите: <b>{next_label}</b>"
        )
        
        raw_ex = FIELD_EXAMPLES.get(next_id, "")
        if raw_ex:
            clean_ex = raw_ex.replace("Пример:", "").strip()
            response_text += f"\n\n💡 <i>Пример: {clean_ex}</i>"
            
        response_text += "\n\n⌨️ <i>Просто отправьте текст сообщением ниже...</i>"
        
        await update.message.reply_text(response_text, parse_mode='HTML')
        return 502

   
    
    # 4. Финализация метода (когда все поля в текущем методе заполнены)
    if 'collected_methods' not in context.user_data:
        context.user_data['collected_methods'] = {}
    
    # Сохраняем данные
    context.user_data['collected_methods'][current_method_id] = current_method['data']
    
    # --- УЛУЧШАЕМ ТЕКСТ ЗАВЕРШЕНИЯ ---
    from bot.bankworld import COUNTRY_METHODS
    
    # Ищем красивое название (например, "Банковская карта") вместо card_latvia
    nice_method_name = current_method.get('name', current_method_id.replace('_', ' ').title())
    
    # Убираем метод из очереди
    queue.pop(0)
    context.user_data['filling_queue'] = queue
    context.user_data['current_field_index'] = 0
    
    # Сообщаем красиво
    success_text = (
        f"✅ <b>{nice_method_name}</b>\n"
        f"────────────────────\n"
        f"✨ Данные успешно собраны!"
    )
    
    await update.message.reply_text(success_text, parse_mode='HTML')
    
    # Переходим к следующему методу в очереди или к финалу
    return await ask_next_method(update, context)







async def save_all_methods(update, context):
    """
    ФИНАЛЬНОЕ СОХРАНЕНИЕ: Записывает в БД и выводит сочный отчет с кнопкой сайта.
    """
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    import json
    
    query = update.callback_query
    await query.answer("🚀 Публикую на сайт...")
    
    collected = context.user_data.get('collected_methods', {})
    user_id = update.effective_user.id
    tg_username = update.effective_user.username
    
    if not collected:
        await query.edit_message_text("❌ <b>Данные не найдены.</b> Попробуйте начать заново.", parse_mode='HTML')
        return -1

    try:
        from bot.utils import get_db_connection
        from bot.bankworld import COUNTRY_METHODS, generate_payment_link

        async with get_db_connection() as conn:
            # 1. Поиск страницы и получение slug (username)
            row = await conn.fetchrow("SELECT id, username FROM pages WHERE user_id = $1 LIMIT 1", user_id)
            
            if not row and tg_username:
                row = await conn.fetchrow("SELECT id, username FROM pages WHERE username = $1 LIMIT 1", tg_username)
            
            if not row:
                new_username = tg_username or f"id{user_id}"
                row = await conn.fetchrow(
                    "INSERT INTO pages (user_id, username, title, created_at, updated_at, is_active) "
                    "VALUES ($1, $2, $3, NOW(), NOW(), true) RETURNING id, username",
                    user_id, new_username, f"Страница {new_username}"
                )
            
            page_id = row['id']
            user_slug = row['username']
            site_url = f"https://botolink.pro/{user_slug}"

            # 2. Сохранение методов
            max_sort = await conn.fetchval("SELECT COALESCE(MAX(sort_order), 0) FROM links WHERE page_id = $1", page_id)
            saved_names_report = []
            
            for method_id, details in collected.items():
                # По умолчанию иконка из деталей (если нашлась в BANK_ICONS_MAP), иначе стандарт
                icon_path = details.get('icon', "/static/icons/bank.png")
                method_display_name = method_id.replace('_', ' ').title()
                
                # Ищем страну и название метода для отчета
                for country_name, methods in COUNTRY_METHODS.items():
                    m_info = next((m for m in methods if m['id'] == method_id), None)
                    if m_info:
                        # Формат: Банковская карта (🇱🇹 Литва)
                        method_display_name = f"{m_info['name']} ({country_name})"
                        break

                generated_url = generate_payment_link(method_id, details)
                pay_details_json = json.dumps(details, ensure_ascii=False)

                await conn.execute(
                    """
                    INSERT INTO links (
                        page_id, title, url, icon, link_type, category,
                        pay_details, sort_order, is_active, is_exchange, created_at, updated_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, true, false, NOW(), NOW())
                    """,
                    page_id, method_display_name, generated_url, icon_path,
                    method_id, 'transfers', pay_details_json,
                    max_sort + len(saved_names_report) + 1
                )
                saved_names_report.append(method_display_name)

        # 3. ФОРМИРУЕМ ФИНАЛЬНЫЙ ОТЧЕТ (ИНФОРМАТИВНЫЙ!)
        methods_list = "\n".join([f" ✅ <b>{name}</b>" for name in saved_names_report])
        
        final_text = (
            f"🚀 <b>УСПЕШНО ОПУБЛИКОВАНО!</b>\n"
            f"────────────────────\n"
            f"Ваши реквизиты добавлены и уже работают:\n\n"
            f"{methods_list}\n\n"
            f"🔗 <b>Ваша ссылка:</b>\n<code>{site_url}</code>\n"
            f"────────────────────\n"
            f"👇 <b>Нажмите кнопку, чтобы проверить результат:</b>"
        )

        keyboard = [
            [InlineKeyboardButton("🌍 ОТКРЫТЬ МОЙ САЙТ", url=site_url)],
            [InlineKeyboardButton("🏠 В меню категорий", callback_data="start_over")]
        ]
        
        await query.edit_message_text(
            final_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        
        # 4. Очистка временных данных
        keys_to_clear = [
            'collected_methods', 'selected_methods', 'filling_queue',
            'current_field_index', 'selected_country'
        ]
        for key in keys_to_clear:
            context.user_data.pop(key, None)
            
    except Exception as e:
        print(f"💥 ОШИБКА СОХРАНЕНИЯ: {e}")
        await query.edit_message_text(f"❌ <b>Ошибка записи в БД:</b>\n<code>{e}</code>", parse_mode='HTML')

    return -1 # Завершаем ConversationHandler
    
  

async def show_filling_complete(update_or_query, context):
    """
    Показывает итоговое превью всех заполненных методов ПЕРЕД сохранением в БД.
    """
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from bot.bankworld import FIELD_NAMES, COUNTRY_METHODS
    
    collected = context.user_data.get('collected_methods', {})
    
    # 1. Защита: если данных нет
    if not collected:
        text = "❌ <b>Данные не найдены.</b>\nВозможно, сессия истекла."
        keyboard = [[InlineKeyboardButton("◀️ В начало", callback_data="back_to_categories")]]
        await _send_universal(update_or_query, context, text, InlineKeyboardMarkup(keyboard))
        return -1

    # Получаем юзернейм для ссылки (если есть в базе/контексте)
    # Замени на реальный подбор домена из твоего конфига
    user_slug = context.user_data.get('user_slug', 'my_page')
    site_url = f"https://botolink.pro/{user_slug}"

    # 2. Формируем отчет
    text = "🧐 <b>ПРОВЕРКА ВВЕДЕННЫХ ДАННЫХ</b>\n"
    text += "───────────────────\n"
    text += f"📍 Эти данные будут на: <u>{site_url}</u>\n\n"
    
    for method_id, data in collected.items():
        # Находим красивое имя метода
        method_display_name = method_id.replace('_', ' ').title()
        for country_list in COUNTRY_METHODS.values():
            m_info = next((m for m in country_list if m['id'] == method_id), None)
            if m_info:
                method_display_name = m_info['name']
                break
        
        text += f"🏛 <b>{method_display_name.upper()}</b>\n"
        
        # Перебираем поля (банк, номер и т.д.)
        for field_id, value in data.items():
            if field_id == "icon": continue # Иконку не пишем текстом
            
            label = FIELD_NAMES.get(field_id, field_id.replace('_', ' ').capitalize())
            
            # Исправляем регистр для имен и названий банков
            display_value = value.title() if field_id in ["bank_name", "beneficiary"] else value
            
            text += f"  ├ {label}: <code>{display_value}</code>\n"
        
        text += "───────────────────\n"
    
    text += "\n🚀 <b>Все верно? Сохраняем на сайт?</b>"
    
    # 3. Кнопки
    keyboard = [
        [InlineKeyboardButton("✅ ДА, ОПУБЛИКОВАТЬ", callback_data="save_all_methods")],
        [InlineKeyboardButton("✏️ ИСПРАВИТЬ ОШИБКИ", callback_data="restart_filling")],
        [InlineKeyboardButton("❌ ОТМЕНА", callback_data="back_to_countries")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await _send_universal(update_or_query, context, text, reply_markup)
    return 503

async def _send_universal(update_or_query, context, text, reply_markup):
    """Вспомогательная функция для отправки/редактирования"""
    chat_id = update_or_query.effective_chat.id
    try:
        if hasattr(update_or_query, 'callback_query') and update_or_query.callback_query:
            await update_or_query.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML', disable_web_page_preview=True)
        else:
            await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML', disable_web_page_preview=True)
    except Exception:
        await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')
        




def generate_payment_link(method_id: str, data: dict) -> str:
    """Генерирует кастомный протокол ссылки на основе данных метода для фронтенда"""
    
    # Очистка строк от пробелов и плюсов для чистых протоколов
    def clean(key):
        val = data.get(key, '')
        if isinstance(val, str):
            return val.replace(' ', '').replace('+', '')
        return str(val)

    # 💳 КАРТЫ (card_lithuania, card_russia, card_vietnam и т.д.)
    if 'card' in method_id:
        # Проверяем все возможные ключи номера карты
        card = clean('card_number') or clean('card')
        return f"card://{card}"
    
    # 📱 ТЕЛЕФОН / СБП (phone_russia, phone_uzbekistan, vkpay, click, payme)
    elif 'phone' in method_id or method_id in ['vkpay', 'click', 'payme', 'tbcpay']:
        phone = clean('phone')
        return f"tel://{phone}"
    
    # 🏦 IBAN / SEPA (iban_lithuania, wise, revolut)
    elif 'iban' in method_id or method_id in ['wise', 'revolut']:
        iban = clean('iban')
        if not iban and method_id == 'revolut':
            # Если для Revolut ввели только тег
            tag = clean('tag')
            return f"revolut://{tag}"
        return f"iban://{iban}"
    
    # 🧾 СЧЕТА (account_russia, account_armenia, non_res_vietnam)
    elif 'account' in method_id or 'non_res' in method_id:
        acc = clean('account') or clean('account_number')
        return f"account://{acc}"
    
    # 🇷🇺 ЮMONEY
    elif method_id == 'yoomoney':
        wallet = clean('wallet')
        return f"yoomoney://{wallet}"
    
    # 🌐 PAYPAL / WISE (Email)
    elif method_id == 'paypal' or (method_id == 'wise' and 'email' in data):
        email = data.get('email', '') or data.get('username', '')
        return f"email://{email}"

    # 🇺🇸 США (ACH / WIRE)
    elif 'ach_usa' in method_id:
        return f"ach://{clean('routing')}/{clean('account')}"
    
    elif 'wire_usa' in method_id:
        return f"wire://{clean('swift')}/{clean('account')}"
    
    # 🆔 КАСПИ / ИДРАМ (могут идти как по карте, так и по телефону)
    elif method_id in ['kaspi', 'idram']:
        val = clean('card') or clean('phone')
        return f"transfer://{val}"

    # Дефолт: если ничего не подошло, просто возвращаем пустую строку или базовый протокол
    return f"unknown://{method_id}"
# ============================================
# РЕДАКТИРОВАНИЕ МЕТОДОВ
# ============================================
# // D:\aRabota\TelegaBoom\030_mylinkspace\bot\bankworld.py

async def edit_methods(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возвращает к выбору методов для редактирования"""
    query = update.callback_query
    await query.answer()
    
    country = context.user_data.get('selected_country')
    methods = COUNTRY_METHODS.get(country, [])
    selected = context.user_data.get('selected_methods', [])
    collected = context.user_data.get('collected_methods', {}) # Твои заполненные данные
    
    country_name = COUNTRY_NAMES.get(country, country.capitalize())
    
    text = f"🏴 <b>{country_name}</b>\n"
    text += "───────────────────\n"
    text += "✏️ <b>Редактирование списка</b>\n"
    text += "Нажмите на метод, чтобы добавить или удалить его:\n\n"
    
    keyboard = []
    
    for method in methods:
        method_id = method['id']
        is_selected = method_id in selected
        is_filled = method_id in collected
        
        # Формируем иконку состояния
        if is_selected and is_filled:
            prefix = "✅" # Выбран и заполнен
            status = " (заполнено)"
        elif is_selected:
            prefix = "🔘" # Выбран, но еще не заполнен
            status = " (нужны данные)"
        else:
            prefix = "⬜" # Не выбран
            status = ""
            
        button_text = f"{prefix} {method['name']}{status}"
        
        keyboard.append([
            InlineKeyboardButton(button_text, callback_data=f"edit_toggle_{method_id}")
        ])
    
    # Кнопки навигации
    keyboard.append([InlineKeyboardButton("➡️ Готово (Вернуться)", callback_data="start_filling")])
    # Если заново нажать start_filling, он проверит очередь и отправит в финал или на дозаполнение
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    return 20 # Стейт WAIT_METHOD_SELECTION

# ============================================
# ОБРАБОТКА РЕДАКТИРОВАНИЯ
# ============================================
# // bot/bankworld.py

async def edit_toggle_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Убирает или добавляет метод при редактировании, обновляя полные данные"""
    query = update.callback_query
    await query.answer()
    
    method_id = query.data.replace("edit_toggle_", "")
    selected = context.user_data.get('selected_methods', [])
    collected = context.user_data.get('collected_methods', {})
    full_dict = context.user_data.get('selected_methods_full', {})
    
    country = context.user_data.get('selected_country')
    
    if method_id in selected:
        # 1. УДАЛЯЕМ
        selected.remove(method_id)
        if method_id in collected:
            del collected[method_id]
        if method_id in full_dict:
            del full_dict[method_id]
        print(f"🗑 Метод {method_id} удален из всех списков")
    else:
        # 2. ДОБАВЛЯЕМ
        selected.append(method_id)
        
        # Находим полные данные метода в COUNTRY_METHODS
        country_methods = COUNTRY_METHODS.get(country, [])
        found_method = next((m for m in country_methods if m['id'] == method_id), None)
        
        if found_method:
            # Копируем данные, чтобы не менять глобальный словарь
            full_dict[method_id] = found_method.copy()
            print(f"➕ Метод {method_id} добавлен в очередь на заполнение")

    # Сохраняем обновленные данные обратно в context
    context.user_data['selected_methods'] = selected
    context.user_data['collected_methods'] = collected
    context.user_data['selected_methods_full'] = full_dict
    
    # Обновляем сообщение с кнопками (функция edit_methods)
    await edit_methods(update, context)
    return 20 # WAIT_METHOD_SELECTION

# ============================================
# ПРОДОЛЖИТЬ ПОСЛЕ РЕДАКТИРОВАНИЯ
# ============================================
# // bot/bankworld.py

async def continue_after_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Продолжает заполнение после редактирования.
    Формирует новую очередь только из тех методов, для которых НЕТ данных.
    """
    query = update.callback_query
    await query.answer()
    
    print(f"🌍 bankworld.py: переход после редактирования")
    
    selected = context.user_data.get('selected_methods', [])
    collected = context.user_data.get('collected_methods', {})
    
    # 1. Находим только те методы, которые выбраны, но еще не заполнены
    unfilled = [m for m in selected if m not in collected]
    
    if unfilled:
        print(f"📝 Нужно дозаполнить методы: {unfilled}")
        
        # Обновляем очередь и ОБЯЗАТЕЛЬНО сбрасываем индекс поля
        context.user_data['filling_queue'] = unfilled
        context.user_data['current_field_index'] = 0
        
        # Запускаем процесс опроса
        return await ask_next_method(update, context)
    
    else:
        # 2. Если всё уже заполнено (или юзер всё удалил)
        print("✅ Все методы заполнены, идем в превью")
        
        if not selected:
            # Если юзер вообще всё снял, возвращаем к выбору стран или категорий
            await query.edit_message_text("⚠️ Вы не выбрали ни одного метода.")
            return 20 # WAIT_METHOD_SELECTION
            
        return await show_filling_complete(update, context)

# ============================================
# СОХРАНЕНИЕ ВСЕХ МЕТОДОВ В БАЗУ (ИСПРАВЛЕННАЯ)
# ============================================
import json # Добавь в начало файла или оставь здесь


# // bot/bankworld.py

async def restart_filling(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Полностью перезапускает процесс заполнения для текущей страны"""
    query = update.callback_query
    await query.answer()
    
    print(f"🔄 Перезапуск процесса заполнения...")
    
    # 1. Сохраняем страну ПЕРЕД очисткой
    selected_country = context.user_data.get('selected_country')
    
    # 2. Список ключей (убрал selected_country из списка, чтобы не удалять лишний раз)
    keys_to_clear = [
        'selected_methods',
        'filling_queue',
        'collected_methods',
        'current_method',
        'current_field_index',
        'payment_data',
        'revolut_data',
        'wise_data',
        'selected_methods_full'
    ]
    
    for key in keys_to_clear:
        if key in context.user_data:
            del context.user_data[key]
    
    # 3. Возврат к выбору
    if selected_country:
        print(f"📡 Возвращаемся к списку методов для: {selected_country}")
        # Вызываем функцию показа методов (убедись, что она импортирована или в этом же файле)
        return await show_country_methods(update, context)
    else:
        print("⚠️ Страна не найдена, возврат к выбору страны")
        # Используем твой импорт
        try:
            from bot.bank import choose_country
            return await choose_country(update, context)
        except ImportError:
            # Если файл называется по-другому, подправь путь
            await query.edit_message_text("❌ Ошибка навигации. Начните заново: /addlink")
            return ConversationHandler.END
        
        
# ============================================
# ОТМЕНА ВСЕГО ПРОЦЕССА
# ============================================
# // bot/bankworld.py

async def cancel_filling(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Полностью отменяет процесс заполнения и завершает ConversationHandler.
    """
    query = update.callback_query
    await query.answer()
    
    print(f"🛑 Отмена заполнения пользователем {update.effective_user.id}")
    
    # Список всех ключей, которые мы использовали в этом флоу
    keys_to_purge = [
        'selected_methods', 'filling_queue', 'collected_methods',
        'current_method', 'selected_country', 'current_field_index',
        'selected_methods_full', 'payment_data'
    ]
    
    for key in keys_to_purge:
        context.user_data.pop(key, None)
    
    # Текст уведомления (добавил название команды из твоего описания)
    await query.edit_message_text(
        "❌ <b>Процесс добавления способов отменен.</b>\n\n"
        "Данные не были сохранены. Вы можете начать заново, используя команду /addlink",
        parse_mode='HTML'
    )
    
    return ConversationHandler.END