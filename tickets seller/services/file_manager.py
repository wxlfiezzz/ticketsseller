# services/file_manager.py
import os
import shutil
import hashlib
import uuid
from datetime import datetime
from database.session import Session
from database.models import File, FileDelivery, User
from services.logger import bot_logger
from config import Config

class FileManager:
    """Сервис управления файлами"""
    
    @staticmethod
    def create_backup_copy(file_path: str, user_hash: str) -> str:
        """Создает резервную копию файла"""
        try:
            backup_filename = f"{user_hash}_backup{os.path.splitext(file_path)[1]}"
            backup_path = os.path.join(Config.BACKUP_FOLDER, backup_filename)
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception as e:
            bot_logger.logger.error(f"Ошибка при создании резервной копии: {e}")
            return None
    
    @staticmethod
    async def send_file_to_user(user_obj: User, file: File, application) -> bool:
        """Отправляет файл пользователю и обновляет статусы"""
        session = Session()
        try:
            file_ext = os.path.splitext(file.file_path)[1]
            
            backup_path = FileManager.create_backup_copy(file.file_path, user_obj.file_hash)
            
            with open(file.file_path, 'rb') as file_data:
                await application.bot.send_document(
                    chat_id=user_obj.user_id,
                    document=file_data,
                    filename=f"{user_obj.file_hash}{file_ext}",
                    caption=(
                        f"🎫 Ваш уникальный файл!\n\n"
                        f"🆔 Ваш ID: `{user_obj.file_hash}`\n"
                        f"📁 Исходное название: {file.original_name}\n\n"
                        f"💾 Сохраните файл в надежном месте!\n"
                        f"🔧 Если файл будет утерян, используйте /recover для восстановления"
                    )
                )
            
            file.distributed = True
            file.distributed_to = user_obj.user_id
            file.distributed_at = datetime.utcnow()
            file.backup_path = backup_path
            
            delivery = FileDelivery(
                user_id=user_obj.user_id,
                file_id=file.id,
                delivery_status='sent'
            )
            session.add(delivery)
            
            user_obj.files_received += 1
            user_obj.last_file_sent = datetime.utcnow()
            user_obj.pending_file = False
            
            session.commit()
            return True
            
        except Exception as e:
            bot_logger.logger.error(f"Ошибка отправки файла пользователю {user_obj.user_id}: {e}")
            
            delivery = FileDelivery(
                user_id=user_obj.user_id,
                file_id=file.id,
                delivery_status='failed',
                error_message=str(e)
            )
            session.add(delivery)
            session.commit()
            return False
        finally:
            session.close()
    
    @staticmethod
    def generate_user_hash(user_id: int) -> str:
        """Генерирует уникальный хэш для пользователя"""
        hash_object = hashlib.sha256(f"{user_id}_{uuid.uuid4()}".encode())
        return hash_object.hexdigest()[:16]