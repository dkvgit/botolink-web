# D:\aRabota\TelegaBoom\030_mylinkspace\supabase\functions\telegram-bot\index.py
import os
import json
import asyncio
# Импортируем само приложение из твоего существующего кода
# (При деплое пути нужно будет подправить под структуру Supabase)
from bot.main import application

async def main(request):
    # # для Python
    # Проверяем, что это POST запрос от Telegram
    if request.method == "POST":
        try:
            # Получаем JSON с данными сообщения
            payload = await request.json()
            
            # Создаем объект Update из JSON
            from telegram import Update
            update = Update.de_json(payload, application.bot)
            
            # Запускаем обработку этого конкретного сообщения
            # В облаке мы используем асинхронный контекст
            async with application:
                await application.process_update(update)
            
            # Возвращаем Telegram ответ, что всё ок
            return Response.new("OK", status=200)
        except Exception as e:
            # Если что-то упало, пишем в логи Supabase
            print(f"Ошибка: {str(e)}")
            return Response.new(json.dumps({"error": str(e)}), status=500)
    
    return Response.new("Only POST allowed", status=405)