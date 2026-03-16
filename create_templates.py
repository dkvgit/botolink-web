import os

# Путь к папке templates
templates_path = os.path.join("web", "templates")

# Создаем основную папку если нет
os.makedirs(templates_path, exist_ok=True)

# Список шаблонов
templates = [
    {"id": "01", "name": "classic", "title": "Классический"},
    {"id": "02", "name": "minimal", "title": "Минимализм"},
    {"id": "03", "name": "bright", "title": "Яркий"},
    {"id": "04", "name": "neon", "title": "Neon Night"},
    {"id": "05", "name": "glass", "title": "Glassmorphism"},
    {"id": "06", "name": "deepspace", "title": "Deep Space"},
    {"id": "07", "name": "cyberpunk", "title": "Cyberpunk"},
    {"id": "08", "name": "royalgold", "title": "Royal Gold"},
    {"id": "09", "name": "aurora", "title": "Aurora"},
    {"id": "10", "name": "hologram", "title": "Hologram"},
    {"id": "11", "name": "den", "title": "Den"}
]

# Базовый HTML шаблон
base_html = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ page.username }} | BotoLinkPro</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="/templates/{folder}/{folder}_style.css">
</head>
<body>
    <div class="container">
        <div class="profile">
            <div class="avatar">
                <i class="fas fa-user"></i>
            </div>
            <h1>@{{ page.username }}</h1>
            {% if page.description %}
            <p class="description">{{ page.description }}</p>
            {% endif %}
        </div>

        <div class="links">
            {% for link in links %}
            <a href="{{ link.url }}" class="link-card" target="_blank">
                <div class="link-icon">
                    <i class="{{ link.icon_class }}"></i>
                </div>
                <span class="link-title">{{ link.title }}</span>
                <i class="fas fa-chevron-right"></i>
            </a>
            {% endfor %}
        </div>

        <div class="footer">
            <p>made in BotoLinkPro</p>
            <p class="views">👁 {{ page.view_count or 0 }}</p>
        </div>
    </div>
</body>
</html>'''

# Стили для каждого шаблона
template_styles = {
    "01classic": '''/* 01classic_style.css - Классический */
body {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    min-height: 100vh;
    display: flex;
    justify-content: center;
    padding: 20px;
}

.container {
    max-width: 600px;
    width: 100%;
    background: white;
    border-radius: 20px;
    padding: 40px 30px;
    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
}

.profile {
    text-align: center;
    margin-bottom: 30px;
}

.avatar {
    width: 100px;
    height: 100px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 50%;
    margin: 0 auto 15px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 40px;
    color: white;
}

h1 {
    font-size: 24px;
    color: #333;
    margin-bottom: 5px;
}

.link-card {
    display: flex;
    align-items: center;
    padding: 15px 20px;
    background: white;
    border: 2px solid #f0f0f0;
    border-radius: 12px;
    text-decoration: none;
    color: #333;
    margin-bottom: 12px;
    transition: all 0.3s;
}

.link-card:hover {
    border-color: #667eea;
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(102, 126, 234, 0.1);
}

.link-icon {
    width: 40px;
    height: 40px;
    background: #f5f5f5;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 15px;
    color: #667eea;
    font-size: 20px;
}

.link-title {
    flex: 1;
    font-weight: 500;
}''',

    "02minimal": '''/* 02minimal_style.css - Минимализм */
body {
    background: #fafafa;
    font-family: 'Inter', -apple-system, sans-serif;
    min-height: 100vh;
    display: flex;
    justify-content: center;
    padding: 20px;
}

.container {
    max-width: 500px;
    width: 100%;
    background: white;
    padding: 40px 20px;
}

.avatar {
    width: 80px;
    height: 80px;
    background: #e0e0e0;
    border-radius: 50%;
    margin: 0 auto 15px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 32px;
    color: #666;
}

.link-card {
    display: flex;
    align-items: center;
    padding: 16px 20px;
    background: transparent;
    border: 1px solid #e0e0e0;
    border-radius: 50px;
    text-decoration: none;
    color: #333;
    margin-bottom: 8px;
    transition: all 0.2s;
}

.link-card:hover {
    background: #f5f5f5;
    border-color: #999;
}

.link-icon {
    width: 24px;
    margin-right: 12px;
    color: #666;
    font-size: 18px;
}''',

    "03bright": '''/* 03bright_style.css - Яркий */
body {
    background: linear-gradient(45deg, #ff6b6b, #feca57);
    font-family: 'Poppins', sans-serif;
    min-height: 100vh;
    display: flex;
    justify-content: center;
    padding: 20px;
}

.container {
    max-width: 550px;
    width: 100%;
    background: rgba(255,255,255,0.95);
    backdrop-filter: blur(10px);
    border-radius: 30px;
    padding: 40px 30px;
    box-shadow: 0 30px 60px rgba(0,0,0,0.2);
}

.avatar {
    width: 100px;
    height: 100px;
    background: linear-gradient(45deg, #ff6b6b, #feca57);
    border-radius: 30px;
    margin: 0 auto 15px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 40px;
    color: white;
    transform: rotate(-5deg);
}

.link-card {
    background: white;
    border-radius: 20px;
    padding: 18px 25px;
    text-decoration: none;
    display: flex;
    align-items: center;
    box-shadow: 0 5px 15px rgba(0,0,0,0.05);
    transition: all 0.3s;
    border: 2px solid transparent;
    margin-bottom: 15px;
}

.link-card:hover {
    transform: scale(1.02) translateY(-3px);
    border-color: #ff6b6b;
    box-shadow: 0 15px 30px rgba(255,107,107,0.2);
}

.link-icon {
    width: 45px;
    height: 45px;
    background: linear-gradient(45deg, #ff6b6b20, #feca5720);
    border-radius: 15px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #ff6b6b;
    font-size: 20px;
    margin-right: 15px;
}'''
}

# Создаем папки и файлы
for template in templates:
    folder = f"{template['id']}{template['name']}"
    folder_path = os.path.join(templates_path, folder)

    # Создаем папку
    os.makedirs(folder_path, exist_ok=True)
    print(f"✅ Создана папка {folder}")

    # Создаем пустой HTML файл
    html_file = os.path.join(folder_path, f"{folder}_page.html")
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write("<!-- Сюда вставь HTML шаблона -->")

    # Создаем пустой CSS файл
    css_file = os.path.join(folder_path, f"{folder}_style.css")
    with open(css_file, 'w', encoding='utf-8') as f:
        f.write(f"/* {folder}_style.css - стили для шаблона {template['title']} */")

    print(f"  📄 Созданы файлы: {folder}_page.html и {folder}_style.css")

print("\n✅ Все 10 папок с шаблонами созданы в web/templates/")
print("Теперь нужно скопировать в них HTML и CSS из базы данных")