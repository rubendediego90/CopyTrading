class EstrategiasConfig:
    def __init__(self):
        # Inicializamos las estrategias dentro del diccionario
        self.estrategias = {
            "VLAD": {
                "riesgo": 0.005,
                "tp_tope": 2,
                "close_pendings_in_new": True,
                "close_opens_in_new": True,
            },
            "SPGV": {
                "riesgo": 0.005,
                "tp_tope": 2,
                "close_pendings_in_new": False,
                "close_opens_in_new": False,
            },
            "SPGP": {
                "riesgo": 0.005,
                "tp_tope": 2,
                "close_pendings_in_new": True,
                "close_opens_in_new": True,
            },
            "TURP": {
                "riesgo": 0.005,
                "tp_tope": 2,
                "close_pendings_in_new": True,
                "close_opens_in_new": True,
            },
        }

    # Método para obtener detalles de una estrategia
    def get(self, nombre_estrategia, atributo):
        # Verificar si la estrategia existe
        if nombre_estrategia in self.estrategias:
            estrategia = self.estrategias[nombre_estrategia]
            # Verificar si el atributo existe en la estrategia
            if atributo in estrategia:
                return estrategia[atributo]
            else:
                return f"El atributo '{atributo}' no existe en la estrategia '{nombre_estrategia}'."
        else:
            return f"La estrategia '{nombre_estrategia}' no existe."