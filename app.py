# =============================================================================
# app.py -> Archivo PRINCIPAL del Sistema de Becas (la interfaz que se ve)
# Para correrlo:  streamlit run app.py
#
# Cómo está organizado el proyecto:
#   app.py                    -> LÓGICA de la interfaz (Python)
#   style.css                 -> ESTILOS (colores, bordes, sombras)
#   plantillas/banner.html    -> ESTRUCTURA del banner de Inicio (HTML)
#   plantillas/ficha.html     -> ESTRUCTURA de la ficha del estudiante (HTML)
#   .streamlit/config.toml    -> TEMA general de colores de Streamlit
# =============================================================================

from pathlib import Path

import streamlit as st
import pandas as pd
from archivos import cargar_datos, guardar_datos
from estudiantes import modulo_estudiantes, ESTUDIANTES_INICIALES
from academico import modulo_academico, PROMEDIO, REPROBADO
from consulta_becas import modulo_consulta_becas

# Carpeta donde está este archivo (así encuentra el CSS y el HTML sin importar
# desde dónde se ejecute el programa)
CARPETA = Path(__file__).parent

# 1. Configuración de la página (debe ser el PRIMER comando de Streamlit)
st.set_page_config(
    page_title="Sistema de Becas",
    page_icon="🎓",
    layout="wide",
)

# 2. ESTILOS: leemos el archivo style.css y se lo pasamos a Streamlit.
#    Se aplica a toda la app, incluyendo los formularios de los otros módulos.
css = (CARPETA / "style.css").read_text(encoding="utf-8")
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# 3. Cargar los datos de becas.json UNA sola vez.
#    Streamlit vuelve a correr este archivo en cada clic, por eso se guardan
#    en st.session_state: así no se pierden entre clics.
if "datos" not in st.session_state:
    st.session_state.datos = cargar_datos()

    # Primera vez que se usa el sistema: agregamos los estudiantes de ejemplo
    if not st.session_state.datos["estudiantes"]:
        st.session_state.datos["estudiantes"] = ESTUDIANTES_INICIALES.copy()
        guardar_datos(st.session_state.datos)

datos = st.session_state.datos

# 4. Lista de páginas: un solo lugar para agregar o renombrar secciones
PAGINAS = ["Inicio", "Estudiantes", "Académico", "Consulta de becas"]

# 5. Barra lateral con el menú
st.sidebar.title("Sistema de Becas")
pagina = st.sidebar.radio("Navegación", PAGINAS)
st.sidebar.divider()  # línea separadora
st.sidebar.info("Sistema de Gestión y Seguimiento de Becas")

# 6. Mostrar el contenido según la página elegida
if pagina == "Inicio":
    # Banner de bienvenida: leemos la plantilla HTML y rellenamos sus huecos
    banner = (CARPETA / "plantillas" / "banner.html").read_text(encoding="utf-8")
    st.markdown(
        banner.format(
            titulo="Sistema de Gestión y Seguimiento de Becas",
            subtitulo="Administra estudiantes, registra su rendimiento académico y consulta el estado de las becas.",
        ),
        unsafe_allow_html=True,
    )

    # --- Cálculo de los números del resumen ---
    total_estudiantes = len(datos["estudiantes"])

    # Contamos cuántos semestres se han registrado en total
    total_semestres = 0
    for historial in datos["academico"].values():
        total_semestres += len(historial)

    # Contamos cuántos estudiantes cumplen los requisitos en su ÚLTIMO semestre
    con_beca = 0
    for historial in datos["academico"].values():
        if historial:
            ultimo = historial[-1]
            if ultimo["Promedio"] >= PROMEDIO and ultimo["Reprobados"] == REPROBADO:
                con_beca += 1

    # --- Tarjetas con los números (3 columnas) ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Estudiantes registrados", total_estudiantes)
    col2.metric("Semestres registrados", total_semestres)
    col3.metric("Cumplen requisitos de beca", con_beca)

    st.write("")  # espacio en blanco

    # # --- Gráfico de estudiantes por carrera ---
    # st.subheader("Estudiantes por carrera")
    # carreras = {}
    # for estudiante in datos["estudiantes"].values():
    #     carrera = estudiante["carrera"]
    #     carreras[carrera] = carreras.get(carrera, 0) + 1  # sumamos 1 a esa carrera
    # st.bar_chart(pd.Series(carreras))

    # --- Guía rápida desplegable ---
    with st.expander("¿Cómo se usa el sistema?"):
        st.markdown(
            f"""
            1. Ve a **Estudiantes** para ver la lista o agregar un estudiante nuevo.
            2. Ve a **Académico** para registrar el semestre de un estudiante y ver su historial.
            3. Ve a **Consulta de becas** para ver quién tiene beca y por qué.
            4. Para mantener la beca se necesita un promedio de **{PROMEDIO} o más** y
               **{REPROBADO}** asignaturas reprobadas.
            """
        )

elif pagina == "Estudiantes":
    modulo_estudiantes(datos)       # módulo de Yahosca

elif pagina == "Académico":
    modulo_academico(datos)         # módulo de Darlenne

elif pagina == "Consulta de becas":
    modulo_consulta_becas(datos)    # módulo de Jeffry