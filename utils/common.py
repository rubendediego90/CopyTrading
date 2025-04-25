import re

class Common:
    def limpiar_numero(self, num_str):
        """
        Limpia y convierte un string numérico en float.
        Soporta:
        - Separadores de miles con punto o coma
        - Decimales con coma o punto
        - Sufijos K, M, B
        - Formatos como 1.234,56 o 1,234.56
        """

        if not isinstance(num_str, str):
            num_str = str(num_str)

        num_str = num_str.strip().replace(" ", "")  # Elimina espacios

        # Detectar sufijos
        multiplicador = 1
        if num_str[-1] in ('K', 'k'):
            multiplicador = 1_000
            num_str = num_str[:-1]
        elif num_str[-1] in ('M', 'm'):
            multiplicador = 1_000_000
            num_str = num_str[:-1]
        elif num_str[-1] in ('B', 'b'):
            multiplicador = 1_000_000_000
            num_str = num_str[:-1]

        # Detectar y normalizar formato europeo (1.234,56) o americano (1,234.56)
        if re.match(r"^\d{1,3}(\.\d{3})+,\d+$", num_str):  # Formato europeo
            num_str = num_str.replace(".", "").replace(",", ".")
        elif re.match(r"^\d{1,3}(,\d{3})+\.\d+$", num_str):  # Formato americano
            num_str = num_str.replace(",", "")
        elif "," in num_str and "." not in num_str:
            num_str = num_str.replace(",", ".")

        try:
            return float(num_str) * multiplicador
        except ValueError:
            print(f"⚠️ No se pudo convertir el valor '{num_str}' a número.")
            return None
        
    def extraer_porcentaje(self,texto):
    # Buscar el número antes del símbolo '%'
        resultado = re.search(r'(\d+)%', texto)
        
        if resultado:
            return int(resultado.group(1))  # Devolver el número como un entero
        else:
            return 50  # Si no se encuentra un porcentaje, devolver None