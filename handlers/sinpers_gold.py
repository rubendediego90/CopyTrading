from constantes.types import SYMBOLS_SNIPERS_GOLD, SYMBOL
import re
from brokers.MetaTrader5_broker import MetaTrader5Broker
from utils.common import Common

class SnipersGold:
    def __init__(self, brokerInstance : MetaTrader5Broker, comentario,id_order):
        self.brokerInstance : MetaTrader5Broker = brokerInstance
        self.comentario = comentario
        self.id_order = id_order
        pass
        
    def handle(self,msg):
        print('*Snipers Gold*',msg)
        symbol = self.getSymbol(msg)
            
        self.brokerInstance.setSymbolInfo(symbol)
        print('El símbolo es:',symbol)
        
        orders_type = self.getOrderType(msg)
        
        print("order typs",orders_type)
               
        if orders_type["hasNewOrder"]:
            print("ACTION - Nueva orden")
            
            valores = self.extraer_valores(msg)
            tpList = valores['TP']
            print("tpList",tpList)
            entries_distribution = Common.cal_entries_distribution(valores,distribution_param=[0,0,1,1,2])
            self.brokerInstance.handle_order(valores=valores,symbol=symbol,tpList=tpList,
                                             nombreStrategy=self.comentario,id_order=self.id_order,entry_prices_distribution=entries_distribution)
            return
        
        if orders_type["hasMoveSL"]:
            print("ACTION - Mueve stop loss")
            sl_value = self.getNewSlValue(msg)
            self.brokerInstance.mover_stop_loss_be_by_symbol(symbol=symbol,strategiaName=self.comentario, newPrice=sl_value)
            return
        
        if orders_type["hasClosePendings"]:
            print("ACTION - Cierra pendientes")
            self.brokerInstance.close_pending(symbol=SYMBOL.ORO.value,nombre_estrategia=self.comentario)
            return

    def getSymbol(self,msg):
        if SYMBOLS_SNIPERS_GOLD.XAU.lower() in msg.lower() or SYMBOLS_SNIPERS_GOLD.XAUUSD.lower() in msg.lower() or SYMBOLS_SNIPERS_GOLD.GOLD.lower() in msg.lower():
            return SYMBOL.ORO.value
        
        if SYMBOLS_SNIPERS_GOLD.BTC.lower() in msg.lower() or SYMBOLS_SNIPERS_GOLD.BITCOIN.lower() in msg.lower():
            return SYMBOL.BTC.value
        
        return None
    

    def getNewSlValue(self, msg):
        # Usamos re.IGNORECASE para no distinguir entre mayúsculas y minúsculas
        coincidencia = re.search(r" sl to\s+(\d+)", msg, re.IGNORECASE)
        if coincidencia:
            return int(coincidencia.group(1))
        return None
        
    def getOrderType(self,msg):
        words_open = ["tp","entry","sl"]
        words_move_sl = ["sl","move", "to"]
        #words_delete_pendings_1 = ["rabooooo"]
        words_delete_pendings_1 = ["tp1//","pips"]
        words_delete_pendings_2 = ["tp2//","pips"]

        msg_lower = msg.lower()
        words_open_lower = [p.lower() for p in words_open]
        words_close_pendings_1_lower = [p.lower() for p in words_delete_pendings_1]
        words_close_pendings_2_lower = [p.lower() for p in words_delete_pendings_2]
        words_move_sl_lower = [p.lower() for p in words_move_sl]
        
        hasNewOrder = False
        hasMoveSL = False
        hasClosePendings = False

           
        if all(palabra in msg_lower for palabra in words_open_lower):
            hasNewOrder = True
            
        if all(palabra in msg_lower for palabra in words_move_sl_lower):
            hasMoveSL = True
            
        if (all(palabra in msg_lower for palabra in words_close_pendings_1_lower) or
            all(palabra in msg_lower for palabra in words_close_pendings_2_lower)):
            hasClosePendings = True
             
        return {
            "hasNewOrder": hasNewOrder,
            "hasMoveSL": hasMoveSL,
            "hasClosePendings": hasClosePendings,
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