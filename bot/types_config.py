# types_config.py
# Конфигурация всех типов ссылок для конструктора
# Каждый тип описывает:
# - название, категорию, иконку
# - последовательность шагов заполнения

import logging
from typing import Dict, Any, Optional

# В НАЧАЛО ФАЙЛА (после импортов)

logger = logging.getLogger(__name__)

# ПОСЛЕ определения LINK_TYPES добавить:


# ===== КАТЕГОРИИ =====
CATEGORIES: Dict[str, Dict[str, Any]] = {
	"social": {
		"name": "📱 Соцсети / Email",
		"description": "Добавь ссылки на свои соцсети или электронные адреса - они появятся на твоей странице красивыми карточками с иконками. YouTube, Instagram, TikTok, VK и другие",
		"icon": "🌐"
	},
	"messengers": {
		"name": "💬 Мессенджеры",
		"description": "Укажи контакты для быстрой связи - они отобразятся на твоей странице. Telegram, WhatsApp, Viber, Signal",
		"icon": "💬"
	},
	"transfers": {
		"name": "💳 Банки / Переводы",
		"description": "Добавь реквизиты для переводов - они будут удобно показаны на твоей странице. Сбер, Т-Банк, Revolut, Wise",
		"icon": "🏦"
	},
	"crypto": {
		"name": "⚡ Кошельки и Биржи",
		"description": "Загрузи адреса криптокошельков - они появятся на твоей странице. Bitcoin, Ethereum, Binance, Bybit",
		"icon": "₿"
	},
	"donate": {
		"name": "🎨 Донат",
		"description": "Добавь ссылки для поддержки - кнопки донатов появятся на твоей странице. Patreon, Boosty, DonationAlerts",
		"icon": "❤️"
	},
	"shops": {
		"name": "🛍️ Магазины",
		"description": "Укажи ссылки на свои магазины - они отобразятся на твоей странице. Ozon, Wildberries, Avito, Amazon",
		"icon": "🛒"
	},
}
# ===== ОПРЕДЕЛЕНИЯ ШАГОВ =====
# Типы шагов:
# - text: простой текстовый ввод
# - phone: ввод телефона
# - email: ввод email
# - card: ввод карты (16 цифр)
# - iban: ввод IBAN
# - url: ввод ссылки
# - choice: выбор из вариантов
# - title: ввод названия (специальный, всегда последний)

# ===== ТИПЫ ССЫЛОК =====
LINK_TYPES: Dict[str, Dict[str, Any]] = {
	
	# ===== СОЦСЕТИ =====
	# Конфигурация шагов для YouTube с поддержкой копирования (HTML parse_mode)
	"youtube": {
		"name": "YouTube",
		"category": "social",
		"icon": "youtube",
		"steps": [
			{
				"type": "title",
				"question": "📝 <b>Заголовок карточки YouTube</b>\n\n"
				            "Например: <code>Мой влог</code> или <code>Игровой канал</code>\n"
				            "Если нажмете <b>Пропустить</b> → будет просто «YouTube»\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "title",
				"optional": True,
				"skip_button": True
			},
			{
				"type": "text",
				"question": "🔗 <b>Введите ID канала или ссылку</b>\n\n"
				            "Так выглядит пример готовой ссылки: <code>https://www.youtube.com/@MrBeast</code>\n\n"
				            "Вы можете ввести ниже:\n"
				            "• <code>@MrBeast</code>\n"
				            "• <code>MrBeast</code>\n"
				            "или просто ссылку целиком\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "channel_input",
				"optional": False,
				"skip_button": False
			},
			{
				"type": "text",
				"question": "📺 Введите <b>название вашего канала на youtube</b>\n"
				            "Например: <code>Мистер Бист</code>\n"
				            "Если нажмете <b>Пропустить</b> → то бот возьмет название из ID/ссылки",
				"field": "channel_name",
				"optional": True,
				"skip_button": True
			}
		]
	},
	
	"instagram": {
		"name": "Instagram",
		"category": "social",
		"icon": "instagram",
		"steps": [
			{
				"type": "title",
				"question": "📝 <b>Заголовок карточки Instagram</b>\n\n"
				            "Например: <code>Мой Instagram</code> или <code>Фотографии</code>\n"
				            "Если нажмете <b>Пропустить</b> → будет просто «Instagram»\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "title",
				"optional": True,
				"skip_button": True
			},
			{
				"type": "text",
				"question": "👤 <b>Введите username</b>\n\n"
				            "Например: <code>@mrbeast</code> или просто <code>mrbeast</code>\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "username",
				"optional": False
			}
		]
	},
	
	"tiktok": {
		"name": "TikTok",
		"category": "social",
		"icon": "tiktok",
		"steps": [
			{
				"type": "title",
				"question": "📝 <b>Заголовок карточки TikTok</b>\n\n"
				            "Например: <code>Мой TikTok</code> или <code>Приколы</code>\n"
				            "Если нажмете <b>Пропустить</b> → будет просто «TikTok»\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "title",
				"optional": True,
				"skip_button": True
			},
			{
				"type": "text",
				"question": "👤 <b>Введите username</b>\n\n"
				            "Например: <code>@mrbeast</code> или просто <code>mrbeast</code>\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "username",
				"optional": False
			}
		]
	},
	
	"vk": {
		"name": "VK",
		"category": "social",
		"icon": "vk",
		"steps": [
			{  # ШАГ 0: Заголовок
				"type": "title",
				"question": "📝 <b>Заголовок карточки VK</b>\n\n"
				            "Если нажмете <b>Пропустить</b> → будет просто «VK» Профиль Сообщество или Публичная страница",
				"field": "title",
				"optional": True,
				"skip_button": True
			},
			{  # ШАГ 1: Выбор типа
				"type": "choice",
				"question": "🇻🇰 <b>Что вы добавляете?</b>",
				"options": [
					{"value": "profile", "label": "👤 Личный профиль", "next_step": 2},
					{"value": "public", "label": "📄 Публичная страница", "next_step": 3},
					{"value": "group", "label": "👥 Группа", "next_step": 4}
				]
			},
			{  # ШАГ 2: Профиль - ID или короткое имя
				"type": "text",
				"question": "👤 <b>Введите ID или короткое имя профиля</b>\n\n"
				            "Примеры:\n"
				            "• ID: <code>123456789</code>\n"
				            "• Короткое имя: <code>durov</code>\n"
				            "• Ссылка: <code>https://vk.com/durov</code>\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "profile_id",
				"optional": False
			},
			{  # ШАГ 3: Публичная страница - ID или короткое имя
				"type": "text",
				"question": "📄 <b>Введите ID или короткое имя публичной страницы</b>\n\n"
				            "Примеры:\n"
				            "• ID: <code>-123456789</code> (с минусом)\n"
				            "• Короткое имя: <code>public_name</code>\n"
				            "• Ссылка: <code>https://vk.com/public_name</code>\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "public_id",
				"optional": False
			},
			{  # ШАГ 4: Группа - ID или короткое имя
				"type": "text",
				"question": "👥 <b>Введите ID или короткое имя группы</b>\n\n"
				            "Примеры:\n"
				            "• ID: <code>-987654321</code> (с минусом)\n"
				            "• Короткое имя: <code>club_name</code>\n"
				            "• Ссылка: <code>https://vk.com/club_name</code>\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "group_id",
				"optional": False
			}
		]
	},
	
	"ok": {
		"name": "Одноклассники",
		"category": "social",
		"icon": "ok",
		"steps": [
			{
				"type": "title",
				"question": "📝 <b>Заголовок карточки Одноклассники</b>\n\n"
				            "Например: <code>Мой профиль</code> или <code>Группа</code>\n"
				            "Если нажмете <b>Пропустить</b> → будет просто «Одноклассники»\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "title",
				"optional": True,
				"skip_button": True
			},
			{
				"type": "text",
				"question": "🔗 <b>Введите ID или ссылку на профиль/группу</b>\n\n"
				            "Примеры:\n"
				            "• ID профиля: <code>1234567890</code>\n"
				            "• ID группы: <code>123456789</code>\n"
				            "• Ссылка: <code>https://ok.ru/profile/1234567890</code>\n"
				            "• Ссылка: <code>https://ok.ru/group/123456789</code>\n"
				            "• Именная ссылка: <code>ivanov</code> или <code>https://ok.ru/ivanov</code>\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "profile_input",
				"optional": False
			}
		]
	},
	
	"facebook": {
		"name": "Facebook",
		"category": "social",
		"icon": "facebook",
		"steps": [
			{  # ШАГ 0: Заголовок
				"type": "title",
				"question": "📝 <b>Заголовок карточки Facebook</b>\n\n"
				            "Если нажмете <b>Пропустить</b> → будет просто «Facebook» Профиль Страница или Группа ",
				"field": "title",
				"optional": True,
				"skip_button": True
			},
			{  # ШАГ 1: Выбор типа
				"type": "choice",
				"question": "📘 <b>Что вы добавляете?</b>",
				"options": [
					{"value": "profile", "label": "👤 Личный профиль", "next_step": 2},
					{"value": "page", "label": "📄 Публичная страница", "next_step": 3},
					{"value": "group", "label": "👥 Группа", "next_step": 5}
				]
			},
			{  # ШАГ 2: Профиль - username
				"type": "text",
				"question": "👤 <b>Введите username профиля</b>\n\n"
				            "Например: <code>zuck</code> или <code>https://facebook.com/zuck</code>",
				"field": "username",
				"optional": False
			},
			{  # ШАГ 3: Страница - название
				"type": "text",
				"question": "📄 <b>Введите название страницы</b>\n\n"
				            "Например: <code>Nike Germany</code>",
				"field": "page_title",
				"optional": False
			},
			{  # ШАГ 4: Страница - username
				"type": "text",
				"question": "🔗 <b>Введите username страницы</b>\n\n"
				            "Например: <code>nike</code> или <code>https://facebook.com/nike</code>",
				"field": "page_username",
				"optional": False
			},
			{  # ШАГ 5: Группа - название
				"type": "text",
				"question": "👥 <b>Введите название группы</b>\n\n"
				            "Например: <code>BMW Club</code>",
				"field": "group_title",
				"optional": False
			},
			{  # ШАГ 6: Группа - username
				"type": "text",
				"question": "🔗 <b>Введите username группы</b>\n\n"
				            "Например: <code>bmwclub</code> или <code>https://facebook.com/groups/bmwclub</code>",
				"field": "group_username",
				"optional": False
			}
		]
	},
	
	"twitter": {
		"name": "Twitter/X",
		"category": "social",
		"icon": "twitter",
		"steps": [
			{
				"type": "title",
				"question": "📝 <b>Заголовок карточки Twitter/X</b>\n\n"
				            "Например: <code>Мой Twitter</code> или <code>Новости X</code>\n"
				            "Если нажмете <b>Пропустить</b> → будет просто «Twitter»\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "title",
				"optional": True,
				"skip_button": True
			},
			{
				"type": "text",
				"question": "👤 <b>Введите username профиля</b>\n\n"
				            "Примеры:\n"
				            "• Только username: <code>elonmusk</code>\n"
				            "• С @: <code>@elonmusk</code>\n"
				            "• Полная ссылка: <code>https://twitter.com/elonmusk</code>\n"
				            "• Или ссылка X.com: <code>https://x.com/elonmusk</code>\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "username",
				"optional": False
			}
		]
	},
	
	"twitch": {
		"name": "Twitch",
		"category": "social",
		"icon": "twitch",
		"steps": [
			{
				"type": "title",
				"question": "📝 <b>Заголовок карточки Twitch</b>\n\n"
				            "Например: <code>Мой стрим</code> или <code>Игры</code>\n"
				            "Если нажмете <b>Пропустить</b> → будет просто «Twitch»\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "title",
				"optional": True,
				"skip_button": True
			},
			{
				"type": "text",
				"question": "👤 <b>Введите название канала</b>\n\n"
				            "Примеры:\n"
				            "• <code>summit1g</code>\n"
				            "• <code>https://twitch.tv/summit1g</code>\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "username",
				"optional": False
			}
		]
	},
	
	"rutube": {
		"name": "Rutube",
		"category": "social",
		"icon": "rutube",
		"steps": [
			{
				"type": "title",
				"question": "📝 <b>Заголовок карточки Rutube</b>\n\n"
				            "Например: <code>Мой канал</code> или <code>Лучшие видео</code>\n"
				            "Если нажмете <b>Пропустить</b> → будет просто «Rutube»\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "title",
				"optional": True,
				"skip_button": True
			},
			{
				"type": "text",
				"question": "🔗 <b>Введите ID канала или ссылку</b>\n\n"
				            "Так выглядит пример готовой ссылки: <code>https://rutube.ru/channel/24613585/</code>\n\n"
				            "Вы можете ввести ниже:\n"
				            "• <code>24613585</code>\n"
				            "• <code>https://rutube.ru/channel/24613585/</code>\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "channel_input",
				"optional": False,
				"skip_button": False
			},
			{
				"type": "text",
				"question": "📺 Введите <b>название вашего канала на Rutube</b>\n"
				            "Например: <code>Мой лучший канал</code>\n"
				            "Если нажмете <b>Пропустить</b> → то бот возьмет название из ID/ссылки",
				"field": "channel_name",
				"optional": True,
				"skip_button": True
			}
		]
	},
	
	"dzen": {
		"name": "Дзен",
		"category": "social",
		"icon": "dzen",
		"steps": [
			{
				"type": "title",
				"question": "📝 <b>Заголовок карточки Дзен</b>\n\n"
				            "Например: <code>Мой канал</code>\n"
				            "Если нажмете <b>Пропустить</b> → будет просто «Дзен»\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "title",
				"optional": True,
				"skip_button": True
			},
			{
				"type": "text",
				"question": "🔗 <b>Введите ID канала или ссылку</b>\n\n"
				            "Примеры:\n"
				            "• ID канала: <code>123456</code>\n"
				            "• Ссылка: <code>https://dzen.ru/id/123456</code>\n"
				            "• Ссылка: <code>https://dzen.ru/username</code>\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "channel_input",
				"optional": False
			}
		]
	},
	
	"snapchat": {
		"name": "Snapchat",
		"category": "social",
		"icon": "snapchat",
		"steps": [
			{
				"type": "title",
				"question": "📝 <b>Заголовок карточки snapchat</b>\n\n"
				            "Например: <code>Мой Snapchat</code>\n"
				            "Если нажмете <b>Пропустить</b> → будет просто «Snapchat»\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "title",
				"optional": True,
				"skip_button": True
			},
			{
				"type": "text",
				"question": "👤 <b>Введите username</b>\n\n"
				            "Примеры:\n"
				            "• <code>username</code>\n"
				            "• <code>@username</code>\n"
				            "• <code>https://snapchat.com/add/username</code>\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "username",
				"optional": False
			}
		]
	},
	
	"likee": {
		"name": "Likee",
		"category": "social",
		"icon": "likee",
		"steps": [
			{
				"type": "title",
				"question": "📝 <b>Заголовок карточки Likee</b>\n\n"
				            "Например: <code>Мой Likee</code>\n"
				            "Если нажмете <b>Пропустить</b> → будет просто «Likee»\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "title",
				"optional": True,
				"skip_button": True
			},
			{
				"type": "text",
				"question": "👤 <b>Введите username</b>\n\n"
				            "Примеры:\n"
				            "• <code>username</code>\n"
				            "• <code>@username</code>\n"
				            "• <code>https://likee.video/@username</code>\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "username",
				"optional": False
			}
		]
	},
	
	"threads": {
		"name": "Threads",
		"category": "social",
		"icon": "threads",
		"steps": [
			{
				"type": "title",
				"question": "📝 <b>Заголовок карточки</b>\n\n"
				            "Например: <code>Мои мысли</code>\n"
				            "Если нажмете <b>Пропустить</b> → будет просто «Threads»\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "title",
				"optional": True,
				"skip_button": True
			},
			{
				"type": "text",
				"question": "👤 <b>Введите username</b>\n\n"
				            "Примеры:\n"
				            "• <code>username</code>\n"
				            "• <code>@username</code>\n"
				            "• <code>https://threads.net/@username</code>\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "username",
				"optional": False
			}
		]
	},
	
	"discord": {
		"name": "Discord",
		"category": "social",
		"icon": "discord",
		"steps": [
			{
				"type": "title",
				"question": "📝 <b>Заголовок карточки Discord</b>\n\n"
				            "Например: <code>Мой сервер</code> или <code>Discord</code>\n"
				            "Если нажмете <b>Пропустить</b> → будет просто «Discord»\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "title",
				"optional": True,
				"skip_button": True
			},
			{
				"type": "choice",
				"question": "🎮 <b>Что добавляем?</b>",
				"options": [
					{"value": "invite", "label": "🔗 Приглашение на сервер", "next_step": 2},
					{"value": "profile", "label": "👤 Профиль пользователя", "next_step": 3}
				]
			},
			{
				"type": "text",
				"question": "🔗 <b>Введите ссылку-приглашение на сервер</b>\n\n"
				            "Примеры:\n"
				            "• <code>https://discord.gg/abc123</code>\n"
				            "• <code>discord.gg/phibisparadise</code>\n"
				            "• <code>https://discord.gg/MyServer</code>\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "invite_link",
				"optional": False
			},
			{
				"type": "text",
				"question": "👤 <b>Введите ID пользователя или ссылку на профиль</b>\n\n"
				            "Примеры:\n"
				            "• <code>568696023409754142</code> (ID пользователя)\n"
				            "• <code>https://discord.com/users/568696023409754142</code>\n\n"
				            "Как найти ID: Настройки → Режим разработчика → ПКМ на пользователе → Копировать ID\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "user_id",
				"optional": False
			}
		]
	},
	
	"email": {
	    "name": "Email",
	    "category": "social",
	    "icon": "email",
	    "steps": [
	        {
	            "type": "title",
	            "question": "📝 <b>Заголовок карточки Email</b>\n\n"
	                        "Например: <code>Мой Gmail</code> или <code>Email</code>\n"
	                        "Если нажмете <b>Пропустить</b> → будет просто «Email»\n\n"
	                        "👇 <b>Вводите текст в поле чата бота</b>",
	            "field": "title",
	            "optional": True,
	            "skip_button": True
	        },
	        {
	            "type": "text",
	            "question": "✉️ <b>Введите email адрес</b>\n\n"
	                        "Примеры:\n"
	                        "• <code>name@example.com</code>\n"
	                        "• <code>my.mail@gmail.com</code>\n\n"
	                        "👇 <b>Вводите текст в поле чата бота</b>",
	            "field": "email",
	            "optional": False
	        }
	    ]
	},
	
	# ===== МЕССЕНДЖЕРЫ =====
	"whatsapp": {
		"name": "WhatsApp",
		"category": "messengers",
		"icon": "whatsapp",
		"steps": [
			{
				"type": "title",
				"question": "📝 <b>Название карточки WhatsApp</b>\n\n"
				            "Придумайте название для этой карточки\n"
				            "Например: <code>Мой WhatsApp</code>\n\n"
				            "👇 <b>Вводите текст</b>",
				"field": "title",
				"optional": True,
				"skip_button": True
			},
			{
				"type": "text",
				"question": "📞 <b>Номер или ссылка WhatsApp</b>\n\n"
				            "Введите номер в любом формате:\n"
				            "• <code>77011234567</code> (только цифры)\n"
				            "• <code>+77011234567</code> (с плюсом)\n"
				            "• <code>8 701 123-45-67</code> (с пробелами и дефисами)\n"
				            "• <code>https://wa.me/77011234567</code> (готовая ссылка)\n\n"
				            "👇 <b>Вводите текст</b>",
				"field": "phone",
				"optional": False
			}
		]
	},
	
	"viber": {
		"name": "Viber",
		"category": "messengers",
		"icon": "viber",
		"steps": [
			{
				"type": "title",
				"question": "📝 <b>Название карточки Viber</b>\n\n"
				            "Придумайте название для этой карточки\n"
				            "Например: <code>Мой Viber</code>\n\n"
				            "👇 <b>Вводите текст</b>",
				"field": "title",
				"optional": True,
				"skip_button": True
			},
			{
				"type": "text",
				"question": "📞 <b>Номер телефона для Viber</b>\n\n"
				            "Введите номер в любом формате:\n"
				            "• <code>4915123456789</code> (только цифры)\n"
				            "• <code>+49 151 23456789</code> (Германия, с плюсом)\n"
				            "• <code>8 029 123-45-67</code> (с пробелами и дефисами)\n"
				            "• <code>https://viber.click/4915123456789</code> (готовая ссылка)\n\n"
				            "👇 <b>Вводите текст</b>",
				"field": "phone",
				"optional": False
			}
		]
	},
	
	"telegram": {
		"name": "Telegram",
		"category": "messengers",
		"icon": "telegram",
		"steps": [
			{
				"type": "choice",
				"question": "📱 <b>Что добавляем в карточку Telegram?</b>",
				"options": [
					{"value": "personal", "label": "👤 Личный аккаунт", "next_step": 2},
					{"value": "channel", "label": "📢 Канал", "next_step": 3},
					{"value": "group", "label": "👥 Группа/Супергруппа", "next_step": 4},
					{"value": "bot", "label": "🤖 Бот", "next_step": 5}
				]
			},
			{
				"type": "title",
				"question": "📝 <b>Заголовок карточки Telegram</b>\n\nЕсли нажмете <b>Пропустить</b> → будет просто «Telegram»\n\n👇 <b>Вводите текст</b>",
				"field": "title",
				"max_length": 100,
				"optional": True,
				"skip_button": True
			},
			{
				"type": "text",
				"question": "👤 <b>Введите username или ссылку для личного аккаунта Telegram</b>\n\nПримеры:\n• <code>durov</code>\n• <code>@durov</code>\n• <code>https://t.me/durov</code>\n\n👇 <b>Вводите текст</b>",
				"field": "identifier",
				"max_length": 100,
				"optional": False
			},
			{
				"type": "text",
				"question": "📢 <b>Введите username или ссылку на канал Telegram</b>\n\nПримеры:\n• <code>durov</code>\n• <code>@durov</code>\n• <code>https://t.me/durov</code>\n\n👇 <b>Вводите текст</b>",
				"field": "identifier",
				"max_length": 100,
				"optional": False
			},
			{
				"type": "text",
				"question": "👥 <b>Введите username или ссылку на группу в Telegram</b>\n\nПримеры:\n• <code>durov</code> (публичная группа)\n• <code>@durov</code>\n• <code>https://t.me/durov</code>\n• <code>https://t.me/joinchat/AbCdEfGhIjK</code> (приватная)\n• <code>https://t.me/+AbCdEfGhIjK</code> (приватная)\n\n👇 <b>Вводите текст</b>",
				"field": "identifier",
				"max_length": 100,
				"optional": False
			},
			{
				"type": "text",
				"question": "🤖 <b>Введите username или ссылку на бота в Telegram</b>\n\nПримеры:\n• <code>durov_bot</code>\n• <code>@durov_bot</code>\n• <code>https://t.me/durov_bot</code>\n\n👇 <b>Вводите текст</b>",
				"field": "identifier",
				"max_length": 100,
				"optional": False
			}
		]
	},
	
	"signal": {
		"name": "Signal",
		"category": "messengers",
		"icon": "signal",
		"steps": [
			{
				"type": "text",
				"question": "🆔 <b>Signal ID (username)</b>\n\n"
				            "Введите ваш Signal username:\n"
				            "• Например: <code>john_doe.123</code> или <code>alice.signal</code>\n"
				            "• Можно с точками и цифрами\n"
				            "• Без @ в начале\n"
				            "• <code>https://signal.me/#u/username</code> (готовая ссылка)\n\n"
				            "👇 <b>Вводите текст</b>",
				"field": "username",
				"optional": False,
				"skip_button": False
			},
			{
				"type": "title",
				"question": "📝 <b>Название карточки Signal</b>\n\n"
				            "Придумайте название для этой карточки\n"
				            "Например: <code>Мой Signal</code>\n\n"
				            "👇 <b>Вводите текст</b>",
				"field": "title",
				"optional": True,
				"skip_button": True
			}
		]
	},
	

	
	"zalo": {
	    "name": "Zalo",
	    "category": "messengers",
	    "icon": "zalo",
	    "steps": [
	       {
	          "type": "title",
	          "question": "📝 <b>Название карточки Zalo</b>\n\n"
	                      "Придумайте название для этой карточки\n"
	                      "Например: <code>Мой Zalo</code>\n\n"
	                      "👇 <b>Вводите текст</b>",
	          "field": "title",
	          "optional": True,
	          "skip_button": True
	       },
	       {
	          "type": "text",
	          "question": "📞 <b>Данные для Zalo</b>\n\n"
	                      "Введите любой из вариантов:\n"
	                      "• <b>Номер:</b> <code>84912345678</code>\n"
	                      "• <b>ID:</b> <code>912345678</code>\n"
	                      "• <b>Ссылка:</b> <code>https://zalo.me/84912345678</code>\n\n"
	                      "👇 <b>Вводите текст</b>",
	          "field": "phone",
	          "optional": False
	       }
	    ]
	},
	
	"max": {
	    "name": "Max",
	    "category": "messengers",
	    "icon": "max",
	    "steps": [
	       {
	          "type": "title",
	          "question": "📝 <b>Название карточки Max</b>\n\n"
	                      "Придумайте название для этой карточки\n"
	                      "Например: <code>Мой Max</code>\n\n"
	                      "👇 <b>Вводите текст</b>",
	          "field": "title",
	          "optional": True,
	          "skip_button": True
	       },
	       {
	          "type": "text",
	          "question": "🆔 <b>Идентификатор Max</b>\n\n"
	                      "Введите данные в любом формате:\n"
	                      "• <b>ID:</b> <code>7952544647</code>\n"
	                      "• <b>Ссылка:</b> <code>https://max.ru/id/7952544647</code>\n\n"
	                      "👇 <b>Вводите текст</b>",
	          "field": "id",
	          "optional": False
	       }
	    ]
	},
	

	
	# ===== БАНКИ (простые) =====
	# Добавить в LINK_TYPES (после других банков)
	
	"paypal": {  # уже есть, но обновить
		"name": "PayPal",
		"category": "transfers",
		"icon": "paypal",
		"steps": [
			{"type": "text", "question": "Введите email PayPal:", "field": "username", "example": "user@example.com"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"monobank": {
		"name": "Монобанк",
		"category": "transfers",
		"icon": "monobank",
		"steps": [
			{"type": "card", "question": "Введите номер карты:", "field": "card_number",
			 "example": "5375 4114 1234 5678"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"kaspi": {
		"name": "Kaspi.kz",
		"category": "transfers",
		"icon": "kaspi",
		"steps": [
			{"type": "choice", "question": "🇰🇿 Что указать?",
			 "options": [
				 {"value": "card", "label": "Карта", "next_step": 1},
				 {"value": "phone", "label": "Телефон", "next_step": 2}
			 ]},
			{"type": "card", "question": "Введите номер карты:", "field": "card_number"},
			{"type": "phone", "question": "Введите номер телефона:", "field": "phone"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"payme": {
		"name": "Payme",
		"category": "transfers",
		"icon": "payme",
		"steps": [
			{"type": "phone", "question": "Введите номер телефона:", "field": "phone", "example": "+998901234567"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"click": {
		"name": "Click",
		"category": "transfers",
		"icon": "click",
		"steps": [
			{"type": "phone", "question": "Введите номер телефона:", "field": "phone", "example": "+998901234567"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"tbcpay": {
		"name": "TBC Pay",
		"category": "transfers",
		"icon": "tbcpay",
		"steps": [
			{"type": "choice", "question": "🇬🇪 Что указать?",
			 "options": [
				 {"value": "card", "label": "Карта", "next_step": 1},
				 {"value": "phone", "label": "Телефон", "next_step": 2}
			 ]},
			{"type": "card", "question": "Введите номер карты:", "field": "card_number"},
			{"type": "phone", "question": "Введите номер телефона:", "field": "phone"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"idram": {
		"name": "Idram",
		"category": "transfers",
		"icon": "idram",
		"steps": [
			{"type": "choice", "question": "🇦🇲 Что указать?",
			 "options": [
				 {"value": "card", "label": "Карта", "next_step": 1},
				 {"value": "phone", "label": "Телефон", "next_step": 2}
			 ]},
			{"type": "card", "question": "Введите номер карты:", "field": "card_number"},
			{"type": "phone", "question": "Введите номер телефона:", "field": "phone"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"yoomoney": {
		"name": "ЮMoney",
		"category": "transfers",
		"icon": "yoomoney",
		"steps": [
			{"type": "choice", "question": "💰 Что указать?",
			 "options": [
				 {"value": "wallet", "label": "Номер кошелька", "next_step": 1},
				 {"value": "card", "label": "Карта", "next_step": 2}
			 ]},
			{"type": "text", "question": "Введите номер кошелька:", "field": "wallet"},
			{"type": "card", "question": "Введите номер карты:", "field": "card"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"sber": {
		"name": "Сбер",
		"category": "transfers",
		"icon": "sber",
		"steps": [
			{"type": "choice", "question": "🏦 Что указать?",
			 "options": [
				 {"value": "card", "label": "Карта", "next_step": 1},
				 {"value": "phone", "label": "Телефон", "next_step": 2}
			 ]},
			{"type": "card", "question": "Введите номер карты:", "field": "card"},
			{"type": "phone", "question": "Введите номер телефона:", "field": "phone"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"vtb": {
		"name": "ВТБ",
		"category": "transfers",
		"icon": "vtb",
		"steps": [
			{"type": "card", "question": "💳 Введите номер карты:", "field": "card"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"tbank": {
		"name": "Т-Банк",
		"category": "transfers",
		"icon": "tbank",
		"steps": [
			{"type": "choice", "question": "🏦 Что указать?",
			 "options": [
				 {"value": "card", "label": "Карта", "next_step": 1},
				 {"value": "phone", "label": "Телефон", "next_step": 2}
			 ]},
			{"type": "card", "question": "Введите номер карты:", "field": "card"},
			{"type": "phone", "question": "Введите номер телефона:", "field": "phone"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"bidv": {
		"name": "BIDV",
		"category": "transfers",
		"icon": "bidv",
		"steps": [
			{"type": "text", "question": "🏦 Введите номер счета:", "field": "account"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"korona": {
		"name": "Золотая Корона",
		"category": "transfers",
		"icon": "korona",
		"steps": [
			{"type": "choice", "question": "👑 Что указать?",
			 "options": [
				 {"value": "card", "label": "Карта", "next_step": 1},
				 {"value": "phone", "label": "Телефон", "next_step": 2}
			 ]},
			{"type": "card", "question": "Введите номер карты:", "field": "card"},
			{"type": "phone", "question": "Введите номер телефона:", "field": "phone"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"westernunion": {
		"name": "Western Union",
		"category": "transfers",
		"icon": "westernunion",
		"steps": [
			{"type": "text", "question": "👤 Введите имя получателя:", "field": "recipient"},
			{"type": "text", "question": "📍 Введите страну:", "field": "country"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"unistream": {
		"name": "Unistream",
		"category": "transfers",
		"icon": "unistream",
		"steps": [
			{"type": "text", "question": "💳 Введите номер перевода:", "field": "transfer_number"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	
	
	    "metamask": {
	        "name": "Metamask",
	        "category": "wallets",
	        "icon": "metamask",
	        "steps": [
	            {"type": "text", "field": "wallet_address", "question": "🦊 <b>Адрес вашего Metamask</b>\n\n<blockquote>Это единый адрес для всех сетей стандарта EVM (Ethereum, BSC, Polygon, Arbitrum и т.д.).</blockquote>\n\n📝 <b>Пример:</b> <code>0x71C...</code>\n\n👇 <b>Вставьте адрес кошелька:</b>"},
	            {"type": "text", "field": "network", "question": "🌐 <b>Укажите основную сеть</b>\n\n<blockquote>Напишите, в какой сети вы чаще всего ждете переводы на этот адрес.</blockquote>\n\n📝 <b>Примеры:</b> <code>Ethereum</code>, <code>BSC (BEP20)</code>, <code>Polygon</code>\n\n👇 <b>Введите название сети:</b>"},
	            {"type": "title", "field": "title", "optional": True, "question": "🎴 <b>Название на странице:</b>"}
	        ]
	    },
	
	"trustwallet": {
	        "name": "Trust Wallet",
	        "category": "wallets",
	        "icon": "trustwallet",
	        "steps": [
	            {
	                "type": "text",
	                "field": "wallet_address",
	                "question": "🔐 <b>Ваш адрес в Trust Wallet</b>\n\n<blockquote>Зайдите в кошелёк, выберите нужную монету, нажмите «Получить» и скопируйте адрес.</blockquote>\n\n👇 <b>Вставьте скопированный адрес:</b>"
	            },
	            {
	                "type": "text",
	                "field": "network",
	                "question": "🌐 <b>Сеть для перевода (Network)</b>\n\n<blockquote>В какой сети работает этот адрес? Это очень важно для успешного зачисления средств.</blockquote>\n\n📝 <b>Например:</b> <code>BEP20 (BSC)</code>, <code>TRC20</code>, <code>Solana</code>\n\n👇 <b>Введите название сети:</b>"
	            },
	            {
	                "type": "title",
	                "field": "title",
	                "optional": True,
	                "question": "🎴 <b>Название для вашей страницы</b>\n\n<blockquote>Как будет подписана эта карточка в профиле? Если пропустите, будет написано «Trust Wallet».</blockquote>\n\n👇 <b>Введите название или нажмите «Пропустить»:</b>"
	            }
	        ]
	    },
	
	"usdt": {
	        "name": "USDT",
	        "category": "wallets",
	        "icon": "usdt",
	        "steps": [
	            {
	                "type": "text",
	                "field": "wallet_address",
	                "question": "💰 <b>Ваш адрес USDT</b>\n\n<blockquote>Внимательно проверьте каждый символ! Ошибка приведет к безвозвратной потере средств.</blockquote>\n\n📝 <b>Пример:</b> <code>TR7NHqjeKQxGChJ...</code>\n\n👇 <b>Вставьте адрес кошелька:</b>"
	            },
	            {
	                "type": "text",
	                "field": "network",
	                "question": "🌐 <b>Сеть для USDT (Обязательно!)</b>\n\n<blockquote>Самые популярные: <b>TRC20</b>, <b>ERC20</b> или <b>BEP20</b>. Укажите именно ту, в которой работает ваш адрес.</blockquote>\n\n👇 <b>Введите название сети:</b>"
	            },
	            {
	                "type": "title",
	                "field": "title",
	                "optional": True,
	                "question": "🎴 <b>Название карточки</b>\n\n<blockquote>Например: «Мой USDT (TRC20)». По умолчанию будет просто «USDT».</blockquote>\n\n👇 <b>Введите текст или нажмите «Пропустить»:</b>"
	            }
	        ]
	    },
	
	"btc": {
	        "name": "Bitcoin",
	        "category": "wallets",
	        "icon": "btc",
	        "steps": [
	            {
	                "type": "text",
	                "field": "wallet_address",
	                "question": "₿ <b>Ваш Bitcoin адрес (BTC)</b>\n\n<blockquote><b>Как выглядит адрес:</b>\n• Начинается на <code>1...</code>, <code>3...</code> или <code>bc1...</code>\n• Длинная строка из букв и цифр.</blockquote>\n\n👇 <b>Вставьте адрес кошелька:</b>"
	            },
	            {
	                "type": "text",
	                "field": "network",
	                "question": "🌐 <b>Тип сети / Формат</b>\n\n<blockquote>Если не знаете, что писать — нажмите <b>«Пропустить»</b>.</blockquote>\n\n📝 <b>Популярные сети:</b>\n• <code>Bitcoin (Mainnet)</code> — стандарт\n• <code>Lightning</code> — для быстрых микроплатежей\n• <code>SegWit</code> — современные адреса\n\n👇 <b>Введите сеть или пропустите:</b>",
	                "optional": True
	            },
	            {"type": "title", "field": "title", "optional": True, "question": "🎴 <b>Название для карточки:</b>"}
	        ]
	    },
	
	    "usdt": {
	        "name": "USDT",
	        "category": "wallets",
	        "icon": "usdt",
	        "steps": [
	            {
	                "type": "text",
	                "field": "wallet_address",
	                "question": "💰 <b>Ваш адрес USDT</b>\n\n<blockquote><b>Как выглядит адрес:</b>\n• В сети TRC20 начинается на <code>T...</code>\n• В сети ERC20/BEP20 начинается на <code>0x...</code></blockquote>\n\n👇 <b>Вставьте адрес:</b>"
	            },
	            {
	                "type": "text",
	                "field": "network",
	                "question": "🌐 <b>Укажите сеть (Обязательно)</b>\n\n<blockquote>Ошибка в сети приведет к потере денег!</blockquote>\n\n📝 <b>Самые популярные:</b>\n• <code>TRC20</code> — (Сеть TRON, дешево)\n• <code>ERC20</code> — (Сеть Ethereum, дорого)\n• <code>BEP20</code> — (Сеть BSC, дешево)\n\n👇 <b>Введите название сети:</b>"
	            },
	            {"type": "title", "field": "title", "optional": True, "question": "🎴 <b>Название для карточки:</b>"}
	        ]
	    },
	
	    "eth": {
	        "name": "Ethereum",
	        "category": "wallets",
	        "icon": "eth",
	        "steps": [
	            {
	                "type": "text",
	                "field": "wallet_address",
	                "question": "Ξ <b>Ваш Ethereum адрес (ETH)</b>\n\n<blockquote><b>Как выглядит адрес:</b>\n• Всегда начинается на <code>0x...</code></blockquote>\n\n👇 <b>Вставьте адрес кошелька:</b>"
	            },
	            {
	                "type": "text",
	                "field": "network",
	                "question": "🌐 <b>Укажите сеть</b>\n\n📝 <b>Популярные:</b>\n• <code>ERC20</code> — (Основная сеть)\n• <code>Arbitrum One</code> — (L2 сеть)\n• <code>Optimism</code> — (L2 сеть)\n\n👇 <b>Введите сеть или пропустите:</b>",
	                "optional": True
	            },
	            {"type": "title", "field": "title", "optional": True, "question": "🎴 <b>Название для карточки:</b>"}
	        ]
	    },
	
	    "ton": {
	        "name": "TON",
	        "category": "wallets",
	        "icon": "ton",
	        "steps": [
	            {
	                "type": "text",
	                "field": "wallet_address",
	                "question": "💎 <b>Ваш адрес TON</b>\n\n<blockquote><b>Как выглядит адрес:</b>\n• Начинается на <code>UQ...</code> или <code>EQ...</code></blockquote>\n\n👇 <b>Вставьте адрес из Wallet или Tonkeeper:</b>"
	            },
	            {
	                "type": "text",
	                "field": "network",
	                "question": "🌐 <b>Укажите сеть</b>\n\n📝 <b>Обычно это:</b>\n• <code>TON Mainnet</code>\n\n👇 <b>Введите сеть или пропустите:</b>",
	                "optional": True
	            },
	            {"type": "title", "field": "title", "optional": True, "question": "🎴 <b>Название для карточки:</b>"}
	        ]
	    },
	
	    "sol": {
	        "name": "Solana",
	        "category": "wallets",
	        "icon": "sol",
	        "steps": [
	            {
	                "type": "text",
	                "field": "wallet_address",
	                "question": "◎ <b>Ваш Solana адрес (SOL)</b>\n\n<blockquote><b>Как выглядит адрес:</b>\n• Набор случайных букв и цифр (обычно длиннее BTC).</blockquote>\n\n👇 <b>Вставьте адрес:</b>"
	            },
	            {
	                "type": "text",
	                "field": "network",
	                "question": "🌐 <b>Укажите сеть</b>\n\n📝 <b>Обычно это:</b>\n• <code>Solana Mainnet</code>\n\n👇 <b>Введите сеть или пропустите:</b>",
	                "optional": True
	            },
	            {"type": "title", "field": "title", "optional": True, "question": "🎴 <b>Название для карточки:</b>"}
	        ]
	    },
	
	"trx": {
		        "name": "TRON",
		        "category": "wallets",
		        "icon": "trx",
		        "steps": [
		            {"type": "text", "field": "wallet_address", "question": "🔷 <b>Ваш TRON (TRX) адрес</b>\n\n<blockquote>Обычно начинается на букву «T».</blockquote>\n\n👇 <b>Вставьте адрес:</b>"},
		            {"type": "text", "field": "network", "question": "🌐 <b>Укажите сеть</b>\n\n👇 <b>Напишите <code>TRC20</code> или нажмите «Пропустить»:</b>", "optional": True},
		            {"type": "title", "field": "title", "optional": True, "question": "🎴 <b>Название для карточки:</b>"}
		        ]
		    },
		
		    "bnb": {
		        "name": "BNB (BSC)",
		        "category": "wallets",
		        "icon": "bnb",
		        "steps": [
		            {"type": "text", "field": "wallet_address", "question": "🟡 <b>Ваш адрес BNB (Smart Chain)</b>\n\n<blockquote>Адрес сети BEP20, начинается на <code>0x...</code>.</blockquote>\n\n👇 <b>Вставьте адрес:</b>"},
		            {"type": "text", "field": "network", "question": "🌐 <b>Сеть</b>\n\n👇 <b>Напишите <code>BSC (BEP20)</code> или нажмите «Пропустить»:</b>", "optional": True},
		            {"type": "title", "field": "title", "optional": True, "question": "🎴 <b>Название для карточки:</b>"}
		        ]
		    },
		
		    "doge": {
		        "name": "Dogecoin",
		        "category": "wallets",
		        "icon": "doge",
		        "steps": [
		            {"type": "text", "field": "wallet_address", "question": "🐕 <b>Ваш Dogecoin адрес</b>\n\n👇 <b>Вставьте адрес (обычно начинается на «D»):</b>"},
		            {"type": "text", "field": "network", "question": "🌐 <b>Сеть</b>\n\n👇 <b>Напишите <code>Dogecoin</code> или нажмите «Пропустить»:</b>", "optional": True},
		            {"type": "title", "field": "title", "optional": True, "question": "🎴 <b>Название для карточки:</b>"}
		        ]
		    },
		
		    "ltc": {
		        "name": "Litecoin",
		        "category": "wallets",
		        "icon": "ltc",
		        "steps": [
		            {"type": "text", "field": "wallet_address", "question": "Ł <b>Ваш Litecoin адрес (LTC)</b>\n\n👇 <b>Вставьте адрес:</b>"},
		            {"type": "text", "field": "network", "question": "🌐 <b>Сеть</b>\n\n👇 <b>Напишите <code>Litecoin</code> или нажмите «Пропустить»:</b>", "optional": True},
		            {"type": "title", "field": "title", "optional": True, "question": "🎴 <b>Название для карточки:</b>"}
		        ]
		    },
		
		    "xrp": {
		        "name": "Ripple",
		        "category": "wallets",
		        "icon": "xrp",
		        "steps": [
		            {"type": "text", "field": "wallet_address", "question": "💧 <b>Ваш XRP адрес</b>\n\n<blockquote>Если для получения нужен <b>Tag (Memo)</b>, допишите его через пробел или укажите в названии.</blockquote>\n\n👇 <b>Вставьте адрес:</b>"},
		            {"type": "text", "field": "network", "question": "🌐 <b>Сеть</b>\n\n👇 <b>Напишите <code>Ripple</code> или нажмите «Пропустить»:</b>", "optional": True},
		            {"type": "title", "field": "title", "optional": True, "question": "🎴 <b>Название для карточки:</b>"}
		        ]
		    },
		
		    "ada": {
		        "name": "Cardano",
		        "category": "wallets",
		        "icon": "ada",
		        "steps": [
		            {"type": "text", "field": "wallet_address", "question": "🔷 <b>Ваш Cardano адрес (ADA)</b>\n\n👇 <b>Вставьте адрес:</b>"},
		            {"type": "text", "field": "network", "question": "🌐 <b>Сеть</b>\n\n👇 <b>Напишите <code>Cardano</code> или нажмите «Пропустить»:</b>", "optional": True},
		            {"type": "title", "field": "title", "optional": True, "question": "🎴 <b>Название для карточки:</b>"}
		        ]
		    },
		
		    "dot": {
		        "name": "Polkadot",
		        "category": "wallets",
		        "icon": "dot",
		        "steps": [
		            {"type": "text", "field": "wallet_address", "question": "⏺️ <b>Ваш Polkadot адрес (DOT)</b>\n\n👇 <b>Вставьте адрес:</b>"},
		            {"type": "text", "field": "network", "question": "🌐 <b>Сеть</b>\n\n👇 <b>Напишите <code>Polkadot</code> или нажмите «Пропустить»:</b>", "optional": True},
		            {"type": "title", "field": "title", "optional": True, "question": "🎴 <b>Название для карточки:</b>"}
		        ]
		    },
		
		    "matic": {
		        "name": "Polygon",
		        "category": "wallets",
		        "icon": "matic",
		        "steps": [
		            {"type": "text", "field": "wallet_address", "question": "💜 <b>Ваш MATIC адрес</b>\n\n<blockquote>Для сети Polygon (адрес формата <code>0x...</code>).</blockquote>\n\n👇 <b>Вставьте адрес:</b>"},
		            {"type": "text", "field": "network", "question": "🌐 <b>Сеть</b>\n\n👇 <b>Напишите <code>Polygon (MATIC)</code> или нажмите «Пропустить»:</b>", "optional": True},
		            {"type": "title", "field": "title", "optional": True, "question": "🎴 <b>Название для карточки:</b>"}
		        ]
		    },
	

	# ===== ДОНАТЫ =====
	"patreon": {
		"name": "Patreon",
		"category": "donate",
		"icon": "patreon",
		"steps": [
			{
				"type": "text",
				"question": "🔗 <b>Введите название страницы Patreon</b>\n\n"
				            "Примеры:\n"
				            "• <code>mrbeast</code>\n"
				            "• <code>https://www.patreon.com/mrbeast</code>\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "username",
				"optional": False
			},
			{
				"type": "title",
				"question": "📝 <b>Название для карточки (можно пропустить)</b>\n\n"
				            "Например: <code>Поддержать на Patreon</code>\n"
				            "Если пропустите → будет просто «Patreon»",
				"field": "title",
				"optional": True
			}
		]
	},
	
	"boosty": {
		"name": "Boosty",
		"category": "donate",
		"icon": "boosty",
		"steps": [
			{
				"type": "text",
				"question": "🔗 <b>Введите название канала Boosty</b>\n\n"
				            "Примеры:\n"
				            "• <code>mrbeast</code>\n"
				            "• <code>https://boosty.to/mrbeast</code>\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "username",
				"optional": False
			},
			{
				"type": "title",
				"question": "📝 <b>Название для карточки (можно пропустить)</b>",
				"field": "title",
				"optional": True
			}
		]
	},
	
	"donationalerts": {
		"name": "Donation Alerts",
		"category": "donate",
		"icon": "donationalerts",
		"steps": [
			{
				"type": "text",
				"question": "🔔 <b>Введите ID на Donation Alerts</b>\n\n"
				            "Примеры:\n"
				            "• <code>mrbeast</code>\n"
				            "• <code>https://www.donationalerts.com/r/mrbeast</code>\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "username",
				"optional": False
			},
			{
				"type": "title",
				"question": "📝 <b>Название для карточки (можно пропустить)</b>",
				"field": "title",
				"optional": True
			}
		]
	},
	
	"kofi": {
		"name": "Ko-fi",
		"category": "donate",
		"icon": "kofi",
		"steps": [
			{
				"type": "text",
				"question": "☕ <b>Введите username Ko-fi</b>\n\n"
				            "Примеры:\n"
				            "• <code>mrbeast</code>\n"
				            "• <code>https://ko-fi.com/mrbeast</code>\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "username",
				"optional": False
			},
			{
				"type": "title",
				"question": "📝 <b>Название для карточки (можно пропустить)</b>",
				"field": "title",
				"optional": True
			}
		]
	},
	
	"buymeacoffee": {
		"name": "Buy Me a Coffee",
		"category": "donate",
		"icon": "buymeacoffee",
		"steps": [
			{
				"type": "text",
				"question": "☕ <b>Введите username Buy Me a Coffee</b>\n\n"
				            "Примеры:\n"
				            "• <code>mrbeast</code>\n"
				            "• <code>https://www.buymeacoffee.com/mrbeast</code>\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "username",
				"optional": False
			},
			{
				"type": "title",
				"question": "📝 <b>Название для карточки (можно пропустить)</b>",
				"field": "title",
				"optional": True
			}
		]
	},
	
	# ===== МАГАЗИНЫ =====
	"ozon": {
		"name": "Ozon",
		"category": "shops",
		"icon": "ozon",
		"steps": [
			{
				"type": "text",
				"question": "🛍️ <b>Введите ссылку на магазин или товар Ozon</b>\n\n"
				            "Примеры:\n"
				            "• <code>https://www.ozon.ru/seller/magazin-123</code>\n"
				            "• <code>ozon.ru/product/123456789</code>\n"
				            "• или просто ссылку целиком\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "url",
				"optional": False
			},
			{
				"type": "title",
				"question": "📝 <b>Название для кнопки (можно пропустить)</b>\n\n"
				            "Например: <code>Мой магазин на Ozon</code>\n"
				            "Если пропустите → будет просто «Ozon»",
				"field": "title",
				"optional": True
			}
		]
	},
	
	"wildberries": {
		"name": "Wildberries",
		"category": "shops",
		"icon": "wildberries",
		"steps": [
			{
				"type": "text",
				"question": "🛍️ <b>Введите ссылку на магазин или товар Wildberries</b>\n\n"
				            "Примеры:\n"
				            "• <code>https://www.wildberries.ru/seller/123456</code>\n"
				            "• <code>wildberries.ru/catalog/123456789</code>\n"
				            "• или просто ссылку целиком\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "url",
				"optional": False
			},
			{
				"type": "title",
				"question": "📝 <b>Название для кнопки (можно пропустить)</b>",
				"field": "title",
				"optional": True
			}
		]
	},
	
	"avito": {
		"name": "Avito",
		"category": "shops",
		"icon": "avito",
		"steps": [
			{
				"type": "text",
				"question": "📦 <b>Введите ссылку на объявление Avito</b>\n\n"
				            "Пример:\n"
				            "• <code>https://www.avito.ru/moskva/tovary/123456789</code>\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "url",
				"optional": False
			},
			{
				"type": "title",
				"question": "📝 <b>Название для кнопки (можно пропустить)</b>",
				"field": "title",
				"optional": True
			}
		]
	},
	
	"yandex_market": {
		"name": "Яндекс Маркет",
		"category": "shops",
		"icon": "yandex_market",
		"steps": [
			{
				"type": "text",
				"question": "🛒 <b>Введите ссылку на товар или магазин</b>\n\n"
				            "Примеры:\n"
				            "• <code>https://market.yandex.ru/product/123456789</code>\n"
				            "• <code>market.yandex.ru/cc/XXXXX</code>\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "url",
				"optional": False
			},
			{
				"type": "title",
				"question": "📝 <b>Название для кнопки (можно пропустить)</b>",
				"field": "title",
				"optional": True
			}
		]
	},
	
	"aliexpress": {
		"name": "AliExpress",
		"category": "shops",
		"icon": "aliexpress",
		"steps": [
			{
				"type": "text",
				"question": "🌏 <b>Введите ссылку на товар или магазин</b>\n\n"
				            "Примеры:\n"
				            "• <code>https://aliexpress.ru/item/1234567890.html</code>\n"
				            "• <code>aliexpress.com/store/1234567</code>\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "url",
				"optional": False
			},
			{
				"type": "title",
				"question": "📝 <b>Название для кнопки (можно пропустить)</b>",
				"field": "title",
				"optional": True
			}
		]
	},
	
	"kazanexpress": {
		"name": "KazanExpress",
		"category": "shops",
		"icon": "kazanexpress",
		"steps": [
			{
				"type": "text",
				"question": "📦 <b>Введите ссылку на товар</b>\n\n"
				            "Пример:\n"
				            "• <code>https://kazanexpress.ru/product/123456789</code>\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "url",
				"optional": False
			},
			{
				"type": "title",
				"question": "📝 <b>Название для кнопки (можно пропустить)</b>",
				"field": "title",
				"optional": True
			}
		]
	},
	
	"amazon": {
		"name": "Amazon",
		"category": "shops",
		"icon": "amazon",
		"steps": [
			{
				"type": "text",
				"question": "🇺🇸 <b>Введите ссылку на товар или магазин</b>\n\n"
				            "Примеры:\n"
				            "• <code>https://www.amazon.com/dp/B08N5WRWNW</code>\n"
				            "• <code>amazon.com/shop/username</code>\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "url",
				"optional": False
			},
			{
				"type": "title",
				"question": "📝 <b>Название для кнопки (можно пропустить)</b>",
				"field": "title",
				"optional": True
			}
		]
	},
	
	"ebay": {
		"name": "eBay",
		"category": "shops",
		"icon": "ebay",
		"steps": [
			{
				"type": "text",
				"question": "🇺🇸 <b>Введите ссылку на товар или магазин</b>\n\n"
				            "Примеры:\n"
				            "• <code>https://www.ebay.com/itm/123456789012</code>\n"
				            "• <code>ebay.com/usr/username</code>\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "url",
				"optional": False
			},
			{
				"type": "title",
				"question": "📝 <b>Название для кнопки (можно пропустить)</b>",
				"field": "title",
				"optional": True
			}
		]
	},
	
	"etsy": {
		"name": "Etsy",
		"category": "shops",
		"icon": "etsy",
		"steps": [
			{
				"type": "text",
				"question": "🎨 <b>Введите ссылку на магазин</b>\n\n"
				            "Примеры:\n"
				            "• <code>https://www.etsy.com/shop/shopname</code>\n"
				            "• <code>etsy.com/listing/123456789</code>\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "url",
				"optional": False
			},
			{
				"type": "title",
				"question": "📝 <b>Название для кнопки (можно пропустить)</b>",
				"field": "title",
				"optional": True
			}
		]
	},
	
	"shopify": {
		"name": "Shopify",
		"category": "shops",
		"icon": "shopify",
		"steps": [
			{
				"type": "text",
				"question": "🛒 <b>Введите ссылку на магазин</b>\n\n"
				            "Пример:\n"
				            "• <code>https://магазин.myshopify.com</code>\n\n"
				            "👇 <b>Вводите текст в поле чата бота</b>",
				"field": "url",
				"max_length": 500,
				"optional": False
			},
			{
				"type": "title",
				"question": "📝 <b>Название для кнопки (можно пропустить)</b>",
				"field": "title",
				"max_length": 100,
				"optional": True
			}
		]
	}
}




# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
def get_types_by_category(category: str) -> Dict[str, Dict[str, Any]]:
	"""Получить все типы ссылок для категории"""
	return {k: v for k, v in LINK_TYPES.items() if v.get("category") == category}


def get_step_count(link_type: str) -> int:
	"""Получить количество шагов для типа"""
	return len(LINK_TYPES.get(link_type, {}).get("steps", []))


def get_step(link_type: str, step_index: int) -> Optional[Dict[str, Any]]:
	"""Получить конкретный шаг"""
	steps = LINK_TYPES.get(link_type, {}).get("steps", [])
	if 0 <= step_index < len(steps):
		return steps[step_index]
	return None

	
