import json
import os
import tempfile

ARCHIVO = "becas.json"
ESTRUCTURA_BASE = {"estudiantes": {}, "academico": {}}


def cargar_datos(ruta: str = ARCHIVO) -> dict:
    if not os.path.exists(ruta):
        return ESTRUCTURA_BASE.copy()

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)

        datos.setdefault("estudiantes", {})
        datos.setdefault("academico", {})
        return datos
    except (json.JSONDecodeError, OSError):
        if os.path.exists(ruta):
            os.replace(ruta, f"{ruta}.bak")
        return ESTRUCTURA_BASE.copy()


def guardar_datos(datos: dict, ruta: str = ARCHIVO) -> bool:
    directorio = os.path.dirname(ruta) or "."
    temp_name = None

    try:
        with tempfile.NamedTemporaryFile(
            "w", delete=False, dir=directorio, encoding="utf-8"
        ) as tf:
            temp_name = tf.name
            json.dump(datos, tf, ensure_ascii=False, indent=2)

        os.replace(temp_name, ruta)
        return True
    except Exception as e:
        if temp_name and os.path.exists(temp_name):
            os.remove(temp_name)
        print(f"Error crítico al guardar datos: {e}")
        return False