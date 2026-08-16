"""
Модели для работы с пользователями в MongoDB
"""
from datetime import datetime
from pymongo import ASCENDING
from .mongodb import get_db

def get_users_collection():
    """Возвращает коллекцию пользователей."""
    db = get_db()
    if db is None:
        return None
    collection = db['users']
    collection.create_index('telegram_id', unique=True)
    collection.create_index('status')
    return collection

def create_user(telegram_id, full_name, email, roles=None, status='pending'):
    """Создаёт новую заявку пользователя."""
    if roles is None:
        roles = ['guest']
    
    collection = get_users_collection()
    if collection is None:
        return None
    
    user_data = {
        'telegram_id': telegram_id,
        'full_name': full_name,
        'email': email,
        'roles': roles,
        'status': status,
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }
    
    try:
        result = collection.insert_one(user_data)
        user_data['_id'] = result.inserted_id
        print(f"✅ Пользователь {full_name} создан (ID: {telegram_id})")
        return user_data
    except Exception as e:
        print(f"❌ Ошибка создания пользователя: {e}")
        return None

def get_user_by_id(telegram_id):
    """Получает пользователя по Telegram ID."""
    collection = get_users_collection()
    if collection is None:
        return None
    return collection.find_one({'telegram_id': telegram_id})

def update_user_status(telegram_id, status):
    """Обновляет статус заявки пользователя."""
    collection = get_users_collection()
    if collection is None:
        return False
    
    result = collection.update_one(
        {'telegram_id': telegram_id},
        {'$set': {'status': status, 'updated_at': datetime.now()}}
    )
    return result.modified_count > 0

def update_user_roles(telegram_id, roles):
    """Обновляет роли пользователя."""
    collection = get_users_collection()
    if collection is None:
        return False
    
    result = collection.update_one(
        {'telegram_id': telegram_id},
        {'$set': {'roles': roles, 'updated_at': datetime.now()}}
    )
    return result.modified_count > 0

def get_all_users(status=None):
    """Получает список всех пользователей."""
    collection = get_users_collection()
    if collection is None:
        return []
    
    query = {}
    if status:
        query['status'] = status
    
    return list(collection.find(query))


def set_user_active(telegram_id, is_active):
    """Устанавливает статус активности пользователя."""
    collection = get_users_collection()
    if collection is None:
        return False

    result = collection.update_one(
        {'telegram_id': telegram_id},
        {'$set': {'is_active': is_active, 'updated_at': datetime.now()}}
    )
    return result.modified_count > 0


def get_active_users():
    """Возвращает список активных пользователей."""
    collection = get_users_collection()
    if collection is None:
        return []

    return list(collection.find({'is_active': True}))


def delete_user(telegram_id):
    """Удаляет пользователя из базы."""
    collection = get_users_collection()
    if collection is None:
        return False

    result = collection.delete_one({'telegram_id': telegram_id})
    return result.deleted_count > 0