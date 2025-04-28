import pickle
import os

class ParameterStore:
    def __init__(self, filename='parameters.pkl'):
        self.filename = filename
        self.parameters = self._load_parameters()

    # Cargar los parámetros desde el archivo (si existe)
    def _load_parameters(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'rb') as f:
                    return pickle.load(f)
            except (EOFError, pickle.UnpicklingError):
                return {}
        return {}

    # Guardar los parámetros en el archivo
    def _save_parameters(self):
        with open(self.filename, 'wb') as f:
            pickle.dump(self.parameters, f)

    # Obtener un parámetro específico
    def get(self, key, default=None):
        return self.parameters.get(key, default)

    # Establecer un valor para una clave específica
    def set(self, key, value):
        self.parameters[key] = value
        self._save_parameters()

    # Mostrar todos los parámetros
    def get_all(self):
        return self.parameters

    # Establecer múltiples parámetros a la vez
    def set_all(self, new_parameters):
        self.parameters.update(new_parameters)
        self._save_parameters()

    # ✅ Añadir una orden a la lista de una estrategia
    def add_to_list(self, key, item):
        if key not in self.parameters:
            self.parameters[key] = []
        self.parameters[key].append(item)
        self._save_parameters()

    # ✅ Eliminar una orden de la lista según una condición
    def remove_from_list(self, key, filter_func):
        if key in self.parameters:
            original = self.parameters[key]
            filtered = [item for item in original if not filter_func(item)]
            self.parameters[key] = filtered
            self._save_parameters()

    # ✅ Vaciar la lista de una estrategia
    def clear_list(self, key):
        if key in self.parameters:
            self.parameters[key] = []
            self._save_parameters()