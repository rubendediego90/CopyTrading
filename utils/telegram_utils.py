from services.notifications.notifications import NotificationService, TelegramNotificationProperties
import os
from constantes.types import ENTORNOS

class TelegramUtils:
    async def send_msg(msgToSend,chat_id):
        environment = os.getenv("ENVIRONMENT")
        icon = None
        if ENTORNOS.PRO == environment:
            icon = "🟥"
            
        elif ENTORNOS.PRE == environment:
            icon = "🟨"
            
        elif ENTORNOS.DEV == environment:
            icon = "🟩"
        
        title = f"{icon}{icon} ** {environment} ** {icon}{icon}" 
        
        notificationService = NotificationService(properties=TelegramNotificationProperties(
            token=os.getenv("BOT_TOKEN"),
            chat_id=chat_id,
        ))
            
        await notificationService.send_notification(title,msgToSend)     