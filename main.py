import os
import threading
import asyncio
from telethon.sync import TelegramClient
from telethon import events
from constantes.grupos import GROUPS
from constantes.canals import CANALS
from utils.groups_canals import CanalsYGroups
from brokers.MetaTrader5_broker import MetaTrader5Broker
from store.orders_store import ParameterStore
from utils.ftmo_utils import FTMOUtils
from handlers.handler_chat import HandlerChat
from dotenv import load_dotenv

load_dotenv()

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
    int(CANALS.US30_PRO),
    int(CANALS.SNIPERS_GOLD_PUBLIC),
    int(CANALS.TURBO_PUBLIC),
    int(GROUPS.PRE),
    int(GROUPS.PRO),
    int(GROUPS.DEV),
]

param_store = ParameterStore()
brokerInstance = MetaTrader5Broker()
handlerChat = HandlerChat(param_store,brokerInstance)
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
    
    await handlerChat.handle(chat_id,mensaje)


# ✅ HILO SECUNDARIO – imprime mensaje cada 5 segundos
def bucle_mensajes():
    move_sl_auto_time = 0
    move_sl_auto_time_default = 15
    global can_open_global 
    ftmo_utils = FTMOUtils()

    # Crear un ciclo de eventos para el hilo secundario
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Hacer que la función sea asincrónica para poder usar asyncio
    async def auto_sl_loop():
        nonlocal move_sl_auto_time
        while True:
            move_sl_auto_time += 1
            if move_sl_auto_time == move_sl_auto_time_default:
                await ftmo_utils.auto_sl(brokerInstance=brokerInstance)
                move_sl_auto_time = 0
            await asyncio.sleep(1)

    # Ejecutar el loop asincrónico en el hilo secundario
    loop.create_task(auto_sl_loop())
    loop.run_forever()

# Lanza el hilo secundario que ejecuta la función
threading.Thread(target=bucle_mensajes, daemon=True).start()

# Ejecutar el cliente de Telegram
print("📡 Escuchando grupos y canales...")
client.run_until_disconnected()