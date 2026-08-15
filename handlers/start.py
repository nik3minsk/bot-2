# handlers/start.py
"""
Модуль обработчиков команды /start и callback-запросов главного меню.
"""
from telegram import Update
from telegram.ext import ContextTypes

from utils.logger import setup_logger
from keyboards.main_menu import get_main_menu_keyboard, get_back_menu_keyboard

# Создаём логгер для этого модуля
logger = setup_logger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /start.
    Отправляет приветственное сообщение и показывает главное меню.

    Args:
        update (Update): Объект обновления от Telegram
        context (ContextTypes.DEFAULT_TYPE): Контекст обработчика
    """
    user = update.effective_user
    user_name = user.first_name if user.first_name else "Пользователь"

    # Логируем запуск бота пользователем
    logger.info(f"Пользователь {user.id} ({user_name}) запустил бота")

    # Формируем приветственное сообщение
    welcome_text = (
        f"👋 Привет, {user_name}!\n\n"
        f"Я — твой помощник. Вот что я умею:\n"
        f"• 🧠 Отвечать на простые команды\n"
        f"• 📊 Показывать меню с кнопками\n\n"
        f"Выбери действие ниже:"
    )

    # Отправляем сообщение с клавиатурой
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu_keyboard()
    )


async def greeting_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик нажатия на кнопку "👋 Приветствие".
    Отправляет приветственное сообщение.

    Args:
        update (Update): Объект обновления от Telegram
        context (ContextTypes.DEFAULT_TYPE): Контекст обработчика
    """
    query = update.callback_query
    await query.answer()  # Подтверждаем нажатие (убираем "часики")

    user = update.effective_user
    user_name = user.first_name if user.first_name else "Пользователь"

    logger.info(f"Пользователь {user.id} запросил приветствие")

    # Текст приветствия
    greeting_text = (
        f"🌟 Привет, {user_name}!\n\n"
        f"Рад тебя видеть! Я — бот, созданный для помощи в работе с данными.\n"
        f"Пока что я умею только показывать меню, но в будущем научусь:\n"
        f"• 📧 Обрабатывать почту\n"
        f"• 📊 Анализировать данные из 1С\n"
        f"• 🤖 Автоматизировать рутинные задачи\n\n"
        f"Жди обновлений! 🚀"
    )

    # Редактируем текущее сообщение, показывая приветствие и кнопку "Назад"
    await query.edit_message_text(
        greeting_text,
        reply_markup=get_back_menu_keyboard()
    )


async def about_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик нажатия на кнопку "ℹ️ О боте".
    Показывает информацию о боте.

    Args:
        update (Update): Объект обновления от Telegram
        context (ContextTypes.DEFAULT_TYPE): Контекст обработчика
    """
    query = update.callback_query
    await query.answer()

    logger.info(f"Пользователь {update.effective_user.id} запросил информацию о боте")

    about_text = (
        "🤖 <b>О боте</b>\n\n"
        "📌 <b>Версия:</b> 2.0.0\n"
        "📌 <b>Автор:</b> Команда разработки\n"
        "📌 <b>Назначение:</b> Универсальный помощник для бизнес-задач\n\n"
        "🔧 <b>Технологии:</b>\n"
        "• Python 3.11+\n"
        "• python-telegram-bot 22.6\n"
        "• Docker (в планах)\n\n"
        "📅 <b>Дата создания:</b> 2026\n"
        "🔄 <b>Статус:</b> В разработке"
    )

    await query.edit_message_text(
        about_text,
        parse_mode='HTML',
        reply_markup=get_back_menu_keyboard()
    )


async def back_to_main_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик нажатия на кнопку "🔙 Назад".
    Возвращает пользователя в главное меню.

    Args:
        update (Update): Объект обновления от Telegram
        context (ContextTypes.DEFAULT_TYPE): Контекст обработчика
    """
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    user_name = user.first_name if user.first_name else "Пользователь"

    logger.info(f"Пользователь {user.id} вернулся в главное меню")

    # Возвращаем главное меню
    await query.edit_message_text(
        f"👋 Главное меню, {user_name}!\n\nВыберите действие:",
        reply_markup=get_main_menu_keyboard()
    )