# bot.py
"""
Точка входа в приложение.
Настраивает и запускает Telegram-бота с обработчиками команд и callback-запросов.
"""
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler

from config import BOT_TOKEN
from utils.logger import setup_logger
from handlers.start import (
    start_command,
    greeting_callback,
    about_callback,
    back_to_main_callback,
    register_callback,
)
from handlers.register import (
    start_register,
    get_full_name,
    get_email,
    approve_user,
    reject_user,
    WAITING_FULL_NAME,
    WAITING_EMAIL,
)
from handlers.admin import (
    list_users,
    admin_refresh,
    admin_add_user_start,
    admin_add_user_confirm,
    set_role_start,
    set_role_select_user,
    set_role_toggle,
    toggle_block_start,
    toggle_block_confirm,
    delete_user_start,
    delete_user_select,
    delete_user_final,
    admin_cancel,
    exit_role_selection,
    WAITING_USER_ID,
    WAITING_ROLE,
    WAITING_ADD_USER,
    WAITING_CONFIRM,
)

# Настройка основного логгера
from config import LOG_LEVEL, LOG_FILE
logger = setup_logger(__name__, level=LOG_LEVEL, log_file=LOG_FILE)


def main() -> None:
    """
    Главная функция приложения.
    Создаёт экземпляр бота, регистрирует обработчики и запускает polling.
    """
    logger.info("🚀 Запуск бота...")

    # Создаём приложение (Application) с токеном бота
    app = Application.builder().token(BOT_TOKEN).build()

    # --- ОБРАБОТЧИКИ КОМАНД ---
    app.add_handler(CommandHandler("start", start_command))
    # app.add_handler(CommandHandler("register", start_register))  # <-- Добавлено

    # --- ОБРАБОТЧИКИ ДЛЯ РЕГИСТРАЦИИ (ConversationHandler) ---
    conv_handler_register = ConversationHandler(
        entry_points=[CommandHandler("register", start_register)],
        states={
            WAITING_FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_full_name)],
            WAITING_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
        },
        fallbacks=[CommandHandler("start", start_command)],
    )
    app.add_handler(conv_handler_register)

    # --- АДМИН-КОМАНДЫ ---
    conv_handler_admin = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_add_user_start, pattern='^admin_add_user$'),
            CallbackQueryHandler(set_role_start, pattern='^admin_set_role$'),
            CallbackQueryHandler(toggle_block_start, pattern='^admin_toggle_block$'),
            CallbackQueryHandler(delete_user_start, pattern='^admin_delete_user$'),
            CallbackQueryHandler(admin_refresh, pattern='^admin_refresh$'),
        ],
        states={
            WAITING_ADD_USER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_user_confirm),
            ],
            WAITING_USER_ID: [
                CallbackQueryHandler(set_role_select_user, pattern='^role_select_'),
                CallbackQueryHandler(toggle_block_confirm, pattern='^toggle_block_'),
                CallbackQueryHandler(delete_user_select, pattern='^delete_select_'),
            ],
            WAITING_ROLE: [
                CallbackQueryHandler(set_role_toggle, pattern='^role_set_'),
                CallbackQueryHandler(exit_role_selection, pattern='^admin_list_users$'),  # <-- ИСПРАВЛЕНО
            ],
            WAITING_CONFIRM: [
                CallbackQueryHandler(delete_user_final, pattern='^delete_confirm_'),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(admin_cancel, pattern='^admin_cancel$'),
            CommandHandler("start", start_command),
        ],
    )
    app.add_handler(conv_handler_admin)

    # --- ОБРАБОТЧИКИ КНОПОК ГЛАВНОГО МЕНЮ ---
    app.add_handler(CommandHandler("users", list_users))
    app.add_handler(CallbackQueryHandler(list_users, pattern='^admin_list_users$'))
    app.add_handler(CallbackQueryHandler(register_callback, pattern='^register$'))

    # --- ОБРАБОТЧИКИ ДЛЯ АДМИНА (одобрение/отклонение) ---
    app.add_handler(CallbackQueryHandler(approve_user, pattern='^approve_'))
    app.add_handler(CallbackQueryHandler(reject_user, pattern='^reject_'))

    # --- ОБРАБОТЧИКИ CALLBACK-ЗАПРОСОВ ОТ КНОПОК ---
    app.add_handler(CallbackQueryHandler(greeting_callback, pattern='^greeting$'))
    app.add_handler(CallbackQueryHandler(about_callback, pattern='^about$'))
    app.add_handler(CallbackQueryHandler(back_to_main_callback, pattern='^back_to_main$'))

    # Запускаем бота в режиме polling
    logger.info("✅ Бот запущен и готов к работе!")
    app.run_polling(allowed_updates=['message', 'callback_query'])


if __name__ == "__main__":
    main()