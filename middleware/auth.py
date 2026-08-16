"""
Декораторы для проверки прав доступа
"""
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from database.user_models import get_user_by_id

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
                await update.message.reply_text(
                    "⛔ У вас нет доступа к этой команде.\n"
                    "Обратитесь к администратору для получения прав."
                )
                return
            
            return await func(update, context)
        return wrapper
    return decorator
