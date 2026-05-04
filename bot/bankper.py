# D:\aRabota\TelegaBoom\030_mylinkspace\bot\bankper.py
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.constructor import process_current_step
from bot.utils import get_db_connection
from bot.bank import choose_country
from bot.parsers import parse_and_validate

# D:\aRabota\TelegaBoom\030_mylinkspace\bot\bankper.py



BANK_PER_CONFIG = {
    "paypal": {
        "name": "PayPal",
        "icon": "paypal",
        "category": "transfers",
        "url_template": "paypal_logic",
        "steps": [
            {
                "type": "text",
                "question": "🔗 <b>Введите ваш PayPal (Username или Ссылку)</b>\n\n"
                            "Примеры:\n"
                            "• <code>dkvpay</code>\n"
                            "• <code>paypal.me/dkvpay</code>\n\n"
                            "👇 <b>Вводите текст в поле чата бота</b>",
                "field": "link",
                "optional": False
            },
            {
                "type": "title",
                "question": "📝 <b>Название для карточки (можно пропустить)</b>\n\n"
                            "Напр: <code>Мой PayPal</code>\n\n"
                            "👇 <b>Впишите текст или нажмите «Пропустить»</b>",
                "field": "title",
                "optional": True
            }
        ]
    },

    "revolut": {
        "name": "Revolut",
        "icon": "revolut",
        "category": "transfers",
        "url_template": "https://revolut.me/{val}",
        "steps": [
            {
                "type": "text",
                "question": "🔗 <b>Ваша ссылка Revolut.me</b>\n\n"
                            "Пример: <code>denmailde</code>\n"
                            "или <code>revolut.me/denmailde</code>\n\n"
                            "👇 <b>Введите логин или ссылку:</b>",
                "field": "login",
                "optional": False
            },
            {
                "type": "text",
                "question": "👤 <b>Имя получателя (Beneficiary)</b>\n\n"
                            "Пример: <code>Deniss Kabakovs</code>\n\n"
                            "👇 <b>Введите ФИО или нажмите «⏭ Пропустить»</b>",
                "field": "recipient",
                "optional": True
            },
            {
                "type": "text",
                "question": "🏦 <b>Номер счета (IBAN)</b>\n\n"
                            "Пример: <code>LT67 3250 0982 ...</code>\n\n"
                            "👇 <b>Введите IBAN или нажмите «⏭ Пропустить»</b>",
                "field": "iban",
                "optional": True
            },
            {
                "type": "text",
                "question": "🌐 <b>BIC / SWIFT код</b>\n\n"
                            "Пример: <code>REVOLT21</code>\n\n"
                            "👇 <b>Введите код или нажмите «⏭ Пропустить»</b>",
                "field": "swift",
                "optional": True
            },
            {
                "type": "text",
                "question": "🏢 <b>Банк-корреспондент (Correspondent)</b>\n\n"
                            "Пример: <code>CHASDEFX</code>\n\n"
                            "👇 <b>Введите код или нажмите «⏭ Пропустить»</b>",
                "field": "correspondent",
                "optional": True
            },
            {
                "type": "text",
                "question": "🏠 <b>Адрес банка (Bank Address)</b>\n\n"
                            "Пример: <code>Konstitucijos ave. 21B, Vilnius, Lithuania</code>\n\n"
                            "👇 <b>Введите адрес или нажмите «⏭ Пропустить»</b>",
                "field": "address",
                "optional": True
            },
            {
                "type": "title",
                "question": "📝 <b>Название карточки</b>\n\n"
                            "Напр: <code>Euro (SEPA)</code> или <code>Личный Revolut</code>\n\n"
                            "👇 <b>Введите текст или нажмите «⏭ Пропустить»</b>",
                "field": "title",
                "optional": True
            }
        ]
    },

    "wise": {
        "name": "Wise",
        "icon": "wise",
        "category": "transfers",
        "url_template": "{val}",
        "steps": [
            {
                "type": "text",
                "question": "🔗 <b>Ваша ссылка или логин Wise</b>\n\n"
                            "Пример: <code>wise.com/pay/me/denissk</code>\n"
                            "или просто <code>denissk</code>\n\n"
                            "👇 <b>Введите данные в поле чата бота:</b>",
                "field": "identifier",
                "optional": False
            },
            {
                "type": "text",
                "question": "👤 <b>Имя получателя (Beneficiary)</b>\n\n"
                            "Пример: <code>Deniss Kabakovs</code>\n\n"
                            "👇 <b>Введите ФИО или нажмите «⏭ Пропустить»</b>",
                "field": "recipient",
                "optional": True
            },
            {
                "type": "text",
                "question": "🏦 <b>Номер счета (IBAN)</b>\n\n"
                            "Пример: <code>BE12 3456 7890 ...</code>\n\n"
                            "👇 <b>Введите IBAN или нажмите «⏭ Пропустить»</b>",
                "field": "iban",
                "optional": True
            },
            {
                "type": "text",
                "question": "🌐 <b>BIC / SWIFT код</b>\n\n"
                            "Пример: <code>PPROBEB1</code>\n\n"
                            "👇 <b>Введите код или нажмите «⏭ Пропустить»</b>",
                "field": "swift",
                "optional": True
            },
            {
                "type": "text",
                "question": "🏢 <b>Банк-корреспондент (Correspondent)</b>\n\n"
                            "Пример: <code>CHASDEFX</code>\n\n"
                            "👇 <b>Введите код или нажмите «⏭ Пропустить»</b>",
                "field": "correspondent",
                "optional": True
            },
            {
                "type": "text",
                "question": "🏠 <b>Адрес банка (Bank Address)</b>\n\n"
                            "Пример: <code>Avenue Louise 54, Brussels, Belgium</code>\n\n"
                            "👇 <b>Введите адрес или нажмите «⏭ Пропустить»</b>",
                "field": "address",
                "optional": True
            },
            {
                "type": "title",
                "question": "📝 <b>Название карточки</b>\n\n"
                            "Напр: <code>Wise EUR</code>\n\n"
                            "👇 <b>Введите текст или нажмите «⏭ Пропустить»</b>",
                "field": "title",
                "optional": True
            }
        ]
    },
    "swift": {
            "name": "SWIFT/IBAN",
            "icon": "swiftiban",
            "category": "transfers",
            "steps": [
                {
                    "type": "text",
                    "field": "iban",
                    "question": "🏦 <b>Введите номер счета (IBAN)</b>\n\nПример: <code>DE12 3456 7890 ...</code>\n\n👇 <b>Вводите текст в поле чата бота</b>",
                    "optional": False
                },
                {
                    "type": "text",
                    "field": "recipient",
                    "question": "👤 <b>Имя получателя (на латинице)</b>\n\nПример: <code>Ivan Ivanov</code>\n\n👇 <b>Впишите ФИО в поле чата</b>",
                    "optional": False
                },
                {
                    "type": "text",
                    "field": "swift",
                    "question": "🌐 <b>SWIFT / BIC код банка</b>\n\nПример: <code>DBSSDEFF</code>\n\n👇 <b>Впишите код или нажмите «⏭ Пропустить»</b>",
                    "optional": True
                },
                {
                    "type": "text",
                    "field": "bank_name",
                    "question": "🏛 <b>Название банка</b>\n\nПример: <code>Deutsche Bank</code>\n\n👇 <b>Впишите название или нажмите «⏭ Пропустить»</b>",
                    "optional": True
                },
                {
                    "type": "text",
                    "field": "address",
                    "question": "🏠 <b>Адрес банка или получателя</b>\n\nПример: <code>Berlin, Germany</code>\n\n👇 <b>Впишите адрес или нажмите «⏭ Пропустить»</b>",
                    "optional": True
                },
                {
                    "type": "title",
                    "field": "title",
                    "question": "📝 <b>Название карточки</b>\n\nНапр: <code>Личный счет (EUR)</code>\n\n👇 <b>Впишите текст или нажмите «⏭ Пропустить»</b>",
                    "optional": True
                }
            ]
        },
    
        "yoomoney": {
            "name": "ЮMoney",
            "icon": "yoomoney",
            "category": "transfers",
            "steps": [
                {
                    "type": "text",
                    "field": "identifier",
                    "question": "💜 <b>Номер кошелька ЮMoney</b>\n\nПример: <code>410012345678901</code>\n\n👇 <b>Введите номер кошелька в поле чата</b>",
                    "optional": False
                },
                {
                    "type": "title",
                    "field": "title",
                    "question": "📝 <b>Название карточки (можно пропустить)</b>\n\nНапр: <code>ЮMoney</code>\n\n👇 <b>Впишите текст или нажмите «⏭ Пропустить»</b>",
                    "optional": True
                }
            ]
        },
    
    "vkpay": {
            "name": "VK Pay",
            "icon": "vkpay",
            "category": "transfers",
            "steps": [
                {
                    "type": "text",
                    "field": "identifier",
                    "question": "💙 <b>ID пользователя или ссылка VK Pay</b>\n\nПример: <code>12345678</code> или <code>https://vk.com/vkpay#to12345678</code>\n\n👇 <b>Введите данные в поле чата</b>",
                    "optional": False
                },
                {
                    "type": "title",
                    "field": "title",
                    "question": "📝 <b>Название карточки (можно пропустить)</b>\n\nНапр: <code>Мой VK Pay</code>\n\n👇 <b>Впишите текст или нажмите «⏭ Пропустить»</b>",
                    "optional": True
                }
            ]
        },
    
    "monobank": {
        "name": "Monobank",
        "icon": "monobank",
        "category": "transfers",
        "steps": [
            {
                "type": "text",
                "field": "link",
                "question": "🏦 <b>Ссылка на банку или карту Monobank</b>\n\nПример: <code>send.monobank.ua/abc123</code>\n\n👇 <b>Вставьте ссылку в поле чата бота</b>",
                "optional": False
            },
            {
                "type": "title",
                "field": "title",
                "question": "📝 <b>Название карточки (можно пропустить)</b>\n\nНапр: <code>Банка на мечту</code>\n\n👇 <b>Впишите текст или нажмите «⏭ Пропустить»</b>",
                "optional": True
            }
        ]
    },

    "kaspi": {
        "name": "Kaspi.kz",
        "icon": "kaspi",
        "category": "transfers",
        "steps": [
            {
                "type": "text",
                "field": "identifier",
                "question": "🇰🇿 <b>Номер телефона Kaspi</b>\n\nПример: <code>+77011234567</code>\n\n👇 <b>Введите номер в поле чата бота</b>",
                "optional": False
            },
            {
                "type": "text",
                "field": "recipient",
                "question": "👤 <b>Имя получателя (можно пропустить)</b>\n\nПример: <code>Иван И.</code>\n\n👇 <b>Впишите имя или нажмите «⏭ Пропустить»</b>",
                "optional": True
            },
            {
                "type": "title",
                "field": "title",
                "question": "📝 <b>Название карточки (можно пропустить)</b>\n\nНапр: <code>Мой Kaspi</code>\n\n👇 <b>Впишите текст или нажмите «⏭ Пропустить»</b>",
                "optional": True
            }
        ]
    },

    "payme": {
            "name": "Payme",
            "icon": "payme",
            "category": "transfers",
            "steps": [
                {
                    "type": "text",
                    "field": "identifier",
                    "question": "💳 <b>Номер карты или ID Payme</b>\n\nПримеры:\n— <code>8600123456789012</code>\n— <code>@deniss_k</code>\n— <code>https://payme.uz/@deniss_k</code>\n\n👇 <b>Введите данные в поле чата</b>",
                    "optional": False
                },
                {
                    "type": "title",
                    "field": "title",
                    "question": "📝 <b>Название карточки (можно пропустить)</b>\n\nНапр: <code>Payme UZ</code>\n\n👇 <b>Впишите текст или нажмите «⏭ Пропустить»</b>",
                    "optional": True
                }
            ]
        },

    "click_uz": {
            "name": "Click.uz",
            "icon": "click_uz",
            "category": "transfers",
            "steps": [
                {
                    "type": "text",
                    "field": "identifier",
                    "question": "🔵 <b>Номер телефона или ID Click</b>\n\nПример: <code>99890...</code>\n\n👇 <b>Введите данные в поле чата</b>",
                    "optional": False
                },
                {
                    "type": "title",
                    "field": "title",
                    "question": "📝 <b>Название карточки (можно пропустить)</b>\n\nНапр: <code>Click</code>\n\n👇 <b>Впишите текст или нажмите «⏭ Пропустить»</b>",
                    "optional": True
                }
            ]
        },
    
    "tbcpay": {
        "name": "TBC Pay",
        "icon": "tbcpay",
        "category": "transfers",
        "steps": [
            {
                "type": "text",
                "field": "identifier",
                "question": "🏦 <b>Номер счета или ID TBC Pay</b>\n\n👇 <b>Введите данные в поле чата</b>",
                "optional": False
            },
            {
                "type": "title",
                "field": "title",
                "question": "📝 <b>Название карточки (можно пропустить)</b>\n\nНапр: <code>TBC Bank</code>\n\n👇 <b>Впишите текст или нажмите «⏭ Пропустить»</b>",
                "optional": True
            }
        ]
    },

    "idram": {
        "name": "Idram",
        "icon": "idram",
        "category": "transfers",
        "steps": [
            {
                "type": "text",
                "field": "identifier",
                "question": "🇦🇲 <b>Номер счета или телефон Idram</b>\n\nПример: <code>091234567</code>\n\n👇 <b>Введите данные в поле чата бота</b>",
                "optional": False
            },
            {
                "type": "title",
                "field": "title",
                "question": "📝 <b>Название карточки (можно пропустить)</b>\n\nНапр: <code>Idram Кошелек</code>\n\n👇 <b>Впишите текст или нажмите «⏭ Пропустить»</b>",
                "optional": True
            }
        ]
    }
}




async def save_bank_link_to_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Универсальное сохранение банковских реквизитов в БД"""
    # Вытаскиваем ключ банка и ответы из контекста
    bank_key = context.user_data.get('current_bank_key')
    answers = context.user_data.get('flow_answers', {})
    config = BANK_PER_CONFIG.get(bank_key, {})
    
    # 1. ВЫЗЫВАЕМ ПАРСЕР (он возвращает финальный URL или ошибку)
    from bot.parsers import parse_and_validate
    
    final_url, error = await parse_and_validate(bank_key, answers)
    
    if error and final_url is None:
        print(f"❌ [SAVE] Ошибка валидации: {error}")
        await update.effective_message.reply_text(f"⚠️ {error}")
        return 282 # Возвращаем на ввод, если парсер забраковал данные

    # 2. Собираем основной идентификатор (ссылка, логин или сам номер счета)
    # Ищем во всех возможных полях, что ввел юзер
    raw_id = (answers.get('link') or
              answers.get('login') or
              answers.get('identifier') or
              answers.get('iban', ''))
    
    # 3. Формируем pay_details для хранения в JSON-колонке БД
    pay_details = {
        "type": bank_key,
        "payment_type": bank_key,
        "link": str(raw_id)
    }
    
    # СПИСОК ВСЕХ ПОЛЕЙ (включая новые для Kaspi, Idram, ЮMoney и т.д.)
    fields_to_save = [
        'iban', 'swift', 'recipient', 'address', 'bank_name',
        'wise_email', 'wise_phone', 'correspondent', 'identifier'
    ]
    
    for f in fields_to_save:
        if answers.get(f):
            pay_details[f] = answers[f]

    # 4. Работа с базой данных
    conn = await get_db_connection()
    try:
        # Получаем данные страницы пользователя
        user_row = await conn.fetchrow("""
            SELECT p.id as page_id, p.username
            FROM users u
            JOIN pages p ON u.id = p.user_id
            WHERE u.telegram_id = $1
        """, update.effective_user.id)
        
        if not user_row:
            print("❌ [SAVE] Пользователь не найден в БД")
            return -1

        page_id = user_row['page_id']
        username = user_row['username']
        
        # Определяем заголовок: приоритет у ввода юзера, иначе имя из конфига
        title = answers.get('title') or config.get('name', bank_key.capitalize())
        
        # Считаем текущий порядок сортировки, чтобы добавить в конец
        max_order = await conn.fetchval(
            "SELECT COALESCE(MAX(sort_order), 0) FROM links WHERE page_id = $1",
            page_id
        )

        # СОХРАНЯЕМ В ТАБЛИЦУ LINKS
        # Используем json.dumps для корректной записи словаря в JSONB колонку
        import json
        await conn.execute("""
            INSERT INTO links (page_id, title, url, icon, sort_order, is_active, pay_details, category)
            VALUES ($1, $2, $3, $4, $5, true, $6, 'transfers')
        """, page_id, title, final_url, config.get('icon', 'bank'), max_order + 1, json.dumps(pay_details))
        
        print(f"✅ [SAVE] {bank_key} сохранен для @{username}")
        
    except Exception as e:
        print(f"❌ [SAVE] Ошибка БД: {e}")
        await update.effective_message.reply_text("⛔️ Ошибка при сохранении в базу данных.")
        return -1
    finally:
        if conn: await conn.close()

    # 5. Очистка временных данных (чтобы следующий банк настраивался чисто)
    for key in ['flow_config', 'flow_step_index', 'flow_answers', 'current_bank_key']:
        context.user_data.pop(key, None)
    
    # Возвращаем категорию в контекст для удобства навигации
    context.user_data['category'] = 'transfers'

    # Формируем красивый текст подтверждения
    success_text = (
        f"✅ <b>{config.get('name')} успешно добавлен!</b>\n\n"
        f"📍 <b>Название:</b> {title}\n"
        
        f"🚀 <b>Твоя страница обновлена:</b>\n"
        f"👉 <a href='https://botolink.pro/{username}'>botolink.pro/{username}</a>"
    )
    
    # Кнопки после сохранения
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Открыть страницу", url=f"https://botolink.pro/{username}")],
        [InlineKeyboardButton("➕ Добавить ещё банк", callback_data="cat_transfers")],
        [InlineKeyboardButton("🏠 В главное меню", callback_data="start")]
    ])
    
    # Отправляем новое сообщение с подтверждением успеха
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=success_text,
        reply_markup=keyboard,
        parse_mode='HTML',
        disable_web_page_preview=True
    )

    # Завершаем текущий ConversationHandler
    return -1


# Название файла: bot/bankper.py

async def start_bank_config_flow(update: Update, context: ContextTypes.DEFAULT_TYPE, bank_key: str):
    """Инициализация процесса настройки банка (PayPal, Wise, Revolut)"""
    # 1. Загружаем конфиг конкретного банка
    config = BANK_PER_CONFIG.get(bank_key)
    if not config:
        print(f"❌ [START] Конфиг для {bank_key} не найден!")
        return 20 # Возврат в выбор категорий

    # 2. Очищаем старые хвосты и готовим данные
    context.user_data['flow_config'] = config
    context.user_data['flow_step_index'] = 0
    context.user_data['flow_answers'] = {}
    context.user_data['current_bank_key'] = bank_key
    
    # 👇👇👇 ДОБАВЬ ЭТУ СТРОКУ 👇👇👇
    context.user_data['link_type'] = bank_key  # Сохраняем тип для save_link
    # 👆👆👆👆👆👆👆👆👆👆👆👆👆👆
    
    # 3. ЗАПОМИНАЕМ ID СООБЩЕНИЯ, чтобы потом его редактировать
    if update.callback_query:
        context.user_data['last_flow_msg_id'] = update.callback_query.message.message_id
        print(f"🚀 [START] Начинаем {bank_key}, MsgID: {update.callback_query.message.message_id}")

    # 4. Вызываем отрисовку первого шага
    await render_flow_step(update, context)
    
    # ВАЖНО: Возвращаем стейт 282 (где работает handle_flow_input для текста)
    return 282







# D:\aRabota\TelegaBoom\030_mylinkspace\bot\bankper.py

async def check_next_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Универсальный проверяльщик:
    Идем дальше по списку или показываем финал?
    """
    config = context.user_data.get('flow_config')
    # Берем индекс, который МЫ УЖЕ ОБНОВИЛИ в обработчике ввода
    idx = context.user_data.get('flow_step_index', 0)
    
    print(f"⚖️ [CHECK] Проверка: шаг {idx} из {len(config['steps'])}")

    # Если индекс равен или больше длины списка шагов — всё, приехали
    if idx >= len(config['steps']):
        print("🏁 [CHECK] Все шаги пройдены. Показываем подтверждение.")
        return await render_flow_confirmation(update, context)
    
    # Если шаги еще есть — рисуем следующий
    return await render_flow_step(update, context)






async def back_to_transfers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await choose_country(update, context)

# D:\aRabota\TelegaBoom\030_mylinkspace\bot\bankper.py



async def render_flow_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Финальный экран: выводит все введенные данные 'простыней'"""
    answers = context.user_data.get('flow_answers', {})
    bank_key = context.user_data.get('current_bank_key', 'unknown')
    
    # Формируем заголовок в зависимости от типа
    title = f"<b>🏦 Подтвердите данные {bank_key.upper()}</b>\n"
    title += "────────────────────\n\n"
    
    # Собираем все заполненные поля в одну строку
    details = ""
    
    # Словарь человекочитаемых названий для полей
    field_names = {
        "bank_name": "🏦 Банк",
        "recipient": "👤 Получатель",
        "iban": "💳 IBAN",
        "swift": "🌐 SWIFT/BIC",
        "address": "🏠 Адрес",
        "identifier": "🔗 Логин/Email",
        "correspondent": "🏢 Корреспондент",
        "title": "📝 Заголовок карточки"
    }

    for field, value in answers.items():
        if value: # Показываем только заполненные поля
            name = field_names.get(field, field.capitalize())
            details += f"{name}: <code>{value}</code>\n"

    full_text = f"{title}{details}\n────────────────────\nВсе верно? Нажмите сохранить, чтобы опубликовать на странице."

    keyboard = [
        [InlineKeyboardButton("💾 Сохранить и опубликовать", callback_data="flow_confirm_save")],
        [InlineKeyboardButton("🔄 Исправить (заново)", callback_data=f"method_{bank_key}")],
        [InlineKeyboardButton("🔙 Отмена", callback_data="back_to_transfers")]
    ]

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=full_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=full_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

    return 503






# Название файла: bot/bankper.py

async def render_flow_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отрисовка текущего шага. Шлет новое сообщение, сохраняя историю."""
    config = context.user_data.get('flow_config')
    step_idx = context.user_data.get('flow_step_index', 0)
    step = config['steps'][step_idx]
    bank_key = context.user_data.get('current_bank_key', 'unknown')
    
    # ЛОГ: Какой шаг показываем
    print(f"📝 [RENDER] Банк: {bank_key.upper()} | Шаг: {step_idx+1}/{len(config['steps'])} | Поле: {step['field']}")

    keyboard = []
    if step.get('optional'):
        keyboard.append([InlineKeyboardButton("⏭ Пропустить", callback_data="flow_skip")])

    if step.get('type') == "choice":
        for opt in step['options']:
            keyboard.append([InlineKeyboardButton(opt['label'], callback_data=f"flow_opt_{opt['next_step']}||{opt['value']}")])

    keyboard.append([InlineKeyboardButton("🔙 Отмена", callback_data="back_to_transfers")])
    
    text = step['question']
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

    return 282




async def handle_flow_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопок внутри флоу (Пропустить, Выбор, Сохранить)"""
    query = update.callback_query
    data = query.data
    await query.answer()
    
    # 1. Сразу проверяем сохранение
    if data == "flow_confirm_save":
        print("💾 [CALLBACK] Нажато 'Сохранить в базу'")
        return await save_bank_link_to_db(update, context)
    
    # 2. Подгружаем контекст
    bank_key = context.user_data.get('current_bank_key')
    config = BANK_PER_CONFIG.get(bank_key)
    
    if not config:
        print(f"❌ [CALLBACK] Конфиг для {bank_key} не найден!")
        return 20

    steps = config['steps']
    idx = context.user_data.get('flow_step_index', 0)
    
    # Гарантируем наличие словаря для ответов
    context.user_data.setdefault('flow_answers', {})

    # 3. Обработка действий
    if data == "flow_skip":
        print(f"⏭ [CALLBACK] {bank_key.upper()} | Шаг {idx} пропущен")
        next_idx = idx + 1
        
    elif data.startswith("flow_opt_"):
        # Логика для выбора из вариантов (например, тип аккаунта в Wise)
        try:
            parts = data.replace("flow_opt_", "").split("||")
            # Если в кнопке зашит переход на конкретный шаг, берем его, иначе просто +1
            next_idx = int(parts[0]) if parts[0].isdigit() else idx + 1
            val = parts[1]
            
            # Записываем значение в текущее поле
            field_name = steps[idx]['field']
            context.user_data['flow_answers'][field_name] = val
            print(f"✅ [CALLBACK] {bank_key.upper()} | Поле {field_name} = {val}")
        except (IndexError, ValueError):
            next_idx = idx + 1
    else:
        # Для всех остальных случаев (на всякий случай)
        next_idx = idx + 1

    # 4. Обновляем индекс и решаем, куда слать юзера
    context.user_data['flow_step_index'] = next_idx

    # Если шаги закончились — выводим финальную простыню
    if next_idx >= len(steps):
        return await render_flow_confirmation(update, context)

    # Если нет — рисуем следующий вопрос
    return await render_flow_step(update, context)


async def handle_flow_skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Просто двигаем индекс вперед, ничего не записывая в flow_answers
    context.user_data['flow_step_index'] += 1
    config = context.user_data.get('flow_config')

    if context.user_data['flow_step_index'] < len(config['steps']):
        return await render_flow_step(update, context)
    else:
        return await render_flow_confirmation(update, context)




async def handle_flow_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстового ввода для пошагового конструктора (Соцсети/Email)"""
    print("\n" + "=" * 60)
    print("📥 handle_flow_input ВЫЗВАН")
    
    # В handle_flow_input, первая строка после print
    if 'flow_config' in context.user_data:
        context.user_data['type_config'] = context.user_data['flow_config']
    # --- ВОТ ЭТО ДОБАВЬ ---
    try:
        await update.message.delete() # Удаляем ввод юзера, чтобы не мусорить
    except Exception as e:
        print(f"⚠️ Не удалось удалить сообщение: {e}")
    # -----------------------
    
    # 1. Забираем текст
    text = update.message.text.strip()
    
    # --- ЗАЩИТА ОТ СПАМА ---
    MAX_LENGTH = 200
    if len(text) > MAX_LENGTH:
        print(f"⚠️ [INPUT] Попытка спама: {len(text)} симв.")
        await update.message.reply_text(
            f"⚠️ <b>Текст слишком длинный!</b> (макс. {MAX_LENGTH})",
            parse_mode='HTML'
        )
        # Возвращаем текущий стейт (1001), чтобы остаться на этом же шаге
        return 1001

    # 2. Достаем конфиг (используем ключи из лога handle_type)
    config = context.user_data.get('type_config')
    step_idx = context.user_data.get('step_index', 0)
    
    if not config or 'steps' not in config:
        print("❌ ОШИБКА: Конфиг не найден в user_data")
        return 1200 # Назад в категории

    # 3. Сохраняем ответ
    steps = config.get('steps', [])
    if step_idx < len(steps):
        current_step = steps[step_idx]
        field_name = current_step.get('field', f'step_{step_idx}')
        
        # Сохраняем в collected_data (как в логе)
        if 'collected_data' not in context.user_data:
            context.user_data['collected_data'] = {}
        
        context.user_data['collected_data'][field_name] = text
        print(f"✅ Сохранено: {field_name} = {text}")
        
        # Увеличиваем индекс
        context.user_data['step_index'] = step_idx + 1
    
    # 4. Переходим к следующему шагу или финалу
    print(f"➡️ Переход к следующему шагу (новый индекс: {context.user_data['step_index']})")
    print("=" * 60)
    
    # Вызываем ту же функцию, что и в handle_type, для отрисовки следующего шага
    return await process_current_step(update, context)
    

async def process_bank_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Определяет выбранный банк и запускает процесс настройки"""
    query = update.callback_query
    data = query.data
    
    bank_key = None
    # Список всех методов, которые должны уходить в универсальную анкету (flow)
    new_methods = [
        "paypal", "revolut", "wise", "iban", "swift",
        "yoomoney", "vkpay", "kaspi", "payme", "click_uz", "idram", "tbcpay", "monobank"
    ]
    
    # Ищем, какой метод был нажат в колбэке
    for key in new_methods:
        if key in data:
            bank_key = key
            break
            
    if bank_key:
        await query.answer()
        # Запускаем флоу анкеты. Теперь для Каспи, Юмани и прочих
        # данные будут браться из BANK_PER_CONFIG по этому ключу.
        return await start_bank_config_flow(update, context, bank_key)
    
    # Если метод не распознан, просто отвечаем на запрос и остаемся в 20 стейте
    await query.answer("Метод не поддерживается", show_alert=True)
    return 20