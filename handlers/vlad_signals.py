from constantes.types import SYMBOLS_VLAD, SYMBOL
import re
from brokers.MetaTrader5_broker import MetaTrader5Broker
from utils.common import Common

class VladSignal:
    def __init__(self, brokerInstance : MetaTrader5Broker,comentario, id_order):
        self.brokerInstance : MetaTrader5Broker = brokerInstance
        self.RISK = 0.005
        self.comentario = comentario
        self.id_order = id_order
        pass
        
    def handle(self,msg):
        print('*Vlad*',msg)
        symbol = self.getSymbol(msg)
        if(symbol == None):
            print('mensaje sin identificar simbolo',msg)
            return
            
        self.brokerInstance.setSymbolInfo(symbol)
        print('El símbolo es:',symbol)
        
        orders_type = self.getOrderType(msg)
        
        print("orders_type",orders_type)
        
        if orders_type["hasMoveSL"]:
            print("ACTION - Mover SL")
            self.brokerInstance.mover_stop_loss_be_by_symbol(symbol=symbol,strategiaName=self.comentario)
            
        if orders_type["hasClosePartial"]:
            print("ACTION - Parcial")
            percentage = Common.extraer_porcentaje(msg)
            self.brokerInstance.close_partial(symbol,self.comentario,partial=percentage)
            
        if orders_type["hasMoveSL"] or orders_type["hasClosePartial"]:
            return
        
        if orders_type["hasNewOrder"]:
            print("ACTION - Nueva orden")
            
            valores = self.extraer_valores(msg)
            tpList = [valores['TP1']]
            if(valores['TP2'] != None):tpList.append(valores['TP2'])
            if(valores['TP3'] != None):tpList.append(valores['TP3'])
            self.brokerInstance.handle_order(valores=valores,symbol=symbol,risk=self.RISK,tpList=tpList,nombreStrategy=self.comentario,id_order=self.id_order)
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
                resultados[clave] = [Common.limpiar_numero(c) for c in coincidencias if Common.limpiar_numero(c) is not None]
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
    






        

    