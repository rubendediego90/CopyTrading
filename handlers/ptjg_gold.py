from constantes.types import PTJG_GOLD, SYMBOL
import re
from brokers.MetaTrader5_broker import MetaTrader5Broker
from utils.common import Common

class PtjgGold:
    def __init__(self, brokerInstance : MetaTrader5Broker, comentario):
        self.brokerInstance : MetaTrader5Broker = brokerInstance
        self.RISK = 0.005
        self.comentario = comentario
        pass
        
    def handle(self,msg,last_cash_balance):
        print('*Snipers Gold*',msg)
        symbol = self.getSymbol(msg)
        FTMO_CONDITION_PERCENTAGE = 4
        can_open_new_position = self.brokerInstance.can_open_new_position(last_cash_balance,FTMO_CONDITION_PERCENTAGE)
        if(symbol == None):
            print('mensaje sin identificar simbolo',msg)
            return
            
        self.brokerInstance.setSymbolInfo(symbol)
        print('El símbolo es:',symbol)
        
        orders_type = self.getOrderType(msg)
        
        print("order typs",orders_type)
        
        if can_open_new_position == False:
            return
        
        if orders_type["hasNewOrder"]:
            print("ACTION - Nueva orden")
            
            valores = self.extraer_valores(msg)
            tpList = valores['TP']
            print("tpList",tpList)
            print("valores",valores)
            self.brokerInstance.handle_order(valores=valores,symbol=symbol,risk=self.RISK,tpList=tpList,nombreStrategy=self.comentario)
            return
        
        if orders_type["hasMoveSL"]:
            print("ACTION - Mueve stop loss")
            self.brokerInstance.mover_stop_loss_be(symbol=symbol,comentario_buscado=self.comentario)
            return
        
        if orders_type["hasClosePendings"]:
            print("ACTION - Cierra pendientes")
            self.brokerInstance.close_pending(symbol=symbol,comentario_buscado=self.comentario)
            return

    def getSymbol(self, msg):
        msg = msg.lower()
        if (
            PTJG_GOLD.XAU.lower() in msg or 
            PTJG_GOLD.XAUUSD.lower() in msg or
            PTJG_GOLD.ORO.lower() in msg or
            PTJG_GOLD.GOLD.lower() in msg
        ):
            return SYMBOL.ORO.value
        return None
    
    def getOrderType(self,msg):
        words_open = ["tp","ahora","sl"]

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
            "Entry": r"\b(?:ahora)[:\-]?\s*([\d.,]+[KkMmBb]?)",
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





        

    