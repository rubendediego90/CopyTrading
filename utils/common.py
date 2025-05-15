import re

class Common:
    def __init__(self):
        pass
    
    def limpiar_numero(num_str):
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
        

    '''
    entry_prices = [3185,3190,3205, 3210]

    long
    [0,0,1,1]

    short
    [1,1,0,0]
    
    lista de {entrada:3200,distribucion:2,entrada:3300,distribucion:1} entraremos con el doble en la primera
    '''
    def cal_entries_distribution(valores,distribution_param):
        PRICE_MIN = valores["rango_inferior"]
        PRICE_MAX = valores["rango_superior"]
        isLong = valores["isLong"]
        isShort = valores["isShort"]
        
        #invertir el array distribution
        distribution_short = distribution_param[::-1]
        distribution_long = distribution_param
        distribution_longitud = len(distribution_long)

        # === CALCULAR PRECIOS DE ENTRADA ===
        step = (PRICE_MAX - PRICE_MIN) / (distribution_longitud - 1)
        entry_prices = [round(PRICE_MIN + i * step, 2) for i in range(distribution_longitud)]
        
        #numeros ordenados de menor a mayor
        entry_prices_sorted = sorted(entry_prices)
        
        distribution = distribution_short if isShort else distribution_long
        
        entry_prices_mapped = [{"entry": entry_prices_sorted[i], "distribution": distribution[i]} for i in range(len(entry_prices_sorted))]
        
        #si llega al extremo contrario no seria buena señal, se elimina para distribuir mejor los lotes
        
        #cuenta cuantos ceros hay para borrarlos
        num_position_to_delete = distribution.count(0)
        if entry_prices_mapped:
            if isShort:
                # Eliminar los diccionarios con los valores más altos de 'entry'
                for _ in range(num_position_to_delete):
                    # Encontrar el diccionario con el valor máximo de 'entry'
                    max_entry = max(entry_prices_mapped, key=lambda x: x['entry'])
                    entry_prices_mapped.remove(max_entry)
            elif isLong:
                # Eliminar los diccionarios con los valores más bajos de 'entry'
                for _ in range(num_position_to_delete):
                    # Encontrar el diccionario con el valor mínimo de 'entry'
                    min_entry = min(entry_prices_mapped, key=lambda x: x['entry'])
                    entry_prices_mapped.remove(min_entry)
        print("entry_prices_mapped",entry_prices_mapped)
        return entry_prices_mapped