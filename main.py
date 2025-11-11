import MetaTrader5 as mt5
import time
import sys

from config import SYMBOL_CONFIGS
from utils import formatear_vela
from core import nueva_vela_cerrada
from estrategias.ema_rsi_adx import ema_rsi_adx
from brokers.MetaTrader5_broker import MetaTrader5Broker


def main():
    try:
        broker = MetaTrader5Broker()
    except Exception as e:
        print(f"❌ Error inicializando MetaTrader5Broker: {e}")
        return

    # Filtrar y seleccionar solo símbolos activos
    simbolos_activos = [symbol for symbol, config in SYMBOL_CONFIGS.items() if config.get("enabled", True)]

    for symbol in simbolos_activos:
        if not mt5.symbol_select(symbol, True):
            print(f"❌ No se pudo seleccionar el símbolo: {symbol}")
            broker.disconnect()
            return

    print(f"📈 Monitorizando nuevas velas cerradas de: {', '.join(simbolos_activos)}")

    # Guardar última vela cerrada por símbolo
    ultima_fechas = {symbol: None for symbol in simbolos_activos}

    try:
        while True:
            for symbol in simbolos_activos:
                config = SYMBOL_CONFIGS[symbol]
                timeframe = config["timeframe"]

                nueva_vela, ultima_fechas[symbol] = nueva_vela_cerrada(symbol, timeframe, ultima_fechas[symbol])

                if nueva_vela:
                    print(f"\n✅ [{symbol}] Nueva vela cerrada detectada:")
                    print(formatear_vela(nueva_vela, timeframe=timeframe))
                    print("-" * 60)

                    ema_rsi_adx(
                        symbol=symbol,
                        timeframe=timeframe,
                        n=config["n"],
                        rsi_period=config["rsi_period"],
                        adx_length=config["adx_length"],
                        adx_smoothing=config["adx_smoothing"],
                        ema_period=config["ema_period"]
                    )
            time.sleep(1)

    except KeyboardInterrupt:
        print("🛑 Proceso detenido por el usuario.")
    finally:
        broker.disconnect()


if __name__ == "__main__":
    print(sys.executable)  # Muestra la ruta del ejecutable de Python por si estás en entorno virtual
    main()
