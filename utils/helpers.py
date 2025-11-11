import pandas as pd
from constantes import MT5_TIMEFRAME_SECONDS
from datetime import datetime, timedelta, timezone

def formatear_vela(vela, timeframe):
    """
    Formatea una vela para imprimir con hora de inicio y cierre en UTC.
    vela['time'] debe ser un timestamp en segundos (int).
    """
    duracion = timeframe_to_seconds(timeframe)

    # Convertimos a datetime timezone-aware en UTC
    inicio = datetime.fromtimestamp(vela['time'], tz=timezone.utc)
    cierre = inicio + timedelta(seconds=duracion)

    return (
        f"F.Fin: {cierre.strftime('%Y-%m-%d %H:%M:%S')} | "
        f"F.Inicio: {inicio.strftime('%Y-%m-%d %H:%M:%S')} | "
        f"O: {vela['open']:.2f}, H: {vela['high']:.2f}, "
        f"L: {vela['low']:.2f}, C: {vela['close']:.2f}"
    )


def convertir_rates_a_dataframe(rates):
    """Convierte rates de MT5 a DataFrame con columna 'time' en datetime UTC."""
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)  # UTC explícito
    return df

def timeframe_to_seconds(timeframe):
    if timeframe in MT5_TIMEFRAME_SECONDS:
        return MT5_TIMEFRAME_SECONDS[timeframe]
    else:
        raise ValueError(f"Timeframe {timeframe} no reconocido en MT5_TIMEFRAME_SECONDS")
