# Inicio de proyecto
import streamlit as st
import pandas as pd

PROMEDIO = 85.0
REPROBADO = 0

# Se reciben los datos academicos, se validan que sean correctos y se registra el semestre del estudiante


def registro_semestre(datos: dict, carnet: str, semestre: str, promedio: float, aprobadas: int, reprobadas: int):
    if carnet not in datos["estudiantes"]:
        return "Su número de carnet no corresponde a ningún estudiante"
    if not semestre.strip():
        return ("Debe específicar su semestre")
    if not (0.0 <= promedio <= 100):
        return "Ingrese un promedio entre 0.0 y 100.0"
    if type(aprobadas) != int or type(reprobadas) != int:
        return "El numero debe ser entero"
    if aprobadas < 0 or reprobadas < 0:
        raise ValueError("El número de asignaturas no puede ser negativo")
    Historial = datos["academico"].setdefault(carnet, [])
    nuevo_registro = {
        "Semestre": semestre,
        "Promedio": promedio,
        "Aprobado": aprobadas,
        "Reprobados": reprobadas
    }
    Historial.append(nuevo_registro)
    return "Se ha registrado su semestre"
