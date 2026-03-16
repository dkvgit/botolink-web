# bot/avatar_handler.py

import os
import time
import asyncio
import aiohttp
import logging
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes
from bot.utils import get_db_connection

logger = logging.getLogger(__name__)

# Папка для хранения аватаров
AVATAR_FOLDER = "web/static/avatars"
os.makedirs(AVATAR_FOLDER, exist_ok=True)

def _save_file_sync(path: str, data: bytes):
	"""Синхронная функция для сохранения файла"""
	with open(path, 'wb') as f:
		f.write(data)

async def download_user_avatar(user_id: int, bot) -> Optional[str]:
	"""Скачивает аватар пользователя из Telegram и сохраняет локально."""
	
	print(f"\n📸 ===== СКАЧИВАНИЕ АВАТАРА для {user_id} ===== ")
	
	try:
		# Получаем список фото профиля
		photos = await bot.get_user_profile_photos(user_id, limit=1)
		
		if not photos or not photos.photos or photos.total_count == 0:
			print(f"❌ У пользователя {user_id} нет аватара")
			return None
		
		# Берем самую качественную версию
		best_photo = photos.photos[0][-1]
		file_id = best_photo.file_id
		print(f"📸 File ID: {file_id}")
		
		# Получаем файл
		file = await bot.get_file(file_id)
		
		# Локальный путь для сохранения
		local_filename = f"user_{user_id}.jpg"
		local_path = os.path.join(AVATAR_FOLDER, local_filename)
		print(f"📸 Локальный путь: {local_path}")
		
		# Создаем папку если нет
		os.makedirs(AVATAR_FOLDER, exist_ok=True)
		
		# Скачиваем файл (встроенный метод библиотеки!)
		await file.download_to_drive(local_path)
		
		# Проверяем что файл сохранился
		if os.path.exists(local_path):
			print(f"✅ Файл успешно сохранен: {local_path}")
			return local_path
		else:
			print(f"❌ Файл не сохранился!")
			return None
	
	except Exception as e:
		print(f"❌ Ошибка: {e}")
		import traceback
		traceback.print_exc()
		return None



async def get_or_download_avatar(user_id: int, bot, force_update: bool = False) -> Optional[str]:
	"""
	Проверяет, есть ли уже скачанный аватар.
	Если нет или нужно обновить - скачивает новый.
	"""
	local_filename = f"user_{user_id}.jpg"
	local_path = os.path.join(AVATAR_FOLDER, local_filename)
	# Правильный веб-путь
	web_path = f"/static/avatars/{local_filename}"
	
	# Если файл существует и не нужно обновлять
	if os.path.exists(local_path) and not force_update:
		# Проверяем возраст файла (обновляем раз в неделю)
		file_age = time.time() - os.path.getmtime(local_path)
		if file_age < 7 * 24 * 3600:  # 7 дней
			logger.info(f"Используем существующий аватар для {user_id}")
			return web_path
		else:
			logger.info(f"Аватар для {user_id} устарел, скачиваем новый")
	
	# Скачиваем новый аватар
	new_path = await download_user_avatar(user_id, bot)
	return web_path if new_path else None



async def save_avatar_to_db(user_id: int, avatar_path: str, conn) -> None:
	"""Сохраняет путь к аватару в базу данных."""
	try:
		# Получаем пользователя из БД
		user = await conn.fetchrow(
			"SELECT id FROM users WHERE telegram_id = $1",
			user_id
		)
		
		if not user:
			logger.warning(f"Пользователь {user_id} не найден в БД")
			return
		
		# Обновляем путь к аватару в странице пользователя
		await conn.execute(
			"UPDATE pages SET avatar_path = $1 WHERE user_id = $2",
			avatar_path,
			user['id']
		)
		logger.info(f"Путь к аватару сохранен в БД для пользователя {user_id}")
	
	except Exception as e:
		logger.error(f"Ошибка при сохранении аватара в БД: {e}")

async def update_user_avatar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	"""Обновляет аватар пользователя (вызывается при старте или по команде)."""
	user = update.effective_user
	user_id = user.id
	
	await update.message.reply_text("🔄 Обновляю аватар...")
	
	# Скачиваем аватар
	avatar_path = await download_user_avatar(user_id, context.bot)
	
	if avatar_path:
		# Сохраняем в БД
		conn = await get_db_connection()
		try:
			# Правильный веб-путь - берем только имя файла
			filename = os.path.basename(avatar_path)
			web_path = f"/static/avatars/{filename}"
			
			await save_avatar_to_db(user_id, web_path, conn)
			await update.message.reply_text("✅ Аватар успешно обновлен!")
		finally:
			await conn.close()
	else:
		await update.message.reply_text("❌ Не удалось загрузить аватар")
		
		
		
async def refresh_avatar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	"""Команда для принудительного обновления аватара."""
	await update_user_avatar(update, context)

async def setup_user_avatar(user_id: int, bot, conn) -> Optional[str]:
	"""Настраивает аватар для пользователя при первом запуске."""
	
	
	
	# Проверяем, есть ли уже аватар в БД
	user = await conn.fetchrow(
		"""
        SELECT p.avatar_path, u.id as user_db_id FROM pages p
                                                          JOIN users u ON u.id = p.user_id
        WHERE u.telegram_id = $1
		""",
		user_id
	)
	
	
	
	# Если уже есть аватар - используем его
	if user and user['avatar_path']:
		
		local_path = user['avatar_path'].replace("/static/avatars/", "")
		full_local_path = os.path.join(AVATAR_FOLDER, local_path)
		
		# Проверяем, существует ли файл
		if os.path.exists(full_local_path):
			
			return user['avatar_path']
		else:
			print(f"")
		
	
	# Скачиваем новый аватар
	
	avatar_path = await download_user_avatar(user_id, bot)
	
	
	if avatar_path:
		# ИСПРАВЛЕНО: правильное формирование веб-пути
		filename = os.path.basename(avatar_path)  # получит user_5425101564.jpg
		web_path = f"/static/avatars/{filename}"
		
		
		await save_avatar_to_db(user_id, web_path, conn)
		
		return web_path
	
	
	return None