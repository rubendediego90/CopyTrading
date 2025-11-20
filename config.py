# Importar LogConfig para configuración de logs
from estrategias.ema_rsi_adx import LogConfig
import MetaTrader5 as mt5
#Tutorial 
SYMBOL_CONFIGS = {
    "XAUUSD": {
        "enabled": True,  # Usar este símbolo
        "timeframe": mt5.TIMEFRAME_M5,
        "n": 60,
        "rsi_period": 3,
        "adx_length": 5,
        "adx_smoothing": 5,
        "ema_period": 50,
        "barras_totales": 100,
        "risk": 0.01  # Riesgo por operación (1%)
    },
    "BTCUSD": {
        "enabled": False,  # No usar este símbolo
        "timeframe": mt5.TIMEFRAME_M5,
        "n": 10,
        "rsi_period": 7,
        "adx_length": 10,
        "adx_smoothing": 5,
        "ema_period": 100,
        "barras_totales": 100,
        "risk": 0.01  # Riesgo por operación (1%)
    }
}

# Configuración global de logs para la estrategia EMA/RSI/ADX
LOG_CONFIG = LogConfig(
    evaluar=True,        # Logs de evaluación general
    bloque_rsi=True,     # Logs del bloque RSI
    contexto_ema=True,   # Logs de validación de contexto EMA
    senal_final=True     # Logs de señal final aceptada
)
