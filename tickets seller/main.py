from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import Config
from database.session import init_db

def setup_handlers(application):
    """Настройка обработчиков"""
    
    # Импортируем обработчики здесь, чтобы избежать циклических импортов
    from handlers.start import StartHandler
    from handlers.admin import AdminHandler
    from handlers.user import UserHandler
    from handlers.files import FileHandler
    from handlers.callbacks import CallbackHandler
    
    # Команды
    application.add_handler(CommandHandler("start", StartHandler.start))
    application.add_handler(CommandHandler("admin", AdminHandler.admin_panel))
    application.add_handler(CommandHandler("mysub", UserHandler.my_subscription))
    application.add_handler(CommandHandler("myticket", UserHandler.my_ticket))
    application.add_handler(CommandHandler("recover", UserHandler.recover_ticket))
    application.add_handler(CommandHandler("addadmin", AdminHandler.add_admin))
    application.add_handler(CommandHandler("removeadmin", AdminHandler.remove_admin))
    application.add_handler(CommandHandler("send_pending", AdminHandler.send_pending_files))
    
    # Обработчики сообщений
    application.add_handler(MessageHandler(filters.Document.ALL, FileHandler.handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, StartHandler.handle_message))
    
    # Обработчики callback
    application.add_handler(CallbackQueryHandler(CallbackHandler.button_handler))

def main():
    """Главная функция запуска бота"""
    # Инициализация
    Config.create_folders()
    init_db()
    
    # Создание приложения
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    # Настройка обработчиков
    setup_handlers(application)
    
    # Запуск бота
    from services.logger import bot_logger
    bot_logger.logger.info("Бот запускается...")
    application.run_polling()

if __name__ == "__main__":
    main()