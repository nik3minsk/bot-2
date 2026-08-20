"""
Мониторинг ресурсов (SSL сертификаты и домены)
"""
import ssl
import socket
from datetime import datetime, timezone
import whois

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler



from database.resource_models import (
    get_all_resources,
    add_resource,
    delete_resource,
    update_resource_days,
    get_resource_by_name, update_domain_days, update_ssl_days
)
from middleware.auth import require_feature
from utils.logger import get_logger

logger = get_logger(__name__)

# ============================================================
# СОСТОЯНИЯ ДЛЯ ДИАЛОГОВ
# ============================================================
WAITING_RESOURCE_NAME = 1
WAITING_RESOURCE_URL = 2
WAITING_RESOURCE_REGISTRAR = 3
WAITING_DELETE_CONFIRM = 4
WAITING_EDIT_RESOURCE = 5


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def check_ssl_days(url):
    """
    Проверяет SSL сертификат.
    Возвращает (days_left, expire_date).
    """
    try:
        if url.startswith('https://'):
            hostname = url.replace('https://', '').split('/')[0]
        elif url.startswith('http://'):
            hostname = url.replace('http://', '').split('/')[0]
        else:
            hostname = url.split('/')[0]

        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()

        expire_date = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
        days_left = (expire_date - datetime.now()).days
        return max(0, days_left), expire_date
    except Exception as e:
        logger.error(f"Ошибка проверки SSL для {url}: {e}")
        return None, None


import whois
from datetime import datetime, timezone


from datetime import datetime, timezone


def check_domain_days(domain):
    """
    Проверяет количество дней до истечения домена через WHOIS.
    Возвращает (days_left, expire_date, registrar).
    """
    try:
        w = whois.whois(domain)

        # Получаем регистратора
        registrar = None
        if w.registrar:
            registrar = str(w.registrar)

        if w.expiration_date:
            if isinstance(w.expiration_date, list):
                expire_date = w.expiration_date[0]
            else:
                expire_date = w.expiration_date
            if isinstance(expire_date, datetime):
                if expire_date.tzinfo is None:
                    expire_date = expire_date.replace(tzinfo=timezone.utc)
                days_left = (expire_date - datetime.now(timezone.utc)).days
                return max(0, days_left), expire_date, registrar
        return None, None, None
    except Exception as e:
        logger.error(f"Ошибка WHOIS для {domain}: {e}")
        return None, None, None


def format_resource(resource):
    """Форматирует ресурс для вывода в Telegram."""
    name = resource['name']

    # Получаем минимальную дату истечения
    domain_date = resource.get('domain_expire_date')
    ssl_date = resource.get('ssl_expire_date')

    min_date = None
    status_icon = "🟢"
    warning_text = ""

    if domain_date and ssl_date:
        min_date = min(domain_date, ssl_date)
    elif domain_date:
        min_date = domain_date
    elif ssl_date:
        min_date = ssl_date

    if min_date:
        days_left = (min_date - datetime.now()).days
        if days_left < 10:
            status_icon = "🔴"
            warning_text = " ⚠️"
        elif days_left < 30:
            status_icon = "🟡"

    date_str = f"(до {min_date.strftime('%d.%m.%Y')})" if min_date else ""

    # Домен
    if resource.get('track_domain'):
        days = resource.get('domain_days')
        if days is not None:
            if days < 10:
                domain_text = f"🔴 {days}дн ⚠️"
            elif days < 30:
                domain_text = f"🟡 {days}дн"
            else:
                domain_text = f"🟢 {days}дн"
        else:
            domain_text = "⚪ —"
    else:
        domain_text = "⚪ —"

    # SSL
    if resource.get('track_ssl'):
        days = resource.get('ssl_days')
        if days is not None:
            if days < 10:
                ssl_text = f"🔴 {days}дн ⚠️"
            elif days < 30:
                ssl_text = f"🟡 {days}дн"
            else:
                ssl_text = f"🟢 {days}дн"
        else:
            ssl_text = "⚪ —"
    else:
        ssl_text = "⚪ —"

    return f"{status_icon} {name}    {date_str}{warning_text}   Домен: {domain_text}   SSL: {ssl_text}"


async def update_all_resources():
    """Обновляет информацию о всех ресурсах."""
    resources = get_all_resources()
    for resource in resources:
        name = resource['name']

        if resource.get('track_domain'):
            days, expire_date, registrar = check_domain_days(name)
            if days is not None:
                update_domain_days(name, days, expire_date, registrar)

        if resource.get('track_ssl') and resource.get('url'):
            days, expire_date = check_ssl_days(resource['url'])
            if days is not None:
                update_ssl_days(name, days, expire_date)

# ============================================================
# ОСНОВНЫЕ ОБРАБОТЧИКИ
# ============================================================

@require_feature('monitoring_resources')
async def monitoring_resources(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список ресурсов."""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        edit_func = query.edit_message_text
    else:
        edit_func = update.message.reply_text

    await update_all_resources()
    resources = get_all_resources()

    if not resources:
        keyboard = [
            [InlineKeyboardButton("➕ Добавить ресурс", callback_data='monitoring_add')],
            [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]
        ]
        await edit_func(
            "🌐 <b>Мониторинг ресурсов</b>\n\nСписок ресурсов пуст.",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    lines = ["🌐 <b>Мониторинг ресурсов</b>\n", "─" * 40, ""]
    for resource in resources:
        lines.append(format_resource(resource))
    lines.append("")
    lines.append("─" * 40)

    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data='monitoring_refresh')],
        [InlineKeyboardButton("➕ Добавить ресурс", callback_data='monitoring_add')],
        [InlineKeyboardButton("✏️ Редактировать", callback_data='monitoring_edit')],  # <-- ДОБАВЬ
        [InlineKeyboardButton("❌ Удалить ресурс", callback_data='monitoring_delete')],
        [InlineKeyboardButton("🔙 В главное меню", callback_data='back_to_main')],
    ]

    try:
        await edit_func(
            "\n".join(lines),
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        if "Message is not modified" in str(e):
            # Игнорируем, если сообщение не изменилось
            pass
        else:
            raise e


@require_feature('monitoring_resources')
async def monitoring_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обновляет данные мониторинга."""
    query = update.callback_query
    await query.answer()
    await monitoring_resources(update, context)


# ============================================================
# ДОБАВЛЕНИЕ РЕСУРСА
# ============================================================

@require_feature('monitoring_resources')
async def add_resource_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает диалог добавления ресурса."""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "➕ <b>Добавление ресурса</b>\n\nВведите имя ресурса (домен):\nПример: example.com",
        parse_mode='HTML'
    )
    return WAITING_RESOURCE_NAME


async def add_resource_get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает имя ресурса."""
    name = update.message.text.strip().lower()

    if get_resource_by_name(name):
        await update.message.reply_text(f"❌ Ресурс {name} уже существует. Введите другое имя:")
        return WAITING_RESOURCE_NAME

    context.user_data['resource_name'] = name

    keyboard = [
        [InlineKeyboardButton("✅ Да, отслеживать SSL", callback_data='track_ssl_yes')],
        [InlineKeyboardButton("❌ Нет, только домен", callback_data='track_ssl_no')],
        [InlineKeyboardButton("🔙 Отмена", callback_data='monitoring_cancel')],
    ]
    await update.message.reply_text(
        f"📌 <b>Ресурс:</b> {name}\n\n"
        "Отслеживать SSL сертификат?\n"
        "(URL будет автоматически сформирован как https://{имя_ресурса})",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return WAITING_RESOURCE_URL


async def add_resource_get_track_ssl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор отслеживания SSL."""
    query = update.callback_query
    await query.answer()

    track_ssl = query.data == 'track_ssl_yes'
    name = context.user_data['resource_name']

    url = f"https://{name}" if track_ssl else None

    # Получаем данные домена (дни, дата, регистратор)
    days, expire_date, registrar = check_domain_days(name)
    domain_days = days

    # Проверяем SSL
    ssl_days, ssl_expire = check_ssl_days(url) if track_ssl else (None, None)

    # Создаём ресурс с регистратором
    resource = add_resource(
        name=name,
        track_domain=True,
        track_ssl=track_ssl,
        url=url,
        registrar=registrar  # <-- теперь определён
    )

    if resource:
        update_resource_days(name, domain_days=domain_days, ssl_days=ssl_days)
        msg = f"✅ Ресурс <b>{name}</b> добавлен!"
        if ssl_days is not None:
            msg += f"\n🔒 SSL: {ssl_days} дней до истечения"
        else:
            msg += f"\n🔒 SSL: не отслеживается"
        await query.edit_message_text(msg, parse_mode='HTML')
    else:
        await query.edit_message_text("❌ Ошибка при добавлении ресурса.")

    context.user_data.clear()

    # Показываем обновлённый список ресурсов
    await monitoring_resources(update, context)
    return ConversationHandler.END


async def add_resource_get_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает URL для SSL проверки."""
    url = update.message.text.strip()
    if not url.startswith('http'):
        url = 'https://' + url
    context.user_data['url'] = url
    return await save_resource(update, context)


async def save_resource(update, context):
    """Сохраняет ресурс в базу данных."""
    name = context.user_data['resource_name']
    track_domain = context.user_data.get('track_domain', True)
    track_ssl = context.user_data.get('track_ssl', False)
    url = context.user_data.get('url')

    ssl_days = check_ssl_days(url) if track_ssl and url else None
    domain_days = check_domain_days(name) if track_domain else None

    resource = add_resource(name, track_domain, track_ssl, url)
    if resource:
        update_resource_days(name, domain_days=domain_days, ssl_days=ssl_days)
        msg = f"✅ Ресурс <b>{name}</b> добавлен!"
        if ssl_days is not None:
            msg += f"\n🔒 SSL: {ssl_days} дней"
        if domain_days is not None:
            msg += f"\n📌 Домен: {domain_days} дней"

        # Отправляем результат в текущий чат
        await update.message.reply_text(msg, parse_mode='HTML')
    else:
        await update.message.reply_text("❌ Ошибка при добавлении ресурса.")

    context.user_data.clear()

    # Показываем обновлённый список ресурсов
    resources = get_all_resources()
    if not resources:
        keyboard = [
            [InlineKeyboardButton("➕ Добавить ресурс", callback_data='monitoring_add')],
            [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]
        ]
        await update.message.reply_text(
            "🌐 <b>Мониторинг ресурсов</b>\n\nСписок ресурсов пуст.",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    lines = ["🌐 <b>Мониторинг ресурсов</b>\n", "─" * 40, ""]
    for resource in resources:
        lines.append(format_resource(resource))
    lines.append("")
    lines.append("─" * 40)

    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data='monitoring_refresh')],
        [InlineKeyboardButton("➕ Добавить ресурс", callback_data='monitoring_add')],
        [InlineKeyboardButton("✏️ Редактировать", callback_data='monitoring_edit')],  # <-- НОВАЯ
        [InlineKeyboardButton("❌ Удалить ресурс", callback_data='monitoring_delete')],
        [InlineKeyboardButton("🔙 В главное меню", callback_data='back_to_main')],
    ]

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return ConversationHandler.END

# ============================================================
# УДАЛЕНИЕ РЕСУРСА
# ============================================================

@require_feature('monitoring_resources')
async def delete_resource_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает диалог удаления ресурса."""
    query = update.callback_query
    await query.answer()

    resources = get_all_resources()
    if not resources:
        await query.edit_message_text("📭 Список ресурсов пуст.")
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(f"❌ {r['name']}", callback_data=f"del_res_{r['name']}")] for r in resources]
    keyboard.append([InlineKeyboardButton("🔙 Отмена", callback_data='monitoring_cancel')])

    await query.edit_message_text(
        "❌ <b>Удаление ресурса</b>\n\nВыберите ресурс для удаления:",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return WAITING_DELETE_CONFIRM


async def delete_resource_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждает удаление ресурса."""
    query = update.callback_query
    await query.answer()

    name = query.data.replace('del_res_', '')
    if delete_resource(name):
        await query.edit_message_text(f"✅ Ресурс <b>{name}</b> удалён!", parse_mode='HTML')
    else:
        await query.edit_message_text(f"❌ Ошибка при удалении {name}.")

    await monitoring_resources(update, context)
    return ConversationHandler.END


async def monitoring_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменяет текущее действие."""
    query = update.callback_query
    await query.answer()
    await monitoring_resources(update, context)
    return ConversationHandler.END


async def edit_resource_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список ресурсов для редактирования."""
    query = update.callback_query
    await query.answer()

    resources = get_all_resources()
    if not resources:
        await query.edit_message_text("📭 Список ресурсов пуст.")
        return ConversationHandler.END

    lines = ["✏️ <b>Выберите ресурс для редактирования</b>\n"]
    lines.append("─" * 40)

    keyboard = []
    for idx, resource in enumerate(resources, 1):
        name = resource['name']
        ssl_status = "🟢" if resource.get('track_ssl') else "⚪"
        lines.append(f"{idx}. {ssl_status} {name}")
        keyboard.append([
            InlineKeyboardButton(
                f"{idx}. {name}",
                callback_data=f"edit_res_{name}"
            )
        ])

    lines.append("")
    lines.append("─" * 40)
    lines.append("🟢 — SSL отслеживается\n⚪ — SSL не отслеживается")

    keyboard.append([InlineKeyboardButton("🔙 Назад к списку", callback_data='monitoring_back_to_list')])

    await query.edit_message_text(
        "\n".join(lines),
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return WAITING_EDIT_RESOURCE


async def edit_resource_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает настройки ресурса для редактирования."""
    query = update.callback_query
    await query.answer()

    name = query.data.replace('edit_res_', '')
    resource = get_resource_by_name(name)

    if not resource:
        await query.edit_message_text("❌ Ресурс не найден.")
        return ConversationHandler.END

    context.user_data['edit_resource_name'] = name

    track_ssl = resource.get('track_ssl', False)
    track_domain = resource.get('track_domain', True)
    url = resource.get('url', 'не указан')

    keyboard = [
        [InlineKeyboardButton(
            f"{'🟢' if track_ssl else '⚪'} SSL сертификат",
            callback_data='edit_toggle_ssl'
        )],
        [InlineKeyboardButton(
            f"{'🟢' if track_domain else '⚪'} Доменное имя",
            callback_data='edit_toggle_domain'
        )],
        [InlineKeyboardButton("🔙 Назад к списку", callback_data='monitoring_back_to_list')],
        [InlineKeyboardButton("🔙 В главное меню", callback_data='back_to_main')],
    ]

    await query.edit_message_text(
        f"✏️ <b>Редактирование: {name}</b>\n\n"
        f"🔗 URL: {url}\n"
        f"📌 Домен: {'🟢 отслеживается' if track_domain else '⚪ не отслеживается'}\n"
        f"🔒 SSL: {'🟢 отслеживается' if track_ssl else '⚪ не отслеживается'}\n\n"
        f"Нажмите на параметр, чтобы переключить:",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )
    return WAITING_EDIT_RESOURCE



async def edit_toggle_ssl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Переключает отслеживание SSL."""
    query = update.callback_query
    await query.answer()

    name = context.user_data.get('edit_resource_name')
    if not name:
        await query.edit_message_text("❌ Ошибка: ресурс не выбран.")
        return ConversationHandler.END

    resource = get_resource_by_name(name)
    if not resource:
        await query.edit_message_text("❌ Ресурс не найден.")
        return ConversationHandler.END

    new_track_ssl = not resource.get('track_ssl', False)

    from database.resource_models import update_resource_settings
    update_resource_settings(name, track_ssl=new_track_ssl)

    if new_track_ssl and resource.get('url'):
        ssl_days = check_ssl_days(resource['url'])
        if ssl_days is not None:
            from database.resource_models import update_resource_days
            update_resource_days(name, ssl_days=ssl_days)

    await query.edit_message_text(
        f"✅ Для {name} SSL {'включён' if new_track_ssl else 'отключён'}.",
        parse_mode='HTML'
    )

    # Очищаем данные
    context.user_data.clear()

    # Возвращаемся к списку ресурсов
    await monitoring_resources(update, context)

    # ВАЖНО: завершаем диалог, чтобы можно было снова нажать "Редактировать"
    return ConversationHandler.END


async def edit_toggle_domain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Переключает отслеживание домена."""
    query = update.callback_query
    await query.answer()

    name = context.user_data.get('edit_resource_name')
    if not name:
        await query.edit_message_text("❌ Ошибка: ресурс не выбран.")
        return ConversationHandler.END

    resource = get_resource_by_name(name)
    if not resource:
        await query.edit_message_text("❌ Ресурс не найден.")
        return ConversationHandler.END

    new_track_domain = not resource.get('track_domain', True)

    from database.resource_models import update_resource_settings
    update_resource_settings(name, track_domain=new_track_domain)

    await query.edit_message_text(
        f"✅ Для {name} отслеживание домена {'включено' if new_track_domain else 'отключено'}.",
        parse_mode='HTML'
    )

    context.user_data.clear()
    await monitoring_resources(update, context)
    return ConversationHandler.END

