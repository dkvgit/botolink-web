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
		"name": "📱 Соцсети",
		"description": "Добавь ссылки на свои соцсети - они появятся на твоей странице красивыми карточками с иконками. YouTube, Instagram, TikTok, VK и другие",
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
	
	"wechat": {
		"name": "WeChat",
		"category": "messengers",
		"icon": "wechat",
		"steps": [
			{
				"type": "choice",
				"question": "🇨🇳 <b>Выберите способ связи в WeChat</b>\n\n"
				            "What to specify? / Что указать?\n\n"
				            "Вы можете добавить WeChat ID или QR-код для добавления в друзья",
				"options": [
					{
						"value": "id",
						"label": "🆔 WeChat ID",
						"next_step": 1,
						"description": "Укажите ваш WeChat ID для поиска"
					},
				
				]
			},
			{
				"type": "text",
				"question": "🆔 <b>WeChat ID</b>\n\n"
				            "Введите ваш WeChat ID:\n"
				            "• Латинские буквы и цифры\n"
				            "• Например: <code>wechat_user_123</code>\n"
				            "• Минимум 6 символов\n\n"
				            "👇 <b>Вводите текст</b>",
				"field": "wechat_id",
				"optional": False
			},
			
			{
				"type": "title",
				"question": "📝 <b>Название карточки WeChat</b>\n\n"
				            "Придумайте название для этой карточки\n"
				            "Например: <code>Мой WeChat</code> или <code>WeChat для Китая</code>\n\n"
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
				"type": "text",
				"question": "📞 <b>Номер телефона для Zalo</b>\n\n"
				            "Введите номер в любом формате:\n"
				            "• <code>84912345678</code> (только цифры)\n"
				            "• <code>+84 91 234 5678</code> (Вьетнам, с плюсом)\n"
				            "• <code>0912 345 678</code> (с пробелами)\n\n"
				            "👇 <b>Вводите текст</b>",
				"field": "phone",
				"optional": False
			},
			{
				"type": "title",
				"question": "📝 <b>Название карточки Zalo</b>\n\n"
				            "Придумайте название для этой карточки\n"
				            "Например: <code>Мой Zalo</code> или <code>Zalo для Вьетнама</code>\n\n"
				            "👇 <b>Вводите текст</b>",
				"field": "title",
				"optional": True,
				"skip_button": True
			}
		]
	},
	
	"max": {
		"name": "Max",
		"category": "messengers",
		"icon": "max",
		"steps": [
			{
				"type": "text",
				"question": "📞 <b>Номер телефона для Max</b>\n\n"
				            "Введите номер в любом формате:\n"
				            "• <code>7952544647</code> (только цифры)\n"
				            "• <code>+7 952-544-647</code> (Россия)\n"
				            "• <code>7 952 544 647</code> (с пробелами)\n\n"
				            "👇 <b>Вводите текст</b>",
				"field": "phone",
				"optional": False
			},
			{
				"type": "title",
				"question": "📝 <b>Название карточки Max</b>\n\n"
				            "Придумайте название для этой карточки\n"
				            "Например: <code>Мой Max</code> или <code>Max для работы</code>\n\n"
				            "👇 <b>Вводите текст</b>",
				"field": "title",
				"optional": True,
				"skip_button": True
			}
		]
	},
	
	"googlechat": {
		"name": "Google Chat",
		"category": "messengers",
		"icon": "googlechat",
		"steps": [
			{
				"type": "text",
				"question": "📧 <b>Email для Google Chat</b>\n\n"
				            "Введите email адрес в любом формате:\n"
				            "• <code>username@gmail.com</code>\n"
				            "• <code>user@work-domain.com</code> (для Workspace)\n"
				            "• <code>https://mail.google.com/chat/u/0/#chat/space/example</code> (ссылка на чат)\n\n"
				            "👇 <b>Вводите текст</b>",
				"field": "email",
				"optional": False
			},
			{
				"type": "title",
				"question": "📝 <b>Название карточки Google Chat</b>\n\n"
				            "Придумайте название для этой карточки\n"
				            "Например: <code>Рабочий чат</code> или <code>Google Chat</code>\n\n"
				            "👇 <b>Вводите текст</b>",
				"field": "title",
				"optional": True,
				"skip_button": True
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
	
	# ===== КРИПТА (биржи и кошельки) =====
	"binance": {
		"name": "Binance",
		"category": "crypto",
		"icon": "binance",
		"steps": [
			{"type": "choice", "question": "📊 Что указать?",
			 "options": [
				 {"value": "uid", "label": "UID", "next_step": 1},
				 {"value": "email", "label": "Email", "next_step": 2},
				 {"value": "wallet", "label": "Адрес кошелька", "next_step": 3}
			 ]},
			{"type": "text", "question": "Введите UID:", "field": "uid"},
			{"type": "email", "question": "Введите email:", "field": "email"},
			{"type": "text", "question": "Введите адрес кошелька:", "field": "wallet_address"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"bybit": {
		"name": "Bybit",
		"category": "crypto",
		"icon": "bybit",
		"steps": [
			{"type": "choice", "question": "📊 Что указать?",
			 "options": [
				 {"value": "uid", "label": "UID", "next_step": 1},
				 {"value": "email", "label": "Email", "next_step": 2}
			 ]},
			{"type": "text", "question": "Введите UID:", "field": "uid"},
			{"type": "email", "question": "Введите email:", "field": "email"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"okx": {
		"name": "OKX",
		"category": "crypto",
		"icon": "okx",
		"steps": [
			{"type": "choice", "question": "📊 Что указать?",
			 "options": [
				 {"value": "uid", "label": "UID", "next_step": 1},
				 {"value": "email", "label": "Email", "next_step": 2}
			 ]},
			{"type": "text", "question": "Введите UID:", "field": "uid"},
			{"type": "email", "question": "Введите email:", "field": "email"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"gateio": {
		"name": "Gate.io",
		"category": "crypto",
		"icon": "gateio",
		"steps": [
			{"type": "email", "question": "📧 Введите email:", "field": "email"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"kucoin": {
		"name": "KuCoin",
		"category": "crypto",
		"icon": "kucoin",
		"steps": [
			{"type": "email", "question": "📧 Введите email:", "field": "email"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"huobi": {
		"name": "Huobi",
		"category": "crypto",
		"icon": "huobi",
		"steps": [
			{"type": "email", "question": "📧 Введите email:", "field": "email"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"metamask": {
		"name": "Metamask",
		"category": "crypto",
		"icon": "metamask",
		"steps": [
			{"type": "text", "question": "🦊 Введите адрес кошелька:", "field": "wallet_address"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"trustwallet": {
		"name": "Trust Wallet",
		"category": "crypto",
		"icon": "trustwallet",
		"steps": [
			{"type": "text", "question": "🔐 Введите адрес кошелька:", "field": "wallet_address"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"coinbase": {
		"name": "Coinbase",
		"category": "crypto",
		"icon": "coinbase",
		"steps": [
			{"type": "choice", "question": "📊 Что указать?",
			 "options": [
				 {"value": "email", "label": "Email", "next_step": 1},
				 {"value": "wallet", "label": "Адрес кошелька", "next_step": 2}
			 ]},
			{"type": "email", "question": "Введите email:", "field": "email"},
			{"type": "text", "question": "Введите адрес кошелька:", "field": "wallet_address"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"kraken": {
		"name": "Kraken",
		"category": "crypto",
		"icon": "kraken",
		"steps": [
			{"type": "email", "question": "📧 Введите email:", "field": "email"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	# ===== КРИПТОВАЛЮТЫ (кошельки) =====
	"usdt": {
		"name": "USDT",
		"category": "crypto",
		"icon": "usdt",
		"steps": [
			{"type": "text", "question": "💰 Введите адрес USDT (TRC20):", "field": "wallet_address"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"btc": {
		"name": "Bitcoin",
		"category": "crypto",
		"icon": "btc",
		"steps": [
			{"type": "text", "question": "₿ Введите Bitcoin адрес:", "field": "wallet_address"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"eth": {
		"name": "Ethereum",
		"category": "crypto",
		"icon": "eth",
		"steps": [
			{"type": "text", "question": "Ξ Введите Ethereum адрес:", "field": "wallet_address"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"ton": {
		"name": "TON",
		"category": "crypto",
		"icon": "ton",
		"steps": [
			{"type": "text", "question": "💎 Введите TON адрес:", "field": "wallet_address"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"sol": {
		"name": "Solana",
		"category": "crypto",
		"icon": "sol",
		"steps": [
			{"type": "text", "question": "◎ Введите Solana адрес:", "field": "wallet_address"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"trx": {
		"name": "TRON",
		"category": "crypto",
		"icon": "trx",
		"steps": [
			{"type": "text", "question": "🔷 Введите TRON адрес:", "field": "wallet_address"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"bnb": {
		"name": "BNB (BSC)",
		"category": "crypto",
		"icon": "bnb",
		"steps": [
			{"type": "text", "question": "🟡 Введите BSC адрес:", "field": "wallet_address"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"doge": {
		"name": "Dogecoin",
		"category": "crypto",
		"icon": "doge",
		"steps": [
			{"type": "text", "question": "🐕 Введите Dogecoin адрес:", "field": "wallet_address"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"ltc": {
		"name": "Litecoin",
		"category": "crypto",
		"icon": "ltc",
		"steps": [
			{"type": "text", "question": "Ł Введите Litecoin адрес:", "field": "wallet_address"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"xrp": {
		"name": "Ripple",
		"category": "crypto",
		"icon": "xrp",
		"steps": [
			{"type": "text", "question": "💧 Введите XRP адрес:", "field": "wallet_address"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"ada": {
		"name": "Cardano",
		"category": "crypto",
		"icon": "ada",
		"steps": [
			{"type": "text", "question": "🔷 Введите Cardano адрес:", "field": "wallet_address"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"dot": {
		"name": "Polkadot",
		"category": "crypto",
		"icon": "dot",
		"steps": [
			{"type": "text", "question": "⏺️ Введите Polkadot адрес:", "field": "wallet_address"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
		]
	},
	
	"matic": {
		"name": "Polygon",
		"category": "crypto",
		"icon": "matic",
		"steps": [
			{"type": "text", "question": "💜 Введите MATIC адрес:", "field": "wallet_address"},
			{"type": "title", "question": "📝 Название для кнопки:", "field": "title"}
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


# Добавь если нужно еще из bank.py...

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
