# bot.py
"""
Точка входа в приложение.
Настраивает и запускает Telegram-бота с обработчиками команд и callback-запросов.
"""
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from config import BOT_TOKEN
from utils.logger import setup_logger
from handlers.start import (
    start_command,
    greeting_callback,
    about_callback,
    back_to_main_callback,
)

# Настройка основного логгера
logger = setup_logger(__name__, level=logging.INFO)


def main() -> None:
    """
    Главная функция приложения.
    Создаёт экземпляр бота, регистрирует обработчики и запускает polling.
    """
    logger.info("🚀 Запуск бота...")

    # Создаём приложение (Application) с токеном бота
    app = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчик команды /start
    app.add_handler(CommandHandler("start", start_command))

    # Регистрируем обработчики callback-запросов от кнопок
    # CallbackQueryHandler будет перехватывать все callback_data,
    # но мы явно укажем pattern для каждого, чтобы избежать конфликтов
    app.add_handler(CallbackQueryHandler(greeting_callback, pattern='^greeting$'))
    app.add_handler(CallbackQueryHandler(about_callback, pattern='^about$'))
    app.add_handler(CallbackQueryHandler(back_to_main_callback, pattern='^back_to_main$'))

    # Запускаем бота в режиме polling (опрос серверов Telegram)
    logger.info("✅ Бот запущен и готов к работе!")
    app.run_polling(allowed_updates=['message', 'callback_query'])


if __name__ == "__main__":
    main()