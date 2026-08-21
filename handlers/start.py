# handlers/start.py
"""
Модуль обработчиков команды /start и callback-запросов главного меню.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database.resource_models import get_min_days
from database.user_models import get_user_by_id
from handlers.admin import list_users
from handlers.monitoring import monitoring_resources
from handlers.register import start_register
from middleware.auth import get_user_role
from utils.logger import get_logger
from keyboards.main_menu import get_main_menu_keyboard, get_back_menu_keyboard

# Создаём логгер для этого модуля
logger = get_logger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /start.
    Отправляет приветственное сообщение и показывает главное меню.
    """
    logger.info(f"Пользователь {update.effective_user.id} вызвал /start")


    user_id = update.effective_user.id
    user = get_user_by_id(user_id)
    roles = get_user_role(user_id)
    logger.info(f"Роли пользователя {user_id}: {roles}")  #

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

    # Отправляем сообщение с клавиатурой (передаём роли)
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu_keyboard(roles)  # <-- передаём роли
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
    roles = get_user_role(update.effective_user.id)

    logger.info(f"Пользователь {user.id} вернулся в главное меню")

    await query.edit_message_text(
        f"👋 Главное меню, {user_name}!\n\nВыберите действие:",
        reply_markup=get_main_menu_keyboard(roles)  # <-- передаём роли
    )


async def register_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатия на кнопку 'Регистрация'."""
    query = update.callback_query
    await query.answer()
    await start_register(update, context)


async def menu_admin_dev(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Раздел 'Admin (dev)'."""
    query = update.callback_query
    await query.answer()

    # Проверяем доступ
    user_id = update.effective_user.id
    roles = get_user_role(user_id)

    if 'dev' not in roles and 'admin' not in roles:
        await query.edit_message_text("⛔ У вас нет доступа к этому разделу.")
        return

    # ========== НОВАЯ ЛОГИКА ==========
    # Проверяем, есть ли ресурсы в базе
    from database.resource_models import get_all_resources
    resources = get_all_resources()

    if not resources:
        # Если ресурсов нет — показываем кнопку "Добавить ресурс"
        monitoring_text = "➕ Добавить ресурс"
        monitoring_callback = 'monitoring_add'  # <-- этот callback уже есть в bot.py
    else:
        # Если ресурсы есть — показываем мониторинг с количеством дней
        min_days = get_min_days()
        if min_days is not None:
            if min_days < 10:
                monitoring_text = f"🌐 Мониторинг ресурсов ({min_days} дн!)"
            else:
                monitoring_text = f"🌐 Мониторинг ресурсов ({min_days} дн)"
        else:
            monitoring_text = "🌐 Мониторинг ресурсов (—)"
        monitoring_callback = 'monitoring_resources'  # <-- этот callback уже есть в bot.py

    keyboard = [
        [InlineKeyboardButton("👥 Управление пользователями", callback_data='admin_list_users')],
        [InlineKeyboardButton(monitoring_text, callback_data=monitoring_callback)],  # <-- изменённая строка
        [InlineKeyboardButton("🔙 В главное меню", callback_data='back_to_main')],
    ]

    await query.edit_message_text(
        "🔧 <b>Панель разработчика</b>\n\n"
        "Выберите действие:",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )



async def menu_personal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Раздел 'Личное'."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("👤 Раздел 'Личное' (в разработке).")

async def menu_monitoring(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Раздел 'Мониторинг'."""
    query = update.callback_query
    await query.answer()
    # Здесь вызываем monitoring_resources
    await monitoring_resources(update, context)
    # await query.edit_message_text("📊 Раздел 'Мониторинг' (в разработке).")

async def menu_work(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Раздел 'Работа'."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("💼 Раздел 'Работа' (в разработке).")

async def menu_mail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Раздел 'Обработка почты'."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📧 Раздел 'Обработка почты' (в разработке).")




async def menu_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Раздел 'Настройки'."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("⚙️ Раздел 'Настройки' (в разработке).")


async def monitoring_resources_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Раздел 'Мониторинг ресурсов'."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🌐 <b>Мониторинг ресурсов</b>\n\nРаздел в разработке.", parse_mode='HTML')