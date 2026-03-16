# bot/states.py

# ============================================
# СОСТОЯНИЯ ДЛЯ ДОБАВЛЕНИЯ ССЫЛКИ (1-29)
# ============================================
ADD_LINK_TITLE = 1  # Ввод названия ссылки
ADD_LINK_URL = 2  # Ввод URL ссылки
ADD_LINK_ICON = 3  # Выбор иконки

# --- Состояния для редактирования ---
EDIT_LINK_SELECT = 4  # Выбор ссылки для редактирования
EDIT_LINK_TITLE = 5  # Редактирование названия
EDIT_LINK_URL = 6  # Редактирование URL
EDIT_LINK_ICON = 7  # Редактирование иконки

# --- Состояния для конструктора ссылок ---
SELECT_LINK_TYPE = 10  # Выбор: Обычная или Реквизиты (PRO)
SELECT_FINANCE_SUBTYPE = 11  # Выбор: Карта, BTC, USDT и т.д.

SELECT_CATEGORY = 20  # Шаг 1: Выбор категории
ADD_LINK_DESCRIPTION = 21  # Шаг 6: Ввод описания (для соцсетей)
SELECT_PRESET = 22  # Выбор предустановленного типа ссылки
ADD_CUSTOM_CURRENCY_NAME = 25  # Ввод названия своей валютыif category == "transfers":
SELECT_CRYPTO_NETWORK = 26  # Выбор сети из списка (кнопки)
WAIT_CUSTOM_NETWORK = 27  # Ввод своей сети текстом
ADD_MULTI_FINANCE_DATA = 28  # Добавление нескольких финансовых данных
FINALIZE_FINANCE_LINK = 29  # Финал для бирж

# ============================================
# ПРОФИЛЬ И НАСТРОЙКИ (30-49)
# ============================================
WAITING_FOR_NICKNAME = 30  # Смена ника

# ============================================
# БАНКОВСКИЕ РЕКВИЗИТЫ И ПЕРЕВОДЫ (100-299)
# ============================================

# --- Выбор страны и метода (100-109) ---
SELECT_COUNTRY = 100  # Выбор страны
SELECT_METHOD = 101  # Выбор метода в стране
BACK_TO_COUNTRIES = 102  # Назад к списку стран

# ===== РОССИЯ (110-119) =====
WAIT_RUSSIA_CARD = 110  # Ввод карты РФ
WAIT_RUSSIA_PHONE = 111  # Ввод телефона для СБП
WAIT_RUSSIA_DETAILS = 112  # Ввод реквизитов (БИК + счет)

# ===== БЕЛАРУСЬ (120-129) =====
WAIT_BELARUS_CARD = 120  # Ввод карты Белкарт/Visa
WAIT_BELARUS_ERIP = 121  # Ввод кода ЕРИП
WAIT_BELARUS_IBAN = 122  # Ввод IBAN

# ===== КАЗАХСТАН (130-139) =====
WAIT_KAZAKHSTAN_CARD = 130  # Ввод карты Kaspi/Halyk
WAIT_KAZAKHSTAN_PHONE = 131  # Ввод телефона (Kaspi Gold)
WAIT_KAZAKHSTAN_IBAN = 132  # Ввод IBAN

# ===== УКРАИНА (140-149) =====
WAIT_UKRAINE_CARD = 140  # Ввод карты (Приват, Монобанк)
WAIT_UKRAINE_IBAN = 141  # Ввод IBAN

# ===== УЗБЕКИСТАН (150-159) =====
WAIT_UZBEKISTAN_CARD = 150  # Ввод карты Uzcard/Humo
WAIT_UZBEKISTAN_PHONE = 151  # Ввод телефона (Payme, Click)

# ===== ТАДЖИКИСТАН (160-169) =====
WAIT_TAJIKISTAN_CARD = 160  # Ввод карты Корти Милли
WAIT_TAJIKISTAN_PHONE = 161  # Ввод телефона

# ===== КЫРГЫЗСТАН (170-179) =====
WAIT_KYRGYZSTAN_CARD = 170  # Ввод карты Элкарт
WAIT_KYRGYZSTAN_PHONE = 171  # Ввод телефона

# ===== ТУРКМЕНИСТАН (180-189) =====
# WAIT_TURKMENISTAN_CARD = 180     # Ввод карты

# ===== АРМЕНИЯ (190-199) =====
WAIT_ARMENIA_CARD = 190  # Ввод карты Ардшинбанк и др.
WAIT_ARMENIA_IBAN = 191  # Ввод IBAN

# ===== АЗЕРБАЙДЖАН (200-209) =====
WAIT_AZERBAIJAN_CARD = 200  # Ввод карты
WAIT_AZERBAIJAN_IBAN = 201  # Ввод IBAN

# ===== ГРУЗИЯ (210-219) =====
WAIT_GEORGIA_CARD = 210  # Ввод карты (TBC, Bank of Georgia)
WAIT_GEORGIA_IBAN = 211  # Ввод IBAN

# ===== МОЛДОВА (220-229) =====
WAIT_MOLDOVA_CARD = 220  # Ввод карты
WAIT_MOLDOVA_IBAN = 221  # Ввод IBAN

# ===== ЕВРОПА (230-239) =====
WAIT_EUROPE_CARD = 230  # Ввод карты (Visa/Mastercard EU)
WAIT_EUROPE_IBAN = 231  # Ввод IBAN (SEPA)

# ===== США И КАНАДА (240-249) =====
WAIT_USA_CARD = 240  # Ввод карты (Visa/Mastercard/Amex)
WAIT_USA_ACH = 241  # ACH (Routing + Account)
WAIT_USA_WIRE = 242  # Wire transfer
WAIT_USA_IBAN = 243  # IBAN (редко используется)

# ===== МЕЖДУНАРОДНЫЕ СЕРВИСЫ (250-259) =====
WAIT_REVOLUT = 250  # Ввод логина Revolut (@username)
WAIT_WISE = 251  # Ввод ссылки Wise или IBAN
WAIT_PAYPAL = 252  # Ввод email или ссылки PayPal
WAIT_SWIFT = 253  # Ввод SWIFT реквизитов (полные)
WAIT_IBAN = 254  # Ввод IBAN (отдельно)

# ===== ДРУГИЕ СТРАНЫ (260-269) =====
WAIT_OTHER_COUNTRY = 260  # Другая страна
WAIT_OTHER_DETAILS = 261  # Ввод реквизитов для другой страны

# ===== ПОДТВЕРЖДЕНИЕ (270-279) =====
CONFIRM_PAYMENT = 270  # Подтверждение введенных данных
EDIT_PAYMENT = 271  # Редактирование данных

# ===== REVOLUT СТЕЙТЫ (280-289) =====
WAIT_REVOLUT_CHOICE = 280  # Выбор типа (быстрый/полный)
WAIT_REVOLUT_QUICK = 281  # Быстрый ввод (только логин)
WAIT_REVOLUT_FULL = 282  # Начало полного ввода
WAIT_REVOLUT_LOGIN = 283  # Логин (шаг 1/6)
WAIT_REVOLUT_BENEFICIARY = 284  # Получатель (шаг 2/6)
WAIT_REVOLUT_IBAN = 285  # IBAN (шаг 3/6)
WAIT_REVOLUT_BIC = 286  # BIC/SWIFT (шаг 4/6)
WAIT_REVOLUT_CORRESPONDENT = 287  # Correspondent (шаг 5/6)
WAIT_REVOLUT_ADDRESS = 288  # Адрес банка (шаг 6/6)

# ===== WISE СТЕЙТЫ (290-299) =====
WAIT_WISE_CHOICE = 290  # Выбор типа (быстрый/полный)
WAIT_WISE_QUICK = 291  # Быстрый ввод (только логин)
WAIT_WISE_LOGIN = 292  # Логин (шаг 1/6)
WAIT_WISE_BENEFICIARY = 293  # Получатель (шаг 2/6)
WAIT_WISE_IBAN = 294  # IBAN (шаг 3/6)
WAIT_WISE_BIC = 295  # BIC/SWIFT (шаг 4/6)
WAIT_WISE_CORRESPONDENT = 296  # Correspondent (шаг 5/6)
WAIT_WISE_ADDRESS = 297  # Адрес банка (шаг 6/6)
WAIT_WISE_FULL = 298  # Начало полного ввода

WAIT_METHOD_SELECTION = 500  # Тот самый стейт 500 из лога
WAIT_FILLING_DATA = 501
WAIT_FIELD_INPUT = 502
WAIT_FINAL_CONFIRM = 503

# Туркменистан (уже есть в твоем списке, убедись что у него есть значение)
WAIT_TURKMENISTAN_CARD = 504

# Универсальные методы (без страны)
WAIT_YOOMONEY = 505
WAIT_VKPAY = 506
WAIT_MONOBANK = 507
WAIT_KASPI = 508
WAIT_PAYME = 509
WAIT_CLICK = 510
WAIT_TBCPAY = 511
WAIT_IDRAM = 512

# Состояния для соцсетей
WAIT_SOCIAL_STEP1 = 601  # Для первого шага (название канала, username и т.д.)
WAIT_SOCIAL_URL = 602  # Для второго шага (ссылка)

# В states.py добавить:
WAIT_TELEGRAM_STEP1 = 610
WAIT_TELEGRAM_STEP2 = 611
WAIT_TELEGRAM_STEP3 = 612

STEP_CHOICE = 1000
STEP_INPUT = 1001

WAIT_CONSTRUCTOR_CATEGORY = 1200
WAIT_CONSTRUCTOR_TYPE = 1201
WAIT_CONSTRUCTOR_CHOICE = 1202
WAIT_CONSTRUCTOR_TEXT = 1203
SKIP_STEP = 1002

# ============================================
# ИТОГОВЫЙ СПИСОК ДЛЯ ИМПОРТА
# ============================================
__all__ = [
	# Основные состояния (1-29)
	'ADD_LINK_TITLE', 'ADD_LINK_URL', 'ADD_LINK_ICON',
	'EDIT_LINK_SELECT', 'EDIT_LINK_TITLE', 'EDIT_LINK_URL', 'EDIT_LINK_ICON',
	'SELECT_LINK_TYPE', 'SELECT_FINANCE_SUBTYPE',
	'SELECT_CATEGORY', 'ADD_LINK_DESCRIPTION', 'SELECT_PRESET',
	'ADD_CUSTOM_CURRENCY_NAME', 'SELECT_CRYPTO_NETWORK', 'WAIT_CUSTOM_NETWORK',
	'ADD_MULTI_FINANCE_DATA', 'FINALIZE_FINANCE_LINK',
	
	# Профиль (30-49)
	'WAITING_FOR_NICKNAME',
	
	# Банки (100-299)
	'SELECT_COUNTRY', 'SELECT_METHOD', 'BACK_TO_COUNTRIES',
	
	# Россия
	'WAIT_RUSSIA_CARD', 'WAIT_RUSSIA_PHONE', 'WAIT_RUSSIA_DETAILS',
	
	# Беларусь
	'WAIT_BELARUS_CARD', 'WAIT_BELARUS_ERIP', 'WAIT_BELARUS_IBAN',
	
	# Казахстан
	'WAIT_KAZAKHSTAN_CARD', 'WAIT_KAZAKHSTAN_PHONE', 'WAIT_KAZAKHSTAN_IBAN',
	
	# Украина
	'WAIT_UKRAINE_CARD', 'WAIT_UKRAINE_IBAN',
	
	# Узбекистан
	'WAIT_UZBEKISTAN_CARD', 'WAIT_UZBEKISTAN_PHONE',
	
	# Таджикистан
	'WAIT_TAJIKISTAN_CARD', 'WAIT_TAJIKISTAN_PHONE',
	
	# Кыргызстан
	'WAIT_KYRGYZSTAN_CARD', 'WAIT_KYRGYZSTAN_PHONE',
	
	# Туркменистан
	'WAIT_TURKMENISTAN_CARD',
	
	# Армения
	'WAIT_ARMENIA_CARD', 'WAIT_ARMENIA_IBAN',
	
	# Азербайджан
	'WAIT_AZERBAIJAN_CARD', 'WAIT_AZERBAIJAN_IBAN',
	
	# Грузия
	'WAIT_GEORGIA_CARD', 'WAIT_GEORGIA_IBAN',
	
	# Молдова
	'WAIT_MOLDOVA_CARD', 'WAIT_MOLDOVA_IBAN',
	
	# Европа
	'WAIT_EUROPE_CARD', 'WAIT_EUROPE_IBAN',
	
	# США
	'WAIT_USA_CARD', 'WAIT_USA_ACH', 'WAIT_USA_WIRE', 'WAIT_USA_IBAN',
	
	# Международные сервисы
	'WAIT_REVOLUT', 'WAIT_WISE', 'WAIT_PAYPAL', 'WAIT_SWIFT', 'WAIT_IBAN',
	
	# Другие страны
	'WAIT_OTHER_COUNTRY', 'WAIT_OTHER_DETAILS',
	
	# Подтверждение
	'CONFIRM_PAYMENT', 'EDIT_PAYMENT',
	
	# Revolut стейты (283-288)
	'WAIT_REVOLUT_CHOICE', 'WAIT_REVOLUT_QUICK', 'WAIT_REVOLUT_FULL',
	'WAIT_REVOLUT_BENEFICIARY', 'WAIT_REVOLUT_IBAN', 'WAIT_REVOLUT_BIC',
	'WAIT_REVOLUT_CORRESPONDENT', 'WAIT_REVOLUT_ADDRESS', 'WAIT_REVOLUT_LOGIN',
	
	# Wise стейты (291-298)
	'WAIT_WISE_CHOICE', 'WAIT_WISE_QUICK', 'WAIT_WISE_FULL',
	'WAIT_WISE_BENEFICIARY', 'WAIT_WISE_IBAN', 'WAIT_WISE_BIC',
	'WAIT_WISE_CORRESPONDENT', 'WAIT_WISE_ADDRESS', 'WAIT_WISE_LOGIN',
	
	# Банки Мира / Универсальный конструктор (500-503)
	'WAIT_METHOD_SELECTION', 'WAIT_FILLING_DATA', 'WAIT_FIELD_INPUT', 'WAIT_FINAL_CONFIRM',
	
	# Соцсети
	'WAIT_SOCIAL_STEP1', 'WAIT_SOCIAL_URL', 'WAIT_TELEGRAM_STEP1', 'WAIT_TELEGRAM_STEP2',
	'WAIT_TELEGRAM_STEP3',
	
	'STEP_CHOICE',
	'STEP_INPUT',
	'WAIT_CONSTRUCTOR_CATEGORY',
	'WAIT_CONSTRUCTOR_TYPE',
	'WAIT_CONSTRUCTOR_CHOICE',
	'WAIT_CONSTRUCTOR_TEXT',
	'SKIP_STEP',

]
