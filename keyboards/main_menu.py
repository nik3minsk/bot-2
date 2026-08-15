# keyboards/main_menu.py
"""
Модуль клавиатур для главного меню.
Содержит функции, возвращающие InlineKeyboardMarkup для различных меню.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру главного меню с кнопками.

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками:
            - "👋 Приветствие" — показывает приветствие
            - "ℹ️ О боте" — информация о боте
    """
    keyboard = [
        [InlineKeyboardButton("👋 Приветствие", callback_data='greeting')],
        [InlineKeyboardButton("ℹ️ О боте", callback_data='about')],
    ]
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