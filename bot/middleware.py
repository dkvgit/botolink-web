from functools import wraps

from core.database import AsyncSessionLocal  # Исправленное имя
from core.models import User, Subscription, Page, Link
from sqlalchemy import select, func  # Импортируем select и func


def check_limits(func_to_wrap):  # переименовал, чтобы не путать с func из sqlalchemy
	"""Декоратор для проверки лимитов перед действиями"""
	
	@wraps(func_to_wrap)
	async def wrapper(update, context, *args, **kwargs):
		user_id = update.effective_user.id
		
		# Работаем асинхронно, так как AsyncSessionLocal — это асинхронная фабрика
		async with AsyncSessionLocal() as db:
			try:
				# В асинхронной алхимии используем select вместо db.query
				result = await db.execute(select(User).filter(User.telegram_id == user_id))
				user = result.scalar_one_or_none()
				
				if not user:
					return await func_to_wrap(update, context, *args, **kwargs)
				
				# Получаем подписку
				sub_result = await db.execute(select(Subscription).filter(Subscription.user_id == user.id))
				subscription = sub_result.scalar_one_or_none()
				
				plan = subscription.plan_type if subscription else "free"
				action = kwargs.get('action', '')
				
				if action == 'add_link':
					# Считаем ссылки асинхронно
					page_result = await db.execute(select(Page).filter(Page.user_id == user.id))
					page = page_result.scalar_one_or_none()
					
					if page:
						# Считаем количество ссылок
						count_result = await db.execute(
							select(func.count(Link.id)).filter(Link.page_id == page.id)
						)
						links_count = count_result.scalar()
						
						max_links = 3 if plan == 'free' else 25
						
						if links_count >= max_links:
							await update.message.reply_text(
								f"❌ Достигнут лимит ссылок ({max_links}).\n"
								f"Купите PRO для увеличения лимита до 25 ссылок: /upgrade"
							)
							return
				
				return await func_to_wrap(update, context, *args, **kwargs)
			
			finally:
				await db.close()  # Асинхронное закрытие
	
	return wrapper
