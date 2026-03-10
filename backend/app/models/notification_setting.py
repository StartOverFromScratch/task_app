from sqlalchemy import Boolean, Column, Integer, String

from app.db.base import Base


class NotificationSetting(Base):
    __tablename__ = "notification_settings"

    id = Column(Integer, primary_key=True, default=1)
    notify_time = Column(String, nullable=True)   # "HH:MM" 形式、None = 無効
    enabled = Column(Boolean, nullable=False, default=False)
