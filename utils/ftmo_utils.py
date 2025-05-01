from store.orders_store import ParameterStore
import datetime
from constantes.store_properties import STORE_PROPERTIES

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
        today = datetime.date.today()
        if(fecha_balance == None or fecha_balance < today):
            # Guardar la fecha actual
            self.param_store.save_date(STORE_PROPERTIES.FECHA_BALANCE.value)
            # Guardar balance
            self.param_store.save_number(STORE_PROPERTIES.CASH_BALANCE.value, current_balance)
            

