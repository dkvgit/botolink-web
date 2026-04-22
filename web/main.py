#D:\aRabota\TelegaBoom\030_mylinkspace\web\main.py




import logging
import mimetypes  # ← ДОБАВЬ ЭТОТ ИМПОРТ
import os
import sys
from contextlib import asynccontextmanager
from urllib.parse import urlparse
from telegram.request import HTTPXRequest
import asyncpg
import httpx
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from telegram import Update
from fastapi import HTTPException
from fastapi.responses import FileResponse
from bot.bankworld import COUNTRY_NAMES

# Путь должен быть от корня проекта, где запускается main.py
GUIDE_PATH = "app_data/Гайд_Нячанг_Вьетнам_2026_ДенисКабаков.pdf"
DOWNLOAD_SECRET = "vn2026_top_secret_access"


# Добавляем путь к корневой папке проекта

# Импортируем application из bot.main и сразу даем понятное имя
try:
    from bot.main import application as bot_app
    print("✅ Успешно импортирован bot_app")
except ImportError as e:
    print(f"--- КРИТИЧЕСКАЯ ОШИБКА ИМПОРТА: {e} ---")
    # Запасной вариант
    from bot.main import ptb_application as bot_app


# ========== НАСТРОЙКА ЛОГГЕРА ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)




# ========== ИМПОРТ БОТА ==========
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from bot.main import application as bot_app
    logger.info("✅ Бот успешно импортирован как bot_app")
except ImportError as e:
    logger.error(f"❌ Ошибка импорта бота: {e}")
    # Запасной вариант
    from bot.main import ptb_application as bot_app

load_dotenv()





    
    
# Принудительно регистрируем MIME-типы - ДОБАВЬ ЭТО СРАЗУ ПОСЛЕ ИМПОРТОВ!
mimetypes.add_type('image/jpeg', '.jpg')
mimetypes.add_type('image/jpeg', '.jpeg')
mimetypes.add_type('image/png', '.png')
mimetypes.add_type('image/gif', '.gif')
mimetypes.add_type('image/webp', '.webp')



# ========== НАСТРОЙКА БАЗЫ ДАННЫХ ==========
RAW_DB_URL = os.getenv("DATABASE_URL", "")

if RAW_DB_URL and "postgresql+asyncpg://" not in RAW_DB_URL:
    BOT_DATABASE_URL = RAW_DB_URL.replace("postgresql://", "postgresql+asyncpg://")
else:
    BOT_DATABASE_URL = RAW_DB_URL

DIRECT_DATABASE_URL = RAW_DB_URL.replace("postgresql+asyncpg://", "postgresql://")
DATABASE_URL = DIRECT_DATABASE_URL



@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio
    import bot.main as bot_module
    
    telegram_application = getattr(bot_module, 'bot_app', None) or getattr(bot_module, 'application', None)
    
    if not telegram_application:
        logger.error("❌ [CRITICAL] Не удалось найти объект бота (bot_app или application) в bot/main.py")
        raise RuntimeError("Bot application object not found")

    run_mode = os.getenv("RUN_MODE", "webhook").lower().strip()
    logger.info(f"🚀 [SYSTEM] Старт сервера. Режим бота: {run_mode.upper()}")

    try:
        # 1. Инициализация бота с 3 попытками (чтобы не падать по таймауту)
        for attempt in range(3):
            try:
                if not telegram_application.running:
                    await telegram_application.initialize()
                    await telegram_application.start()
                logger.info(f"✅ Бот успешно инициализирован (попытка {attempt + 1})")
                break
            except Exception as e:
                if "Timed out" in str(e) and attempt < 2:
                    logger.warning(f"⚠️ Попытка {attempt + 1} не удалась (таймаут), ждем 5 сек...")
                    await asyncio.sleep(5)
                    continue
                raise e

        # 2. Логика Webhook / Polling
        if run_mode == "polling":
            logger.info("📡 [LOCAL] Чистим вебхуки и включаем Polling...")
            await telegram_application.bot.delete_webhook(drop_pending_updates=True)
            if telegram_application.updater:
                await telegram_application.updater.start_polling(
                    allowed_updates=["message", "callback_query", "edited_message"],
                    drop_pending_updates=True
                )
            logger.info("✅ Бот на связи через Polling")
        
        else:
            app_url = os.getenv('APP_URL', '').strip().rstrip('/')
            if app_url:
                webhook_url = f"{app_url}/webhook"
                await telegram_application.bot.set_webhook(
                    url=webhook_url,
                    drop_pending_updates=True,
                    allowed_updates=["message", "callback_query", "edited_message"]
                )
                logger.info(f"✅ Webhook установлен на: {webhook_url}")
            else:
                logger.error("❌ APP_URL не задан! Бот в режиме Webhook не оживет.")

    except Exception as e:
        logger.error(f"❌ [CRITICAL] Ошибка старта: {e}", exc_info=True)

    yield

    # --- ЗДЕСЬ ВСЁ ВЫКЛЮЧАЕТСЯ ---
    logger.info("🚦 [SYSTEM] Глушим двигатель...")
    try:
        if run_mode == "polling" and telegram_application.updater and telegram_application.updater.running:
            await telegram_application.updater.stop()
            
        if telegram_application.running:
            await telegram_application.stop()
            await telegram_application.shutdown()
        logger.info("✅ [SYSTEM] Все процессы корректно завершены")
    except Exception as e:
        logger.error(f"❌ [ERROR] Ошибка при выключении: {e}")
        

# D:\aRabota\TelegaBoom\030_mylinkspace\web\main.py

app = FastAPI(lifespan=lifespan)

# ПУТИ К СТАТИКЕ
current_dir = os.path.dirname(os.path.realpath(__file__))

# Монтируем /static для картинок и /templates для CSS/JS внутри папок тем
app.mount("/static", StaticFiles(directory=os.path.join(current_dir, "static")), name="static")
app.mount("/templates", StaticFiles(directory=os.path.join(current_dir, "templates")), name="templates_static")

templates = Jinja2Templates(directory=os.path.join(current_dir, "templates"))

@app.get("/favicon.ico", include_in_schema=False)
async def get_favicon():
    favicon_path = os.path.join(current_dir, "static", "favicon", "favicon_guide.png")
    if os.path.exists(favicon_path):
        # Форсируем отдачу иконки
        return FileResponse(favicon_path, media_type="image/png")
    return Response(status_code=204)









# ========== WEBHOOK - ЭТО САМОЕ ГЛАВНОЕ! ==========
@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Прием и обработка обновлений от Telegram API"""
    # Динамически достаем бота, чтобы не было проблем с импортами
    import bot.main as bot_module
    telegram_application = getattr(bot_module, 'bot_app', None) or getattr(bot_module, 'application', None)

    try:
        # 1. Читаем данные от Telegram
        data = await request.json()
        
        # ЛОГ: Увидим сообщение в консоли Hugging Face
        logger.info(f"📥 [WEBHOOK] Новое сообщение: {data}")

        if not data:
            return Response(status_code=200)

        # 2. Проверяем, готов ли бот к работе
        if not telegram_application or not telegram_application.bot:
            logger.error("❌ [CRITICAL] Объект бота не найден или не инициализирован!")
            return Response(status_code=200)

        # 3. Превращаем JSON в объект Update и запускаем обработку
        update = Update.de_json(data, telegram_application.bot)
        
        # Это отправит сообщение в твои хендлеры (start и прочие)
        await telegram_application.process_update(update)
        
        return Response(status_code=200)
        
    except Exception as e:
        logger.error(f"❌ [WEBHOOK ERROR] Ошибка при обработке: {e}", exc_info=True)
        # Всегда возвращаем 200, чтобы Telegram не пытался слать это бесконечно
        return Response(status_code=200)
    
    
# ========== ОСТАЛЬНЫЕ ЭНДПОИНТЫ ==========
# ========== СИСТЕМНЫЕ РОУТЫ И ГАЙД ==========

@app.get("/")
async def root():
    # Редирект на главного бота при заходе на корень домена
    return RedirectResponse(url="https://t.me/botolinkprobot")


@app.get("/get-my-guide-2026")
async def download_guide(key: str = None):
    # Проверка секретного ключа из ссылки
    if key != DOWNLOAD_SECRET:
        logger.warning(f"⚠️ Попытка скачать гайд с неверным ключом: {key}")
        raise HTTPException(status_code=403, detail="Доступ запрещен. Неверный ключ.")
    
    # Проверка наличия файла на диске
    if not os.path.exists(GUIDE_PATH):
        logger.error(f"❌ Файл гайда не найден по пути: {GUIDE_PATH}")
        raise HTTPException(status_code=404, detail="Файл временно недоступен на сервере.")

    # Отправка PDF файла пользователю
    return FileResponse(
        path=GUIDE_PATH,
        filename="Гайд_Нячанг_Вьетнам_2026_ДенисКабаков.pdf",
        media_type="application/pdf"
    )


@app.get("/easy", include_in_schema=False)
async def redirect_to_easy_bot():
    # Быстрый переход на вспомогательного бота
    return RedirectResponse(url="https://t.me/easyVietnamBot", status_code=307)




@app.get("/set_webhook")
async def set_webhook():
    # # Подготавливаем базовый URL: убираем лишние пробелы и слэши в конце
    base_url = os.getenv('APP_URL', '').strip().rstrip('/')
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    
    # # Если URL не задан, пробуем вытянуть его из Railway домена (на всякий случай)
    if not base_url:
        base_url = f"https://{os.getenv('RAILWAY_STATIC_URL', '')}".rstrip('/')

    webhook_url = f"{base_url}/webhook"
    
    if not base_url or not bot_token:
        return {
            "status": "error",
            "message": "APP_URL или BOT_TOKEN не установлены в переменных окружения!",
            "debug": {
                "base_url": base_url,
                "has_token": bool(bot_token)
            }
        }
    
    # # Формируем запрос к Telegram API
    tg_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    
    # # Параметры для Telegram
    payload = {
        "url": webhook_url,
        "drop_pending_updates": True,  # Очистит очередь старых сообщений, чтобы бот не захлебнулся
        "allowed_updates": ["message", "callback_query", "edited_message"]
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # # Используем POST, так как передаем JSON с настройками
            response = await client.post(tg_url, json=payload, timeout=10.0)
            result = response.json()
            
            return {
                "status": "ok" if result.get("ok") else "failed",
                "webhook_url_sent": webhook_url,
                "telegram_reply": result,
                "note": "Если 'ok': true, значит всё четко. Проверяй бота!"
            }
        except Exception as e:
            logger.error(f"❌ Ошибка при установке вебхука: {e}")
            return {
                "status": "exception",
                "error": str(e),
                "tip": "Проверь соединение сервера с api.telegram.org"
            }
        
        
        
        
        




@app.get("/click/{link_id}")
async def track_click(link_id: int, request: Request):
    print(f"🔥 ПОЛУЧЕН КЛИК для link_id={link_id}")
    # Используем чистый URL без +asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        row = await conn.fetchrow("SELECT url, page_id FROM links WHERE id = $1", link_id)
        if not row:
            print(f"❌ Ссылка {link_id} не найдена")
            return HTMLResponse("Link not found", status_code=404)
        
        # 1. Увеличиваем счетчик
        await conn.execute("""
            UPDATE links
            SET click_count = COALESCE(click_count, 0) + 1
            WHERE id = $1
        """, link_id)
        
        # 2. Сохраняем детали
        await conn.execute("""
            INSERT INTO clicks (link_id, page_id, ip_address, user_agent, clicked_at)
            VALUES ($1, $2, $3, $4, NOW())
        """,
        link_id,
        row['page_id'],
        request.client.host,
        request.headers.get('user-agent', ''))
        
        target_url = row['url']
        if not target_url.startswith(('http://', 'https://')):
            target_url = f'https://{target_url}'
        
        return RedirectResponse(url=target_url)
    except Exception as e:
        print(f"🔥 Ошибка трекинга: {e}")
        return HTMLResponse(f"Error: {e}", status_code=500)
    finally:
        await conn.close()


@app.post("/click/{link_id}")
async def track_details_click(link_id: int, request: Request):
    # Метод для кнопок "Скопировать" или "Показать реквизиты"
    print(f"🔥 ПОЛУЧЕН КЛИК ПО РЕКВИЗИТАМ для link_id={link_id}")
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute("""
            UPDATE links
            SET click_count = COALESCE(click_count, 0) + 1
            WHERE id = $1
        """, link_id)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        await conn.close()




# Словари для иконок
BRAND_ICONS = {
    'instagram': 'fab fa-instagram',
    'tiktok': 'fab fa-tiktok',
    'youtube': 'fab fa-youtube',
    'twitch': 'fab fa-twitch',
    'telegram': 'fab fa-telegram',
    'vk': 'fab fa-vk',
    'twitter': 'fab fa-twitter',
    'facebook': 'fab fa-facebook',
    'github': 'fab fa-github',
    'whatsapp': 'fab fa-whatsapp',
    'snapchat': 'fab fa-snapchat',
    'spotify': 'fab fa-spotify',
    'discord': 'fab fa-discord',
    'linkedin': 'fab fa-linkedin',
    'pinterest': 'fab fa-pinterest',
    'reddit': 'fab fa-reddit',
    'medium': 'fab fa-medium',
    'tumblr': 'fab fa-tumblr',
    'flickr': 'fab fa-flickr',
    'behance': 'fab fa-behance',
    'dribbble': 'fab fa-dribbble',
    'soundcloud': 'fab fa-soundcloud',
    'bandcamp': 'fab fa-bandcamp',
    'etsy': 'fab fa-etsy',
    'amazon': 'fab fa-amazon',
    'apple': 'fab fa-apple',
    'google': 'fab fa-google',
    'microsoft': 'fab fa-microsoft',
    'steam': 'fab fa-steam',
    'epicgames': 'fab fa-epic-games',
    'xbox': 'fab fa-xbox',
    'playstation': 'fab fa-playstation',
    'nintendo': 'fab fa-nintendo-switch',
}

# Словарь соответствия link_type -> категория
LINK_TYPE_CATEGORY = {
    # Соцсети
    'instagram': 'social', 'youtube': 'social',
    'tiktok': 'social', 'vk': 'social', 'ok': 'social', 'facebook': 'social',
    'twitter': 'social', 'discord': 'social', 'twitch': 'social', 'rutube': 'social',
    'dzen': 'social', 'tenchat': 'social', 'snapchat': 'social', 'likee': 'social',
    'threads': 'social',
    
    # Мессенджеры
    'telegram': 'messengers', 'whatsapp': 'messengers', 'viber': 'messengers', 'signal': 'messengers',
    'zalo': 'messengers', 'facetime': 'messengers',
    'max': 'messengers',
    
    # Переводы
    'revolut': 'transfers', 'wise': 'transfers', 'paypal': 'transfers',
    'yoomoney': 'transfers', 'vkpay': 'transfers', 'monobank': 'transfers',
    'kaspi': 'transfers', 'payme': 'transfers', 'click': 'transfers',
    'tbcpay': 'transfers', 'idram': 'transfers',
    'cryptobot': 'transfers', 'sber': 'transfers',
    'tinkoff': 'transfers', 'bidv': 'transfers', 'korona': 'transfers',
    'westernunion': 'transfers', 'unistream': 'transfers', 'contact': 'transfers',
    'card': 'transfers', 'iban': 'transfers', 'arc': 'transfers', 'wire': 'transfers',
    'phone': 'transfers', 'account': 'transfers', 'non_res_vietnam': 'transfers',
    
    # Донат
    'patreon': 'donate', 'boosty': 'donate', 'donationalerts': 'donate',
    'kofi': 'donate', 'buymeacoffee': 'donate', 'cloudtips': 'donate',
    
    # Крипта (теперь всё летит в categories.crypto)
    'crypto': 'crypto',  # Наш новый универсальный тип для "Своей валюты"
    'binance': 'crypto',
    'bybit': 'crypto',
    'okx': 'crypto',
    'kucoin': 'crypto',
    'gateio': 'crypto',
    'huobi': 'crypto',
    'metamask': 'crypto',
    'trustwallet': 'crypto',
    'coinbase': 'crypto',
    'kraken': 'crypto',
    'bitget': 'crypto',  # Добавил на будущее
    'phantom': 'crypto',  # Добавил на будущее
    'tronlink': 'crypto',  # Добавил на будущее
    'exodus': 'crypto',  # Добавил на будущее
    'tonkeeper': 'crypto',  # Важно для TON веток
    
    # Магазины
    'ozon': 'shops', 'wildberries': 'shops', 'avito': 'shops', 'yandex_market': 'shops',
    'aliexpress': 'shops', 'kazanexpress': 'shops', 'amazon': 'shops', 'ebay': 'shops',
    'etsy': 'shops', 'shopify': 'shops',
    
    # Партнерки
    'partner': 'partner', 'promo': 'partner', 'referral': 'partner', 'cashback': 'partner',
    
    # Разное
    'standard': 'other', 'text': 'other'
}

STANDARD_ICONS = {
    'link': 'fas fa-link',
    'globe': 'fas fa-globe',
    'music': 'fas fa-music',
    'video': 'fas fa-video',
    'image': 'fas fa-image',
    'camera': 'fas fa-camera',
    'book': 'fas fa-book',
    'game': 'fas fa-gamepad',
    'code': 'fas fa-code',
    'chat': 'fas fa-comment',
    'mail': 'fas fa-envelope',
    'phone': 'fas fa-phone',
    'map': 'fas fa-map-marker-alt',
    'clock': 'fas fa-clock',
    'calendar': 'fas fa-calendar',
    'star': 'fas fa-star',
    'heart': 'fas fa-heart',
    'fire': 'fas fa-fire',
    'bolt': 'fas fa-bolt',
    'crown': 'fas fa-crown',
    'rocket': 'fas fa-rocket',
    'wallet': 'fas fa-wallet',
    'money': 'fas fa-money-bill',
    'bank': 'fas fa-university',
    'coin': 'fas fa-coins',
    'bitcoin': 'fab fa-bitcoin',
    'ethereum': 'fab fa-ethereum',
    'paypal': 'fab fa-paypal',
}

PAYMENT_KEYWORDS = {
    'btc': {'class': 'fab fa-bitcoin', 'emoji': '₿', 'keywords': ['btc', 'bitcoin']},
    'usdt': {'class': 'fas fa-dollar-sign', 'emoji': '💵', 'keywords': ['usdt', 'tether']},
    'eth': {'class': 'fab fa-ethereum', 'emoji': 'Ξ', 'keywords': ['eth', 'ethereum']},
    'card': {'class': 'fas fa-credit-card', 'emoji': '💳', 'keywords': ['card', 'карта', 'mastercard', 'visa']},
    'webmoney': {'class': 'fas fa-money-bill', 'emoji': 'WM', 'keywords': ['webmoney', 'wm']},
    'qiwi': {'class': 'fas fa-phone', 'emoji': '📱', 'keywords': ['qiwi', 'киви']},
    'yoomoney': {'class': 'fas fa-ruble-sign', 'emoji': '₽', 'keywords': ['yoomoney', 'юmoney', 'юмани']},
}


def get_icon_class(icon_name, link_type, url, pay_details):
    """Определяет класс иконки на основе всех доступных данных"""
    
    # Для финансовых ссылок
    if link_type == 'finance':
        pay_text = (pay_details or '').lower()
        
        # Ищем по ключевым словам
        for key, data in PAYMENT_KEYWORDS.items():
            if any(keyword in pay_text for keyword in data['keywords']):
                return {
                    'class': data['class'],  # Используем 'class' вместо 'icon_class'
                    'emoji': data['emoji'],
                    'is_payment': True
                }
        
        # По умолчанию карта
        return {
            'class': 'fas fa-credit-card',
            'emoji': '💳',
            'is_payment': True
        }
    
    # Для обычных ссылок
    if icon_name and isinstance(icon_name, str):
        icon_lower = icon_name.lower()
        
        # Проверяем брендовые иконки
        if icon_lower in BRAND_ICONS:
            return {'class': BRAND_ICONS[icon_lower]}
        
        # Проверяем стандартные иконки
        if icon_lower in STANDARD_ICONS:
            return {'class': STANDARD_ICONS[icon_lower]}
    
    # Если ничего не нашли, пробуем получить фавиконку
    if url and url != '#' and url.startswith(('http://', 'https://')):
        try:
            domain = urlparse(url).netloc
            return {
                'class': 'fas fa-link',
                'favicon': f"https://www.google.com/s2/favicons?domain={domain}&sz=32"
            }
        except:
            pass
    
    # Абсолютный дефолт
    return {'class': 'fas fa-link'}






# --- СИСТЕМНЫЕ ПУТИ (Вставлять строго перед @app.get("/{username}")) ---




@app.get("/guide", response_class=HTMLResponse, include_in_schema=False)
async def vietnam_guide_landing(request: Request):
    try:
        file_path = os.path.join(current_dir, "templates", "guide", "guide_landing.html")
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except Exception as e:
        return HTMLResponse(f"<h1>Ошибка: {e}</h1>")

# --- ТВОЯ ОСНОВНАЯ ФУНКЦИЯ (ОСТАВЛЯЙ КАК ЕСТЬ НИЖЕ) ---
@app.get("/{username}", response_class=HTMLResponse)
async def user_page(request: Request, username: str):
    # --- СИСТЕМНАЯ ЗАПЛАТКА ---
    # Если вдруг FastAPI проигнорировал верхний роут и прислал адрес сюда
    if username == "get-my-guide-2026":
        key = request.query_params.get("key")
        return await download_guide(key)
    # --------------------------

    conn = await asyncpg.connect(DATABASE_URL, statement_cache_size=0)
    try:
        # 1. Увеличиваем счетчик просмотров
        await conn.execute("UPDATE pages SET view_count = view_count + 1 WHERE username = $1", username)
        
        # 2. Получаем данные страницы
        row = await conn.fetchrow("""
            SELECT p.*, t.folder_name, t.name as t_name
            FROM pages p
            LEFT JOIN templates t ON p.template_id = t.id
            WHERE p.username = $1
        """, username)
        
        if not row:
            return HTMLResponse("<h1>Пользователь не найден</h1>", status_code=404)
        
        page_data = dict(row)
        folder = page_data.get('folder_name')
        
        # Строго проверяем путь к шаблону
        if folder and isinstance(folder, str):
            template_file = f"{folder}/{folder}_page.html"
        else:
            template_file = "page.html"
            
        # 3. Получаем ссылки
        links_records = await conn.fetch("""
            SELECT *
            FROM links
            WHERE page_id = $1
              AND is_active = true
            ORDER BY sort_order
        """, page_data['id'])
        
        # 4. Собираем иконки
        icon_names = list(set([r['icon'] for r in links_records if r['icon']]))
        icon_map = {}
        
        if icon_names:
            icon_rows = await conn.fetch("""
                SELECT icon_code, font_awesome_class
                FROM icons
                WHERE icon_code = ANY ($1::text[])
            """, icon_names)
            icon_map = {r['icon_code']: r['font_awesome_class'] for r in icon_rows}

        # 5. Обрабатываем ссылки
        processed_links = []
        import json
        
        for r in links_records:
            l_dict = dict(r)
            
            # Обработка JSON
            pay_details = l_dict.get('pay_details')
            if pay_details and isinstance(pay_details, str):
                try:
                    l_dict['pay_details'] = json.loads(pay_details)
                except Exception:
                    l_dict['pay_details'] = {}
            elif not isinstance(pay_details, (dict, list)):
                l_dict['pay_details'] = {}
            
            # ========== НОРМАЛИЗАЦИЯ ДАННЫХ ДЛЯ ШАБЛОНОВ ==========
            pd = l_dict.get('pay_details')
            if pd and isinstance(pd, dict):
                if 'wallet_address' in pd:
                    pd['address'] = pd.pop('wallet_address')
                if 'phone' in pd:
                    pd['phone_number'] = pd.pop('phone')
                l_dict['pay_details'] = pd
            # ====================================================
            
            # Обработка URL
            original_url = l_dict.get('url')
            link_type = str(l_dict.get('link_type', 'standard'))
            
            if original_url and original_url != "#":
                original_url = str(original_url).strip()
                crypto_types = ['crypto', 'binance', 'bybit', 'okx', 'metamask', 'kucoin']
                if link_type in crypto_types:
                    l_dict['url'] = original_url
                elif not original_url.startswith(('http://', 'https://')):
                    l_dict['url'] = f"https://{original_url}"
                else:
                    l_dict['url'] = original_url
            else:
                l_dict['url'] = "#"
            
            # Обработка иконок
            icon_name = l_dict.get('icon')
            if icon_name and icon_name in icon_map:
                l_dict['icon_class'] = icon_map[icon_name]
            else:
                if link_type in ['binance', 'bybit', 'okx', 'metamask', 'kucoin', 'crypto']:
                    l_dict['icon_class'] = 'fas fa-coins' if link_type == 'crypto' else BRAND_ICONS.get(link_type, 'fas fa-wallet')
                elif link_type == 'finance':
                    l_dict['icon_class'] = 'fas fa-credit-card'
                else:
                    l_dict['icon_class'] = 'fas fa-link'
            
            l_dict['is_external'] = str(l_dict['url']).startswith(('http://', 'https://'))
            processed_links.append(l_dict)
        
        # 6. Данные пользователя
        user_row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", page_data['user_id'])
        user_data = dict(user_row) if user_row else {}
        
        user_data['first_name'] = str(user_data.get('first_name') or page_data.get('username') or 'Пользователь')
        user_data['username'] = str(user_data.get('username') or '')

        # 7. Распределение по категориям
        categories = {k: [] for k in ['social', 'messengers', 'transfers', 'donate', 'crypto', 'shops', 'partner', 'other']}
        
        for link in processed_links:
            l_type = link.get('link_type')
            if not isinstance(l_type, str):
                l_type = str(l_type) if l_type is not None else 'other'
            
            is_transfer = any(l_type.startswith(p) for p in ['card_', 'iban_', 'phone_', 'account_', 'ach_', 'wire_'])
            
            if is_transfer:
                cat = 'transfers'
            else:
                cat = LINK_TYPE_CATEGORY.get(l_type, 'other')
            
            if cat in categories:
                categories[cat].append(link)
            else:
                categories['other'].append(link)

        # 8. Формирование контекста и возврат
        context = {
            "request": request,
            "user": user_data,
            "page": page_data,
            "links": processed_links,
            "categories": categories,
            "COUNTRY_NAMES": COUNTRY_NAMES,
            "template_path": folder
        }

        return templates.TemplateResponse(
            name=str(template_file),
            context=context
        )

    except Exception as e:
        print(f"🔥 КРИТИЧЕСКАЯ ОШИБКА В user_page: {e}")
        import traceback
        traceback.print_exc()
        return HTMLResponse(f"Ошибка сервера: {e}", status_code=500)
    finally:
        await conn.close()

    


if __name__ == "__main__":
    import uvicorn
    import os
    from dotenv import load_dotenv
    
    # Загружаем переменные, если запускаем этот файл напрямую
    load_dotenv()
    
    # Порт для локальных тестов или HF
    port = int(os.getenv("PORT", 8000))
    
    # Запускаем сам объект app.
    # В этом режиме бот включится через lifespan (через webhook)
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)