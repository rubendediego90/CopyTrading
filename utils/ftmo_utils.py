import re
from store.orders_store import ParameterStore
from constantes.store_properties import STORE_PROPERTIES
from utils.estrategias_config import EstrategiasConfig
from brokers.MetaTrader5_broker import MetaTrader5Broker

class FTMOUtils:
    def __init__(self):
        self.param_store = ParameterStore()
        self.estrategias_config = EstrategiasConfig()

    def filtrar_tps_no_validos(self, comentarios):
        """Filtra los comentarios con TP no válido según la estrategia configurada y devuelve solo aquellos que hayan alcanzado el BE."""
        
        if not comentarios:
            return []
        
        # Ordenar los comentarios de forma ascendente por id y TP
        comentarios_ordenados = sorted(
            comentarios, 
            key=lambda x: (
                re.search(r'_(\d+)_TP(\d+)', x).group(1), 
                int(re.search(r'_(\d+)_TP(\d+)', x).group(2))
            )
        )

        print("comentarios_ordenados", comentarios_ordenados)

        # Diccionario para almacenar los TPs por id
        comentarios_por_id = {}

        # Procesar los comentarios y organizarlos en el diccionario
        for comentario in comentarios_ordenados:
            # Extraemos la estrategia, id y TP del comentario
            match = re.match(r'(?P<estrategia>[A-Z]+)_(?P<id>\d+)_TP(?P<tp>\d+)', comentario, re.IGNORECASE)
            if not match:
                continue  # Si el comentario no coincide con el formato esperado, lo ignoramos

            estrategia = match.group("estrategia").upper()
            tp = int(match.group("tp"))
            id_operacion = match.group("id")
            tp_tope = self.estrategias_config.get(estrategia, "tp_tope")

            # Si el id de operación no está en el diccionario, inicializamos su lista de TPs
            if id_operacion not in comentarios_por_id:
                comentarios_por_id[id_operacion] = {'tps': [], 'comentarios': []}

            # Añadimos el TP y comentario al diccionario correspondiente
            comentarios_por_id[id_operacion]['tps'].append(tp)
            comentarios_por_id[id_operacion]['comentarios'].append(comentario)

        print("comentarios_por_id", comentarios_por_id)

        comentarios_a_devolver = []

        # Procesamos los TPs por id al final
        for id_operacion, data in comentarios_por_id.items():
            tps_por_id = data['tps']
            comentarios_id_actual = data['comentarios']

            # Verificamos si el primer TP (menor) de la operación alcanza el tp_tope
            tp_tope = self.estrategias_config.get(estrategia, "tp_tope")
            if tps_por_id and min(tps_por_id) >= tp_tope:
                comentarios_a_devolver.extend(comentarios_id_actual)

        print("comentarios_a_devolver", comentarios_a_devolver)
        return comentarios_a_devolver

    def obtener_comentarios(self, items):
        """Obtiene los comentarios de las órdenes."""
        return [item['comentario'] for item in items if 'comentario' in item]

    def extraer_base_comentario(self, comentario):
        """Remueve el sufijo _TPn."""
        return re.sub(r'_TP\d+$', '', comentario)

    async def auto_sl(self, brokerInstance: MetaTrader5Broker):
        """Mueve el Stop Loss a Break Even si hay TP inválido y cierra las órdenes pendientes relacionadas."""
        # Obtener órdenes abiertas y pendientes
        orders_pendings = brokerInstance.get_orders_pendings()
        positions_opens = brokerInstance.get_positions_open()

        comentario_pendings_orders = [order.comment for order in orders_pendings]
        comentario_positions_opens = [order.comment for order in positions_opens]
        comentarios_positions_and_orders = comentario_pendings_orders + comentario_positions_opens

        # Paso 1: Filtrar TPs inválidos solo en posiciones abiertas
        comentarios_sin_tp_1 = self.filtrar_tps_no_validos(comentario_positions_opens)
        comentarios_sin_tp_1_sin_duplicados = list(dict.fromkeys(comentarios_sin_tp_1))  # elimina duplicados

        # Paso 2: Mover SL y cerrar pendientes relacionadas
        for comentario in comentarios_sin_tp_1_sin_duplicados:
            # Mover SL de las posiciones con TP inválido
            print("Comentario no válido, mover SL:", comentario)
            positionsFiltered = [pos for pos in positions_opens if pos.comment == comentario]
            for position in positionsFiltered:
                brokerInstance.mover_stop_loss_be_by_position(position)

            # Cerrar órdenes pendientes relacionadas
            base_comentario = self.extraer_base_comentario(comentario)
            orders_pendings_Filtered = [
                order for order in orders_pendings if base_comentario in order.comment
            ]
            for order_pending in orders_pendings_Filtered:
                brokerInstance.close_pending_by_order(order_pending)

        # Paso 3: Limpiar comentarios obsoletos del almacenamiento
        itemsStored = self.param_store.get(STORE_PROPERTIES.ORDERS_OPEN_PENDINGS_LIST.value) or []
        comentarios_stored = self.obtener_comentarios(itemsStored)

        comentarios_obsoletos = [
            item for item in comentarios_stored if item not in comentarios_positions_and_orders
        ]

        self.param_store.remove_from_list(
            STORE_PROPERTIES.ORDERS_OPEN_PENDINGS_LIST.value,
            lambda item: item.get("comentario") in comentarios_obsoletos
        )


