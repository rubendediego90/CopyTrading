import os
import threading
import time
import datetime
from telethon.sync import TelegramClient
from telethon import events
from constantes.grupos import GROUPS
from constantes.canals import CANALS
from utils.groups_canals import CanalsYGroups
from handlers.vlad_signals import VladSignal
from handlers.sinpers_gold import SnipersGold
from handlers.ptjg_gold import PtjgGold
from brokers.MetaTrader5_broker import MetaTrader5Broker
from utils.utils import Utils

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

last_day_balance = datetime.date(1990, 4, 21)
last_cash_balance = 0.0
brokerInstance = MetaTrader5Broker()

# ✅ Manejo de mensajes
@client.on(events.NewMessage(chats=chats_a_escuchar))
async def manejador_mensajes(event):
    global last_day_balance, last_cash_balance
    today = datetime.date.today()

    if last_day_balance == 0.0 or last_day_balance <= today:
        last_day_balance = today
        last_cash_balance = brokerInstance.getBalanceCash()
        print(f"{Utils.dateprint()} - Reseteo fecha y guarda balance", last_cash_balance)

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
        #SnipersGold(brokerInstance, "SNIPERS_GOLD_PUB").handle(mensaje, last_cash_balance)
        #VladSignal(brokerInstance).handle(mensaje, last_cash_balance)
        PtjgGold(brokerInstance,"PTJG_GOLD_PUB").handle(mensaje, last_cash_balance)
        #SnipersGold(brokerInstance, "SNIPERS_GOLD_VIP").handle(mensaje, last_cash_balance)

    if chat_id == int(CANALS.SNIPERS_GOLD_VIP):
        SnipersGold(brokerInstance, "SNIPERS_GOLD_VIP").handle(mensaje, last_cash_balance)

    if chat_id == int(CANALS.SNIPERS_GOLD_PUBLIC):
        SnipersGold(brokerInstance, "SNIPERS_GOLD_PUB").handle(mensaje, last_cash_balance)
        
    if chat_id == int(CANALS.PTJG_GOLD_PUBLIC):
        PtjgGold(brokerInstance, "PTJG_GOLD_PUB").handle(mensaje, last_cash_balance)

    if chat_id == int(CANALS.SIGNAL_VLAD):
        VladSignal(brokerInstance,"VLAD").handle(mensaje, last_cash_balance)

# ✅ HILO SECUNDARIO – imprime mensaje cada 5 segundos
def bucle_mensajes():
    while True:
        print("🟢 Mensaje enviado desde hilo secundario")
        time.sleep(30)

# 🔁 Lanzamos el hilo antes de bloquear el hilo principal con el cliente
threading.Thread(target=bucle_mensajes, daemon=True).start()

print("📡 Escuchando grupos y canales...")
client.run_until_disconnected()