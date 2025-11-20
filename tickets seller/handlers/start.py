from telegram import Update
from telegram.ext import ContextTypes
from services.auth import AuthService
from services.subscription import SubscriptionService
from services.logger import bot_logger
from database.session import Session
from database.models import User

class StartHandler:
    """Обработчик команды start"""
    
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        try:
            # Проверяем параметры запуска для активации подписки
            if context.args and len(context.args) > 0:
                token = context.args[0]
                if SubscriptionService.activate_subscription(user.id, token):
                    # Обновляем данные пользователя
                    session = Session()
                    try:
                        existing_user = session.query(User).filter_by(user_id=user.id).first()
                        if existing_user:
                            existing_user.username = user.username or ""
                            existing_user.first_name = user.first_name or ""
                            existing_user.pending_file = True
                            session.commit()
                        
                        # Пытаемся автоматически отправить файл
                        await SubscriptionService.auto_send_to_new_users(context.application)
                        
                        await update.message.reply_text(
                            "🎉 Подписка успешно активирована!\n\n"
                            "Теперь у вас есть доступ к боту. "
                            "Проверяем наличие файлов для вас...\n\n"
                            "Используйте команды:\n"
                            "/mysub - информация о подписке\n"
                            "/myticket - статус билетов\n"
                            "/recover - восстановить билет"
                        )
                        return
                        
                    except Exception as e:
                        bot_logger.logger.error(f"Ошибка обновления пользователя {user.id}: {e}")
                        await update.message.reply_text("❌ Ошибка при обновлении данных пользователя.")
                        return
                    finally:
                        session.close()
                else:
                    await update.message.reply_text(
                        "❌ Недействительная или использованная ссылка подписки.\n"
                        "Обратитесь к продавцу для получения новой ссылки."
                    )
                    return
            
            # Обычный старт
            if not AuthService.check_user_access(user.id) and not AuthService.is_admin(user.id):
                await update.message.reply_text(
                    "🔒 Этот бот доступен только по подписке.\n\n"
                    "Для получения доступа:\n"
                    "1. Обратитесь к продавцу\n"
                    "2. Получите уникальную ссылку\n"
                    "3. Перейдите по ссылке для активации подписки\n\n"
                    "Если у вас есть ссылка, просто перейдите по ней."
                )
                return
            
            # Пользователь с доступом или админ
            if AuthService.is_admin(user.id):
                await update.message.reply_text(
                    f"👑 Добро пожаловать, администратор {user.first_name}!\n\n"
                    f"Используйте команду /admin для доступа к панели управления."
                )
            else:
                session = Session()
                try:
                    user_data = session.query(User).filter_by(user_id=user.id).first()
                    
                    if user_data and user_data.files_received == 0:
                        status_text = (
                            f"👋 Добро пожаловать, {user.first_name}!\n\n"
                            f"🎫 Ваш статус: Активная подписка\n"
                            f"🆔 Ваш уникальный ID: `{user_data.file_hash}`\n"
                            f"📭 Статус файлов: Ожидаем распределения\n\n"
                            f"Файл будет отправлен вам автоматически в ближайшее время.\n"
                            f"Если файл не пришел, администратор будет уведомлен."
                        )
                    else:
                        status_text = (
                            f"👋 Добро пожаловать, {user.first_name}!\n\n"
                            f"🎫 Ваш статус: Активная подписка\n"
                            f"🆔 Ваш уникальный ID: `{user_data.file_hash}`\n"
                            f"📨 Получено файлов: {user_data.files_received}\n\n"
                            "Доступные команды:\n"
                            "/mysub - информация о подписке\n"
                            "/myticket - статус билетов\n"
                            "/recover - восстановить билет"
                        )
                    
                    await update.message.reply_text(status_text)
                finally:
                    session.close()
        
        except Exception as e:
            bot_logger.logger.error(f"Ошибка в команде /start: {e}")
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")
    
    @staticmethod
    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user = update.effective_user
        
        if not AuthService.check_user_access(user.id) and not AuthService.is_admin(user.id):
            await update.message.reply_text(
                "🔒 Бот доступен только по подписке.\n\n"
                "Для получения доступа обратитесь к продавцу."
            )
            return
        
        await update.message.reply_text(
            "ℹ️ Используйте команды:\n"
            "/start - информация о боте\n"
            "/mysub - информация о вашей подписке\n"
            "/myticket - статус ваших билетов\n"
            "/recover - восстановить утерянный билет\n\n"
            "Ожидайте распределения файлов от владельца."
        )