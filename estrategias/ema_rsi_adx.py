class LogConfig:
    def __init__(self, evaluar=True, bloque_rsi=True, contexto_ema=True, senal_final=True):
        self.evaluar = evaluar
        self.bloque_rsi = bloque_rsi
        self.contexto_ema = contexto_ema
        self.senal_final = senal_final

import pandas as pd
from datetime import timedelta
from typing import Optional, Dict, List

from indicadores.indicadores import calcular_rsi, calcular_ema, calcular_adx
from utils.helpers import convertir_rates_a_dataframe, timeframe_to_seconds
from core.deteccion import obtener_velas_cerradas


def detectar_cruce_ema(row, prev_row, ema_period):
    """
    Detecta cruces de EMA.
    
    Retorna:
        dict: {
            'tipo': 'alcista' | 'bajista' | None,
            'valor_ema': float,
            'precio': float,
            'diferencia': float
        }
        O None si no hay cruce
    """
    if prev_row is None:
        return None
    
    ema_val = row[f'EMA_{ema_period}']
    prev_ema = prev_row[f'EMA_{ema_period}']
    
    if pd.isna(ema_val) or pd.isna(prev_ema):
        return None
    
    # Cruce alcista: precio viene de abajo de la EMA y toca/cruza arriba
    if prev_row['close'] < prev_ema and row['high'] >= ema_val:
        return {
            'tipo': 'alcista',
            'valor_ema': ema_val,
            'precio': row['high'],
            'diferencia': row['high'] - ema_val
        }
    
    # Cruce bajista: precio viene de arriba de la EMA y toca/cruza abajo
    if prev_row['close'] > prev_ema and row['low'] <= ema_val:
        return {
            'tipo': 'bajista',
            'valor_ema': ema_val,
            'precio': row['low'],
            'diferencia': row['low'] - ema_val
        }
    
    return None


def validar_contexto_ema(df, idx_inicio_bloque, ema_period, side, verbose=False):
    """
    PASO 8: Valida que las 10 velas anteriores estén al mismo lado de la EMA.
    """
    # Selecciona las 10 velas previas al bloque, incluyendo la vela justo antes del bloque
    fin = idx_inicio_bloque  # Exclusivo
    inicio = max(0, fin - 10)
    velas_contexto = df.iloc[inicio:fin]
    logs = []
    
    if len(velas_contexto) == 0:
        logs.append("[ERROR] CONTEXTO: No hay velas en el contexto")
        return False, logs
    
    ema_col = f'EMA_{ema_period}'
    cruces_count = 0
    velas_lado = 0
    
    # Imprimir solo las 10 velas previas, con índice relativo 1-10
    for rel_idx, (i, row) in enumerate(velas_contexto.iterrows(), start=1):
        ema_val = row[ema_col]
        close = row['close']

        if pd.isna(ema_val):
            logs.append(f"[ERROR] CONTEXTO [{i}]: EMA es NaN")
            return False, logs

        # Añadir info de precios por vela para trazabilidad (índice relativo)
        logs.append(f"  [CTX {rel_idx}] time={row['time']}, O={row['open']:.2f}, H={row['high']:.2f}, L={row['low']:.2f}, C={close:.2f}, EMA={ema_val:.2f}")

        if side == 'long':
            en_lado = close > ema_val
            if not en_lado:
                cruces_count += 1
        else:  # short
            en_lado = close < ema_val
            if not en_lado:
                cruces_count += 1

        if en_lado:
            velas_lado += 1
    
    logs.append(f"[INFO] CONTEXTO EMA: {velas_lado}/{len(velas_contexto)} velas en lado {'LONG' if side == 'long' else 'SHORT'}, Cruces={cruces_count}")
    
    valido = cruces_count <= 1
    if valido:
        logs.append("[OK] CONTEXTO: Cruces <= 1")
    else:
        logs.append(f"[ERROR] CONTEXTO FALLA: Demasiados cruces ({cruces_count} > 1)")
    
    return valido, logs


def verificar_cruce_rsi(row, prev_row, side, log_idx=None):
    """
    PASO 1-2: Verifica si RSI cruzó desde extremo a neutral.
    side: 'long' o 'short'
    """
    if pd.isna(row['RSI']) or pd.isna(prev_row['RSI']):
        return False, None
    
    if side == 'long':
        cruce = prev_row['RSI'] < 20 and row['RSI'] > 20
        if cruce:
            return True, f"[OK] RSI LONG: {prev_row['RSI']:.2f} < 20 -> {row['RSI']:.2f} > 20"
        else:
            return False, f"[ERROR] RSI LONG falla: prev={prev_row['RSI']:.2f}, curr={row['RSI']:.2f}"
    else:  # short
        cruce = prev_row['RSI'] > 80 and row['RSI'] < 80
        if cruce:
            return True, f"[OK] RSI SHORT: {prev_row['RSI']:.2f} > 80 -> {row['RSI']:.2f} < 80"
        else:
            return False, f"[ERROR] RSI SHORT falla: prev={prev_row['RSI']:.2f}, curr={row['RSI']:.2f}"


def verificar_adx(row, adx_min, adx_col='ADX_14', side=None):
    """PASO 3: Verifica si ADX es suficiente."""
    adx = row.get(adx_col, 0)
    valido = not pd.isna(adx) and adx > adx_min
    
    if valido:
        msg = f"[OK] ADX: {adx:.2f} > {adx_min}"
    else:
        msg = f"[ERROR] ADX falla: {adx:.2f} <= {adx_min}"
    
    return valido, msg


def recolectar_bloque_rsi(df, idx_inicio, ema_period, side, adx_min, adx_col='ADX_14'):
    """
    PASOS 4-6: Recorre hacia atrás recolectando velas del bloque RSI.
    Retorna: (bloque_velas, max_low/min_high, cruce_encontrado, logs)
    """
    bloque_velas = []
    extremo_price = float('inf') if side == 'long' else 0
    cruce_encontrado = False
    logs = []
    
    for i in range(idx_inicio - 1, -1, -1):
        row = df.iloc[i]
        prev_row = df.iloc[i - 1] if i > 0 else None
        
        rsi = row['RSI']
        if pd.isna(rsi):
            logs.append(f"  [{i}] RSI es NaN, saliendo del bloque")
            break
        
        # Verificar si RSI sale del rango extremo
        if side == 'long' and rsi > 20:
            logs.append(f"  [{i}] RSI={rsi:.2f} sale del extremo (>20), FIN BLOQUE")
            break
        if side == 'short' and rsi < 80:
            logs.append(f"  [{i}] RSI={rsi:.2f} sale del extremo (<80), FIN BLOQUE")
            break
        
        # Verificar ADX
        adx = row.get(adx_col, 0)
        if pd.isna(adx) or adx <= adx_min:
            adx_str = f"{adx:.2f}" if not pd.isna(adx) else "NaN"
            logs.append(f"  [{i}] time={row['time']}, C={row['close']:.2f} | ADX={adx_str} <= {adx_min}, SALTANDO")
            continue
        
        # Recolectar extremo
        if side == 'long':
            if row['low'] < extremo_price:
                extremo_price = row['low']
        else:  # short
            if row['high'] > extremo_price:
                extremo_price = row['high']
        
        # Detectar cruce
        cruce = detectar_cruce_ema(row, prev_row, ema_period)
        if cruce:
            cruce_encontrado = True
            logs.append(f"  [{i}] CRUCE EMA {cruce['tipo'].upper()}: Precio={cruce['precio']:.2f}, EMA={cruce['valor_ema']:.2f}")
        
    bloque_velas.append((i, row))
    logs.append(f"  [{i}] time={row['time']}, O={row['open']:.2f}, H={row['high']:.2f}, L={row['low']:.2f}, C={row['close']:.2f} | RSI={rsi:.2f}, Extremo={'LOW' if side == 'long' else 'HIGH'}={extremo_price:.2f}")
    
    logs.append(f"[INFO] BLOQUE RSI: {len(bloque_velas)} velas, Extremo={extremo_price:.2f}, Cruce={'SI' if cruce_encontrado else 'NO'}")
    
    return bloque_velas, extremo_price, cruce_encontrado, logs


def validar_bloque_completo(bloque_velas, cruce_encontrado, df, ema_period, side):
    """PASOS 7-8: Valida que el bloque sea válido."""
    logs = []
    
    if len(bloque_velas) == 0:
        logs.append("[ERROR] VALIDACION BLOQUE: Bloque vacio")
        return False, logs
    
    if not cruce_encontrado:
        logs.append("[ERROR] VALIDACION BLOQUE: No hay cruce EMA en el bloque")
        return False, logs
    
    idx_primer_vela = bloque_velas[-1][0]
    contexto_ok, contexto_logs = validar_contexto_ema(df, idx_primer_vela, ema_period, side)
    logs.extend(contexto_logs)
    
    if contexto_ok:
        logs.append("[OK] VALIDACION BLOQUE COMPLETA: OK")
    
    return contexto_ok, logs


def crear_senal(side, idx_entrada, entry_price, extremo_price, bloque_size):
    """Construye diccionario de señal."""
    return {
        'side': side,
        'entry_idx': idx_entrada,
        'entry_price': entry_price,
        'stop_loss': extremo_price,
        'bloque_size': bloque_size,
        'cruce': True
    }


def evaluar_entrada_para_vela(df, idx, ema_period, adx_min=30, adx_col='ADX_14'):
    """Evalúa las condiciones para una única vela (idx) y muestra logs detallados.

    Retorna diccionario {'long': signal|None, 'short': signal|None}
    """
    resultado = {'long': None, 'short': None}
    if idx <= 0:
        return resultado

    # Configuración de logs (puedes pasarla como argumento si lo prefieres)
    log_config = getattr(df, 'log_config', LogConfig())

    row = df.iloc[idx]
    prev_row = df.iloc[idx - 1]

    if log_config.evaluar:
        print(f"[INFO] Vela evaluada index={idx}, time={row['time']}, O={row['open']:.2f}, H={row['high']:.2f}, L={row['low']:.2f}, C={row['close']:.2f}")

    if pd.isna(row['RSI']) or pd.isna(prev_row['RSI']):
        if log_config.evaluar:
            print("[DEBUG] RSI no disponible para la vela, no se puede evaluar")
        return resultado

    for side in ('long', 'short'):
        if log_config.evaluar:
            print(f"\n[CHECK] Evaluando {side.upper()} para vela index={idx}")
        rsi_ok, rsi_msg = verificar_cruce_rsi(row, prev_row, side)
        if log_config.evaluar:
            print(f"   {rsi_msg} | C={row['close']:.2f}")
        adx_ok, adx_msg = verificar_adx(row, adx_min, adx_col=adx_col)
        adx_val = row.get(adx_col, 0)
        if log_config.evaluar:
            print(f"   {adx_msg} | ADX_actual={adx_val:.2f} | C={row['close']:.2f}")

        if not rsi_ok or not adx_ok:
            reasons = []
            if not rsi_ok:
                reasons.append('RSI')
            if not adx_ok:
                reasons.append('ADX')
            if log_config.evaluar:
                print(f"   [RESULT] {side.upper()} RECHAZADO por: {', '.join(reasons)}")
            continue

        if log_config.bloque_rsi:
            print(f"   [DEBUG] RSI y ADX pasan — recolectando bloque RSI hacia atrás (vela inicial C={row['close']:.2f})")
        bloque, extremo, cruce, logs_bloque = recolectar_bloque_rsi(df, idx, ema_period, side, adx_min, adx_col=adx_col)
        if log_config.bloque_rsi:
            for l in logs_bloque:
                print(f"      {l}")

        valido, logs_validacion = validar_bloque_completo(bloque, cruce, df, ema_period, side)
        if log_config.contexto_ema:
            for l in logs_validacion:
                print(f"      {l}")

        if not valido:
            if log_config.evaluar:
                print(f"   [RESULT] {side.upper()} RECHAZADO en validación de bloque/contexto")
            continue

        senal = crear_senal(side, idx, row['close'], extremo, len(bloque))
        resultado[side] = senal
        if log_config.senal_final:
            print(f"   [RESULT] {side.upper()} ACEPTADO — señal construida | STOP LOSS: {senal['stop_loss']:.2f}")

    return resultado


def evaluar_entrada_long_short(df, ema_period, adx_min=30, adx_col='ADX_14'):
    """Evalúa entrada LONG y SHORT con confirmación multicapa."""
    resultado = {'long': None, 'short': None}
    
    if len(df) < 5:
        return resultado
    
    for idx in range(len(df) - 1, 0, -1):
        row = df.iloc[idx]
        prev_row = df.iloc[idx - 1]
        
        rsi = row['RSI']
        if pd.isna(rsi) or pd.isna(prev_row['RSI']):
            continue
        
        # Evaluar LONG
        rsi_ok, rsi_msg = verificar_cruce_rsi(row, prev_row, 'long')
        if rsi_ok:
            adx_ok, adx_msg = verificar_adx(row, adx_min, adx_col=adx_col)
            if adx_ok:
                print(f"\n[DEBUG] Evaluando LONG en vela [{idx}]:")
                print(f"   {rsi_msg}")
                print(f"   {adx_msg}")
                entrada = _procesar_entrada(df, idx, ema_period, 'long', adx_min, adx_col=adx_col)
                if entrada:
                    resultado['long'] = entrada
        
        # Evaluar SHORT
        rsi_ok, rsi_msg = verificar_cruce_rsi(row, prev_row, 'short')
        if rsi_ok:
            adx_ok, adx_msg = verificar_adx(row, adx_min, adx_col=adx_col)
            if adx_ok:
                print(f"\n[DEBUG] Evaluando SHORT en vela [{idx}]:")
                print(f"   {rsi_msg}")
                print(f"   {adx_msg}")
                entrada = _procesar_entrada(df, idx, ema_period, 'short', adx_min, adx_col=adx_col)
                if entrada:
                    resultado['short'] = entrada
    
    return resultado


def _procesar_entrada(df, idx, ema_period, side, adx_min, adx_col='ADX_14'):
    """Procesa una entrada potencial con logs detallados."""
    bloque, extremo, cruce, logs_bloque = recolectar_bloque_rsi(df, idx, ema_period, side, adx_min, adx_col=adx_col)
    
    for log in logs_bloque:
        print(f"   {log}")
    
    valido, logs_validacion = validar_bloque_completo(bloque, cruce, df, ema_period, side)
    
    for log in logs_validacion:
        print(f"   {log}")
    
    if not valido:
        return None
    
    return crear_senal(side, idx, df.iloc[idx]['close'], extremo, len(bloque))


def imprimir_vela(row, prev_row, duracion, ema_period, df):
    """
    Imprime una vela con todos sus indicadores.
    
    Retorna:
        dict: información del cruce si existe
    """
    cierre_utc = row['time'] + timedelta(seconds=duracion)
    
    # Formatos de indicadores
    rsi_str = f"{row['RSI']:.2f}" if pd.notna(row['RSI']) else "---"
    ema_val = row[f'EMA_{ema_period}']
    ema_str = f"{ema_val:.2f}" if pd.notna(ema_val) else "---"
    
    # Buscar columnas de ADX y directionales
    adx_col = next((col for col in df.columns if col.startswith('ADX')), None)
    dmp_col = next((col for col in df.columns if col.startswith('DMP')), None)
    dmn_col = next((col for col in df.columns if col.startswith('DMN')), None)
    
    adx_str = f"{row[adx_col]:.2f}" if adx_col and pd.notna(row[adx_col]) else "---"
    dmp_str = f"{row[dmp_col]:.2f}" if dmp_col and pd.notna(row[dmp_col]) else "---"
    dmn_str = f"{row[dmn_col]:.2f}" if dmn_col and pd.notna(row[dmn_col]) else "---"
    
    # Detectar cruce EMA
    cruce_info = detectar_cruce_ema(row, prev_row, ema_period)
    
    if cruce_info:
        cruce_str = f"{cruce_info['tipo'].upper()}: EMA={cruce_info['valor_ema']:.2f}, Precio={cruce_info['precio']:.2f}, Diff={cruce_info['diferencia']:.2f}"
    else:
        cruce_str = "None"
    
    # Imprimir vela
    print(
        f"F.Fin: {cierre_utc.strftime('%Y-%m-%d %H:%M:%S')} | "
        f"F.Inicio: {row['time'].strftime('%Y-%m-%d %H:%M:%S')} | "
        f"O: {row['open']:.2f}, H: {row['high']:.2f}, L: {row['low']:.2f}, C: {row['close']:.2f} | "
        f"RSI: {rsi_str}, ADX: {adx_str}, +DI: {dmp_str}, -DI: {dmn_str}, EMA: {ema_str}, CRUCE: {cruce_str}"
    )
    
    return cruce_info


def imprimir_senales_finales(entradas):
    """Imprime SOLO las señales VÁLIDAS encontradas."""
    if entradas['long']:
        senal = entradas['long']
        print(f"\n{'='*80}")
        print(f"[SIGNAL] SEÑAL LONG VALIDA ENCONTRADA")
        print(f"   Entry: {senal['entry_price']:.2f}")
        print(f"   Stop Loss: {senal['stop_loss']:.2f}")
        print(f"   Bloque RSI: {senal['bloque_size']} velas")
        print(f"{'='*80}")
    
    if entradas['short']:
        senal = entradas['short']
        print(f"\n{'='*80}")
        print(f"[SIGNAL] SEÑAL SHORT VALIDA ENCONTRADA")
        print(f"   Entry: {senal['entry_price']:.2f}")
        print(f"   Stop Loss: {senal['stop_loss']:.2f}")
        print(f"   Bloque RSI: {senal['bloque_size']} velas")
        print(f"{'='*80}")


def ema_rsi_adx(symbol, timeframe, n, rsi_period=14, adx_length=14, adx_smoothing=14, ema_period=50, barras_totales=10):
    """
    Calcula indicadores técnicos (RSI, ADX, EMA) y evalúa señales de entrada LONG/SHORT.
    
    Retorna:
        dict: {
            'long': {...} o None,
            'short': {...} o None
        }
    """
    velas = obtener_velas_cerradas(symbol, timeframe, barras_totales)
    if velas is None:
        print("[ERROR] No se pudieron obtener las velas cerradas.")
        return {'long': None, 'short': None}

    df = convertir_rates_a_dataframe(velas)

    # Calculamos indicadores sobre todo el dataframe
    df['RSI'] = calcular_rsi(df, rsi_period)
    df[f'EMA_{ema_period}'] = calcular_ema(df, ema_period)
    adx_df = calcular_adx(df, di_length=adx_length, adx_smoothing=adx_smoothing)
    df = pd.concat([df, adx_df], axis=1)

    # Detectar columna de ADX correcta (nombre depende de di_length)
    adx_col = f'ADX_{adx_length}'
    if adx_col not in df.columns:
        adx_cols = [col for col in df.columns if col.startswith('ADX_')]
        if adx_cols:
            adx_col = adx_cols[0]
            print(f"[INFO] Columna ADX detectada: {adx_col}")
        else:
            print("[ERROR] No se encontró columna ADX en el dataframe")
            return {'long': None, 'short': None}
    
    # Evaluar sólo la última vela cerrada (evitar imprimir todo el histórico)
    last_idx = len(df) - 1
    if last_idx <= 0:
        return {'long': None, 'short': None}


    # Permitir pasar log_config como argumento (por defecto todo activado)
    import config
    log_config = getattr(config, 'LOG_CONFIG', LogConfig())
    df.log_config = log_config

    entradas = evaluar_entrada_para_vela(df, last_idx, ema_period, adx_min=30, adx_col=adx_col)
    imprimir_senales_finales(entradas)

    return entradas
