from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.auth import AuthService
from services.logger import bot_logger
from services.subscription import SubscriptionService
from database.session import Session
from database.models import User, File, FileDelivery, SubscriptionLink, Admin

class CallbackHandler:
    """Обработчик callback кнопок"""
    
    @staticmethod
    async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        user = query.from_user
        
        # Обработка кнопок для пользователей
        if query.data == "recover_ticket":
            from handlers.user import UserHandler
            await UserHandler.recover_ticket(update, context)
            return
        
        elif query.data == "delivery_stats":
            session = Session()
            try:
                deliveries = session.query(FileDelivery).filter_by(user_id=user.id).all()
                
                if not deliveries:
                    await query.edit_message_text("📊 У вас еще нет истории доставок.")
                    return
                
                stats_text = "📊 Детальная статистика доставок:\n\n"
                
                for i, delivery in enumerate(deliveries[-10:], 1):
                    file = session.query(File).filter_by(id=delivery.file_id).first()
                    file_name = file.original_name if file else "Неизвестно"
                    
                    status_emoji = "✅" if delivery.delivery_status == 'sent' else "🔁" if delivery.delivery_status == 'recovered' else "❌"
                    
                    stats_text += (
                        f"{i}. {file_name}\n"
                        f"   {status_emoji} Статус: {delivery.delivery_status}\n"
                        f"   📅 Дата: {delivery.sent_at.strftime('%d.%m.%Y %H:%M')}\n"
                    )
                    
                    if delivery.recovery_attempts > 0:
                        stats_text += f"   🔄 Попыток восстановления: {delivery.recovery_attempts}\n"
                    
                    stats_text += "\n"
                
                if len(deliveries) > 10:
                    stats_text += f"... и еще {len(deliveries) - 10} доставок\n"
                
                await query.edit_message_text(stats_text)
                
            except Exception as e:
                bot_logger.logger.error(f"Ошибка при получении статистики доставок: {e}")
                await query.edit_message_text("❌ Ошибка при получении статистики.")
            finally:
                session.close()
            return
        
        # Проверяем права доступа для админ-функций
        if not AuthService.is_admin(user.id):
            await query.edit_message_text("❌ Доступ запрещен")
            return
        
        # Обработка админ-кнопок
        if query.data == "create_link":
            await CallbackHandler._handle_create_link(query, user)
        
        elif query.data == "stats":
            await CallbackHandler._handle_stats(query, user)
        
        elif query.data == "send_pending":
            await CallbackHandler._handle_send_pending(query, user, context)
        
        elif query.data == "upload_zip":
            await CallbackHandler._handle_upload_zip(query, user)
        
        elif query.data == "distribute_files":
            await CallbackHandler._handle_distribute_files(query, user, context)
        
        elif query.data == "free_tickets_archive":
            await CallbackHandler._handle_free_tickets_archive(query, user)
        
        elif query.data == "subscribers_list":
            await CallbackHandler._handle_subscribers_list(query, user)
        
        elif query.data == "manage_admins":
            await CallbackHandler._handle_manage_admins(query, user)
        
        elif query.data == "back_to_admin":
            await CallbackHandler._handle_back_to_admin(update, context)
    
    @staticmethod
    async def _handle_create_link(query, user):
        """Обработка создания ссылки"""
        await bot_logger.log_admin_action(user, "Создание ссылки подписки")
        
        link = SubscriptionService.create_subscription_link(user.id)
        if link:
            await query.edit_message_text(
                f"✅ Ссылка для подписки создана!\n\n"
                f"🔗 Отправьте эту ссылку покупателю:\n\n"
                f"{link}\n\n"
                f"📝 Просто скопируйте и отправьте ссылку. "
                f"При переходе по ссылке у пользователя автоматически откроется бот и активируется подписка."
            )
        else:
            await query.edit_message_text("❌ Ошибка при создании ссылки")
    
    @staticmethod
    async def _handle_stats(query, user):
        """Обработка показа статистики"""
        await bot_logger.log_admin_action(user, "Просмотр статистики")
        
        session = Session()
        try:
            users_count = session.query(User).count()
            active_users = session.query(User).filter_by(has_access=True).count()
            files_count = session.query(File).count()
            distributed_files = session.query(File).filter_by(distributed=True).count()
            free_files = session.query(File).filter_by(distributed=False).count()
            links_count = session.query(SubscriptionLink).count()
            used_links = session.query(SubscriptionLink).filter_by(is_used=True).count()
            
            stats_text = (
                f"📊 Статистика бота:\n\n"
                f"👥 Всего пользователей: {users_count}\n"
                f"✅ Активных подписок: {active_users}\n"
                f"📁 Всего файлов: {files_count}\n"
                f"📨 Распределено файлов: {distributed_files}\n"
                f"📋 Свободных файлов: {free_files}\n"
                f"🔗 Создано ссылок: {links_count}\n"
                f"🎫 Использовано ссылок: {used_links}"
            )
            
            await query.edit_message_text(stats_text)
        except Exception as e:
            bot_logger.logger.error(f"Ошибка при получении статистики: {e}")
            await query.edit_message_text("❌ Ошибка при получении статистики")
        finally:
            session.close()
    
    @staticmethod
    async def _handle_send_pending(query, user, context):
        """Обработка отправки файлов ожидающим"""
        await bot_logger.log_admin_action(user, "Автоматическая отправка файлов ожидающим")
        
        await query.edit_message_text("🔍 Ищу пользователей без файлов...")
        
        session = Session()
        try:
            users_without_files = session.query(User).filter(
                User.has_access == True,
                User.files_received == 0
            ).all()
            
            if not users_without_files:
                await query.edit_message_text("✅ Все пользователи уже получили свои файлы!")
                return
            
            free_files = session.query(File).filter_by(distributed=False).all()
            
            if not free_files:
                await query.edit_message_text("❌ Нет свободных файлов для отправки!")
                return
            
            if len(free_files) < len(users_without_files):
                await query.edit_message_text(
                    f"⚠️ Недостаточно свободных файлов!\n"
                    f"Пользователей без файлов: {len(users_without_files)}\n"
                    f"Свободных файлов: {len(free_files)}"
                )
                return
            
            await query.edit_message_text(
                f"🔄 Начинаю отправку файлов {len(users_without_files)} пользователям..."
            )
            
            # Импортируем FileManager локально, чтобы избежать циклического импорта
            from services.file_manager import FileManager
            
            sent_count = 0
            failed_users = []
            
            for user_obj, file in zip(users_without_files, free_files):
                try:
                    success = await FileManager.send_file_to_user(user_obj, file, context.application)
                    if success:
                        sent_count += 1
                    else:
                        failed_users.append(f"{user_obj.first_name} (@{user_obj.username})")
                        
                except Exception as e:
                    bot_logger.logger.error(f"Ошибка отправки пользователю {user_obj.user_id}: {e}")
                    failed_users.append(f"{user_obj.first_name} (@{user_obj.username})")
                    continue
            
            result_message = (
                f"✅ Автоматическая отправка завершена!\n\n"
                f"📨 Успешно отправлено: {sent_count}/{len(users_without_files)}\n"
                f"👥 Обработано пользователей: {len(users_without_files)}"
            )
            
            if failed_users:
                result_message += f"\n\n❌ Не удалось отправить {len(failed_users)} пользователям:\n"
                result_message += "\n".join(failed_users[:5])
                if len(failed_users) > 5:
                    result_message += f"\n... и еще {len(failed_users) - 5}"
            
            await query.edit_message_text(result_message)
            
        except Exception as e:
            bot_logger.logger.error(f"Ошибка в send_pending: {e}")
            await query.edit_message_text("❌ Ошибка при отправке файлов")
        finally:
            session.close()
    
    @staticmethod
    async def _handle_upload_zip(query, user):
        """Обработка загрузки ZIP архива"""
        await bot_logger.log_admin_action(user, "Запрос загрузки ZIP архива")
        
        await query.edit_message_text(
            "📦 Загрузите ZIP архив с файлами (PDF, TXT, DOC, DOCX)\n\n"
            "Каждый файл будет автоматически переименован в уникальный хэш."
        )
    
    @staticmethod
    async def _handle_distribute_files(query, user, context):
        """Обработка распределения файлов"""
        from handlers.files import FileHandler
        await FileHandler.distribute_files(query=query)
    
    @staticmethod
    async def _handle_free_tickets_archive(query, user):
        """Обработка создания архива свободных билетов"""
        await query.edit_message_text("📦 Создаю архив со свободными билетами...")
        # TODO: Реализовать создание архива
        await query.edit_message_text("❌ Функция создания архива временно недоступна")
    
    @staticmethod
    async def _handle_subscribers_list(query, user):
        """Обработка показа списка подписчиков"""
        await bot_logger.log_admin_action(user, "Просмотр списка подписчиков")
        
        session = Session()
        try:
            subscribers = session.query(User).filter_by(has_access=True).all()
            
            if not subscribers:
                await query.edit_message_text("👥 Нет активных подписчиков")
                return
            
            subscribers_text = "👥 Активные подписчики:\n\n"
            for i, sub in enumerate(subscribers, 1):
                sub_date = sub.subscription_date.strftime('%d.%m.%Y') if sub.subscription_date else "неизвестно"
                subscribers_text += f"{i}. {sub.first_name} (@{sub.username})\n"
                subscribers_text += f"   🆔 ID: {sub.file_hash}\n"
                subscribers_text += f"   📅 Подписка с: {sub_date}\n\n"
            
            if len(subscribers_text) > 4000:
                subscribers_text = subscribers_text[:4000] + "\n..."
            
            await query.edit_message_text(subscribers_text)
        except Exception as e:
            bot_logger.logger.error(f"Ошибка при получении списка подписчиков: {e}")
            await query.edit_message_text("❌ Ошибка при получении списка")
        finally:
            session.close()
    
    @staticmethod
    async def _handle_manage_admins(query, user):
        """Обработка управления администраторами"""
        await bot_logger.log_admin_action(user, "Открытие управления администраторами")
        
        session = Session()
        try:
            admins = session.query(Admin).all()
            
            admins_text = "👑 Список администраторов:\n\n"
            for i, admin in enumerate(admins, 1):
                added_by_admin = session.query(Admin).filter_by(user_id=admin.added_by).first()
                added_by_name = added_by_admin.first_name if added_by_admin else "Система"
                
                admins_text += (
                    f"{i}. {admin.first_name} (@{admin.username})\n"
                    f"   🆔 ID: {admin.user_id}\n"
                    f"   📅 Добавлен: {admin.added_at.strftime('%d.%m.%Y %H:%M')}\n"
                    f"   👤 Кем добавлен: {added_by_name}\n\n"
                )
            
            keyboard = [
                [InlineKeyboardButton("➕ Добавить админа", callback_data="add_admin_panel")],
                [InlineKeyboardButton("➖ Удалить админа", callback_data="remove_admin_panel")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_admin")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(admins_text, reply_markup=reply_markup)
            
        except Exception as e:
            bot_logger.logger.error(f"Ошибка при получении списка админов: {e}")
            await query.edit_message_text("❌ Ошибка при получении списка администраторов")
        finally:
            session.close()
    
    @staticmethod
    async def _handle_back_to_admin(update, context):
        """Обработка возврата в админ-панель"""
        from handlers.admin import AdminHandler
        await AdminHandler.admin_panel(update, context)