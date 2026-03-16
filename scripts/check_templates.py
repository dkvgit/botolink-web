# scripts/check_templates.py
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres@localhost/botolinkpro')
DATABASE_URL = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')

async def check_templates():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        templates = await conn.fetch("""
                                     SELECT id, name, is_pro, is_default
                                     FROM templates
                                     ORDER BY id
                                     """)

        print("📊 Существующие шаблоны:")
        print("-" * 50)
        free_count = 0
        pro_count = 0

        for t in templates:
            type_icon = "🔵 FREE" if not t['is_pro'] else "🟣 PRO"
            default_icon = "⭐ DEFAULT" if t['is_default'] else ""
            print(f"ID: {t['id']} | {type_icon} | {t['name']} {default_icon}")

            if not t['is_pro']:
                free_count += 1
            else:
                pro_count += 1

        print("-" * 50)
        print(f"Всего: {len(templates)} шаблонов")
        print(f"Бесплатных: {free_count}")
        print(f"Платных: {pro_count}")

    finally:
        await conn.close()

asyncio.run(check_templates())