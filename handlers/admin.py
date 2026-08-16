"""
Административные команды для управления пользователями
"""
from utils.logger import get_logger
logger = get_logger(__name__)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database.user_models import (
    get_user_by_id,
    get_all_users,
    update_user_status,
    update_user_roles,
    set_user_active,
    get_active_users,
    create_user,
    delete_user,
)
from middleware.auth import require_roles


# Состояния для диалогов
WAITING_USER_ID = 1
WAITING_ROLE = 2
WAITING_ADD_USER = 3
WAITING_CONFIRM = 4

# Доступные роли
AVAILABLE_ROLES = {
    'admin': '👑 Администратор (всё)',
    'manager': '📊 Менеджер (работа, мониторинг)',
    'buh': '💰 Бухгалтер (НДС, отчёты)',
    'user': '👤 Пользователь (личное)',
    'guest': '👋 Гость (только просмотр)'
}


def get_users_list_keyboard(users, action, title):
    """
    Создаёт клавиатуру со списком пользователей для выбора.

    Args:
        users (list): Список пользователей
        action (str): Действие (set_role, block, unblock, delete)
        title (str): Заголовок сообщения

    Returns:
        tuple: (текст сообщения, клавиатура)
    """
    if not users:
        return "📭 Список пользователей пуст.", None

    keyboard = []
    message = f"{title}\n\n"

    for idx, user in enumerate(users, 1):
        status_icon = "🔴" if not user.get('is_active', True) else "🟢"
        roles = ', '.join(user.get('roles', ['guest']))
        name = user.get('full_name', 'Без имени')
        user_id = user.get('telegram_id')

        message += f"{idx}. {status_icon} {name}\n"
        message += f"   ID: {user_id}\n"
        message += f"   Роли: {roles}\n\n"

        # Добавляем кнопку для этого пользователя
        keyboard.append([
            InlineKeyboardButton(
                f"{idx}. {name}",
                callback_data=f"{action}_{user_id}"
            )
        ])

    keyboard.append([InlineKeyboardButton("🔙 Отмена", callback_data='admin_cancel')])

    return message, InlineKeyboardMarkup(keyboard)

@require_roles(['admin'])
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список всех пользователей."""
    users = get_all_users()

    if not users:
        if update.callback_query:
            await update.callback_query.edit_message_text("📭 Список пользователей пуст.")
        else:
            await update.message.reply_text("📭 Список пользователей пуст.")
        return

    # Группируем по статусу
    active = [u for u in users if u.get('is_active', True)]
    blocked = [u for u in users if not u.get('is_active', True)]
    pending = [u for u in users if u.get('status') == 'pending']

    message = "👥 <b>Управление пользователями</b>\n\n"

    if active:
        message += "✅ <b>Активные пользователи:</b>\n"
        for u in active[:10]:
            roles = ', '.join(u.get('roles', ['guest']))
            message += f"  • {u['full_name']} (ID: {u['telegram_id']}) - {roles}\n"
        if len(active) > 10:
            message += f"  ... и ещё {len(active) - 10} пользователей\n"

    if pending:
        message += f"\n⏳ <b>Ожидают одобрения ({len(pending)}):</b>\n"
        for u in pending[:5]:
            message += f"  • {u['full_name']} (ID: {u['telegram_id']})\n"

    if blocked:
        message += f"\n🚫 <b>Заблокированные ({len(blocked)}):</b>\n"
        for u in blocked[:5]:
            message += f"  • {u['full_name']} (ID: {u['telegram_id']})\n"

    message += f"\n📊 <b>Всего пользователей:</b> {len(users)}"
    # message += f"\n<i>💡 Для управления ролями выберите пользователя</i>"


    # Кнопки
    keyboard = [
        [InlineKeyboardButton("➕ Добавить пользователя", callback_data='admin_add_user')],
        [InlineKeyboardButton("📝 Назначить/Удалить роль", callback_data='admin_set_role')],
        [InlineKeyboardButton("🔄 Блокировка/Разблокировка", callback_data='admin_toggle_block')],
        [InlineKeyboardButton("❌ Удалить пользователя", callback_data='admin_delete_user')],
        [InlineKeyboardButton("📋 Обновить список", callback_data='admin_refresh')],
        [InlineKeyboardButton("🔙 В главное меню", callback_data='back_to_main')],
    ]

    # Отправляем ответ
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                message,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            # Если сообщение не изменилось — игнорируем
            if "Message is not modified" in str(e):
                await update.callback_query.answer("✅ Список уже актуален.")
            else:
                # Если другая ошибка — логируем
                logger.error(f"Ошибка при обновлении списка: {e}")
                raise e
    else:
        await update.message.reply_text(
            message,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


@require_roles(['admin'])
async def admin_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обновляет список пользователей."""
    query = update.callback_query
    await query.answer()

    # Просто вызываем list_users
    await list_users(update, context)



@require_roles(['admin'])
async def admin_add_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает процесс добавления пользователя вручную."""


    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "👤 <b>Добавление пользователя вручную</b>\n\n"
        "Введите данные в формате:\n"
        "<code>ID, ФИО, email, роли</code>\n\n"
        "Пример:\n"
        "<code>123456789, Иванов Иван, ivan@mail.ru, manager</code>\n\n"
        "Доступные роли: admin, manager, buh, user, guest\n"
        "Можно указать несколько ролей через запятую.",
        parse_mode='HTML'
    )
    return WAITING_ADD_USER


@require_roles(['admin'])
async def admin_add_user_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавляет пользователя вручную."""
    logger.info(f"Вошли в admin_add_user_confirm. Сообщение: {update.message.text}")

    text = update.message.text.strip()
    parts = [p.strip() for p in text.split(',')]

    if len(parts) < 3:
        await update.message.reply_text(
            "❌ Неверный формат. Нужно: ID, ФИО, email, роли\n"
            "Пример: 123456789, Иванов Иван, ivan@mail.ru, manager"
        )
        return WAITING_ADD_USER

    try:
        user_id = int(parts[0])
        full_name = parts[1]
        email = parts[2]
        roles = [r.strip() for r in parts[3].split(',')] if len(parts) > 3 else ['user']
    except ValueError:
        await update.message.reply_text("❌ ID должен быть числом.")
        return WAITING_ADD_USER

    # Проверяем, не существует ли уже
    existing = get_user_by_id(user_id)
    if existing:
        await update.message.reply_text(
            f"❌ Пользователь с ID {user_id} уже существует.\n"
            f"Имя: {existing['full_name']}"
        )
        return WAITING_ADD_USER

    # Создаём пользователя
    user = create_user(
        telegram_id=user_id,
        full_name=full_name,
        email=email,
        roles=roles,
        status='approved'
    )

    if user:
        await update.message.reply_text(
            f"✅ Пользователь <b>{full_name}</b> добавлен!\n"
            f"🆔 ID: {user_id}\n"
            f"📧 Email: {email}\n"
            f"🎭 Роли: {', '.join(roles)}",
            parse_mode='HTML'
        )
        logger.info(f"Админ {update.effective_user.id} добавил пользователя {user_id}")
    else:
        await update.message.reply_text("❌ Ошибка при создании пользователя.")

    # --- ВОЗВРАЩАЕМСЯ В МЕНЮ УПРАВЛЕНИЯ ПОЛЬЗОВАТЕЛЯМИ ---
    users = get_all_users()

    if not users:
        await update.message.reply_text("📭 Список пользователей пуст.")
        return ConversationHandler.END

    active = [u for u in users if u.get('is_active', True)]
    blocked = [u for u in users if not u.get('is_active', True)]
    pending = [u for u in users if u.get('status') == 'pending']

    message = "👥 <b>Управление пользователями</b>\n\n"

    if active:
        message += "✅ <b>Активные пользователи:</b>\n"
        for u in active[:10]:
            roles = ', '.join(u.get('roles', ['guest']))
            message += f"  • {u['full_name']} (ID: {u['telegram_id']}) - {roles}\n"
        if len(active) > 10:
            message += f"  ... и ещё {len(active) - 10} пользователей\n"

    if pending:
        message += f"\n⏳ <b>Ожидают одобрения ({len(pending)}):</b>\n"
        for u in pending[:5]:
            message += f"  • {u['full_name']} (ID: {u['telegram_id']})\n"

    if blocked:
        message += f"\n🚫 <b>Заблокированные ({len(blocked)}):</b>\n"
        for u in blocked[:5]:
            message += f"  • {u['full_name']} (ID: {u['telegram_id']})\n"

    message += f"\n📊 <b>Всего пользователей:</b> {len(users)}"

    keyboard = [
        [InlineKeyboardButton("➕ Добавить пользователя", callback_data='admin_add_user')],
        [InlineKeyboardButton("📝 Назначить роль", callback_data='admin_set_role')],
        [InlineKeyboardButton("🔄 Блокировка/Разблокировка", callback_data='admin_toggle_block')],
        [InlineKeyboardButton("❌ Удалить пользователя", callback_data='admin_delete_user')],
        [InlineKeyboardButton("📋 Обновить список", callback_data='admin_refresh')],
        [InlineKeyboardButton("🔙 В главное меню", callback_data='back_to_main')],
    ]

    await update.message.reply_text(
        message,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    logger.info(f"Выход из диалога. Возвращаем ConversationHandler.END")
    return ConversationHandler.END


@require_roles(['admin'])
async def set_role_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список пользователей для назначения роли."""
    query = update.callback_query
    await query.answer()

    users = get_all_users()
    active_users = [u for u in users if u.get('is_active', True)]

    if not active_users:
        await query.edit_message_text("📭 Нет активных пользователей.")
        return ConversationHandler.END

    message, keyboard = get_users_list_keyboard(
        active_users,
        'role_select',
        "📝 <b>Выберите пользователя для назначения/удаления роли:</b>"
    )

    await query.edit_message_text(
        message,
        parse_mode='HTML',
        reply_markup=keyboard
    )
    return WAITING_USER_ID


@require_roles(['admin'])
async def set_role_select_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор пользователя для роли."""
    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split('_')[2])
    user = get_user_by_id(user_id)

    if not user:
        await query.edit_message_text("❌ Пользователь не найден.")
        return ConversationHandler.END

    context.user_data['target_user_id'] = user_id
    context.user_data['target_user'] = user

    current_roles = user.get('roles', [])

    # Показываем доступные роли с отметками
    keyboard = []
    for role_id, role_name in AVAILABLE_ROLES.items():
        if role_id in current_roles:
            button_text = f"✅ {role_name}"  # Уже назначена
        else:
            button_text = f"⬜ {role_name}"  # Не назначена
        keyboard.append([
            InlineKeyboardButton(button_text, callback_data=f"role_set_{role_id}")
        ])
    keyboard.append([InlineKeyboardButton("🔙 Назад к списку", callback_data='admin_list_users')])
    keyboard.append([InlineKeyboardButton("🔙 В главное меню", callback_data='back_to_main')])

    await query.edit_message_text(
        f"👤 <b>Пользователь:</b> {user['full_name']}\n"
        f"🆔 <b>ID:</b> {user['telegram_id']}\n"
        f"📧 <b>Email:</b> {user.get('email', 'не указан')}\n"
        f"🎭 <b>Текущие роли:</b> {', '.join(current_roles) if current_roles else 'нет ролей'}\n\n"
        f"<b>Выберите действие:</b>\n"
        f"✅ — роль уже назначена (нажмите, чтобы убрать)\n"
        f"⬜ — роль не назначена (нажмите, чтобы добавить)\n\n"
        f"<i>💡 Нажмите на роль, чтобы добавить или убрать её</i>",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return WAITING_ROLE


@require_roles(['admin'])
async def set_role_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Переключает роль пользователя (добавляет/убирает)."""
    query = update.callback_query
    await query.answer()

    role_id = query.data.split('_')[2]
    user_id = context.user_data.get('target_user_id')
    user = context.user_data.get('target_user')

    if not user_id or not user:
        await query.edit_message_text("❌ Ошибка: пользователь не найден.")
        return ConversationHandler.END

    current_roles = user.get('roles', [])
    role_name = AVAILABLE_ROLES.get(role_id, role_id)

    if role_id in current_roles:
        current_roles.remove(role_id)
        action = "❌ убрана"
        action_emoji = "❌"
    else:
        current_roles.append(role_id)
        action = "✅ добавлена"
        action_emoji = "✅"

    success = update_user_roles(user_id, current_roles)

    if success:
        updated_user = get_user_by_id(user_id)
        context.user_data['target_user'] = updated_user

        result_message = (
            f"{action_emoji} Роль <b>{role_name}</b> {action} у пользователя <b>{user['full_name']}</b>!\n"
            f"🎭 <b>Текущие роли:</b> {', '.join(current_roles) if current_roles else 'нет ролей'}\n\n"
            f"<i>💡 Чтобы убрать роль — нажмите на неё ещё раз</i>"
        )

        keyboard = []
        for role_id2, role_name2 in AVAILABLE_ROLES.items():
            if role_id2 in current_roles:
                button_text = f"✅ {role_name2}"
            else:
                button_text = f"⬜ {role_name2}"
            keyboard.append([
                InlineKeyboardButton(button_text, callback_data=f"role_set_{role_id2}")
            ])
        keyboard.append([InlineKeyboardButton("🔙 Назад к списку", callback_data='admin_list_users')])
        keyboard.append([InlineKeyboardButton("🔙 В главное меню", callback_data='back_to_main')])

        await query.edit_message_text(
            result_message,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        logger.info(f"Админ {update.effective_user.id} {action} роль {role_id} у пользователя {user_id}")
    else:
        await query.edit_message_text("❌ Ошибка при изменении роли.")

    # Возвращаем WAITING_ROLE, чтобы остаться в диалоге и менять роли дальше
    return WAITING_ROLE


@require_roles(['admin'])
async def exit_role_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выходит из выбора ролей и показывает список пользователей."""
    query = update.callback_query
    await query.answer()

    # Очищаем данные диалога
    context.user_data.clear()

    # Показываем список пользователей
    await list_users(update, context)

    # Завершаем диалог
    return ConversationHandler.END


@require_roles(['admin'])
async def toggle_block_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список пользователей для блокировки/разблокировки."""
    query = update.callback_query
    await query.answer()

    users = get_all_users()

    if not users:
        await query.edit_message_text("📭 Список пользователей пуст.")
        return ConversationHandler.END

    message, keyboard = get_users_list_keyboard(
        users,
        'toggle_block',
        "🔄 <b>Выберите пользователя для блокировки/разблокировки:</b>\n"
        "🔴 — заблокирован, 🟢 — активен"
    )

    await query.edit_message_text(
        message,
        parse_mode='HTML',
        reply_markup=keyboard
    )
    return WAITING_USER_ID


@require_roles(['admin'])
async def toggle_block_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Переключает статус блокировки пользователя."""
    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split('_')[2])
    user = get_user_by_id(user_id)

    if not user:
        await query.edit_message_text("❌ Пользователь не найден.")
        return ConversationHandler.END

    current_status = user.get('is_active', True)
    new_status = not current_status

    success = set_user_active(user_id, new_status)

    if success:
        status_text = "разблокирован" if new_status else "заблокирован"
        emoji = "✅" if new_status else "🚫"

        await query.edit_message_text(
            f"{emoji} Пользователь <b>{user['full_name']}</b> {status_text}!",
            parse_mode='HTML'
        )

        # Уведомляем пользователя
        try:
            if new_status:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="✅ Ваш доступ к боту восстановлен!\nВведите /start для начала работы."
                )
            else:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="🚫 Ваш доступ к боту приостановлен.\nОбратитесь к администратору."
                )
        except Exception as e:
            logger.warning(f"Не удалось уведомить пользователя {user_id}: {e}")

        logger.info(f"Админ {update.effective_user.id} {status_text} пользователя {user_id}")
    else:
        await query.edit_message_text("❌ Ошибка при изменении статуса.")

    # Обновляем список
    await admin_refresh(update, context)
    return ConversationHandler.END



@require_roles(['admin'])
async def delete_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список пользователей для удаления."""
    query = update.callback_query
    await query.answer()

    users = get_all_users()

    if not users:
        await query.edit_message_text("📭 Список пользователей пуст.")
        return ConversationHandler.END

    message, keyboard = get_users_list_keyboard(
        users,
        'delete_select',
        "❌ <b>Выберите пользователя для удаления:</b>\n"
        "⚠️ Действие <b>необратимо</b>!"
    )

    await query.edit_message_text(
        message,
        parse_mode='HTML',
        reply_markup=keyboard
    )
    return WAITING_USER_ID


@require_roles(['admin'])
async def delete_user_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запрашивает подтверждение удаления."""
    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split('_')[2])
    user = get_user_by_id(user_id)

    if not user:
        await query.edit_message_text("❌ Пользователь не найден.")
        return ConversationHandler.END

    context.user_data['delete_user_id'] = user_id

    keyboard = [
        [
            InlineKeyboardButton("✅ Да, удалить", callback_data=f"delete_confirm_{user_id}"),
            InlineKeyboardButton("❌ Отмена", callback_data='admin_cancel')
        ]
    ]

    await query.edit_message_text(
        f"⚠️ <b>Подтверждение удаления</b>\n\n"
        f"Вы уверены, что хотите удалить пользователя:\n"
        f"👤 <b>{user['full_name']}</b>\n"
        f"🆔 ID: {user['telegram_id']}\n"
        f"📧 Email: {user.get('email', 'не указан')}\n"
        f"🎭 Роли: {', '.join(user.get('roles', ['guest']))}\n\n"
        f"Это действие <b>необратимо</b>!",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return WAITING_CONFIRM


@require_roles(['admin'])
async def delete_user_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Окончательно удаляет пользователя."""
    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split('_')[2])
    user = get_user_by_id(user_id)

    if not user:
        await query.edit_message_text("❌ Пользователь не найден.")
        return ConversationHandler.END

    success = delete_user(user_id)

    if success:
        await query.edit_message_text(
            f"✅ Пользователь <b>{user['full_name']}</b> удалён!",
            parse_mode='HTML'
        )
        logger.info(f"Админ {update.effective_user.id} удалил пользователя {user_id}")
    else:
        await query.edit_message_text("❌ Ошибка при удалении.")

    # Обновляем список (используем query, а не update.message)
    await admin_refresh(update, context)
    return ConversationHandler.END




@require_roles(['admin'])
async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменяет текущее действие админа и возвращает в меню управления."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Действие отменено.")
    # Возвращаемся в меню управления пользователями
    await admin_refresh(update, context)
    return ConversationHandler.END