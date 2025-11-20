from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.auth import AuthService
from services.logger import bot_logger
from services.subscription import SubscriptionService
from database.session import Session
from database.models import User, File, Admin

class AdminHandler:
    """Обработчики административных команд"""
    
    @staticmethod
    async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Панель администратора"""
        user = update.effective_user
        
        if not AuthService.is_admin(user.id):
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        bot_logger.log_admin_action(user, "Открытие панели администратора")
        
        # Получаем статистику
        users_without_files, free_files = AdminHandler._get_stats()
        
        keyboard = [
            [InlineKeyboardButton("🔗 Создать ссылку подписки", callback_data="create_link")],
            [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
            [InlineKeyboardButton("📦 Загрузить ZIP архив", callback_data="upload_zip")],
            [InlineKeyboardButton("🎫 Распределить файлы", callback_data="distribute_files")],
            [InlineKeyboardButton(f"🚀 Отправить ожидающим ({users_without_files})", callback_data="send_pending")],
            [InlineKeyboardButton("📦 Архив свободных билетов", callback_data="free_tickets_archive")],
            [InlineKeyboardButton("👥 Список подписчиков", callback_data="subscribers_list")],
            [InlineKeyboardButton("👑 Управление админами", callback_data="manage_admins")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        status_info = ""
        if users_without_files > 0:
            status_info = f"\n\n⚠️ *{users_without_files} пользователей ожидают файлы*\n🆓 Свободных файлов: {free_files}"
        
        await update.message.reply_text(
            f"👑 Панель управления{status_info}\n\n"
            "Выберите действие:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    @staticmethod
    def _get_stats():
        """Получает статистику для админ-панели"""
        session = Session()
        try:
            users_without_files = session.query(User).filter(
                User.has_access == True,
                User.files_received == 0
            ).count()
            
            free_files = session.query(File).filter_by(distributed=False).count()
            return users_without_files, free_files
        except Exception as e:
            bot_logger.logger.error(f"Ошибка получения статистики: {e}")
            return 0, 0
        finally:
            session.close()
    
    @staticmethod
    async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Добавление администратора"""
        user = update.effective_user
        
        if not AuthService.is_admin(user.id):
            await update.message.reply_text("❌ У вас нет прав для выполнения этой команды.")
            return
        
        # ... остальная логика добавления админа