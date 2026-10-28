import Streamlit as st

# 1. Configuración de la página (debe ser el PRIMER comando de Streamlit)
st.set_page_config(
    page_title="Sistema de Becas UNI",
    page_icon="🎓",
    layout="wide",
)

# 2. Lista de páginas: un solo lugar para agregar o renombrar secciones
PAGINAS = ["Inicio", "Estudiantes", "Académico", "Consulta de becas"]

# 3. Barra lateral con el menú
st.sidebar.title("Sistema de Becas ")
pagina = st.sidebar.radio("Navegación", PAGINAS)

# 4. Mostrar contenido según la página elegida
if pagina == "Inicio":
    st.title("Sistema de Gestión y Seguimiento de Becas")
    st.write("Bienvenido.")

elif pagina == "Estudiantes":
    st.title("Estudiantes")
    st.info("En construcción (Yahosca)")

elif pagina == "Académico":
    st.title("Académico")
    st.info("En construcción (Darlenne)")

elif pagina == "Consulta de becas":
    st.title("Consulta de becas")
    st.info("En construcción (Jeffry)")