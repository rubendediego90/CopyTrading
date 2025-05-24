import csv
import os

class Export:
    def export_as_cvs(self,path,listado,nombre_fichero):

        # Nombre completo del archivo con ruta
        nombre_archivo = os.path.join(path, nombre_fichero)

        # Exportar a CSV
        with open(nombre_archivo, mode='w', newline='', encoding='utf-8') as archivo:
            campos = listado[0].keys()
            writer = csv.DictWriter(archivo, fieldnames=campos)
            writer.writeheader()
            writer.writerows(listado)