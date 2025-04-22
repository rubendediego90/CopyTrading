from constantes.types import SYMBOLS_SNIPERS_GOLD, SYMBOL
import re
from brokers.MetaTrader5_broker import MetaTrader5Broker

class SnipersGold:
    def __init__(self, brokerInstance : MetaTrader5Broker):
        self.brokerInstance : MetaTrader5Broker = brokerInstance
        self.RISK = 0.005
        pass
        
    def handle(self,msg,last_cash_balance):
        print('*Snipers Gold*',msg)
        symbol = self.getSymbol(msg)
        FTMO_CONDITION_PERCENTAGE = 4
        can_open_new_position = self.brokerInstance.can_open_new_position(last_cash_balance,FTMO_CONDITION_PERCENTAGE)
        if(symbol == None):
            print('mensaje sin identificar simbolo',msg)
            return
            
        print('El símbolo es:',symbol)
        
        orders_type = self.getOrderType(msg)
        
        if can_open_new_position == False:
            return
        
        if orders_type["hasNewOrder"]:
            print("ACTION - Nueva orden")
            
            valores = self.extraer_valores(msg)
            tpList = valores['TP']
            print("tpList",tpList)
            print("valores",valores)
            self.brokerInstance.handle_order(valores=valores,symbol=symbol,risk=self.RISK,tpList=tpList,nombreStrategy="SNIPERS_GOLD")
            return

    def getSymbol(self,msg):
        print("SYMBOLS_SNIPERS_GOLD.XAU.lower()",SYMBOLS_SNIPERS_GOLD.XAU.lower())
        print("msg.lower())",msg.lower())
        if SYMBOLS_SNIPERS_GOLD.XAU.lower() in msg.lower() or SYMBOLS_SNIPERS_GOLD.XAUUSD.lower() in msg.lower():
            return SYMBOL.ORO.value
        
        if SYMBOLS_SNIPERS_GOLD.BTC.lower() in msg.lower() or SYMBOLS_SNIPERS_GOLD.BITCOIN.lower() in msg.lower():
            return SYMBOL.BTC.value
        
        return None
    
    def getOrderType(self,msg):
        words_open = ["tp","entry","sl"]

        msg_lower = msg.lower()
        words_open_lower = [p.lower() for p in words_open]
        
        hasNewOrder = False

        if all(palabra in msg_lower for palabra in words_open_lower):
            hasNewOrder = True
            
        return {
            "hasNewOrder": hasNewOrder,
        }
        
    #TODO revisar
    def extraer_valores(self, texto):
        patrones = {
            "SL": r"\bSL[:\-]?\s*([\d.,]+[KkMmBb]?)",  # Añadido para manejar 'K', 'M', 'B'
            "TP": r"\bTP[:\-]?\s*([\d.,]+[KkMmBb]?)",
            "Entry": r"\b(?:Entrada|Long|Short)[:\-]?\s*([\d.,]+[KkMmBb]?)",
            "rango":r"([\d.,]+[KkMmBb]?)\s*(?:a|-|~)\s*([\d.,]+[KkMmBb]?)"
        }

        resultados = {
                      'TP': None,
                      'SL': None,
                      'isShort':None,
                      'isLong':None,
                      'rango': None,  # Nuevo campo para almacenar el rango,
                      'rango_inferior':None,
                      'rango_superior':None,
                      }
        

        # Primero, extraemos las coincidencias sin hacer ningún casteo
        extracciones = {}
        for clave, patron in patrones.items():
            coincidencias = re.findall(patron, texto, flags=re.IGNORECASE)
            extracciones[clave] = coincidencias if coincidencias else None
            
        if extracciones['rango'] and len(extracciones['rango'][0]) == 2:
            extracciones['rango_inferior'] = [extracciones['rango'][0][0]]
            extracciones['rango_superior'] = [extracciones['rango'][0][1]]
        extracciones['rango'] = None 
        
        print("extracciones",extracciones)

        # Ahora, limpiamos (casteamos) los valores extraídos
        for clave, coincidencias in extracciones.items():
            if coincidencias:
                # Si encontramos coincidencias, las limpiamos
                resultados[clave] = [self.limpiar_numero(c) for c in coincidencias if self.limpiar_numero(c) is not None]
            else:
                # Si no encontramos coincidencias, asignamos None
                resultados[clave] = None
                

            
        # Aquí procesamos las listas para devolver solo el primer valor o None si no existen
        for clave in resultados:
            if isinstance(resultados[clave], list) and len(resultados[clave]) > 0 and clave != "TP":
                # Si es una lista no vacía, asignamos el primer valor
                resultados[clave] = resultados[clave][0]
            elif isinstance(resultados[clave], list) and len(resultados[clave]) == 0:
                # Si la lista está vacía, asignamos None
                resultados[clave] = None
                
        # Comparación entre SL y TP2 para determinar isShort y isLong
        if resultados['SL'] is not None and resultados['TP'] is not None:
            if resultados['SL'] > resultados['TP'][0]:
                resultados['isShort'] = True
                resultados['isLong'] = False
            elif resultados['SL'] < resultados['TP'][0]:
                resultados['isShort'] = False
                resultados['isLong'] = True


        return resultados
    
    def limpiar_numero(self, num_str):
        """
        Limpiar el número removiendo espacios, comas, y manejando sufijos como 'K', 'M' o 'B'.
        También gestiona la separación de miles y decimales.
        """
        # Quitar espacios y comas primero
        num_str = num_str.replace(" ", "").replace(",", "")

        # Si tiene un punto, verificamos si es un separador de miles o un decimal
        if '.' in num_str:
            partes = num_str.split('.')
            # Si el número tiene más de 3 dígitos después del punto, es un separador de miles
            if len(partes[-1]) == 3:  # Tiene 3 cifras a la derecha => separador de miles
                    num_str = num_str.replace('.', '')

        # Verificamos los sufijos 'K', 'M', 'B' (mayúsculas y minúsculas)
        if num_str.endswith(('K', 'k')):
            return float(num_str[:-1]) * 1000
        elif num_str.endswith(('M', 'm')):
            return float(num_str[:-1]) * 1000000
        elif num_str.endswith(('B', 'b')):
            return float(num_str[:-1]) * 1000000000

        # Intentamos convertir el número limpio en float
        try:
            return float(num_str)
        except ValueError:
            print(f"Advertencia: No se pudo convertir el valor '{num_str}' a número.")
            return None
        





        

    