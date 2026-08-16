# config.py
"""
Модуль конфигурации приложения.
Загружает переменные окружения из файла .env и предоставляет их в виде констант.
"""
import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Токен бота — обязательный параметр
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан в .env файле!")

# CHAT_ID — может использоваться для отправки уведомлений в конкретный чат
CHAT_ID = os.getenv("CHAT_ID")

# Настройки логирования
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/bot.log")