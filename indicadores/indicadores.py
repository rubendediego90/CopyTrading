# indicadores.py

import pandas as pd
import pandas_ta as ta

# Calcula RSI
def calcular_rsi(df, periodo=14):
    return ta.rsi(df['close'], length=periodo)

# 📉 Calcula ADX
def calcular_adx(df, di_length=14, adx_smoothing=14):
    adx = ta.adx(high=df['high'], low=df['low'], close=df['close'], length=di_length, adx=adx_smoothing)
    if adx is None:
        return pd.DataFrame(columns=['ADX_14', 'DMP_14', 'DMN_14'])
    return adx

# Calcula EMA

def calcular_ema(df, periodo=50):
    """
    Calcula la EMA de una columna 'close' usando el método más parecido al de TradingView.
    """
    # Asegurar que los precios estén en float64 para precisión
    precios = df['close'].astype('float64')

    # Calcular EMA con método exponencial recursivo (adjust=False)
    ema = precios.ewm(span=periodo, adjust=False).mean()

    return ema