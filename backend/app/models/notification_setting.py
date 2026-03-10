from sqlalchemy import Boolean, Column, Integer, String

from app.db.base import Base


class NotificationSetting(Base):
    __tablename__ = "notification_settings"

    id = Column(Integer, primary_key=True, default=1)
    notify_time_1 = Column(String, nullable=True)   # "HH:MM" 形式（第1通知時刻）
    notify_time_2 = Column(String, nullable=True)   # "HH:MM" 形式（第2通知時刻）
    enabled = Column(Boolean, nullable=False, default=False)
