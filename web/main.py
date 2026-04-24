#D:\aRabota\TelegaBoom\030_mylinkspace\web\main.py




import logging
import mimetypes  # ← ДОБАВЬ ЭТОТ ИМПОРТ
import os
import sys
from contextlib import asynccontextmanager
from urllib.parse import urlparse

import asyncpg
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi import Response
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
from starlette.responses import RedirectResponse
from telegram import Update

from bot.bankworld import COUNTRY_NAMES

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


# ==============ВРЕМЯНКА==========================================

# @app.get("/my-guide", response_class=HTMLResponse)
# async def read_guide(request: Request):
#     import os
#     from fastapi.responses import HTMLResponse
#
#     # --- ВРЕМЕННО ЗАКОММЕНТИРУЙ ВСЮ ПРОВЕРКУ КУК И БАЗЫ ДАННЫХ ---
#     # auth_token = request.cookies.get("guide_auth_token")
#     # ... (и весь код с asyncpg тоже можешь пока не трогать) ...
#
#     # 3. Всё ок! Просто отдаем страницу гайда для разработки
#     template_path = "web/templates/guide/guide_content.html"
#
#     if not os.path.exists(template_path):
#         return HTMLResponse(content=f"<h1>Файл не найден по пути: {template_path}</h1>", status_code=404)
#
#     with open(template_path, "r", encoding="utf-8") as f:
#         html_content = f.read()
#
#     return HTMLResponse(content=html_content)

# ========================================================

@app.get("/my-guide", response_class=HTMLResponse)
async def read_guide(request: Request):
    from core.config import DATABASE_URL
    import asyncpg
    from fastapi.responses import HTMLResponse, RedirectResponse
    import os

    # 1. Достаем нашу куку "абонемент"
    auth_token = request.cookies.get("guide_auth_token")

    if not auth_token:
        # Нет куки? Отправляем на лендинг
        return RedirectResponse(url="/guide")

    # Очищаем URL (стандарт для работы с asyncpg напрямую)
    db_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    conn = await asyncpg.connect(db_url)
    try:
        # 2. Проверяем в базе, есть ли такая сессия
        user_check = await conn.fetchrow(
            "SELECT customer_email FROM public.paid_sessions WHERE session_id = $1 LIMIT 1",
            auth_token
        )

        if not user_check:
            # Кука левая или сессия удалена
            response = RedirectResponse(url="/guide")
            response.delete_cookie("guide_auth_token")
            return response

        # 3. Всё ок! Отдаем страницу гайда
        # Указываем правильный путь с учетом подпапки guide
        template_path = "web/templates/guide/guide_content.html"

        if not os.path.exists(template_path):
            return HTMLResponse(content="<h1>Файл гайда не найден</h1>", status_code=404)

        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        return HTMLResponse(content=html_content)

    except Exception as e:
        print(f"!!! Ошибка доступа к гайду: {e}")
        return HTMLResponse(content="Ошибка сервера", status_code=500)
    finally:
        await conn.close()
        

@app.get("/auth/verify")
async def verify_magic_link(token: str):
    from core.config import DATABASE_URL
    from datetime import datetime
    import asyncpg
    from fastapi.responses import RedirectResponse
    import logging

    logger = logging.getLogger("uvicorn")

    # Очистка URL для asyncpg
    db_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    conn = await asyncpg.connect(db_url)
    try:
        # 1. Проверяем токен.
        # Если прошло более 15 минут с момента генерации, база ничего не вернет ($2 = текущее время)
        query = """
            SELECT session_id, customer_email
            FROM public.paid_sessions
            WHERE magic_link_token = $1 AND token_expires_at > $2
        """
        user_record = await conn.fetchrow(query, token, datetime.utcnow())

        # 2. Если токен не найден или время (15 мин) уже вышло
        if not user_record:
            logger.warning(f"⚠️ Токен невалиден или протух: {token}")
            return RedirectResponse(url="/guide?error=link_invalid_or_used")

        # 3. Токен верный. Готовим переход в гайд
        response = RedirectResponse(url="/my-guide", status_code=303)

        # 4. Устанавливаем куку-абонемент
        response.set_cookie(
            key="guide_auth_token",
            value=str(user_record['session_id']),
            httponly=True,
            max_age=31536000,
            samesite="lax",
            secure=False
        )

        # 5. Одноразовость отключена
        # Мы НЕ зануляем magic_link_token.
        # Теперь ссылку можно нажать 2, 3 или 10 раз, пока не истечет время в колонке token_expires_at.
        # await conn.execute(
        #     "UPDATE public.paid_sessions SET magic_link_token = NULL WHERE session_id = $1",
        #     user_record['session_id']
        # )

        logger.info(f"✅ Вход выполнен (ссылка активна до истечения времени): {user_record['customer_email']}")
        return response

    except Exception as e:
        print(f"!!! ОШИБКА В VERIFY: {e}")
        return RedirectResponse(url="/guide?error=server_error")
    finally:
        await conn.close()
        
        
        
class AuthEmail(BaseModel):
    email: EmailStr

@app.post("/auth/request-magic-link")
async def request_magic_link(payload: AuthEmail):
    from core.config import DATABASE_URL, SMTP_USER, SMTP_PASSWORD, SMTP_SERVER, SMTP_PORT
    import secrets
    from datetime import datetime, timedelta
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.header import Header
    import asyncpg
    from fastapi import HTTPException

    target_email = payload.email.strip().lower()
    clean_db_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    conn = await asyncpg.connect(clean_db_url, statement_cache_size=0)
    try:
        # 1. Получаем данные пользователя и статистику запросов
        user_record = await conn.fetchrow(
            """
            SELECT customer_email, login_attempts_today, last_login_request
            FROM public.paid_sessions
            WHERE customer_email ILIKE $1 LIMIT 1
            """,
            target_email
        )
        
        if not user_record:
            raise HTTPException(status_code=404, detail="Email не найден в базе покупателей")

        db_email = user_record['customer_email']
        current_attempts = user_record['login_attempts_today'] or 0
        last_request = user_record['last_login_request']
        now = datetime.now() # Для сравнения дат используем локальное время сервера

        # 2. ПРОВЕРКА ЛИМИТА
        # Если последний запрос был в другой день — сбрасываем счетчик
        if last_request and last_request.date() < now.date():
            current_attempts = 0

        # Если попыток уже 2 или больше — блокируем
        if current_attempts >= 2:
            logger.warning(f"🚫 Лимит исчерпан для {db_email}")
            raise HTTPException(
                status_code=429,
                detail="Лимит исчерпан. Можно запрашивать ссылку не более 2 раз в сутки."
            )

        # 3. ГЕНЕРАЦИЯ ДАННЫХ
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(minutes=15)
        new_attempts = current_attempts + 1

        # 4. ОБНОВЛЯЕМ БАЗУ (токен + инкремент счетчика)
        await conn.execute(
            """
            UPDATE public.paid_sessions
            SET magic_link_token = $1,
                token_expires_at = $2,
                login_attempts_today = $3,
                last_login_request = $4
            WHERE customer_email = $5
            """,
            token, expires_at, new_attempts, now, db_email
        )

        # 5. ОТПРАВКА ПИСЬМА
        magic_link = f"https://botolink.pro/auth/verify?token={token}"
        
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = db_email
        msg['Subject'] = Header("Ваш доступ к Гайду по Нячангу", 'utf-8').encode()

        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #635bff;">Привет!</h2>
                <p>Вы запросили доступ к гайду. Нажмите на кнопку ниже:</p>
                <a href="{magic_link}" style="display: inline-block; padding: 12px 25px; background: #635bff; color: #fff; text-decoration: none; border-radius: 8px;">Войти в Гайд</a>
                <p style="margin-top: 20px; font-size: 13px; color: #666;">
                    ⚠️ Ссылка <b>многоразовая</b> в течение 15 минут, но запрашивать новое письмо можно не более 2 раз в сутки.
                </p>
            </body>
        </html>
        """
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"📧 Письмо #{new_attempts} отправлено на {db_email}")
        return {"status": "success"}

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"❌ Ошибка лимитов/отправки: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка сервера")
    finally:
        await conn.close()
        
        
        
        
        
        
# ПУТИ К СТАТИКЕ
current_dir = os.path.dirname(os.path.realpath(__file__))

# Монтируем /static для картинок и /templates для CSS/JS внутри папок тем
app.mount("/static", StaticFiles(directory=os.path.join(current_dir, "static")), name="static")
app.mount("/templates", StaticFiles(directory=os.path.join(current_dir, "templates")), name="templates_static")

templates = Jinja2Templates(directory=os.path.join(current_dir, "templates"))

@app.get("/favicon.ico", include_in_schema=False)
async def get_favicon():
    # Собираем путь: web / static / favicon / favicon.ico
    favicon_path = os.path.join(current_dir, "static", "favicon", "favicon.ico")
    
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path, media_type="image/x-icon")
    
    # Если основного нет, пробуем отдать png гайда
    guide_favicon = os.path.join(current_dir, "static", "favicon", "favicon_guide.png")
    if os.path.exists(guide_favicon):
        return FileResponse(guide_favicon, media_type="image/png")
        
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




@app.post("/stripe-webhook")
async def stripe_webhook(request: Request):
    from core.config import STRIPE_WEBHOOK_SECRET, STRIPE_SECRET_KEY, DATABASE_URL
    import stripe
    import asyncpg
    from datetime import datetime

    logger.info("🔄 [WEBHOOK] Получен запрос на /stripe-webhook")
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    stripe.api_key = STRIPE_SECRET_KEY

    if not sig_header:
        logger.warning("⚠️ [WEBHOOK] Отсутствует stripe-signature в заголовках")
        return Response(status_code=400)

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        logger.info(f"📦 [WEBHOOK] Событие получено: {event['type']} | ID: {event['id']}")
    except Exception as e:
        logger.error(f"❌ [WEBHOOK] Ошибка подписи: {e}")
        return Response(content=str(e), status_code=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        logger.info(f"💰 [WEBHOOK] Обработка completed сессии: {session.get('id')}")
        
        customer_email = session.get("customer_details", {}).get("email")
        if customer_email:
            customer_email = customer_email.lower()
            logger.info(f"📧 [WEBHOOK] Email клиента: {customer_email}")
        else:
            logger.warning(f"⚠️ [WEBHOOK] Email отсутствует в сессии {session.get('id')}")
        
        user_id_str = session.get("client_reference_id")
        logger.info(f"🆔 [WEBHOOK] client_reference_id: {user_id_str}")
        
        session_id = session.get("id")
        payment_status = session.get("payment_status")
        logger.info(f"💳 [WEBHOOK] Статус оплаты: {payment_status}")

        try:
            # Чистим URL для asyncpg
            clean_db_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
            logger.info(f"🗄️ [WEBHOOK] Подключение к БД: {clean_db_url[:50]}...")
            
            conn = await asyncpg.connect(clean_db_url)
            logger.info("✅ [WEBHOOK] Подключение к БД успешно")
            
            # 1. Обновляем таблицу users (если есть user_id)
            if user_id_str and user_id_str.isdigit():
                user_id = int(user_id_str)
                logger.info(f"👤 [WEBHOOK] Обновляем users для id={user_id}, email={customer_email}")
                result = await conn.execute(
                    "UPDATE users SET email = $1 WHERE id = $2",
                    customer_email, user_id
                )
                logger.info(f"📊 [WEBHOOK] users обновлено: {result}")
            else:
                logger.info(f"ℹ️ [WEBHOOK] user_id невалидный или отсутствует: '{user_id_str}', пропускаем users")
            
            # 2. Создаем запись в paid_sessions (UPSERT)
            user_id_value = int(user_id_str) if user_id_str and user_id_str.isdigit() else None
            logger.info(f"💾 [WEBHOOK] Вставляем в paid_sessions: session_id={session_id}, user_id={user_id_value}, email={customer_email}")
            
            await conn.execute("""
                INSERT INTO paid_sessions (session_id, user_id, customer_email, download_count, created_at)
                VALUES ($1, $2, $3, 0, $4)
                ON CONFLICT (session_id) DO UPDATE SET
                    user_id = EXCLUDED.user_id,
                    customer_email = EXCLUDED.customer_email,
                    updated_at = EXCLUDED.created_at
            """, session_id, user_id_value, customer_email, datetime.utcnow())
            
            # Проверяем, что запись создалась
            check = await conn.fetchrow(
                "SELECT session_id, customer_email FROM paid_sessions WHERE session_id = $1",
                session_id
            )
            if check:
                logger.info(f"✅ [WEBHOOK] Запись подтверждена: {check['session_id']} -> {check['customer_email']}")
            else:
                logger.error(f"❌ [WEBHOOK] Не удалось проверить создание записи!")
            
            await conn.close()
            logger.info(f"🎉 [WEBHOOK] УСПЕХ! Доступ создан для {customer_email} с session_id={session_id}")
            
        except Exception as db_err:
            logger.error(f"❌ [WEBHOOK DB ERROR] {type(db_err).__name__}: {db_err}")
            import traceback
            logger.error(f"📋 [WEBHOOK TRACEBACK]: {traceback.format_exc()}")
            # Не возвращаем ошибку Stripe, чтобы он не переотправлял

    else:
        logger.info(f"ℹ️ [WEBHOOK] Игнорируем событие типа: {event['type']}")

    logger.info("🏁 [WEBHOOK] Завершение обработки")
    return Response(status_code=200)




@app.get("/success", response_class=HTMLResponse)
async def payment_success_page(request: Request, session_id: str = None):
    from core.config import STRIPE_SECRET_KEY, DATABASE_URL
    from core.config import SMTP_USER, SMTP_PASSWORD, SMTP_SERVER, SMTP_PORT
    import stripe
    import asyncpg
    import secrets
    from datetime import datetime, timedelta
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.header import Header

    if not session_id:
        return HTMLResponse("<h1>Ошибка: Нет ID сессии</h1>", status_code=400)

    try:
        stripe.api_key = STRIPE_SECRET_KEY
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == "paid":
            email = session.customer_details.email if session.customer_details else None
            
            if not email:
                return HTMLResponse("<h1>Ошибка: Email не получен</h1>", status_code=400)
            
            # ========== ФУНКЦИЯ ДЛЯ ОПРЕДЕЛЕНИЯ ПОЧТОВОГО СЕРВИСА ==========
            def get_mail_link_and_icon(email):
                domain = email.split('@')[-1].lower()
                
                mail_info = {
                    # Google
                    'gmail.com': {'url': 'https://mail.google.com', 'icon': '📧', 'name': 'Gmail'},
                    
                    # Яндекс
                    'yandex.ru': {'url': 'https://mail.yandex.ru', 'icon': '📬', 'name': 'Яндекс Почта'},
                    'ya.ru': {'url': 'https://mail.yandex.ru', 'icon': '📬', 'name': 'Яндекс Почта'},
                    
                    # Mail.ru
                    'mail.ru': {'url': 'https://mail.ru', 'icon': '📫', 'name': 'Mail.ru'},
                    'bk.ru': {'url': 'https://mail.ru', 'icon': '📫', 'name': 'Mail.ru'},
                    'list.ru': {'url': 'https://mail.ru', 'icon': '📫', 'name': 'Mail.ru'},
                    'inbox.ru': {'url': 'https://mail.ru', 'icon': '📫', 'name': 'Mail.ru'},
                    
                    # Microsoft
                    'outlook.com': {'url': 'https://outlook.live.com', 'icon': '📧', 'name': 'Outlook'},
                    'hotmail.com': {'url': 'https://outlook.live.com', 'icon': '📧', 'name': 'Outlook'},
                    'live.com': {'url': 'https://outlook.live.com', 'icon': '📧', 'name': 'Outlook'},
                    'live.ru': {'url': 'https://outlook.live.com', 'icon': '📧', 'name': 'Outlook'},
                    
                    # Yahoo
                    'yahoo.com': {'url': 'https://mail.yahoo.com', 'icon': '📨', 'name': 'Yahoo Mail'},
                    'yahoo.co.uk': {'url': 'https://mail.yahoo.com', 'icon': '📨', 'name': 'Yahoo Mail'},
                    
                    # Rambler
                    'rambler.ru': {'url': 'https://mail.rambler.ru', 'icon': '📭', 'name': 'Rambler'},
                    
                    # Apple
                    'icloud.com': {'url': 'https://www.icloud.com/mail', 'icon': '🍎', 'name': 'iCloud'},
                    'me.com': {'url': 'https://www.icloud.com/mail', 'icon': '🍎', 'name': 'iCloud'},
                    'mac.com': {'url': 'https://www.icloud.com/mail', 'icon': '🍎', 'name': 'iCloud'},
                    
                    # ProtonMail
                    'protonmail.com': {'url': 'https://mail.proton.me', 'icon': '🔒', 'name': 'ProtonMail'},
                    'proton.me': {'url': 'https://mail.proton.me', 'icon': '🔒', 'name': 'ProtonMail'},
                    
                    # AOL
                    'aol.com': {'url': 'https://mail.aol.com', 'icon': '📧', 'name': 'AOL Mail'},
                    
                    # Seznam (Чехия)
                    'seznam.cz': {'url': 'https://email.seznam.cz', 'icon': '📧', 'name': 'Seznam Email'},
                    
                    # WP (Польша)
                    'wp.pl': {'url': 'https://poczta.wp.pl', 'icon': '📧', 'name': 'WP Poczta'},
                    
                    # Ukr.net (Украина)
                    'ukr.net': {'url': 'https://mail.ukr.net', 'icon': '📧', 'name': 'Ukr.net'},
                    
                    # GMX
                    'gmx.de': {'url': 'https://www.gmx.net', 'icon': '📧', 'name': 'GMX'},
                    'gmx.com': {'url': 'https://www.gmx.com', 'icon': '📧', 'name': 'GMX'},
                    
                    # Zoho
                    'zoho.com': {'url': 'https://mail.zoho.com', 'icon': '📧', 'name': 'Zoho Mail'},
                    
                    # Mail.com
                    'mail.com': {'url': 'https://www.mail.com', 'icon': '📧', 'name': 'Mail.com'},
                    
                    # Tutanota
                    'tutanota.com': {'url': 'https://mail.tutanota.com', 'icon': '🔒', 'name': 'Tutanota'},
                    'tuta.com': {'url': 'https://mail.tutanota.com', 'icon': '🔒', 'name': 'Tutanota'},
                    
                    # FastMail
                    'fastmail.com': {'url': 'https://www.fastmail.com', 'icon': '⚡', 'name': 'FastMail'},
                    'fastmail.fm': {'url': 'https://www.fastmail.com', 'icon': '⚡', 'name': 'FastMail'},
                }
                
                for key, info in mail_info.items():
                    if key in domain:
                        return info
                
                # Если почтовик не найден — ведём на лендинг
                return {'url': '/guide', 'icon': '🔐', 'name': 'лендинг'}
            
            mail_info = get_mail_link_and_icon(email)
            mail_url = mail_info['url']
            mail_icon = mail_info['icon']
            mail_name = mail_info['name']
            # ==================================================================
            
            clean_db_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
            conn = await asyncpg.connect(clean_db_url)
            
            try:
                token = secrets.token_urlsafe(32)
                expires_at = datetime.utcnow() + timedelta(minutes=15)
                
                await conn.execute("""
                    INSERT INTO paid_sessions (session_id, customer_email, magic_link_token, token_expires_at, download_count, created_at)
                    VALUES ($1, $2, $3, $4, 0, $5)
                """, session_id, email, token, expires_at, datetime.utcnow())
                
                logger.info(f"✅ [SUCCESS] Создана запись для {email}")
                
                magic_link = f"https://botolink.pro/auth/verify?token={token}"
                
                # ========== ПИСЬМО ==========
                msg = MIMEMultipart()
                msg['From'] = SMTP_USER
                msg['To'] = email
                msg['Subject'] = Header("Ваш доступ к Гайду по Нячангу", 'utf-8').encode()
                
                html_body = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                </head>
                <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 550px; margin: 0 auto; padding: 20px;">
                    
                    <div style="text-align: center; padding: 20px 0 10px;">
                        <div style="font-size: 48px;">📘</div>
                        <h1 style="color: #635bff; margin: 10px 0 5px;">Ваш доступ к гайду</h1>
                        <p style="color: #666;">по Нячангу — активен!</p>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{magic_link}" style="display: inline-block; padding: 16px 32px; background: #635bff; color: white; text-decoration: none; border-radius: 12px; font-weight: bold; font-size: 18px;">
                            🚀 ОТКРЫТЬ ГАЙД
                        </a>
                        <p style="font-size: 12px; color: #999; margin-top: 10px;">
                            ⏰ Ссылка действительна 15 минут
                        </p>
                    </div>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 25px 0;">
                    
                    <div style="background: #f8f9ff; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
                        <p style="margin: 0 0 10px;"><strong>📖 Как пользоваться?</strong></p>
                        <p style="margin: 0 0 5px;">1. Нажмите на кнопку выше — откроется гайд</p>
                        <p style="margin: 0 0 5px;">2. Добавьте страницу в <strong>закладки браузера</strong></p>
                        <p style="margin: 0;">3. В следующий раз гайд откроется сразу</p>
                    </div>
                    
                    <div style="background: #fff3e0; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
                        <p style="margin: 0 0 10px;"><strong>🔐 Если потеряете ссылку</strong></p>
                        <p style="margin: 0;">Зайдите на <a href="https://botolink.pro/guide" style="color: #635bff;">botolink.pro/guide</a>, введите ваш email <strong>{email}</strong> — мы пришлём новую ссылку (до 2 раз в день).</p>
                    </div>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 25px 0;">
                    
                    <div style="text-align: center; font-size: 12px; color: #aaa;">
                        <p>Вопросы? Пишите в Telegram: <a href="https://t.me/botolinkprobot" style="color: #635bff;">@botolinkprobot</a></p>
                    </div>
                </body>
                </html>
                """
                msg.attach(MIMEText(html_body, 'html', 'utf-8'))
                
                with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                    server.send_message(msg)
                
                logger.info(f"📧 Письмо отправлено на {email}")
                
            finally:
                await conn.close()
            
            # ========== СТРАНИЦА УСПЕХА С УМНОЙ КНОПКОЙ ==========
            return HTMLResponse(content=f"""
            <div style="text-align: center; margin-top: 100px; font-family: sans-serif; padding: 20px;">
                <div style="font-size: 60px;">🎉</div>
                <h1 style="color: #111;">Оплата прошла успешно!</h1>
                <p style="color: #555; font-size: 18px;">Доступ активирован для <strong>{email}</strong>.</p>
                
                <div style="background: #e8f5e9; border-radius: 12px; padding: 20px; margin: 30px auto; max-width: 450px; text-align: left;">
                    <p style="margin: 0 0 10px 0; font-size: 18px; font-weight: bold;">📧 Что дальше?</p>
                    <p style="margin: 0 0 8px 0;">1️⃣ Мы отправили письмо на <strong>{email}</strong></p>
                    <p style="margin: 0 0 8px 0;">2️⃣ Нажмите на кнопку <strong style="color: #635bff;">«ОТКРЫТЬ ГАЙД»</strong> внутри письма</p>
                    <p style="margin: 0;">3️⃣ Сохраните гайд в закладки</p>
                </div>
                
                <a href="{mail_url}" target="_blank" style="display: inline-block; margin-top: 10px; padding: 14px 28px; background: #635bff; color: white; text-decoration: none; border-radius: 10px; font-weight: bold; font-size: 16px;">
                    {mail_icon} ОТКРЫТЬ {mail_name}
                </a>
                <p style="color: #666; font-size: 12px; margin-top: 8px;">
                    Письмо от <strong>dkvkabakov@gmail.com</strong><br>
                    Если не видите — проверьте папку <strong>Спам</strong>
                </p>
                
                <div style="background: #fff3e0; border-radius: 12px; padding: 15px; margin: 25px auto; max-width: 450px; text-align: left;">
                    <p style="margin: 0 0 5px 0;">🔐 <strong>Не нашли письмо?</strong></p>
                    <p style="margin: 0;">• Запросите новую ссылку на <a href="/guide" style="color: #635bff;">botolink.pro/guide</a></p>
                </div>
            </div>
            """)
        
        return HTMLResponse("<h1>Оплата еще обрабатывается...</h1>")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в /success: {e}")
        import traceback
        traceback.print_exc()
        return HTMLResponse(f"<h1>Ошибка</h1><p>{str(e)}</p>", status_code=500)
    
    
    

    
# ========== ОСТАЛЬНЫЕ ЭНДПОИНТЫ ==========
# ========== СИСТЕМНЫЕ РОУТЫ И ГАЙД ==========

@app.get("/")
@app.head("/")  # Добавь это
async def root():
    # Редирект на главного бота при заходе на корень домена
    return RedirectResponse(url="https://t.me/botolinkprobot")


@app.get("/get-my-guide-2026")
async def download_guide(key: str = None, session_id: str = None):
    # Импортируем настроенные переменные из нашего конфига
    from core.config import DOWNLOAD_SECRET, DATABASE_URL, GUIDE_PATH
    import os
    import asyncpg

    # 1. Проверка секретного ключа (теперь DOWNLOAD_SECRET берется из config.py)
    if key != DOWNLOAD_SECRET:
        logger.warning(f"⚠️ Попытка скачать гайд с неверным ключом: {key}")
        raise HTTPException(status_code=403, detail="Доступ запрещен. Неверный ключ.")
    
    # 2. Проверка сессии в базе
    if not session_id:
        raise HTTPException(status_code=403, detail="ID сессии обязателен.")

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        row = await conn.fetchrow("SELECT session_id FROM paid_sessions WHERE session_id = $1", session_id)
        if not row:
            logger.warning(f"⚠️ Попытка скачать без оплаты или записи в БД: {session_id}")
            raise HTTPException(status_code=403, detail="Оплата не подтверждена.")
    finally:
        await conn.close()
    
    # 3. Проверка наличия файла
    if not os.path.exists(GUIDE_PATH):
        logger.error(f"❌ Файл гайда не найден по пути: {GUIDE_PATH}")
        raise HTTPException(status_code=404, detail="Файл временно недоступен на сервере.")

    # 4. Отправка PDF
    return FileResponse(
        path=GUIDE_PATH,
        filename="guide_vnt_2026.pdf",
        media_type="application/pdf"
    )

@app.get("/easy", include_in_schema=False)
async def redirect_to_easy_bot():
    # Быстрый переход на вспомогательного бота
    return RedirectResponse(url="https://t.me/easyVietnamBot", status_code=307)




@app.get("/set_webhook")
async def set_webhook():
    from core.config import APP_URL, BOT_TOKEN
    
    base_url = APP_URL.strip().rstrip('/')
    bot_token = BOT_TOKEN.strip()
    
    if not base_url or not bot_token:
        return {
            "status": "error",
            "message": "APP_URL или BOT_TOKEN не установлены!",
            "debug": {
                "base_url": base_url,
                "has_token": bool(bot_token)
            }
        }
    
    webhook_url = f"{base_url}/webhook"
    tg_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    
    payload = {
        "url": webhook_url,
        "drop_pending_updates": True,
        "allowed_updates": ["message", "callback_query", "edited_message"]
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(tg_url, json=payload, timeout=10.0)
            result = response.json()
            
            return {
                "status": "ok" if result.get("ok") else "failed",
                "webhook_url_sent": webhook_url,
                "telegram_reply": result,
            }
        except Exception as e:
            logger.error(f"❌ Ошибка при установке вебхука: {e}")
            return {"status": "exception", "error": str(e)}
        
        
        
        




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




@app.get("/create-checkout")
async def create_checkout(user_id: str):
    # Импортируем готовые ключи, которые config.py уже выбрал за нас (тест или лайв)
    from core.config import STRIPE_SECRET_KEY, GUIDE_PRICE_ID
    import stripe
    
    try:
        # Устанавливаем ключ, который мы вытянули из нашего конфига
        stripe.api_key = STRIPE_SECRET_KEY
        
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': GUIDE_PRICE_ID, # Здесь теперь автоматически будет нужный ID
                'quantity': 1,
            }],
            mode='payment',
            client_reference_id=user_id,
            success_url='https://botolink.pro/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='https://botolink.pro/guide',
        )
        
        return RedirectResponse(url=session.url)
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания сессии: {e}")
        return HTMLResponse(content=f"<h1>Ошибка оплаты: {e}</h1>", status_code=500)
    


# --- СИСТЕМНЫЕ ПУТИ (Вставлять строго перед @app.get("/{username}")) ---


    

@app.get("/guide", response_class=HTMLResponse, include_in_schema=False)
async def vietnam_guide_landing(request: Request):
    try:
        # Путь к лендингу гайда
        file_path = os.path.join(current_dir, "templates", "guide", "guide_landing.html")
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки лендинга: {e}")
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

        # 8. Универсальный возврат контекста
        context = {
            "request": request,
            "user": user_data,
            "page": page_data,
            "links": processed_links,
            "categories": categories,
            "COUNTRY_NAMES": COUNTRY_NAMES,
            "template_path": folder
        }

        # Этот блок проверяет версию "на лету" и не дает серверу упасть
        try:
            # Пытаемся вызвать по-новому (как хочет Render)
            return templates.TemplateResponse(
                request=request,
                name=str(template_file),
                context=context
            )
        except TypeError:
            # Если падает (как на твоем localhost), вызываем по-старому
            return templates.TemplateResponse(
                str(template_file),
                context
            )

     
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"🔥 КРИТИЧЕСКАЯ ОШИБКА В user_page:\n{error_details}")
        
        # Выводим подробный traceback прямо в браузер для отладки
        return HTMLResponse(
            content=f"<h1>Ошибка сервера (500)</h1><pre>{error_details}</pre>",
            status_code=500
        )
    finally:
        if 'conn' in locals():
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