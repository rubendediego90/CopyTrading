# core/deteccion.py

import MetaTrader5 as mt5

# 🔄 Obtiene las últimas 2 velas (una cerrada, otra en formación)
def obtener_ultimas_velas(symbol, timeframe):
    return mt5.copy_rates_from_pos(symbol, timeframe, 0, 2)

# 📈 Detecta si hay una nueva vela cerrada
def nueva_vela_cerrada(symbol, timeframe, ultima_fecha_guardada):
    rates = obtener_ultimas_velas(symbol, timeframe)
    if rates is None or len(rates) < 2:
        return None, ultima_fecha_guardada

    vela_cerrada = rates[-2]
    fecha_cierre = vela_cerrada['time']

    if fecha_cierre != ultima_fecha_guardada:
        return vela_cerrada, fecha_cierre

    return None, ultima_fecha_guardada

# 🆕 Obtiene las últimas N velas cerradas
def obtener_velas_cerradas(symbol, timeframe, n):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 1, n)
    return rates if rates is not None and len(rates) == n else None
