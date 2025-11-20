# services/__init__.py

# Оставляем только самые базовые импорты, которые не зависят от других модулей
from .logger import bot_logger

__all__ = ['bot_logger']