# =============================================================================
# app.py -> Archivo PRINCIPAL del Sistema de Becas (la interfaz que se ve)
# Para correrlo:   streamlit run app.py
#
# Cómo está organizado el proyecto:
#   app.py                    -> LÓGICA de la interfaz (Python)
#   style.css                 -> ESTILOS (colores, bordes, sombras, animaciones)
#   plantillas/banner.html    -> ESTRUCTURA del banner de Inicio (HTML)
#   plantillas/ficha.html     -> ESTRUCTURA de la ficha del estudiante (HTML)
#   .streamlit/config.toml    -> TEMA general de colores de Streamlit
#   assets/logo_uni.png       -> logo de la UNI (blanco, con fondo transparente) para la barra superior
# =============================================================================
# Marcas de los comentarios:
#   # NUEVO:  -> algo que se agregó en esta versión
#   # CAMBIO: -> algo que ya existía y se modificó
# =============================================================================

import base64   # Importación para codificar el logotipo en formato base64 e incrustarlo como variable CSS
from pathlib import Path

import streamlit as st
import pandas as pd
from archivos import cargar_datos, guardar_datos
from estudiantes import modulo_estudiantes, ESTUDIANTES_INICIALES
from academico import modulo_academico, PROMEDIO, REPROBADO
# Se importan también estado_beca y CLASES para reutilizar la misma regla de validación y los mismos colores en el inicio
from consulta_becas import modulo_consulta_becas, estado_beca, CLASES

# Definición de la ruta base del directorio actual donde reside app.py (facilita la ubicación de recursos relativos)
CARPETA = Path(__file__).parent

# NUEVO: Color de las barras de la gráfica de Inicio. Debe coincidir con --acento de style.css.
COLOR_GRAFICA = "#25525c"

# NUEVO: Cuántos estudiantes se muestran en el ranking de Inicio.
TOP_RANKING = 5

# 1. Configuración de la página (REQUISITO: Debe ser estrictamente el PRIMER comando de Streamlit ejecutado en el script)
st.set_page_config(
    page_title="SG UNI - Sistema de Becas",
    page_icon="🎓",
    layout="wide",
)

# 2. ESTILOS: Lectura del archivo style.css e inyección directa en el DOM mediante etiquetas <style> de Markdown.
#    Se aplica de manera global a toda la aplicación web, incluyendo los componentes de los sub-módulos.
css = (CARPETA / "style.css").read_text(encoding="utf-8")
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# Logo de la UNI dentro de la barra de navegación (a la derecha, antes del menú de tres puntos).
# Aquí solo se entrega la imagen como variable CSS (--logo-uni); style.css la dibuja dentro del header
# con stHeader::after, así no depende de dónde esté el elemento en la página.
LOGO_UNI = CARPETA / "assets" / "logo_uni.png"
LOGO_UNI_B64 = base64.b64encode(LOGO_UNI.read_bytes()).decode()
st.markdown(
    f'<style>:root {{ --logo-uni: url("data:image/png;base64,{LOGO_UNI_B64}"); }}</style>',
    unsafe_allow_html=True,
)

# 3. Carga inicial persistente de la base de datos (becas.json) mediante archivos.py.
#    Streamlit reejecuta todo el script ante cualquier interacción del usuario; por ello, los datos se almacenan
#    en st.session_state para garantizar que perduren intactos entre clics y recargas de página.
if "datos" not in st.session_state:
    st.session_state.datos = cargar_datos()

    # Primera ejecución del sistema: si el diccionario de estudiantes está vacío, se precargan los estudiantes de ejemplo iniciales
    if not st.session_state.datos["estudiantes"]:
        st.session_state.datos["estudiantes"] = ESTUDIANTES_INICIALES.copy()
        guardar_datos(st.session_state.datos)

# Instanciación de referencia corta al diccionario central de datos almacenado en la sesión
datos = st.session_state.datos

# NUEVO: Mensaje emergente de bienvenida, una sola vez por sesión
if "bienvenida" not in st.session_state:
    st.session_state.bienvenida = True
    st.toast("Bienvenido al Sistema de Becas SG UNI", icon="👋")


# NUEVO: Tarjeta de número con animación de conteo (0 -> valor). El estilo está en style.css (.kpi y .cuenta).
def tarjeta_numero(etiqueta, valor):
    return (
        f'<div class="kpi"><span>{etiqueta}</span>'
        f'<strong class="cuenta" style="--valor:{valor}"></strong></div>'
    )


# 4. Definición de funciones contenedoras para el contenido de cada página de la aplicación.
# CAMBIO: Anteriormente la lógica se evaluaba mediante un bloque condicional 'if pagina == "Inicio": ... elif ...'.
#         Ahora cada sección está encapsulada en su propia función modular para integrarse limpiamente con st.navigation().
def pagina_inicio():
    # Banner de bienvenida principal: lee la plantilla HTML y realiza un formateo de huecos (placeholders) mediante .format()
    banner = (CARPETA / "plantillas" / "banner.html").read_text(encoding="utf-8")
    st.markdown(
        banner.format(
            titulo="Sistema de Gestión y Seguimiento de Becas",
            subtitulo="Administra estudiantes, registra su rendimiento académico y consulta el estado de las becas.",
        ),
        unsafe_allow_html=True,
    )

    # --- Cálculo de métricas y contadores para el resumen general ---
    total_estudiantes = len(datos["estudiantes"])

    # Conteo acumulativo de la cantidad total de semestres registrados sumando los historiales de todos los estudiantes
    total_semestres = 0
    for historial in datos["academico"].values():
        total_semestres += len(historial)

    # Conteo de cuántos estudiantes cumplen estrictamente con los requisitos de beca evaluando su ÚLTIMO semestre cursado
    con_beca = 0
    for historial in datos["academico"].values():
        if historial:
            ultimo = historial[-1]
            if ultimo["Promedio"] >= PROMEDIO and ultimo["Reprobados"] == REPROBADO:
                con_beca += 1

    # --- Despliegue visual de tarjetas de números organizadas en 3 columnas ---
    # CAMBIO: Antes eran st.metric; ahora son tarjetas HTML cuyos números cuentan desde 0 al abrir la página.
    col1, col2, col3 = st.columns(3)
    col1.markdown(tarjeta_numero("Estudiantes registrados", total_estudiantes), unsafe_allow_html=True)
    col2.markdown(tarjeta_numero("Semestres registrados", total_semestres), unsafe_allow_html=True)
    col3.markdown(tarjeta_numero("Cumplen requisitos de beca", con_beca), unsafe_allow_html=True)

    st.write("")  # Espaciador visual vertical en blanco

    # NUEVO: Accesos rápidos. Botones grandes que llevan directo a cada página del sistema.
    #        PAGINAS se define más abajo, pero esta función se ejecuta después, cuando ya existe.
    acceso1, acceso2, acceso3 = st.columns(3)
    acceso1.page_link(PAGINAS[1], label="Agregar estudiante", icon=":material/person_add:")
    acceso2.page_link(PAGINAS[2], label="Registrar semestre", icon=":material/edit_note:")
    acceso3.page_link(PAGINAS[3], label="Consultar becas", icon=":material/search:")

    st.write("")

    # Agrupación y clasificación del estado de beca de cada estudiante para el resumen general y el ranking de mejores promedios.
    # Emplea la función estado_beca() importada de consulta_becas.py para asegurar consistencia idéntica en toda la app.
    conteo = {"Con beca": 0, "Sin beca": 0, "Sin registro": 0}
    ranking = []
    for carnet, estudiante in datos["estudiantes"].items():
        historial = datos["academico"].get(carnet, [])
        estado, motivo = estado_beca(historial)
        conteo[estado] += 1
        if historial:   # Condición: Solo ingresan al ranking de honor aquellos estudiantes que posean al menos un semestre cursado
            ranking.append({
                "Estudiante": estudiante["Nombre"],
                "Carrera": estudiante["carrera"],
                "Último promedio": historial[-1]["Promedio"],
                "Estado": estado,
            })

    # División de la interfaz principal en dos columnas simétricas
    izquierda, derecha = st.columns(2)

    # Columna izquierda -> Tarjetas de colores estilizadas que reflejan el desglose del estado global de las becas
    with izquierda:
        st.subheader("Estado de las becas")
        tarjetas = st.columns(3)
        for columna, estado in zip(tarjetas, conteo):
            # CAMBIO: El número usa la clase "cuenta" para animarse de 0 al valor final
            columna.markdown(
                f'<div class="stat stat-{CLASES[estado]}"><span>{estado}</span>'
                f'<strong class="cuenta" style="--valor:{conteo[estado]}"></strong></div>',
                unsafe_allow_html=True,
            )

        st.write("")
        # Barra de progreso porcentual: calcula la proporción de estudiantes evaluados que califican exitosamente a la beca
        evaluados = conteo["Con beca"] + conteo["Sin beca"]
        if evaluados > 0:
            porcentaje = conteo["Con beca"] / evaluados
            st.progress(
                porcentaje,
                text=f"{conteo['Con beca']} de {evaluados} estudiantes evaluados cumplen los requisitos ({porcentaje:.0%})",
            )
        else:
            st.caption("Aún no hay semestres registrados para evaluar las becas.")

    # Columna derecha -> Ranking de los mejores últimos promedios, con filtro por estado y vista de tabla o gráfica
    with derecha:
        st.subheader("Mejores promedios")
        if ranking:
            # NUEVO: Filtro interactivo por estado de beca. Si el usuario desmarca la opción, se muestran todos.
            filtro = st.segmented_control(
                "Filtrar por estado",
                ["Todos", "Con beca", "Sin beca"],
                default="Todos",
                key="filtro_ranking",
                label_visibility="collapsed",
            ) or "Todos"
            filas = [f for f in ranking if filtro == "Todos" or f["Estado"] == filtro]

            # Ordena la lista de diccionarios de mayor a menor basándose en la clave "Último promedio"
            filas.sort(key=lambda fila: fila["Último promedio"], reverse=True)
            filas = filas[:TOP_RANKING]

            # NUEVO: Dos vistas del mismo ranking: tabla y gráfica de barras
            pestana_tabla, pestana_grafica = st.tabs(["Tabla", "Gráfica"])
            with pestana_tabla:
                if filas:
                    st.dataframe(
                        pd.DataFrame(filas),
                        width="stretch",
                        hide_index=True,
                        column_config={
                            "Último promedio": st.column_config.ProgressColumn(
                                "Último promedio", min_value=0, max_value=100, format="%.1f"
                            ),
                        },
                    )
                else:
                    st.info("Ningún estudiante tiene ese estado.")
            with pestana_grafica:
                if filas:
                    st.bar_chart(
                        pd.DataFrame(filas),
                        x="Estudiante",
                        y="Último promedio",
                        color=COLOR_GRAFICA,
                        height=250,
                    )
                else:
                    st.info("Ningún estudiante tiene ese estado.")
        else:
            st.info("Registra semestres en Académico para ver el ranking.")

    # --- Componente desplegable con una guía rápida de uso del sistema para orientar al usuario ---
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


def pagina_estudiantes():
    modulo_estudiantes(datos)        # Ejecuta y renderiza el módulo de gestión de estudiantes (creado por Yahosca)


def pagina_academico():
    modulo_academico(datos)          # Ejecuta y renderiza el módulo de control académico y notas (creado por Darlenne)


def pagina_consulta():
    modulo_consulta_becas(datos)     # Ejecuta y renderiza el módulo de evaluación y consulta de becas (creado por Jeffry)


# 5. Definición de la estructura de navegación de la aplicación en un solo punto centralizado.
# CAMBIO: Antes se utilizaba una lista de textos plano (PAGINAS = ["Inicio", ...]) combinada con controles en st.sidebar.radio.
#         Ahora cada sección se declara formalmente mediante st.Page (asignando título, icono de Material Design y la función vinculada).
#         st.navigation se encarga de estructurar el menú en una BARRA DE NAVEGACIÓN SUPERIOR limpia gracias a position="top".
PAGINAS = [
    st.Page(pagina_inicio, title="Inicio", icon=":material/home:", default=True),
    st.Page(pagina_estudiantes, title="Estudiantes", icon=":material/groups:"),
    st.Page(pagina_academico, title="Académico", icon=":material/school:"),
    st.Page(pagina_consulta, title="Consulta de becas", icon=":material/workspace_premium:"),
]

# CAMBIO: Se eliminó por completo la barra lateral. Toda la navegación principal va en la parte superior
#         (position="top"), dentro de la barra redondeada que dibuja style.css.
pagina = st.navigation(PAGINAS, position="top")

# 6. Ejecución y renderizado dinámico de la página seleccionada por el usuario en la barra superior.
# CAMBIO: Se reemplazaron los bloques condicionales anidados if / elif; ahora el método integrado .run() procesa y dibuja la vista activa.
pagina.run()