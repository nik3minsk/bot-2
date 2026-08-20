"""
Модели для управления доступом к функциям.
"""
from datetime import datetime
from .mongodb import get_db


def get_features_collection():
    """Возвращает коллекцию функций."""
    db = get_db()
    if db is None:
        return None
    return db['features']


def get_feature(feature_id):
    """Получает настройки функции по ID."""
    collection = get_features_collection()
    if collection is None:
        return None
    return collection.find_one({'feature_id': feature_id})


def get_all_features():
    """Возвращает список всех функций."""
    collection = get_features_collection()
    if collection is None:
        return []
    return list(collection.find())


def update_feature_roles(feature_id, roles):
    """Обновляет список ролей для функции."""
    collection = get_features_collection()
    if collection is None:
        return False

    result = collection.update_one(
        {'feature_id': feature_id},
        {'$set': {'allowed_roles': roles, 'updated_at': datetime.now()}}
    )
    return result.modified_count > 0


def init_default_features():
    """Инициализирует стандартные функции."""
    default_features = [
        {
            'feature_id': 'salary_report',
            'name': 'Отчёт по зарплате',
            'description': 'Просмотр зарплат сотрудников',
            'allowed_roles': ['boss', 'buh'],
            'enabled': True,
            'created_at': datetime.now()
        },
        {
            'feature_id': 'user_management',
            'name': 'Управление пользователями',
            'description': 'Добавление, блокировка, удаление пользователей',
            'allowed_roles': ['admin', 'dev'],
            'enabled': True,
            'created_at': datetime.now()
        },
        {
            'feature_id': 'monitoring_resources',
            'name': 'Мониторинг ресурсов',
            'description': 'SSL сертификаты и домены',
            'allowed_roles': ['admin', 'dev'],
            'enabled': True,
            'created_at': datetime.now()
        },
    ]

    collection = get_features_collection()
    if collection is None:
        return

    for feature in default_features:
        existing = collection.find_one({'feature_id': feature['feature_id']})
        if not existing:
            collection.insert_one(feature)