from constantes.types import SYMBOL
import re
from brokers.MetaTrader5_broker import MetaTrader5Broker
from utils.common import Common

class JohanGoldSignal:
    def __init__(self, brokerInstance : MetaTrader5Broker, comentario,id_order):
        self.brokerInstance : MetaTrader5Broker = brokerInstance
        self.comentario = comentario
        self.id_order = id_order
        pass
        
    def handle(self,msg):
        print('*Joghan*',msg)
        symbol = SYMBOL.ORO.value
            
        self.brokerInstance.setSymbolInfo(symbol)
        print('El símbolo es:',symbol)
        
        valores = self.extraer_valores(msg)
        tpList = valores['TP']
        
        print("valors",valores)
        
        self.brokerInstance.handle_order(valores=valores,symbol=symbol,tpList=tpList,nombreStrategy=self.comentario,
                                            id_order=self.id_order,price_open=valores["OpenPrice"],riskParam=valores["Risk"]/100)
        return
        

    def extraer_valores(self, texto):
        texto_limpio = texto.lower().strip()

        patrones = {
            "SL": r"\bsl[:\s]*([\d.,]+[KkMmBb]?)",
            "TP": r"\bTP[:\s]*([\d.,]+[KkMmBb]?)",
            "Risk": r"\brisk[:\s]*([\d.,]+)%?"
        }

        resultados = {
            'TP': None,
            'OpenPrice':None,
            'SL': None,
            'Risk': None,
            'Type': None,
            'rango_superior':None,
            'rango_inferior':None,
            'isLong':None,
            'isShort':None,
        }

        # 🧠 Función para interpretar valores como 05 o 01 como 0.5 o 0.1
        def interpretar_risk(valor):
            try:
                valor = valor.replace('%', '').strip()
                if valor.isdigit():
                    if len(valor) == 2 and valor.startswith('0'):
                        return float(f"0.{valor[-1]}")
                    return float(valor)
                elif '.' in valor or ',' in valor:
                    return float(valor.replace(',', '.'))
                return None
            except:
                return None

        # 🧪 Extraer SL, TP y Risk
        extracciones = {}
        for clave, patron in patrones.items():
            coincidencias = re.findall(patron, texto_limpio, flags=re.IGNORECASE)
            extracciones[clave] = coincidencias if coincidencias else None

        # 🚿 Limpiar resultados
        for clave, coincidencias in extracciones.items():
            if coincidencias:
                if clave == "Risk":
                    resultados[clave] = interpretar_risk(coincidencias[0])
                else:
                    resultados[clave] = [Common.limpiar_numero(c) for c in coincidencias if Common.limpiar_numero(c) is not None]
            else:
                resultados[clave] = None

        # ✅ Simplificar SL
        if isinstance(resultados['SL'], list) and resultados['SL']:
            resultados['SL'] = resultados['SL'][0]

        # ✅ Validar TP (puede haber múltiples)
        if isinstance(resultados['TP'], list) and not resultados['TP']:
            resultados['TP'] = None

        ordenes = {
            "buy limit": "BUY_LIMIT",
            "buy stop": "BUY_STOP",
            "sell limit": "SELL_LIMIT",
            "sell stop": "SELL_STOP"
        }

        for key in ordenes:
            if key in texto_limpio:
                resultados['Type'] = ordenes[key]
                break

        ordenes_regex = {
            r"buy limit\s+([\d.,]+)": "BUY_LIMIT",
            r"buy stop\s+([\d.,]+)": "BUY_STOP",
            r"sell limit\s+([\d.,]+)": "SELL_LIMIT",
            r"sell stop\s+([\d.,]+)": "SELL_STOP"
        }

        for patron, tipo in ordenes_regex.items():
            match = re.search(patron, texto_limpio)
            if match:
                resultados['Type'] = tipo
                open_price_raw = match.group(1)
                resultados['OpenPrice'] = Common.limpiar_numero(open_price_raw)
                break

        return resultados