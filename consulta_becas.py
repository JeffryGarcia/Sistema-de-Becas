# =============================================================================
# consulta_becas.py -> Módulo de CONSULTA DE BECAS (Jeffry)
#
# Este módulo SOLO LEE los datos (no modifica nada). Usa:
#   datos["estudiantes"] = { "carnet (texto)": {Nombre, Edad, carnet, carrera, correo} }
#   datos["academico"]   = { "carnet (texto)": [ {Semestre, Promedio, Aprobado, Reprobados}, ... ] }
#
# Regla de la beca (viene de academico.py):
#   Un estudiante TIENE beca si en su ÚLTIMO semestre registrado
#   su promedio es >= PROMEDIO y sus reprobadas son <= REPROBADO.
#
# La estructura de la ficha está en plantillas/ficha.html y los colores en style.css
# =============================================================================

import html
from pathlib import Path

import streamlit as st
import pandas as pd

from academico import PROMEDIO, REPROBADO

# Carpeta donde está este archivo (para encontrar la plantilla HTML)
CARPETA = Path(__file__).parent

# Clase de color (definida en style.css) que le toca a cada estado
CLASES = {"Con beca": "ok", "Sin beca": "no", "Sin registro": "na"}


# Revisa el historial de un estudiante y devuelve (estado, motivo).
# El estado puede ser: "Con beca", "Sin beca" o "Sin registro".
def estado_beca(historial):
    # Si no tiene semestres registrados, no se puede evaluar
    if not historial:
        return "Sin registro", "Aún no tiene semestres registrados."

    # Se evalúa con el último semestre registrado
    ultimo = historial[-1]

    # Juntamos los motivos por los que NO cumpliría
    motivos = []
    if ultimo["Promedio"] < PROMEDIO:
        motivos.append(f"su promedio ({ultimo['Promedio']}) es menor a {PROMEDIO}")
    if ultimo["Reprobados"] > REPROBADO:
        motivos.append(f"tiene {ultimo['Reprobados']} asignatura(s) reprobada(s) (máximo {REPROBADO})")

    # Si hay motivos, no cumple; si no hay ninguno, sí cumple
    if motivos:
        return "Sin beca", "No cumple porque " + " y ".join(motivos) + "."
    return "Con beca", "Cumple los requisitos en su último semestre."


# Lo que se ve en la página "Consulta de becas"
def modulo_consulta_becas(datos):
    st.title("Consulta de becas")

    # Si no hay estudiantes, no hay nada que consultar
    if not datos["estudiantes"]:
        st.info("No hay estudiantes registrados.")
        return

    # Armamos una fila por estudiante con su estado de beca
    filas = []
    for carnet, estudiante in datos["estudiantes"].items():
        historial = datos["academico"].get(carnet, [])
        estado, motivo = estado_beca(historial)
        filas.append({
            "Carnet": estudiante["carnet"],
            "Nombre": estudiante["Nombre"],
            "Carrera": estudiante["carrera"],
            "Semestres": len(historial),
            "Último promedio": historial[-1]["Promedio"] if historial else None,
            "Estado": estado,
        })

    # Dos pestañas: resumen de todos y consulta de un solo estudiante
    tab_resumen, tab_individual = st.tabs(["Resumen general", "Consulta individual"])

    # ---------- Pestaña: resumen general ----------
    with tab_resumen:
        st.subheader("Estado de becas de todos los estudiantes")
        st.caption(f"Requisitos: promedio de {PROMEDIO} o más y máximo {REPROBADO} asignaturas reprobadas.")

        # Contamos cuántos estudiantes hay en cada estado
        conteo = {"Con beca": 0, "Sin beca": 0, "Sin registro": 0}
        for fila in filas:
            conteo[fila["Estado"]] += 1

        # Tres tarjetas de colores (verde, rojo, gris), una por estado
        columnas = st.columns(3)
        for columna, estado in zip(columnas, conteo):
            columna.markdown(
                f'<div class="stat stat-{CLASES[estado]}"><span>{estado}</span><strong>{conteo[estado]}</strong></div>',
                unsafe_allow_html=True,
            )

        st.write("")  # espacio en blanco

        # Barra de progreso: porcentaje de estudiantes evaluados que tienen beca
        evaluados = conteo["Con beca"] + conteo["Sin beca"]
        if evaluados > 0:
            porcentaje = conteo["Con beca"] / evaluados
            st.progress(
                porcentaje,
                text=f"{conteo['Con beca']} de {evaluados} estudiantes evaluados cumplen los requisitos ({porcentaje:.0%})",
            )

        st.write("")

        # Filtros: por estado (izquierda) y por nombre o carnet (derecha)
        col_filtro, col_buscar = st.columns([2, 1])
        filtro = col_filtro.radio(
            "Mostrar", ["Todos", "Con beca", "Sin beca", "Sin registro"], horizontal=True
        )
        buscar = col_buscar.text_input("Buscar", placeholder="Nombre o carnet")

        # Nos quedamos solo con las filas que cumplen los filtros
        filas_filtradas = []
        for fila in filas:
            coincide_estado = filtro == "Todos" or fila["Estado"] == filtro
            coincide_texto = buscar.lower() in fila["Nombre"].lower() or buscar in str(fila["Carnet"])
            if coincide_estado and coincide_texto:
                filas_filtradas.append(fila)

        if filas_filtradas:
            st.dataframe(
                pd.DataFrame(filas_filtradas),
                width="stretch",
                hide_index=True,
                column_config={
                    "Carnet": st.column_config.NumberColumn("Carnet", format="%d"),
                    # El promedio se muestra como barra de progreso de 0 a 100
                    "Último promedio": st.column_config.ProgressColumn(
                        "Último promedio", min_value=0, max_value=100, format="%.1f"
                    ),
                },
            )
            st.caption(f"Mostrando {len(filas_filtradas)} de {len(filas)} estudiantes")
        else:
            st.info("No hay estudiantes que coincidan con los filtros.")

    # ---------- Pestaña: consulta individual ----------
    with tab_individual:
        st.subheader("Consultar un estudiante")

        # Lista desplegable: se ve "carnet - nombre", pero por dentro usamos el carnet
        opciones = {}
        for carnet, estudiante in datos["estudiantes"].items():
            opciones[f"{carnet} - {estudiante['Nombre']}"] = carnet

        seleccion = st.selectbox("Estudiante", list(opciones.keys()))
        carnet = opciones[seleccion]
        estudiante = datos["estudiantes"][carnet]
        historial = datos["academico"].get(carnet, [])
        estado, motivo = estado_beca(historial)

        # Ficha del estudiante: leemos la plantilla HTML y rellenamos sus huecos.
        # html.escape protege el HTML por si algún dato trae símbolos como < o >.
        ficha = (CARPETA / "plantillas" / "ficha.html").read_text(encoding="utf-8")
        st.markdown(
            ficha.format(
                nombre=html.escape(estudiante["Nombre"]),
                carrera=html.escape(estudiante["carrera"]),
                correo=html.escape(estudiante["correo"]),
                carnet=estudiante["carnet"],
                edad=estudiante["Edad"],
                estado=estado,
                clase=CLASES[estado],
                motivo=motivo,
            ),
            unsafe_allow_html=True,
        )

        # Resumen y tabla del historial (solo si tiene semestres registrados)
        if historial:
            tabla = pd.DataFrame(historial)

            col1, col2, col3 = st.columns(3)
            col1.metric("Semestres cursados", len(tabla))
            col2.metric("Promedio general", f"{tabla['Promedio'].mean():.1f}")
            col3.metric("Último promedio", f"{tabla['Promedio'].iloc[-1]:.1f}")

            st.markdown("**Historial académico**")
            st.dataframe(
                tabla,
                width="stretch",
                hide_index=True,
                column_config={
                    "Promedio": st.column_config.ProgressColumn(
                        "Promedio", min_value=0, max_value=100, format="%.1f"
                    ),
                },
            )