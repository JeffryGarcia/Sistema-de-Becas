# =============================================================================
# academico.py -> Módulo ACADÉMICO (Darlenne)
#
# El historial se guarda en el diccionario `datos` así:
#   datos["academico"] = { "carnet (como texto)": [ {semestre}, {semestre}, ... ] }
# =============================================================================

import math
import re

import streamlit as st
import pandas as pd
from archivos import guardar_datos

# Requisitos para mantener la beca
PROMEDIO = 85.0   # promedio mínimo
REPROBADO = 0     # máximo de asignaturas reprobadas
NOTA_APROBATORIA = 60.0


# Se reciben los datos academicos, se validan que sean correctos y se registra el semestre del estudiante
def registro_semestre(
    datos: dict,
    carnet: str,
    semestre: str,
    promedio: float,
    aprobadas: int = 0,
    reprobadas: int = 0,
    asignaturas: list[dict] | None = None,
):
    if carnet not in datos["estudiantes"]:
        return "Su número de carnet no corresponde a ningún estudiante"
    if not semestre.strip():
        return "Debe especificar el semestre"
    if not re.fullmatch(r"\d{4}-(?:I|II)", semestre.strip()):
        return "El semestre debe tener el formato AAAA-I o AAAA-II (ejemplo: 2026-I)"
    try:
        promedio = float(promedio)
    except (TypeError, ValueError):
        return "Ingrese un promedio mayor que 0 y hasta 100"
    if not math.isfinite(promedio) or not (0 < promedio <= 100):
        return "Ingrese un promedio mayor que 0 y hasta 100"

    registros_asignaturas = []
    if asignaturas is not None:
        if not asignaturas:
            return "Registre al menos una asignatura"
        for asignatura in asignaturas:
            if not isinstance(asignatura, dict):
                return "Los datos de las asignaturas no son válidos"
            nombre = str(asignatura.get("Asignatura", "")).strip()
            try:
                nota = float(asignatura.get("Nota"))
            except (TypeError, ValueError):
                return f"Ingrese una nota válida para {nombre or 'cada asignatura'}"
            if not nombre:
                return "Debe completar el nombre de cada asignatura"
            if not math.isfinite(nota) or not 0 <= nota <= 100:
                return f"La nota de {nombre} debe estar entre 0 y 100"
            registros_asignaturas.append({
                "Asignatura": nombre,
                "Nota": nota,
                "Estado": "Aprobada" if nota >= NOTA_APROBATORIA else "Reprobada",
            })
        aprobadas = sum(
            asignatura["Estado"] == "Aprobada"
            for asignatura in registros_asignaturas
        )
        reprobadas = len(registros_asignaturas) - aprobadas
    elif (
        type(aprobadas) is not int
        or type(reprobadas) is not int
        or aprobadas < 0
        or reprobadas < 0
    ):
        return "El número de asignaturas debe ser un entero no negativo"

    historial = datos.setdefault("academico", {}).setdefault(carnet, [])
    nuevo_registro = {
        "Semestre": semestre.strip(),
        "Promedio": promedio,
        "Aprobado": aprobadas,
        "Reprobados": reprobadas
    }
    if asignaturas is not None:
        nuevo_registro["Asignaturas"] = registros_asignaturas
    historial.append(nuevo_registro)
    return "Se ha registrado su semestre"


# Lo que se ve en la página "Académico"
def modulo_academico(datos):
    st.title("Académico")

    # Lista desplegable: se ve "carnet - nombre", pero por dentro usamos el carnet
    opciones = {}
    for carnet, estudiante in datos["estudiantes"].items():
        opciones[f"{carnet} - {estudiante['Nombre']}"] = carnet

    if not opciones:
        st.info("No hay estudiantes registrados.")
        return

    # Dos pestañas: registrar semestre e historial
    tab_registro, tab_historial = st.tabs(["Registrar semestre", "Historial académico"])

    # Llenamos primero "registrar" y después el historial,
    # así el historial ya sale actualizado cuando se registra un semestre.
    with tab_registro:
        st.subheader("Registrar semestre")
        st.caption(f"Para mantener la beca: promedio de {PROMEDIO} o más y {REPROBADO} reprobadas.")
        seleccion = st.selectbox(
            "Estudiante",
            list(opciones.keys()),
            key="academico_estudiante",
        )
        carnet = opciones[seleccion]
        st.caption(f"Las asignaturas quedarán asociadas al carnet {carnet}.")

        carnet_anterior = st.session_state.get("academico_carnet_activo")
        if carnet_anterior is not None and carnet_anterior != carnet:
            for clave in list(st.session_state):
                if clave.startswith(("academico_asignatura_", "academico_nota_")) or clave in {
                    "academico_semestre",
                    "academico_promedio",
                }:
                    del st.session_state[clave]
            st.session_state["academico_filas"] = [0]
            st.session_state["academico_siguiente_fila"] = 1
        st.session_state["academico_carnet_activo"] = carnet
        st.session_state.setdefault("academico_filas", [0])
        st.session_state.setdefault("academico_siguiente_fila", 1)

        col1, col2 = st.columns(2)
        semestre = col1.text_input(
            "Semestre",
            placeholder="Ej: 2026-I",
            help="Use el año y el período en números romanos: 2026-I o 2026-II.",
            key="academico_semestre",
        )
        promedio_texto = col2.text_input(
            "Promedio (0 a 100)",
            placeholder="Ej: 85.5",
            key="academico_promedio",
        )

        st.markdown("**Asignaturas y notas**")
        st.caption(
            f"Una nota de {NOTA_APROBATORIA:g} o más cuenta como aprobada. "
            "El sistema calculará los conteos automáticamente."
        )
        if st.button("Agregar asignatura", key="academico_agregar_fila"):
            siguiente = st.session_state["academico_siguiente_fila"]
            st.session_state["academico_filas"].append(siguiente)
            st.session_state["academico_siguiente_fila"] = siguiente + 1

        asignaturas = []
        errores = []
        if not semestre.strip():
            errores.append("Semestre")
        elif not re.fullmatch(r"\d{4}-(?:I|II)", semestre.strip()):
            errores.append("Semestre (formato AAAA-I o AAAA-II)")

        promedio = None
        if not promedio_texto.strip():
            errores.append("Promedio")
        else:
            try:
                promedio = float(promedio_texto)
            except ValueError:
                errores.append("Promedio (debe ser un número)")
            else:
                if not math.isfinite(promedio) or not (0 < promedio <= 100):
                    errores.append("Promedio (debe ser mayor que 0 y hasta 100)")

        for numero, fila in enumerate(list(st.session_state["academico_filas"]), start=1):
            col_nombre, col_nota, col_quitar = st.columns([5, 2, 1])
            if col_quitar.button(
                "Quitar",
                key=f"academico_quitar_{fila}",
                disabled=len(st.session_state["academico_filas"]) == 1,
            ):
                st.session_state["academico_filas"].remove(fila)
                st.session_state.pop(f"academico_asignatura_{fila}", None)
                st.session_state.pop(f"academico_nota_{fila}", None)
                continue
            nombre = col_nombre.text_input(
                f"Asignatura {numero}",
                key=f"academico_asignatura_{fila}",
            )
            nota_texto = col_nota.text_input(
                f"Nota {numero}",
                placeholder="0 a 100",
                key=f"academico_nota_{fila}",
            )
            if not nombre.strip():
                errores.append(f"Asignatura {numero}")
            if not nota_texto.strip():
                errores.append(f"Nota de asignatura {numero}")
            else:
                try:
                    nota = float(nota_texto)
                except ValueError:
                    errores.append(f"Nota de asignatura {numero} (debe ser numérica)")
                else:
                    if not math.isfinite(nota) or not 0 <= nota <= 100:
                        errores.append(f"Nota de asignatura {numero} (de 0 a 100)")
                    else:
                        asignaturas.append({"Asignatura": nombre, "Nota": nota})

        if errores:
            st.warning("Complete o corrija estos campos: " + ", ".join(errores) + ".")

        enviado = st.button(
            "Registrar semestre",
            type="primary",
            width="stretch",
            disabled=bool(errores),
        )
        if enviado:
            resultado = registro_semestre(
                datos,
                carnet,
                semestre,
                promedio,
                asignaturas=asignaturas,
            )
            if resultado == "Se ha registrado su semestre":
                if guardar_datos(datos):
                    st.success(resultado)
                else:
                    st.error("El semestre se registró, pero no se pudo guardar en el archivo.")
            else:
                st.error(resultado)

    with tab_historial:
        st.subheader("Historial académico")

        seleccion_h = st.selectbox("Estudiante", list(opciones.keys()), key="sel_historial")
        historial = datos["academico"].get(opciones[seleccion_h], [])

        if not historial:
            st.info("Este estudiante aún no tiene semestres registrados.")
        else:
            # Tabla del historial + columna que dice si cumple los requisitos de la beca
            tabla = pd.DataFrame([
                {clave: valor for clave, valor in registro.items() if clave != "Asignaturas"}
                for registro in historial
            ])
            cumple = (tabla["Promedio"] >= PROMEDIO) & (tabla["Reprobados"] == REPROBADO)
            tabla["Cumple requisitos"] = cumple.map({True: "Sí", False: "No"})

            # Tarjetas con el resumen del estudiante
            col1, col2, col3 = st.columns(3)
            col1.metric("Semestres cursados", len(tabla))
            col2.metric("Promedio general", f"{tabla['Promedio'].mean():.1f}")
            # El estado se basa en el ÚLTIMO semestre registrado
            col3.metric("Estado actual", "Cumple" if cumple.iloc[-1] else "No cumple")

            # El promedio se muestra como barra de progreso de 0 a 100
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
            for registro in historial:
                asignaturas = registro.get("Asignaturas", [])
                if asignaturas:
                    with st.expander(f"Asignaturas de {registro['Semestre']}"):
                        st.dataframe(
                            pd.DataFrame(asignaturas),
                            width="stretch",
                            hide_index=True,
                        )
            st.caption(f"Requisitos: promedio ≥ {PROMEDIO} y {REPROBADO} asignaturas reprobadas.")