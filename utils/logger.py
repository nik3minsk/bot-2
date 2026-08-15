# utils/logger.py
"""
Модуль настройки логирования.
"""
import logging
import sys


def setup_logger(name: str = __name__, level: int = logging.INFO) -> logging.Logger:
    """
    Настраивает и возвращает логгер с заданным именем.

    Args:
        name (str): Имя логгера (обычно __name__)
        level (int): Уровень логирования (по умолчанию INFO)

    Returns:
        logging.Logger: Настроенный логгер
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Создаём обработчик для вывода в консоль
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    # Формат вывода: время - имя - уровень - сообщение
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger