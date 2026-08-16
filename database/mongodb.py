"""
Подключение к MongoDB
"""
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

client = None
db = None

def get_db():
    """Возвращает подключение к базе данных."""
    global client, db
    
    if db is not None:
        return db
    
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        db = client['bot_database']
        print("✅ Подключение к MongoDB успешно")
        return db
    except ConnectionFailure as e:
        print(f"❌ Ошибка подключения к MongoDB: {e}")
        return None

def close_connection():
    """Закрывает подключение к MongoDB."""
    global client
    if client:
        client.close()
        client = None
        print("🔒 Подключение к MongoDB закрыто")
