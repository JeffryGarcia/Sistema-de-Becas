# =============================================================================
# carreras.py -> Catálogo de CARRERAS de la UNI (módulo NUEVO)
#
# Una sola lista oficial que usan Estudiantes (para elegir la carrera) y
# Consulta de becas (para separar y contar por carrera).
#
# canonica() reconoce también carreras escritas a mano en registros anteriores
# ("Ingenieria Computacion", "ingeniería en sistemas"...) y las asocia con su
# nombre oficial, ignorando tildes, mayúsculas y palabras como "en" o "de".
# =============================================================================

import re
import unicodedata

CARRERAS = [
    "Arquitectura",
    "Ingeniería en Agronomía / Agrícola",
    "Ingeniería Agroindustrial",
    "Ingeniería Civil",
    "Ingeniería en Computación",
    "Ingeniería Eléctrica",
    "Ingeniería Electrónica",
    "Ingeniería en Economía y Negocios",
    "Ingeniería Industrial",
    "Ingeniería Mecánica",
    "Ingeniería Mecatrónica",
    "Ingeniería de Minas",
    "Ingeniería Química",
    "Ingeniería Robótica",
    "Ingeniería de Sistemas",
    "Ingeniería en Telecomunicaciones",
]

# Otras formas habituales de escribir una carrera -> nombre oficial
ALIAS = {
    "Ingeniería en Agronomía": "Ingeniería en Agronomía / Agrícola",
    "Ingeniería Agronómica": "Ingeniería en Agronomía / Agrícola",
    "Ingeniería Agrícola": "Ingeniería en Agronomía / Agrícola",
}

_PALABRAS_VACIAS = {"en", "de", "del", "la", "el", "y", "e"}


# Convierte un texto en un conjunto de palabras sin tildes, en minúsculas y sin palabras de relleno
def _clave(texto) -> frozenset:
    t = unicodedata.normalize("NFD", str(texto).lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return frozenset(p for p in re.findall(r"[a-z0-9]+", t) if p not in _PALABRAS_VACIAS)


_INDICE = {_clave(c): c for c in CARRERAS}
_INDICE.update({_clave(alias): oficial for alias, oficial in ALIAS.items()})


# Devuelve el nombre oficial de la carrera o None si el texto no corresponde a ninguna del catálogo
def canonica(texto):
    return _INDICE.get(_clave(texto))

