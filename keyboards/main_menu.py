# keyboards/main_menu.py
"""
Модуль клавиатур для главного меню.
Содержит функции, возвращающие InlineKeyboardMarkup для различных меню.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from database.resource_models import get_min_days
from database.user_models import ROLE_DEV, ROLE_ADMIN, ROLE_GUEST


def get_main_menu_keyboard(roles=None):
    """
    Возвращает клавиатуру главного меню в зависимости от ролей.
    """
    if roles is None:
        roles = []

    keyboard = []

    # Базовое меню для всех
    keyboard.append([InlineKeyboardButton("👤 Личное", callback_data='menu_personal')])

    # Для всех кроме гостей
    if ROLE_GUEST not in roles:
        keyboard.append([InlineKeyboardButton("📊 Мониторинг", callback_data='menu_monitoring')])
        keyboard.append([InlineKeyboardButton("💼 Работа", callback_data='menu_work')])
        keyboard.append([InlineKeyboardButton("📧 Обработка почты", callback_data='menu_mail')])

    # Для разработчиков и админов — только Admin (dev)
    if roles and (ROLE_DEV in roles or ROLE_ADMIN in roles):
        keyboard.append([InlineKeyboardButton("🔧 Admin (dev)", callback_data='menu_admin_dev')])

    keyboard.append([InlineKeyboardButton("⚙️ Настройки", callback_data='menu_settings')])

    return InlineKeyboardMarkup(keyboard)


def get_back_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру с кнопкой "Назад".

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопкой "🔙 Назад"
    """
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')],
    ]
    return InlineKeyboardMarkup(keyboard)