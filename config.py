import MetaTrader5 as mt5
#Tutorial 
SYMBOL_CONFIGS = {
    "XAUUSD": {
        "enabled": True,  # ✅ Usar este símbolo
        "timeframe": mt5.TIMEFRAME_M5,
        "n": 60,
        "rsi_period": 3,
        "adx_length": 5,
        "adx_smoothing": 5,
        "ema_period": 50,
        "barras_totales": 100
    },
    "BTCUSD": {
        "enabled": False,  # ❌ No usar este símbolo
        "timeframe": mt5.TIMEFRAME_M5,
        "n": 10,
        "rsi_period": 7,
        "adx_length": 10,
        "adx_smoothing": 5,
        "ema_period": 100,
        "barras_totales": 100
    }
}
