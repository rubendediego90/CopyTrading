from constantes.types import SYMBOLS_VLAD, SYMBOL
import re
from brokers.MetaTrader5_broker import MetaTrader5Broker

class VladSignal:
    def __init__(self, brokerInstance : MetaTrader5Broker):
        self.brokerInstance : MetaTrader5Broker = brokerInstance
        self.RISK = 0.005
        pass
        
    def handle(self,msg,last_cash_balance):
        print('*Vlad*',msg)
        symbol = self.getSymbol(msg)
        FTMO_CONDITION_PERCENTAGE = 4
        can_open_new_position = self.brokerInstance.can_open_new_position(last_cash_balance,FTMO_CONDITION_PERCENTAGE)
        if(symbol == None):
            print('mensaje sin identificar simbolo',msg)
            return
            
        print('El símbolo es:',symbol)
        
        orders_type = self.getOrderType(msg)
        
        if orders_type["hasMoveSL"]:
            print("ACTION - Mover SL")
            self.brokerInstance.mover_stop_loss_be(symbol,"vlad")
            
        if orders_type["hasClosePartial"]:
            print("ACTION - Parcial")
            percentage = self.extraer_porcentaje(msg)
            self.brokerInstance.close_partial(symbol,"vlad",partial=percentage)
            
        if orders_type["hasMoveSL"] or orders_type["hasClosePartial"] or can_open_new_position == False:
            return
        
        if orders_type["hasNewOrder"]:
            print("ACTION - Nueva orden")
            
            valores = self.extraer_valores(msg)
            tpList = [valores['TP1']]
            if(valores['TP2'] != None):tpList.append(valores['TP2'])
            if(valores['TP3'] != None):tpList.append(valores['TP3'])
            self.brokerInstance.handle_order(valores=valores,symbol=symbol,risk=self.RISK,tpList=tpList,nombreStrategy="VLAD")
            return

    def getSymbol(self,msg):
        if SYMBOLS_VLAD.SP500.lower() in msg.lower():
            return SYMBOL.SP500.value
        
        if SYMBOLS_VLAD.NASDAQ.lower() in msg.lower():
            return SYMBOL.NASDAQ.value
        
        if SYMBOLS_VLAD.BTC.lower() in msg.lower() or SYMBOLS_VLAD.BITCOIN.lower() in msg.lower():
            return SYMBOL.BTC.value
        
        if SYMBOLS_VLAD.ETH.lower() in msg.lower():
            return SYMBOL.ETH.value
        
        if SYMBOLS_VLAD.ORO.lower() in msg.lower() or SYMBOLS_VLAD.XAU.lower() in msg.lower():
            return SYMBOL.ORO.value
        
        return None
    
    def getOrderType(self,msg):
        words_be = ["break even", " be ", "muevo", "protejo","mover","moved", "sl a ","stop loss a "]
        words_open = ["tp","sl","#"]
        words_partial = ["tom", "bloquea", "cerrad", "cierr"]

        msg_lower = msg.lower()
        words_be_lower = [p.lower() for p in words_be]
        words_open_lower = [p.lower() for p in words_open]
        words_partial_lower = [p.lower() for p in words_partial]
        
        hasMoveSL = False
        hasNewOrder = False
        hasClosePartial = False

        if any(palabra in msg_lower for palabra in words_be_lower):
            hasMoveSL = True
            
        if all(palabra in msg_lower for palabra in words_open_lower):
            hasNewOrder = True
            
        if any(palabra in msg_lower for palabra in words_partial_lower) and "parcial" in msg_lower and "tp" not in msg_lower:
            hasClosePartial = True
        
        return {
            "hasMoveSL": hasMoveSL,
            "hasNewOrder": hasNewOrder,
            "hasClosePartial": hasClosePartial
        }
        
    #TODO revisar
    def extraer_valores(self, texto):
        patrones = {
            "SL": r"\bSL[:\-]?\s*([\d.,]+[KkMmBb]?)",  # Añadido para manejar 'K', 'M', 'B'
            "TP": r"\bTP[:\-]?\s*([\d.,]+[KkMmBb]?)",
            "TP1": r"\bTP1[:\-]?\s*([\d.,]+[KkMmBb]?)",  
            "TP2": r"\bTP2[:\-]?\s*([\d.,]+[KkMmBb]?)", 
            "TP3": r"\bTP3[:\-]?\s*([\d.,]+[KkMmBb]?)", 
            "1-)": r"\b1-\)\s*([\d.,]+[KkMmBb]?)",
            "2-)": r"\b2-\)\s*([\d.,]+[KkMmBb]?)",
            "3-)": r"\b3-\)\s*([\d.,]+[KkMmBb]?)",
            "Entry": r"\b(?:Entrada|Long|Short)[:\-]?\s*([\d.,]+[KkMmBb]?)",
            "rango":r"([\d.,]+[KkMmBb]?)\s*(?:a|-|~)\s*([\d.,]+[KkMmBb]?)"
        }

        resultados = {
                      'TP': None,
                      'TP1': None,
                      'TP3': None,
                      'TP2': None,
                      '1-)': None,
                      '2-)': None,
                      '3-)': None,
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

        # Ahora, limpiamos (casteamos) los valores extraídos
        for clave, coincidencias in extracciones.items():
            if coincidencias:
                # Si encontramos coincidencias, las limpiamos
                resultados[clave] = [self.limpiar_numero(c) for c in coincidencias if self.limpiar_numero(c) is not None]
            else:
                # Si no encontramos coincidencias, asignamos None
                resultados[clave] = None
                

        # ✅ Filtro para TP: eliminar 1.0 y 2.0 si están presentes
        if 'TP' in resultados and resultados['TP']:
            resultados['TP'] = [v for v in resultados['TP'] if v not in (1.0, 2.0)]

        # Asignación condicional para TP1 y TP2
        if not resultados['TP1']:  # Si TP1 es None o está vacío
            resultados['TP1'] = resultados.get('TP') or resultados.get('1-)')

        if not resultados['TP2']:  # Si TP2 es None o está vacío
            resultados['TP2'] = resultados.get('2-)')
            
        if not resultados['TP3']:  # Si TP3 es None o está vacío
            resultados['TP3'] = resultados.get('3-)')
            
        # Aquí procesamos las listas para devolver solo el primer valor o None si no existen
        for clave in resultados:
            if isinstance(resultados[clave], list) and len(resultados[clave]) > 0:
                # Si es una lista no vacía, asignamos el primer valor
                resultados[clave] = resultados[clave][0]
            elif isinstance(resultados[clave], list) and len(resultados[clave]) == 0:
                # Si la lista está vacía, asignamos None
                resultados[clave] = None
                
        # Comparación entre SL y TP2 para determinar isShort y isLong
        if resultados['SL'] is not None and resultados['TP2'] is not None:
            if resultados['SL'] > resultados['TP2']:
                resultados['isShort'] = True
                resultados['isLong'] = False
            elif resultados['SL'] < resultados['TP2']:
                resultados['isShort'] = False
                resultados['isLong'] = True
            else:
                # En caso de que sean iguales
                resultados['isShort'] = False
                resultados['isLong'] = False
        else:
            # Si alguno de los valores es None, no asignamos isShort o isLong
            resultados['isShort'] = None
            resultados['isLong'] = None

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
        
    def extraer_porcentaje(self,texto):
    # Buscar el número antes del símbolo '%'
        resultado = re.search(r'(\d+)%', texto)
        
        if resultado:
            return int(resultado.group(1))  # Devolver el número como un entero
        else:
            return 50  # Si no se encuentra un porcentaje, devolver None





        

    