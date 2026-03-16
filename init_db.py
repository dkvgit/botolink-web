# init_db.py
import asyncio
import logging
from core.database import engine, Base
from core.models import User, Page, Link, Subscription, Click, Icon, Template
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_database():
    """Создание всех таблиц в базе данных"""
    logger.info("Создание таблиц в базе данных...")

    async with engine.begin() as conn:
        # Создаем все таблицы
        await conn.run_sync(Base.metadata.create_all)

    logger.info("✅ Таблицы успешно созданы!")

async def drop_database():
    """Удаление всех таблиц (ОСТОРОЖНО!)"""
    logger.warning("⚠️ Удаление всех таблиц...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    logger.info("✅ Таблицы удалены!")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--drop":
        asyncio.run(drop_database())
    else:
        asyncio.run(init_database())
        print("\n✅ База данных готова!")
        print("Запустите: python init_db.py --drop  # чтобы удалить все таблицы")