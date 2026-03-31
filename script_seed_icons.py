# seed_icons.py (полная версия со всеми иконками)
import asyncio
import asyncpg
import logging
from core.config import DATABASE_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Все иконки для проекта (включая все категории для шаблона 011den)
ICONS = [
    # ========== СОЦИАЛЬНЫЕ СЕТИ ==========
    {"name": "Instagram", "icon_code": "instagram", "category": "social", "keywords": ["insta", "photo", "social"], "font_awesome_class": "fab fa-instagram"},
    {"name": "TikTok", "icon_code": "tiktok", "category": "social", "keywords": ["tik", "tok", "video"], "font_awesome_class": "fab fa-tiktok"},
    {"name": "YouTube", "icon_code": "youtube", "category": "social", "keywords": ["youtube", "video", "channel"], "font_awesome_class": "fab fa-youtube"},
    {"name": "Twitch", "icon_code": "twitch", "category": "social", "keywords": ["twitch", "stream", "game"], "font_awesome_class": "fab fa-twitch"},
    {"name": "Telegram", "icon_code": "telegram_social", "category": "social", "keywords": ["tg", "telegram", "channel"], "font_awesome_class": "fab fa-telegram"},
    {"name": "VK", "icon_code": "vk", "category": "social", "keywords": ["vk", "vkontakte"], "font_awesome_class": "fab fa-vk"},
    {"name": "Twitter", "icon_code": "twitter", "category": "social", "keywords": ["twitter", "x"], "font_awesome_class": "fab fa-twitter"},
    {"name": "Facebook", "icon_code": "facebook", "category": "social", "keywords": ["fb", "facebook"], "font_awesome_class": "fab fa-facebook"},
    {"name": "LinkedIn", "icon_code": "linkedin", "category": "social", "keywords": ["linkedin", "job"], "font_awesome_class": "fab fa-linkedin"},
    {"name": "Pinterest", "icon_code": "pinterest", "category": "social", "keywords": ["pinterest", "pin"], "font_awesome_class": "fab fa-pinterest"},
    {"name": "Snapchat", "icon_code": "snapchat", "category": "social", "keywords": ["snap", "chat"], "font_awesome_class": "fab fa-snapchat"},
    {"name": "Discord", "icon_code": "discord", "category": "social", "keywords": ["discord"], "font_awesome_class": "fab fa-discord"},
    {"name": "Medium", "icon_code": "medium", "category": "social", "keywords": ["medium", "blog"], "font_awesome_class": "fab fa-medium"},
    {"name": "Reddit", "icon_code": "reddit", "category": "social", "keywords": ["reddit"], "font_awesome_class": "fab fa-reddit"},
    {"name": "Одноклассники", "icon_code": "ok", "category": "social", "keywords": ["ok", "odnoklassniki"], "font_awesome_class": "fab fa-odnoklassniki"},
    {"name": "Rutube", "icon_code": "rutube", "category": "social", "keywords": ["rutube"], "font_awesome_class": "fas fa-play-circle"},
    {"name": "Дзен", "icon_code": "dzen", "category": "social", "keywords": ["dzen", "yandex"], "font_awesome_class": "fab fa-yandex-international"},
    {"name": "TenChat", "icon_code": "tenchat", "category": "social", "keywords": ["tenchat"], "font_awesome_class": "fas fa-briefcase"},
    {"name": "Likee", "icon_code": "likee", "category": "social", "keywords": ["likee"], "font_awesome_class": "fas fa-thumbs-up"},
    {"name": "Threads", "icon_code": "threads", "category": "social", "keywords": ["threads"], "font_awesome_class": "fab fa-threads"},

    # ========== МЕССЕНДЖЕРЫ ==========
    {"name": "WhatsApp", "icon_code": "whatsapp", "category": "messenger", "keywords": ["whatsapp", "wa"], "font_awesome_class": "fab fa-whatsapp"},
    {"name": "Telegram Chat", "icon_code": "telegram_chat", "category": "messenger", "keywords": ["tg", "chat"], "font_awesome_class": "fab fa-telegram"},
    {"name": "Viber", "icon_code": "viber", "category": "messenger", "keywords": ["viber"], "font_awesome_class": "fab fa-viber"},
    {"name": "Signal", "icon_code": "signal", "category": "messenger", "keywords": ["signal"], "font_awesome_class": "fas fa-comment"},
    
    {"name": "Messenger", "icon_code": "messenger", "category": "messenger", "keywords": ["fb", "messenger"], "font_awesome_class": "fab fa-facebook-messenger"},
    {"name": "Skype", "icon_code": "skype", "category": "messenger", "keywords": ["skype"], "font_awesome_class": "fab fa-skype"},
    {"name": "Zalo", "icon_code": "zalo", "category": "messenger", "keywords": ["zalo"], "font_awesome_class": "fas fa-comment-dots"},
    {"name": "FaceTime", "icon_code": "facetime", "category": "messenger", "keywords": ["facetime"], "font_awesome_class": "fab fa-apple"},
    

    # ========== ПЛАТЕЖИ И ДОНАТЫ ==========
    {"name": "DonationAlerts", "icon_code": "donationalerts", "category": "payment", "keywords": ["donation", "donat", "alert"], "font_awesome_class": "fas fa-heart"},
    {"name": "Streamlabs", "icon_code": "streamlabs", "category": "payment", "keywords": ["stream", "donation"], "font_awesome_class": "fas fa-stream"},
    {"name": "Buy Me a Coffee", "icon_code": "buymeacoffee", "category": "payment", "keywords": ["coffee", "donation"], "font_awesome_class": "fas fa-mug-hot"},
    {"name": "Patreon", "icon_code": "patreon", "category": "payment", "keywords": ["patreon"], "font_awesome_class": "fab fa-patreon"},
    {"name": "Boosty", "icon_code": "boosty", "category": "payment", "keywords": ["boosty"], "font_awesome_class": "fas fa-bolt"},
    {"name": "Qiwi", "icon_code": "qiwi", "category": "payment", "keywords": ["qiwi"], "font_awesome_class": "fas fa-wallet"},
    {"name": "ЮMoney", "icon_code": "yoomoney", "category": "payment", "keywords": ["yoomoney", "yandex"], "font_awesome_class": "fas fa-ruble-sign"},
    {"name": "CloudTips", "icon_code": "cloudtips", "category": "payment", "keywords": ["cloudtips", "tips"], "font_awesome_class": "fas fa-cloud"},
    {"name": "PayPal", "icon_code": "paypal", "category": "payment", "keywords": ["paypal"], "font_awesome_class": "fab fa-paypal"},
    {"name": "Ko-fi", "icon_code": "kofi", "category": "payment", "keywords": ["kofi", "coffee"], "font_awesome_class": "fas fa-mug-saucer"},

    # ========== БАНКОВСКИЕ КАРТЫ ==========
    {"name": "Visa", "icon_code": "visa", "category": "bank", "keywords": ["visa", "card"], "font_awesome_class": "fab fa-cc-visa"},
    {"name": "Mastercard", "icon_code": "mastercard", "category": "bank", "keywords": ["mastercard"], "font_awesome_class": "fab fa-cc-mastercard"},
    {"name": "Мир", "icon_code": "mir", "category": "bank", "keywords": ["mir"], "font_awesome_class": "fas fa-credit-card"},
    {"name": "American Express", "icon_code": "amex", "category": "bank", "keywords": ["amex"], "font_awesome_class": "fab fa-cc-amex"},
    {"name": "СБП", "icon_code": "sbp", "category": "bank", "keywords": ["sbp", "перевод"], "font_awesome_class": "fas fa-arrow-right-arrow-left"},

    # ========== ФИНАНСОВЫЕ СИСТЕМЫ (ПЕРЕВОДЫ) ==========
    {"name": "Revolut", "icon_code": "revolut", "category": "finance", "keywords": ["revolut"], "font_awesome_class": "fas fa-university"},
    {"name": "Wise", "icon_code": "wise", "category": "finance", "keywords": ["wise"], "font_awesome_class": "fas fa-exchange-alt"},
    {"name": "Криптобот", "icon_code": "cryptobot", "category": "finance", "keywords": ["cryptobot"], "font_awesome_class": "fab fa-bitcoin"},
    {"name": "Тинькофф", "icon_code": "tinkoff", "category": "finance", "keywords": ["tinkoff"], "font_awesome_class": "fas fa-credit-card"},
    {"name": "Сбер", "icon_code": "sber", "category": "finance", "keywords": ["sber", "сбербанк"], "font_awesome_class": "fas fa-university"},
    {"name": "BIDV", "icon_code": "bidv", "category": "finance", "keywords": ["bidv"], "font_awesome_class": "fas fa-university"},
    {"name": "Золотая Корона", "icon_code": "korona", "category": "finance", "keywords": ["korona"], "font_awesome_class": "fas fa-crown"},
    {"name": "Western Union", "icon_code": "westernunion", "category": "finance", "keywords": ["western union"], "font_awesome_class": "fas fa-globe"},
    {"name": "Unistream", "icon_code": "unistream", "category": "finance", "keywords": ["unistream"], "font_awesome_class": "fas fa-arrow-right-arrow-left"},
    {"name": "Contact", "icon_code": "contact", "category": "finance", "keywords": ["contact"], "font_awesome_class": "fas fa-address-book"},

    # ========== КРИПТОВАЛЮТЫ ==========
    {"name": "Bitcoin", "icon_code": "btc", "category": "crypto", "keywords": ["btc", "bitcoin"], "font_awesome_class": "fab fa-bitcoin"},
    {"name": "Ethereum", "icon_code": "eth", "category": "crypto", "keywords": ["eth", "ethereum"], "font_awesome_class": "fab fa-ethereum"},
    {"name": "USDT", "icon_code": "usdt", "category": "crypto", "keywords": ["usdt", "tether"], "font_awesome_class": "fas fa-dollar-sign"},
    {"name": "Litecoin", "icon_code": "ltc", "category": "crypto", "keywords": ["ltc", "litecoin"], "font_awesome_class": "fab fa-litecoin-sign"},
    {"name": "Dogecoin", "icon_code": "doge", "category": "crypto", "keywords": ["doge"], "font_awesome_class": "fab fa-dogecoin"},
    {"name": "Binance Coin", "icon_code": "bnb", "category": "crypto", "keywords": ["bnb"], "font_awesome_class": "fab fa-bnb"},

    # ========== БИРЖИ КРИПТОВАЛЮТ ==========
    {"name": "Binance", "icon_code": "binance", "category": "exchange", "keywords": ["binance"], "font_awesome_class": "fab fa-bnb"},
    {"name": "Bybit", "icon_code": "bybit", "category": "exchange", "keywords": ["bybit"], "font_awesome_class": "fas fa-chart-line"},
    {"name": "OKX", "icon_code": "okx", "category": "exchange", "keywords": ["okx"], "font_awesome_class": "fas fa-coins"},
    {"name": "KuCoin", "icon_code": "kucoin", "category": "exchange", "keywords": ["kucoin"], "font_awesome_class": "fas fa-coins"},
    {"name": "Gate.io", "icon_code": "gateio", "category": "exchange", "keywords": ["gateio"], "font_awesome_class": "fas fa-gate"},
    {"name": "Huobi", "icon_code": "huobi", "category": "exchange", "keywords": ["huobi"], "font_awesome_class": "fas fa-fire"},

    # ========== КРИПТО-КОШЕЛЬКИ ==========
    {"name": "Metamask", "icon_code": "metamask", "category": "wallet", "keywords": ["metamask"], "font_awesome_class": "fab fa-firefox-browser"},
    {"name": "Trust Wallet", "icon_code": "trustwallet", "category": "wallet", "keywords": ["trustwallet"], "font_awesome_class": "fas fa-shield-alt"},
    {"name": "Coinbase", "icon_code": "coinbase", "category": "wallet", "keywords": ["coinbase"], "font_awesome_class": "fab fa-coinbase"},
    {"name": "Kraken", "icon_code": "kraken", "category": "wallet", "keywords": ["kraken"], "font_awesome_class": "fab fa-octopus-deploy"},

    # ========== МУЗЫКА И СТРИМИНГ ==========
    {"name": "Spotify", "icon_code": "spotify", "category": "music", "keywords": ["spotify"], "font_awesome_class": "fab fa-spotify"},
    {"name": "Apple Music", "icon_code": "applemusic", "category": "music", "keywords": ["apple"], "font_awesome_class": "fab fa-apple"},
    {"name": "YouTube Music", "icon_code": "youtubemusic", "category": "music", "keywords": ["youtube"], "font_awesome_class": "fab fa-youtube"},
    {"name": "SoundCloud", "icon_code": "soundcloud", "category": "music", "keywords": ["soundcloud"], "font_awesome_class": "fab fa-soundcloud"},
    {"name": "Bandcamp", "icon_code": "bandcamp", "category": "music", "keywords": ["bandcamp"], "font_awesome_class": "fab fa-bandcamp"},

    # ========== МАГАЗИНЫ ==========
    {"name": "Wildberries", "icon_code": "wildberries", "category": "shop", "keywords": ["wildberries", "wb"], "font_awesome_class": "fas fa-shopping-bag"},
    {"name": "Ozon", "icon_code": "ozon", "category": "shop", "keywords": ["ozon"], "font_awesome_class": "fas fa-shopping-cart"},
    {"name": "Avito", "icon_code": "avito", "category": "shop", "keywords": ["avito"], "font_awesome_class": "fas fa-tag"},
    {"name": "Яндекс Маркет", "icon_code": "yandex_market", "category": "shop", "keywords": ["yandex market"], "font_awesome_class": "fab fa-yandex"},
    {"name": "AliExpress", "icon_code": "aliexpress", "category": "shop", "keywords": ["aliexpress"], "font_awesome_class": "fab fa-alipay"},
    {"name": "KazanExpress", "icon_code": "kazanexpress", "category": "shop", "keywords": ["kazanexpress"], "font_awesome_class": "fas fa-truck"},
    {"name": "Amazon", "icon_code": "amazon", "category": "shop", "keywords": ["amazon"], "font_awesome_class": "fab fa-amazon"},
    {"name": "eBay", "icon_code": "ebay", "category": "shop", "keywords": ["ebay"], "font_awesome_class": "fab fa-ebay"},
    {"name": "Etsy", "icon_code": "etsy", "category": "shop", "keywords": ["etsy"], "font_awesome_class": "fab fa-etsy"},
    {"name": "Shopify", "icon_code": "shopify", "category": "shop", "keywords": ["shopify"], "font_awesome_class": "fab fa-shopify"},

    # ========== ПАРТНЕРКИ ==========
    {"name": "Партнерская ссылка", "icon_code": "partner", "category": "partner", "keywords": ["partner"], "font_awesome_class": "fas fa-handshake"},
    {"name": "Промокод", "icon_code": "promo", "category": "partner", "keywords": ["promo"], "font_awesome_class": "fas fa-ticket-alt"},
    {"name": "Реферальная ссылка", "icon_code": "referral", "category": "partner", "keywords": ["referral"], "font_awesome_class": "fas fa-users"},
    {"name": "Кешбэк", "icon_code": "cashback", "category": "partner", "keywords": ["cashback"], "font_awesome_class": "fas fa-percent"},

    # ========== КОНТАКТЫ ==========
    {"name": "Email", "icon_code": "email", "category": "contact", "keywords": ["email", "mail"], "font_awesome_class": "fas fa-envelope"},
    {"name": "Телефон", "icon_code": "phone", "category": "contact", "keywords": ["phone", "call"], "font_awesome_class": "fas fa-phone"},
    {"name": "Адрес", "icon_code": "address", "category": "contact", "keywords": ["address", "map"], "font_awesome_class": "fas fa-map-marker-alt"},

    # ========== РАЗНОЕ ==========
    {"name": "Обычная ссылка", "icon_code": "link", "category": "other", "keywords": ["link"], "font_awesome_class": "fas fa-link"},
    {"name": "Текстовая заметка", "icon_code": "text", "category": "other", "keywords": ["text"], "font_awesome_class": "fas fa-file-alt"},
    {"name": "Глобус", "icon_code": "globe", "category": "other", "keywords": ["globe", "website"], "font_awesome_class": "fas fa-globe"},
    {"name": "Звезда", "icon_code": "star", "category": "other", "keywords": ["star"], "font_awesome_class": "fas fa-star"},
    {"name": "Сердце", "icon_code": "heart", "category": "other", "keywords": ["heart"], "font_awesome_class": "fas fa-heart"},
    {"name": "Огонь", "icon_code": "fire", "category": "other", "keywords": ["fire"], "font_awesome_class": "fas fa-fire"},
    {"name": "Корона", "icon_code": "crown", "category": "other", "keywords": ["crown"], "font_awesome_class": "fas fa-crown"},
    {"name": "Ракета", "icon_code": "rocket", "category": "other", "keywords": ["rocket"], "font_awesome_class": "fas fa-rocket"},
]

async def seed_icons():
    """Наполнение таблицы иконок"""
    # Убираем +asyncpg если есть
    db_url = DATABASE_URL.replace('+asyncpg', '')
    conn = await asyncpg.connect(db_url)

    try:
        # Очищаем таблицу
        await conn.execute("TRUNCATE icons RESTART IDENTITY CASCADE;")
        logger.info("Таблица icons очищена")

        # Вставляем иконки
        for icon in ICONS:
            await conn.execute("""
                               INSERT INTO icons (name, icon_code, category, keywords, font_awesome_class, is_active, sort_order)
                               VALUES ($1, $2, $3, $4, $5, true, 0)
                               """, icon["name"], icon["icon_code"], icon["category"], icon["keywords"], icon["font_awesome_class"])

        # Проверяем количество
        count = await conn.fetchval("SELECT COUNT(*) FROM icons")
        logger.info(f"✅ Добавлено {count} иконок в базу данных")

        # Покажем по категориям
        categories = await conn.fetch("""
                                      SELECT category, COUNT(*) as cnt
                                      FROM icons
                                      GROUP BY category
                                      ORDER BY cnt DESC
                                      """)

        logger.info("📊 Иконки по категориям:")
        for cat in categories:
            logger.info(f"  • {cat['category']}: {cat['cnt']} шт.")

    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(seed_icons())