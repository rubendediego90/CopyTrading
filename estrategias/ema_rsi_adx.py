import pandas as pd
from datetime import timedelta

from indicadores.indicadores import calcular_rsi, calcular_ema, calcular_adx
from utils.helpers import convertir_rates_a_dataframe, timeframe_to_seconds
from core.deteccion import obtener_velas_cerradas

def ema_rsi_adx(symbol, timeframe, n, rsi_period=14, adx_length=14, adx_smoothing=14, ema_period=50, barras_totales=10):
    # Usar directamente barras_totales sin cálculos adicionales
    print("🧮 Barras totales a obtener:", barras_totales)
    
    velas = obtener_velas_cerradas(symbol, timeframe, barras_totales)
    if velas is None:
        print("❌ No se pudieron obtener las velas cerradas.")
        return

    df = convertir_rates_a_dataframe(velas)
    duracion = timeframe_to_seconds(timeframe)

    print(f"📊 Últimas {n} velas cerradas de {symbol} con RSI, ADX y EMA (calculadas con {barras_totales} barras de contexto):")

    # ✅ Calculamos indicadores sobre todo el dataframe
    df['RSI'] = calcular_rsi(df, rsi_period)
    df[f'EMA_{ema_period}'] = calcular_ema(df, ema_period)
    adx_df = calcular_adx(df, di_length=adx_length, adx_smoothing=adx_smoothing)
    df = pd.concat([df, adx_df], axis=1)

    # 🔁 Recorremos las últimas n barras (las más recientes)
    for i in range(len(df) - n, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i - 1] if i > 0 else None

        cierre_utc = row['time'] + timedelta(seconds=duracion)

        rsi_str = f"{row['RSI']:.2f}" if pd.notna(row['RSI']) else "---"
        adx_col = next((col for col in df.columns if col.startswith('ADX')), None)
        dmp_col = next((col for col in df.columns if col.startswith('DMP')), None)
        dmn_col = next((col for col in df.columns if col.startswith('DMN')), None)

        adx_str = f"{row[adx_col]:.2f}" if adx_col and pd.notna(row[adx_col]) else "---"
        dmp_str = f"{row[dmp_col]:.2f}" if dmp_col and pd.notna(row[dmp_col]) else "---"
        dmn_str = f"{row[dmn_col]:.2f}" if dmn_col and pd.notna(row[dmn_col]) else "---"

        ema_val = row[f'EMA_{ema_period}']
        ema_str = f"{ema_val:.2f}" if pd.notna(ema_val) else "---"

        # 📉 Cruce EMA
        cruce = None
        if prev_row is not None and pd.notna(ema_val) and pd.notna(prev_row[f'EMA_{ema_period}']):
            if prev_row['close'] < prev_row[f'EMA_{ema_period}'] and row['high'] >= ema_val:
                cruce = ema_val  # 🟢 Cruce alcista
            elif prev_row['close'] > prev_row[f'EMA_{ema_period}'] and row['low'] <= ema_val:
                cruce = ema_val  # 🔴 Cruce bajista

        cruce_str = f"{cruce:.2f}" if cruce is not None else "None"

        print(
            f"F.Fin: {cierre_utc.strftime('%Y-%m-%d %H:%M:%S')} | "
            f"F.Inicio: {row['time'].strftime('%Y-%m-%d %H:%M:%S')} | "
            f"O: {row['open']:.2f}, H: {row['high']:.2f}, L: {row['low']:.2f}, C: {row['close']:.2f} | "
            f"RSI: {rsi_str}, ADX: {adx_str}, +DI: {dmp_str}, -DI: {dmn_str}, EMA: {ema_str}, CRUCE EMA: {cruce_str}"
        )

    print("-" * 120)
