from constantes.store_properties import STORE_PROPERTIES
from handlers.vlad_signals import VladSignal
from handlers.sinpers_gold import SnipersGold
from handlers.johan_gold import JohanGoldSignal
from handlers.nasdaq100 import Nas100Signal
from handlers.ptjg_gold import PtjgGold
from handlers.turbo import TurboSignal
from constantes.config_comment import CONFIG_NAME_STRATEGY
from constantes.canals import CANALS
from constantes.grupos import GROUPS
from constantes.types import ENTORNOS
from utils.exports import Export
from utils.telegram_utils import TelegramUtils
import os
import re
from constantes.chat_properties import CHAT_PROPERTIES

class HandlerChat:
    def __init__(self,param_store,brokerInstance):
        self.param_store = param_store
        self.brokerInstance = brokerInstance
        self.token_bot = os.getenv("BOT_TOKEN")
        self.environment = os.getenv("ENVIRONMENT")
        self.isOnEntorno = True
    
    async def handle(self,chat_id,mensaje):
        id_order = self.setIdOrder()
        
        chat_id_int = int(chat_id)
        
        if chat_id_int == int(CANALS.SNIPERS_GOLD_VIP.value) and self.isOnEntorno:
            snipersGold = SnipersGold(self.brokerInstance, f"{CONFIG_NAME_STRATEGY.SNIPERS_GOLD_VIP.value}",id_order)
            #snipersGold.handle(mensaje)
            if self.environment == ENTORNOS.PRO : await self.sendToOtherEnvironment(chat_id_int,mensaje)
            
            return

        if chat_id_int == int(CANALS.SNIPERS_GOLD_PUBLIC.value) and self.isOnEntorno:
            snipersGold = SnipersGold(self.brokerInstance, f"{CONFIG_NAME_STRATEGY.SNIPERS_GOLD_PUB.value}",id_order)
            #snipersGold.handle(mensaje)
            
            if self.environment == ENTORNOS.PRO : await self.sendToOtherEnvironment(chat_id_int,mensaje)
            
            return
            
        if chat_id_int == int(CANALS.PTJG_GOLD_PUBLIC.value) and self.isOnEntorno:
            ptjgGold = PtjgGold(self.brokerInstance, f"{CONFIG_NAME_STRATEGY.PTJG_GOLD_PUB.value}",id_order)
            #ptjgGold.handle(mensaje)
            if self.environment == ENTORNOS.PRO : await self.sendToOtherEnvironment(chat_id_int,mensaje)
            return

        if chat_id_int == int(CANALS.SIGNAL_VLAD.value ) and self.isOnEntorno:
            vladSignal = VladSignal(self.brokerInstance,f"{CONFIG_NAME_STRATEGY.VLAD.value}",id_order)
            #vladSignal.handle(mensaje)
            if self.environment == ENTORNOS.PRO : await self.sendToOtherEnvironment(chat_id_int,mensaje)
            return
            
        if chat_id_int == int(CANALS.NASDAQ_100.value) and self.isOnEntorno:
            nasPro = Nas100Signal(self.brokerInstance,f"{CONFIG_NAME_STRATEGY.NASDAQ_100.value}",id_order)
            #nasPro.handle(mensaje)
            if self.environment == ENTORNOS.PRO: await self.sendToOtherEnvironment(chat_id_int,mensaje)
            return
            
        if chat_id_int == int(CANALS.JOHAN_GOLD.value) and self.isOnEntorno:
            johan = JohanGoldSignal(self.brokerInstance, f"{CONFIG_NAME_STRATEGY.JOAN_GOLD_VIP.value}",id_order)
            johan.handle(mensaje)
            if self.environment == ENTORNOS.PRO : await self.sendToOtherEnvironment(chat_id_int,mensaje)
            
            return
        
        if chat_id_int == int(CANALS.TURBO_PUBLIC.value) and self.isOnEntorno:
            turbo = TurboSignal(self.brokerInstance,f"{CONFIG_NAME_STRATEGY.TURBO_PUBLIC.value}",id_order)
            #turbo.handle(mensaje)
            if self.environment == ENTORNOS.PRO : await self.sendToOtherEnvironment(chat_id_int,mensaje)
            
            return
        
        await self.handleReHandler(mensaje=mensaje,chat_id=chat_id_int)
        await self.handleEntornosChat(msg=mensaje,chat_id=chat_id_int,id_order=id_order)
        
    async def handleReHandler(self,mensaje,chat_id):
        if chat_id == int(GROUPS.DEV.value) or chat_id == int(GROUPS.PRE.value):
            match = re.search(r"chat_(.*?)_msg_(.*)", mensaje, re.DOTALL)
            if match:
                chat_id_extraido = match.group(1)
                msg = match.group(2)
                await self.handle(chat_id_extraido,msg)
        
        
    async def sendToOtherEnvironment(self,chat_id,msg):
        text = f'chat_{chat_id}_msg_{msg}'
        #Envia a PRE
        await TelegramUtils.send_msg(msgToSend=text,chat_id=GROUPS.PRE.value)
        #Envia a develop
        await TelegramUtils.send_msg(msgToSend=text,chat_id=GROUPS.DEV.value)
        
            
    def setIdOrder(self):
        id_order = self.param_store.get(STORE_PROPERTIES.ID_ORDER.value)
        id_order = id_order + 1
        if(id_order == 1000) : id_order = 1
        self.param_store.set(STORE_PROPERTIES.ID_ORDER.value, id_order)
        return id_order
    
    def handleExportReport(self):
        report = self.brokerInstance.getReport()
        exports = Export()
        exports.export_as_cvs(path=os.getenv("PATH_COMPARTIDA"),listado=report,nombre_fichero='report_balance.csv')
        
    def handleOnOff(self,isOn):
        self.isOnEntorno = isOn
            
    async def handleEntornosChat(self,msg,chat_id,id_order):
        if (chat_id == int(GROUPS.DEV.value)and self.environment == ENTORNOS.DEV.value ):
            await self.healthCheck(msg=msg,entorno=ENTORNOS.DEV.value)
            
            if (CHAT_PROPERTIES.TEST in msg.lower() and self.isOnEntorno):
                '''
                CODIGO DE PRUEBAS
                '''
                johan = JohanGoldSignal(self.brokerInstance, f"{CONFIG_NAME_STRATEGY.JOAN_GOLD_VIP.value}",id_order)
                johan.handle(msg)
                
                '''
                FIN
                '''
                
        if (chat_id == int(GROUPS.PRE)and self.environment == ENTORNOS.PRE.value):
            await self.healthCheck(msg=msg,entorno=ENTORNOS.PRE.value)
        
        if (chat_id == int(GROUPS.PRO)and self.environment == ENTORNOS.PRO.value):
            await self.healthCheck(msg=msg,entorno=ENTORNOS.PRO.value)
            
        if(msg.lower() == CHAT_PROPERTIES.REPORT): self.handleExportReport()
        
        if(msg.lower() == CHAT_PROPERTIES.ON_ENTORNO): self.handleOnOff(True)
        
        if(msg.lower() == CHAT_PROPERTIES.OFF_ENTORNO): self.handleOnOff(False)
        
        if(msg.lower() == CHAT_PROPERTIES.HELP): await self.helpChat()
        
    async def helpChat(self):
        
        chat_id=None
        if ENTORNOS.PRO == self.environment:
            chat_id = GROUPS.PRO.value
            
        elif ENTORNOS.PRE == self.environment:
            chat_id = GROUPS.PRE.value
            
        elif ENTORNOS.DEV == self.environment:
            chat_id = GROUPS.DEV.value
        msg = '1) hi => Chequear salud\n2) test TextoDeLaSeñal => Usa la prueba escrita en el entorno\n3) on entorno => Encender entorno\n4) off entorno => Apagar entorno'
        await TelegramUtils.send_msg(msgToSend=msg,chat_id=chat_id)
        
    async def healthCheck(self,msg,entorno):
        if msg.lower() != CHAT_PROPERTIES.HI : return
        
        chat_id=None
        if ENTORNOS.PRO == entorno:
            chat_id = GROUPS.PRO.value
            
        elif ENTORNOS.PRE == entorno:
            chat_id = GROUPS.PRE.value
            
        elif ENTORNOS.DEV == entorno:
            chat_id = GROUPS.DEV.value
            
        msg=  "Robin a su servicio, entorno:"  + str(self.isOnEntorno)
        await TelegramUtils.send_msg(msgToSend=msg,chat_id=chat_id)
        
    def setChatsToWatch(self):
        entorno = os.getenv("ENVIRONMENT")
        
        
        chats_DEV = [  
            int(GROUPS.PRO),
            int(GROUPS.DEV)
            ]

        chats_PRE = [  
            int(GROUPS.PRE),
            int(GROUPS.DEV)
            ]

        chats_PRO = [  
            int(CANALS.BIT_LOBO),
            int(CANALS.SIGNAL_VLAD),
            int(CANALS.CRIPTO_SENIALES),
            int(CANALS.SNIPERS_GOLD_VIP),
            int(CANALS.SNIPERS_GOLD_PUBLIC),
            int(CANALS.TURBO_PUBLIC),
            int(CANALS.NASDAQ_100),
            ]

        if entorno == ENTORNOS.DEV:
            return chats_DEV
        elif entorno == ENTORNOS.PRE:
            return chats_PRE
        elif entorno == ENTORNOS.PRO:
            return chats_PRO
        else:
            print(f"⚠️ Entorno no reconocido: {entorno}")
            return []