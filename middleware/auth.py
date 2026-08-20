"""
Декораторы для проверки прав доступа
"""
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from database.user_models import get_user_by_id
from database.user_models import ROLE_LEVELS, ROLE_GUEST
from database.feature_models import get_feature


def has_access(user_roles, required_level):
    """
    Проверяет, есть ли у пользователя доступ к функции.

    Args:
        user_roles (list): Список ролей пользователя
        required_level (int): Минимальный уровень доступа

    Returns:
        bool: True если доступ есть
    """
    for role in user_roles:
        if ROLE_LEVELS.get(role, 0) >= required_level:
            return True
    return False


def get_highest_role(user_roles):
    """Возвращает наивысшую роль пользователя."""
    highest = ROLE_GUEST
    max_level = 0
    for role in user_roles:
        level = ROLE_LEVELS.get(role, 0)
        if level > max_level:
            max_level = level
            highest = role
    return highest


def get_user_role(telegram_id):
    """Возвращает роли пользователя."""
    user = get_user_by_id(telegram_id)
    if user and user.get('status') == 'approved' and user.get('is_active', True):
        return user.get('roles', [ROLE_GUEST])
    return [ROLE_GUEST]




def get_user_role(telegram_id):
    """Возвращает роли пользователя."""
    user = get_user_by_id(telegram_id)
    if user and user.get('status') == 'approved' and user.get('is_active', True):
        return user.get('roles', ['guest'])
    return ['guest']

def require_roles(required_roles):
    """
    Декоратор для проверки прав доступа.
    
    Usage:
        @require_roles(['admin', 'manager'])
        async def my_command(update, context):
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = update.effective_user.id
            user_roles = get_user_role(user_id)
            
            if not any(role in user_roles for role in required_roles):
                # Проверяем, откуда пришёл запрос
                if update.callback_query:
                    await update.callback_query.answer("⛔ У вас нет доступа к этой команде.", show_alert=True)
                    await update.callback_query.edit_message_text(
                        "⛔ У вас нет доступа к этой команде.\n"
                        "Обратитесь к администратору для получения прав."
                    )
                else:
                    await update.message.reply_text(
                        "⛔ У вас нет доступа к этой команде.\n"
                        "Обратитесь к администратору для получения прав."
                    )
                return

            return await func(update, context)
        return wrapper
    return decorator


# Декоратор для проверки доступа


def require_feature(feature_id):
    """
    Декоратор для проверки доступа к функции.

    Usage:
        @require_feature('salary_report')
        async def salary_report(update, context):
            pass
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = update.effective_user.id
            user_roles = get_user_role(user_id)

            feature = get_feature(feature_id)
            if not feature:
                if update.message:
                    await update.message.reply_text("❌ Функция не найдена.")
                elif update.callback_query:
                    await update.callback_query.answer("❌ Функция не найдена.")
                else:
                    # Логируем или игнорируем неизвестный тип обновления
                    print(f"⚠️ Неизвестный тип обновления: {update}")
                return

            if not feature.get('enabled'):
                await update.message.reply_text("⛔ Функция временно отключена.")
                return

            allowed_roles = feature.get('allowed_roles', [])
            if not any(role in user_roles for role in allowed_roles):
                await update.message.reply_text(
                    "⛔ У вас нет доступа к этой функции.\n"
                    "Обратитесь к администратору."
                )
                return

            return await func(update, context)

        return wrapper

    return decorator