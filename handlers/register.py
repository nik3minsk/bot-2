"""
Обработчики для регистрации пользователей
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database.user_models import create_user, get_user_by_id, update_user_status, get_all_users
from utils.logger import get_logger

logger = get_logger(__name__)

# Состояния для регистрации
WAITING_FULL_NAME = 1
WAITING_EMAIL = 2
WAITING_ROLES = 3

# Доступные роли
AVAILABLE_ROLES = {
    'manager': 'Менеджер',
    'buh': 'Бухгалтер',
    'user': 'Пользователь'
}

async def start_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает процесс регистрации."""
    user_id = update.effective_user.id
    existing_user = get_user_by_id(user_id)

    if existing_user:
        if existing_user.get('status') == 'approved':
            await update.message.reply_text(
                "✅ Вы уже зарегистрированы!\n"
                "Введите /start для главного меню."
            )
            return ConversationHandler.END
        elif existing_user.get('status') == 'pending':
            await update.message.reply_text(
                "⏳ Ваша заявка на рассмотрении.\n"
                "Администратор свяжется с вами."
            )
            return ConversationHandler.END
        elif existing_user.get('status') == 'rejected':
            await update.message.reply_text(
                "❌ Ваша заявка была отклонена.\n"
                "Обратитесь к администратору для повторной регистрации."
            )
            return ConversationHandler.END

    await update.message.reply_text(
        "📝 Добро пожаловать! Для регистрации ответьте на несколько вопросов.\n\n"
        "Введите ваше полное ФИО:"
    )
    return WAITING_FULL_NAME

async def get_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает ФИО пользователя."""
    full_name = update.message.text.strip()
    if len(full_name) < 5:
        await update.message.reply_text(
            "❌ Слишком короткое имя. Введите полное ФИО:"
        )
        return WAITING_FULL_NAME

    context.user_data['full_name'] = full_name
    await update.message.reply_text(
        "📧 Введите ваш email (для связи):"
    )
    return WAITING_EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает email пользователя."""
    email = update.message.text.strip()
    if '@' not in email or '.' not in email:
        await update.message.reply_text(
            "❌ Некорректный email. Попробуйте ещё раз:"
        )
        return WAITING_EMAIL

    context.user_data['email'] = email
    await update.message.reply_text(
        "✅ Заявка отправлена на рассмотрение!\n"
        "Администратор свяжется с вами после проверки."
    )

    # Создаём пользователя со статусом 'pending'
    user_id = update.effective_user.id
    create_user(
        telegram_id=user_id,
        full_name=context.user_data['full_name'],
        email=context.user_data['email'],
        roles=['guest'],
        status='pending'
    )

    # Уведомляем администратора
    admin_keyboard = [
        [InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{user_id}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{user_id}")]
    ]
    admin_text = (
        f"🆕 Новая заявка на регистрацию!\n\n"
        f"👤 Пользователь: {context.user_data['full_name']}\n"
        f"📧 Email: {email}\n"
        f"🆔 Telegram ID: {user_id}"
    )

    # Отправляем админу (твой личный ID)
    await context.bot.send_message(
        chat_id=275403892,  # Твой Telegram ID
        text=admin_text,
        reply_markup=InlineKeyboardMarkup(admin_keyboard)
    )

    return ConversationHandler.END

async def approve_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Одобряет заявку пользователя."""
    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split('_')[1])
    update_user_status(user_id, 'approved')

    # Уведомляем пользователя
    await context.bot.send_message(
        chat_id=user_id,
        text="✅ Ваша заявка одобрена!\n"
             "Теперь у вас есть доступ к боту.\n"
             "Введите /start для начала работы."
    )

    await query.edit_message_text(
        f"✅ Пользователь {user_id} одобрен!"
    )

async def reject_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отклоняет заявку пользователя."""
    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split('_')[1])
    update_user_status(user_id, 'rejected')

    # Уведомляем пользователя
    await context.bot.send_message(
        chat_id=user_id,
        text="❌ Ваша заявка была отклонена.\n"
             "Обратитесь к администратору для уточнения причин."
    )

    await query.edit_message_text(
        f"❌ Пользователь {user_id} отклонён!"
    )