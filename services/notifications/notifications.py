

from .interfaces.notification_channel_interface import INotificationChannel
from .properties.properties import TelegramNotificationProperties, NotificationChannelBaseProperties
from .channels.telegram_notification_channel import TelegramNotificationChannel

class NotificationService:
    
    def __init__(self, properties: NotificationChannelBaseProperties) -> None:
        self._channel = self._get_channel(properties)
        
    def _get_channel(self, properties: NotificationChannelBaseProperties) -> INotificationChannel:
        if isinstance(properties, TelegramNotificationProperties):
            return TelegramNotificationChannel(properties)
        else:
            raise Exception("ERROR: El canal de comunicación seleccionado no existe")
    
    async def send_notification(self, title: str, message: str):
        await self._channel.send_message(title, message)
