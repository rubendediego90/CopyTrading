from telethon.tl.types import Channel

class CanalsYGroups:
    def __init__(self, client):
        self.client = client
        
    def getCanals(self):
        dialogs = self.client.get_dialogs()

        print("\n📢 Canales donde estás suscrito:\n")

        for dialog in dialogs:
            entity = dialog.entity
            if isinstance(entity, Channel) and entity.megagroup is False:
                print(f"🏷️  Nombre: {entity.title}")
                print(f"🆔 ID: {entity.id}")
                print(f"🔗 Username: @{entity.username}" if entity.username else "🔒 Canal privado")
                print("-" * 40)
    
    async def getGroups(self):
        chats = await self.client.get_dialogs()

        groups = [chat for chat in chats if chat.is_group]

        if groups:
            print("Grupos a los que estás unido:")
            for group in groups:
                print(f"Nombre: {group.name}, ID: {group.id}")
        else:
            print("No estás unido a ningún grupo.")
            
    async def obtener_ultimos_mensajes(self,canal_used):
        canal = await self.client.get_entity(canal_used)

        mensajes = await self.client.get_messages(canal, limit=5)

        print("\n📝 Últimos 5 mensajes en el canal:\n")
        for msg in mensajes:
            print(f"🔹 {msg.sender_id}: {msg.text}")
            print("-" * 40)
            
    async def msgLog(self,event):
        try:
            chat_id = event.chat_id  # 👈 ID del canal o grupo
            mensaje = event.raw_text
            fecha = event.date.strftime('%Y-%m-%d %H:%M:%S')

            # Obtener nombre del autor si es posible
            try:
                sender = await event.get_sender()
                autor = f"{sender.first_name or ''} {sender.last_name or ''}".strip()
                if sender.username:
                    autor += f" (@{sender.username})"
            except Exception:
                autor = "Anónimo o canal"

            # Obtener nombre del canal/grupo
            try:
                chat = await event.get_chat()
                chat_title = chat.title or 'Sin título'
            except Exception:
                chat_title = 'Desconocido'

            print("📥 Nuevo mensaje recibido:")
            print(f"📆 Fecha: {fecha}")
            print(f"👤 Autor: {autor}")
            print(f"💬 Mensaje: {mensaje}")
            print(f"🏷️ Canal/Grupo: {chat_title}")
            print(f"🆔 ID del chat: {chat_id}")
            print()

        except Exception as e:
            print(f"⚠️ Error procesando el mensaje: {e}")
        

