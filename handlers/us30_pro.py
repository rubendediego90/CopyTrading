from constantes.types import US30PRO, SYMBOL
import re
from brokers.MetaTrader5_broker import MetaTrader5Broker
from utils.common import Common

class US30ProSignal:
    def __init__(self, brokerInstance : MetaTrader5Broker, comentario,id_order):
        self.brokerInstance : MetaTrader5Broker = brokerInstance
        self.comentario = comentario
        self.id_order = id_order
        pass
        
    def handle(self,msg):
        print('*US 30 PRO*',msg)
        symbol = self.getSymbol(msg)
        if(symbol == None):
            print('mensaje sin identificar simbolo',msg)
            return
            
        self.brokerInstance.setSymbolInfo(symbol)
        print('El símbolo es:',symbol)
        
        orders_type = self.getOrderType(msg)
        
        if orders_type["hasNewOrder"]:
            print("ACTION - Nueva orden")
            
            valores = self.extraer_valores(msg)
            tpList = valores['TP']
                       
            valores = Common.setRange(valores,percentage=20)
            entries_distribution = Common.cal_entries_distribution(valores,distribution_param=[1,1,1])
            print("entries_distribution",entries_distribution)
            self.brokerInstance.handle_order(valores=valores,symbol=symbol,tpList=tpList,nombreStrategy=self.comentario,
                                             id_order=self.id_order,entry_prices_distribution=entries_distribution)
            return
        

    def getSymbol(self, msg):
        msg = msg.lower()
        if (
            US30PRO.US30.lower() in msg
        ):
            return SYMBOL.US30.value
        return None
    
    def getOrderType(self,msg):
        words_open = ["tp","sl"]

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
            "SL": r"\bSL\s+([\d.,]+[KkMmBb]?)",
            "TP": r"\bTP\s+([\d.,]+[KkMmBb]?)",
            "Entry": r"\b(?:|BUY|SELL)\s+([\d.,]+[KkMmBb]?)",
        }

        resultados = {
                      'TP': None,
                      'SL': None,
                      'isShort':None,
                      'isLong':None,
                      'rango_inferior':None,
                      'rango_superior':None,
                      'Entry':None,
                      }
        

        # Primero, extraemos las coincidencias sin hacer ningún casteo
        extracciones = {}
        for clave, patron in patrones.items():
            coincidencias = re.findall(patron, texto, flags=re.IGNORECASE)
            extracciones[clave] = coincidencias if coincidencias else None
            
        # Ahora, limpiamos (casteamos) los valores extraídos
        for clave, coincidencias in extracciones.items():
            if coincidencias:
                # Si encontramos coincidencias, las limpiamos
                resultados[clave] = [Common.limpiar_numero(c) for c in coincidencias if Common.limpiar_numero(c) is not None]
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





        

    