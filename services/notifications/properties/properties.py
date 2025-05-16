

from pydantic import BaseModel

class NotificationChannelBaseProperties(BaseModel):
    pass

class TelegramNotificationProperties(NotificationChannelBaseProperties):
    chat_id: str
    token: str
