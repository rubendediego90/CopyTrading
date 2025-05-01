import os
import threading
import time
from telethon.sync import TelegramClient
from telethon import events
from constantes.grupos import GROUPS
from constantes.canals import CANALS
from constantes.config_comment import CONFIG_COMMENT,CONFIG_NAME_STRATEGY
from utils.groups_canals import CanalsYGroups
from handlers.vlad_signals import VladSignal
from handlers.sinpers_gold import SnipersGold
from handlers.ptjg_gold import PtjgGold
from brokers.MetaTrader5_broker import MetaTrader5Broker
from store.orders_store import ParameterStore
from utils.ftmo_utils import FTMOUtils

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
    int(CANALS.PTJG_GOLD_PUBLIC),
    #int(CANALS.SNIPERS_GOLD_PUBLIC),
    int(GROUPS.TEST),
]

param_store = ParameterStore()
brokerInstance = MetaTrader5Broker(param_store)
can_open_global = True
#param_store.clear_list("MiEstrategia")

# ✅ Manejo de mensajes
@client.on(events.NewMessage(chats=chats_a_escuchar))
async def manejador_mensajes(event):

    chat_id = event.chat_id
    mensaje = event.raw_text
    await canalsYGroups.msgLog(event)

    print("es lobo?", chat_id == int(CANALS.BIT_LOBO))
    print("es vlad?", chat_id == int(CANALS.SIGNAL_VLAD))
    print("es señales nuevo?", chat_id == int(CANALS.CRIPTO_SENIALES))
    print("esgold vip?", chat_id == int(CANALS.SNIPERS_GOLD_VIP))
    print("esgold public?", chat_id == int(CANALS.SNIPERS_GOLD_PUBLIC))
    print("es ptjg public?", chat_id == int(CANALS.PTJG_GOLD_PUBLIC))
    print("es TEST?", chat_id == int(GROUPS.TEST))

    if chat_id == int(GROUPS.TEST):
        #SnipersGold(brokerInstance, f"{CONFIG_NAME_STRATEGY.SNIPERS_GOLD_VIP.value}{CONFIG_COMMENT.AUTO_SL.value}").handle(mensaje, last_cash_balance)
        VladSignal(brokerInstance,f"{CONFIG_NAME_STRATEGY.VLAD.value}{CONFIG_COMMENT.AUTO_SL.value}").handle(mensaje)
        #PtjgGold(brokerInstance,f"{CONFIG_NAME_STRATEGY.PTJG_GOLD_PUB.value}{CONFIG_COMMENT.AUTO_SL.value}").handle(mensaje, last_cash_balance)
        #SnipersGold(brokerInstance, "SNIPERS_GOLD_VIP").handle(mensaje, last_cash_balance)

    if chat_id == int(CANALS.SNIPERS_GOLD_VIP):
        SnipersGold(brokerInstance, f"{CONFIG_NAME_STRATEGY.SNIPERS_GOLD_VIP.value}{CONFIG_COMMENT.AUTO_SL.value}").handle(mensaje)

    if chat_id == int(CANALS.SNIPERS_GOLD_PUBLIC):
        SnipersGold(brokerInstance, f"{CONFIG_NAME_STRATEGY.SNIPERS_GOLD_PUB.value}{CONFIG_COMMENT.AUTO_SL.value}").handle(mensaje)
        
    if chat_id == int(CANALS.PTJG_GOLD_PUBLIC):
        PtjgGold(brokerInstance, f"{CONFIG_NAME_STRATEGY.PTJG_GOLD_PUB.value}{CONFIG_COMMENT.AUTO_SL.value}").handle(mensaje)

    if chat_id == int(CANALS.SIGNAL_VLAD):
        VladSignal(brokerInstance,f"{CONFIG_NAME_STRATEGY.VLAD.value}{CONFIG_COMMENT.AUTO_SL.value}").handle(mensaje)

# ✅ HILO SECUNDARIO – imprime mensaje cada 5 segundos
def bucle_mensajes():
    can_open_time = 0
    can_opem_time_default = 60
    move_sl_auto_time = 0
    move_sl_auto_time_default = 15
    global can_open_global 
    while True:
        can_open_time = can_open_time + 1
        move_sl_auto_time = move_sl_auto_time + 1

        
        #chequa si se puede abrir una nueva operacion
        if(can_open_time == can_opem_time_default):
            current_cash_balance = brokerInstance.getBalanceCash()
            ftmo_utils = FTMOUtils()
            
            #setea fecha y valor, se hace una vez al dia
            ftmo_utils.set_balance_data(current_cash_balance)
            
            #evalua si se puede abrir orden
            can_open_global = ftmo_utils.can_open_new_position(current_cash_balance)
            can_open_time = 0
            print("🟢 se puede abrir la operacion?")
            
            
        if(move_sl_auto_time == move_sl_auto_time_default):
            #auto sl
            print("🟢 muevo stop loss?")
            move_sl_auto_time = 0
            

        '''
        ordenes = param_store.get(STORE_PROPERTIES.ORDERS_OPEN_PENDINGS_LIST.value, [])
        for orden in ordenes:
            print("print store",orden)
        '''
        time.sleep(1)

# 🔁 Lanzamos el hilo antes de bloquear el hilo principal con el cliente
threading.Thread(target=bucle_mensajes, daemon=True).start()

print("📡 Escuchando grupos y canales...")
client.run_until_disconnected()