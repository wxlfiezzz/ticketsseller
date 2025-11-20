from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from datetime import datetime
from database.session import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True)
    username = Column(String)
    first_name = Column(String)
    has_access = Column(Boolean, default=False)
    subscription_date = Column(DateTime)
    file_hash = Column(String, unique=True)
    last_file_sent = Column(DateTime)
    files_received = Column(Integer, default=0)
    pending_file = Column(Boolean, default=False)

class SubscriptionLink(Base):
    __tablename__ = 'subscription_links'
    id = Column(Integer, primary_key=True)
    token = Column(String, unique=True)
    created_by = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    used_by = Column(Integer, default=None)
    used_at = Column(DateTime, default=None)
    is_used = Column(Boolean, default=False)

class File(Base):
    __tablename__ = 'files'
    id = Column(Integer, primary_key=True)
    original_name = Column(String)
    hash_name = Column(String, unique=True)
    file_path = Column(String)
    distributed = Column(Boolean, default=False)
    distributed_to = Column(Integer, default=None)
    distributed_at = Column(DateTime, default=None)
    backup_path = Column(String)

class FileDelivery(Base):
    __tablename__ = 'file_deliveries'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    file_id = Column(Integer)
    sent_at = Column(DateTime, default=datetime.utcnow)
    delivery_status = Column(String, default='sent')
    error_message = Column(Text)
    recovery_attempts = Column(Integer, default=0)
    last_recovery_attempt = Column(DateTime)

class Admin(Base):
    __tablename__ = 'admins'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True)
    username = Column(String)
    first_name = Column(String)
    added_by = Column(Integer)
    added_at = Column(DateTime, default=datetime.utcnow)