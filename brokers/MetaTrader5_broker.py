import MetaTrader5 as mt5
import os
from dotenv import load_dotenv, find_dotenv
from datetime import datetime
from event.events import OrderEvent, OrderType, SignalType

class MetaTrader5Broker:
    
    def __init__(self):
        load_dotenv(find_dotenv())
        self.account_info = None
        self.symbol_info = None

        self._initialize_platform()
        self._check_algo_trading_enabled()
        self._set_account_info()

    def _initialize_platform(self):
        init = mt5.initialize(
            path=os.getenv("MT5_PATH"),
            login=int(os.getenv("MT5_LOGIN")),
            password=os.getenv("MT5_PASSWORD"),
            server=os.getenv("MT5_SERVER"),
            timeout=int(os.getenv("MT5_TIMEOUT")),
            portable=eval(os.getenv("MT5_PORTABLE"))
        )
        if not init:
            raise Exception(f"Fallo al conectar: {mt5.last_error()}")

    def _check_algo_trading_enabled(self):
        if not mt5.terminal_info().trade_allowed:
            raise Exception("El trading algorítmico está desactivado")

    def _set_account_info(self):
        self.account_info = mt5.account_info()._asdict()

    def getBalanceCash(self):
        return self.account_info['balance']

    def setSymbolInfo(self, symbol):
        self.symbol_info = mt5.symbol_info(symbol)

    def getSymbolInfo(self):
        return self.symbol_info

    def calc_lotes(self, sl, entry, numTP, risk):
        balance = self.account_info['balance']
        contract_size = self.symbol_info.trade_contract_size
        risk_amount = balance * risk / numTP
        price_diff = abs(entry - sl)
        volume = risk_amount / (price_diff * contract_size)
        return self.ajuste_volumen_step(volume, self.symbol_info)

    def ajuste_volumen_step(self, volumen, symbol_info):
        step = symbol_info.volume_step
        adjusted = round(volumen / step) * step
        return max(adjusted, symbol_info.volume_min)

    def execute_order(self, order_event: OrderEvent):
        if order_event.target_order == OrderType.MARKET:
            self._execute_market_order(order_event)

    def _execute_market_order(self, order_event: OrderEvent):
        order_type = mt5.ORDER_TYPE_BUY if order_event.signal == SignalType.BUY else mt5.ORDER_TYPE_SELL
        price = self.symbol_info.ask if order_event.signal == SignalType.BUY else self.symbol_info.bid

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": order_event.symbol,
            "volume": order_event.volume,
            "sl": order_event.sl,
            "tp": order_event.tp,
            "type": order_type,
            "deviation": 0,
            "comment": order_event.comment,
            "type_filling": mt5.ORDER_FILLING_FOK,
            "magic": order_event.magic
        }

        result = mt5.order_send(request)
        if self._check_execution_status(result):
            print(f"✅ Orden Market ejecutada: {order_event.symbol} {order_event.signal} vol: {order_event.volume}")
        else:
            print(f"❌ Error al ejecutar orden: {result.comment}")

    def _check_execution_status(self, result) -> bool:
        return result.retcode in [mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_DONE_PARTIAL]

    def mover_stop_loss_be_by_symbol(self, newPrice=None, strategiaName=None, symbol=None):
        positions = mt5.positions_get()
        if not positions:
            print("No hay posiciones activas")
            return

        for pos in positions:
            if strategiaName and strategiaName not in pos.comment:
                continue
            if symbol and symbol != pos.symbol:
                continue
            self.mover_stop_loss_be_by_position(pos, newPrice)

    def mover_stop_loss_be_by_position(self, position, newPrice=None):
        new_sl = newPrice if newPrice else position.price_open
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": position.symbol,
            "position": position.ticket,
            "sl": new_sl,
            "tp": position.tp,
            "volume": position.volume,
            "type": position.type,
            "deviation": 0,
            "comment": position.comment
        }
        result = mt5.order_send(request)
        if self._check_execution_status(result):
            print(f"✅ SL movido a BE: {position.symbol}, ticket: {position.ticket}")
        else:
            print(f"❌ Error al mover SL a BE: {result.comment}")

        '''

    def close_partial(self, symbol, nombre_estrategia, partial):
        positions = mt5.positions_get()
        if not positions:
            print("No hay posiciones activas")
            return


        if item_order is None:
            return

        for pos in positions:
            if str(item_order["id_order"]) in pos.comment.lower():
                new_vol = pos.volume * partial / 100
                adjusted_vol = self.ajuste_volumen_step(new_vol, self.symbol_info)

                close_request = {
                    'action': mt5.TRADE_ACTION_DEAL,
                    'position': pos.ticket,
                    'symbol': pos.symbol,
                    'volume': adjusted_vol,
                    'price': self.symbol_info.bid,
                    'type': mt5.ORDER_TYPE_BUY if pos.type == mt5.ORDER_TYPE_SELL else mt5.ORDER_TYPE_SELL,
                    'type_filling': mt5.ORDER_FILLING_FOK,
                    'comment': pos.comment
                }

                result = mt5.order_send(close_request)
                if self._check_execution_status(result):
                    print(f"✅ Parcial cerrada: {pos.symbol} ticket {pos.ticket}")
                else:
                    print(f"❌ Error al cerrar parcial: {result.comment}")
                    '''

    def close_pending(self, symbol, nombre_estrategia):
        orders = mt5.orders_get()
        if not orders:
            print("No hay órdenes pendientes")
            return

        for order in orders:
            if symbol.lower() == order.symbol.lower() and nombre_estrategia.lower() in order.comment.lower():
                self.close_pending_by_order(order)

    def close_pending_by_order(self, order):
        request = {
            'action': mt5.TRADE_ACTION_REMOVE,
            'order': order.ticket,
            'symbol': order.symbol,
            'comment': order.comment
        }

        result = mt5.order_send(request)
        if self._check_execution_status(result):
            print(f"✅ Orden pendiente eliminada: {order.ticket} ({order.symbol})")
        else:
            print(f"❌ Error al eliminar orden: {result.comment}")
            
    def disconnect(self) -> None:
        """
        Cierra la conexión con MetaTrader 5.
        """
        import MetaTrader5 as mt5
        mt5.shutdown()
        print("🔌 Desconectado de MetaTrader 5.")
