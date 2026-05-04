# bot/link_constructor.py
"""
Модуль для пошагового создания ссылок с выбором категории и типа
"""

import json
import logging

import asyncpg
from bot.bank import (
    choose_country,
    back_to_countries,
    method_revolut,
    method_paypal,
    revolut_skip_address,
    wise_choice_handler,
    wise_start_full,
    wise_skip_correspondent,
    wise_skip_address,
    process_wise_login,
    process_wise_beneficiary,
    process_wise_iban,
    process_wise_bic,
    process_wise_correspondent,
    process_wise_address,
    process_wise_quick_input
)
from bot.bankworld import show_country_methods
from bot.constructor import process_current_step, back_to_types
from bot.link_utils import add_link_icon  # ← убрать дубликат
from bot.states import (
    SELECT_CATEGORY,  # Шаг 1: Выбор категории
    SELECT_LINK_TYPE,  # Шаг 2: Выбор типа ссылки
    SELECT_FINANCE_SUBTYPE,  # Шаг 3: Выбор подтипа (для финансов)
    ADD_LINK_TITLE,  # Шаг 4: Ввод названия
    ADD_LINK_URL,  # Шаг 5: Ввод URL/реквизитов
    ADD_LINK_DESCRIPTION,  # Шаг 6: Ввод описания (опционально)
    ADD_LINK_ICON, SELECT_PRESET, ADD_CUSTOM_CURRENCY_NAME, SELECT_CRYPTO_NETWORK,
    WAIT_CUSTOM_NETWORK, ADD_MULTI_FINANCE_DATA, __all__, WAIT_WISE_CHOICE, WAIT_WISE_QUICK,
    WAIT_WISE_LOGIN, WAIT_WISE_BENEFICIARY, WAIT_WISE_IBAN, WAIT_WISE_BIC,
    WAIT_WISE_CORRESPONDENT, WAIT_WISE_ADDRESS, WAIT_WISE_FULL, SELECT_COUNTRY  # Шаг 7: Выбор иконки
)
from bot.utils import check_subscription, get_db_connection, get_or_create_user
from core.config import DATABASE_URL, FREE_LINKS_LIMIT, PRO_LINKS_LIMIT
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters, \
    CommandHandler

logger = logging.getLogger(__name__)

# ========== СЛОВАРИ С ДАННЫМИ ДЛЯ КАТЕГОРИЙ ==========

# Названия категорий на русском
# Только то, что видит юзер в самом начале
CATEGORY_NAMES = {
    "social": "📱 Соцсети / Email",
    "messengers": "💬 Мессенджеры",
    "transfers": "💳 Банки / Переводы",
    "donate": "🎨 Донат",
    "wallets_and_crypto_menu": "⚡ Кошельки и Биржи",  # Оставляем только ВХОД в меню
    "shops": "🛍️ Магазины",
    "partner": "🤝 Партнерки",
    "other": "📦 Разное"
}
# Типы ссылок для каждой категории
CATEGORY_LINK_TYPES = {
    "social": [
        {"type": "youtube", "name": "YouTube", "icon": "youtube", "is_finance": False, "needs_description": True},
        {"type": "telegram", "name": "Telegram", "icon": "telegram_social", "is_finance": False,
         "needs_description": True},
        {"type": "tiktok", "name": "TikTok", "icon": "tiktok", "is_finance": False, "needs_description": True},
        {"type": "vk", "name": "VK", "icon": "vk", "is_finance": False, "needs_description": True},
        {"type": "instagram", "name": "Instagram", "icon": "instagram", "is_finance": False, "needs_description": True},
        {"type": "ok", "name": "Одноклассники", "icon": "ok", "is_finance": False, "needs_description": True},
        {"type": "facebook", "name": "Facebook", "icon": "facebook", "is_finance": False, "needs_description": True},
        {"type": "twitter", "name": "Twitter/X", "icon": "twitter", "is_finance": False, "needs_description": True},
        
        {"type": "twitch", "name": "Twitch", "icon": "twitch", "is_finance": False, "needs_description": True},
        {"type": "rutube", "name": "Rutube", "icon": "rutube", "is_finance": False, "needs_description": True},
        {"type": "dzen", "name": "Дзен", "icon": "dzen", "is_finance": False, "needs_description": True},
        {"type": "snapchat", "name": "Snapchat", "icon": "snapchat", "is_finance": False, "needs_description": True},
        {"type": "likee", "name": "Likee", "icon": "likee", "is_finance": False, "needs_description": True},
        {"type": "threads", "name": "Threads", "icon": "threads", "is_finance": False, "needs_description": True},
        {"type": "email", "name": "Email", "icon": "email", "is_finance": False, "needs_description": True, "is_input": True}
        
    
    ],
    
    "messengers": [
        {"type": "whatsapp", "name": "WhatsApp", "icon": "whatsapp", "is_finance": False, "needs_description": False},
        {"type": "viber", "name": "Viber", "icon": "viber", "is_finance": False, "needs_description": False},
        {"type": "signal", "name": "Signal", "icon": "signal", "is_finance": False, "needs_description": False},
        
        {"type": "discord", "name": "Discord", "icon": "discord", "is_finance": False, "needs_description": True},
        
        {"type": "zalo", "name": "Zalo", "icon": "zalo", "is_finance": False, "needs_description": False},
        {"type": "max", "name": "Max", "icon": "max", "is_finance": False, "needs_description": False},
        {"type": "facetime", "name": "FaceTime", "icon": "facetime", "is_finance": False, "needs_description": False},
        
        {"type": "telegram", "name": "Telegram", "icon": "telegram_chat", "is_finance": False,
         "needs_description": False},
    
    ],
    "transfers": [
        {"type": "revolut", "name": "Revolut", "icon": "revolut", "is_finance": True, "subtype": "revolut"},
        {"type": "wise", "name": "Wise", "icon": "wise", "is_finance": True, "subtype": "wise"},
        {"type": "paypal", "name": "PayPal", "icon": "paypal", "is_finance": False , "needs_description": False},
        {"type": "yoomoney", "name": "ЮMoney", "icon": "yoomoney", "is_finance": True, "subtype": "yoomoney"},
        
        {"type": "sber", "name": "Сбер", "icon": "sber", "is_finance": True, "subtype": "sber"},
        {"type": "vtb", "name": "ВТБ", "icon": "vtb", "is_finance": True, "subtype": "vtb"},
        {"type": "tbank", "name": "Т-Банк", "icon": "tbank", "is_finance": True, "subtype": "tbank"},
        {"type": "bidv", "name": "BIDV", "icon": "bidv", "is_finance": True, "subtype": "bidv"},
        {"type": "korona", "name": "Золотая Корона", "icon": "korona", "is_finance": True, "subtype": "korona"},
        {"type": "westernunion", "name": "Western Union", "icon": "westernunion", "is_finance": True,
         "subtype": "westernunion"},
        {"type": "unistream", "name": "Unistream", "icon": "unistream", "is_finance": True, "subtype": "unistream"},
    
    ],
    "donate": [
        {"type": "patreon", "name": "Patreon", "icon": "patreon", "is_finance": False, "needs_description": False},
        {"type": "boosty", "name": "Boosty", "icon": "boosty", "is_finance": False, "needs_description": False},
        {"type": "donationalerts", "name": "Donation Alerts", "icon": "donationalerts", "is_finance": False,
         "needs_description": False},
        {"type": "kofi", "name": "Ko-fi", "icon": "kofi", "is_finance": False, "needs_description": False},
        {"type": "buymeacoffee", "name": "Buy Me a Coffee", "icon": "buymeacoffee", "is_finance": False,
         "needs_description": False},
    
    ],
    
    "wallets": [
        {"type": "usdt", "name": "USDT", "icon": ""},
        {"type": "usdc", "name": "USDC", "icon": ""},
        
        {"type": "btc", "name": "Bitcoin", "icon": ""},
        {"type": "eth", "name": "Ethereum", "icon": ""},
        {"type": "ton", "name": "TON", "icon": ""},
        {"type": "sol", "name": "Solana", "icon": ""},
        {"type": "trx", "name": "TRON", "icon": ""},
        {"type": "bnb", "name": "BNB", "icon": ""},
        {"type": "doge", "name": "Dogecoin", "icon": ""},
        {"type": "ltc", "name": "Litecoin", "icon": ""},
        {"type": "xrp", "name": "Ripple", "icon": ""},
        {"type": "ada", "name": "Cardano", "icon": ""},
        {"type": "dot", "name": "Polkadot", "icon": ""},
        {"type": "matic", "name": "Polygon", "icon": ""},
    
    ],
    
    "stocks": [
        {"type": "binance", "name": "Binance", "icon": "binance", "is_finance": True, "subtype": "binance"},
        {"type": "bybit", "name": "Bybit", "icon": "bybit", "is_finance": True, "subtype": "bybit"},
        {"type": "okx", "name": "OKX", "icon": "okx", "is_finance": True, "subtype": "okx"},
        {"type": "kucoin", "name": "KuCoin", "icon": "kucoin", "is_finance": True, "subtype": "kucoin"},
        {"type": "gateio", "name": "Gate.io", "icon": "gateio", "is_finance": True, "subtype": "gateio"},
        {"type": "huobi", "name": "Huobi", "icon": "huobi", "is_finance": True, "subtype": "huobi"},
        {"type": "metamask", "name": "Metamask", "icon": "metamask", "is_finance": True, "subtype": "metamask"},
        {"type": "trustwallet", "name": "Trust Wallet", "icon": "trustwallet", "is_finance": True,
         "subtype": "trustwallet"},
        {"type": "coinbase", "name": "Coinbase", "icon": "coinbase", "is_finance": True, "subtype": "coinbase"},
        {"type": "kraken", "name": "Kraken", "icon": "kraken", "is_finance": True, "subtype": "kraken"},
    
    ],
    "shops": [
        {"type": "ozon", "name": "Ozon", "icon": "ozon", "is_finance": False, "needs_description": False},
        {"type": "wildberries", "name": "Wildberries", "icon": "wildberries", "is_finance": False,
         "needs_description": False},
        {"type": "avito", "name": "Avito", "icon": "avito", "is_finance": False, "needs_description": False},
        {"type": "yandex_market", "name": "Яндекс Маркет", "icon": "yandex_market", "is_finance": False,
         "needs_description": False},
        {"type": "aliexpress", "name": "AliExpress", "icon": "aliexpress", "is_finance": False,
         "needs_description": False},
        {"type": "kazanexpress", "name": "KazanExpress", "icon": "kazanexpress", "is_finance": False,
         "needs_description": False},
        {"type": "amazon", "name": "Amazon", "icon": "amazon", "is_finance": False, "needs_description": False},
        {"type": "ebay", "name": "eBay", "icon": "ebay", "is_finance": False, "needs_description": False},
        {"type": "etsy", "name": "Etsy", "icon": "etsy", "is_finance": False, "needs_description": False},
        {"type": "shopify", "name": "Shopify", "icon": "shopify", "is_finance": False, "needs_description": False},
    
    ]
    
}

# Подтипы для финансовых ссылок (крипта с табами)
FINANCE_SUBTYPES = {
    "revolut": {"name": "Revolut", "has_tabs": False,
                "fields": ["qr_code", "beneficiary", "iban", "bic", "payment_link"]},
    "wise": {"name": "Wise", "has_tabs": False, "fields": ["qr_code", "beneficiary", "iban", "bic", "payment_link"]},
    "sber": {"name": "Сбер", "has_tabs": True, "tabs": ["card", "phone"]},
    "tinkoff": {"name": "Тинькофф", "has_tabs": True, "tabs": ["card", "phone"]},
    "yoomoney": {"name": "ЮMoney", "has_tabs": False, "fields": ["wallet", "qr_code"]},
    "cryptobot": {"name": "Криптобот", "has_tabs": False, "fields": ["username", "payment_link"]},
    "bidv": {"name": "BIDV", "has_tabs": False, "fields": ["account", "beneficiary", "qr_code"]},
    "binance": {"name": "Binance", "has_tabs": True, "tabs": ["usdt", "usdc", "btc", "eth"]},
    "bybit": {"name": "Bybit", "has_tabs": True, "tabs": ["usdt", "usdc", "uid"]},
    "okx": {"name": "OKX", "has_tabs": True, "tabs": ["usdc", "btc", "eth"]},
    "metamask": {"name": "Metamask", "has_tabs": True, "tabs": ["usdt", "usdc", "eth", "arb", "tron", "btc"]},
}


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

# // D:\aRabota\TelegaBoom\030_mylinkspace\bot\link_constructor.py

import asyncpg
from contextlib import asynccontextmanager # <--- Добавь импорт

@asynccontextmanager # <--- Добавь декоратор
async def get_db_connection():
    """
    Контекстный менеджер для работы с БД.
    Гарантирует закрытие соединения после завершения блока async with.
    """
    # Чистим URL от +asyncpg, если он там есть
    clean_url = DATABASE_URL.replace('+asyncpg', '')
    
    conn = None
    try:
        # 1. Открываем соединение
        conn = await asyncpg.connect(clean_url)
        # 2. Передаем управление в блок 'async with'
        yield conn
    except Exception as e:
        print(f"❌ Ошибка БД в link_constructor: {e}")
        raise
    finally:
        # 3. ВСЕГДА закрываем соединение, что бы ни случилось
        if conn:
            await conn.close()

async def check_links_limit(conn, user_db_id: int, is_pro: bool):
    """Проверка лимита ссылок"""
    # Получаем page_id по user_db_id
    page = await conn.fetchrow("SELECT id FROM pages WHERE user_id = $1", user_db_id)
    logger.info(f"🔥 check_links_limit: page={page}")
    
    if not page:
        # Если страницы нет - создаем
        logger.warning(f"🔥 check_links_limit: страница не найдена для user_db_id={user_db_id}")
        return False, 0, 0
    
    count = await conn.fetchval("""
                                SELECT COUNT(*)
                                FROM links
                                WHERE page_id = $1
                                  AND is_active = true
                                """, page['id'])
    
    if count is None:
        count = 0
    
    limit = PRO_LINKS_LIMIT if is_pro else FREE_LINKS_LIMIT
    can_add = count < limit
    
    logger.info(f"🔥 check_links_limit: can_add={can_add}, count={count}, limit={limit}")
    
    return can_add, count, limit


# ========== ОСНОВНЫЕ ОБРАБОТЧИКИ ==========

async def add_link_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало добавления ссылки - выбор категории"""
    
    print(f"🔍 ТЕКУЩИЙ ДИАЛОГ АКТИВЕН: {context.user_data.get('_state') is not None}")
    print(f"🔍 ДАННЫЕ ПОЛЬЗОВАТЕЛЯ: {list(context.user_data.keys())}")
    # ===== ОТЛАДКА =====
    current_state = context.user_data.get('_state')
    conversation_name = context.user_data.get('_conversation')
    print(f"\n🔍 add_link_start ВЫЗВАНА")
    print(f"🔍 ДИАЛОГ: {conversation_name}")
    print(f"🔍 СОСТОЯНИЕ: {current_state}")
    if update.callback_query:
        print(f"🔍 callback_data: {update.callback_query.data}")
    print("=" * 40)
    # ===================
    
    try:
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        user = update.effective_user
        logger.info(f"🔥 add_link_start: user_id={user_id}")
        
        conn = await get_db_connection()
        try:
            # ВАЖНО: Сначала получаем или создаем пользователя
            db_user = await get_or_create_user(conn, user_id, user.username, user.first_name, user.last_name)
            logger.info(f"🔥 add_link_start: db_user_id={db_user['id']}")
            
            # 👇 ПОЛУЧАЕМ И СОХРАНЯЕМ page_id 👇
            from bot.handlers import get_user_page
            page = await get_user_page(conn, db_user['id'])
            page_id = page['id']
            context.user_data['page_id'] = page_id
            logger.info(f"🔥 add_link_start: page_id={page_id}")
            
            # Проверяем PRO статус
            user_data = await conn.fetchrow("SELECT is_pro FROM users WHERE telegram_id = $1", user_id)
            is_pro = user_data['is_pro'] if user_data else False
            logger.info(f"🔥 add_link_start: is_pro={is_pro}")
            
            # Проверяем лимиты
            can_add, count, limit = await check_links_limit(conn, db_user['id'], is_pro)
            
            if not can_add:
                await query.edit_message_text(
                    f"❌ Достигнут лимит ссылок ({count}/{limit})\n\n"
                    f"Для увеличения лимита оформи PRO-подписку: /upgrade",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("💳 Купить PRO", callback_data="upgrade")],
                        [InlineKeyboardButton("🔗 Управление ссылками", callback_data="links")],
                        [InlineKeyboardButton("◀️ Назад", callback_data="links")]
                    ])
                )
                print(f"🔚 add_link_start возвращает ConversationHandler.END (лимит исчерпан)")
                return ConversationHandler.END
            
            # Сохраняем в контекст, что мы в процессе добавления
            # context.user_data['adding_link'] = True
            # context.user_data['db_user_id'] = db_user['id']
            
            if is_pro:
                # PRO - показываем все категории
                keyboard = [
                    [
                        InlineKeyboardButton("📱 Соцсети", callback_data="cat_social"),
                        InlineKeyboardButton("Email", callback_data="cat_email")
                        
                    ],
                    [
                        InlineKeyboardButton("💬 Мессенджеры", callback_data="cat_messengers"),
                        InlineKeyboardButton("💳 Банки / Переводы", callback_data="transfers")
                        
                    ],
                    [
                        InlineKeyboardButton("💰 Донат", callback_data="cat_donate"),
                        InlineKeyboardButton("🪙 Крипта", callback_data="cat_stocks")
                        
                    ],
                    [
                        InlineKeyboardButton("🛍️ Магазины", callback_data="cat_shops"),
                        InlineKeyboardButton("🤝 Партнерки", callback_data="cat_partner")
                        
                    ],
                    
                    [
                        InlineKeyboardButton("📦 Разное", callback_data="cat_other")
                        
                    ],
                    
                    
                    [
                        InlineKeyboardButton("◀️ Отмена", callback_data="cancel")
                    ]
                ]
                
                await query.edit_message_text(
                    f"📂 **Добавление ссылки (PRO)**\n\n"
                    f"Использовано: {count} из {limit} ссылок\n"
                    f"Осталось: {limit - count}\n\n"
                    f"Выбери категорию:",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                
                # # 👇 ПРИНУДИТЕЛЬНО УСТАНАВЛИВАЕМ СОСТОЯНИЕ
                # context.user_data['_state'] = SELECT_CATEGORY
                # context.user_data['_conversation'] = 'link_constructor_conversation'
                
                print(f"🔚 add_link_start возвращает SELECT_CATEGORY={SELECT_CATEGORY} (PRO)")
                return SELECT_CATEGORY
            
            else:
                # Бесплатные - показываем популярные варианты
                context.user_data['link_type'] = 'standard'
                context.user_data['link_category'] = 'other'
                
                # Проверяем подписку
                sub_status = await check_subscription(conn, user.id)
                if sub_status and sub_status.get('active'):
                    time_left = sub_status.get('time_left_str', 'активна')
                    status_text = f"💎 **Ваш статус: PRO:** осталось {time_left}"
                else:
                    status_text = "💡 **Ваш статус:** Бесплатный"
                
                # Кнопки с популярными вариантами
                popular_buttons = [
                    [InlineKeyboardButton("📱 Instagram", callback_data="preset_instagram")],
                    [InlineKeyboardButton("📺 YouTube", callback_data="preset_youtube")],
                    [InlineKeyboardButton("✈️ Telegram", callback_data="preset_telegram")],
                    [InlineKeyboardButton("🎵 TikTok", callback_data="preset_tiktok")],
                    [InlineKeyboardButton("💬 VK", callback_data="preset_vk")],
                    [InlineKeyboardButton("📧 Email", callback_data="preset_email")],
                    [InlineKeyboardButton("🌐 Другой сайт", callback_data="preset_custom")],
                    [InlineKeyboardButton("◀️ Отмена", callback_data="cancel")]
                ]
                
                await query.edit_message_text(
                    f"{status_text}\n\n"
                    f"Использовано: {count} из {limit} ссылок\n"
                    f"Осталось: {limit - count}\n\n"
                    f"Выбери тип ссылки:",
                    reply_markup=InlineKeyboardMarkup(popular_buttons),
                    parse_mode='Markdown'
                )
                
                # 👇 ПРИНУДИТЕЛЬНО УСТАНАВЛИВАЕМ СОСТОЯНИЕ
                context.user_data['_state'] = SELECT_PRESET
                context.user_data['_conversation'] = 'link_constructor_conversation'
                
                print(f"🔚 add_link_start возвращает SELECT_PRESET={SELECT_PRESET} (FREE)")
                return SELECT_PRESET
        
        except Exception as e:
            logger.error(f"🔥 Ошибка в add_link_start (внутри conn): {e}")
            await query.edit_message_text(
                "❌ Произошла ошибка. Попробуйте позже.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ В меню", callback_data="links")
                ]])
            )
            return ConversationHandler.END
        
        finally:
            await conn.close()
    
    except Exception as e:
        logger.error(f"🔥 КРИТИЧЕСКАЯ ошибка в add_link_start: {e}")
        try:
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    "❌ Произошла критическая ошибка. Начните заново.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔄 Попробовать снова", callback_data="add_link")
                    ]])
                )
        except:
            pass
        return ConversationHandler.END




async def wallets_and_crypto_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    # Сразу переходим к списку кошельков
    target_sub = "wallets"
    
    # Сохраняем категорию для корректной работы навигации
    context.user_data['category'] = target_sub
    
    from bot.constructor import build_types_keyboard
    
    text = (
        "👛 <b>Выберите криптовалюту</b>\n\n"
        "<blockquote>Выберите монету, чтобы добавить адрес кошелька на свою страницу. "
        "Убедитесь, что копируете адрес в правильной сети.</blockquote>\n\n"
        "👇 <b>Доступные активы:</b>"
    )
    
    # Генерируем клавиатуру только для wallets
    keyboard = build_types_keyboard(target_sub)
    
    try:
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='HTML')
    except Exception as e:
        if "Message is not modified" in str(e):
            # Игнорируем ошибку, если меню уже такое же
            await query.answer()
        else:
            # Если ошибка другая - прокидываем дальше
            raise e
    
    return 1201

async def exchanges_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню Биржи"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🏦 **Биржи**\n\nЗдесь будут биржи...",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("◀️ Назад", callback_data="crypto_and_wallets_menu")
        ]]),
        parse_mode='Markdown'
    )


# # для Python

async def select_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"🔍 select_category ВЫЗВАНА. Callback: {update.callback_query.data if update.callback_query else 'No data'}")
    
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from bot.states import SELECT_LINK_TYPE, SELECT_CATEGORY, SELECT_FINANCE_SUBTYPE
    # Импортируем твои конфиги из правильного файла
    from bot.types_config import LINK_TYPES, CATEGORIES
    
    query = update.callback_query
    await query.answer()
    
    # ОЧИСТКА
    keys_to_clear = [
       'selected_currencies', 'finance_data_map', 'current_collecting_coin',
       'finance_subtype', 'link_title', 'link_url', 'link_icon', 'link_category'
    ]
    for key in keys_to_clear:
       context.user_data.pop(key, None)
    
    # Получаем категорию из callback (например, cat_social -> social)
    category = query.data.replace("cat_", "")
    context.user_data['link_category'] = category
    
    # 1. Если это Банки — уходим в подтипы (там своя логика выбора страны/банка)
    if category == "transfers":
       context.user_data['goto_banks'] = True
       return await select_finance_subtype(update, context)
    
    # 2. Если это Крипта — показываем меню "Кошельки / Биржи"
    if category == "crypto" or category == "wallets_and_crypto_menu":
       return await wallets_and_crypto_menu(update, context)
    
    # 3. Для всех остальных (social, messengers, wallets, stocks)
    # Собираем кнопки из LINK_TYPES, где совпадает категория
    buttons = []
    for link_key, config in LINK_TYPES.items():
        if config.get('category') == category:
            buttons.append(InlineKeyboardButton(config['name'], callback_data=f"type_{link_key}"))
    
    if not buttons:
        await query.message.reply_text(f"❌ В разделе '{category}' пока нет платформ.")
        return SELECT_CATEGORY

    # Группируем по 2 в ряд
    keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    
    # Навигация "Назад"
    if category in ["wallets", "stocks"]:
        back_call = "cat_wallets_and_crypto_menu"
    else:
        back_call = "add_link"
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data=back_call)])
    
    # Берем красивое название и иконку из CATEGORIES
    cat_info = CATEGORIES.get(category, {})
    cat_name = cat_info.get('name', "Выбор")
    cat_icon = cat_info.get('icon', "📂")
    
    message_text = f"{cat_icon} **{cat_name}**\n\nВыберите платформу для добавления:"
    
    await query.edit_message_text(
       message_text,
       reply_markup=InlineKeyboardMarkup(keyboard),
       parse_mode='HTML'
    )
    
    # 🎯 Важно: Возвращаем состояние 1201 (SELECT_LINK_TYPE)
    return SELECT_LINK_TYPE

# ============================================
# ФУНКЦИИ ПАРСИНГА ДЛЯ РАЗНЫХ СОЦСЕТЕЙ
# ============================================

def parse_youtube_input(text: str) -> dict:
    """Парсит ввод пользователя для YouTube"""
    text = text.strip()
    
    # Ссылка на канал через @
    if 'youtube.com/@' in text:
        username = text.split('youtube.com/@')[-1].split('/')[0].split('?')[0]
        return {
            'type': 'handle',
            'value': username,
            'url': f"https://youtube.com/@{username}",
            'display': f"@{username}"
        }
    
    # Channel ID (UC...)
    if 'youtube.com/channel/' in text:
        channel_id = text.split('youtube.com/channel/')[-1].split('/')[0].split('?')[0]
        return {
            'type': 'channel_id',
            'value': channel_id,
            'url': f"https://youtube.com/channel/{channel_id}",
            'display': f"Channel ID: {channel_id[:8]}..."
        }
    
    # Короткая ссылка youtu.be
    if 'youtu.be/' in text:
        video_id = text.split('youtu.be/')[-1].split('/')[0].split('?')[0]
        return {
            'type': 'video',
            'value': video_id,
            'url': f"https://youtu.be/{video_id}",
            'display': f"Video: {video_id}"
        }
    
    # Просто @username
    if text.startswith('@'):
        username = text[1:]
        return {
            'type': 'handle',
            'value': username,
            'url': f"https://youtube.com/@{username}",
            'display': f"@{username}"
        }
    
    # Просто username (без @)
    if '/' not in text and ' ' not in text and '.' not in text and not text.startswith(('http://', 'https://')):
        return {
            'type': 'handle',
            'value': text,
            'url': f"https://youtube.com/@{text}",
            'display': f"@{text}"
        }
    
    # Полная ссылка
    if text.startswith(('http://', 'https://')):
        return {
            'type': 'url',
            'value': text,
            'url': text,
            'display': text[:30] + "..." if len(text) > 30 else text
        }
    
    # По умолчанию - добавляем https://
    return {
        'type': 'url',
        'value': text,
        'url': f"https://{text}",
        'display': text
    }


def parse_telegram_input(text: str) -> dict:
    """Парсит ввод пользователя для Telegram"""
    text = text.strip()
    
    # Ссылка t.me
    if 't.me/' in text:
        username = text.split('t.me/')[-1].split('/')[0].split('?')[0]
        return {
            'type': 'username',
            'value': username,
            'url': f"https://t.me/{username}",
            'display': f"@{username}"
        }
    
    # telegram.org
    if 'telegram.org/' in text:
        username = text.split('telegram.org/')[-1].split('/')[0].split('?')[0]
        return {
            'type': 'username',
            'value': username,
            'url': f"https://t.me/{username}",
            'display': f"@{username}"
        }
    
    # @username
    if text.startswith('@'):
        username = text[1:]
        return {
            'type': 'username',
            'value': username,
            'url': f"https://t.me/{username}",
            'display': f"@{username}"
        }
    
    # Просто username
    if '/' not in text and ' ' not in text and '.' not in text and not text.startswith(('http://', 'https://')):
        return {
            'type': 'username',
            'value': text,
            'url': f"https://t.me/{text}",
            'display': f"@{text}"
        }
    
    # Полная ссылка
    if text.startswith(('http://', 'https://')):
        return {
            'type': 'url',
            'value': text,
            'url': text,
            'display': text[:30] + "..." if len(text) > 30 else text
        }
    
    return {
        'type': 'url',
        'value': text,
        'url': f"https://{text}",
        'display': text
    }


def parse_instagram_input(text: str) -> dict:
    """Парсит ввод пользователя для Instagram"""
    text = text.strip()
    
    # instagram.com/username
    if 'instagram.com/' in text:
        username = text.split('instagram.com/')[-1].split('/')[0].split('?')[0]
        return {
            'type': 'username',
            'value': username,
            'url': f"https://instagram.com/{username}",
            'display': f"@{username}"
        }
    
    # @username
    if text.startswith('@'):
        username = text[1:]
        return {
            'type': 'username',
            'value': username,
            'url': f"https://instagram.com/{username}",
            'display': f"@{username}"
        }
    
    # Просто username
    if '/' not in text and ' ' not in text and '.' not in text and not text.startswith(('http://', 'https://')):
        return {
            'type': 'username',
            'value': text,
            'url': f"https://instagram.com/{text}",
            'display': f"@{text}"
        }
    
    # Полная ссылка
    if text.startswith(('http://', 'https://')):
        return {
            'type': 'url',
            'value': text,
            'url': text,
            'display': text[:30] + "..." if len(text) > 30 else text
        }
    
    return {
        'type': 'url',
        'value': text,
        'url': f"https://{text}",
        'display': text
    }


def parse_tiktok_input(text: str) -> dict:
    """Парсит ввод пользователя для TikTok"""
    text = text.strip()
    
    # tiktok.com/@username
    if 'tiktok.com/@' in text:
        username = text.split('tiktok.com/@')[-1].split('/')[0].split('?')[0]
        return {
            'type': 'username',
            'value': username,
            'url': f"https://tiktok.com/@{username}",
            'display': f"@{username}"
        }
    
    # @username
    if text.startswith('@'):
        username = text[1:]
        return {
            'type': 'username',
            'value': username,
            'url': f"https://tiktok.com/@{username}",
            'display': f"@{username}"
        }
    
    # Просто username
    if '/' not in text and ' ' not in text and '.' not in text and not text.startswith(('http://', 'https://')):
        return {
            'type': 'username',
            'value': text,
            'url': f"https://tiktok.com/@{text}",
            'display': f"@{text}"
        }
    
    # Полная ссылка
    if text.startswith(('http://', 'https://')):
        return {
            'type': 'url',
            'value': text,
            'url': text,
            'display': text[:30] + "..." if len(text) > 30 else text
        }
    
    return {
        'type': 'url',
        'value': text,
        'url': f"https://{text}",
        'display': text
    }


def parse_vk_input(text: str) -> dict:
    """Парсит ввод пользователя для VK"""
    text = text.strip()
    
    # vk.com/durov
    if 'vk.com/' in text:
        username = text.split('vk.com/')[-1].split('/')[0].split('?')[0]
        return {
            'type': 'page',
            'value': username,
            'url': f"https://vk.com/{username}",
            'display': username
        }
    
    # vk.ru/durov
    if 'vk.ru/' in text:
        username = text.split('vk.ru/')[-1].split('/')[0].split('?')[0]
        return {
            'type': 'page',
            'value': username,
            'url': f"https://vk.com/{username}",
            'display': username
        }
    
    # id123456
    if text.startswith('id') and text[2:].isdigit():
        user_id = text[2:]
        return {
            'type': 'id',
            'value': user_id,
            'url': f"https://vk.com/id{user_id}",
            'display': f"id{user_id}"
        }
    
    # public123456
    if text.startswith('public') and text[6:].isdigit():
        public_id = text[6:]
        return {
            'type': 'public',
            'value': public_id,
            'url': f"https://vk.com/public{public_id}",
            'display': f"public{public_id}"
        }
    
    # club123456
    if text.startswith('club') and text[4:].isdigit():
        club_id = text[4:]
        return {
            'type': 'club',
            'value': club_id,
            'url': f"https://vk.com/club{club_id}",
            'display': f"club{club_id}"
        }
    
    # Просто username
    if '/' not in text and ' ' not in text and not text.startswith(('http://', 'https://')):
        return {
            'type': 'page',
            'value': text,
            'url': f"https://vk.com/{text}",
            'display': text
        }
    
    # Полная ссылка
    if text.startswith(('http://', 'https://')):
        return {
            'type': 'url',
            'value': text,
            'url': text,
            'display': text[:30] + "..." if len(text) > 30 else text
        }
    
    return {
        'type': 'url',
        'value': text,
        'url': f"https://{text}",
        'display': text
    }


# Словарь парсеров по типам соцсетей
SOCIAL_PARSERS = {
    'youtube': parse_youtube_input,
    'telegram': parse_telegram_input,
    'instagram': parse_instagram_input,
    'tiktok': parse_tiktok_input,
    'vk': parse_vk_input,
    # Для остальных используем базовый парсер
    'twitter': lambda t: {'type': 'url', 'value': t,
                          'url': f"https://twitter.com/{t.replace('@', '')}" if not t.startswith('http') else t,
                          'display': t},
    'facebook': lambda t: {'type': 'url', 'value': t,
                           'url': f"https://facebook.com/{t.replace('@', '')}" if not t.startswith('http') else t,
                           'display': t},
    'ok': lambda t: {'type': 'url', 'value': t, 'url': f"https://ok.ru/{t}" if not t.startswith('http') else t,
                     'display': t},
    'twitch': lambda t: {'type': 'url', 'value': t,
                         'url': f"https://twitch.tv/{t.replace('@', '')}" if not t.startswith('http') else t,
                         'display': t},
    'rutube': lambda t: {'type': 'url', 'value': t,
                         'url': t if t.startswith('http') else f"https://rutube.ru/channel/{t}", 'display': t},
    'dzen': lambda t: {'type': 'url', 'value': t, 'url': t if t.startswith('http') else f"https://dzen.ru/{t}",
                       'display': t},
}


# # для Python

# # для Python

# # для Python

# # для Python

# # для Python

# # для Python

# # для Python

async def select_link_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Название файла: bot/link_constructor.py
    # # Пишем несколько строк кода перед вставкой: логируем входящий callback
    print(f"🔥🔥🔥 select_link_type ВЫЗВАНА: {update.callback_query.data}")
    
    # ЛОКАЛЬНЫЕ ИМПОРТЫ ДЛЯ ПРЕДОТВРАЩЕНИЯ CIRCULAR IMPORT
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from bot.states import (
        SELECT_LINK_TYPE, ADD_CUSTOM_CURRENCY_NAME,
        ADD_LINK_URL, SELECT_FINANCE_SUBTYPE, SELECT_CATEGORY
    )
    from bot.utils import get_db_connection, get_or_create_user
    
    # Если эти функции лежат в других файлах, импортируем их ЗДЕСЬ
    # Если select_finance_subtype в этом же файле — импорт не нужен
    
    query = update.callback_query
    await query.answer()
    
    link_type = query.data.replace("type_", "")
    category = context.user_data.get('link_category')
    
    # Получаем пользователя через твой utils.py
    user_db_id = context.user_data.get('db_user_id')
    if not user_db_id:
        user_id = update.effective_user.id
        conn = await get_db_connection()
        try:
            db_user = await get_or_create_user(conn, user_id, None, None, None)
            context.user_data['db_user_id'] = db_user['id']
            user_db_id = db_user['id']
        finally:
            await conn.close()
    
    PRO_WIDGETS = [
        "binance", "bybit", "okx", "kucoin", "metamask", "gateio",
        "huobi", "trustwallet", "coinbase", "kraken"
    ]
    
    # ПРОВЕРКА НА ДУБЛИКАТЫ
    if link_type in PRO_WIDGETS:
        conn = await get_db_connection()
        try:
            existing = await conn.fetchrow("""
                                           SELECT l.id
                                           FROM links l
                                                    JOIN pages p ON l.page_id = p.id
                                           WHERE p.user_id = $1
                                             AND l.link_type = $2
                                             AND l.is_active = true
                                           """, user_db_id, link_type)
            
            if existing:
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🗑 Управление", callback_data="links")],
                    [InlineKeyboardButton("◀️ Назад", callback_data="add_link")]
                ])
                await query.edit_message_text(f"⚠️ Виджет {link_type.upper()} уже есть!", reply_markup=keyboard)
                return SELECT_LINK_TYPE
        finally:
            await conn.close()
    
    # CATEGORY_LINK_TYPES у тебя определен глобально в этом файле
    link_types = CATEGORY_LINK_TYPES.get(category, [])
    link_info = next((lt for lt in link_types if lt['type'] == link_type), None)
    
    if not link_info:
        # Если это акция/сток
        if category == "stocks":
            link_info = {"type": link_type, "name": link_type.upper(), "is_finance": True}
        else:
            return SELECT_LINK_TYPE
    
    context.user_data.update({
        'link_info': link_info,
        'category': category,
        'link_type': link_type,
        'link_icon': link_info.get('icon', link_type)
    })
    
    # --- ЛОГИКА ПЕРЕХОДОВ ---
    if link_type == "custom_wallet":
        await query.edit_message_text("📝 Введите название монеты:")
        return ADD_CUSTOM_CURRENCY_NAME
    
    # Биржи или Банки (transfers)
    if link_type in PRO_WIDGETS or category == "stocks" or category == "transfers":
        context.user_data.update({'is_exchange': True, 'finance_subtype': link_type})
        # Вызываем функцию (она должна быть определена в этом файле или импортирована локально)
        return await select_finance_subtype(update, context)
    
    # Кошельки (USDT, BTC...)
    if category == "wallets":
        context.user_data.update({'link_title': link_info['name'], 'is_exchange': True, 'link_type': 'crypto'})
        # Вызываем твою функцию ask_for_wallet_address из этого же файла
        return await ask_for_wallet_address(update, context, link_info)
    
    # Соцсети и прочее
    context.user_data['is_exchange'] = False
    # Если ask_for_title в другом файле, импортируй его здесь локально
    # from bot.link_constructor_other import ask_for_title
    return await ask_for_title(update, context, link_info)


async def ask_for_wallet_address(update: Update, context: ContextTypes.DEFAULT_TYPE, link_info):
    # Название файла: bot/link_constructor.py
    # # Пишем несколько строк кода перед вставкой: запрос стейта
    from bot.states import ADD_LINK_URL
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    query = update.callback_query
    
    text = (
        f"🔗 Добавление <b>{link_info['name']}</b> кошелька\n\n"
        f"Введите адрес вашего кошелька в чат (сообщением).\n\n"
        f"⚠️ <i>Тщательно проверьте адрес перед отправкой!</i>"
    )
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("◀️ Назад к списку", callback_data="cat_wallets")
        ]]),
        parse_mode='HTML'
    )
    # # Возврат этого стейта заставляет бота ждать текст от юзера
    return ADD_LINK_URL


# bot/link_constructor.py

async def add_custom_currency_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ловим название кастомной монеты и задаем путь к локальной иконке"""
    custom_name = update.message.text.strip()
    
    if len(custom_name) > 30:
        await update.message.reply_text("❌ Название слишком длинное. Введите короче:")
        return ADD_CUSTOM_CURRENCY_NAME
    
    # 1. Запоминаем название как заголовок ссылки
    context.user_data['link_title'] = custom_name
    
    # 2. УСТАНАВЛИВАЕМ ИМЯ ФАЙЛА ИКОНКИ (из твоей папки /static/icons)
    # Убедись, что файл с таким именем реально лежит в web/static/icons/
    context.user_data['link_icon'] = "generic_crypto.png"
    
    # 3. Обновляем объект link_info
    link_info = context.user_data.get('link_info', {})
    link_info['name'] = custom_name
    context.user_data['link_info'] = link_info
    
    # 4. Текст запроса адреса
    text = (
        f"🔗 Добавление <b>{custom_name}</b> кошелька\n\n"
        f"Введите адрес вашего кошелька в чат (сообщением).\n\n"
        f"⚠️ <i>Тщательно проверьте адрес перед отправкой!</i>"
    )
    
    await update.message.reply_text(
        text=text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("◀️ Назад", callback_data="cat_wallets")
        ]]),
        parse_mode='HTML'
    )
    return ADD_LINK_URL


# bot/link_constructor.py


WALLETS_LIST = CATEGORY_LINK_TYPES["wallets"]


async def select_finance_subtype(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    ФУНКЦИЯ: select_finance_subtype
    belong_to: bot/link_constructor.py
    Логика: Единый универсальный конструктор для всех бирж с лимитом 3 и фиксом отображения USDT.
    """
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from bot.states import SELECT_FINANCE_SUBTYPE
    
    query = update.callback_query
    data = query.data
    currency_type = None
    
    print(f"🔥🔥🔥 select_finance_subtype ВЫЗВАНА")
    
    # 1. РАЗБОР CALLBACK_DATA
    if data and data.startswith("fin_sub_"):
        parts = data.split('_')
        subtype = parts[2]  # Это название биржи (например: bybit, binance)
        if len(parts) > 3:
            currency_type = "_".join(parts[3:])
    else:
        subtype = context.user_data.get('finance_subtype')
    
    # 2. СОХРАНЯЕМ ДАННЫЕ ПРЕСЕТА И КАТЕГОРИЮ
    context.user_data['finance_subtype'] = subtype
    
    # Словарь для правильного отображения названий в базе и боте
    pretty_names = {
        "okx": "OKX",
        "binance": "Binance",
        "bybit": "Bybit",
        "kucoin": "KuCoin",
        "gateio": "Gate.io",
        "huobi": "HTX (Huobi)",
        "metamask": "MetaMask",
        "trustwallet": "Trust Wallet"
    }
    
    # Сохраняем нормальное имя (если нет в списке - делаем капсом)
    context.user_data['selected_preset_name'] = pretty_names.get(subtype.lower(), subtype.upper())
    
    # ЖЕСТКО ЗАКРЕПЛЯЕМ КАТЕГОРИЮ, чтобы не было NULL в базе при сохранении
    context.user_data['link_category'] = 'stocks'
    
    # Иконки пресета
    preset_icons = {"bybit": "bybit", "binance": "binance", "okx": "okx", "gateio": "gateio"}
    context.user_data['selected_preset_icon'] = preset_icons.get(subtype.lower(), "💰")
    
    # 3. ПОДГОТОВКА СПИСКОВ
    from bot.link_constructor import CATEGORY_LINK_TYPES
    wallets_list = CATEGORY_LINK_TYPES.get("wallets", [])
    available_currencies = [{"type": "uid", "name": "UID", "icon": "🆔"}] + wallets_list
    
    if 'selected_currencies' not in context.user_data:
        context.user_data['selected_currencies'] = []
    
    selected = context.user_data['selected_currencies']
    
    # 4. ЛОГИКА ОБРАБОТКИ НАЖАТИЙ
    if currency_type:
        if currency_type == "done":
            if not selected:
                await query.answer("⚠️ Выберите хотя бы один актив!", show_alert=True)
                return SELECT_FINANCE_SUBTYPE
            await query.answer()
            return await ask_for_multi_finance_details(update, context)
        
        if currency_type in selected:
            selected.remove(currency_type)
            await query.answer()
        else:
            if len(selected) >= 3:
                await query.answer("🛑 Лимит: не более 3-х активов!", show_alert=True)
                return SELECT_FINANCE_SUBTYPE
            selected.append(currency_type)
            await query.answer()
    else:
        await query.answer()
    
    # 5. ФОРМИРОВАНИЕ ТЕКСТА
    selected_names = []
    for s_type in selected:
        coin_obj = next((c for c in available_currencies if c['type'] == s_type), None)
        name = coin_obj['name'] if coin_obj else s_type.replace('_', ' ').upper()
        selected_names.append(f"**{name}**")
    
    display_title = context.user_data['selected_preset_name']
    text = (
            f"🏛 **Настройка виджета {display_title}**\n\n"
            "Выберите **до 3-х активов**. На странице они будут вкладками.\n\n"
            f"✅ **Выбрано ({len(selected)}/3):** " +
            (", ".join(selected_names) if selected_names else "_ничего не выбрано_")
    )
    
    # 6. СБОРКА КЛАВИАТУРЫ
    keyboard = []
    row = []
    for i, coin in enumerate(available_currencies):
        is_selected = " ✅" if coin['type'] in selected else ""
        button_text = f"{coin.get('icon', '')} {coin['name']}{is_selected}".strip()
        row.append(InlineKeyboardButton(button_text, callback_data=f"fin_sub_{subtype}_{coin['type']}"))
        
        if len(row) == 2 or i == len(available_currencies) - 1:
            keyboard.append(row)
            row = []
    
    keyboard.append([InlineKeyboardButton("🚀 Подтвердить и ввести данные", callback_data=f"fin_sub_{subtype}_done")])
    keyboard.append([InlineKeyboardButton("◀️ Назад в список бирж", callback_data="cat_stocks")])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    return SELECT_FINANCE_SUBTYPE


async def finalize_finance_modal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Создает запись в БД.
    Проверяет, нет ли уже такой биржи на странице пользователя.
    """
    import json
    from bot.utils import get_db_connection
    from telegram.ext import ConversationHandler
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    query = update.callback_query
    user_db_id = context.user_data.get('db_user_id')
    subtype = context.user_data.get('finance_subtype', 'crypto').lower()
    data_map = context.user_data.get('finance_data_map', {})
    
    # Извлекаем категорию из user_data
    category = context.user_data.get('link_category', 'stocks')
    
    # 1. Формируем табы для JSON
    tabs = []
    for coin_type, data in data_map.items():
        if isinstance(data, dict):
            address = data.get('address', '')
            net = data.get('net', 'Mainnet')
        else:
            address = data
            net = 'Mainnet'
        
        if coin_type.lower() == 'uid':
            display_name = "ID Аккаунта"
            full_net = subtype.capitalize()
        else:
            display_name = coin_type.upper()
            full_net = f"{net}"
        
        tabs.append({
            "name": display_name,
            "address": address,
            "network": net,
            "network_full": full_net,
            "qr_code": None
        })
    
    pay_details_json = json.dumps({"tabs": tabs}, ensure_ascii=False)
    title = context.user_data.get('selected_preset_name', subtype.capitalize())
    icon_name = subtype
    
    conn = await get_db_connection()
    try:
        # Получаем ID страницы
        page = await conn.fetchrow("SELECT id FROM pages WHERE user_id = $1", user_db_id)
        if not page:
            raise Exception("Страница пользователя не найдена")
        
        # ПРОВЕРКА НА ДУБЛИКАТ
        existing_link = await conn.fetchrow(
            "SELECT id FROM public.links WHERE page_id = $1 AND link_type = $2 AND is_active = true",
            page['id'], subtype
        )
        
        if existing_link:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("⚙️ Редактировать мои ссылки", callback_data="links")],
                [InlineKeyboardButton("◀️ Назад", callback_data="add_link")]
            ])
            text = (
                f"⚠️ <b>У вас уже есть виджет {title}!</b>\n\n"
                f"На одной странице нельзя разместить две одинаковые биржи.\n"
                f"Вы можете отредактировать данные существующего виджета в разделе управления ссылками."
            )
            if query:
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='HTML')
            else:
                await update.effective_message.reply_text(text, reply_markup=keyboard, parse_mode='HTML')
            return ConversationHandler.END
        
        # РАСЧЕТ SORT_ORDER (чтобы в базе не было null как в твоем логе)
        order_row = await conn.fetchrow(
            "SELECT COALESCE(MAX(sort_order), 0) + 1 as next_order FROM public.links WHERE page_id = $1", page['id'])
        next_order = order_row['next_order']
        
        # ВСТАВЛЯЕМ ДАННЫЕ (Параметры до $8: page_id, title, url, icon, link_type, pay_details, category, sort_order)
        await conn.execute("""
                           INSERT INTO public.links
                           (page_id, title, url, icon, link_type, pay_details, category, sort_order, is_active,
                            created_at)
                           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, true, NOW())
                           """,
                           page['id'], title, "#modal", icon_name, subtype, pay_details_json, category, next_order)
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Управление ссылками", callback_data="links")],
            [InlineKeyboardButton("➕ Добавить ещё", callback_data="add_link")],
            [InlineKeyboardButton("🏠 В меню", callback_data="start")]
        ])
        
        success_text = (
            f"🚀 <b>Виджет {title} успешно создан!</b>\n\n"
            f"Теперь на вашей странице появилась кнопка с модальным окном.\n\n"
            f"👇 <b>Что делаем дальше?</b>"
        )
        
        if query:
            await query.edit_message_text(success_text, reply_markup=keyboard, parse_mode='HTML')
        else:
            await update.effective_message.reply_text(success_text, reply_markup=keyboard, parse_mode='HTML')
    
    except Exception as e:
        print(f"Ошибка в finalize_finance_modal: {e}")
        error_msg = "❌ Ошибка при сохранении данных."
        if query:
            await query.edit_message_text(error_msg)
        else:
            await update.effective_message.reply_text(error_msg)
    finally:
        await conn.close()
    
    # Очистка контекста
    context.user_data.pop('finance_data_map', None)
    context.user_data.pop('selected_currencies', None)
    context.user_data.pop('current_collecting_coin', None)
    context.user_data.pop('link_category', None)
    
    return ConversationHandler.END


async def finalize_finance_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    ФУНКЦИЯ: finalize_finance_link
    belong_to: bot/link_constructor.py
    Логика: Берёт название из пресета или ввода, сохраняет данные в JSON и закрывает диалог.
    """
    import json
    from telegram.ext import ConversationHandler
    
    # 1. Определяем название (Title)
    preset_name = context.user_data.get('selected_preset_name')
    user_input = (update.message.text or "").strip()
    
    title = preset_name if preset_name else user_input
    
    # Извлекаем категорию
    category = context.user_data.get('link_category', 'wallets')
    
    # 2. Собираем данные
    finance_data = context.user_data.get('finance_data_map', {})
    if not finance_data:
        await update.message.reply_text("❌ Ошибка: данные не найдены. Попробуйте создать ссылку заново.")
        return ConversationHandler.END
    
    # Формируем JSON-строку
    final_json = json.dumps(finance_data, ensure_ascii=False)
    
    # 3. СОХРАНЕНИЕ В БАЗУ
    user_id = update.effective_user.id
    page_id = context.user_data.get('page_id')
    
    try:
        from core.database import db
        
        # Добавляем category в вызов метода
        await db.add_link(
            user_id=user_id,
            page_id=page_id,
            title=title,
            url=final_json,
            link_type='crypto_modal',
            category=category
        )
        
        # 4. Финальный ответ
        await update.message.reply_text(
            f"✅ Группа «{title}» успешно сохранена!\n"
            f"Данные ({len(finance_data)} шт.) привязаны к кнопке."
        )
    except Exception as e:
        print(f"Ошибка в finalize_finance_link: {e}")
        await update.message.reply_text("⚠ Произошла ошибка при сохранении в базу данных.")
    
    # 5. Полная очистка кеша
    context.user_data.clear()
    return ConversationHandler.END


async def handle_multi_net_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия на кнопки сетей (TRC-20, ERC-20, Custom и т.д.)"""
    query = update.callback_query
    if not query:
        return ADD_MULTI_FINANCE_DATA
    
    data = query.data
    await query.answer()
    
    # Логика обработки нажатий
    if data == "multi_net_back":
        # Сброс выбранной сети, чтобы вернуться к кнопкам выбора
        context.user_data['temp_net'] = None
    elif data == "multi_net_custom":
        # Пользователь выбрал ввод своей сети/пропустить
        context.user_data['temp_net'] = "Custom/Other"
    else:
        # Извлекаем название сети из callback_data (напр. multi_net_TRC-20 -> TRC-20)
        network = data.replace("multi_net_", "")
        context.user_data['temp_net'] = network
    
    # Отладочный лог в консоль (поможет при дебаге)
    current_coin = context.user_data.get('current_collecting_coin', 'unknown')
    print(f"[DEBUG] Сеть для {current_coin} выбрана: {context.user_data['temp_net']}")
    
    # Возвращаемся в основную функцию.
    # Теперь ask_for_multi_finance_details увидит, что temp_net заполнен,
    # уберет кнопки сетей и попросит прислать адрес ТЕКСТОМ.
    return await ask_for_multi_finance_details(update, context)


async def process_multi_network_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатия на кнопку сети в мульти-виджете"""
    query = update.callback_query
    await query.answer()
    
    # Извлекаем сеть из callback_data (например: multi_net_TRC-20)
    network = query.data.replace("multi_net_", "")
    
    current_coin = context.user_data.get('current_collecting_coin')
    
    # Получаем инфо о монете для красивого текста
    wallets_list = CATEGORY_LINK_TYPES.get("wallets", [])
    coin_info = next((c for c in wallets_list if c['type'] == current_coin), {"name": "актива"})
    
    if network == "custom":
        # Запоминаем, что юзер будет вводить СВОЮ сеть
        context.user_data['waiting_for_custom_network'] = True
        await query.edit_message_text(
            f"📝 **{coin_info['name']}**\n\nВведите название вашей сети (например, *Arbitrum* или *Polygon*):",
            parse_mode='Markdown'
        )
    else:
        # Запоминаем выбранную стандартную сеть
        context.user_data['current_selected_network'] = network
        context.user_data['waiting_for_custom_network'] = False
        await query.edit_message_text(
            f"✅ Выбрана сеть: **{network}**\n\nТеперь введите адрес вашего кошелька для {coin_info['name']}:",
            parse_mode='Markdown'
        )
    
    return ADD_MULTI_FINANCE_DATA


async def process_multi_finance_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    ФУНКЦИЯ: process_multi_finance_data
    belong_to: bot/link_constructor.py
    Логика: Принимает адрес, сохраняет и ПИНАЕТ бота проверять очередь монет.
    """
    user_text = update.message.text.strip()
    current_coin = context.user_data.get('current_collecting_coin')
    chosen_net = context.user_data.get('temp_net')
    
    # Защита от дурака
    if current_coin != 'uid' and not chosen_net:
        await update.message.reply_text("⚠️ Сначала выберите сеть кнопкой!")
        return ADD_MULTI_FINANCE_DATA
    
    if 'finance_data_map' not in context.user_data:
        context.user_data['finance_data_map'] = {}
    
    # Формируем строку (UID или Сеть + Адрес)
    val = user_text if current_coin == 'uid' else f"[{chosen_net}] {user_text}"
    context.user_data['finance_data_map'][current_coin] = val
    
    # Сброс временной сети
    context.user_data['temp_net'] = None
    
    # Идем проверять, есть ли в очереди еще монеты
    return await ask_for_multi_finance_details(update, context)


async def ask_for_title(update: Update, context: ContextTypes.DEFAULT_TYPE, link_info: dict):
    """Запрос названия ссылки или автоматический переход дальше"""
    query = update.callback_query
    if query:
        await query.answer()
    
    # Если у ссылки предопределенное название (custom_name: False)
    if not link_info.get('custom_name', False):
        # Используем стандартное название из link_info
        context.user_data['link_title'] = link_info.get('name', 'Без названия')
        
        # Переходим к следующему шагу в зависимости от типа
        if link_info.get('is_finance'):
            # Это как раз наш случай с биржами/банками
            return await ask_for_finance_details(update, context)
        elif link_info.get('type') == 'text':
            return await ask_for_text_content(update, context)
        else:
            return await ask_for_url(update, context)
    
    # Если нужно спросить название у пользователя
    text = (
        f"📝 **Введите название для ссылки**\n\n"
        f"Это текст, который будет отображаться на кнопке.\n"
        f"Например: `Мой Binance (USDT)` или `Основной кошелек`"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Назад", callback_data=f"cat_{context.user_data['link_category']}")]
        ]),
        parse_mode='Markdown'
    )
    
    return ADD_LINK_TITLE


async def select_preset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора популярного варианта для бесплатных"""
    query = update.callback_query
    await query.answer()
    
    preset = query.data.replace("preset_", "")
    
    # Словарь с соответствием preset -> категория и тип
    presets = {
        "instagram": {"category": "social", "type": "instagram", "title": "Instagram", "icon": "instagram"},
        "youtube": {"category": "social", "type": "youtube", "title": "YouTube", "icon": "youtube"},
        "telegram": {"category": "social", "type": "telegram", "title": "Telegram", "icon": "telegram"},
        "tiktok": {"category": "social", "type": "tiktok", "title": "TikTok", "icon": "tiktok"},
        "vk": {"category": "social", "type": "vk", "title": "VK", "icon": "vk"},
        "email": {"category": "contact", "type": "email", "title": "Email", "icon": "email"},
        "custom": {"category": "other", "type": "standard", "title": "Другой сайт", "icon": "link"}
    }
    
    selected = presets.get(preset, presets["custom"])
    
    # Сохраняем в контекст
    context.user_data['link_category'] = selected["category"]
    context.user_data['link_type'] = selected["type"]
    context.user_data['link_title'] = selected["title"]
    context.user_data['link_icon'] = selected["icon"]
    
    # Запрашиваем URL
    await query.edit_message_text(
        f"🔗 **Введи ссылку для {selected['title']}**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Отмена", callback_data="cancel")]
        ]),
        parse_mode='Markdown'
    )
    return ADD_LINK_URL


async def add_link_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import ConversationHandler
    from bot.states import SELECT_CRYPTO_NETWORK, ADD_LINK_URL
    
    url_val = update.message.text.strip() if update.message else ""
    if not url_val:
        await update.message.reply_text("❌ Введите корректную ссылку!")
        return ADD_LINK_URL
    
    context.user_data['link_url'] = url_val
    category = context.user_data.get('link_category')
    title = context.user_data.get('link_title', 'Без названия')
    user_id = update.effective_user.id
    
    # Если это крипта — отправляем выбирать сеть
    if category == "wallets":
        # Логика выбора сетей для криптовалют
        t_upper = title.upper()
        
        if "USDT" in t_upper:
            # Самые популярные сети для тезера
            networks = [
                ("TRC-20 (Tron)", "trc20"),
                ("BEP-20 (BSC)", "bep20"),
                ("ERC-20 (Ethereum)", "erc20"),
                ("Polygon", "polygon"),
                ("Solana", "sol"),
                ("Arbitrum One", "arbitrum"),
                ("Optimism", "optimism")
            ]
        elif "USDC" in t_upper:
            # Основные сети для USDC
            networks = [
                ("ERC-20 (Ethereum)", "erc20"),
                ("BEP-20 (BSC)", "bep20"),
                ("Polygon", "polygon"),
                ("Solana", "sol"),
                ("Base", "base"),
                ("Arbitrum One", "arbitrum")
            ]
        elif "TON" in t_upper:
            networks = [("TON Network", "ton")]
        elif "BTC" in t_upper or "БИТКОИН" in t_upper:
            networks = [
                ("Bitcoin (Legacy/SegWit)", "btc"),
                ("BEP-20 (Wrapped)", "bep20"),
                ("Lightning Network", "lightning")
            ]
        elif "ETH" in t_upper or "ETHEREUM" in t_upper:
            networks = [
                ("Mainnet (ERC-20)", "erc20"),
                ("Arbitrum One", "arbitrum"),
                ("Optimism", "optimism"),
                ("zkSync Era", "zksync"),
                ("BEP-20", "bep20")
            ]
        elif "SOL" in t_upper or "SOLANA" in t_upper:
            networks = [("Solana Network", "sol")]
        elif "XRP" in t_upper or "RIPPLE" in t_upper:
            networks = [("XRP Ledger", "xrp"), ("BEP-20", "bep20")]
        elif "ADA" in t_upper or "CARDANO" in t_upper:
            networks = [("Cardano Network", "cardano"), ("BEP-20", "bep20")]
        elif "DOGE" in t_upper:
            networks = [("Dogecoin", "doge"), ("BEP-20", "bep20")]
        else:
            # Универсальный набор для всего остального
            networks = [
                ("Mainnet", "mainnet"),
                ("BEP-20 (BSC)", "bep20"),
                ("ERC-20 (ETH)", "erc20"),
                ("TRC-20 (TRON)", "trc20"),
                ("Polygon", "polygon")
            ]
        
        keyboard = [[InlineKeyboardButton(n, callback_data=f"net_{c}")] for n, c in networks]
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="add_link")])
        
        await update.message.reply_text(
            f"🌐 **Адрес принят!**\nВыберите сеть для `{title}`:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return SELECT_CRYPTO_NETWORK
    
    # Если это соцсеть или другое — сохраняем сразу
    icon = context.user_data.get('link_icon', 'link')
    
    # ✅ ПОЛУЧАЕМ ПРАВИЛЬНЫЕ ДАННЫЕ
    link_type = context.user_data.get('link_type')  # конкретный тип (instagram, youtube)
    category = context.user_data.get('category')  # категория для группировки (social)
    
    conn = await get_db_connection()
    
    # ДОБАВЬ ЭТОТ БЛОК ПЕРЕД INSERT:
    print("\n" + "!" * 30)
    print(f"DEBUG SAVE (add_link_url):")
    print(f"TITLE: {title}")
    print(f"ICON: {icon}")
    print(f"LINK_TYPE: {link_type}")
    print(f"CATEGORY: {category}")
    print("!" * 30 + "\n")
    
    try:
        user_db_row = await conn.fetchrow("SELECT id FROM users WHERE telegram_id = $1", user_id)
        page = await conn.fetchrow("SELECT id FROM pages WHERE user_id = $1", user_db_row['id'])
        
        max_sort = await conn.fetchval(
            "SELECT COALESCE(MAX(sort_order), 0) FROM links WHERE page_id = $1",
            page['id']
        )
        
        # ✅ ПРАВИЛЬНЫЙ INSERT
        await conn.execute("""
                           INSERT INTO links (page_id, title, url, icon,
                                              link_type, category,
                                              sort_order, is_active, is_exchange, created_at)
                           VALUES ($1, $2, $3, $4, $5, $6, $7, true, false, NOW())
                           """,
                           page['id'],  # $1
                           title,  # $2
                           url_val,  # $3
                           icon,  # $4
                           link_type,  # $5 - 'instagram' (конкретный тип)
                           category,  # $6 - 'social' (категория)
                           max_sort + 1  # $7
                           )
        
        # Кнопки, чтобы юзер не висел в пустоте
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➕ Добавить ещё", callback_data="add_link"),
                InlineKeyboardButton("🔗 Управление", callback_data="links")
            ],
            [InlineKeyboardButton("🏠 В меню", callback_data="start")]
        ])
        
        await update.message.reply_text(
            f"✅ Ссылка «{title}» добавлена!\nЧто делаем дальше?",
            reply_markup=keyboard
        )
    
    except Exception as e:
        print(f"Ошибка сохранения соцсети: {e}")
        await update.message.reply_text("❌ Ошибка при сохранении ссылки.")
    finally:
        await conn.close()
    
    # Чистим временные данные, но сохраняем нужные
    keys_to_clear = ['link_category', 'link_title', 'link_url', 'link_icon']
    for key in keys_to_clear:
        context.user_data.pop(key, None)
    
    return ConversationHandler.END


async def select_crypto_network(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import json
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import ConversationHandler
    
    query = update.callback_query
    
    # 1. СРАЗУ отвечаем на запрос, чтобы убрать "часики" с кнопки
    try:
        await query.answer()
    except Exception as e:
        print(f"Ошибка ответа на callback: {e}")
    
    # 2. Извлекаем данные
    net_code = query.data.replace("net_", "").upper()
    context.user_data['crypto_network'] = net_code
    
    user_id = update.effective_user.id
    url_val = context.user_data.get('link_url')
    title = context.user_data.get('link_title', 'Без названия')
    category = context.user_data.get('link_category')
    
    # ===== ВАЖНО: ПРАВИЛЬНЫЕ ЗНАЧЕНИЯ ДЛЯ КОШЕЛЬКА =====
    link_type = "crypto"
    is_exchange = False  # ← ИСПРАВЛЕНО: false для кошелька!
    db_category = "crypto"  # ← ДОБАВЛЕНО: категория для группировки
    # ====================================================
    
    # Обработка иконки: убираем расширение, если оно есть, и приводим к нижнему регистру
    icon = context.user_data.get('link_icon', 'link')
    if category == "wallets":
        coin_name = title.split('(')[0].strip().lower()
        icon = f"{coin_name}"
    
    # Дополнительная проверка, чтобы не пролетело ".png" в саму базу
    if isinstance(icon, str):
        icon = icon.replace('.png', '')
    
    # ===== ОПРЕДЕЛЯЕМ icon_class ДЛЯ FONTAWESOME =====
    icon_map = {
        'bitcoin': 'fab fa-bitcoin',
        'btc': 'fab fa-bitcoin',
        'ethereum': 'fab fa-ethereum',
        'eth': 'fab fa-ethereum',
        'litecoin': 'fab fa-litecoin-sign',
        'ltc': 'fab fa-litecoin-sign',
        'dogecoin': 'fab fa-dogecoin',
        'doge': 'fab fa-dogecoin',
        'binance': 'fab fa-bnb',
        'bnb': 'fab fa-bnb',
        'tether': 'fas fa-dollar-sign',
        'usdt': 'fas fa-dollar-sign',
        'solana': 'fas fa-sun',
        'sol': 'fas fa-sun',
        'ripple': 'fas fa-water',
        'xrp': 'fas fa-water',
    }
    
    coin_name = title.lower()
    icon_class = None
    for key, value in icon_map.items():
        if key in coin_name:
            icon_class = value
            break
    
    if not icon_class:
        icon_class = 'fas fa-coins'  # иконка по умолчанию
    # ==================================================
    
    # Формируем JSON структуру
    pay_details = json.dumps({
        "tabs": [{
            "name": net_code,
            "address": url_val,
            "network": net_code,
            "network_full": net_code,
            "qr_code": None
        }]
    }, ensure_ascii=False)
    
    # 3. Работа с БД
    conn = await get_db_connection()
    try:
        user_db_row = await conn.fetchrow("SELECT id FROM users WHERE telegram_id = $1", user_id)
        if not user_db_row:
            await query.message.reply_text("❌ Ошибка: пользователь не найден.")
            return ConversationHandler.END
        
        page = await conn.fetchrow("SELECT id FROM pages WHERE user_id = $1", user_db_row['id'])
        if not page:
            await query.message.reply_text("❌ Ошибка: страница не найдена.")
            return ConversationHandler.END
        
        max_sort = await conn.fetchval(
            "SELECT COALESCE(MAX(sort_order), 0) FROM links WHERE page_id = $1",
            page['id']
        )
        
        # ===== ИСПРАВЛЕННЫЙ INSERT СО ВСЕМИ ПОЛЯМИ =====
        await conn.execute("""
                           INSERT INTO links (page_id, title, url, icon, link_type, category,
                                              pay_details, sort_order, is_active, is_exchange, icon_class, created_at)
                           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, true, $9, $10, NOW())
                           """,
                           page['id'],  # $1
                           title,  # $2
                           url_val,  # $3
                           icon,  # $4
                           link_type,  # $5 - 'crypto'
                           db_category,  # $6 - 'crypto' (категория)
                           pay_details,  # $7
                           max_sort + 1,  # $8
                           is_exchange,  # $9 - false для кошелька
                           icon_class  # $10 - 'fab fa-bitcoin' и т.д.
                           )
        
        # Кнопки навигации
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➕ Добавить ещё", callback_data="add_link"),
                InlineKeyboardButton("🔗 Управление", callback_data="links")
            ],
            [InlineKeyboardButton("🏠 В главное меню", callback_data="start")]
        ])
        
        # 4. ОБНОВЛЯЕМ СООБЩЕНИЕ
        await query.edit_message_text(
            text=f"✅ Готово! «{title}» в сети {net_code} сохранена.",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА ЗАПИСИ: {e}")
        if query.message:
            await query.message.reply_text(f"❌ Произошла ошибка при сохранении: {e}")
    finally:
        await conn.close()
    
    # Очистка контекста
    keys_to_clear = ['link_category', 'link_type', 'link_info', 'link_title', 'link_url', 'crypto_network', 'link_icon']
    for key in keys_to_clear:
        context.user_data.pop(key, None)
    
    return ConversationHandler.END


async def ask_for_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запрос URL для обычной ссылки"""
    text = "🔗 **Введи ссылку:**\n\n"
    text += "Можно отправить:\n"
    text += "• Полную ссылку: `https://example.com`\n"
    text += "• Просто название сайта: `example.com`\n"
    text += "• Имя пользователя: `@username` (для Telegram)\n\n"
    text += "Ссылка должна открываться в браузере"
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data=f"cat_{context.user_data['link_category']}")]]
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    return ADD_LINK_URL


# bot/link_constructor.py

# bot/link_constructor.py


async def wait_custom_network(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Шаг получения названия сети вручную"""
    custom_net = update.message.text.strip()
    
    if len(custom_net) > 30:
        await update.message.reply_text("❌ Слишком длинное название. Попробуй короче:")
        return WAIT_CUSTOM_NETWORK
    
    context.user_data['crypto_network'] = custom_net
    return await finish_link_creation(update, context)


async def show_icon_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает выбор иконок"""
    conn = await get_db_connection()
    try:
        # Берем первые 8 иконок для простоты
        icons = await conn.fetch("SELECT icon_code, name FROM icons WHERE is_active = true ORDER BY sort_order LIMIT 8")
        
        keyboard = []
        row = []
        for i, icon in enumerate(icons):
            row.append(InlineKeyboardButton(icon['name'], callback_data=f"icon_{icon['icon_code']}"))
            if len(row) == 2 or i == len(icons) - 1:
                keyboard.append(row)
                row = []
        
        keyboard.append([InlineKeyboardButton("◀️ Отмена", callback_data="cancel")])
        
        await update.message.reply_text(
            "🎨 **Выбери иконку для ссылки:**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return ADD_LINK_ICON
    finally:
        await conn.close()


async def ask_for_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запрос описания для соцсетей"""
    await update.message.reply_text(
        "📝 **Добавь описание (необязательно)**\n\n"
        "Например: «Канал про путешествия» или «Группа для программистов»\n\n"
        "Если не хочешь добавлять описание, отправь /skip",
        parse_mode='Markdown'
    )
    
    return ADD_LINK_DESCRIPTION


async def add_link_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранение описания"""
    description = update.message.text.strip()
    
    if len(description) > 200:
        await update.message.reply_text(
            "❌ Описание слишком длинное (макс. 200 символов).\n"
            "Попробуй еще раз или отправь /skip:"
        )
        return ADD_LINK_DESCRIPTION
    
    context.user_data['link_description'] = description
    return await finish_link_creation(update, context)


async def skip_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пропуск описания"""
    context.user_data['link_description'] = None
    await update.message.reply_text("⏭ Описание пропущено")
    return await finish_link_creation(update, context)


async def ask_for_text_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запрос текстового содержимого для заметки"""
    text = "📝 **Введи текст заметки**\n\n"
    text += "Это может быть:\n"
    text += "• Расписание стримов\n"
    text += "• FAQ или информация\n"
    text += "• Любой другой текст\n\n"
    text += "Поддерживается перенос строк"
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data=f"cat_{context.user_data['link_category']}")]]
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    return ADD_LINK_URL  # Переиспользуем тот же стейт для ввода текста


async def ask_for_finance_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запрос финансовых реквизитов с точными инструкциями по формату"""
    subtype = context.user_data.get('finance_subtype', 'custom')
    tab = context.user_data.get('finance_tab')
    
    # Определяем заголовок для красоты
    header = subtype.upper() if subtype != 'custom' else "Реквизиты"
    text = f"📥 **Настройка {header}**\n\n"
    
    # Сценарий: Российские банки
    if subtype in ["sber", "tinkoff"]:
        if tab == "card":
            text += "💳 **Номер карты:**\n"
            text += "Введите 16 цифр карты. Можно добавить имя через запятую.\n"
            text += "Пример: `5469 3800 8049 6952, Иван П.`"
        elif tab == "phone":
            text += "📱 **Перевод по номеру:**\n"
            text += "Введите номер телефона и имя через запятую.\n"
            text += "Пример: `+79161234567, Иван П.`"
    
    # Сценарий: Крипто-биржи
    elif subtype in ["binance", "bybit", "okx"]:
        if tab == "uid":
            text += "🆔 **Ваш UID:**\n"
            text += "Введите только цифры вашего идентификатора. \n"
            text += "• _Пробелы и знаки будут удалены автоматически._\n"
            text += "Пример: `111754183`"
        else:
            text += f"💰 **Кошелек {tab.upper()}:**\n"
            text += "Введите адрес и сеть через запятую.\n"
            text += "Пример: `0x2Bc3...D71f, ERC-20`\n\n"
            text += "ℹ️ **QR-код** для этого адреса будет создан автоматически и отобразится на вашей странице."
    
    # Сценарий: Revolut
    elif subtype == "revolut":
        text += "🇪🇺 **Реквизиты Revolut:**\n"
        text += "Введите данные через запятую в формате:\n"
        text += "`IBAN, BIC, Имя, Ссылка на профиль`"
    
    # Все остальное
    else:
        text += "📝 **Введите данные:**\n"
        text += "Укажите номер счета или адрес, а затем детали через запятую.\n"
        text += "Пример: `T928374... , Личный кошелек`"
    
    text += "\n\n⚠️ **Важно:** Проверьте правильность данных перед отправкой."
    
    # Исправлена кнопка назад (убрано лишнее 'index' если оно ломало паттерн)
    category = context.user_data.get('link_category', 'other')
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data=f"cat_{category}")]]
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    return ADD_LINK_URL


# bot/link_constructor.py

async def finish_link_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Определяем, как отвечать пользователю (редактировать старое или слать новое)
    msg = update.message if update.message else update.callback_query.message
    
    # Извлекаем все накопленные данные
    category = context.user_data.get('link_category')
    link_type = context.user_data.get('link_type')
    title = context.user_data.get('link_title')
    url = context.user_data.get('link_url')
    description = context.user_data.get('link_description')
    finance_subtype = context.user_data.get('finance_subtype')
    finance_tab = context.user_data.get('finance_tab')
    is_finance = context.user_data.get('link_info', {}).get('is_finance')
    
    pay_details = None
    
    
    
    
    
    # ПАТЧ 1: Фиксируем тип для финансовых инструментов
    if is_finance:
        link_type = finance_subtype
    
    # ПАТЧ 3: Формирование JSON для крипто-кошельков (одиночных)
    if category == "wallets" or link_type == "crypto":
        link_type = "crypto"
        network_val = context.user_data.get('crypto_network', 'Network')
        address_val = url
        
        pay_details = json.dumps({
            "tabs": [
                {
                    "name": network_val,
                    "address": address_val,
                    "network": network_val,
                    "network_full": network_val,
                    "qr_code": None
                }
            ]
        })
    
    # Обработка других финансовых типов (банки, биржи с табами)
    elif is_finance:
        parts = url.split(',') if url else []
        clean_parts = [p.strip() for p in parts]
        
        if finance_subtype in ["sber", "tinkoff"]:
            if finance_tab == "card":
                pay_details = json.dumps({
                    "type": "card",
                    "card_number": clean_parts[0] if len(clean_parts) > 0 else "",
                    "beneficiary": clean_parts[1] if len(clean_parts) > 1 else ""
                })
            elif finance_tab == "phone":
                pay_details = json.dumps({
                    "type": "phone",
                    "phone": clean_parts[0] if len(clean_parts) > 0 else "",
                    "beneficiary": clean_parts[1] if len(clean_parts) > 1 else ""
                })
        
        elif finance_subtype in ["binance", "bybit", "okx", "kucoin", "gateio"]:
            if finance_tab == "uid":
                pay_details = json.dumps({
                    "type": "uid",
                    "uid": clean_parts[0] if len(clean_parts) > 0 else ""
                })
            else:
                pay_details = json.dumps({
                    "tabs": [
                        {
                            "name": finance_tab.upper() if finance_tab else "USDT",
                            "address": clean_parts[0] if len(clean_parts) > 0 else "",
                            "network": clean_parts[1] if len(clean_parts) > 1 else "TRC-20",
                            "network_full": clean_parts[1] if len(clean_parts) > 1 else "Tron",
                            "qr_code": None
                        }
                    ]
                })
        
        elif finance_subtype == "revolut":
            pay_details = json.dumps({
                "iban": clean_parts[0] if len(clean_parts) > 0 else "",
                "bic": clean_parts[1] if len(clean_parts) > 1 else "",
                "beneficiary": clean_parts[2] if len(clean_parts) > 2 else "",
                "payment_link": clean_parts[3] if len(clean_parts) > 3 else ""
            })
        else:
            pay_details = json.dumps({"details": url})
    
    # Обработка текстовых блоков
    elif link_type == 'text':
        pay_details = json.dumps({"text": url})
        url = "#"
    
    # ===== ОБРЕЗАЕМ ВСЕ СТРОКИ =====
    
    # 1. Title - обычно VARCHAR(255)
    if title and len(title) > 255:
        title = title[:255]
        print(f"⚠️ Title обрезан до 255 символов")
    
    # 2. URL - обычно VARCHAR(500) или TEXT
    if url and len(url) > 500:
        url = url[:500]
        print(f"⚠️ URL обрезан до 500 символов")
    
    # 3. Icon - обычно VARCHAR(100)
    icon = context.user_data.get('link_icon', 'link')
    if icon and len(icon) > 100:
        icon = icon[:100]
        print(f"⚠️ Icon обрезана до 100 символов")
    
    # 4. link_type - обычно VARCHAR(50)
    link_type_saved = context.user_data.get('link_type')
    if link_type_saved and len(link_type_saved) > 50:
        link_type_saved = link_type_saved[:50]
        print(f"⚠️ link_type обрезан до 50 символов")
    
    # 5. category - обычно VARCHAR(50)
    category_saved = context.user_data.get('category')
    if category_saved and len(category_saved) > 50:
        category_saved = category_saved[:50]
        print(f"⚠️ category обрезана до 50 символов")
    
    # 6. JSON данные - подготавливаем и обрезаем
    pay_details_json = pay_details  # pay_details уже json.dumps()
    if pay_details_json and len(pay_details_json) > 10000:  # для TEXT поля
        pay_details_json = pay_details_json[:10000]
        print(f"⚠️ pay_details JSON обрезан до 10000 символов")
    
    # Сохранение в базу данных
    conn = await get_db_connection()
    try:
        user_db_id = await conn.fetchval("SELECT id FROM users WHERE telegram_id = $1", user_id)
        if not user_db_id:
            await msg.reply_text("❌ Ошибка: пользователь не найден")
            return ConversationHandler.END
        
        page = await conn.fetchrow("SELECT id FROM pages WHERE user_id = $1", user_db_id)
        if not page:
            await msg.reply_text("❌ Ошибка: страница не найдена")
            return ConversationHandler.END
        
        max_sort = await conn.fetchval(
            "SELECT COALESCE(MAX(sort_order), 0) FROM links WHERE page_id = $1",
            page['id']
        )
        
        # Добавь ЭТОТ КОД перед await conn.execute(...)
        print("\n" + "🔥" * 30)
        print(f"СОХРАНЯЮ ССЫЛКУ:")
        print(f"title: {title}")
        print(f"link_type из user_data: {context.user_data.get('link_type')}")
        print(f"category из user_data: {context.user_data.get('category')}")
        print(f"icon: {icon}")
        print("🔥" * 30 + "\n")
        
        await conn.execute("""
                           INSERT INTO links (page_id, title, url, icon,
                                              link_type, category,
                                              pay_details, sort_order, is_active, click_count, created_at, is_exchange)
                           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, true, 0, NOW(), $9)
                           """,
                           page['id'],
                           title,  # обрезанный
                           url,  # обрезанный
                           icon,  # обрезанный
                           link_type_saved,  # обрезанный
                           category_saved,  # обрезанная
                           pay_details_json,  # обрезанный JSON
                           max_sort + 1,
                           context.user_data.get('is_exchange', False)
                           )
        
        # Формируем текст успеха ДО очистки context.user_data
        success_text = (
            f"✅ **Данные успешно добавлены!**\n\n"
            f"📌 **Название:** {title}\n"
            f"🌐 **Тип:** {link_type.upper()}\n\n"
            f"Что вы хотите сделать дальше?"
        )
        
        # Очистка всех временных данных конструктора
        keys_to_clear = [
            'link_category', 'link_type', 'link_info', 'link_title',
            'link_url', 'link_description', 'finance_subtype', 'finance_tab', 'crypto_network'
        ]
        for key in keys_to_clear:
            context.user_data.pop(key, None)
        
        # Клавиатура с выбором действий
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Добавить ещё одну ссылку", callback_data="add_link")],
            [InlineKeyboardButton("🔗 Управление моими ссылками", callback_data="links")],
            [InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="start")]
        ])
        
        # Отправляем ответ пользователю
        if update.callback_query:
            await update.callback_query.edit_message_text(success_text, reply_markup=keyboard, parse_mode='Markdown')
        else:
            await msg.reply_text(success_text, reply_markup=keyboard, parse_mode='Markdown')
    
    except Exception as e:
        print(f"Ошибка сохранения: {e}")
        await msg.reply_text("❌ Произошла ошибка при сохранении данных в базу.")
    finally:
        await conn.close()
    
    return ConversationHandler.END


# ========== СОЗДАНИЕ CONVERSATION HANDLER ==========

async def smart_title_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Функция-регулировщик: Биржи — направо, Инстаграм — налево"""
    
    # Проверяем, есть ли данные в памяти
    if context.user_data.get('finance_data_map'):
        # Если это БИРЖА — вызываем локальный тихий финиш
        # (Создай эту функцию ниже, если её нет)
        return await finalize_finance_modal(update, context)
    
    # Если это ОБЫЧНАЯ ссылка — вызываем ту самую функцию из handlers.py
    from bot.handlers import add_link_title
    return await add_link_title(update, context)


async def handle_net_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Логика: Ловит нажатие на кнопку сети (pattern="^net_").
    Запоминает сеть и просит ввести адрес.
    """
    query = update.callback_query
    await query.answer()
    
    # Извлекаем сеть из callback_data (например, "net_TRC20" -> "TRC20")
    selected_net = query.data.replace("net_", "")
    context.user_data['temp_net'] = selected_net
    
    current_coin = context.user_data.get('current_collecting_coin', 'крипты')
    
    await query.edit_message_text(
        f"✅ Сеть **{selected_net}** выбрана.\n\n"
        f"📥 Теперь отправьте сообщением **адрес** для {current_coin.upper()}:",
        parse_mode='Markdown'
    )
    return ADD_MULTI_FINANCE_DATA


async def process_multi_finance_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Логика: Ловит текстовое сообщение с адресом.
    Сохраняет его в карту данных и переходит к следующей монете или финалу.
    """
    if not update.message or not update.message.text:
        return ADD_MULTI_FINANCE_DATA
    
    address = update.message.text.strip()
    current_coin = context.user_data.get('current_collecting_coin')
    selected_net = context.user_data.get('temp_net', 'Mainnet')
    
    if 'finance_data_map' not in context.user_data:
        context.user_data['finance_data_map'] = {}
    
    # Сохраняем адрес и сеть для текущей монеты
    context.user_data['finance_data_map'][current_coin] = {
        "address": address,
        "net": selected_net
    }
    
    # Очищаем временную сеть для следующего шага
    context.user_data['temp_net'] = 'Mainnet'
    
    # Возвращаемся в ask_for_multi_finance_details, чтобы проверить, остались ли еще монеты
    return await ask_for_multi_finance_details(update, context)


async def ask_for_multi_finance_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    ФУНКЦИЯ: ask_for_multi_finance_details
    belong_to: bot/link_constructor.py
    Логика: Циклически опрашивает юзера по каждой выбранной монете.
    """
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from bot.states import ADD_MULTI_FINANCE_DATA
    
    query = update.callback_query
    if query:
        await query.answer()
    
    # Если нажали на кнопку сети (пришли из Callback)
    if query and query.data.startswith("net_"):
        selected_net = query.data.replace("net_", "")
        context.user_data['temp_net'] = selected_net
        
        current_coin = context.user_data.get('current_collecting_coin', 'актива')
        
        # Используем <b> вместо ** для жирности
        text = (
            f"✅ Сеть <b>{selected_net}</b> выбрана.\n\n"
            f"📥 Теперь пришлите сообщением <b>адрес</b> для {current_coin.upper()}:"
        )
        await query.edit_message_text(text, parse_mode='HTML')
        return ADD_MULTI_FINANCE_DATA
    
    # Ищем следующую монету для опроса
    selected_coins = context.user_data.get('selected_currencies', [])
    data_map = context.user_data.get('finance_data_map', {})
    
    next_coin = None
    for coin in selected_coins:
        if coin not in data_map:
            next_coin = coin
            break
    
    # Если все монеты обработаны — сохраняем в базу
    if not next_coin:
        return await finalize_finance_modal(update, context)
    
    # Процесс сбора
    context.user_data['current_collecting_coin'] = next_coin
    
    if next_coin.lower() == 'uid':
        text = f"🆔 Введите ваш <b>UID</b> для этой биржи (отправьте текстом):"
        if query:
            await query.edit_message_text(text, parse_mode='HTML')
        else:
            await update.effective_message.reply_text(text, parse_mode='HTML')
    else:
        # Конфиг сетей
        networks_config = {
            'usdt': ['TRC20', 'ERC20', 'BEP20'],
            'eth': ['ERC20', 'Arbitrum', 'Optimism'],
            'btc': ['Mainnet', 'BEP20'],
            'bnb': ['BEP20', 'BEP2'],
            'sol': ['Mainnet'],
            'trx': ['Mainnet']
        }
        
        coin_nets = networks_config.get(next_coin.lower(), ['Mainnet', 'BEP20'])
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"🌐 {net}", callback_data=f"net_{net}")]
            for net in coin_nets
        ])
        
        text = f"💰 Настройка для <b>{next_coin.upper()}</b>\n\nСначала выберите <b>сеть</b>:"
        
        if query:
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='HTML')
        else:
            await update.effective_message.reply_text(text, reply_markup=keyboard, parse_mode='HTML')
    
    return ADD_MULTI_FINANCE_DATA


async def handle_multi_finance_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Вызывается, когда юзер прислал ТЕКСТ (адрес или UID).
    """
    if not update.message or not update.message.text:
        return ADD_MULTI_FINANCE_DATA
    
    val = update.message.text.strip()
    current_coin = context.user_data.get('current_collecting_coin')
    selected_net = context.user_data.get('temp_net', 'Mainnet')
    
    if 'finance_data_map' not in context.user_data:
        context.user_data['finance_data_map'] = {}
    
    # Сохраняем данные
    context.user_data['finance_data_map'][current_coin] = {
        "address": val,
        "net": selected_net
    }
    
    # Сброс временной сети и переход к следующей монете
    context.user_data['temp_net'] = 'Mainnet'
    return await ask_for_multi_finance_details(update, context)


# Функция: finalize_and_save_link
# belong_to: bot/link_constructor.py
async def finalize_and_save_link(update, context):
    """Финальная точка сохранения для всех типов ссылок (особенно бирж)"""
    user_db_id = context.user_data.get('db_user_id')
    subtype = context.user_data.get('finance_subtype')  # 'okx', 'binance' и т.д.
    data_map = context.user_data.get('finance_data_map', {})
    
    # 1. Если это биржа (мульти-виджет), формируем табы
    if subtype in ["binance", "bybit", "okx", "kucoin", "metamask", "gateio",
                   "huobi", "trustwallet", "coinbase", "kraken"]:
        tabs = []
        for coin_type, value in data_map.items():
            net = coin_type.split('_')[1].upper() if '_' in coin_type else coin_type.upper()
            tabs.append({
                "name": coin_type.replace('_', ' ').upper(),
                "address": value,
                "network": net,
                "network_full": net,
                "qr_code": None
            })
        
        pay_details = json.dumps({"tabs": tabs})
        # ВАЖНО: записываем в link_type именно subtype, чтобы сработал HTML
        link_type = subtype
        url = "#modal"
        icon = subtype
        title = context.user_data.get('selected_preset_name', subtype.capitalize())
    else:
        # Для обычных ссылок (старая логика)
        pay_details = None
        link_type = context.user_data.get('link_type')
        url = context.user_data.get('link_url')
        icon = context.user_data.get('link_icon')
        title = context.user_data.get('link_title')
    
    conn = await get_db_connection()
    try:
        # Получаем ID страницы
        page = await conn.fetchrow("SELECT id FROM pages WHERE user_id = $1", user_db_id)
        
        await conn.execute("""
                           INSERT INTO public.links
                           (page_id, title, url, icon, link_type, pay_details, is_active, created_at)
                           VALUES ($1, $2, $3, $4, $5, $6, true, NOW())
                           """, page['id'], title, url, icon, link_type, pay_details)
        
        msg = "✅ Ссылка успешно добавлена!"
        if update.callback_query:
            await update.callback_query.edit_message_text(msg)
        else:
            await update.message.reply_text(msg)
    
    finally:
        await conn.close()
    
    return ConversationHandler.END


async def back_to_previous(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться к предыдущему шагу"""
    print("\n" + "=" * 60)
    print("🔙 back_to_previous ВЫЗВАН")
    
    print(f"  🔍 ТЕКУЩЕЕ СОСТОЯНИЕ ДИАЛОГА: {context.user_data.get('_state', 'None')}")
    
    query = update.callback_query
    await query.answer()
    
    step_index = context.user_data.get('step_index', 0)
    print(f"  📍 Текущий шаг index: {step_index}")
    
    # Если на первом шаге - возврат к выбору типа
    if step_index <= 0:
        print(f"  🔄 На первом шаге, возврат к выбору типа")
        return await back_to_types(update, context)
    
    # ВАЖНО: Если это шаг после выбора типа (шаг 2), нужно восстановить полный конфиг
    if step_index == 2:
        # Восстанавливаем полный конфиг из сохраненной копии
        if 'full_type_config' in context.user_data:
            import copy
            context.user_data['type_config'] = copy.deepcopy(context.user_data['full_type_config'])
            print(f"  🔄 Восстановлен полный конфиг из full_type_config")
        else:
            # Если нет сохраненной копии, пробуем из оригинального типа
            original_type = context.user_data.get('original_link_type')
            if original_type:
                try:
                    from bot.types_config import LINK_TYPES
                    full_config = LINK_TYPES.get(original_type, {}).copy()
                    context.user_data['type_config'] = full_config
                    print(f"  🔄 Восстановлен полный конфиг для {original_type}")
                except ImportError:
                    print(f"  ❌ Не удалось импортировать LINK_TYPES из types_config")
    
    # Удаляем данные последнего шага
    last_field = None
    steps = context.user_data.get('type_config', {}).get('steps', [])
    if step_index - 1 < len(steps):
        last_step = steps[step_index - 1]
        last_field = last_step.get('field')
        if last_field and last_field in context.user_data.get('collected_data', {}):
            del context.user_data['collected_data'][last_field]
            print(f"  🗑️ Удалено поле: {last_field}")
    
    # Иначе на предыдущий шаг
    context.user_data['step_index'] = step_index - 1
    print(f"  🔄 Возврат к шагу {context.user_data['step_index']}")
    print("=" * 60)
    
    return await process_current_step(update, context)
