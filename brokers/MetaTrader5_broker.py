import MetaTrader5 as mt5
import os
from dotenv import load_dotenv, find_dotenv
from utils.utils import Utils

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
        
        
    def disconnect(self) -> None:
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
        
        return self.ajuste_volumen_step(volumen,symbol_info)
    
    def ajuste_volumen_step(self,volumen,symbol_info):
        volume_step = symbol_info.volume_step  
        volumeFinal = round(volumen / volume_step) * volume_step
        if(volumeFinal < symbol_info.volume_min): return symbol_info.volume_min
        return volumeFinal
    
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
        
        entry_price = 0.0
        if order_event.signal == "BUY":
            entry_price = mt5.symbol_info(order_event.symbol).ask
        else:
            entry_price = mt5.symbol_info(order_event.symbol).bid

        # Creación del market order request
        market_order_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": order_event.symbol,
            "volume": order_event.volume,
            'price': entry_price,
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
        
    def mover_stop_loss_be(self, symbol, comentario_buscado):
        # Obtener las posiciones activas
        positions = mt5.positions_get()

        if positions is None or len(positions) == 0:
            print("No hay posiciones activas")
            return
        
        # Buscar la posición que deseas modificar
        for position in positions:
            if position.symbol == symbol and comentario_buscado.lower() in position.comment.lower():
                # Calcular el nuevo valor de Stop Loss (por ejemplo, en el punto de breakeven)
                # Este es solo un ejemplo, puede que necesites ajustarlo según tu estrategia
                
                # Crear el dict para la modificación
                request = {
                    "action": mt5.TRADE_ACTION_SLTP,
                    "symbol": symbol,
                    "position": position.ticket,
                    "price": position.price_open,  # Precio de apertura (no lo modificamos)
                    "sl": position.price_open,  # El nuevo Stop Loss
                    "tp": position.tp,  # Precio de Take Profit (no lo modificamos)
                    "volume": position.volume,  # Volumen de la orden
                    "type": position.type,  # Tipo de la orden (compra/venta)
                    "deviation": 0,  # Desviación permitida en puntos
                    "comment": position.comment
                }

                # Enviar la solicitud de modificación de orden
                result = mt5.order_send(request)

        if self._check_execution_status(result):
            print(f"{Utils.dateprint()} - Posición con ticket {position.ticket} en {position.symbol} se ha movido el STOP Loss a BE correctamente")
        else:
            # Mandaremos un mensaje de error
            print(f"{Utils.dateprint()} - Ha habido un error al mover el STOP Loss a BE la posición {position.ticket} en {position.symbol}: {result.comment}")
                            
    def close_partial(self, symbol, comentario_buscado,partial):
        # Obtener las posiciones activas
        positions = mt5.positions_get()
        
        print("")

        if positions is None or len(positions) == 0:
            print("No hay posiciones activas")
            return
        
        # Buscar la posición que deseas modificar
        for position in positions:
            if position.symbol == symbol and comentario_buscado.lower() in position.comment.lower():
                nuevo_vol = position.volume*partial/100
                
                symbol_info= mt5.symbol_info(position.symbol)
                nuevo_vol = self.ajuste_volumen_step(nuevo_vol,symbol_info=symbol_info)
                
                # Crear el dict para la modificación
                close_request = {
                    'action': mt5.TRADE_ACTION_DEAL,
                    'position': position.ticket,
                    'symbol': position.symbol,
                    'volume': nuevo_vol,
                    'price': mt5.symbol_info(position.symbol).bid,
                    'type': mt5.ORDER_TYPE_BUY if position.type == mt5.ORDER_TYPE_SELL else mt5.ORDER_TYPE_SELL,
                    'type_filling': mt5.ORDER_FILLING_FOK,
                    'comment':position.comment
                }

                # Mandamos el close_request
                result = mt5.order_send(close_request)

                if self._check_execution_status(result):
                    print(f"{Utils.dateprint()} - Posición con ticket {position.ticket} en {position.symbol} y volumen {position.volume} se ha tomado parcial correctamente")
                else:
                    # Mandaremos un mensaje de error
                    print(f"{Utils.dateprint()} - Ha habido un error al cerrar cerrar parcial de la posición {position.ticket} en {position.symbol} con volumen {nuevo_vol}: {result.comment}")
    
    def pesimist_balance_positions_open_and_pending(self):
        # Obtener órdenes pendientes
        pending_orders = mt5.orders_get()
        # Obtener posiciones abiertas
        open_positions = mt5.positions_get()

        # Función para calcular pérdida potencial
        def calc_stop_loss_loss(volume, open_price, sl_price, symbol, order_type):
            contract_size = mt5.symbol_info(symbol).trade_contract_size
            if order_type in [mt5.ORDER_TYPE_BUY, mt5.ORDER_TYPE_BUY_LIMIT, mt5.ORDER_TYPE_BUY_STOP]:
                loss_per_point = (sl_price - open_price)
            else:
                loss_per_point = (open_price - sl_price)
            return volume * contract_size * loss_per_point

        # Calcular pérdida potencial de órdenes pendientes
        loss_pending = 0
        if pending_orders:
            for order in pending_orders:
                if order.sl != 0.0:
                    loss = calc_stop_loss_loss(order.volume_current, order.price_open, order.sl, order.symbol, order.type)
                    loss_pending += loss

        # Calcular pérdida potencial de posiciones abiertas
        loss_open = 0
        if open_positions:
            for pos in open_positions:
                if pos.sl != 0.0:
                    loss = calc_stop_loss_loss(pos.volume, pos.price_open, pos.sl, pos.symbol, pos.type)
                    loss_open += loss
        total = loss_pending + loss_open
        #print(f"Pérdida potencial por órdenes pendientes yendo a SL: {loss_pending:.2f}")
        #print(f"Pérdida potencial por posiciones abiertas yendo a SL: {loss_open:.2f}")
        #print(f"Pérdida total potencial si todo va a SL: {(loss_pending + loss_open):.2f}")
        
        return total
        
    def getBalanceCash(self):
        return self.account_info['balance']
    
    def can_open_new_position(self,last_cash_balance,percentage_max_down):
        #Ver si llegamos a perder la cuenta
        balance_open_pendings = self.pesimist_balance_positions_open_and_pending()

        balance_postions_closed = self.getBalanceCash() - last_cash_balance + balance_open_pendings
        ammount_max_to_loss = last_cash_balance * percentage_max_down / 100
        
                # se pone negativo porque el balance malo saldra negativo en la suma
        can_open = ammount_max_to_loss > (-balance_postions_closed)
        
        print("BALANCE - PENDINGS",balance_open_pendings)
        print("BALANCE - YESTERDAY",last_cash_balance)
        print("BALANCE - TODAY",self.getBalanceCash())
        print("BALANCE - Ammount max to loss",ammount_max_to_loss)
        print("BALANCE CAN OPEN - ",can_open)

        return can_open
        


