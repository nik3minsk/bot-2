"""
Модели для работы с ресурсами (SSL сертификаты и домены)
"""
from datetime import datetime
from .mongodb import get_db


def get_resources_collection():
    """Возвращает коллекцию ресурсов."""
    db = get_db()
    if db is None:
        return None
    return db['resources']


def get_all_resources():
    """Возвращает список всех ресурсов."""
    collection = get_resources_collection()
    if collection is None:
        return []
    return list(collection.find())


def get_resource_by_name(name):
    """Получает ресурс по имени."""
    collection = get_resources_collection()
    if collection is None:
        return None
    return collection.find_one({'name': name})


def add_resource(name, track_domain=True, track_ssl=False, url=None, registrar=None):
    """Добавляет новый ресурс."""
    collection = get_resources_collection()
    if collection is None:
        return None

    resource = {
        'name': name,
        'track_domain': track_domain,
        'track_ssl': track_ssl,
        'url': url,
        'registrar': registrar,
        'domain_days': None,
        'ssl_days': None,
        'last_check': None,
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
        'status': 'active'  # active | warning | expired
    }

    try:
        result = collection.insert_one(resource)
        resource['_id'] = result.inserted_id
        return resource
    except Exception as e:
        print(f"❌ Ошибка добавления ресурса: {e}")
        return None


def update_resource_days(name, domain_days=None, ssl_days=None):
    """Обновляет количество дней до истечения."""
    collection = get_resources_collection()
    if collection is None:
        return False

    update_data = {'updated_at': datetime.now(), 'last_check': datetime.now()}
    if domain_days is not None:
        update_data['domain_days'] = domain_days
    if ssl_days is not None:
        update_data['ssl_days'] = ssl_days

    result = collection.update_one(
        {'name': name},
        {'$set': update_data}
    )
    return result.modified_count > 0


def delete_resource(name):
    """Удаляет ресурс."""
    collection = get_resources_collection()
    if collection is None:
        return False
    result = collection.delete_one({'name': name})
    return result.deleted_count > 0


def update_resource_settings(name, track_domain=None, track_ssl=None, url=None, registrar=None):
    """Обновляет настройки ресурса."""
    collection = get_resources_collection()
    if collection is None:
        return False

    update_data = {'updated_at': datetime.now()}
    if track_domain is not None:
        update_data['track_domain'] = track_domain
    if track_ssl is not None:
        update_data['track_ssl'] = track_ssl
    if url is not None:
        update_data['url'] = url
    if registrar is not None:
        update_data['registrar'] = registrar

    result = collection.update_one(
        {'name': name},
        {'$set': update_data}
    )
    return result.modified_count > 0


def update_domain_days(name, days, expire_date=None, registrar=None):
    """Обновляет дни, дату и регистратора домена."""
    collection = get_resources_collection()
    if collection is None:
        return False

    update_data = {
        'domain_days': days,
        'last_check': datetime.now()
    }
    if expire_date:
        update_data['domain_expire_date'] = expire_date
    if registrar:
        update_data['registrar'] = registrar

    result = collection.update_one({'name': name}, {'$set': update_data})
    return result.modified_count > 0


def update_ssl_days(name, days):
    """Обновляет только дни SSL, без перезаписи других полей."""
    collection = get_resources_collection()
    if collection is None:
        return False

    result = collection.update_one(
        {'name': name},
        {'$set': {'ssl_days': days, 'last_check': datetime.now()}}
    )
    return result.modified_count > 0


def get_min_days():
    """Возвращает минимальное количество дней до истечения среди всех ресурсов."""
    collection = get_resources_collection()
    if collection is None:  # <-- ИСПРАВЛЕНО
        return None

    resources = list(collection.find())
    min_days = None

    for resource in resources:
        # Проверяем домен
        if resource.get('track_domain') and resource.get('domain_days') is not None:
            days = resource['domain_days']
            if min_days is None or days < min_days:
                min_days = days

        # Проверяем SSL
        if resource.get('track_ssl') and resource.get('ssl_days') is not None:
            days = resource['ssl_days']
            if min_days is None or days < min_days:
                min_days = days

    return min_days


# ============================================================
# ДАТЫ ИСТЕЧЕНИЯ
# ============================================================

def update_domain_days(name, days, expire_date=None, registrar=None):
    """Обновляет дни, дату и регистратора домена."""
    collection = get_resources_collection()
    if collection is None:
        return False

    update_data = {
        'domain_days': days,
        'last_check': datetime.now()
    }
    if expire_date:
        update_data['domain_expire_date'] = expire_date
    # Убираем if registrar: — сохраняем всегда
    update_data['registrar'] = registrar

    result = collection.update_one({'name': name}, {'$set': update_data})
    return result.modified_count > 0


def update_ssl_days(name, days, expire_date=None):
    """Обновляет дни и дату истечения SSL."""
    collection = get_resources_collection()
    if collection is None:
        return False

    update_data = {
        'ssl_days': days,
        'last_check': datetime.now()
    }
    if expire_date:
        update_data['ssl_expire_date'] = expire_date

    result = collection.update_one({'name': name}, {'$set': update_data})
    return result.modified_count > 0


def get_min_days():
    """Возвращает минимальное количество дней до истечения среди всех ресурсов."""
    collection = get_resources_collection()
    if collection is None:
        return None

    resources = list(collection.find())
    min_days = None

    for resource in resources:
        if resource.get('track_domain') and resource.get('domain_days') is not None:
            days = resource['domain_days']
            if min_days is None or days < min_days:
                min_days = days

        if resource.get('track_ssl') and resource.get('ssl_days') is not None:
            days = resource['ssl_days']
            if min_days is None or days < min_days:
                min_days = days

    return min_days


def update_resource_settings(name, track_domain=None, track_ssl=None, url=None, registrar=None):
    """Обновляет настройки ресурса."""
    collection = get_resources_collection()
    if collection is None:
        return False

    update_data = {'updated_at': datetime.now()}
    if track_domain is not None:
        update_data['track_domain'] = track_domain
    if track_ssl is not None:
        update_data['track_ssl'] = track_ssl
    if url is not None:
        update_data['url'] = url
    if registrar is not None:
        update_data['registrar'] = registrar  # <-- сохраняем

    result = collection.update_one({'name': name}, {'$set': update_data})
    return result.modified_count > 0