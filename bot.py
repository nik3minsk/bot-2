# bot.py
"""
Точка входа в приложение.
Настраивает и запускает Telegram-бота с обработчиками команд и callback-запросов.
"""
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from telegram.warnings import PTBUserWarning

from config import BOT_TOKEN
from utils.logger import setup_logger



# ============================================================
# ИМПОРТЫ ИЗ handlers/
# ============================================================
from handlers.start import (
    start_command,
    greeting_callback,
    about_callback,
    back_to_main_callback,
    register_callback,
    menu_personal,
    menu_monitoring,
    menu_work,
    menu_mail,
    menu_admin_dev,
    menu_settings,
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

# ============================================================
# ИМПОРТЫ ИЗ handlers/monitoring.py (НОВЫЕ)
# ============================================================
from handlers.monitoring import (
    monitoring_resources,
    monitoring_refresh,
    add_resource_start,
    add_resource_get_name,
    add_resource_get_track_ssl,
    add_resource_get_url,
    delete_resource_start,
    delete_resource_confirm,
    monitoring_cancel,
    WAITING_RESOURCE_NAME,
    WAITING_RESOURCE_URL,
    WAITING_RESOURCE_REGISTRAR,
    WAITING_DELETE_CONFIRM, edit_resource_start, WAITING_EDIT_RESOURCE, edit_resource_select, edit_toggle_ssl,
    edit_toggle_domain,
)
import warnings

# ============================================================
# НАСТРОЙКА ЛОГГЕРА
# ============================================================
from config import LOG_LEVEL, LOG_FILE
logger = setup_logger(__name__, level=LOG_LEVEL, log_file=LOG_FILE)


# Отключаем предупреждение о per_* settings в ConversationHandler
warnings.filterwarnings(
    action="ignore",
    message=r".*per_message=False.*CallbackQueryHandler.*",
    category=PTBUserWarning
)

# ============================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================
def main() -> None:
    """
    Главная функция приложения.
    Создаёт экземпляр бота, регистрирует обработчики и запускает polling.
    """
    logger.info("🚀 Запуск бота...")

    # Создаём приложение
    app = Application.builder().token(BOT_TOKEN).build()

    # ============================================================
    # 1. ОБРАБОТЧИКИ КОМАНД
    # ============================================================
    app.add_handler(CommandHandler("start", start_command))

    # ============================================================
    # 2. РЕГИСТРАЦИЯ (ConversationHandler)
    # ============================================================
    conv_handler_register = ConversationHandler(
        entry_points=[CommandHandler("register", start_register)],
        states={
            WAITING_FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_full_name)],
            WAITING_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
        },
        fallbacks=[CommandHandler("start", start_command)],
    )
    app.add_handler(conv_handler_register)

    # ============================================================
    # 3. УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ (ConversationHandler)
    # ============================================================
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
                CallbackQueryHandler(exit_role_selection, pattern='^admin_list_users$'),
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

    # ============================================================
    # 4. МОНИТОРИНГ РЕСУРСОВ (ConversationHandler) — НОВЫЙ
    # ============================================================
    conv_handler_monitoring = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_resource_start, pattern='^monitoring_add$'),
            CallbackQueryHandler(delete_resource_start, pattern='^monitoring_delete$'),
            CallbackQueryHandler(monitoring_refresh, pattern='^monitoring_refresh$'),
            CallbackQueryHandler(edit_resource_start, pattern='^monitoring_edit$'),
        ],
        states={
            WAITING_RESOURCE_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_resource_get_name),
            ],
            WAITING_RESOURCE_URL: [
                CallbackQueryHandler(add_resource_get_track_ssl, pattern='^track_ssl_'),
            ],
            WAITING_RESOURCE_REGISTRAR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_resource_get_url),
            ],
            WAITING_DELETE_CONFIRM: [
                CallbackQueryHandler(delete_resource_confirm, pattern='^del_res_'),
            ],
            # Добавляем состояние в states
            WAITING_EDIT_RESOURCE: [
                CallbackQueryHandler(edit_resource_select, pattern='^edit_res_'),
                CallbackQueryHandler(edit_toggle_ssl, pattern='^edit_toggle_ssl$'),
                CallbackQueryHandler(edit_toggle_domain, pattern='^edit_toggle_domain$'),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(monitoring_cancel, pattern='^monitoring_cancel$'),
            CommandHandler("start", start_command),
        ],
    )
    app.add_handler(conv_handler_monitoring)


    # ============================================================
    # 5. КНОПКИ ГЛАВНОГО МЕНЮ
    # ============================================================
    app.add_handler(CallbackQueryHandler(menu_personal, pattern='^menu_personal$'))
    app.add_handler(CallbackQueryHandler(menu_monitoring, pattern='^menu_monitoring$'))
    app.add_handler(CallbackQueryHandler(menu_work, pattern='^menu_work$'))
    app.add_handler(CallbackQueryHandler(menu_mail, pattern='^menu_mail$'))
    app.add_handler(CallbackQueryHandler(menu_admin_dev, pattern='^menu_admin_dev$'))
    app.add_handler(CallbackQueryHandler(menu_settings, pattern='^menu_settings$'))

    # ============================================================
    # 6. КНОПКИ АДМИНА (одобрение/отклонение заявок)
    # ============================================================
    app.add_handler(CallbackQueryHandler(approve_user, pattern='^approve_'))
    app.add_handler(CallbackQueryHandler(reject_user, pattern='^reject_'))

    # ============================================================
    # 7. КНОПКИ УПРАВЛЕНИЯ ПОЛЬЗОВАТЕЛЯМИ
    # ============================================================
    app.add_handler(CallbackQueryHandler(list_users, pattern='^admin_list_users$'))

    # ============================================================
    # 8. КНОПКИ МОНИТОРИНГА РЕСУРСОВ — НОВЫЕ
    # ============================================================
    app.add_handler(CallbackQueryHandler(monitoring_resources, pattern='^monitoring_resources$'))
    app.add_handler(CallbackQueryHandler(monitoring_resources, pattern='^monitoring_back$'))
    app.add_handler(CallbackQueryHandler(monitoring_resources, pattern='^monitoring_back_to_list$'))


    # ============================================================
    # 9. ОБЩИЕ CALLBACK-ОБРАБОТЧИКИ
    # ============================================================
    app.add_handler(CallbackQueryHandler(greeting_callback, pattern='^greeting$'))
    app.add_handler(CallbackQueryHandler(about_callback, pattern='^about$'))
    app.add_handler(CallbackQueryHandler(back_to_main_callback, pattern='^back_to_main$'))

    # ============================================================
    # ЗАПУСК БОТА
    # ============================================================
    logger.info("✅ Бот запущен и готов к работе!")
    app.run_polling(allowed_updates=['message', 'callback_query'])


if __name__ == "__main__":
    main()