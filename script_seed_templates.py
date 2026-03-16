# seed_templates.py
import asyncio
import asyncpg
import logging
from core.config import DATABASE_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Базовые шаблоны дизайна
TEMPLATES = [
    {
        "name": "Классический",
        "description": "Простой и элегантный шаблон",
        "html_template": """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ page.title }} | BotoLinkPro</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, {{ colors.primary }} 0%, {{ colors.primary }}dd 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            max-width: 600px;
            width: 100%;
            background: {{ colors.background }};
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 40px 30px;
        }
        
        .profile {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .avatar {
            width: 100px;
            height: 100px;
            border-radius: 50%;
            background: {{ colors.primary }};
            margin: 0 auto 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 40px;
            color: white;
        }
        
        .username {
            font-size: 24px;
            font-weight: bold;
            color: {{ colors.text }};
            margin-bottom: 5px;
        }
        
        .description {
            color: {{ colors.text }}99;
            font-size: 16px;
        }
        
        .links {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        
        .link-card {
            background: {{ colors.background }};
            border: 2px solid {{ colors.primary }}20;
            border-radius: 12px;
            padding: 15px 20px;
            text-decoration: none;
            color: {{ colors.text }};
            display: flex;
            align-items: center;
            gap: 15px;
            transition: all 0.3s ease;
        }
        
        .link-card:hover {
            border-color: {{ colors.primary }};
            transform: translateY(-2px);
            box-shadow: 0 10px 20px {{ colors.primary }}20;
        }
        
        .link-icon {
            width: 40px;
            height: 40px;
            background: {{ colors.primary }}10;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: {{ colors.primary }};
            font-size: 20px;
        }
        
        .link-title {
            flex: 1;
            font-weight: 500;
        }
        
        .link-arrow {
            color: {{ colors.primary }};
            opacity: 0.5;
            transition: opacity 0.3s;
        }
        
        .link-card:hover .link-arrow {
            opacity: 1;
        }
        
        .footer {
            margin-top: 30px;
            text-align: center;
            color: {{ colors.text }}80;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="profile">
            <div class="avatar">
                <i class="fas fa-user"></i>
            </div>
            <div class="username">@{{ page.username }}</div>
            {% if page.description %}
            <div class="description">{{ page.description }}</div>
            {% endif %}
        </div>
        
        <div class="links">
            {% for link in links %}
            <a href="{{ link.url }}" class="link-card" target="_blank" rel="noopener noreferrer">
                <div class="link-icon">
                    <i class="{{ link.icon_class }}"></i>
                </div>
                <span class="link-title">{{ link.title }}</span>
                <i class="fas fa-chevron-right link-arrow"></i>
            </a>
            {% endfor %}
        </div>
        
        <div class="footer">
            made in BotoLinkPro
        </div>
    </div>
</body>
</html>
        """,
        "css_template": "",
        "preview_url": "/static/templates/classic.jpg",
        "is_default": True
    },
    {
        "name": "Минимализм",
        "description": "Чистый и лаконичный дизайн",
        "html_template": """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ page.title }} | BotoLinkPro</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background: {{ colors.background }};
            min-height: 100vh;
            display: flex;
            justify-content: center;
            padding: 40px 20px;
        }
        
        .container {
            max-width: 500px;
            width: 100%;
        }
        
        .profile {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .avatar {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            background: {{ colors.primary }}10;
            margin: 0 auto 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 32px;
            color: {{ colors.primary }};
        }
        
        .username {
            font-size: 28px;
            font-weight: 600;
            color: {{ colors.text }};
            letter-spacing: -0.5px;
        }
        
        .description {
            color: {{ colors.text }}80;
            font-size: 16px;
            margin-top: 8px;
        }
        
        .links {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        .link-card {
            padding: 16px 20px;
            background: transparent;
            border: 1px solid {{ colors.text }}20;
            border-radius: 12px;
            text-decoration: none;
            color: {{ colors.text }};
            display: flex;
            align-items: center;
            gap: 12px;
            transition: all 0.2s;
        }
        
        .link-card:hover {
            background: {{ colors.primary }}10;
            border-color: {{ colors.primary }};
        }
        
        .link-icon {
            width: 24px;
            color: {{ colors.primary }};
            font-size: 18px;
        }
        
        .link-title {
            flex: 1;
            font-weight: 500;
        }
        
        .footer {
            margin-top: 40px;
            text-align: center;
            color: {{ colors.text }}40;
            font-size: 12px;
            letter-spacing: 0.5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="profile">
            <div class="avatar">
                <i class="fas fa-user-circle"></i>
            </div>
            <div class="username">@{{ page.username }}</div>
            {% if page.description %}
            <div class="description">{{ page.description }}</div>
            {% endif %}
        </div>
        
        <div class="links">
            {% for link in links %}
            <a href="{{ link.url }}" class="link-card" target="_blank" rel="noopener noreferrer">
                <div class="link-icon">
                    <i class="{{ link.icon_class }}"></i>
                </div>
                <span class="link-title">{{ link.title }}</span>
                <i class="fas fa-external-link-alt" style="font-size: 12px; opacity: 0.5;"></i>
            </a>
            {% endfor %}
        </div>
        
        <div class="footer">
            M Y L I N K S P A C E
        </div>
    </div>
</body>
</html>
        """,
        "css_template": "",
        "preview_url": "/static/templates/minimal.jpg",
        "is_default": False
    },
    {
        "name": "Яркий",
        "description": "Динамичный шаблон с градиентами",
        "html_template": """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ page.title }} | BotoLinkPro</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(45deg, {{ colors.primary }}, {{ colors.secondary|default(colors.primary) }});
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            max-width: 550px;
            width: 100%;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 30px;
            padding: 40px 30px;
            box-shadow: 0 30px 60px rgba(0,0,0,0.2);
        }
        
        .profile {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .avatar {
            width: 100px;
            height: 100px;
            border-radius: 30px;
            background: linear-gradient(45deg, {{ colors.primary }}, {{ colors.secondary|default(colors.primary) }});
            margin: 0 auto 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 40px;
            color: white;
            transform: rotate(-5deg);
        }
        
        .username {
            font-size: 32px;
            font-weight: 700;
            background: linear-gradient(45deg, {{ colors.primary }}, {{ colors.secondary|default(colors.primary) }});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 5px;
        }
        
        .description {
            color: #666;
            font-size: 16px;
        }
        
        .links {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        
        .link-card {
            background: white;
            border-radius: 20px;
            padding: 18px 25px;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
            transition: all 0.3s;
            border: 2px solid transparent;
        }
        
        .link-card:hover {
            transform: scale(1.02) translateY(-3px);
            border-color: {{ colors.primary }};
            box-shadow: 0 15px 30px {{ colors.primary }}30;
        }
        
        .link-icon {
            width: 45px;
            height: 45px;
            background: linear-gradient(45deg, {{ colors.primary }}20, {{ colors.secondary|default(colors.primary) }}20);
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: {{ colors.primary }};
            font-size: 20px;
        }
        
        .link-title {
            flex: 1;
            font-weight: 600;
            color: #333;
        }
        
        .footer {
            margin-top: 30px;
            text-align: center;
            color: #999;
            font-size: 12px;
            font-weight: 500;
            letter-spacing: 1px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="profile">
            <div class="avatar">
                <i class="fas fa-star"></i>
            </div>
            <div class="username">@{{ page.username }}</div>
            {% if page.description %}
            <div class="description">{{ page.description }}</div>
            {% endif %}
        </div>
        
        <div class="links">
            {% for link in links %}
            <a href="{{ link.url }}" class="link-card" target="_blank" rel="noopener noreferrer">
                <div class="link-icon">
                    <i class="{{ link.icon_class }}"></i>
                </div>
                <span class="link-title">{{ link.title }}</span>
                <i class="fas fa-arrow-right" style="color: {{ colors.primary }};"></i>
            </a>
            {% endfor %}
        </div>
        
        <div class="footer">
            BotoLinkPro
        </div>
    </div>
</body>
</html>
        """,
        "css_template": "",
        "preview_url": "/static/templates/bright.jpg",
        "is_default": False
    }
]

async def seed_templates():
    """Наполнение таблицы шаблонов"""
    conn = await asyncpg.connect(DATABASE_URL.replace('+asyncpg', ''))

    try:
        # Очищаем таблицу
        await conn.execute("TRUNCATE templates RESTART IDENTITY CASCADE;")
        logger.info("Таблица templates очищена")

        # Вставляем шаблоны
        for template in TEMPLATES:
            await conn.execute("""
                               INSERT INTO templates (name, description, html_template, css_template, preview_url, is_default, is_active, sort_order)
                               VALUES ($1, $2, $3, $4, $5, $6, true, 0)
                               """, template["name"], template["description"], template["html_template"],
                               template["css_template"], template["preview_url"], template["is_default"])

        # Проверяем количество
        count = await conn.fetchval("SELECT COUNT(*) FROM templates")
        logger.info(f"✅ Добавлено {count} шаблонов в базу данных")

        # Покажем шаблоны
        templates = await conn.fetch("SELECT id, name, is_default FROM templates ORDER BY id")
        logger.info("📋 Доступные шаблоны:")
        for t in templates:
            default = " (по умолчанию)" if t['is_default'] else ""
            logger.info(f"  • {t['name']}{default}")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(seed_templates())