import os
import threading
import time
from telethon.sync import TelegramClient
from telethon import events
from constantes.grupos import GROUPS
from constantes.canals import CANALS
from constantes.config_comment import CONFIG_NAME_STRATEGY
from utils.groups_canals import CanalsYGroups
from handlers.vlad_signals import VladSignal
from handlers.sinpers_gold import SnipersGold
from handlers.us30_pro import US30ProSignal
from handlers.ptjg_gold import PtjgGold
from brokers.MetaTrader5_broker import MetaTrader5Broker
from store.orders_store import ParameterStore
from utils.ftmo_utils import FTMOUtils
from constantes.store_properties import STORE_PROPERTIES

# ✅ Cargamos las variables de entorno
a = os.getenv("MT5_PATH")
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")

# ✅ Cliente de Telegram
client = TelegramClient('SesionRuben', api_id, api_hash)
client.start()

# ✅ Inicializamos grupos y canales
canalsYGroups = CanalsYGroups(client)
canalsYGroups.getCanals()
client.loop.run_until_complete(canalsYGroups.getGroups())

chats_a_escuchar = [
    int(CANALS.BIT_LOBO),
    int(CANALS.SIGNAL_VLAD),
    int(CANALS.CRIPTO_SENIALES),
    int(CANALS.SNIPERS_GOLD_VIP),
    #int(CANALS.PTJG_GOLD_PUBLIC),
    int(CANALS.US30_PRO),
    int(CANALS.SNIPERS_GOLD_PUBLIC),
    int(GROUPS.TEST),
]

param_store = ParameterStore()
brokerInstance = MetaTrader5Broker()
can_open_global = True

# ✅ Manejo de mensajes
@client.on(events.NewMessage(chats=chats_a_escuchar))
async def manejador_mensajes(event):
    global can_open_global 
    chat_id = event.chat_id
    mensaje = event.raw_text
    await canalsYGroups.msgLog(event)

    #validar que se pueden abrir nuevas ordenes
    if(can_open_global == False): return
    
    #Setear id_order
    id_order = param_store.get(STORE_PROPERTIES.ID_ORDER.value)
    id_order = id_order + 1
    if(id_order == 1000) : id_order = 1
    param_store.set(STORE_PROPERTIES.ID_ORDER.value, id_order)

    if chat_id == int(GROUPS.TEST):
        
        '''
        signalVlad = VladSignal(brokerInstance,f"{CONFIG_NAME_STRATEGY.VLAD.value}",id_order)
        signalVlad.handle(mensaje)
        signalVlad = None
        '''
        snipersGold = SnipersGold(brokerInstance, f"{CONFIG_NAME_STRATEGY.SNIPERS_GOLD_VIP.value}",id_order)
        snipersGold.handle(mensaje)
        '''
        
        nasPro = US30ProSignal(brokerInstance,f"{CONFIG_NAME_STRATEGY.US30_PRO.value}",id_order)
        nasPro.handle(mensaje)

        '''
        '''
        #SnipersGold(brokerInstance, f"{CONFIG_NAME_STRATEGY.SNIPERS_GOLD_VIP.value}{CONFIG_COMMENT.AUTO_SL.value}").handle(mensaje, last_cash_balance)
        signalVlad = VladSignal(brokerInstance,f"{CONFIG_NAME_STRATEGY.VLAD.value}",id_order)
        signalVlad.handle(mensaje)
        signalVlad = None
        '''
        
        if(mensaje == "print test") : 
            print("**TEST LIST LOG**")
            log = param_store.get(STORE_PROPERTIES.TEST_LIST.value)
            print(log)
            return

    if chat_id == int(CANALS.SNIPERS_GOLD_VIP):
        snipersGold = SnipersGold(brokerInstance, f"{CONFIG_NAME_STRATEGY.SNIPERS_GOLD_VIP.value}",id_order)
        snipersGold.handle(mensaje)

    if chat_id == int(CANALS.SNIPERS_GOLD_PUBLIC):
        snipersGold = SnipersGold(brokerInstance, f"{CONFIG_NAME_STRATEGY.SNIPERS_GOLD_PUB.value}",id_order)
        snipersGold.handle(mensaje)
        
    if chat_id == int(CANALS.PTJG_GOLD_PUBLIC):
        ptjgGold = PtjgGold(brokerInstance, f"{CONFIG_NAME_STRATEGY.PTJG_GOLD_PUB.value}",id_order)
        ptjgGold.handle(mensaje)

    if chat_id == int(CANALS.SIGNAL_VLAD):
        vladSignal = VladSignal(brokerInstance,f"{CONFIG_NAME_STRATEGY.VLAD.value}",id_order)
        vladSignal.handle(mensaje)
        
    if chat_id == int(CANALS.US30_PRO):
        nasPro = US30ProSignal(brokerInstance,f"{CONFIG_NAME_STRATEGY.US30_PRO.value}",id_order)
        nasPro.handle(mensaje)
        
# ✅ HILO SECUNDARIO – imprime mensaje cada 5 segundos
def bucle_mensajes():
    move_sl_auto_time = 0
    move_sl_auto_time_default = 15
    global can_open_global 
    ftmo_utils = FTMOUtils()
    while True:
        move_sl_auto_time = move_sl_auto_time + 1
        
        if(move_sl_auto_time == move_sl_auto_time_default):
            ftmo_utils.auto_sl(brokerInstance=brokerInstance)
            move_sl_auto_time = 0
            
        time.sleep(1)

# 🔁 Lanzamos el hilo antes de bloquear el hilo principal con el cliente
threading.Thread(target=bucle_mensajes, daemon=True).start()

print("📡 Escuchando grupos y canales...")
client.run_until_disconnected()