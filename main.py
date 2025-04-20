import os
from telethon.sync import TelegramClient
from telethon.tl.types import Channel
from telethon import TelegramClient, events
from datetime import datetime
from constantes.grupos import GROUPS
from constantes.canals import CANALS
from utils.groups_canals import CanalsYGroups
from handlers.vlad_signals import VladSignal
from brokers.MetaTrader5_broker import MetaTrader5Broker

a = os.getenv("MT5_PATH")

api_id = os.getenv("API_ID")    # tu api_id
api_hash = os.getenv("API_HASH")  # tu api_hash


canal_used = CANALS.SIGNAL_VLAD
group_used = GROUPS.RUPENS

# Creamos el cliente y arrancamos sesión
client = TelegramClient('SesionRuben', api_id, api_hash)
client.start()

canalsYGroups = CanalsYGroups(client)
canalsYGroups.getCanals()
client.loop.run_until_complete(canalsYGroups.getGroups())

chats_a_escuchar = [
    int(CANALS.BIT_LOBO),
    int(CANALS.SIGNAL_VLAD),
    int(CANALS.CRIPTO_SENIALES),
    int(GROUPS.TEST),
    #int(GROUPS.VLAD_DUDAS),
    #int(GROUPS.RUPENS),
]

connectMetaTrader = MetaTrader5Broker()

@client.on(events.NewMessage(chats=chats_a_escuchar))
async def manejador_mensajes(event):
    chat_id = event.chat_id  # 👈 ID del canal o grupo
    mensaje = event.raw_text
    await canalsYGroups.msgLog(event)
    #print("chat_id",chat_id)
    #print("canal vlad señales",int(CANALS.SIGNAL_VLAD))
    print("es lobo?",chat_id == int(CANALS.BIT_LOBO))
    print("es vlad?",chat_id == int(CANALS.SIGNAL_VLAD))
    print("es señales nuevo?",chat_id == int(CANALS.CRIPTO_SENIALES))
    print("es TEST?",chat_id == int(GROUPS.TEST))
    
    if chat_id == int(GROUPS.TEST):#CANALS.SIGNAL_VLAD: 
        vladSignal = VladSignal(connectMetaTrader)
        vladSignal.handle(mensaje)
    
    '''
    if chat_id == int(CANALS.SIGNAL_VLAD):#CANALS.SIGNAL_VLAD: 
        vladSignal = VladSignal(connectMetaTrader)
        vladSignal.handle(mensaje)
    '''
            

print("📡 Escuchando grupos y canales...")
client.run_until_disconnected()