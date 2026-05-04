# parsers.py
# Универсальные парсеры и валидаторы для всех типов ссылок

import re


def clean_username(username: str) -> str:
    """Очистить username от @, / и пробелов"""
    username = username.strip()
    username = username.replace('@', '').replace('/', '').replace(' ', '')
    return username


def clean_phone(phone: str) -> str:
    """Очистить номер телефона и привести к формату +XXXXXXXXXXX"""
    phone = phone.strip()
    phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    if not phone.startswith('+'):
        phone = '+' + phone
    return phone


def clean_card(card: str) -> str:
    """Очистить номер карты от пробелов и дефисов"""
    card = card.strip()
    card = card.replace(' ', '').replace('-', '')
    return card


def validate_email(email: str) -> bool:
    """Проверить валидность email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_url(url: str) -> bool:
    """Базовая проверка URL"""
    return url.startswith(('http://', 'https://', 't.me/', 'viber://', 'tg://'))


async def parse_and_validate(link_type: str, collected_data: dict) -> tuple:
    """
    Универсальный парсер/валидатор для всех типов ссылок
    Возвращает (url, error_message)
    """
    print(f"🔥🔥🔥 parse_and_validate: link_type = '{link_type}'")
    # ===== СОЦСЕТИ =====
    if link_type == "youtube":
        channel_input = collected_data.get('channel_input', '')
        channel_name = collected_data.get('channel_name', '')
        
        if not channel_input:
            return None, "❌ Введи ID канала или ссылку в поле ввода 👇"
        
        # Если пользователь вставил готовую ссылку
        if channel_input.startswith(('http://', 'https://', 'youtube.com', 'www.youtube.com')):
            return channel_input, None
        
        # Если ввел @username
        if channel_input.startswith('@'):
            username = channel_input.replace('@', '').strip()
            return f"https://youtube.com/@{username}", None
        
        # Если ввел ID канала (длинная строка без пробелов)
        if len(channel_input) > 10 and ' ' not in channel_input:
            return f"https://youtube.com/channel/{channel_input}", None
        
        # Если просто название - считаем что это username
        username = channel_input.strip().replace(' ', '')
        return f"https://youtube.com/@{username}", None
    
    
    
    elif link_type == "instagram":
        username = collected_data.get('username', '')
        if username:
            # Если ввели ссылку
            if username.startswith(('http://', 'https://', 'instagram.com', 'www.instagram.com')):
                return username, None
            # Если ввели @username
            username = username.replace('@', '').replace(' ', '').strip()
            return f"https://instagram.com/{username}", None
        return None, "❌ Укажи username или ссылку"
    
    elif link_type == "tiktok":
        username = collected_data.get('username', '')
        if username:
            # Если ввели ссылку
            if username.startswith(('http://', 'https://', 'tiktok.com', 'www.tiktok.com')):
                return username, None
            # Если ввели @username
            if username.startswith('@'):
                username = username.replace('@', '').strip()
            return f"https://tiktok.com/@{username}", None
        return None, "❌ Укажи username или ссылку"
    
    
    
    elif link_type == "vk":
        choice = collected_data.get('choice')
        
        # Профиль
        if choice == 'profile':
            profile_id = collected_data.get('profile_id', '')
            if not profile_id:
                return None, "❌ Введи ID или короткое имя профиля"
            
            if profile_id.startswith(('http://', 'https://', 'vk.com', 'www.vk.com')):
                
                match = re.search(r'vk\.com/([^/?]+)', profile_id)
                clean_name = match.group(1) if match else profile_id.split('/')[-1].split('?')[0]
            else:
                clean_name = profile_id.strip()
            
            # Для профиля
            if clean_name.isdigit():
                url = f"https://vk.com/id{clean_name}"
                collected_data['profile_id'] = clean_name
            else:
                url = f"https://vk.com/{clean_name}"
                collected_data['profile_id'] = clean_name
            return url, None
        
        # Публичная страница
        elif choice == 'public':
            public_id = collected_data.get('public_id', '')
            if not public_id:
                return None, "❌ Введи ID или короткое имя публичной страницы"
            
            if public_id.startswith(('http://', 'https://', 'vk.com', 'www.vk.com')):
                
                # Ищем club/ или public/ И ВСЁ что после них
                match = re.search(r'vk\.com/((?:public|club)?[^/?]+)', public_id)
                clean_name = match.group(1) if match else public_id.split('/')[-1].split('?')[0]
            else:
                clean_name = public_id.strip()
            
            # Для публичной страницы
            if clean_name.isdigit():
                url = f"https://vk.com/public{clean_name}"
                collected_data['public_id'] = clean_name
            else:
                url = f"https://vk.com/{clean_name}"
                collected_data['public_id'] = clean_name
            return url, None
        
        # Группа
        elif choice == 'group':
            group_id = collected_data.get('group_id', '')
            if not group_id:
                return None, "❌ Введи ID или короткое имя группы"
            
            if group_id.startswith(('http://', 'https://', 'vk.com', 'www.vk.com')):
                
                # Ищем club/ или public/ И ВСЁ что после них
                match = re.search(r'vk\.com/((?:public|club)?[^/?]+)', group_id)
                clean_name = match.group(1) if match else group_id.split('/')[-1].split('?')[0]
            else:
                clean_name = group_id.strip()
            
            # Для группы
            if clean_name.isdigit():
                url = f"https://vk.com/club{clean_name}"
                collected_data['group_id'] = clean_name
            else:
                url = f"https://vk.com/{clean_name}"
                collected_data['group_id'] = clean_name
            return url, None
        
        return None, "❌ Выбери тип (профиль, публичная страница или группа)"
    elif link_type == "ok":
        profile_input = collected_data.get('profile_input', '')
        if not profile_input:
            return None, "❌ Укажи ID или ссылку"
        
        # Если ввели ссылку
        if profile_input.startswith(('http://', 'https://', 'ok.ru')):
            return profile_input, None
        
        # Если ввели просто цифры (ID)
        if profile_input.isdigit():
            # Проверяем, похоже ли на ID группы (обычно короче) или профиля
            if len(profile_input) > 8:  # ID профиля обычно длиннее
                return f"https://ok.ru/profile/{profile_input}", None
            else:
                return f"https://ok.ru/group/{profile_input}", None
        
        # Если ввели именную ссылку
        profile_input = profile_input.replace('@', '').replace(' ', '').strip()
        return f"https://ok.ru/{profile_input}", None
    
    
    
    elif link_type == "facebook":
        choice = collected_data.get('choice')
        
        # Профиль
        if choice == 'profile':
            username = collected_data.get('username', '')
            if not username:
                return None, "❌ Введи username профиля"
            
            if username.startswith(('http://', 'https://', 'facebook.com')):
                
                match = re.search(r'facebook\.com/(?:profile\.php\?id=)?([^/?&]+)', username)
                clean_name = match.group(1) if match else username.split('/')[-1].split('?')[0]
            else:
                clean_name = username.replace('@', '').replace(' ', '').strip()
            
            collected_data['username'] = clean_name
            return f"https://facebook.com/{clean_name}", None
        
        # Страница
        elif choice == 'page':
            page_title = collected_data.get('page_title', '')
            page_username = collected_data.get('page_username', '')
            
            if not page_username:
                return None, "❌ Введи username страницы"
            
            # Обрабатываем username для ссылки
            if page_username.startswith(('http://', 'https://', 'facebook.com')):
                
                match = re.search(r'facebook\.com/([^/?]+)', page_username)
                clean_name = match.group(1) if match else page_username.split('/')[-1].split('?')[0]
            else:
                clean_name = page_username.replace('@', '').replace(' ', '').strip()
            
            # Сохраняем оба поля
            collected_data['page_username'] = clean_name
            # page_title оставляем как есть для отображения
            
            return f"https://facebook.com/{clean_name}", None
        
        # Группа
        elif choice == 'group':
            group_title = collected_data.get('group_title', '')
            group_username = collected_data.get('group_username', '')
            
            if not group_username:
                return None, "❌ Введи username группы"
            
            if group_username.startswith(('http://', 'https://', 'facebook.com')):
                
                match = re.search(r'facebook\.com/groups/([^/?]+)', group_username)
                clean_name = match.group(1) if match else group_username.split('/')[-1].split('?')[0]
            else:
                clean_name = group_username.replace('@', '').replace(' ', '').strip()
            
            collected_data['group_username'] = clean_name
            return f"https://facebook.com/groups/{clean_name}", None
        
        return None, "❌ Выбери тип (профиль, страница или группа)"
    
    
    elif link_type == "twitter":
        username = collected_data.get('username', '')
        if username:
            if username.startswith(('http://', 'https://', 'twitter.com', 'x.com')):
                # Извлекаем только имя из ссылки
                
                match = re.search(r'(?:twitter\.com|x\.com)/([^/?]+)', username)
                if match:
                    clean_name = match.group(1)
                else:
                    clean_name = username.split('/')[-1].split('?')[0]
                collected_data['username'] = clean_name
                return f"https://twitter.com/{clean_name}", None
            username = username.replace('@', '').replace(' ', '').strip()
            return f"https://twitter.com/{username}", None
        return None, "❌ Укажи username или ссылку"
    
    elif link_type == "twitch":
        username = collected_data.get('username', '')
        if username:
            if username.startswith(('http://', 'https://', 'twitch.tv')):
                # Извлекаем только имя из ссылки
                
                match = re.search(r'twitch\.tv/([^/?]+)', username)
                if match:
                    clean_name = match.group(1)
                else:
                    clean_name = username.split('/')[-1].split('?')[0]
                collected_data['username'] = clean_name
                return f"https://twitch.tv/{clean_name}", None
            username = username.replace('@', '').replace(' ', '').strip()
            return f"https://twitch.tv/{username}", None
        return None, "❌ Укажи название канала или ссылку"
    
    elif link_type == "rutube":
        channel_input = collected_data.get('channel_input', '')
        if not channel_input:
            return None, "❌ Введи ID канала или ссылку"
        
        if channel_input.startswith(('http://', 'https://', 'rutube.ru')):
            
            # Ищем ID канала из ссылки rutube.ru/channel/XXXX/
            match = re.search(r'rutube\.ru/channel/([^/?]+)', channel_input)
            if match:
                clean_id = match.group(1)
            else:
                # Если не нашли channel, пробуем просто взять последнюю часть
                clean_id = channel_input.split('/')[-1].split('?')[0]
            
            collected_data['channel_input'] = clean_id
            return f"https://rutube.ru/channel/{clean_id}/", None
        else:
            # Если ввели просто ID
            clean_id = channel_input.strip()
            collected_data['channel_input'] = clean_id
            return f"https://rutube.ru/channel/{clean_id}/", None
    
    elif link_type == "dzen":
        channel_input = collected_data.get('channel_input', '')
        if not channel_input:
            return None, "❌ Введи ID канала или ссылку"
        
        # Если это уже полная ссылка
        if channel_input.startswith(('http://', 'https://', 'dzen.ru', 'www.dzen.ru')):
            # Очищаем ссылку от лишнего
            if 'dzen.ru' in channel_input:
                return channel_input, None
            else:
                return None, "❌ Это не ссылка Дзен"
        
        # Если ввели просто ID
        else:
            # Очищаем ID от лишних символов
            clean_id = channel_input.strip()
            if clean_id.isdigit():
                return f"https://dzen.ru/id/{clean_id}", None
            else:
                # Если это не цифровой ID, возможно это username
                return f"https://dzen.ru/{clean_id}", None
    
    elif link_type == "snapchat":
        username = collected_data.get('username', '')
        if username:
            if username.startswith(('http://', 'https://', 'snapchat.com')):
                # Извлекаем только имя из ссылки
                
                match = re.search(r'snapchat\.com/add/([^/?]+)', username)
                if match:
                    clean_name = match.group(1)
                else:
                    clean_name = username.split('/')[-1].split('?')[0]
                collected_data['username'] = clean_name
                return f"https://snapchat.com/add/{clean_name}", None
            username = username.replace('@', '').replace(' ', '').strip()
            return f"https://snapchat.com/add/{username}", None
        return None, "❌ Укажи username или ссылку"
    
    elif link_type == "likee":
        username = collected_data.get('username', '')
        if username:
            if username.startswith(('http://', 'https://', 'likee.video', 'likee.com')):
                # Извлекаем только имя из ссылки
                
                match = re.search(r'likee\.(?:video|com)/@?([^/?]+)', username)
                if match:
                    clean_name = match.group(1)
                else:
                    clean_name = username.split('/')[-1].split('?')[0].replace('@', '')
                collected_data['username'] = clean_name
                return f"https://likee.video/@{clean_name}", None
            username = username.replace('@', '').replace(' ', '').strip()
            return f"https://likee.video/@{username}", None
        return None, "❌ Укажи username или ссылку"
    elif link_type == "threads":
        username = collected_data.get('username', '')
        if username:
            if username.startswith(('http://', 'https://', 'threads.net')):
                # Извлекаем только имя из ссылки
                
                match = re.search(r'threads\.net/@?([^/?]+)', username)
                if match:
                    clean_name = match.group(1)
                else:
                    clean_name = username.split('/')[-1].split('?')[0].replace('@', '')
                collected_data['username'] = clean_name
                return f"https://threads.net/@{clean_name}", None
            username = username.replace('@', '').replace(' ', '').strip()
            return f"https://threads.net/@{username}", None
        return None, "❌ Укажи username или ссылку"
    
    
    elif link_type == "discord":
        choice = collected_data.get('choice')
        
        # Приглашение на сервер
        if choice == 'invite':
            invite_link = collected_data.get('invite_link', '')
            if not invite_link:
                return None, "❌ Введи ссылку-приглашение или код приглашения"
            
            # Если это уже полная ссылка с http:// или https://
            if invite_link.startswith(('http://', 'https://')):
                if 'discord.gg' in invite_link or 'discord.com/invite' in invite_link:
                    return invite_link, None
                else:
                    return None, "❌ Это не ссылка Discord"
            
            # Если это ссылка вида discord.gg/abc123 (без http)
            elif invite_link.startswith('discord.gg/'):
                return f"https://{invite_link}", None
            
            # Если это ссылка вида discord.com/invite/abc123 (без http)
            elif invite_link.startswith('discord.com/invite/'):
                return f"https://{invite_link}", None
            
            # Если ввели просто код (abc123)
            else:
                clean_code = invite_link.strip()
                return f"https://discord.gg/{clean_code}", None
        
        # Профиль пользователя
        elif choice == 'profile':
            user_id = collected_data.get('user_id', '')
            if not user_id:
                return None, "❌ Введи ID пользователя или ссылку на профиль"
            
            # Если это ссылка с http
            if user_id.startswith(('http://', 'https://')):
                if 'discord.com/users/' in user_id or 'discordapp.com/users/' in user_id:
                    return user_id, None
                else:
                    return None, "❌ Это не ссылка Discord"
            
            # Если это ссылка вида discord.com/users/123456 (без http)
            elif user_id.startswith('discord.com/users/'):
                return f"https://{user_id}", None
            
            # Если ввели просто ID (число)
            else:
                clean_id = user_id.strip()
                if clean_id.isdigit():
                    return f"https://discord.com/users/{clean_id}", None
                else:
                    return None, "❌ ID пользователя должен состоять только из цифр"
        
        return None, "❌ Выбери тип (приглашение или профиль)"
    
        
    elif link_type == "email":
        email = collected_data.get('email', '').strip()
        if not email:
            return None, "❌ Email не указан"
        
        # Простая валидация
        if '@' not in email or '.' not in email:
            return None, "❌ Неверный формат email"
        
        # Сохраняем как mailto: ссылку
        return f"mailto:{email}", None
    
    
    
    # ===== МЕССЕНДЖЕРЫ =====
    
    elif link_type == "whatsapp":
        phone = collected_data.get('phone', '')
        if not phone:
            return None, "❌ Введи номер телефона или ссылку"
        
        # Извлекаем только цифры для формирования ссылки
        if 'wa.me' in phone or 'whatsapp.com' in phone:
            match = re.search(r'(?:wa\.me/|phone=)(\d+)', phone)
            clean_number = match.group(1) if match else re.sub(r'\D', '', phone)
        else:
            clean_number = re.sub(r'\D', '', phone)
        
        if clean_number.startswith('8') and len(clean_number) == 11:
            clean_number = '7' + clean_number[1:]
        
        if not clean_number:
            return None, "❌ Некорректный номер"
        
        collected_data['phone_display'] = '+' + clean_number
        collected_data['phone_clean'] = clean_number
        collected_data['phone'] = clean_number
        
        return f"https://wa.me/{clean_number}", None
    
    elif link_type == "viber":
        phone = collected_data.get('phone', '')
        if not phone:
            return None, "❌ Введи номер телефона или ссылку"
        
        if 'viber.click' in phone or 'viber.com' in phone:
            match = re.search(r'(?:viber\.click/|number=)(\d+)', phone)
            clean_number = match.group(1) if match else re.sub(r'\D', '', phone)
        else:
            clean_number = re.sub(r'\D', '', phone)
        
        if not clean_number:
            return None, "❌ Некорректный номер"
        
        collected_data['phone_display'] = '+' + clean_number
        collected_data['phone_clean'] = clean_number
        collected_data['phone'] = clean_number
        
        # Используем https ссылку для универсальности (откроется и в браузере, и в приложении)
        return f"https://viber.click/{clean_number}", None
    
    elif link_type == "telegram":
        identifier = collected_data.get('identifier', '').strip()
        if not identifier:
            return None, "❌ Введи username или ссылку"
        
        # Если полная ссылка - возвращаем как есть
        if identifier.startswith(('http://', 'https://')):
            if 't.me' in identifier or 'telegram.org' in identifier:
                return identifier, None
            return None, "❌ Это не похоже на ссылку Telegram"
        
        # Ссылка без протокола
        if identifier.startswith('t.me/'):
            return f"https://{identifier}", None
        
        # Пригласительная ссылка
        if identifier.startswith('+') or '/+' in identifier:
            invite_code = identifier.replace('t.me/', '').replace('+', '').strip()
            return f"https://t.me/+{invite_code}", None
        
        # Просто username
        clean_username = identifier.replace('@', '').replace(' ', '').strip()
        if not re.match(r'^[a-zA-Z0-9_]{5,}$', clean_username):
            return None, "❌ Некорректный username (минимум 5 символов)"
        
        return f"https://t.me/{clean_username}", None
    
    elif link_type == "signal":
        username = collected_data.get('username', '')
        if not username:
            return None, "❌ Введи Signal ID или ссылку"
        
        if 'signal.me' in username:
            match = re.search(r'signal\.me/#u/([a-zA-Z0-9_.]+)', username)
            clean_username = match.group(1) if match else username.split('/')[-1]
        else:
            clean_username = username.strip().replace('@', '')
        
        if not clean_username:
            return None, "❌ Некорректный Signal ID"
        
        collected_data['username'] = clean_username
        return f"https://signal.me/#u/{clean_username}", None
    
    elif link_type == "zalo":
        phone = collected_data.get('phone', '')
        if not phone:
            return None, "❌ Введи номер телефона или ссылку Zalo"
        
        if 'zalo.me' in phone:
            match = re.search(r'zalo\.me/(\d+)', phone)
            clean_number = match.group(1) if match else re.sub(r'\D', '', phone)
        else:
            clean_number = re.sub(r'\D', '', phone)
    
        if not clean_number:
            return None, "❌ Некорректный номер (только цифры)"
        
        collected_data['phone_display'] = '+' + clean_number
        collected_data['phone_clean'] = clean_number
        collected_data['phone'] = clean_number
        
        return f"https://zalo.me/{clean_number}", None
    
    elif link_type == "max":
        user_input = collected_data.get('id') or collected_data.get('phone', '')
        if not user_input:
            return None, "❌ Введи ID пользователя Max"
        
        # Извлекаем цифры (ID) из ссылки или текста
        match = re.search(r'(\d+)$', user_input.strip())
        clean_id = match.group(1) if match else re.sub(r'\D', '', user_input)
        
        if not clean_id:
            return None, "❌ Некорректный ID"
        
        collected_data['id_clean'] = clean_id
        collected_data['id'] = clean_id
        
        # Формируем прямую ссылку через старт-параметр бота
        return f"https://t.me/max?start={clean_id}", None
    
    elif link_type == "googlechat":
        email_input = collected_data.get('email', '') or collected_data.get('phone', '')
        if not email_input:
            return None, "❌ Введи email или ссылку Google Chat"
        
        # Если ввели прямую ссылку на чат/пространство
        if 'chat.google.com' in email_input:
            return email_input.strip(), None
            
        # Если ввели email
        match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', email_input)
        if match:
            clean_email = match.group(1)
            collected_data['email'] = clean_email
            # Для Google Chat нет универсальной публичной ссылки по email,
            # поэтому возвращаем email. В шаблоне это обработается как копирование.
            return clean_email, None
            
        return None, "❌ Укажите корректный email или ссылку"
    
    
    # ===== ДОНАТЫ (БЕЗ @) =====
    elif link_type == "patreon":
        username = collected_data.get('username', '')
        if not username:
            return None, "❌ Введите название страницы Patreon"
        
        # Очищаем username (убираем @ если случайно ввели)
        if username.startswith(('http://', 'https://', 'patreon.com')):
            match = re.search(r'patreon\.com/([^/?&]+)', username)
            clean_name = match.group(1) if match else username.split('/')[-1].split('?')[0]
        else:
            clean_name = username.replace('@', '').replace(' ', '').strip()
        
        collected_data['username'] = clean_name
        return f"https://patreon.com/{clean_name}", None
    
    elif link_type == "boosty":
        username = collected_data.get('username', '')
        if not username:
            return None, "❌ Введите название канала Boosty"
        
        if username.startswith(('http://', 'https://', 'boosty.to')):
            match = re.search(r'boosty\.to/([^/?&]+)', username)
            clean_name = match.group(1) if match else username.split('/')[-1].split('?')[0]
        else:
            clean_name = username.replace('@', '').replace(' ', '').strip()
        
        collected_data['username'] = clean_name
        return f"https://boosty.to/{clean_name}", None
    
    elif link_type == "donationalerts":
        username = collected_data.get('username', '')
        if not username:
            return None, "❌ Введите ID на Donation Alerts"
        
        if username.startswith(('http://', 'https://', 'donationalerts.com')):
            match = re.search(r'donationalerts\.com/r/([^/?&]+)', username)
            clean_name = match.group(1) if match else username.split('/')[-1].split('?')[0]
        else:
            clean_name = username.replace('@', '').replace(' ', '').strip()
        
        collected_data['username'] = clean_name
        return f"https://www.donationalerts.com/r/{clean_name}", None
    
    elif link_type == "kofi":
        username = collected_data.get('username', '')
        if not username:
            return None, "❌ Введите username Ko-fi"
        
        if username.startswith(('http://', 'https://', 'ko-fi.com')):
            match = re.search(r'ko-fi\.com/([^/?&]+)', username)
            clean_name = match.group(1) if match else username.split('/')[-1].split('?')[0]
        else:
            clean_name = username.replace('@', '').replace(' ', '').strip()
        
        collected_data['username'] = clean_name
        return f"https://ko-fi.com/{clean_name}", None
    
    elif link_type == "buymeacoffee":
        username = collected_data.get('username', '')
        if not username:
            return None, "❌ Введите username Buy Me a Coffee"
        
        if username.startswith(('http://', 'https://', 'buymeacoffee.com')):
            match = re.search(r'buymeacoffee\.com/([^/?&]+)', username)
            clean_name = match.group(1) if match else username.split('/')[-1].split('?')[0]
        else:
            clean_name = username.replace('@', '').replace(' ', '').strip()
        
        collected_data['username'] = clean_name
        return f"https://www.buymeacoffee.com/{clean_name}", None
    
    
    
    
    # ===== МАГАЗИНЫ =====
    elif link_type == "ozon":
        url = collected_data.get('url', '')
        if not url:
            return None, "❌ Введите ссылку на Ozon"
        
        # Очищаем от пробелов
        url = url.strip()
        
        # Проверяем разные форматы
        if url.startswith(('http://', 'https://')):
            if "ozon.ru" not in url and "ozon.com" not in url:
                return None, "❌ Это не похоже на ссылку Ozon. Ссылка должна содержать ozon.ru"
            return url, None
        else:
            # Если без протокола
            if "ozon.ru" in url or "ozon.com" in url:
                return f"https://{url}", None
            # Если просто текст
            elif url.isdigit() or url.startswith('product/'):
                return f"https://www.ozon.ru/product/{url}", None
            elif url.startswith('seller/'):
                return f"https://www.ozon.ru/seller/{url.replace('seller/', '')}", None
            else:
                return None, "❌ Введите корректную ссылку на Ozon (например: ozon.ru/product/123 или https://www.ozon.ru/seller/456)"
    
    elif link_type == "wildberries":
        url = collected_data.get('url', '')
        if not url:
            return None, "❌ Введите ссылку на Wildberries"
        
        url = url.strip()
        
        if url.startswith(('http://', 'https://')):
            if "wildberries.ru" not in url and "wb.ru" not in url:
                return None, "❌ Это не похоже на ссылку Wildberries"
            return url, None
        else:
            if "wildberries.ru" in url or "wb.ru" in url:
                return f"https://{url}", None
            elif url.isdigit() or url.startswith('catalog/'):
                clean = url.replace('catalog/', '').strip()
                return f"https://www.wildberries.ru/catalog/{clean}/detail.aspx", None
            elif url.startswith('seller/'):
                clean = url.replace('seller/', '').strip()
                return f"https://www.wildberries.ru/seller/{clean}", None
            else:
                return None, "❌ Введите корректную ссылку на Wildberries"
    
    elif link_type == "avito":
        url = collected_data.get('url', '')
        if not url:
            return None, "❌ Введите ссылку на Avito"
        
        url = url.strip()
        
        if url.startswith(('http://', 'https://')):
            if "avito.ru" not in url:
                return None, "❌ Это не похоже на ссылку Avito"
            return url, None
        else:
            if "avito.ru" in url:
                return f"https://{url}", None
            elif url.replace('/', '').isdigit() or 'item' in url:
                # Если просто ID объявления
                item_id = url.split('/')[-1].split('?')[0]
                return f"https://www.avito.ru/{item_id}", None
            else:
                return None, "❌ Введите корректную ссылку на Avito (например: avito.ru/moskva/tovary/123456789)"
    
    elif link_type == "yandex_market":
        url = collected_data.get('url', '')
        if not url:
            return None, "❌ Введите ссылку на Яндекс Маркет"
        
        url = url.strip()
        
        if url.startswith(('http://', 'https://')):
            if "market.yandex.ru" not in url:
                return None, "❌ Это не похоже на ссылку Яндекс Маркет"
            return url, None
        else:
            if "market.yandex.ru" in url:
                return f"https://{url}", None
            elif url.startswith('product/') or url.isdigit():
                product_id = url.replace('product/', '').strip()
                return f"https://market.yandex.ru/product/{product_id}", None
            elif url.startswith('cc/'):
                return f"https://market.yandex.ru/cc/{url.replace('cc/', '')}", None
            else:
                return None, "❌ Введите корректную ссылку на Яндекс Маркет"
    
    elif link_type == "aliexpress":
        url = collected_data.get('url', '')
        if not url:
            return None, "❌ Введите ссылку на AliExpress"
        
        url = url.strip()
        
        if url.startswith(('http://', 'https://')):
            if "aliexpress" not in url:
                return None, "❌ Это не похоже на ссылку AliExpress"
            return url, None
        else:
            if "aliexpress" in url:
                return f"https://{url}", None
            elif url.isdigit() or 'item' in url:
                item_id = url.split('/')[-1].split('?')[0]
                return f"https://aliexpress.ru/item/{item_id}.html", None
            elif url.startswith('store/'):
                store_id = url.replace('store/', '').strip()
                return f"https://aliexpress.ru/store/{store_id}", None
            else:
                return None, "❌ Введите корректную ссылку на AliExpress"
    
    elif link_type == "kazanexpress":
        url = collected_data.get('url', '')
        if not url:
            return None, "❌ Введите ссылку на KazanExpress"
        
        url = url.strip()
        
        if url.startswith(('http://', 'https://')):
            if "kazanexpress.ru" not in url:
                return None, "❌ Это не похоже на ссылку KazanExpress"
            return url, None
        else:
            if "kazanexpress.ru" in url:
                return f"https://{url}", None
            elif url.isdigit() or url.startswith('product/'):
                product_id = url.replace('product/', '').strip()
                return f"https://kazanexpress.ru/product/{product_id}", None
            else:
                return None, "❌ Введите корректную ссылку на KazanExpress"
    
    elif link_type == "amazon":
        url = collected_data.get('url', '')
        if not url:
            return None, "❌ Введите ссылку на Amazon"
        
        url = url.strip()
        
        if url.startswith(('http://', 'https://')):
            if "amazon" not in url:
                return None, "❌ Это не похоже на ссылку Amazon"
            return url, None
        else:
            if "amazon" in url:
                return f"https://{url}", None
            elif url.startswith('dp/') or url.startswith('product/'):
                asin = url.split('/')[-1].split('?')[0]
                return f"https://www.amazon.com/dp/{asin}", None
            elif len(url) == 10:  # ASIN код
                return f"https://www.amazon.com/dp/{url}", None
            else:
                return None, "❌ Введите корректную ссылку на Amazon"
    
    elif link_type == "ebay":
        url = collected_data.get('url', '')
        if not url:
            return None, "❌ Введите ссылку на eBay"
        
        url = url.strip()
        
        if url.startswith(('http://', 'https://')):
            if "ebay" not in url:
                return None, "❌ Это не похоже на ссылку eBay"
            return url, None
        else:
            if "ebay" in url:
                return f"https://{url}", None
            elif url.isdigit() or url.startswith('itm/'):
                item_id = url.replace('itm/', '').strip()
                return f"https://www.ebay.com/itm/{item_id}", None
            elif url.startswith('usr/'):
                username = url.replace('usr/', '').strip()
                return f"https://www.ebay.com/usr/{username}", None
            else:
                return None, "❌ Введите корректную ссылку на eBay"
    
    elif link_type == "etsy":
        url = collected_data.get('url', '')
        if not url:
            return None, "❌ Введите ссылку на Etsy"
        
        url = url.strip()
        
        if url.startswith(('http://', 'https://')):
            if "etsy.com" not in url:
                return None, "❌ Это не похоже на ссылку Etsy"
            return url, None
        else:
            if "etsy.com" in url:
                return f"https://{url}", None
            elif url.startswith('shop/'):
                shop_name = url.replace('shop/', '').strip()
                return f"https://www.etsy.com/shop/{shop_name}", None
            elif url.isdigit() or url.startswith('listing/'):
                listing_id = url.replace('listing/', '').strip()
                return f"https://www.etsy.com/listing/{listing_id}", None
            else:
                return None, "❌ Введите корректную ссылку на Etsy"
    
    elif link_type == "shopify":
        url = collected_data.get('url', '')
        if not url:
            return None, "❌ Введите ссылку на Shopify магазин"
        
        url = url.strip()
        
        if url.startswith(('http://', 'https://')):
            if "myshopify.com" not in url and "shopify.com" not in url:
                return None, "❌ Это не похоже на ссылку Shopify"
            return url, None
        else:
            if "myshopify.com" in url or "shopify.com" in url:
                return f"https://{url}", None
            elif '.' in url and not url.startswith(('http', 'https')):
                # Если это домен вида my-store.myshopify.com
                return f"https://{url}", None
            else:
                return None, "❌ Введите корректную ссылку на Shopify (например: my-store.myshopify.com)"
            
            
            
           
            
    # Универсальный сбор данных из того, что ввел юзер
    # Собираем все возможные поля, которые могут прийти из разных конфигов
    val = (collected_data.get('identifier', '').strip() or
           collected_data.get('link', '').strip() or
           collected_data.get('login', '').strip() or
           collected_data.get('iban', '').strip())
    print(f"🔥 parse_and_validate вызван с link_type={link_type}")
    
    # ===== 1. ПРЯМЫЕ ССЫЛКИ (СРАЗУ НА ОПЛАТУ) =====
    if link_type == "paypal":
        if not val: return None, "❌ Введите PayPal Username или ссылку"
        if val.startswith(('http', 'paypal.me')):
            return (val if val.startswith('http') else f"https://{val}"), None
        return f"https://www.paypal.me/{val.replace('@', '').replace(' ', '')}", None
    
    elif link_type == "revolut":
        if not val: return None, "❌ Введите Revolut Username"
        if val.startswith(('http', 'revolut.me')):
            return (val if val.startswith('http') else f"https://{val}"), None
        return f"https://revolut.me/{val.replace('@', '').replace(' ', '')}", None
    
    elif link_type == "wise":
        if not val: return None, "❌ Введите Wise никнейм или ссылку"
        if val.startswith(('http', 'wise.com')):
            return (val if val.startswith('http') else f"https://{val}"), None
        return f"https://wise.com/pay/me/{val.replace('@', '').replace(' ', '')}", None
    
    elif link_type == "yoomoney":
        if not val: return None, "❌ Введите номер кошелька ЮMoney"
        # Чистим номер от пробелов для ссылки
        return f"https://yoomoney.ru/to/{val.replace(' ', '')}", None
        
    elif link_type == "vkpay":
        if not val: return None, "❌ Введите ID или ссылку VK Pay"
        # Вырезаем ID, даже если вставили сложную ссылку
        clean_id = val.split('/')[-1].replace('id', '').replace('vkpay', '').replace('#to', '')
        return f"https://vk.com/vkpay#to{clean_id}", None
    
    elif link_type == "payme":
        if not val: return None, "❌ Введите ссылку или ID Payme"
        if not val.startswith('http'):
            v = val.replace(' ', '')
            return f"https://payme.uz/{v if v.startswith('@') else '@' + v}", None
        return val, None
    
    elif link_type == "click_uz":
        if not val: return None, "❌ Введите номер или ID Click"
        # Ключ click_uz совпадает с конфигом, теперь не будет ошибки "не поддерживается"
        v = val.replace('+', '').replace(' ', '')
        return (val if val.startswith('http') else f"https://click.uz/pay/{v}"), None
    
    elif link_type == "monobank":
        if not val: return None, "❌ Введите ссылку Monobank"
        return (val if val.startswith('http') else f"https://{val}"), None
    
    elif link_type == "tbcpay":
        if not val: return None, "❌ Введите данные TBC Pay"
        # Если ты хочешь МОДАЛКУ, то URL должен быть "#"
        # Тогда шаблон увидит, что реальной ссылки нет, и откроет окно с реквизитами
        return "#", None
    
    # ===== 2. БАНКОВСКИЕ ПЕРЕВОДЫ (ОТКРЫВАЮТ МОДАЛКУ, URL = "#") =====
    elif link_type in ["iban", "swift", "kaspi", "idram"]:
        if not val: return None, f"❌ Данные для {link_type.upper()} обязательны"
        
        if link_type == "iban" and len(val.replace(' ', '')) < 10:
            return None, "❌ Введен слишком короткий номер счета"
            
        return "#", None
    
    
    # ===== КРИПТОВАЛЮТЫ (USDT, BTC, ETH и т.д.) =====
    elif link_type in ["usdt", "btc", "eth", "ton", "sol", "trx", "bnb", "doge", "ltc", "xrp", "ada", "dot", "matic"]:
        # Ищем адрес в разных возможных полях
        address = (val or
                   collected_data.get('address', '') or
                   collected_data.get('wallet_address', '') or
                   collected_data.get('wallet', ''))
        if not address:
            return None, f"❌ Введите адрес кошелька {link_type.upper()}"
        return "#", None
    
    # Если ничего не подошло
    return "#", f"❌ Тип {link_type} не поддерживается"
