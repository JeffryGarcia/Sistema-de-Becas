# =============================================================================
# archivos.py -> Módulo de PERSISTENCIA Y MANEJO DE ARCHIVOS JSON
#
# Este módulo se encarga de gestionar la lectura y el almacenamiento seguro 
# de la información del sistema utilizando archivos JSON y archivos temporales 
# para prevenir la corrupción de datos.
# =============================================================================

import json     # Importación del módulo nativo json para la codificación y decodificación de datos estructurados
import os       # Importación del módulo os para interactuar con el sistema operativo (rutas, archivos, respaldos)
import tempfile # Importación del módulo tempfile para crear archivos temporales seguros durante la escritura

# Definición de constantes globales: nombre predeterminado del archivo de base de datos local
ARCHIVO = "becas.json"
# Estructura de datos base inicial obligatoria en caso de que el archivo no exista o se corrompa
ESTRUCTURA_BASE = {"estudiantes": {}, "academico": {}}


# Función encargada de cargar y recuperar los datos persistidos desde el archivo JSON especificado
def cargar_datos(ruta: str = ARCHIVO) -> dict:
    # Condición de guarda: si el archivo en la ruta dada no existe en disco, retorna una copia de la estructura base vacía
    if not os.path.exists(ruta):
        return ESTRUCTURA_BASE.copy()

    try:
        # Apertura del archivo en modo lectura ("r") con codificación UTF-8 para soportar tildes y caracteres especiales
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)   # Carga y deserializa el contenido JSON en un diccionario de Python

        # Garantiza mediante setdefault que las claves principales siempre existan, evitando errores si el JSON está incompleto
        datos.setdefault("estudiantes", {})
        datos.setdefault("academico", {})
        return datos
    except (json.JSONDecodeError, OSError):
        # Manejo robusto de errores: si el archivo está corrupto (JSON malformado) o hay un error de E/S (OSError)...
        if os.path.exists(ruta):
            os.replace(ruta, f"{ruta}.bak")   # ...crea un respaldo renombrando el archivo dañado con la extensión .bak
        # Retorna la estructura base limpia para evitar que la aplicación colapse
        return ESTRUCTURA_BASE.copy()


# Función encargada de guardar de forma segura los datos en el archivo JSON utilizando un archivo temporal
def guardar_datos(datos: dict, ruta: str = ARCHIVO) -> bool:
    # Obtiene el directorio padre de la ruta de destino; si está vacío, utiliza el directorio actual (".")
    directorio = os.path.dirname(ruta) or "."
    temp_name = None

    try:
        # Creación de un archivo temporal seguro en el mismo directorio para evitar sobreescribir directamente el archivo final
        with tempfile.NamedTemporaryFile(
            "w", delete=False, dir=directorio, encoding="utf-8"
        ) as tf:
            temp_name = tf.name   # Almacena la ruta temporal única asignada al archivo
            # Serializa el diccionario de datos a formato JSON con indentación de 2 espacios y soporte para caracteres Unicode
            json.dump(datos, tf, ensure_ascii=False, indent=2)

        # Operación atómica de reemplazo: sustituye el archivo original por el archivo temporal de manera segura
        os.replace(temp_name, ruta)
        return True   # Retorna True indicando que el guardado fue exitoso
    except Exception as e:
        # Manejo de excepciones: si ocurre cualquier fallo durante el proceso de escritura o reemplazo...
        if temp_name and os.path.exists(temp_name):
            os.remove(temp_name)   # ...elimina el archivo temporal huérfano si llegó a crearse
        print(f"Error crítico al guardar datos: {e}")   # Muestra un mensaje descriptivo del error por consola
        return False   # Retorna False indicando que el guardado falló