import os
import zipfile
import uuid
import hashlib
from telegram import Update
from telegram.ext import ContextTypes
from services.auth import AuthService
from services.logger import bot_logger
from database.session import Session
from database.models import File
from config import Config

class FileHandler:
    """Обработчики работы с файлами"""
    
    @staticmethod
    async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик документов (ZIP архивов)"""
        user = update.effective_user
        
        if not AuthService.is_admin(user.id):
            await update.message.reply_text("❌ Только владелец может загружать файлы")
            return
        
        document = update.message.document
        file_name = document.file_name
        
        if not file_name.lower().endswith('.zip'):
            await update.message.reply_text("❌ Пожалуйста, загрузите ZIP архив")
            return
        
        await update.message.reply_text("📦 Начинаю обработку ZIP архива...")
        
        try:
            bot_logger.log_admin_action(
                user, 
                "Загрузка ZIP архива", 
                f"Файл: {file_name}"
            )
            
            file = await document.get_file()
            zip_path = os.path.join(Config.ZIP_FOLDER, f"temp_{document.file_id}.zip")
            await file.download_to_drive(zip_path)
            
            processed_count = await FileHandler.process_zip_archive(zip_path)
            
            os.remove(zip_path)
            
            await update.message.reply_text(
                f"✅ ZIP архив обработан успешно!\n"
                f"📄 Обработано файлов: {processed_count}\n"
                f"🎯 Все файлы переименованы в уникальные хэши"
            )
            
        except Exception as e:
            bot_logger.logger.error(f"Ошибка при обработке ZIP архива: {e}")
            await update.message.reply_text("❌ Ошибка при обработке ZIP архива")
    
    @staticmethod
    async def process_zip_archive(zip_path: str) -> int:
        """Обрабатывает ZIP архив и сохраняет файлы с хэшированными именами"""
        processed_count = 0
        session = Session()
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for file_info in zip_ref.infolist():
                    try:
                        if file_info.filename.lower().endswith(('.pdf', '.txt', '.doc', '.docx')) and not file_info.is_dir():
                            extracted_path = zip_ref.extract(file_info, Config.UPLOAD_FOLDER)
                            
                            file_hash = hashlib.sha256(f"{uuid.uuid4()}".encode()).hexdigest()[:16]
                            original_ext = os.path.splitext(file_info.filename)[1]
                            new_filename = f"{file_hash}{original_ext}"
                            new_file_path = os.path.join(Config.UPLOAD_FOLDER, new_filename)
                            
                            os.rename(extracted_path, new_file_path)
                            
                            file_record = File(
                                original_name=os.path.basename(file_info.filename),
                                hash_name=file_hash,
                                file_path=new_file_path
                            )
                            session.add(file_record)
                            processed_count += 1
                            
                    except Exception as e:
                        bot_logger.logger.error(f"Ошибка при обработке файла {file_info.filename}: {e}")
                        continue
            
            session.commit()
            
        except Exception as e:
            bot_logger.logger.error(f"Ошибка при обработке архива: {e}")
            session.rollback()
        finally:
            session.close()
        
        return processed_count