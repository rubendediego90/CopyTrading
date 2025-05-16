from constantes.store_properties import STORE_PROPERTIES
from services.notifications.notifications import NotificationService, TelegramNotificationProperties
from handlers.vlad_signals import VladSignal
from handlers.sinpers_gold import SnipersGold
from handlers.us30_pro import US30ProSignal
from handlers.ptjg_gold import PtjgGold
from constantes.config_comment import CONFIG_NAME_STRATEGY
import time
from constantes.canals import CANALS
from constantes.grupos import GROUPS
import os


class HandlerChat:
    def __init__(self,param_store,brokerInstance):
        self.param_store = param_store
        self.brokerInstance = brokerInstance
        self.token_bot = os.getenv("BOT_TOKEN")
        
    
    async def handle(self,chat_id,mensaje):
            #Setear id_order
        id_order = self.param_store.get(STORE_PROPERTIES.ID_ORDER.value)
        id_order = id_order + 1
        if(id_order == 1000) : id_order = 1
        self.param_store.set(STORE_PROPERTIES.ID_ORDER.value, id_order)

        if chat_id == int(GROUPS.TEST):
            snipersGold = SnipersGold(self.brokerInstance, f"{CONFIG_NAME_STRATEGY.SNIPERS_GOLD_VIP.value}",id_order)
            snipersGold.handle(mensaje)
            
            if(mensaje == "payaso") : 
                notificationService = NotificationService(properties=TelegramNotificationProperties(
                    token=self.token_bot,
                    chat_id=GROUPS.TEST,
                ))
                await notificationService.send_notification("title", f"y tu eres un gay {mensaje}")

        if chat_id == int(CANALS.SNIPERS_GOLD_VIP):
            snipersGold = SnipersGold(self.brokerInstance, f"{CONFIG_NAME_STRATEGY.SNIPERS_GOLD_VIP.value}",id_order)
            snipersGold.handle(mensaje)

        if chat_id == int(CANALS.SNIPERS_GOLD_PUBLIC):
            snipersGold = SnipersGold(self.brokerInstance, f"{CONFIG_NAME_STRATEGY.SNIPERS_GOLD_PUB.value}",id_order)
            snipersGold.handle(mensaje)
            
        if chat_id == int(CANALS.PTJG_GOLD_PUBLIC):
            ptjgGold = PtjgGold(self.brokerInstance, f"{CONFIG_NAME_STRATEGY.PTJG_GOLD_PUB.value}",id_order)
            ptjgGold.handle(mensaje)

        if chat_id == int(CANALS.SIGNAL_VLAD):
            vladSignal = VladSignal(self.brokerInstance,f"{CONFIG_NAME_STRATEGY.VLAD.value}",id_order)
            vladSignal.handle(mensaje)
            
        if chat_id == int(CANALS.US30_PRO):
            nasPro = US30ProSignal(self.brokerInstance,f"{CONFIG_NAME_STRATEGY.US30_PRO.value}",id_order)
            nasPro.handle(mensaje)