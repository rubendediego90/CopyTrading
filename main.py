
import MetaTrader5 as mt5
import time
import sys
import threading

from config import SYMBOL_CONFIGS
from utils import formatear_vela
from core import nueva_vela_cerrada
from estrategias.ema_rsi_adx import ema_rsi_adx
from brokers.MetaTrader5_broker import MetaTrader5Broker

# Logger que escribe en consola y en archivo
class DualLogger:
    def __init__(self, filename):
        self.lock = threading.Lock()
        self.file = open(filename, 'a', encoding='utf-8')

    def write(self, msg):
        with self.lock:
            self.file.write(msg)
            self.file.flush()
        sys.__stdout__.write(msg)
        sys.__stdout__.flush()

    def flush(self):
        self.file.flush()
        sys.__stdout__.flush()

    def close(self):
        self.file.close()

# Redirigir print a logger dual
sys.stdout = DualLogger('logs.txt')


def main():
    try:
        broker = MetaTrader5Broker()
    except Exception as e:
        print(f"[ERROR] Inicializando MetaTrader5Broker: {e}")
        return

    # Filtrar y seleccionar solo símbolos activos
    simbolos_activos = [symbol for symbol, config in SYMBOL_CONFIGS.items() if config.get("enabled", True)]

    for symbol in simbolos_activos:
        if not mt5.symbol_select(symbol, True):
            print(f"[ERROR] No se pudo seleccionar el símbolo: {symbol}")
            broker.disconnect()
            return

    print(f"[INFO] Monitorizando nuevas velas cerradas de: {', '.join(simbolos_activos)}")

    # Guardar última vela cerrada por símbolo
    ultima_fechas = {symbol: None for symbol in simbolos_activos}

    try:
        while True:
            for symbol in simbolos_activos:
                config = SYMBOL_CONFIGS[symbol]
                timeframe = config["timeframe"]

                nueva_vela, ultima_fechas[symbol] = nueva_vela_cerrada(symbol, timeframe, ultima_fechas[symbol])

                if nueva_vela:
                    print(f"\n[OK] [{symbol}] Nueva vela cerrada detectada:")
                    print(formatear_vela(nueva_vela, timeframe=timeframe))
                    print("-" * 60)

                    # Ejecutar estrategia y capturar señales
                    entradas = ema_rsi_adx(
                        symbol=symbol,
                        timeframe=timeframe,
                        n=config["n"],
                        rsi_period=config["rsi_period"],
                        adx_length=config["adx_length"],
                        adx_smoothing=config["adx_smoothing"],
                        ema_period=config["ema_period"],
                        barras_totales=config["barras_totales"]
                    )
                    
                    # Procesar señales (aquí puedes agregar lógica de órdenes, notificaciones, etc.)
                    if entradas and (entradas.get('long') or entradas.get('short')):
                        print(f"\n[SIGNAL] Señales generadas para {symbol}:")
                        if entradas.get('long'):
                            print(f"   LONG: Entry={entradas['long']['entry_price']:.2f}, SL={entradas['long']['stop_loss']:.2f}")
                        if entradas.get('short'):
                            print(f"   SHORT: Entry={entradas['short']['entry_price']:.2f}, SL={entradas['short']['stop_loss']:.2f}")
            time.sleep(1)

    except KeyboardInterrupt:
        print("[INFO] Proceso detenido por el usuario.")
    finally:
        broker.disconnect()
        # Restaurar stdout y cerrar archivo
        if hasattr(sys.stdout, 'close'):
            sys.stdout.close()
        sys.stdout = sys.__stdout__


if __name__ == "__main__":
    print(sys.executable)  # Muestra la ruta del ejecutable de Python por si estás en entorno virtual
    main()
