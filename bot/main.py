# bot/main.py


import logging
import warnings

from telegram import BotCommand, BotCommandScopeChat, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, \
	ConversationHandler, ContextTypes
from telegram.warnings import PTBUserWarning

from admin_handlers import (
	admin_delete_user_now, admin_give_pro_execute, \
	admin_take_pro_now, admin_give_pro_menu, admin_list_users, \
	admin_user_detail
)
from bot.avatar_handler import refresh_avatar_command
# ===== ИМПОРТЫ ИЗ bank.py =====
from bot.bank import (
	# Главное меню
	back_to_countries,
	
	# Международные сервисы
	method_revolut, method_wise, method_paypal, method_swift,  # Обработчики ввода
	process_card_input, process_phone_input, process_iban_input,
	process_swift_input, process_wise_input,
	process_paypal_input,  # Подтверждение
	confirm_yes, confirm_no, revolut_choice_handler, process_revolut_bic, process_revolut_iban, process_revolut_address,
	process_revolut_correspondent, process_revolut_beneficiary, process_revolut_quick_input, revolut_start_full,
	process_revolut_login, revolut_skip_correspondent, revolut_skip_address, wise_choice_handler,
	process_wise_quick_input, process_wise_login, process_wise_beneficiary, process_wise_iban, process_wise_bic,
	process_wise_correspondent, wise_skip_correspondent, process_wise_address, wise_skip_address, wise_start_full,
	choose_country_from_constructor, back_to_add_link, process_idram_input, process_tbcpay_input, process_click_input,
	process_payme_input, process_kaspi_input, process_yoomoney_input, process_vkpay_input, process_monobank_input,
	method_yoomoney, method_vkpay, method_monobank, method_kaspi, method_payme, method_click, method_tbcpay,
	method_idram
)
# ===== БАНКОВСКИЙ МИР - УНИВЕРСАЛЬНЫЙ С ГАЛОЧКАМИ =====
from bot.bankworld import (
	show_country_methods,
	toggle_method,
	start_filling,
	process_field_input,
	save_all_methods, restart_filling
)
from bot.constructor import back_to_categories, back_to_types, cancel_constructor
from bot.constructor import start_constructor, handle_category, handle_type, handle_choice, handle_input, handle_skip
from bot.handlers import (
	# Базовые обработчики
	start_handler, help_handler, mysite_handler, qr_handler,
	links_handler, stats_handler, upgrade_handler, profile_handler,
	button_handler, cancel_handler,
	
	# Управление ссылками
	list_links_handler, edit_link_menu,
	show_categories,
	edit_link_title_start, edit_link_title_save,
	edit_link_url_start, edit_link_url_save,
	edit_link_icon_start, edit_link_icon_save,
	move_link, delete_link_confirm,  # Шаблоны
	templates_command,
	select_template_callback,
	unlock_pro_callback,
	activate_pro_callback,
	
	# Вспомогательные
	send_receipt_callback, admin_approve_payment, pro_info_callback,
	admin_payment_callback, change_username_start, save_new_nickname,
	edit_link_title_invalid, edit_link_url_invalid,
	delete_all_links_confirm, delete_all_links_execute
)
from bot.link_constructor import back_to_previous, wallets_and_crypto_menu, select_category, select_finance_subtype, \
	select_link_type, ask_for_multi_finance_details, process_multi_finance_data, select_crypto_network, add_link_url
# Добавить после from bot.link_constructor import select_category
from bot.states import *  # Импортируем все состояния
from bot.states import WAIT_CONSTRUCTOR_CATEGORY, WAIT_CONSTRUCTOR_TYPE, STEP_CHOICE, STEP_INPUT
# ===== ИМПОРТЫ ИЗ bankworld.py =====
from bot.states import WAIT_IDRAM, WAIT_TBCPAY, WAIT_CLICK, WAIT_PAYME, WAIT_KASPI, WAIT_MONOBANK, WAIT_VKPAY, \
	WAIT_YOOMONEY
from bot.states import WAIT_METHOD_SELECTION
from core.config import BOT_TOKEN, ADMIN_IDS

warnings.filterwarnings(
    action="ignore",
    message=r".*CallbackQueryHandler.*",
    category=PTBUserWarning
)


logging.basicConfig(
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	level=logging.INFO
)
logger = logging.getLogger(__name__)


async def post_init(application: Application):
	"""Установка команд бота с разделением прав через .env"""
	
	# 1. Общий список (для всех)
	base_commands = [
		
		BotCommand("start", "🏠 Главное меню"),
		
		BotCommand("bank", "🏦 Банки / Переводы (тест)"),
		
		BotCommand("mysite", "📋 Моя страница"),
		BotCommand("qr", "🔳 QR-код"),
		BotCommand("links", "🔗 Управление ссылками"),
		BotCommand("addlink", "➕ Добавить ссылку"),
		BotCommand("templates", "🎨 Выбрать шаблон"),
		BotCommand("stats", "📊 Статистика"),
		BotCommand("upgrade", "💳 Подписка"),
		BotCommand("profile", "⚙️ Профиль"),
		BotCommand("help", "❓ Помощь"),
	]
	
	await application.bot.set_my_commands(base_commands)
	print("✅ КОМАНДЫ УСТАНОВЛЕНЫ")
	
	await application.bot.set_my_commands(base_commands)
	
	# 2. Персональное меню для админа
	if ADMIN_IDS:
		for admin_id in ADMIN_IDS:
			try:
				admin_commands = base_commands + [
					BotCommand("admin", "👑 Админ-панель"),
					BotCommand("users", "👥 Список юзеров")
				]
				await application.bot.set_my_commands(
					commands=admin_commands,
					scope=BotCommandScopeChat(chat_id=admin_id)
				)
				logger.info(f"✅ Персональное меню установлено для админа ID: {admin_id}")
			except Exception as e:
				logger.error(f"❌ Не удалось установить меню для админа {admin_id}: {e}")
	
	print("--- КОМАНДЫ ОБНОВЛЕНЫ ---")




	
application = Application.builder() \
	.token(BOT_TOKEN) \
	.post_init(post_init) \
	.connect_timeout(30) \
	.read_timeout(30) \
	.write_timeout(30) \
	.pool_timeout(30) \
	.build()

# ===== 2. COMMAND HANDLERS =====
application.add_handler(CommandHandler("start", start_handler))
application.add_handler(CommandHandler("refresh_avatar", refresh_avatar_command))
application.add_handler(CommandHandler("help", help_handler))
application.add_handler(CommandHandler("mysite", mysite_handler))
application.add_handler(CommandHandler("qr", qr_handler))
application.add_handler(CommandHandler("links", links_handler))
application.add_handler(CommandHandler("stats", stats_handler))
application.add_handler(CommandHandler("upgrade", upgrade_handler))
application.add_handler(CommandHandler("profile", profile_handler))
application.add_handler(CommandHandler("templates", templates_command))
application.add_handler(CommandHandler("admin", admin_list_users))



"""Основная функция запуска бота"""
logger.info("🤖 Запуск бота...")






# ===== 1. CONVERSATION HANDLERS =====


# ============================================
#         НОВЫЙ КОНСТРУКТОР ССЫЛОК (ПОЛНЫЙ НАБОР СТЕЙТОВ)
# ============================================

# bot/main.py

constructor_conv = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_constructor, pattern="^add_link$"),
        CommandHandler("addlink", start_constructor)
    ],
    states={
        # === 1. БАЗОВЫЙ КОНСТРУКТОР (ОБЩИЕ ШАГИ) ===
        WAIT_CONSTRUCTOR_CATEGORY: [
            CallbackQueryHandler(handle_category, pattern="^cat_"),
            CallbackQueryHandler(back_to_categories, pattern="^back_to_categories$"),
            CallbackQueryHandler(cancel_constructor, pattern="^back_to_main$")
        ],
        WAIT_CONSTRUCTOR_TYPE: [
            CallbackQueryHandler(handle_type, pattern="^type_"),
            CallbackQueryHandler(back_to_categories, pattern="^back_to_categories$")
        ],
        STEP_CHOICE: [
            CallbackQueryHandler(handle_choice, pattern="^choice_"),
            CallbackQueryHandler(back_to_types, pattern="^back_to_types$"),
            CallbackQueryHandler(back_to_categories, pattern="^back_to_categories$")
        ],
        STEP_INPUT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input),
            CallbackQueryHandler(back_to_types, pattern="^back_to_types$"),
            CallbackQueryHandler(back_to_previous, pattern="^back_to_previous$"),
            CallbackQueryHandler(handle_skip, pattern="^skip_step$"),
            CallbackQueryHandler(back_to_categories, pattern="^back_to_categories$")
        ],

        # === 2. ФИНАНСЫ, КРИПТО И ВЫБОР КАТЕГОРИЙ ===
        SELECT_CATEGORY: [
            CallbackQueryHandler(wallets_and_crypto_menu, pattern="^cat_crypto$"),
            CallbackQueryHandler(select_category, pattern="^cat_wallets$"),
            CallbackQueryHandler(select_category, pattern="^cat_stocks$"),
            CallbackQueryHandler(select_category, pattern="^cat_transfers$"),
            CallbackQueryHandler(show_country_methods, pattern="^country_.*$"),
            CallbackQueryHandler(back_to_categories, pattern="^back_to_categories$"),
        ],
        SELECT_CRYPTO_NETWORK: [
            CallbackQueryHandler(select_crypto_network, pattern="^net_"),
            CallbackQueryHandler(back_to_categories, pattern="^back_to_categories$"),
        ],
        ADD_MULTI_FINANCE_DATA: [
            CallbackQueryHandler(ask_for_multi_finance_details, pattern="^net_"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_multi_finance_data),
            CallbackQueryHandler(back_to_categories, pattern="^back_to_categories$"),
        ],

        # === 3. УНИВЕРСАЛЬНЫЕ БАНКОВСКИЕ СТЕЙТЫ (УБИРАЕМ ТУПИК 502) ===
        WAIT_METHOD_SELECTION: [
            CallbackQueryHandler(toggle_method, pattern="^method_[a-z]+_[a-z_]+$"),
            CallbackQueryHandler(start_filling, pattern="^start_filling$"),
            CallbackQueryHandler(back_to_categories, pattern="^back_to_categories$")
        ],
        WAIT_FIELD_INPUT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_field_input),
            CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$"),
            CallbackQueryHandler(back_to_categories, pattern="^back_to_categories$")
        ],
        WAIT_FILLING_DATA: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_field_input),
            CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$"),
            CallbackQueryHandler(back_to_categories, pattern="^back_to_categories$")
        ],
        WAIT_FINAL_CONFIRM: [
            CallbackQueryHandler(save_all_methods, pattern="^save_all_methods$"),
            CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$"),
	        CallbackQueryHandler(restart_filling, pattern="^restart_filling$"),  # ← это должно быть
            CallbackQueryHandler(back_to_categories, pattern="^back_to_categories$")
        ],

        # === 4. СНГ И МЕЖДУНАРОДНЫЕ БАНКИ (ВВОД ДАННЫХ) ===
        WAIT_RUSSIA_CARD: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_card_input),
            CallbackQueryHandler(back_to_categories, pattern="^back_to_categories$")
        ],
        WAIT_RUSSIA_PHONE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_phone_input),
            CallbackQueryHandler(back_to_categories, pattern="^back_to_categories$")
        ],
        WAIT_KAZAKHSTAN_CARD: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_card_input),
            CallbackQueryHandler(back_to_categories, pattern="^back_to_categories$")
        ],
        WAIT_KAZAKHSTAN_PHONE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_phone_input),
            CallbackQueryHandler(back_to_categories, pattern="^back_to_categories$")
        ],
        WAIT_UKRAINE_CARD: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_card_input),
            CallbackQueryHandler(back_to_categories, pattern="^back_to_categories$")
        ],
        WAIT_UZBEKISTAN_CARD: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_card_input),
            CallbackQueryHandler(back_to_categories, pattern="^back_to_categories$")
        ],
        WAIT_EUROPE_IBAN: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_iban_input),
            CallbackQueryHandler(back_to_categories, pattern="^back_to_categories$")
        ],
        WAIT_USA_ACH: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_card_input),
            CallbackQueryHandler(back_to_categories, pattern="^back_to_categories$")
        ],
        
        # Специальные кошельки
        WAIT_YOOMONEY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_yoomoney_input),
            CallbackQueryHandler(back_to_categories, pattern="^back_to_categories$")
        ],
        WAIT_VKPAY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_vkpay_input),
            CallbackQueryHandler(back_to_categories, pattern="^back_to_categories$")
        ],
        WAIT_KASPI: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_kaspi_input),
            CallbackQueryHandler(back_to_categories, pattern="^back_to_categories$")
        ],
        WAIT_PAYME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_payme_input),
            CallbackQueryHandler(back_to_categories, pattern="^back_to_categories$")
        ],

        # === 5. REVOLUT & WISE (СЛОЖНЫЕ ЦЕПОЧКИ) ===
        WAIT_REVOLUT_CHOICE: [
            CallbackQueryHandler(revolut_choice_handler, pattern="^revolut_(quick|full)$"),
            CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$"),
            CallbackQueryHandler(back_to_categories, pattern="^back_to_categories$")
        ],
        WAIT_REVOLUT_LOGIN: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_revolut_login),
            CallbackQueryHandler(back_to_categories, pattern="^back_to_categories$")
        ],
        WAIT_REVOLUT_IBAN: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_revolut_iban),
            CallbackQueryHandler(back_to_categories, pattern="^back_to_categories$")
        ],
        
        WAIT_WISE_CHOICE: [
            CallbackQueryHandler(wise_choice_handler, pattern="^wise_(quick|full)$"),
            CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$"),
            CallbackQueryHandler(back_to_categories, pattern="^back_to_categories$")
        ],
        WAIT_WISE_LOGIN: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_wise_login),
            CallbackQueryHandler(back_to_categories, pattern="^back_to_categories$")
        ],
        WAIT_WISE_IBAN: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_wise_iban),
            CallbackQueryHandler(back_to_categories, pattern="^back_to_categories$")
        ],
    },
    fallbacks=[
        CommandHandler("cancel", cancel_constructor),
        CallbackQueryHandler(cancel_constructor, pattern="^cancel$"),
        CallbackQueryHandler(cancel_constructor, pattern="^back_to_main$")
    ],
    name="constructor_conversation",
    per_user=True,
    per_chat=True,
    allow_reentry=True
)
print(f"DEBUG: WAIT_FIELD_INPUT is {WAIT_FIELD_INPUT}")
print(f"DEBUG: process_field_input is {process_field_input}")

# Добавляем конструктор
application.add_handler(constructor_conv)

print(f"✅ Конструктор создан: constructor_conversation")
print(f"  • states: {[WAIT_CONSTRUCTOR_CATEGORY, WAIT_CONSTRUCTOR_TYPE, STEP_CHOICE, STEP_INPUT]}")
print("🔧" * 30 + "\n")

# СМЕНА НИКА
change_nick_conv = ConversationHandler(
	entry_points=[
		CallbackQueryHandler(change_username_start, pattern="^change_nick$")
	],
	states={
		"WAITING_FOR_NICKNAME": [
			MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_nickname),
			CallbackQueryHandler(cancel_handler, pattern="^cancel$")
		],
	},
	fallbacks=[
		CommandHandler("cancel", cancel_handler),
		CommandHandler("start", start_handler)
	],
	
	per_chat=True,
	allow_reentry=True,
	name="change_nick_conversation"
)
application.add_handler(change_nick_conv)

# РЕДАКТИРОВАНИЕ НАЗВАНИЯ
edit_title_conv = ConversationHandler(
	entry_points=[CallbackQueryHandler(edit_link_title_start, pattern="^edit_title_")],
	states={
		EDIT_LINK_TITLE: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, edit_link_title_save),
			MessageHandler(filters.ALL, edit_link_title_invalid),
			CallbackQueryHandler(cancel_handler, pattern="^cancel$")
		],
	},
	fallbacks=[
		CommandHandler("cancel", cancel_handler),
		CallbackQueryHandler(cancel_handler, pattern="^cancel$")
	],
	
	per_chat=True,
	allow_reentry=True,
	name="edit_title_conversation"
)
application.add_handler(edit_title_conv)

# Редактирование URL
edit_url_conv = ConversationHandler(
	entry_points=[CallbackQueryHandler(edit_link_url_start, pattern="^edit_url_")],
	states={
		EDIT_LINK_URL: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, edit_link_url_save),
			MessageHandler(filters.ALL, edit_link_url_invalid),
			CallbackQueryHandler(cancel_handler, pattern="^cancel$")
		],
	},
	fallbacks=[
		CommandHandler("cancel", cancel_handler),
		CallbackQueryHandler(cancel_handler, pattern="^cancel$")
	],
	
	per_chat=True,
	allow_reentry=True,
	name="edit_url_conversation"
)
application.add_handler(edit_url_conv)

# РЕДАКТИРОВАНИЕ ИКОНКИИ
edit_icon_conv = ConversationHandler(
	entry_points=[CallbackQueryHandler(edit_link_icon_start, pattern="^edit_icon_")],
	states={
		EDIT_LINK_ICON: [
			CallbackQueryHandler(edit_link_icon_save, pattern="^change_icon_"),
			CallbackQueryHandler(cancel_handler, pattern="^cancel$")
		],
	},
	fallbacks=[
		CommandHandler("cancel", cancel_handler),
		CallbackQueryHandler(cancel_handler, pattern="^cancel$")
	],
	per_message=True,
	per_chat=True,
	allow_reentry=True,
	name="edit_icon_conversation"
)
application.add_handler(edit_icon_conv)




# БАНКОВСКИЙ ДИАЛОГ
bank_world_conv = ConversationHandler(
	entry_points=[
		CallbackQueryHandler(show_country_methods, pattern="^country_.*$"),
		CallbackQueryHandler(select_link_type, pattern="^type_"),  # ← ДОБАВИТЬ!
		CallbackQueryHandler(method_paypal, pattern="^method_paypal$"),
		CallbackQueryHandler(method_wise, pattern="^method_wise$"),
		CallbackQueryHandler(method_revolut, pattern="^method_revolut$"),
		CallbackQueryHandler(method_swift, pattern="^method_swift$"),
		CallbackQueryHandler(method_yoomoney, pattern="^method_yoomoney$"),
		CallbackQueryHandler(method_vkpay, pattern="^method_vkpay$"),
		CallbackQueryHandler(method_monobank, pattern="^method_monobank$"),
		CallbackQueryHandler(method_kaspi, pattern="^method_kaspi$"),
		CallbackQueryHandler(method_payme, pattern="^method_payme$"),
		CallbackQueryHandler(method_click, pattern="^method_click$"),
		CallbackQueryHandler(method_tbcpay, pattern="^method_tbcpay$"),
		CallbackQueryHandler(method_idram, pattern="^method_idram$"),
	],
	
	states={
		SELECT_CATEGORY: [
			CallbackQueryHandler(wallets_and_crypto_menu, pattern="^cat_crypto$"),  # Вход в меню
			CallbackQueryHandler(select_category, pattern="^cat_wallets$"),  # ← ДОБАВИТЬ
			CallbackQueryHandler(select_category, pattern="^cat_stocks$"),  # ← ДОБАВИТЬ
			CallbackQueryHandler(select_category,
			                     pattern="^cat_(?!wallets_and_crypto_menu|social|messengers|wallets|stocks|other).*$"),
			
			# Банки по странам
			CallbackQueryHandler(show_country_methods, pattern="^country_.*$"),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$"),
			
			# Прямые методы
			CallbackQueryHandler(method_paypal, pattern="^method_paypal$"),
			CallbackQueryHandler(method_wise, pattern="^method_wise$"),
			# ... остальные method_* обработчики
		],
		
		SELECT_FINANCE_SUBTYPE: [  # число 11
			CallbackQueryHandler(select_finance_subtype, pattern="^fin_sub_"),
			CallbackQueryHandler(select_category, pattern="^cat_stocks$"),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$"),
		],
		
		ADD_MULTI_FINANCE_DATA: [  # число 28
			CallbackQueryHandler(ask_for_multi_finance_details, pattern="^net_"),
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_multi_finance_data),
			CallbackQueryHandler(select_category, pattern="^cat_stocks$"),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$"),
		],
		
		ADD_LINK_URL: [  # число 5
			MessageHandler(filters.TEXT & ~filters.COMMAND, add_link_url),  # вторую версию
			CallbackQueryHandler(select_category, pattern="^cat_wallets$"),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$"),
		],
		
		SELECT_CRYPTO_NETWORK: [  # число 6
			CallbackQueryHandler(select_crypto_network, pattern="^net_"),
			CallbackQueryHandler(select_category, pattern="^cat_wallets$"),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$"),
		],
		
		WAIT_YOOMONEY: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_yoomoney_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$"),
		],
		WAIT_VKPAY: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_vkpay_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$"),
		],
		WAIT_MONOBANK: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_monobank_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$"),
		],
		WAIT_KASPI: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_kaspi_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$"),
		],
		WAIT_PAYME: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_payme_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$"),
		],
		WAIT_CLICK: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_click_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$"),
		],
		WAIT_TBCPAY: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_tbcpay_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$"),
		],
		WAIT_IDRAM: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_idram_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$"),
		],
		
		SELECT_COUNTRY: [
			CallbackQueryHandler(back_to_countries, pattern="^transfers$"),
		],
		
		WAIT_METHOD_SELECTION: [
			CallbackQueryHandler(toggle_method, pattern="^method_[a-z]+_[a-z_]+$"),
			CallbackQueryHandler(start_filling, pattern="^start_filling$"),
			CallbackQueryHandler(show_country_methods, pattern="^back_to_countries$"),
		],
		
		WAIT_REVOLUT_CHOICE: [
			CallbackQueryHandler(revolut_choice_handler, pattern="^revolut_quick$"),
			CallbackQueryHandler(revolut_choice_handler, pattern="^revolut_full$"),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_REVOLUT_QUICK: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_revolut_quick_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_REVOLUT_FULL: [
			CallbackQueryHandler(revolut_start_full, pattern="^revolut_start_full$"),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_REVOLUT_LOGIN: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_revolut_login),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_REVOLUT_BENEFICIARY: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_revolut_beneficiary),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_REVOLUT_IBAN: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_revolut_iban),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_REVOLUT_BIC: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_revolut_bic),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_REVOLUT_CORRESPONDENT: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_revolut_correspondent),
			CallbackQueryHandler(revolut_skip_correspondent, pattern="^revolut_skip_correspondent$"),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_REVOLUT_ADDRESS: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_revolut_address),
			CallbackQueryHandler(revolut_skip_address, pattern="^revolut_skip_address$"),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_WISE_CHOICE: [
			CallbackQueryHandler(wise_choice_handler, pattern="^wise_quick$"),
			CallbackQueryHandler(wise_choice_handler, pattern="^wise_full$"),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_WISE_QUICK: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_wise_quick_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_WISE_FULL: [
			CallbackQueryHandler(wise_start_full, pattern="^wise_start_full$"),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_WISE_LOGIN: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_wise_login),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_WISE_BENEFICIARY: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_wise_beneficiary),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_WISE_IBAN: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_wise_iban),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_WISE_BIC: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_wise_bic),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_WISE_CORRESPONDENT: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_wise_correspondent),
			CallbackQueryHandler(wise_skip_correspondent, pattern="^wise_skip_correspondent$"),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_WISE_ADDRESS: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_wise_address),
			CallbackQueryHandler(wise_skip_address, pattern="^wise_skip_address$"),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_RUSSIA_CARD: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_card_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_RUSSIA_PHONE: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_phone_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_RUSSIA_DETAILS: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_card_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_BELARUS_CARD: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_card_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_BELARUS_ERIP: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_phone_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_BELARUS_IBAN: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_iban_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_KAZAKHSTAN_CARD: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_card_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_KAZAKHSTAN_PHONE: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_phone_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_KAZAKHSTAN_IBAN: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_iban_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_UKRAINE_CARD: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_card_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_UKRAINE_IBAN: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_iban_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_UZBEKISTAN_CARD: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_card_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_UZBEKISTAN_PHONE: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_phone_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_TAJIKISTAN_CARD: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_card_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_TAJIKISTAN_PHONE: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_phone_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_KYRGYZSTAN_CARD: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_card_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_KYRGYZSTAN_PHONE: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_phone_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_TURKMENISTAN_CARD: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_card_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_ARMENIA_CARD: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_card_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_ARMENIA_IBAN: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_iban_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_AZERBAIJAN_CARD: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_card_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_AZERBAIJAN_IBAN: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_iban_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_GEORGIA_CARD: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_card_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_GEORGIA_IBAN: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_iban_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_MOLDOVA_CARD: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_card_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_MOLDOVA_IBAN: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_iban_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_EUROPE_CARD: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_card_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_EUROPE_IBAN: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_iban_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_USA_CARD: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_card_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_USA_ACH: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_card_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_USA_WIRE: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_card_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		
		WAIT_PAYPAL: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_paypal_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$"),
		],
		
		WAIT_WISE: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_wise_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$"),
		],
		
		WAIT_SWIFT: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_swift_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$"),
		],
		
		WAIT_IBAN: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_iban_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$"),
		],
		
		CONFIRM_PAYMENT: [
			CallbackQueryHandler(confirm_yes, pattern="^confirm_yes$"),
			CallbackQueryHandler(confirm_no, pattern="^confirm_no$")
		],
		
		WAIT_FILLING_DATA: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_field_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		WAIT_FIELD_INPUT: [
			MessageHandler(filters.TEXT & ~filters.COMMAND, process_field_input),
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
		WAIT_FINAL_CONFIRM: [
			CallbackQueryHandler(save_all_methods, pattern="^save_all_methods$"),
			CallbackQueryHandler(restart_filling, pattern="^restart_filling$"),  # ← ДОБАВЬ ЭТО
			CallbackQueryHandler(back_to_countries, pattern="^back_to_countries$")
		],
	},
	fallbacks=[
		CallbackQueryHandler(back_to_countries, pattern="^back_to_countries"),
		CommandHandler("cancel", cancel_handler),
	],
	name="bank_world_conv",
	per_chat=True,
	per_user=True,
	per_message=True,
)
print(f"🔧 Регистрируем bank_world_conv с состоянием WAIT_FIELD_INPUT={WAIT_FIELD_INPUT}")
print(f"   Обработчик WAIT_FIELD_INPUT: {bank_world_conv.states.get(WAIT_FIELD_INPUT)}")
application.add_handler(bank_world_conv)  # Сначала наш новый
print(f"✅ bank_world_conv добавлен, WAIT_FIELD_INPUT={WAIT_FIELD_INPUT}")


# ===== 3. CALLBACK HANDLERS =====
# В main.py, в секции обычных CallbackQueryHandler (после всех ConversationHandler)
application.add_handler(CallbackQueryHandler(back_to_categories, pattern="^back_to_categories$"))
application.add_handler(
	CallbackQueryHandler(back_to_add_link, pattern="^back_to_add_link$")
)
application.add_handler(CallbackQueryHandler(choose_country_from_constructor, pattern="^transfers$"))

application.add_handler(CallbackQueryHandler(cancel_handler, pattern="cancel"))

# application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

application.add_handler(CallbackQueryHandler(show_categories, pattern="^show_categories$"))
application.add_handler(CallbackQueryHandler(list_links_handler, pattern="^list_links$"))
application.add_handler(CallbackQueryHandler(list_links_handler, pattern="^list_links$"))
application.add_handler(CallbackQueryHandler(stats_handler, pattern="^stats$"))  # ← ДОБАВИТЬ СЮДА
application.add_handler(CallbackQueryHandler(edit_link_menu, pattern="^edit_link_"))
application.add_handler(CallbackQueryHandler(edit_link_menu, pattern="^edit_link_"))
application.add_handler(CallbackQueryHandler(move_link, pattern="^move_"))
application.add_handler(CallbackQueryHandler(select_template_callback, pattern="^select_template_"))
application.add_handler(CallbackQueryHandler(templates_command, pattern="^back_to_templates$"))
application.add_handler(CallbackQueryHandler(upgrade_handler, pattern="^(upg_|pay_|show_methods|back_to_upgrade)"))
application.add_handler(CallbackQueryHandler(admin_approve_payment, pattern="^admin_approve_"))
application.add_handler(CallbackQueryHandler(activate_pro_callback, pattern="^activate_pro$"))
application.add_handler(CallbackQueryHandler(unlock_pro_callback, pattern="^unlock_pro$"))
application.add_handler(CallbackQueryHandler(send_receipt_callback, pattern="^send_receipt$"))
application.add_handler(CallbackQueryHandler(pro_info_callback, pattern="^pro_info$"))
application.add_handler(CallbackQueryHandler(admin_payment_callback, pattern="^admin_(approve|reject)_"))

# АДМИН-ПАНЕЛЬ

application.add_handler(CallbackQueryHandler(admin_list_users, pattern="^admin_list_users$"))
application.add_handler(CallbackQueryHandler(admin_user_detail, pattern="^admin_user_"))
application.add_handler(CallbackQueryHandler(admin_give_pro_menu, pattern="^admin_give_pro_menu$"))
application.add_handler(CallbackQueryHandler(admin_give_pro_execute, pattern="^admin_give_pro_(30|90|365)$"))
application.add_handler(CallbackQueryHandler(admin_take_pro_now, pattern="^admin_take_pro_now$"))
application.add_handler(CallbackQueryHandler(admin_delete_user_now, pattern="^admin_delete_user_now$"))

# application.add_handler(CallbackQueryHandler(select_category, pattern="^cat_"))
application.add_handler(CallbackQueryHandler(delete_all_links_confirm, pattern="^delete_all_links$"))
application.add_handler(CallbackQueryHandler(delete_all_links_execute, pattern="^confirm_delete_all$"))
application.add_handler(CallbackQueryHandler(delete_link_confirm, pattern=r"^delete_\d+$"))

# Универсальный обработчик (ВСЕГДА ПОСЛЕДНИЙ)
application.add_handler(CallbackQueryHandler(button_handler))
logger.info("✅ Все хендлеры зарегистрированы.")

async def debug_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"🕵️ ГЛОБАЛЬНЫЙ ПЕРЕХВАТ: Юзер {update.effective_user.id} прислал: {update.message.text}")
    # Проверим, какой стейт сейчас у юзера в конструкторе
    # Это покажет, "видит" ли система активный диалог
    return

application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, debug_all_messages), group=10)



async def run_local():
    # 1. Используем уже созданный в этом файле объект application
    # 2. Инициализируем и запускаем Polling
    async with application:
        await application.initialize()
        await application.start()
        
        # Удаляем вебхук, чтобы Telegram переключился на твой комп
        await application.bot.delete_webhook(drop_pending_updates=True)
        
        # Запускаем прослушивание
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        logger.info("🚀 [LOCAL] Бот запущен в режиме POLLING")
        
        try:
            # Держим процесс активным
            while True:
                await asyncio.sleep(3600)
        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.info("👋 Остановка...")
            if application.updater.running:
                await application.updater.stop()
            if application.running:
                await application.stop()


if __name__ == "__main__":
    import asyncio
    try:
        # Запускаем локальную функцию
        asyncio.run(run_local())
    except (KeyboardInterrupt, SystemExit):
        print("👋 Бот полностью остановлен.")
