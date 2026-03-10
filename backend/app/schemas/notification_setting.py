from pydantic import BaseModel


class NotificationSettingResponse(BaseModel):
    notify_time: str | None
    enabled: bool


class NotificationSettingUpdate(BaseModel):
    notify_time: str | None  # "HH:MM" 形式
    enabled: bool
