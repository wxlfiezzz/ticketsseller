import hashlib
import uuid
from datetime import datetime
from database.session import Session
from database.models import User, SubscriptionLink, File, FileDelivery
from services.logger import bot_logger
# УБЕРИТЕ этот импорт: from services.file_manager import FileManager

class SubscriptionService:
    """Сервис управления подписками"""
    
    @staticmethod
    def generate_subscription_token() -> str:
        """Генерирует уникальный токен для подписки"""
        return hashlib.sha256(f"subscription_{uuid.uuid4()}".encode()).hexdigest()[:12]
    
    @staticmethod
    def generate_user_hash(user_id: int) -> str:
        """Генерирует уникальный хэш для пользователя"""
        hash_object = hashlib.sha256(f"{user_id}_{uuid.uuid4()}".encode())
        return hash_object.hexdigest()[:16]
    
    @staticmethod
    def create_subscription_link(seller_id: int) -> str:
        """Создает уникальную одноразовую ссылку для подписки"""
        session = Session()
        try:
            token = SubscriptionService.generate_subscription_token()
            
            link = SubscriptionLink(
                token=token,
                created_by=seller_id
            )
            session.add(link)
            session.commit()
            
            # Получаем username бота (это будет исправлено позже)
            subscription_link = f"https://t.me/your_bot?start={token}"
            return subscription_link
            
        except Exception as e:
            bot_logger.logger.error(f"Ошибка при создании ссылки: {e}")
            session.rollback()
            return None
        finally:
            session.close()
    
    @staticmethod
    def activate_subscription(user_id: int, token: str) -> bool:
        """Активирует подписку по токену"""
        session = Session()
        try:
            bot_logger.logger.info(f"Активация подписки для {user_id} с токеном: {token}")
            
            # Ищем ссылку по токену
            link = session.query(SubscriptionLink).filter_by(token=token).first()
            
            if not link:
                bot_logger.logger.error(f"Ссылка с токеном {token} не найдена")
                return False
            
            if link.is_used:
                bot_logger.logger.error(f"Ссылка уже использована")
                return False
            
            # Проверяем существующего пользователя
            existing_user = session.query(User).filter_by(user_id=user_id).first()
            
            if existing_user and existing_user.has_access:
                bot_logger.logger.error(f"Пользователь уже имеет активную подписку")
                return False
            
            # Создаем или обновляем пользователя
            if not existing_user:
                user_hash = SubscriptionService.generate_user_hash(user_id)
                user = User(
                    user_id=user_id,
                    username="",
                    first_name="",
                    file_hash=user_hash,
                    has_access=True,
                    subscription_date=datetime.utcnow(),
                    pending_file=True
                )
                session.add(user)
                bot_logger.logger.info(f"Создан новый пользователь: {user_id}")
            else:
                existing_user.has_access = True
                existing_user.subscription_date = datetime.utcnow()
                existing_user.pending_file = True
                bot_logger.logger.info(f"Обновлен существующий пользователь: {user_id}")
            
            # Обновляем статус ссылки
            link.is_used = True
            link.used_by = user_id
            link.used_at = datetime.utcnow()
            
            session.commit()
            bot_logger.logger.info(f"Подписка активирована для пользователя {user_id}")
            return True
            
        except Exception as e:
            bot_logger.logger.error(f"Ошибка при активации подписки: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    @staticmethod
    async def auto_send_to_new_users(application):
        """Автоматически отправляет файлы новым пользователям"""
        session = Session()
        try:
            new_users = session.query(User).filter(
                User.has_access == True,
                User.files_received == 0,
                User.pending_file == True
            ).all()
            
            if not new_users:
                return
            
            free_files = session.query(File).filter_by(distributed=False).all()
            
            if not free_files:
                bot_logger.logger.info("Нет свободных файлов для автоматической отправки")
                return
            
            # Импортируем FileManager здесь, чтобы избежать циклического импорта
            from services.file_manager import FileManager
            
            sent_count = 0
            for user_obj, file in zip(new_users, free_files):
                if len(free_files) <= sent_count:
                    break
                    
                try:
                    success = await FileManager.send_file_to_user(user_obj, file, application)
                    if success:
                        sent_count += 1
                        bot_logger.logger.info(f"Автоматически отправлен файл пользователю {user_obj.user_id}")
                except Exception as e:
                    bot_logger.logger.error(f"Ошибка автоматической отправки: {e}")
                    continue
            
            if sent_count > 0:
                bot_logger.logger.info(f"Автоматически отправлено {sent_count} файлов")
                
        except Exception as e:
            bot_logger.logger.error(f"Ошибка в auto_send_to_new_users: {e}")
        finally:
            session.close()