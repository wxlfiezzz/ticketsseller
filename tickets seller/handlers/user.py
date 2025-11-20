from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.auth import AuthService
from services.logger import bot_logger
from database.session import Session
from database.models import User, FileDelivery, File
from datetime import datetime, timedelta
import os

class UserHandler:
    """Обработчики пользовательских команд"""
    
    @staticmethod
    async def my_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Информация о подписке пользователя"""
        user = update.effective_user
        
        if not AuthService.check_user_access(user.id):
            await update.message.reply_text("❌ У вас нет активной подписки.")
            return
        
        session = Session()
        try:
            user_data = session.query(User).filter_by(user_id=user.id).first()
            if user_data:
                sub_date = user_data.subscription_date.strftime('%d.%m.%Y %H:%M') if user_data.subscription_date else "неизвестно"
                
                await update.message.reply_text(
                    f"✅ Ваша подписка активна\n\n"
                    f"🆔 Ваш ID: `{user_data.file_hash}`\n"
                    f"📅 Активирована: {sub_date}\n"
                    f"👤 Имя: {user_data.first_name}\n"
                    f"📨 Получено файлов: {user_data.files_received}\n\n"
                    f"Используйте /myticket для проверки статуса билетов."
                )
        except Exception as e:
            bot_logger.logger.error(f"Ошибка в команде /mysub: {e}")
            await update.message.reply_text("❌ Ошибка при проверке подписки")
        finally:
            session.close()
    
    @staticmethod
    async def my_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Проверка статуса билета пользователя"""
        user = update.effective_user
        
        if not AuthService.check_user_access(user.id):
            await update.message.reply_text("❌ У вас нет активной подписки.")
            return
        
        session = Session()
        try:
            user_data = session.query(User).filter_by(user_id=user.id).first()
            if not user_data:
                await update.message.reply_text("❌ Пользователь не найден.")
                return
            
            # ... остальная логика my_ticket
        except Exception as e:
            bot_logger.logger.error(f"Ошибка в my_ticket: {e}")
            await update.message.reply_text("❌ Ошибка при проверке статуса.")
        finally:
            session.close()
    
    @staticmethod
    async def recover_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Восстановление билета"""
        user = update.effective_user
        
        if not AuthService.check_user_access(user.id):
            await update.message.reply_text("❌ У вас нет активной подписки.")
            return
        
        # ... логика восстановления билета