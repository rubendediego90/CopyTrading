from constantes.store_properties import STORE_PROPERTIES
from services.notifications.notifications import NotificationService, TelegramNotificationProperties
from handlers.vlad_signals import VladSignal
from handlers.sinpers_gold import SnipersGold
from handlers.us30_pro import US30ProSignal
from handlers.ptjg_gold import PtjgGold
from handlers.turbo import TurboSignal
from constantes.config_comment import CONFIG_NAME_STRATEGY
from constantes.canals import CANALS
from constantes.grupos import GROUPS
from constantes.types import ENTORNOS
import os


class HandlerChat:
    def __init__(self,param_store,brokerInstance):
        self.param_store = param_store
        self.brokerInstance = brokerInstance
        self.token_bot = os.getenv("BOT_TOKEN")
        self.environment = os.getenv("ENVIRONMENT")
        
    
    async def handle(self,chat_id,mensaje):
        id_order = self.setIdOrder()
        

        if chat_id == int(CANALS.SNIPERS_GOLD_VIP):
            snipersGold = SnipersGold(self.brokerInstance, f"{CONFIG_NAME_STRATEGY.SNIPERS_GOLD_VIP.value}",id_order)
            snipersGold.handle(mensaje)
            return

        if chat_id == int(CANALS.SNIPERS_GOLD_PUBLIC):
            snipersGold = SnipersGold(self.brokerInstance, f"{CONFIG_NAME_STRATEGY.SNIPERS_GOLD_PUB.value}",id_order)
            snipersGold.handle(mensaje)
            return
            
        if chat_id == int(CANALS.PTJG_GOLD_PUBLIC):
            ptjgGold = PtjgGold(self.brokerInstance, f"{CONFIG_NAME_STRATEGY.PTJG_GOLD_PUB.value}",id_order)
            ptjgGold.handle(mensaje)
            return

        if chat_id == int(CANALS.SIGNAL_VLAD):
            vladSignal = VladSignal(self.brokerInstance,f"{CONFIG_NAME_STRATEGY.VLAD.value}",id_order)
            vladSignal.handle(mensaje)
            return
            
        if chat_id == int(CANALS.US30_PRO):
            nasPro = US30ProSignal(self.brokerInstance,f"{CONFIG_NAME_STRATEGY.US30_PRO.value}",id_order)
            nasPro.handle(mensaje)
            return
            
        if chat_id == int(CANALS.TURBO_PUBLIC):
            turbo = TurboSignal(self.brokerInstance,f"{CONFIG_NAME_STRATEGY.TURBO_PUBLIC.value}",id_order)
            turbo.handle(mensaje)
            return
            
        await self.handleEntornosChat(msg=mensaje,chat_id=chat_id,id_order=id_order)
        
            
    def setIdOrder(self):
        id_order = self.param_store.get(STORE_PROPERTIES.ID_ORDER.value)
        id_order = id_order + 1
        if(id_order == 1000) : id_order = 1
        self.param_store.set(STORE_PROPERTIES.ID_ORDER.value, id_order)
        return id_order
            
    async def handleEntornosChat(self,msg,chat_id,id_order):
        if (chat_id == int(GROUPS.DEV)and self.environment == ENTORNOS.DEV.value):
            await self.healthCheck(msg=msg,entorno=ENTORNOS.DEV.value)
            
            turbo = TurboSignal(self.brokerInstance,f"{CONFIG_NAME_STRATEGY.TURBO_PUBLIC.value}",id_order)
            turbo.handle(msg)
                
        if (chat_id == int(GROUPS.PRE)and self.environment == ENTORNOS.PRE.value):
            await self.healthCheck(msg=msg,entorno=ENTORNOS.PRE.value)
        
        if (chat_id == int(GROUPS.PRO)and self.environment == ENTORNOS.PRO.value):
            await self.healthCheck(msg=msg,entorno=ENTORNOS.PRO.value)

    async def healthCheck(self,msg,entorno):
        if msg.lower() != "hi" : return
        icon = None
        chat_id=None
        if ENTORNOS.PRO == entorno:
            icon = "🟥"
            chat_id = GROUPS.PRO
            
        elif ENTORNOS.PRE == entorno:
            icon = "🟨"
            chat_id = GROUPS.PRE
            
        elif ENTORNOS.DEV == entorno:
            icon = "🟩"
            chat_id = GROUPS.DEV
            
        notificationService = NotificationService(properties=TelegramNotificationProperties(
            token=self.token_bot,
            chat_id=chat_id,
        ))
            
        await notificationService.send_notification(f"{icon}{icon} ** {entorno} ** {icon}{icon}", "Robin a su servicio")        
            