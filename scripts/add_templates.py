# scripts/add_templates.py
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres@localhost/botolinkpro')
# Преобразуем URL для asyncpg (убираем +asyncpg)
DATABASE_URL = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')

async def add_templates():
    """Добавление шаблонов в базу данных"""
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Проверяем, есть ли уже шаблоны
        count = await conn.fetchval("SELECT COUNT(*) FROM templates")
        if count > 0:
            print(f"В таблице уже есть {count} шаблонов. Пропускаем...")
            return

        templates = [
            # 1. Минимализм (бесплатный, базовый)
            {
                'name': 'Minimal Light',
                'description': 'Чистый и светлый минимализм',
                'bg_color': '#FFFFFF',
                'text_color': '#333333',
                'button_style': 'rounded',
                'font_family': 'Arial, sans-serif',
                'preview_url': '/static/previews/minimal-light.jpg',
                'is_pro': False,
                'sort_order': 1,
                'is_active': True,
                'is_default': True
            },
            # 2. Тёмный режим (бесплатный)
            {
                'name': 'Dark Mode',
                'description': 'Элегантный тёмный фон',
                'bg_color': '#1A1A1A',
                'text_color': '#FFFFFF',
                'button_style': 'pill',
                'font_family': 'Helvetica, sans-serif',
                'preview_url': '/static/previews/dark-mode.jpg',
                'is_pro': False,
                'sort_order': 2,
                'is_active': True,
                'is_default': False
            },
            # 3. Морской (бесплатный)
            {
                'name': 'Ocean Breeze',
                'description': 'Свежий морской стиль',
                'bg_color': '#E3F2FD',
                'text_color': '#01579B',
                'button_style': 'square',
                'font_family': 'Verdana, sans-serif',
                'preview_url': '/static/previews/ocean-breeze.jpg',
                'is_pro': False,
                'sort_order': 3,
                'is_active': True,
                'is_default': False
            },
            # 4. Неон (платный)
            {
                'name': 'Neon Night',
                'description': 'Яркие неоновые акценты',
                'bg_color': '#0D0221',
                'text_color': '#FFFFFF',
                'button_style': 'gradient',
                'font_family': 'Montserrat, sans-serif',
                'preview_url': '/static/previews/neon-night.jpg',
                'is_pro': True,
                'sort_order': 4,
                'is_active': True,
                'is_default': False
            },
            # 5. Мягкие тени (бесплатный)
            {
                'name': 'Soft Shadows',
                'description': 'Мягкие тени и воздушность',
                'bg_color': '#F8F9FA',
                'text_color': '#212529',
                'button_style': 'shadow',
                'font_family': 'Roboto, sans-serif',
                'preview_url': '/static/previews/soft-shadows.jpg',
                'is_pro': False,
                'sort_order': 5,
                'is_active': True,
                'is_default': False
            },
            # 6. Премиум стекло (платный)
            {
                'name': 'Glassmorphism',
                'description': 'Эффект матового стекла',
                'bg_color': 'rgba(255, 255, 255, 0.15)',
                'text_color': '#FFFFFF',
                'button_style': 'rounded',
                'font_family': 'Poppins, sans-serif',
                'preview_url': '/static/previews/glassmorphism.jpg',
                'is_pro': True,
                'sort_order': 6,
                'is_active': True,
                'is_default': False
            },
            # 7. Ретро (бесплатный)
            {
                'name': 'Retro Vibes',
                'description': 'Винтажный стиль 80-х',
                'bg_color': '#FDF4E3',
                'text_color': '#8B5A2B',
                'button_style': 'outline',
                'font_family': 'Courier New, monospace',
                'preview_url': '/static/previews/retro-vibes.jpg',
                'is_pro': False,
                'sort_order': 7,
                'is_active': True,
                'is_default': False
            },
            # 8. Природа (бесплатный)
            {
                'name': 'Forest',
                'description': 'Спокойные природные тона',
                'bg_color': '#E8F5E9',
                'text_color': '#1B5E20',
                'button_style': 'pill',
                'font_family': 'Georgia, serif',
                'preview_url': '/static/previews/forest.jpg',
                'is_pro': False,
                'sort_order': 8,
                'is_active': True,
                'is_default': False
            },
            # 9. Космос (платный)
            {
                'name': 'Deep Space',
                'description': 'Космическая тема',
                'bg_color': '#0B0C10',
                'text_color': '#FFFFFF',
                'button_style': 'gradient',
                'font_family': 'Orbitron, sans-serif',
                'preview_url': '/static/previews/deep-space.jpg',
                'is_pro': True,
                'sort_order': 9,
                'is_active': True,
                'is_default': False
            },
            # 10. Пастель (бесплатный)
            {
                'name': 'Pastel Dream',
                'description': 'Мягкие пастельные тона',
                'bg_color': '#FFE4E1',
                'text_color': '#8B4513',
                'button_style': 'rounded',
                'font_family': 'Quicksand, sans-serif',
                'preview_url': '/static/previews/pastel-dream.jpg',
                'is_pro': False,
                'sort_order': 10,
                'is_active': True,
                'is_default': False
            }
        ]

        # Вставляем шаблоны
        for template in templates:
            await conn.execute("""
                               INSERT INTO templates (
                                   name, description, bg_color, text_color,
                                   button_style, font_family, preview_url,
                                   is_pro, sort_order, is_active, is_default
                               ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                               """,
                               template['name'], template['description'],
                               template['bg_color'], template['text_color'],
                               template['button_style'], template['font_family'],
                               template['preview_url'], template['is_pro'],
                               template['sort_order'], template['is_active'],
                               template['is_default']
                               )

        print(f"✅ Добавлено {len(templates)} шаблонов")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(add_templates())