"""
Модуль настройки логирования.
"""
import logging
import sys
from datetime import datetime
import os

# Уровни логирования
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}


def setup_logger(name: str = __name__, level: str = 'INFO', log_file: str = None) -> logging.Logger:
    """
    Настраивает и возвращает логгер с заданным именем.

    Args:
        name (str): Имя логгера (обычно __name__)
        level (str): Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file (str): Путь к файлу для логирования (опционально)

    Returns:
        logging.Logger: Настроенный логгер
    """
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVELS.get(level, logging.INFO))

    # Очищаем существующие обработчики
    if logger.handlers:
        logger.handlers.clear()

    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Вывод в консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOG_LEVELS.get(level, logging.INFO))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Вывод в файл (если указан)
    if log_file:
        # Создаём папку для логов, если её нет
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # В файл пишем всё
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Возвращает логгер с именем.

    Args:
        name (str): Имя логгера

    Returns:
        logging.Logger: Логгер
    """
    return logging.getLogger(name)