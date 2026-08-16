# handlers/start.py
"""
Модуль обработчиков команды /start и callback-запросов главного меню.
"""
from database.user_models import get_user_by_id
from telegram import Update
from telegram.ext import ContextTypes

from handlers.admin import list_users
from handlers.register import start_register

from utils.logger import get_logger  # <-- ИСПРАВЛЕНО: импортируем get_logger
from keyboards.main_menu import get_main_menu_keyboard, get_back_menu_keyboard

# Создаём логгер для этого модуля
logger = get_logger(__name__)  # <-- ИСПРАВЛЕНО: используем get_logger


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /start.
    Отправляет приветственное сообщение и показывает главное меню.
    """
    logger.info(f"Пользователь {update.effective_user.id} вызвал /start")

    user_id = update.effective_user.id
    user = get_user_by_id(user_id)

    # Если пользователь не зарегистрирован
    if not user:
        await update.message.reply_text(
            "👋 Добро пожаловать!\n"
            "Для начала работы необходимо зарегистрироваться.\n"
            "Введите /register для регистрации."
        )
        return

    # Если заявка на рассмотрении
    if user.get('status') == 'pending':
        await update.message.reply_text(
            "⏳ Ваша заявка на рассмотрении.\n"
            "Администратор свяжется с вами."
        )
        return

    # Если заявка отклонена
    if user.get('status') == 'rejected':
        await update.message.reply_text(
            "❌ Ваша заявка была отклонена.\n"
            "Обратитесь к администратору."
        )
        return

    user_name = update.effective_user.first_name if update.effective_user.first_name else "Пользователь"

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
    """Обработчик нажатия на кнопку "👋 Приветствие"."""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    user_name = user.first_name if user.first_name else "Пользователь"

    logger.info(f"Пользователь {user.id} запросил приветствие")

    greeting_text = (
        f"🌟 Привет, {user_name}!\n\n"
        f"Рад тебя видеть! Я — бот, созданный для помощи в работе с данными.\n"
        f"Пока что я умею только показывать меню, но в будущем научусь:\n"
        f"• 📧 Обрабатывать почту\n"
        f"• 📊 Анализировать данные из 1С\n"
        f"• 🤖 Автоматизировать рутинные задачи\n\n"
        f"Жди обновлений! 🚀"
    )

    await query.edit_message_text(
        greeting_text,
        reply_markup=get_back_menu_keyboard()
    )


async def about_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатия на кнопку "ℹ️ О боте"."""
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
    """Обработчик нажатия на кнопку "🔙 Назад"."""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    user_name = user.first_name if user.first_name else "Пользователь"

    logger.info(f"Пользователь {user.id} вернулся в главное меню")

    await query.edit_message_text(
        f"👋 Главное меню, {user_name}!\n\nВыберите действие:",
        reply_markup=get_main_menu_keyboard()
    )




async def register_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатия на кнопку 'Регистрация'."""
    query = update.callback_query
    await query.answer()

    # Вызываем функцию start_register
    await start_register(update, context)