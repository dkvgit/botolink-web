#D:\aRabota\TelegaBoom\030_mylinkspace\web\main.py


import mimetypes  # ← ДОБАВЬ ЭТОТ ИМПОРТ
import os

from urllib.parse import urlparse
import asyncio
from contextlib import asynccontextmanager
import asyncpg
import uvicorn
from bot.bankworld import COUNTRY_NAMES
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from bot.main import application

from telegram import Update
load_dotenv()

# Принудительно регистрируем MIME-типы - ДОБАВЬ ЭТО СРАЗУ ПОСЛЕ ИМПОРТОВ!
mimetypes.add_type('image/jpeg', '.jpg')
mimetypes.add_type('image/jpeg', '.jpeg')
mimetypes.add_type('image/png', '.png')
mimetypes.add_type('image/gif', '.gif')
mimetypes.add_type('image/webp', '.webp')

RAW_DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres@localhost/botolinkpro")
DATABASE_URL = RAW_DB_URL.replace("+asyncpg", "")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # # Инициализируем компоненты бота, но НЕ запускаем polling,
    # # так как мы будем использовать Webhook.
    print("🤖 Инициализация Telegram бота для Webhook...")
    try:
        # Инициализируем внутренние механизмы (хранилища, настройки)
        await application.initialize()
        # Если используем Webhook, start() обычно не вызывает блокирующий polling
        await application.start()
        print("✅ Бот готов к приему обновлений через /webhook")
    except Exception as e:
        print(f"❌ Ошибка инициализации бота: {e}")
    
    yield
    
    # # Корректное завершение при выключении контейнера
    print("Shutting down...")
    await application.stop()
    await application.shutdown()


# // ВАЖНО: app создается строго ПОСЛЕ функции lifespan
app = FastAPI(lifespan=lifespan)



# web/main.py

@app.get("/set_webhook")
async def set_webhook():
    # Эта функция связывает твоего бота на Railway с серверами Telegram
    import os
    from bot.main import bot_app # Убедись, что импорт правильный исходя из твоей структуры
    
    # Берем адрес, по которому сейчас открывается твой сайт
    base_url = "https://botolink-web-production.up.railway.app"
    webhook_path = f"{base_url}/webhook"
    
    try:
        # Отправляем команду Телеграму: "Шли все сообщения на этот адрес"
        await bot_app.bot.set_webhook(url=webhook_path)
        return {"status": "ok", "message": f"Webhook успешно установлен на {webhook_path}"}
    except Exception as e:
        # Если что-то пошло не так (например, токен не подхватился)
        return {"status": "error", "message": str(e)}



@app.get("/click/{link_id}")
async def track_click(link_id: int, request: Request):
	print(f"🔥 ПОЛУЧЕН КЛИК для link_id={link_id}")
	conn = await asyncpg.connect(DATABASE_URL)
	try:
		# Получаем данные ссылки
		row = await conn.fetchrow("SELECT url, page_id FROM links WHERE id = $1", link_id)
		if not row:
			print(f"❌ Ссылка {link_id} не найдена")
			return {"error": "Link not found"}, 404
		
		# 👇 ИСПРАВЬТЕ ЭТУ СТРОКУ
		# 1. Увеличиваем счетчик в таблице links (с обработкой NULL)
		await conn.execute("""
                           UPDATE links
                           SET click_count = COALESCE(click_count, 0) + 1
                           WHERE id = $1
		                   """, link_id)
		
		# 2. Сохраняем детальную информацию в таблицу clicks (ЭТО НЕ ТРОГАЕМ)
		await conn.execute("""
                           INSERT INTO clicks
                               (link_id, page_id, ip_address, user_agent, clicked_at)
                           VALUES ($1, $2, $3, $4, NOW())
		                   """,
		                   link_id,
		                   row['page_id'],
		                   request.client.host,
		                   request.headers.get('user-agent', '')
		                   )
		
		print(f"✅ Клик для link_id={link_id} засчитан")
		
		# Перенаправляем
		target_url = row['url']
		if not target_url.startswith(('http://', 'https://')):
			target_url = f'https://{target_url}'
		
		return RedirectResponse(url=target_url)
	
	except Exception as e:
		print(f"🔥 Ошибка трекинга: {e}")
		return {"error": str(e)}, 500
	finally:
		await conn.close()


@app.post("/click/{link_id}")
async def track_details_click(link_id: int, request: Request):
	print(f"🔥 ПОЛУЧЕН КЛИК ПО РЕКВИЗИТАМ для link_id={link_id}")
	data = await request.json()  # получаем данные из body
	print(f"📦 Данные: {data}")
	
	conn = await asyncpg.connect(DATABASE_URL)
	try:
		# Обновляем счетчик
		await conn.execute("""
                           UPDATE links
                           SET click_count = COALESCE(click_count, 0) + 1
                           WHERE id = $1
		                   """, link_id)
		
		return {"status": "ok"}
	finally:
		await conn.close()


current_dir = os.path.dirname(os.path.realpath(__file__))

# Монтируем статические папки
app.mount("/templates", StaticFiles(directory=os.path.join(current_dir, "templates")), name="templates_static")
app.mount("/static", StaticFiles(directory=os.path.join(current_dir, "static")), name="static")

templates = Jinja2Templates(directory=os.path.join(current_dir, "templates"))

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
	'wechat': 'messengers', 'zalo': 'messengers', 'facetime': 'messengers',
	'googlechat': 'messengers', 'max': 'messengers',
	
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


@app.get("/{username}", response_class=HTMLResponse)
async def user_page(request: Request, username: str):
	conn = await asyncpg.connect(DATABASE_URL)
	try:
		# Сначала увеличиваем счетчик просмотров
		await conn.execute("UPDATE pages SET view_count = view_count + 1 WHERE username = $1", username)
		
		# Потом получаем данные страницы
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
		template_file = f"{folder}/{folder}_page.html" if folder else "page.html"
		
		# Получаем ссылки
		links_records = await conn.fetch("""
                                         SELECT *
                                         FROM links
                                         WHERE page_id = $1
                                           AND is_active = true
                                         ORDER BY sort_order
		                                 """, page_data['id'])
		
		# ПОЛУЧАЕМ ВСЕ ИКОНКИ ИЗ БАЗЫ ОДНИМ ЗАПРОСОМ
		icon_names = list(set([r['icon'] for r in links_records if r['icon']]))
		icon_map = {}
		
		if icon_names:
			icon_rows = await conn.fetch("""
                                         SELECT icon_code, font_awesome_class
                                         FROM icons
                                         WHERE icon_code = ANY ($1::text[])
			                             """, icon_names)
			icon_map = {row['icon_code']: row['font_awesome_class'] for row in icon_rows}
			
			print(f"📌 icon_names: {icon_names}")
			print(f"📌 icon_map: {icon_map}")
			print(f"📌 bnb in icon_map: {'bnb' in icon_map}")
		
		# Обрабатываем ссылки
		import json  # Добавь импорт в начало функции или файла
		processed_links = []
		for r in links_records:
			l_dict = dict(r)
			
			# --- НОВОЕ: ОБРАБОТКА JSON В pay_details ---
			pay_details = l_dict.get('pay_details')
			if pay_details and isinstance(pay_details, str):
				try:
					# Превращаем строку '{"tabs": ...}' в настоящий словарь Python
					l_dict['pay_details'] = json.loads(pay_details)
				except Exception as e:
					print(f"⚠️ Ошибка парсинга JSON для ссылки {l_dict.get('id')}: {e}")
					l_dict['pay_details'] = {}
			elif not pay_details:
				l_dict['pay_details'] = {}
			
			# --- ИСПРАВЛЕННАЯ ОБРАБОТКА URL (в функции user_page) ---
			original_url = l_dict.get('url')
			link_type = l_dict.get('link_type', 'standard')
			
			if original_url is not None and original_url != "#":
				if isinstance(original_url, str):
					original_url = original_url.strip()
				
				# ПРОВЕРКА: Если это крипта, НЕ добавляем https://, оставляем как есть
				if link_type == 'crypto' or link_type in ['binance', 'bybit', 'okx', 'metamask', 'kucoin']:
					l_dict['url'] = original_url
				
				# Для всего остального (соцсети и т.д.) добавляем протокол, если его нет
				elif not (original_url.startswith('http://') or original_url.startswith('https://')):
					l_dict['url'] = f"https://{original_url}"
				else:
					l_dict['url'] = original_url
			else:
				l_dict['url'] = "#"
			
			# --- ИСПРАВЛЕННАЯ ОБРАБОТКА ИКОНОК (main.py) ---
			icon_name = l_dict.get('icon')
			
			# Если в БД напрямую указан код иконки
			if icon_name and icon_name in icon_map:
				l_dict['icon_class'] = icon_map[icon_name]
			else:
				# Проверяем по link_type
				if link_type in ['binance', 'bybit', 'okx', 'metamask', 'kucoin', 'crypto']:
					# Если это кастомная крипта через бота
					if link_type == 'crypto':
						l_dict['icon_class'] = 'fas fa-coins'
					else:
						# Для бирж ставим иконку, но помни:
						# в HTML шаблоне у тебя приоритет на <img src="/static/icons/{{link_type}}.png">
						l_dict['icon_class'] = BRAND_ICONS.get(link_type, 'fas fa-wallet')
				elif link_type == 'finance':
					l_dict['icon_class'] = 'fas fa-credit-card'
				else:
					l_dict['icon_class'] = 'fas fa-link'
			
			l_dict['is_external'] = l_dict.get('url', '').startswith(('http://', 'https://'))
			processed_links.append(l_dict)
		
		# Получаем данные пользователя
		user_row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", page_data['user_id'])
		user_data = dict(user_row) if user_row else {}
		
		# ЯВНОЕ ПРЕОБРАЗОВАНИЕ ВСЕХ ПОЛЕЙ В СТРОКИ
		if user_data:
			# first_name может быть методом, преобразуем в строку
			if user_data.get('first_name'):
				user_data['first_name'] = str(user_data['first_name'])
			
			# username тоже преобразуем для надежности
			if user_data.get('username'):
				user_data['username'] = str(user_data['username'])
		
		# Если нет first_name, используем username из page
		if not user_data.get('first_name'):
			user_data['first_name'] = str(page_data.get('username', 'Пользователь'))
		
		print(f"🔥🔥🔥 ОБРАБОТКА СТРАНИЦЫ {username}")
		print(f"🔥 Всего ссылок: {len(processed_links)}")
		
		for link in processed_links:
			print(
				f"🔥 Ссылка: {link['title']}, link_type: {link['link_type']}, категория по словарю: {LINK_TYPE_CATEGORY.get(link['link_type'], 'other')}")
		
		# СОЗДАЕМ categories
		categories = {
			'social': [],
			'messengers': [],
			'transfers': [],
			'donate': [],
			'crypto': [],
			'shops': [],
			'partner': [],
			'other': []
		}
		
		for link in processed_links:
			link_type = link['link_type']
			
			# Автоматически определяем категорию для всех новых типов
			if (link_type.startswith('card_') or
					link_type.startswith('iban_') or
					link_type.startswith('phone_') or
					link_type.startswith('account_') or
					link_type.startswith('ach_') or
					link_type.startswith('wire_')):
				cat = 'transfers'
			else:
				# Для остальных используем словарь
				cat = LINK_TYPE_CATEGORY.get(link_type, 'other')
			
			if cat in categories:
				categories[cat].append(link)
			else:
				categories['other'].append(link)
		
		print(f"🔥 transfers: {len(categories['transfers'])} ссылок")
		
		# Теперь return с categories и COUNTRY_NAMES
		return templates.TemplateResponse(template_file, {
			"request": request,
			"user": user_data,
			"page": page_data,
			"links": processed_links,
			"categories": categories,
			"COUNTRY_NAMES": COUNTRY_NAMES
		})
	
	except Exception as e:
		print(f"🔥 ОШИБКА: {e}")
		import traceback
		traceback.print_exc()
		return HTMLResponse(f"Ошибка сервера: {e}", status_code=500)
	finally:
		await conn.close()


# # для Python
@app.get("/set_webhook")
async def set_webhook():
    # # Эта функция — одноразовая кнопка для связи с Telegram
    import os
    from telegram import Bot
    
    token = os.getenv("BOT_TOKEN")
    # # Твой адрес на Railway (или botolink.pro, когда DNS обновятся)
    webhook_url = "https://botolink.pro/webhook"
    
    bot = Bot(token=token)
    
    # Сначала удаляем старый вебхук (или поллинг), потом ставим новый
    await bot.delete_webhook()
    success = await bot.set_webhook(url=webhook_url)
    
    if success:
        return {"status": "success", "message": f"Webhook set to {webhook_url}"}
    return {"status": "error", "message": "Failed to set webhook"}


if __name__ == "__main__":
    # # Код для локального запуска или прямого вызова uvicorn
    import uvicorn
    import os
    
    # Railway передает порт через переменную окружения
    port = int(os.getenv("PORT", 8000))
    
    # Запускаем сервер. lifespan сам подцепит бота.
    uvicorn.run(app, host="0.0.0.0", port=port)