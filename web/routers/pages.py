# D:\aRabota\TelegaBoom\030_botolinkpro\web\routers\pages.py


import json
import logging
import sys

from core.database import get_db
from core.models import Page, Link, Subscription
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["pages"])
templates = Jinja2Templates(directory="web/templates")

TEMPLATES_MAP = {
	1: "01classic", 2: "02minimal", 3: "03bright", 4: "04neon", 5: "05glass",
	6: "06deepspace", 7: "07cyberpunk", 8: "08royalgold", 9: "09aurora", 10: "10hologram", 11: "11den"
}


@router.get("/click/{link_id}")
async def track_click(link_id: int, db: AsyncSession = Depends(get_db)):
	query = select(Link).filter(Link.id == link_id)
	result = await db.execute(query)
	link = result.scalars().first()
	
	if not link:
		raise HTTPException(status_code=404, detail="Ссылка не найдена")
	
	if link.click_count is None:
		link.click_count = 0
	link.click_count += 1
	await db.commit()
	
	target_url = link.url
	if not target_url.startswith(('http://', 'https://')):
		target_url = f'https://{target_url}'
	
	return RedirectResponse(url=target_url)


@router.get("/{username}", response_class=HTMLResponse)
async def view_page(request: Request, username: str, db: AsyncSession = Depends(get_db)):
	# 1. Ищем страницу
	page_query = select(Page).filter(Page.username == username).options(selectinload(Page.user))
	page_result = await db.execute(page_query)
	page = page_result.scalars().first()
	
	if not page:
		raise HTTPException(status_code=404, detail="Страница не найдена")
	
	# 2. Обновляем счетчик просмотров
	if page.view_count is None:
		page.view_count = 0
	page.view_count += 1
	await db.commit()
	
	# 3. Получаем все активные ссылки
	links_query = select(Link).filter(Link.page_id == page.id, Link.is_active == True).order_by(Link.sort_order)
	links_result = await db.execute(links_query)
	links_list = links_result.scalars().all()
	
	# 4. Подготавливаем категории
	categories = {
		"social": [],
		"messengers": [],
		"transfers": [],
		"donate": [],
		"crypto": [],
		"shops": [],
		"partner": [],
		"other": []
	}
	
	# 5. Распределяем ссылки по категориям
	
	# 👇 ЭТИ ПРИНТЫ ДОЛЖНЫ БЫТЬ ДО ЦИКЛА!
	print("🔥🔥🔥 НАЧАЛО ОБРАБОТКИ СТРАНИЦЫ", file=sys.stderr)
	print(f"🔥 Количество ссылок: {len(links_list)}", file=sys.stderr)
	
	for link in links_list:
		print(f"🔥 Ссылка ID={link.id}, title={link.title}, category={link.category}", file=sys.stderr)
		
		# Десериализация реквизитов
		pd = link.pay_details
		if isinstance(pd, str):
			try:
				pd = json.loads(pd)
			except:
				pd = {}
		
		# Определяем категорию
		category = link.category
		if not category:
			category = "other"
		
		link_data = {
			"id": link.id,
			"title": link.title,
			"url": link.url,
			"link_type": str(link.link_type).strip().lower() if link.link_type else "other",
			"category": category,
			"icon": link.icon,
			"icon_class": link.icon_class,
			"pay_details": pd or {},
			"is_exchange": link.is_exchange,
			"description": getattr(link, 'description', None)
		}
		
		# Распределение
		if category == "social":
			categories["social"].append(link_data)
			logger.info(f"✅ social: {link.title}")
		elif category == "messengers":
			categories["messengers"].append(link_data)
			logger.info(f"✅ messengers: {link.title}")
		elif category in ["crypto", "wallets"] or link.is_exchange:
			categories["crypto"].append(link_data)
			logger.info(f"✅ crypto: {link.title}")
		elif category in ["transfers", "transfer"] or link.link_type == "card":
			categories["transfers"].append(link_data)
			logger.info(f"🔄 transfers: {link.title} (category={category}, link_type={link.link_type})")
		elif category in ["shops", "shop"]:
			categories["shops"].append(link_data)
			logger.info(f"✅ shops: {link.title}")
		elif category == "partner":
			categories["partner"].append(link_data)
			logger.info(f"✅ partner: {link.title}")
		else:
			categories["other"].append(link_data)
			logger.info(f"❌ other: {link.title} (category={category})")
	
	# 6. Выбор шаблона
	folder = TEMPLATES_MAP.get(page.template_id, "01classic")
	template_path = f"{folder}/{folder}_page.html"
	
	# 7. Проверка подписки
	sub_query = select(Subscription).filter(Subscription.user_id == page.user_id)
	sub_result = await db.execute(sub_query)
	subscription = sub_result.scalars().first()
	show_watermark = not (subscription and subscription.plan_type == "pro")
	
	return templates.TemplateResponse(
		template_path,
		{
			"request": request,
			"page": page,
			"user": page.user,
			"categories": categories,
			"show_watermark": show_watermark
		}
	)
