import MetaTrader5 as mt5
import os
from dotenv import load_dotenv, find_dotenv
from utils.utils import Utils
from event.events import OrderEvent,OrderType,SignalType
from store.orders_store import ParameterStore
from constantes.store_properties import STORE_PROPERTIES
from utils.estrategias_config import EstrategiasConfig
from constantes.config_comment import CONFIG_STRATEGY_PROPERTIES
from datetime import datetime
class MetaTrader5Broker():
    
    def __init__(self):
        # Buscar valores
        load_dotenv(find_dotenv())
        self.account_info = None
        self.symbol_info = None
        self.parameterStore = ParameterStore()
        
        # Inicializacion de la plataforma
        self._initialize_platform()
        
        #Esta activado el trading algoritmico
        self._check_algo_trading_enabled()
        
        #Añadimos los simbolos 
        #self._add_symbols_to_marketwatch(symbol_list)
        
        #Informacion por consola
        self._set_account_info()
        self.print_account_info()
        self.estrategiasConfig = EstrategiasConfig()
        
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
        
    def setSymbolInfo(self,symbol):
        self.symbol_info = mt5.symbol_info(symbol)
        
    def getSymbolInfo(self): return self.symbol_info
    
    def getReport(self):
        # Definir rango de fechas para buscar historial de órdenes
        fecha_inicio = datetime(2024, 1, 1)
        fecha_fin = datetime.now()

        # Obtener historial de órdenes
        deals = mt5.history_deals_get(fecha_inicio, fecha_fin)

        # Verificar si se recuperaron órdenes
        if deals is None:
            print("No se recuperaron órdenes:", mt5.last_error())
        elif len(deals) == 0:
            print("No hay órdenes en el periodo seleccionado")
        else:
            print(f"Se recuperaron {len(deals)} órdenes:")
            listado = []
            for deal in deals:
                dt = datetime.fromtimestamp(deal.time)
                fecha = dt.strftime('%Y-%m-%d')
                hora = dt.strftime('%H:%M:%S')
                print(f"Ticket: {deal.ticket}, Símbolo: {deal.symbol},Comentario: {deal.comment} Tipo: {deal.type}, "
                    f"Volumen: {deal.volume}, Precio: {deal.price}, Beneficio: {deal.profit:.2f}, Fecha: {fecha}")
                deal_dict = {
                    "ticket": deal.ticket,
                    "comment": deal.comment,
                    "symbol": deal.symbol,
                    "type": deal.type,
                    "volume": deal.volume,
                    "price": deal.price,
                    "profit": deal.profit,
                    "fecha": fecha,
                    "hora": hora
                }
                if deal_dict["comment"] != "Initial account balance":
                    listado.append(deal_dict)
            return listado

        
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
            if self.getSymbolInfo() is None:
                print(f"{Utils.dateprint()} - No se ha podido añadir el símbolo {symbol} al MarketWatch: {mt5.last_error()}")
                continue
            
            if not self.getSymbolInfo().visible:
                if not mt5.symbol_select(symbol, True):
                    print(f"No se ha podido añadir el símbolo {symbol} al MarketWatch: {mt5.last_error()}")
                else:
                    print(f"Símbolo {symbol} se ha añadido con éxito al MarketWatch!")
            else:
                print(f"El símbolo {symbol} ya estaba en el MarketWatch.")
    
    def _set_account_info(self) -> None:
        # Recuperar un objeto de tipo AccountInfo
        self.account_info = mt5.account_info()._asdict()
        
    def print_account_info(self) -> None:
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
                       
    def calc_lotes(self,sl,entry,numTP,risk):
        tamanio_contrato = None
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

        symbol_info = self.getSymbolInfo()
        tamanio_contrato = symbol_info.trade_contract_size
        # Cálculo del volumen
        riesgo_dinero = balance * risk/numTP  # Riesgo en dinero
        diferencia_precio = abs(entry - sl)  # Diferencia de precio (Stop Loss - Entrada)
        volumen = riesgo_dinero / (diferencia_precio * tamanio_contrato)  # Cálculo del volumen
        
        # Ajustar el volumen según los pasos permitidos por el broker
        volumen_ajustado =  self.ajuste_volumen_step(volumen,self.getSymbolInfo())
        
        return volumen_ajustado
    
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
            entry_price = self.getSymbolInfo().ask
        else:
            entry_price = self.getSymbolInfo().bid

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
            self.save_in_log(market_order_request)
        else:
            #Mandaremos un mensaje de error
            print(f"{Utils.dateprint()} - Ha habido un error al ejecutar la Market Order {order_event.signal} para {order_event.symbol}: {result.comment}")

    def _check_execution_status(self, order_result) -> bool:
        if order_result.retcode == mt5.TRADE_RETCODE_DONE:
            # todo ha ido bien
            return True
        elif order_result.retcode == mt5.TRADE_RETCODE_DONE_PARTIAL:
            return True
        else:
            return False
        
    def mover_stop_loss_be_by_symbol(self, newPrice = None, strategiaName = None, symbol = None):
        # Obtener las posiciones activas
        positions = mt5.positions_get()

        if positions is None or len(positions) == 0:
            print("No hay posiciones activas")
            return
        
        #filtrar las posiciones con ese comentario
        if strategiaName is not None:
            positions = [pos for pos in positions if strategiaName in pos.comment]
            
        if symbol is not None:
            positions = [pos for pos in positions if strategiaName in pos.symbol]
        
        # Buscar la posición que deseas modificar
        for position in positions:
            self.mover_stop_loss_be_by_position(position,newPrice)

    def mover_stop_loss_be_by_position(self, position, newPrice = None):
        # Crear el dict para la modificación
        newSl = newPrice if newPrice != None else position.price_open
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": position.symbol,
            "position": position.ticket,
            "price": position.price_open,  # Precio de apertura (no lo modificamos)
            "sl": newSl,  # El nuevo Stop Loss
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
                                                    
    def close_partial(self, symbol, nombre_estrategia,partial):
        # Obtener las posiciones activas
        positions = mt5.positions_get()
        
        if positions is None or len(positions) == 0:
            print("No hay posiciones activas")
            return
        
        #Buscar en la stored los id_orden para un symbol y una strategia
        item_order = self.parameterStore.get_first_from_list(STORE_PROPERTIES.ORDERS_OPEN_PENDINGS_LIST.value, lambda item: item.get("symbol") == symbol and item.get("nombreStrategy") == nombre_estrategia)
        # Buscar la posición que deseas modificar
        
        if(item_order == None): return
        print("item_order",item_order)
        for position in positions:
            if str(item_order["id_order"]) in position.comment.lower():
                nuevo_vol = position.volume*partial/100
                
                symbol_info= self.getSymbolInfo()
                nuevo_vol = self.ajuste_volumen_step(nuevo_vol,symbol_info=symbol_info)
                
                # Crear el dict para la modificación
                close_request = {
                    'action': mt5.TRADE_ACTION_DEAL,
                    'position': position.ticket,
                    'symbol': position.symbol,
                    'volume': nuevo_vol,
                    'price': self.getSymbolInfo().bid,
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
    
    def close_pending(self, symbol, nombre_estrategia):
    # Obtener las órdenes pendientes
        orders = mt5.orders_get()
        if orders is None or len(orders) == 0:
            print("No hay órdenes pendientes")
            return
        
        # Buscar la orden que deseas eliminar
        for order in orders:
            if symbol.lower() == order.symbol.lower() and nombre_estrategia.lower() in order.comment.lower():
              self.close_pending_by_order(order)
        
    def close_pending_by_order(self, order):
        # Crear el dict para eliminar la orden
        cancel_request = {
            'action': mt5.TRADE_ACTION_REMOVE,
            'order': order.ticket,
            'symbol': order.symbol,
            'comment': order.comment
        }

        # Enviar la solicitud para eliminar la orden
        result = mt5.order_send(cancel_request)

        if self._check_execution_status(result):
            print(f"{Utils.dateprint()} - Orden pendiente con ticket {order.ticket} en {order.symbol} ha sido eliminada correctamente")
        else:
            print(f"{Utils.dateprint()} - Error al eliminar la orden pendiente {order.ticket} en {order.symbol}: {result.comment}")

    def getBalanceCash(self):
        return self.account_info['balance']
    
    def setComment(self,nombreStrategy,id_order,num):
        return f"{nombreStrategy}_{id_order}_TP{num}"
    
    def test_strategy(self, symbol, nombreStrategy):
        tick = mt5.symbol_info_tick(symbol)
        if(tick == None):
            print("tick en mt5 class is None",tick)
            return
        current_ask = tick.ask
        current_bid = tick.bid
        
        orden_data = {
            "date":Utils.dateprint(),
            "symbol": symbol,
            "current_ask": current_ask,
            "current_bid": current_bid,
            "nombreStrategy": nombreStrategy
        }
        self.parameterStore.add_to_list(STORE_PROPERTIES.TEST_LIST.value, orden_data)
        
    def save_in_log(self, log):
        pass
    
    def handle_order(self, valores, symbol, tpList, nombreStrategy,id_order,entry_prices_distribution):
        #Cierra ordenes anteriores con mismo comentario
        close_open_in_new = self.estrategiasConfig.get(nombreStrategy,CONFIG_STRATEGY_PROPERTIES.CLOSE_OPENS_IN_NEW)
        close_pendings_in_new = self.estrategiasConfig.get(nombreStrategy,CONFIG_STRATEGY_PROPERTIES.CLOSE_PENDIGNS_IN_NEW)
        if(close_open_in_new): self.close_partial(symbol,nombre_estrategia=nombreStrategy,partial=100)
        if(close_pendings_in_new): self.close_pending(symbol,nombre_estrategia=nombreStrategy)
        
        risk = self.estrategiasConfig.get(nombreStrategy,CONFIG_STRATEGY_PROPERTIES.RISK)
        
        self.parameterStore.remove_from_list(STORE_PROPERTIES.ORDERS_OPEN_PENDINGS_LIST.value, lambda item: item.get("symbol") == symbol and item.get("nombreStrategy") == nombreStrategy)
        
        has_range = valores["rango_inferior"] is not None and valores["rango_superior"] is not None
        num_tps = len(tpList)
        is_long = valores["isLong"]
        is_short = valores["isShort"]
        stop_loss = valores["SL"]

        def enviar_ordenes_market(lotes, signal_type,entry_price):
            for i, tp in enumerate(tpList, start=1):
                comment = self.setComment(nombreStrategy=nombreStrategy,id_order=id_order,num=i)
                order = OrderEvent(
                    symbol=symbol,
                    volume=lotes,
                    signal=signal_type,
                    sl=stop_loss,
                    tp=valores.get(f"TP{i}", tp),
                    target_order=OrderType.MARKET,
                    comment=comment,
                )
                self.execute_order(order)
                print(f"✅ ORDER - TP{i}:", order)
                orden_data = {
                    "id_order":id_order,
                    "symbol": symbol,
                    "lotes":lotes,
                    "comentario": comment,
                    "entry_price": entry_price,
                    "tp_index": i,
                    "nombreStrategy": nombreStrategy,
                    }
                self.parameterStore.add_to_list(STORE_PROPERTIES.ORDERS_OPEN_PENDINGS_LIST.value, orden_data)

        tick = mt5.symbol_info_tick(symbol)
        if(tick == None):
            print("tick en mt5 class is None",tick)
            return
        current_ask = tick.ask
        current_bid = tick.bid
        
        if not has_range:
            entry_price_calc = current_ask if is_long else current_bid
            lotes = self.calc_lotes(sl=stop_loss, entry=entry_price_calc, risk=risk, numTP=num_tps)
            signal_type = SignalType.BUY if is_long else SignalType.SELL
            enviar_ordenes_market(lotes, signal_type,entry_price_calc)
            return

        # Tiene rango: asegurar que rango_inferior < rango_superior
        rango_inferior = min(valores["rango_inferior"], valores["rango_superior"])
        rango_superior = max(valores["rango_inferior"], valores["rango_superior"])
        
        # Entrar al mercado si el precio está dentro del rango
        signal_type = SignalType.BUY if is_long else SignalType.SELL

        if is_long and rango_inferior <= current_ask <= rango_superior:
            lotes = self.calc_lotes(sl=stop_loss, entry=current_ask, risk=risk, numTP=num_tps)
            enviar_ordenes_market(lotes, signal_type,current_ask)
            return

        if is_short and rango_inferior <= current_bid <= rango_superior:
            lotes = self.calc_lotes(sl=stop_loss, entry=current_bid, risk=risk, numTP=num_tps)
            enviar_ordenes_market(lotes, signal_type,current_bid)
            return

        # Si no está en el rango, dejar orden pendiente
        self.handle_order_pending(
            symbol=symbol,
            risk=risk,
            sl=stop_loss,
            entry_prices_distribution=entry_prices_distribution,
            tpList=tpList,
            isLong=is_long,
            isShort=is_short,
            tick_symbol=tick,
            nombreStrategy=nombreStrategy,
            id_order=id_order
        )
        
            # === ENVÍO DE ÓRDENES PENDIENTES ===
    def send_pending_order(self,symbol,order_type, entry_price, sl_price, tp_price, lot,comment,i,nombreStrategy,id_order):
        request = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": symbol,
            "volume": lot,
            "type": order_type,
            "price": entry_price,
            "sl": sl_price,
            "tp": tp_price,
            "deviation": 10,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_RETURN,
            "comment": comment
        }
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"❌ Error: {result.comment} enviada: {entry_price}, lote: {lot}, SL: {sl_price}, TP: {tp_price}")
        else:
            print(f"✅ {order_type} enviada: {entry_price}, lote: {lot}, SL: {sl_price}, TP: {tp_price}")
            orden_data = {
                "id_order":id_order,
                "symbol": symbol,
                "lotes":lot,
                "comentario": comment,
                "entry_price": entry_price,
                "tp_index": i,
                "nombreStrategy": nombreStrategy,
                }
            self.parameterStore.add_to_list(STORE_PROPERTIES.ORDERS_OPEN_PENDINGS_LIST.value, orden_data)
            self.save_in_log(orden_data)
            
    def get_positions_open(self):
        # Obtener posiciones abiertas
        positions = mt5.positions_get()
        if positions is None:
            print("No se pudieron obtener las posiciones:", mt5.last_error())
        else:
            return positions
                
    def get_orders_pendings(self):
        # Obtener órdenes pendientes
        orders = mt5.orders_get()
        if orders is None:
            print("No se pudieron obtener las órdenes pendientes:", mt5.last_error())
        else:
            return orders
    
    
    def handle_order_pending(self,symbol,risk,sl,tpList,entry_prices_distribution,isShort,isLong,tick_symbol,nombreStrategy,id_order):
        RISK_PERCENT = risk  # % de riesgo por operación
        STOP_LOSS_PRICE = sl # SL absoluto (ej. 2000)
        take_profits = tpList  # TPs por entrada

        print("entry_prices",entry_prices_distribution)
        
        # === ENVIAR TODAS LAS ÓRDENES ===
        tick = tick_symbol
        current_ask = tick.ask
        current_bid = tick.bid

        for entry_distribution in entry_prices_distribution:
            #todo sera una lista en la que vendra el x del lote y el precio de entrada
            ENTRY = entry_distribution['entry']
            DISTRIBUTION_LOTE = entry_distribution['distribution']
            for i, tp in enumerate(take_profits, start=1):
                comment = self.setComment(nombreStrategy=nombreStrategy,id_order=id_order,num=i)
                lot = self.calc_lotes(entry=ENTRY, sl=STOP_LOSS_PRICE,risk=RISK_PERCENT / (len(entry_prices_distribution)),numTP=len(take_profits))
                lot_with_distribution = lot*DISTRIBUTION_LOTE

                # === BUY PENDINGS ===
                if ENTRY > current_ask and isLong:
                    self.send_pending_order(symbol,mt5.ORDER_TYPE_BUY_STOP, ENTRY, STOP_LOSS_PRICE, tp, lot_with_distribution,comment,i,nombreStrategy,id_order)
                elif ENTRY < current_ask and isLong:
                    self.send_pending_order(symbol,mt5.ORDER_TYPE_BUY_LIMIT, ENTRY, STOP_LOSS_PRICE, tp, lot_with_distribution,comment,i,nombreStrategy,id_order)

                # === SELL PENDINGS ===
                if ENTRY < current_bid and isShort:
                    self.send_pending_order(symbol,mt5.ORDER_TYPE_SELL_STOP, ENTRY, STOP_LOSS_PRICE, tp, lot_with_distribution,comment,i,nombreStrategy,id_order)
                elif ENTRY > current_bid and isShort:
                    self.send_pending_order(symbol,mt5.ORDER_TYPE_SELL_LIMIT, ENTRY, STOP_LOSS_PRICE, tp, lot_with_distribution,comment,i,nombreStrategy,id_order)
       


