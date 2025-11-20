import os
from typing import List

class Config:
    """Конфигурация бота"""
    
    # Токен бота
    BOT_TOKEN = "8313075300:AAFedctDG5EAlw6ggQhgCWn1bauSMPhbQTI"
    
    # Список администраторов
    ADMIN_IDS = [1049172316]
    SELLER_IDS = [1049172316]
    
    # Лимиты
    MAX_FILES = 1000
    
    # Папки для файлов
    UPLOAD_FOLDER = "pdf_files"
    ZIP_FOLDER = "zip_archives"
    EXCEL_FOLDER = "excel_reports"
    ARCHIVE_FOLDER = "ticket_archives"
    BACKUP_FOLDER = "backup_files"
    LOG_FOLDER = "bot_logs"
    
    # Настройки логирования
    MAX_LOG_SIZE = 5 * 1024 * 1024  # 5MB
    LOG_BACKUP_COUNT = 3
    
    @classmethod
    def create_folders(cls):
        """Создает необходимые папки"""
        folders = [
            cls.UPLOAD_FOLDER,
            cls.ZIP_FOLDER,
            cls.EXCEL_FOLDER,
            cls.ARCHIVE_FOLDER,
            cls.BACKUP_FOLDER,
            cls.LOG_FOLDER
        ]
        
        for folder in folders:
            os.makedirs(folder, exist_ok=True)