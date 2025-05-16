from store.orders_store import ParameterStore
import datetime
from constantes.store_properties import STORE_PROPERTIES
import re
from collections import defaultdict
from brokers.MetaTrader5_broker import MetaTrader5Broker
FTMO_CONDITION_PERCENTAGE = 4

class FTMOUtils:
    def __init__(self):
        self.param_store = ParameterStore()
        
        pass
    
    def can_open_new_position(self,current_balance):
        cash_last_balance = self.param_store.get(STORE_PROPERTIES.CASH_BALANCE.value)
        if(cash_last_balance == None): cash_last_balance = 0.0
        orders = self.param_store.get(STORE_PROPERTIES.ORDERS_OPEN_PENDINGS_LIST.value)
        open_pendings_balance = 0.0
        if(orders != None):
            open_pendings_balance = sum(orden['perdida_estimada'] for orden in orders)
        
        balance_postions_closed = current_balance - cash_last_balance - open_pendings_balance
        ammount_max_to_loss = cash_last_balance * FTMO_CONDITION_PERCENTAGE / 100
        
        print(f"🔴 Pérdida total estimada: {open_pendings_balance:.2f}")
        print(f"🔴 Perdida maxima permitida: {ammount_max_to_loss:.2f}")
        print(f"🔴 Balance actual: {balance_postions_closed:.2f}")
        # se pone negativo porque el balance malo saldra negativo en la suma
        can_open = ammount_max_to_loss > (-balance_postions_closed)
        return can_open
        
        
    def set_balance_data(self,current_balance):
        #mirar la ficha de la store
        fecha_balance = self.param_store.get_date(STORE_PROPERTIES.FECHA_BALANCE.value)
        print("fecha y saved",fecha_balance)
        
        today = datetime.date.today()
        if(fecha_balance == None or fecha_balance < today):
            print("Seteo fecha y balance")
            # Guardar la fecha actual
            self.param_store.save_date(STORE_PROPERTIES.FECHA_BALANCE.value)
            # Guardar balance
            self.param_store.save_number(STORE_PROPERTIES.CASH_BALANCE.value, current_balance)
            
    def filtrar_tps_sin_tp1(self,comentarios):
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

    def obtener_comentarios(self,items):
        return [item['comentario'] for item in items if 'comentario' in item]
            
    async def auto_sl(self,brokerInstance:MetaTrader5Broker):
        #traer lista de ordenes abiertas y pendientes
        orders_pendings = brokerInstance.get_orders_pendings()
        positions_opens = brokerInstance.get_positions_open()
        
        comentario_pendings_orders = [order.comment for order in orders_pendings]
        comentario_positions_opens = [order.comment for order in positions_opens]
        comentarios_positions_and_orders = comentario_pendings_orders + comentario_positions_opens
        
        comentarios_sin_tp_1 = self.filtrar_tps_sin_tp1(comentario_positions_opens)
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
        itemsStored = self.param_store.get(STORE_PROPERTIES.ORDERS_OPEN_PENDINGS_LIST.value)
        comentarios_stored = self.obtener_comentarios(itemsStored)
        
        #compara las dos listas, y busca los comentarios que no estan
        comentarios_obsoletos = [item for item in comentarios_stored if item not in comentarios_positions_and_orders]
        
        #borra comentarios obsoletos
        self.param_store.remove_from_list(
            STORE_PROPERTIES.ORDERS_OPEN_PENDINGS_LIST.value,
            lambda item: item.get("comentario") in comentarios_obsoletos
        )
           
           
           
''''
 #chequa si se puede abrir una nueva operacion
        #todo borrar
        if(can_open_time == can_opem_time_default):
            current_cash_balance = brokerInstance.getBalanceCash()
            
            #setea fecha y valor, se hace una vez al dia
            ftmo_utils.set_balance_data(current_cash_balance)
            
            #evalua si se puede abrir orden
            can_open_global = ftmo_utils.can_open_new_position(current_cash_balance)
            ftmo_utils = None
            can_open_time = 0
            print("🟢 se puede abrir la operacion?")

''' 

