from database.session import Session
from database.models import User, Admin
from config import Config

class AuthService:
    """Сервис авторизации и проверки прав"""
    
    @staticmethod
    def is_admin(user_id: int) -> bool:
        """Проверяет, является ли пользователь администратором"""
        session = Session()
        try:
            admins = session.query(Admin).all()
            admin_ids = [admin.user_id for admin in admins]
            admin_ids.extend(Config.ADMIN_IDS)
            return user_id in list(set(admin_ids))
        except Exception as e:
            return False
        finally:
            session.close()
    
    @staticmethod
    def check_user_access(user_id: int) -> bool:
        """Проверяет есть ли у пользователя доступ к боту"""
        session = Session()
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            return user and user.has_access
        except Exception as e:
            return False
        finally:
            session.close()