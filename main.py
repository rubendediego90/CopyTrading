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
import re
from collections import defaultdict

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
    int(CANALS.US30_PRO),
    int(CANALS.SNIPERS_GOLD_PUBLIC),
    int(GROUPS.TEST),
]

param_store = ParameterStore()
brokerInstance = MetaTrader5Broker(param_store)
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
        
        nasPro = US30ProSignal(brokerInstance,f"{CONFIG_NAME_STRATEGY.US30_PRO.value}",id_order)
        nasPro.handle(mensaje)

        '''
        #SnipersGold(brokerInstance, f"{CONFIG_NAME_STRATEGY.SNIPERS_GOLD_VIP.value}{CONFIG_COMMENT.AUTO_SL.value}").handle(mensaje, last_cash_balance)
        signalVlad = VladSignal(brokerInstance,f"{CONFIG_NAME_STRATEGY.VLAD.value}",id_order)
        signalVlad.handle(mensaje)
        signalVlad = None
        '''
        
        if(mensaje == "print test") : 
            print("**TEST LOG**")
            log = param_store.get(STORE_PROPERTIES.TEST_LIST.value)
            print(log)
            return
        if(mensaje == "print") : 
            print("**TEST LOG**")
            log = param_store.get(STORE_PROPERTIES.LOG_LIST.value)
            print(log)
            return
        if(mensaje == "remove log") : 
            print("**TEST LOG**")
            log = param_store.remove_from_list(STORE_PROPERTIES.LOG_LIST.value)
            print(log)
            return
        #PtjgGold(brokerInstance,f"{CONFIG_NAME_STRATEGY.PTJG_GOLD_PUB.value}{CONFIG_COMMENT.AUTO_SL.value}").handle(mensaje, last_cash_balance)
        #SnipersGold(brokerInstance, "SNIPERS_GOLD_VIP").handle(mensaje, last_cash_balance)

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
        
def filtrar_tps_sin_tp1(comentarios):
    grupos = defaultdict(list)

    for comentario in comentarios:
        match = re.match(r'(.*)_TP(\d+)', comentario)
        if match:
            prefix, tp_num = match.groups()
            grupos[prefix].append((int(tp_num), comentario))

    resultado = []

    for prefix, tps in grupos.items():
        tp_nums = [tp[0] for tp in tps]
        if 1 not in tp_nums:
            ordenados = sorted(tps)
            resultado.extend([tp[1] for tp in ordenados])

    return resultado

def obtener_comentarios(items):
    return [item['comentario'] for item in items if 'comentario' in item]

# ✅ HILO SECUNDARIO – imprime mensaje cada 5 segundos
def bucle_mensajes():
    can_open_time = 0
    can_opem_time_default = 60
    move_sl_auto_time = 0
    move_sl_auto_time_default = 15
    global can_open_global 
    while True:
        move_sl_auto_time = move_sl_auto_time + 1
        
        #chequa si se puede abrir una nueva operacion
        #todo borrar
        if(can_open_time == can_opem_time_default):
            current_cash_balance = brokerInstance.getBalanceCash()
            ftmo_utils = FTMOUtils()
            
            #setea fecha y valor, se hace una vez al dia
            ftmo_utils.set_balance_data(current_cash_balance)
            
            #evalua si se puede abrir orden
            can_open_global = ftmo_utils.can_open_new_position(current_cash_balance)
            ftmo_utils = None
            can_open_time = 0
            print("🟢 se puede abrir la operacion?")
            
            
        if(move_sl_auto_time == move_sl_auto_time_default):
            #traer lista de ordenes abiertas y pendientes
            orders_pendings = brokerInstance.get_orders_pendings()
            positions_opens = brokerInstance.get_positions_open()
            
            comentario_pendings_orders = [order.comment for order in orders_pendings]
            comentario_positions_opens = [order.comment for order in positions_opens]
            comentarios_positions_and_orders = comentario_pendings_orders + comentario_positions_opens
            
            comentarios_sin_tp_1 = filtrar_tps_sin_tp1(comentario_positions_opens)
            comentarios_sin_tp_1_sin_duplicados = list(dict.fromkeys(comentarios_sin_tp_1))
            
            #comentarios a mover sl y a cerrar pendientes
            for comentario in comentarios_sin_tp_1_sin_duplicados:
                positionsFiltered = [pos for pos in positions_opens if pos.comment == comentario]

                for position in positionsFiltered:
                    brokerInstance.mover_stop_loss_be_by_position(position)

                #quitamos los 3 ultimos caracteres TP1 o TP2 o TPn
                orders_pendings_Filtered = [order for order in orders_pendings if comentario[:-3] in order.comment]

                for order_pending in orders_pendings_Filtered:
                    brokerInstance.close_pending_by_order(order_pending)
                    
            #clean store sincronizar store y ordenes y posiciones
            itemsStored = param_store.get(STORE_PROPERTIES.ORDERS_OPEN_PENDINGS_LIST.value)
            comentarios_stored = obtener_comentarios(itemsStored)
            
            #compara las dos listas, y busca los comentarios que no estan
            comentarios_obsoletos = [item for item in comentarios_stored if item not in comentarios_positions_and_orders]
            
            #borra comentarios obsoletos
            param_store.remove_from_list(
                STORE_PROPERTIES.ORDERS_OPEN_PENDINGS_LIST.value,
                lambda item: item.get("comentario") in comentarios_obsoletos
            )
            move_sl_auto_time = 0
            
        time.sleep(1)

# 🔁 Lanzamos el hilo antes de bloquear el hilo principal con el cliente
threading.Thread(target=bucle_mensajes, daemon=True).start()

print("📡 Escuchando grupos y canales...")
client.run_until_disconnected()