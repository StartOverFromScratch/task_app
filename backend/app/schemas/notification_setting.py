from pydantic import BaseModel

DEFAULT_NOTIFY_TIME_1 = "09:00"
DEFAULT_NOTIFY_TIME_2 = "16:00"


class NotificationSettingResponse(BaseModel):
    notify_time_1: str | None
    notify_time_2: str | None
    enabled: bool


class NotificationSettingUpdate(BaseModel):
    notify_time_1: str | None
    notify_time_2: str | None
    enabled: bool
