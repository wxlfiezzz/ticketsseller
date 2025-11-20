import logging
import logging.handlers
import os
from config import Config

class OptimizedLogger:
    """Оптимизированная система логирования"""
    
    def __init__(self):
        self.setup_logging()
    
    def setup_logging(self):
        """Настройка системы логирования"""
        # Создаем папку для логов, если она не существует
        os.makedirs(Config.LOG_FOLDER, exist_ok=True)
        
        # Основной логгер
        self.logger = logging.getLogger('TelegramBot')
        self.logger.setLevel(logging.INFO)
        
        # Форматтер с минимальной информацией
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Ротируемый файловый обработчик
        log_file = os.path.join(Config.LOG_FOLDER, 'bot_actions.log')
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=Config.MAX_LOG_SIZE,
            backupCount=Config.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        
        # Добавляем обработчик
        self.logger.addHandler(file_handler)
        
        # Также добавляем вывод в консоль для отладки
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def log_admin_action(self, admin_user: object, action: str, details: str = ""):
        """Логирование действий администратора"""
        try:
            log_message = f"ADMIN | {admin_user.id} | {admin_user.first_name} | {action}"
            if details:
                log_message += f" | {details}"
            
            self.logger.info(log_message)
            
        except Exception as e:
            self.logger.error(f"LOG_ERROR: {e}")

# Глобальный экземпляр логгера
bot_logger = OptimizedLogger()