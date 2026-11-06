# =============================================================================
# archivos.py -> Módulo de PERSISTENCIA Y MANEJO DE ARCHIVOS JSON
#
# Lee y guarda la información del sistema en un archivo JSON, usando un archivo
# temporal para prevenir la corrupción de datos.
#
# Marcas de los comentarios:
#   # NUEVO:  -> algo que se agregó en esta versión
#   # CAMBIO: -> algo que ya existía y se modificó
# =============================================================================

import copy    # NUEVO: para copias profundas de la estructura base
import json
import os
import tempfile
import time    # NUEVO: para nombrar los respaldos con fecha y hora

ARCHIVO = "becas.json"
ESTRUCTURA_BASE = {"estudiantes": {}, "academico": {}}


# NUEVO: Devuelve una copia PROFUNDA de la estructura base.
#        Antes se usaba ESTRUCTURA_BASE.copy() (copia superficial): los diccionarios internos
#        se compartían, así que al agregar un estudiante se modificaba la constante original.
def _estructura_base() -> dict:
    return copy.deepcopy(ESTRUCTURA_BASE)


# NUEVO: Comprueba que los datos tengan la forma esperada (evita errores si el JSON es válido pero está mal formado
#        o fue editado a mano: una lista en vez de un diccionario, historial que no es lista, etc.)
def _estructura_valida(datos) -> bool:
    if not isinstance(datos, dict):
        return False
    estudiantes = datos.get("estudiantes", {})
    academico = datos.get("academico", {})
    if not isinstance(estudiantes, dict) or not isinstance(academico, dict):
        return False
    if not all(isinstance(e, dict) for e in estudiantes.values()):
        return False
    for historial in academico.values():
        if not isinstance(historial, list) or not all(isinstance(r, dict) for r in historial):
            return False
    return True


# NUEVO: Renombra el archivo dañado con fecha y hora (antes un .bak nuevo pisaba al anterior y se perdía el respaldo previo)
def _respaldar(ruta: str) -> None:
    destino = f"{ruta}.{time.strftime('%Y%m%d-%H%M%S')}.bak"
    try:
        os.replace(ruta, destino)
    except OSError:
        pass   # Si ni siquiera se puede renombrar, se continúa con la estructura base


def cargar_datos(ruta: str = ARCHIVO) -> dict:
    if not os.path.exists(ruta):
        return _estructura_base()   # CAMBIO: copia profunda

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
    # CAMBIO: ValueError cubre JSON malformado y también archivos con codificación inválida (UnicodeDecodeError)
    except (ValueError, OSError):
        _respaldar(ruta)
        return _estructura_base()

    # NUEVO: JSON válido pero con estructura incorrecta -> se trata como archivo dañado
    if not _estructura_valida(datos):
        _respaldar(ruta)
        return _estructura_base()

    datos.setdefault("estudiantes", {})
    datos.setdefault("academico", {})
    return datos


def guardar_datos(datos: dict, ruta: str = ARCHIVO) -> bool:
    # NUEVO: nunca se escribe en disco una estructura inválida
    if not _estructura_valida(datos):
        print("Error crítico al guardar datos: la estructura de datos no es válida")
        return False

    directorio = os.path.dirname(ruta) or "."
    temp_name = None

    try:
        with tempfile.NamedTemporaryFile(
            "w", delete=False, dir=directorio, encoding="utf-8", suffix=".tmp"
        ) as tf:
            temp_name = tf.name
            json.dump(datos, tf, ensure_ascii=False, indent=2)
            # NUEVO: fuerza la escritura real a disco antes de reemplazar el archivo original
            tf.flush()
            os.fsync(tf.fileno())

        os.replace(temp_name, ruta)
        return True
    except Exception as e:
        if temp_name and os.path.exists(temp_name):
            os.remove(temp_name)
        print(f"Error crítico al guardar datos: {e}")
        return False


# NUEVO: Guarda y, si falla, muestra un error visible y detiene la ejecución.
#        Antes los módulos ignoraban el True/False de guardar_datos y el usuario veía
#        "registrado correctamente" aunque nada se hubiera guardado en el archivo.
def guardar_o_detener(datos: dict) -> None:
    if not guardar_datos(datos):
        import streamlit as st   # Importación local para que este módulo siga siendo independiente de Streamlit
        st.error("No se pudieron guardar los cambios en el archivo. "
                 "Revisa los permisos y el espacio en disco e inténtalo de nuevo.")
        st.stop()