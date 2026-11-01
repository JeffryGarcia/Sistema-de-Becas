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

# Importación del módulo nativo html de Python para escapar/sanitizar texto HTML
import html
# Importación del módulo Path para manejo de rutas de archivos dentro del sistema
from pathlib import Path

# Importación de la librería Streamlit para la interfaz de usuario web
import streamlit as st
# Importación de Pandas para manipulación y renderizado de tablas estructuradas (DataFrames)
import pandas as pd

# Importación de las constantes de corte y la función para generar la tabla académica formateada desde el módulo 'academico'
from academico import PROMEDIO, REPROBADO, tabla_historial
# Importación de la función que compila el informe del estudiante a formato binario PDF desde el módulo 'reporte_pdf'
from reporte_pdf import generar_pdf

# Definición de la ruta de la carpeta padre actual donde reside este archivo fuente (consulta_becas.py)
CARPETA = Path(__file__).parent

# Diccionario de mapeo que asocia el estado textual de la beca con la clase CSS correspondiente definida en style.css
CLASES = {"Con beca": "ok", "Sin beca": "no", "Sin registro": "na"}


# Función de evaluación lógica: analiza el historial académico del estudiante e identifica si califica a la beca según el último período
def estado_beca(historial):
    # Verificación de guarda: Si la lista del historial está vacía o es evaluada como Falsa, no hay registros previos
    if not historial:
        return "Sin registro", "Aún no tiene semestres registrados."

    # Obtención del último elemento (último semestre cursado registrado) utilizando indexación negativa [-1]
    ultimo = historial[-1]

    # Inicialización de una lista temporal para almacenar las razones por las cuales el estudiante reprobaría la solicitud
    motivos = []
    
    # Evaluación 1: Compara el promedio del último semestre contra el promedio mínimo estipulado (PROMEDIO)
    if ultimo["Promedio"] < PROMEDIO:
        motivos.append(f"su promedio ({ultimo['Promedio']}) es menor a {PROMEDIO}")
        
    # Evaluación 2: Compara la cantidad de materias reprobadas del último semestre contra el máximo permitido (REPROBADO)
    if ultimo["Reprobados"] > REPROBADO:
        motivos.append(f"tiene {ultimo['Reprobados']} asignatura(s) reprobada(s) (máximo {REPROBADO})")

    # Toma de decisión: Si la lista 'motivos' contiene elementos, se unen con ' y ' para estructurar la explicación de denegación
    if motivos:
        return "Sin beca", "No cumple porque " + " y ".join(motivos) + "."
    
    # Si la lista 'motivos' está vacía, cumple con todos los criterios exigidos
    return "Con beca", "Cumple los requisitos en su último semestre."


# Función principal de renderizado del módulo de UI dentro de Streamlit
def modulo_consulta_becas(datos):
    # Despliega el título principal de la sección en la pantalla de Streamlit
    st.title("Consulta de becas")

    # Condición de guarda: Si el diccionario de estudiantes está vacío, desglosa un mensaje informativo y finaliza la ejecución de la función
    if not datos["estudiantes"]:
        st.info("No hay estudiantes registrados.")
        return

    # Construcción de la matriz/lista de diccionarios con la información procesada de cada estudiante para las vistas generales
    filas = []
    for carnet, estudiante in datos["estudiantes"].items():
        # Obtiene la lista de semestres del estudiante o una lista vacía si no existe en el diccionario 'academico'
        historial = datos["academico"].get(carnet, [])
        # Calcula el estado y el motivo invocado mediante la función estado_beca()
        estado, motivo = estado_beca(historial)
        # Agrega la fila estructurada con las claves esperadas para el DataFrame
        filas.append({
            "Carnet": estudiante["carnet"],
            "Nombre": estudiante["Nombre"],
            "Carrera": estudiante["carrera"],
            "Semestres": len(historial),
            # Extrae el promedio del último registro si existe historial; en caso contrario asigna None
            "Último promedio": historial[-1]["Promedio"] if historial else None,
            "Estado": estado,
        })

    # Crea dos pestañas (tabs) en la interfaz gráfica para dividir la vista masiva de la vista detallada
    tab_resumen, tab_individual = st.tabs(["Resumen general", "Consulta individual"])

    # ---------- Pestaña: resumen general ----------
    with tab_resumen:
        # Título descriptivo de la pestaña de métricas y tabla global
        st.subheader("Estado de becas de todos los estudiantes")
        # Subtexto informativo que aclara los límites de evaluación parametrizados
        st.caption(f"Requisitos: promedio de {PROMEDIO} o más y máximo {REPROBADO} asignaturas reprobadas.")

        # Inicialización del acumulador numérico por cada categoría de estado posible
        conteo = {"Con beca": 0, "Sin beca": 0, "Sin registro": 0}
        for fila in filas:
            # Incrementa en 1 el contador correspondiente según el estado del estudiante en la iteración
            conteo[fila["Estado"]] += 1

        # Creación de una distribución visual de 3 columnas para mostrar las tarjetas de resumen (KPIs)
        columnas = st.columns(3)
        for columna, estado in zip(columnas, conteo):
            # Inyección de código HTML renderizado para desplegar cuadros de estado estilizados con clases dinamizadas de CSS
            columna.markdown(
                f'<div class="stat stat-{CLASES[estado]}"><span>{estado}</span><strong>{conteo[estado]}</strong></div>',
                unsafe_allow_html=True,
            )

        st.write("")  # Salto de línea / espaciador visual en la pantalla

        # Cálculo de métrica porcentual de cobertura de becas sobre los estudiantes evaluables (excluye 'Sin registro')
        evaluados = conteo["Con beca"] + conteo["Sin beca"]
        if evaluados > 0:
            porcentaje = conteo["Con beca"] / evaluados
            # Dibuja una barra de progreso que indica la proporción de becados sobre el total evaluado
            st.progress(
                porcentaje,
                text=f"{conteo['Con beca']} de {evaluados} estudiantes evaluados cumplen los requisitos ({porcentaje:.0%})",
            )

        st.write("") # Salto de línea / espaciador visual en la pantalla

        # Creación de dos columnas para albergar los controles de filtrado horizontal y búsqueda por texto
        col_filtro, col_buscar = st.columns([2, 1])
        # Control de selección por botones de radio para filtrar por la columna "Estado"
        filtro = col_filtro.radio(
            "Mostrar", ["Todos", "Con beca", "Sin beca", "Sin registro"], horizontal=True
        )
        # Campo de entrada de texto libre para buscar coincidencias por Nombre o por Carnet
        buscar = col_buscar.text_input("Buscar", placeholder="Nombre o carnet")

        # Aplicación del filtrado de datos iterando la lista original de filas
        filas_filtradas = []
        for fila in filas:
            # Condición 1: Comprueba si el filtro es 'Todos' o coincide exactamente con el estado de la fila
            coincide_estado = filtro == "Todos" or fila["Estado"] == filtro
            # Condición 2: Comprueba si el texto ingresado se encuentra en el nombre (ignore case) o en el carnet
            coincide_texto = buscar.lower() in fila["Nombre"].lower() or buscar in str(fila["Carnet"])
            # Si ambas condiciones son verdaderas, el estudiante se incluye en la lista filtrada
            if coincide_estado and coincide_texto:
                filas_filtradas.append(fila)

        # Si existen elementos coincidentes, se genera y configura la tabla interactiva de datos
        if filas_filtradas:
            st.dataframe(
                pd.DataFrame(filas_filtradas),
                width="stretch",
                hide_index=True,
                column_config={
                    # Formatea el carnet como un número entero sin comas de miles (%d)
                    "Carnet": st.column_config.NumberColumn("Carnet", format="%d"),
                    # Formatea el promedio mostrando una barra visual con rango de 0 a 100 y 1 decimal (%1.f)
                    "Último promedio": st.column_config.ProgressColumn(
                        "Último promedio", min_value=0, max_value=100, format="%.1f"
                    ),
                },
            )
            # Pie de tabla indicando la proporción de resultados mostrados tras aplicar los filtros
            st.caption(f"Mostrando {len(filas_filtradas)} de {len(filas)} estudiantes")
        else:
            # Mensaje en caso de que la búsqueda/filtro no devuelva ningún registro
            st.info("No hay estudiantes que coincidan con los filtros.")

    # ---------- Pestaña: consulta individual ----------
    with tab_individual:
        # Encabezado para la búsqueda y desplegado detallado del perfil de un estudiante
        st.subheader("Consultar un estudiante")

        # Construcción del diccionario 'opciones' para el selectbox: asigna 'Carnet - Nombre' (Etiqueta) -> Carnet (ID clave)
        opciones = {}
        for carnet, estudiante in datos["estudiantes"].items():
            opciones[f"{carnet} - {estudiante['Nombre']}"] = carnet

        # Control selectbox desplegable para elegir el estudiante activo a consultar
        seleccion = st.selectbox("Estudiante", list(opciones.keys()))
        # Recuperación de la clave (carnet) correspondiente al elemento seleccionado del menú
        carnet = opciones[seleccion]
        # Extracción de la información básica y el historial académico del estudiante seleccionado
        estudiante = datos["estudiantes"][carnet]
        historial = datos["academico"].get(carnet, [])
        # Re-evaluación del estado y motivo del estudiante específico
        estado, motivo = estado_beca(historial)

        # Lectura directa del archivo de plantilla HTML ubicado en plantillas/ficha.html usando codificación UTF-8
        ficha = (CARPETA / "plantillas" / "ficha.html").read_text(encoding="utf-8")
        # Inyección de los datos del estudiante dentro de los marcadores posicionales del HTML mediante .format()
        # html.escape() previene fallos de renderizado y ataques XSS neutralizando caracteres especiales (<, >, &, etc.)
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

        # Despliegue del botón nativo de Streamlit para descargar el documento PDF del informe individual
        # Invoca a 'generar_pdf()' pasando la información completa y retorna el contenido binario listo para la descarga
        st.download_button(
            "Descargar reporte en PDF",
            data=generar_pdf(estudiante, historial, estado, motivo),
            file_name=f"reporte_{carnet}.pdf",
            mime="application/pdf",
            type="primary",
        )

        # Si el estudiante posee historial académico de semestres registrados, despliega sus métricas e historial estructurado
        if historial:
            # Obtiene el DataFrame limpio y procesado proveniente de la función 'tabla_historial' en academico.py
            tabla = tabla_historial(historial)

            # Despliegue de 3 tarjetas numéricas (Metrics) con resumenes globales del estudiante
            col1, col2, col3 = st.columns(3)
            # Métrica 1: Número total de semestres cursados (filas del historial)
            col1.metric("Semestres cursados", len(tabla))
            # Métrica 2: Promedio aritmético acumulado de todos los semestres cursados
            col2.metric("Promedio general", f"{tabla['Promedio'].mean():.1f}")
            # Métrica 3: Promedio obtenido en el último semestre registrado (.iloc[-1])
            col3.metric("Último promedio", f"{tabla['Promedio'].iloc[-1]:.1f}")

            # Subtítulo explicativo para la visualización del desglose académico
            st.markdown("**Historial académico**")
            # Renderizado del DataFrame del historial académico con configuración de barra de progreso para la columna Promedio
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