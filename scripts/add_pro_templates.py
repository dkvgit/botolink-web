# scripts/add_pro_templates.py
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres@localhost/botolinkpro')
DATABASE_URL = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')

# Базовый HTML шаблон (используем существующий из первых 3 шаблонов)
BASE_HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ username }} | BotoLinkPro</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background: {{ bg_color }}; color: {{ text_color }}; font-family: {{ font_family }}; }
        .link-card { transition: all 0.3s; }
    </style>
</head>
<body class="min-h-screen flex flex-col items-center p-4">
    <div class="max-w-md w-full mt-8">
        <h1>@{{ username }}</h1>
        {% for link in links %}
        <a href="{{ link.url }}" class="link-card">{{ link.title }}</a>
        {% endfor %}
    </div>
</body>
</html>
'''

# Базовый CSS
BASE_CSS = '''
body { margin: 0; padding: 20px; }
.link-card { display: block; padding: 15px; margin: 10px 0; text-decoration: none; }
'''

async def add_pro_templates():
    """Добавление платных PRO шаблонов"""
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Получаем существующие шаблоны
        existing = await conn.fetch("SELECT name FROM templates")
        existing_names = [t['name'] for t in existing]

        pro_templates = [
            {
                'name': 'Neon Night',
                'description': 'Яркие неоновые акценты',
                'html_template': BASE_HTML,
                'css_template': BASE_CSS,
                'preview_url': '/static/previews/neon-night.jpg',
                'bg_color': '#0D0221',
                'text_color': '#FFFFFF',
                'button_style': 'gradient',
                'font_family': 'Montserrat, sans-serif',
                'is_pro': True,
                'sort_order': 4,
                'is_active': True,
                'is_default': False
            },
            {
                'name': 'Glassmorphism',
                'description': 'Эффект матового стекла',
                'html_template': BASE_HTML,
                'css_template': BASE_CSS,
                'preview_url': '/static/previews/glassmorphism.jpg',
                'bg_color': 'rgba(255, 255, 255, 0.15)',
                'text_color': '#FFFFFF',
                'button_style': 'rounded',
                'font_family': 'Poppins, sans-serif',
                'is_pro': True,
                'sort_order': 5,
                'is_active': True,
                'is_default': False
            },
            {
                'name': 'Deep Space',
                'description': 'Космическая тема',
                'html_template': BASE_HTML,
                'css_template': BASE_CSS,
                'preview_url': '/static/previews/deep-space.jpg',
                'bg_color': '#0B0C10',
                'text_color': '#FFFFFF',
                'button_style': 'gradient',
                'font_family': 'Orbitron, sans-serif',
                'is_pro': True,
                'sort_order': 6,
                'is_active': True,
                'is_default': False
            },
            {
                'name': 'Cyberpunk',
                'description': 'Киберпанк стиль с неоном',
                'html_template': BASE_HTML,
                'css_template': BASE_CSS,
                'preview_url': '/static/previews/cyberpunk.jpg',
                'bg_color': '#0A0F0F',
                'text_color': '#00FF00',
                'button_style': 'glitch',
                'font_family': 'Share Tech Mono, monospace',
                'is_pro': True,
                'sort_order': 7,
                'is_active': True,
                'is_default': False
            },
            {
                'name': 'Royal Gold',
                'description': 'Королевская роскошь',
                'html_template': BASE_HTML,
                'css_template': BASE_CSS,
                'preview_url': '/static/previews/royal-gold.jpg',
                'bg_color': '#1A0F0F',
                'text_color': '#FFD700',
                'button_style': 'elegant',
                'font_family': 'Cormorant Garamond, serif',
                'is_pro': True,
                'sort_order': 8,
                'is_active': True,
                'is_default': False
            },
            {
                'name': 'Aurora',
                'description': 'Северное сияние',
                'html_template': BASE_HTML,
                'css_template': BASE_CSS,
                'preview_url': '/static/previews/aurora.jpg',
                'bg_color': '#0A2F44',
                'text_color': '#FFFFFF',
                'button_style': 'aurora',
                'font_family': 'Nunito, sans-serif',
                'is_pro': True,
                'sort_order': 9,
                'is_active': True,
                'is_default': False
            },
            {
                'name': 'Hologram',
                'description': 'Голографический эффект',
                'html_template': BASE_HTML,
                'css_template': BASE_CSS,
                'preview_url': '/static/previews/hologram.jpg',
                'bg_color': 'linear-gradient(45deg, #4158D0, #C850C0, #FFCC70)',
                'text_color': '#FFFFFF',
                'button_style': 'holographic',
                'font_family': 'Poppins, sans-serif',
                'is_pro': True,
                'sort_order': 10,
                'is_active': True,
                'is_default': False
            },
            {
                'name': 'Den',
                'description': 'Мой личный',
                'html_template': BASE_HTML,
                'css_template': BASE_CSS,
                'preview_url': '/static/previews/den.jpg',
                'bg_color': 'linear-gradient(135deg, #4f46e5, #7c3aed)',
                'text_color': '#FFFFFF',
                'button_style': 'gradient',
                'font_family': 'Montserrat, sans-serif',
                'is_pro': True,
                'sort_order': 11,
                'is_active': True,
                'is_default': False
            }
        ]

        added = 0
        for template in pro_templates:
            if template['name'] not in existing_names:
                await conn.execute("""
                                   INSERT INTO templates (
                                       name, description, html_template, css_template,
                                       preview_url, bg_color, text_color, button_style,
                                       font_family, is_pro, sort_order, is_active, is_default
                                   ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                                   """,
                                   template['name'], template['description'],
                                   template['html_template'], template['css_template'],
                                   template['preview_url'], template['bg_color'],
                                   template['text_color'], template['button_style'],
                                   template['font_family'], template['is_pro'],
                                   template['sort_order'], template['is_active'],
                                   template['is_default']
                                   )
                added += 1
                print(f"✅ Добавлен: {template['name']}")
            else:
                print(f"⏭️ Уже существует: {template['name']}")

        print(f"\n📊 Итого добавлено: {added} PRO шаблонов")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(add_pro_templates())