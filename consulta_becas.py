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
# Marcas de los comentarios:
#   # NUEVO:  -> algo que se agregó en esta versión
#   # CAMBIO: -> algo que ya existía y se modificó
# =============================================================================

import html
from pathlib import Path

import streamlit as st
import pandas as pd

# CAMBIO: se importa también clave_semestre para ordenar cronológicamente
from academico import PROMEDIO, REPROBADO, tabla_historial, clave_semestre
from reporte_pdf import generar_pdf
from carreras import CARRERAS, canonica   # NUEVO: catálogo oficial de carreras

CARPETA = Path(__file__).parent

CLASES = {"Con beca": "ok", "Sin beca": "no", "Sin registro": "na"}

CAMPOS_SEMESTRE = ("Semestre", "Promedio", "Reprobados")

OTRA = "Otra / sin clasificar"   # NUEVO: para carreras escritas a mano que no están en el catálogo


# NUEVO: nombre oficial de la carrera de un estudiante (o OTRA si no coincide con el catálogo)
def carrera_oficial(estudiante):
    return canonica(estudiante.get("carrera", "")) or OTRA


# NUEVO: Convierte a número de forma segura. Devuelve None si no es un número válido (texto, vacío, NaN, bool).
def _numero(valor):
    if isinstance(valor, bool):
        return None
    try:
        n = float(valor)
    except (TypeError, ValueError):
        return None
    return n if n == n else None   # n != n solo ocurre con NaN


# NUEVO: Devuelve el historial limpio y ORDENADO cronológicamente.
#        Descarta registros dañados (sin Semestre/Promedio/Reprobados o con valores no numéricos).
#        Así el "último semestre" es siempre el más reciente, aunque el JSON se haya editado a mano.
def historial_limpio(historial):
    validos = []
    for r in historial or []:
        if not isinstance(r, dict) or any(c not in r for c in CAMPOS_SEMESTRE):
            continue
        if _numero(r["Promedio"]) is None or _numero(r["Reprobados"]) is None:
            continue
        validos.append(r)
    return sorted(validos, key=clave_semestre)


# NUEVO: Último semestre (el más reciente) o None si no hay ninguno utilizable.
#        app.py debería usar esta función en lugar de historial[-1].
def ultimo_semestre(historial):
    limpio = historial_limpio(historial)
    return limpio[-1] if limpio else None


def estado_beca(historial):
    # CAMBIO: antes usaba historial[-1] directamente (podía fallar o tomar un semestre que no es el último)
    ultimo = ultimo_semestre(historial)
    if ultimo is None:
        if historial:
            return "Sin registro", "Los semestres registrados tienen datos incompletos o dañados."
        return "Sin registro", "Aún no tiene semestres registrados."

    promedio = _numero(ultimo["Promedio"])
    reprobados = int(_numero(ultimo["Reprobados"]))

    motivos = []
    if promedio < PROMEDIO:
        motivos.append(f"su promedio ({promedio:g}) es menor a {PROMEDIO}")
    if reprobados > REPROBADO:
        motivos.append(f"tiene {reprobados} asignatura(s) reprobada(s) (máximo {REPROBADO})")

    if motivos:
        return "Sin beca", "No cumple porque " + " y ".join(motivos) + "."

    return "Con beca", "Cumple los requisitos en su último semestre."


# NUEVO: cuenta cuántos estudiantes de un grupo tienen cierto estado de beca
def contar(grupo, estado):
    return sum(1 for f in grupo if f["Estado"] == estado)


def modulo_consulta_becas(datos):
    st.title("Consulta de becas")

    if not datos["estudiantes"]:
        st.info("No hay estudiantes registrados.")
        return

    filas = []
    for carnet, estudiante in datos["estudiantes"].items():
        historial = historial_limpio(datos["academico"].get(carnet, []))
        estado, motivo = estado_beca(historial)
        ultimo = ultimo_semestre(historial)
        filas.append({
            # CAMBIO: .get() con valores por defecto, para no caer con un registro incompleto
            "Carnet": estudiante.get("carnet", carnet),
            "Nombre": estudiante.get("Nombre", "—"),
            "Edad": estudiante.get("Edad", "—"),                                    # NUEVO
            "Carrera": carrera_oficial(estudiante),                                 # CAMBIO: nombre oficial
            "Semestres": len(historial),
            "Último semestre": ultimo["Semestre"] if ultimo else None,              # NUEVO
            "Último promedio": _numero(ultimo["Promedio"]) if ultimo else None,
            "Reprobados": int(_numero(ultimo["Reprobados"])) if ultimo else None,   # NUEVO
            "Estado": estado,
        })

    # CAMBIO: ahora son 3 pestañas (se crean UNA sola vez, fuera del bucle)
    tab_resumen, tab_carrera, tab_individual = st.tabs(
        ["Resumen general", "Por carrera", "Consulta individual"])

    # ---------- Pestaña: resumen general ----------
    with tab_resumen:
        st.subheader("Estado de becas de todos los estudiantes")
        st.caption(f"Requisitos: promedio de {PROMEDIO} o más y máximo {REPROBADO} asignaturas reprobadas.")

        conteo = {"Con beca": 0, "Sin beca": 0, "Sin registro": 0}
        for fila in filas:
            conteo[fila["Estado"]] += 1

        columnas = st.columns(3)
        for columna, estado in zip(columnas, conteo):
            columna.markdown(
                f'<div class="stat stat-{CLASES[estado]}"><span>{estado}</span><strong>{conteo[estado]}</strong></div>',
                unsafe_allow_html=True,
            )

        st.write("")

        evaluados = conteo["Con beca"] + conteo["Sin beca"]
        if evaluados > 0:
            porcentaje = conteo["Con beca"] / evaluados
            st.progress(
                porcentaje,
                text=f"{conteo['Con beca']} de {evaluados} estudiantes evaluados cumplen los requisitos ({porcentaje:.0%})",
            )

        st.write("")

        col_filtro, col_buscar = st.columns([2, 1])
        filtro = col_filtro.radio(
            "Mostrar", ["Todos", "Con beca", "Sin beca", "Sin registro"], horizontal=True
        )
        # CAMBIO: max_chars y .strip() para ignorar espacios al inicio o al final
        buscar = col_buscar.text_input("Buscar", placeholder="Nombre o carnet", max_chars=60).strip()

        filas_filtradas = []
        for fila in filas:
            coincide_estado = filtro == "Todos" or fila["Estado"] == filtro
            coincide_texto = (buscar.lower() in str(fila["Nombre"]).lower()
                              or buscar in str(fila["Carnet"]))
            if coincide_estado and coincide_texto:
                filas_filtradas.append(fila)

        if filas_filtradas:
            st.dataframe(
                pd.DataFrame(filas_filtradas),
                width="stretch",
                hide_index=True,
                # NUEVO: solo estas columnas se ven en el resumen (las demás son para "Por carrera")
                column_order=["Carnet", "Nombre", "Carrera", "Semestres", "Último promedio", "Estado"],
                column_config={
                    "Carnet": st.column_config.NumberColumn("Carnet", format="%d"),
                    "Último promedio": st.column_config.ProgressColumn(
                        "Último promedio", min_value=0, max_value=100, format="%.1f"
                    ),
                },
            )
            st.caption(f"Mostrando {len(filas_filtradas)} de {len(filas)} estudiantes")
        else:
            st.info("No hay estudiantes que coincidan con los filtros.")

    # ---------- Pestaña: por carrera ----------
    with tab_carrera:
        st.subheader("Estudiantes por carrera")

        por_carrera = {}
        for fila in filas:
            por_carrera.setdefault(fila["Carrera"], []).append(fila)

        opciones_carrera = list(CARRERAS)
        if OTRA in por_carrera:
            opciones_carrera.append(OTRA)

        # Resumen de todas las carreras de un vistazo
        with st.expander("Resumen de todas las carreras"):
            st.dataframe(
                pd.DataFrame([
                    {"Carrera": c,
                     "Estudiantes": len(por_carrera.get(c, [])),
                     "Con beca": contar(por_carrera.get(c, []), "Con beca"),
                     "Sin beca": contar(por_carrera.get(c, []), "Sin beca"),
                     "Sin registro": contar(por_carrera.get(c, []), "Sin registro")}
                    for c in opciones_carrera
                ]),
                width="stretch", hide_index=True,
            )

        carrera_sel = st.selectbox(
            "Carrera", opciones_carrera,
            format_func=lambda c: f"{c} ({len(por_carrera.get(c, []))})",
            key="carr_sel",
        )
        grupo = por_carrera.get(carrera_sel, [])

        if not grupo:
            st.info(f"No hay estudiantes registrados en {carrera_sel}.")
        else:
            # Subdivisiones dentro de la carrera (las llaves incluyen la carrera para no mezclar filtros)
            col_estado, col_buscar_c = st.columns([2, 1])
            filtro_estado = col_estado.radio(
                "Estado", ["Todos", "Con beca", "Sin beca", "Sin registro"],
                horizontal=True, key=f"carr_estado_{carrera_sel}")
            buscar_c = col_buscar_c.text_input(
                "Buscar", placeholder="Nombre o carnet", max_chars=60,
                key=f"carr_buscar_{carrera_sel}").strip()

            semestres = sorted({f["Último semestre"] for f in grupo if f["Último semestre"]},
                               reverse=True)
            sem_sel = st.multiselect("Último semestre", semestres,
                                     key=f"carr_sem_{carrera_sel}")

            visibles = [
                f for f in grupo
                if (filtro_estado == "Todos" or f["Estado"] == filtro_estado)
                and (not sem_sel or f["Último semestre"] in sem_sel)
                and (buscar_c.lower() in str(f["Nombre"]).lower() or buscar_c in str(f["Carnet"]))
            ]

            if visibles:
                tabla_c = pd.DataFrame(visibles)[["Carnet", "Nombre", "Edad", "Último semestre",
                                                  "Último promedio", "Reprobados", "Estado"]]
                tabla_c.insert(0, "N°", range(1, len(tabla_c) + 1))   # tabla enumerada
                st.dataframe(
                    tabla_c, width="stretch", hide_index=True,
                    column_config={
                        "Carnet": st.column_config.NumberColumn("Carnet", format="%d"),
                        "Último promedio": st.column_config.ProgressColumn(
                            "Último promedio", min_value=0, max_value=100, format="%.1f"),
                    },
                )
            else:
                st.info("No hay estudiantes que coincidan con los filtros.")

            # ----- Conteo final de la carrera -----
            st.markdown(f"**Conteo de {carrera_sel}**")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total en la carrera", len(grupo))
            m2.metric("Con beca", contar(grupo, "Con beca"))
            m3.metric("Sin beca", contar(grupo, "Sin beca"))
            m4.metric("Sin registro", contar(grupo, "Sin registro"))

            # Conteo de la selección actual (útil para el informe exacto)
            if len(visibles) != len(grupo):
                st.caption(
                    f"Con los filtros actuales: {len(visibles)} de {len(grupo)} estudiantes "
                    f"({contar(visibles, 'Con beca')} con beca, {contar(visibles, 'Sin beca')} sin beca, "
                    f"{contar(visibles, 'Sin registro')} sin registro)."
                )

    # ---------- Pestaña: consulta individual ----------
    with tab_individual:
        st.subheader("Consultar un estudiante")

        opciones = {}
        for carnet, estudiante in datos["estudiantes"].items():
            opciones[f"{carnet} - {estudiante.get('Nombre', '—')}"] = carnet

        seleccion = st.selectbox("Estudiante", list(opciones.keys()))
        carnet = opciones[seleccion]
        estudiante = datos["estudiantes"][carnet]
        # CAMBIO: historial limpio y ordenado (antes se usaba tal cual estaba en el JSON)
        historial = historial_limpio(datos["academico"].get(carnet, []))
        estado, motivo = estado_beca(historial)

        # NUEVO: si falta la plantilla se muestra un error claro en lugar de romper toda la página
        try:
            ficha = (CARPETA / "plantillas" / "ficha.html").read_text(encoding="utf-8")
        except OSError:
            st.error("No se encontró la plantilla plantillas/ficha.html.")
            return

        # CAMBIO: ahora TODOS los valores se escapan con html.escape (antes carnet, edad, estado y motivo
        #         se insertaban sin escapar) y se usa .get() por si falta algún dato del estudiante.
        st.markdown(
            ficha.format(
                nombre=html.escape(str(estudiante.get("Nombre", "—"))),
                carrera=html.escape(str(estudiante.get("carrera", "—"))),
                correo=html.escape(str(estudiante.get("correo", "—"))),
                carnet=html.escape(str(estudiante.get("carnet", carnet))),
                edad=html.escape(str(estudiante.get("Edad", "—"))),
                estado=html.escape(estado),
                clase=CLASES[estado],
                motivo=html.escape(motivo),
            ),
            unsafe_allow_html=True,
        )

        # CAMBIO: la generación del PDF se protege con try/except. Se ejecuta en cada rerun de la página,
        #         así que un fallo en reporte_pdf antes tumbaba toda la pestaña.
        try:
            pdf = bytes(generar_pdf(estudiante, historial, estado, motivo))
        except Exception as e:
            pdf = None
            st.error(f"No se pudo generar el reporte en PDF: {e}")

        if pdf is not None:
            st.download_button(
                "Descargar reporte en PDF",
                data=pdf,
                file_name=f"reporte_{carnet}.pdf",
                mime="application/pdf",
                type="primary",
            )

        if historial:
            tabla = tabla_historial(historial)

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
        else:
            # NUEVO: antes no se mostraba nada si el estudiante no tenía semestres
            st.info("Este estudiante aún no tiene semestres registrados.")