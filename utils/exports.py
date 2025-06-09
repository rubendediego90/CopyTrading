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
            
    def export_as_txt(self, path, lines, nameFile):
        # Crear la ruta completa (usando 'os.path.join' para asegurarse de que sea compatible con cualquier sistema operativo)
        file_path = os.path.join(path, f"{nameFile}.txt")
        
        # Verificar si el directorio 'path' existe, si no, crearlo
        if not os.path.exists(path):
            os.makedirs(path)  # Crear el directorio si no existe
        
        # Abrir el archivo en modo escritura ('w')
        with open(file_path, "w") as file:
            # Escribir las líneas en el archivo
            file.writelines(linea + "\n" for linea in lines)