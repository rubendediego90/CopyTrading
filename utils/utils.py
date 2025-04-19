import MetaTrader5 as mt5
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

'''
Explicacion video 69
'''
# Crear un método estático para poder convertir una divisa a otra
class Utils():

    def __init__(self):
        pass

    # Creamos nuestro método estático con el decorador @staticmethod
    @staticmethod
    def convert_currency_amount_to_another_currency(amount: float, from_ccy: str, to_ccy: str) -> float:
        # Comprobamos si ambas divisas para la conversión son las mismas
        if from_ccy == to_ccy:
            return amount
        
        all_fx_symbol = ("AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "AUDUSD", "CADCHF", "CADJPY", "CHFJPY", "EURAUD", "EURCAD",
                        "EURCHF", "EURGBP", "EURJPY", "EURNZD", "EURUSD", "GBPAUD", "GBPCAD", "GBPCHF", "GBPJPY", "GBPNZD",
                        "GBPUSD", "NZDCAD", "NZDCHF", "NZDJPY", "NZDUSD", "USDCAD", "USDCHF", "USDJPY", "USDSEK", "USDNOK")
        
        # Convertir las divisas a mayúsculas
        from_ccy = from_ccy.upper()
        to_ccy = to_ccy.upper()

        # Buscamos el símbolo que relaciona nuestra divisa origen con nuestra divisa destino (list comprehension)
        fx_symbol = [symbol for symbol in all_fx_symbol if from_ccy in symbol and to_ccy in symbol][0]
        fx_symbol_base = fx_symbol[:3]

        # Recuperamos los últimos datos disponibles del fx_symbol
        try:
            tick = mt5.symbol_info_tick(fx_symbol)
            if tick is None:
                raise Exception(f"El símbolo {fx_symbol} no está disponible en la plataforma MT5. Por favor, revísa los símbolos disponibles de tu broker.")

        except Exception as e:
            print(f"ERROR: No se pudo recuperar el último tick del símbolo {fx_symbol}. MT5 error: {mt5.last_error()}, Exception: {e}")
            return 0.0
        
        else:
            # Recuperamos el último precio disponible del símbolo
            last_price = tick.bid

            # Convertimos la cantidad de la divisa origen a la divisa destino
            converted_amount = amount / last_price if fx_symbol_base == to_ccy else amount * last_price
            return converted_amount

    @staticmethod
    def dateprint() -> str:
        return datetime.now(ZoneInfo("Asia/Nicosia")).strftime("%d/%m/%Y %H:%M:%S.%f")[:-3]



