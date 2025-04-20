import MetaTrader5 as mt5
import os
from dotenv import load_dotenv, find_dotenv
from utils.utils import Utils
import datetime
from event.events import OrderEvent

class MetaTrader5Broker():
    
    def __init__(self):
        # Buscar valores
        load_dotenv(find_dotenv())
        self.account_info = None
        
        # Inicializacion de la plataforma
        self._initialize_platform()
        
        #Esta activado el trading algoritmico
        self._check_algo_trading_enabled()
        
        #Añadimos los simbolos 
        #self._add_symbols_to_marketwatch(symbol_list)
        
        #Informacion por consola
        self._print_account_info()
        
        #self._get_symbols_in_marketwatch()
        
        
    def disconnect() -> None:
        # Desconexcion de mt5 
        mt5.shutdown()
    
    def _initialize_platform(self) -> None:
        init = mt5.initialize(
            path=os.getenv("MT5_PATH"),
            login=int(os.getenv("MT5_LOGIN")),
            password=os.getenv("MT5_PASSWORD"),
            server=os.getenv("MT5_SERVER"),
            timeout=int(os.getenv("MT5_TIMEOUT")),
            portable=eval(os.getenv("MT5_PORTABLE"))
        )
        
        if init:
            current_account_info = mt5.account_info()
            print("------------------------------------------------------------------")
            print(f"Login: {current_account_info.login} \tserver: {current_account_info.server}")
        else:
            print("failed to connect at account #{}, error code: {}".format(os.getenv("MT5_LOGIN"), mt5.last_error()))
            
    def _check_algo_trading_enabled(self) -> None:
        # comprobar que el trading algoritmico esta activado
        if not mt5.terminal_info().trade_allowed:
            raise Exception("El trading algorítmico está desactivado")
        
    #TODO mensaje telegram añadir en cada operacion si es real o no
    def _is_real_account(self) -> None:
        #Comprueba el tipo de cuenta
        account_info = mt5.account_info().trade_mode
        
        if account_info == mt5.ACCOUNT_TRADE_MODE_DEMO:
            print("Cuenta tipo demo")
            
        elif account_info == mt5.ACCOUNT_TRADE_MODE_REAL:
            print("Cuenta tipo demo")
                
    def _add_symbols_to_marketwatch(self, symbols: list) -> None:
        
        # 1) Comprobamos si el símbolo ya está visible en el MW
        # 2) Si no lo está, lo añadiremos

        for symbol in symbols:
            if mt5.symbol_info(symbol) is None:
                print(f"{Utils.dateprint()} - No se ha podido añadir el símbolo {symbol} al MarketWatch: {mt5.last_error()}")
                continue
            
            if not mt5.symbol_info(symbol).visible:
                if not mt5.symbol_select(symbol, True):
                    print(f"No se ha podido añadir el símbolo {symbol} al MarketWatch: {mt5.last_error()}")
                else:
                    print(f"Símbolo {symbol} se ha añadido con éxito al MarketWatch!")
            else:
                print(f"El símbolo {symbol} ya estaba en el MarketWatch.")
    
    def _print_account_info(self) -> None:
        # Recuperar un objeto de tipo AccountInfo
        self.account_info = mt5.account_info()._asdict()

        print(f"+------------ Información de la cuenta ------------")
        print(f"| - ID de cuenta: {self.account_info['login']}")
        print(f"| - Nombre trader: {self.account_info['name']}")
        print(f"| - Broker: {self.account_info['company']}")
        print(f"| - Servidor: {self.account_info['server']}")
        print(f"| - Apalancamiento: {self.account_info['leverage']}")
        print(f"| - Divisa de la cuenta: {self.account_info['currency']}")
        print(f"| - Balance de la cuenta: {self.account_info['balance']}")
        print(f"+--------------------------------------------------")
        
    def _get_symbols_in_marketwatch(self):
        symbols = mt5.symbols_get()
        if symbols is None:
            print(f"No se pudo obtener la lista de símbolos: {mt5.last_error()}")
            return []

        visible_symbols = [s.name for s in symbols if s.visible]
        print(f"Símbolos visibles en el Market Watch ({len(visible_symbols)}):")
        for sym in visible_symbols:
            print(f" - {sym}")
        
        return visible_symbols
    
    def get_open_positions_by_symbol(self,symbol):
        # Obtener todas las órdenes abiertas
        posiciones_abiertas = mt5.positions_get()
        
        print("posiciones_abiertas",posiciones_abiertas)

        if posiciones_abiertas is None or len(posiciones_abiertas) == 0:
            print("No hay órdenes abiertas.")
        else:
            # Filtrar órdenes por símbolo
            ordenes_filtradas = [orden for orden in posiciones_abiertas if orden.symbol == symbol.upper()]
            
            if not ordenes_filtradas:
                print(f"No hay órdenes abiertas para el símbolo {symbol}")
            else:
                print(f"Órdenes abiertas para {symbol.upper()}:")
                for orden in ordenes_filtradas:
                    print(f"Ticket: {orden.ticket}")
                    print(f"Tipo: {orden.type}")
                    print(f"Precio: {orden.price_open}")
                    
    def calc_lotes(self,sl,entry,symbol):
        tamanio_contrato = None
        risk = 0.005 #
        account_info = mt5.account_info()._asdict()
        balance = account_info['balance']
        #volumen = (balance * riesgo%) / (abs(precio_entrada - stop_loss) * tamaño_contrato)
        '''
        Ejemplo concreto (BTCUSD):
        Balance = 10,000 USD
        Riesgo = 0.5% → 50 USD
        Entrada = 65,000
        Stop Loss = 64,500
        Contrato = 1 BTC (tamaño_contrato = 1)
        text
        Copiar código
        volumen = (10,000 * 0.005) / (|65,000 - 64,500| * 1)
                = 50 / 500
                = 0.1 contratos
        Entonces deberías abrir una posición de 0.1 contratos (BTC) para que, si se alcanza el SL, pierdas exactamente el 0.5% de tu cuenta.
        '''
        
        # Obtener la información del símbolo
        symbol_info = mt5.symbol_info(symbol)

        if symbol_info is not None:
            tamanio_contrato = symbol_info.trade_contract_size
        
        # Cálculo del volumen
        
        riesgo_dinero = balance * risk  # Riesgo en dinero
        diferencia_precio = abs(entry - sl)  # Diferencia de precio (Stop Loss - Entrada)
        volumen = riesgo_dinero / (diferencia_precio * tamanio_contrato)  # Cálculo del volumen
        
        volume_step = symbol_info.volume_step  
        volumeFinal = round(volumen / volume_step) * volume_step
        if(volumeFinal < symbol_info.volume_min): return symbol_info.volume_min
        return volumeFinal
    
    def obtener_historial_operaciones(self):
        '''
        # Definir la fecha de hoy
        fecha_hoy = datetime.datetime.now().date()
        
        # Convertir la fecha a timestamp UNIX para el rango de hoy (hora UTC)
        desde_timestamp = datetime.datetime(fecha_hoy.year, fecha_hoy.month - 1, fecha_hoy.day)
        hasta_timestamp = datetime.datetime(fecha_hoy.year, fecha_hoy.month +1 , fecha_hoy.day)
        
        # Convertir las fechas a timestamps (segundos desde la época UNIX)
        #desde = int(desde_timestamp.timestamp())
        #hasta = int(hasta_timestamp.timestamp())
        
        print("desde_timestamp**********", desde_timestamp)
        print("hasta_timestamp**********", hasta_timestamp)
        
        # Intentar obtener las transacciones del día
        historial = mt5.history_orders_get(from_time=desde_timestamp, to_time=hasta_timestamp)
        
        if historial is None or len(historial) == 0:
            print("No se encontraron transacciones cerradas hoy.")
            return []
        
        # Si hay historial, mostrar la información relevante
        print(f"Se encontraron {len(historial)} transacciones cerradas.")
        for deal in historial:
            print(f"Ticket: {deal.ticket}, Símbolo: {deal.symbol}, Tipo: {deal.type}, Precio de apertura: {deal.price_open}, Precio de cierre: {deal.price_close}, Beneficio: {deal.profit}, Tiempo: {datetime.datetime.fromtimestamp(deal.time)}")
        
        return historial
        '''
        # Obtener las órdenes históricas, por ejemplo, del 1 de enero de 2023 al 31 de diciembre de 2023
        from_date = datetime.datetime(2023, 1, 1)
        to_date = datetime.datetime(2023, 12, 31)

        # Obtener las transacciones históricas (history_orders_get)
        history_orders = mt5.history_orders_get(from_date, to_date)

        # Verificar si se obtuvieron datos
        if history_orders is None:
            print("No se pudieron obtener las órdenes históricas.")
        else:
            # Mostrar algunas de las órdenes históricas
            for order in history_orders:
                print(f"ID: {order.ticket}, Símbolo: {order.symbol}, Volumen: {order.volume}, Precio: {order.price_open}, Fecha de apertura: {order.time}")
        return []


    # Calcular las ganancias y pérdidas del día
    def calcular_perdida_diaria(self,historial):
        perdida_total = 0.0
        for operacion in historial:
            # Sumar las ganancias y pérdidas de las operaciones cerradas
            perdida_total += operacion.profit
        return perdida_total

    # Función principal
    def calcular_perdida(self):
        # Obtener el historial de operaciones de hoy
        historial = self.obtener_historial_operaciones()
        
        if len(historial) == 0:
            print("No hubo operaciones hoy.")
            return
        
        # Calcular la pérdida total
        perdida_total = self.calcular_perdida_diaria(historial)
        
        # Mostrar el resultado
        if perdida_total < 0:
            print(f"Has perdido un total de {abs(perdida_total):.2f} USD hoy.")
        else:
            print(f"Has ganado un total de {perdida_total:.2f} USD hoy.")
            
    def execute_order(self, order_event: OrderEvent) -> None:

        # Evaluamos el tipo de orden que se quiere ejecutar, y llamamos al método adecuado
        if order_event.target_order == "MARKET":
            # Llamamos al método que ejecuta órdenes a mercado
            self._execute_market_order(order_event)
        else:
            # Llamamos al método que coloque órdenes pendientes
            self._send_pending_order(order_event)

    def _execute_market_order(self, order_event: OrderEvent) -> None:
        # Comprobamos si la orden es de compra o de venta
        if order_event.signal == "BUY":
            # Orden de compra
            order_type = mt5.ORDER_TYPE_BUY
        elif order_event.signal == "SELL":
            # Orden de venta
            order_type = mt5.ORDER_TYPE_SELL
        else:
            raise Exception(f"ORD EXEC: La señal {order_event.signal} no es válida")

        # Creación del market order request
        market_order_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": order_event.symbol,
            "volume": order_event.volume,
            'price': mt5.symbol_info(order_event.symbol).bid,
            "sl": order_event.sl,
            "tp": order_event.tp,
            "type": order_type,
            "deviation": 0,
            "comment":order_event.comment,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }

        # Mandamos el trade request para ser ejecutado
        result = mt5.order_send(market_order_request)

        # Verificar el resultado de la ejecución de la orden
        if self._check_execution_status(result):
            print(f"{Utils.dateprint()} - Market Order {order_event.signal} para {order_event.symbol} de {order_event.volume} lotes ejecutada correctamente")
        else:
            #Mandaremos un mensaje de error
            print(f"{Utils.dateprint()} - Ha habido un error al ejecutar la Market Order {order_event.signal} para {order_event.symbol}: {result.comment}")

    def _send_pending_order(self, order_event: OrderEvent) -> None:
        # Comprobar si es de tipo STOP o de tipo LIMITE
        if order_event.target_order == "STOP":
            order_type = mt5.ORDER_TYPE_BUY_STOP if order_event.signal == "BUY" else mt5.ORDER_TYPE_SELL_STOP
        elif order_event.target_order == "LIMIT":
            order_type = mt5.ORDER_TYPE_BUY_LIMIT if order_event.signal == "BUY" else mt5.ORDER_TYPE_SELL_LIMIT
        else:
            raise Exception(f"ORD EXEC: La orden pendiente objetivo {order_event.target_order} no es válida")
        
        # Creación de la pending order request
        pending_order_request = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": order_event.symbol,
            "volume": order_event.volume,
            "sl": order_event.sl,
            "tp": order_event.tp,
            "type": order_type,
            "price": order_event.target_price,
            "deviation": 0,
            "comment": order_event.comment,
            "type_filling": mt5.ORDER_FILLING_FOK,
            "type_time": mt5.ORDER_TIME_GTC
        }

        # Mandamos el trade request para colocar la orden pendiente
        result = mt5.order_send(pending_order_request)
        
        
    def _check_execution_status(self, order_result) -> bool:
        if order_result.retcode == mt5.TRADE_RETCODE_DONE:
            # todo ha ido bien
            return True
        elif order_result.retcode == mt5.TRADE_RETCODE_DONE_PARTIAL:
            return True
        else:
            return False

