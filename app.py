import streamlit as st

# 1. Configuración de la página (debe ser el PRIMER comando de Streamlit)
st.set_page_config(
    page_title="Sistema de Becas",
    page_icon="🎓",
    layout="wide",
)

# 2. Datos: la lista vive en st.session_state para que NO se reinicie
#    cada vez que Streamlit vuelve a ejecutar el script.
ESTUDIANTES_INICIALES = [
    {
        "Nombre": "Luis",
        "Edad": 18,
        "carnet": 5647097,
        "carrera": "Ingenieria electronica",
        "correo": "luis@example.com",
    },
    {
        "Nombre": "Elena",
        "Edad": 21,
        "carnet": 150408,
        "carrera": "Ingenieria civil",
        "correo": "elena@example.com",
    },
    {
        "Nombre": "Martin",
        "Edad": 25,
        "carnet": 9876542,
        "carrera": "Ingenieria en sistemas",
        "correo": "mar@example.com",
    },
    {
        "Nombre": "Andres",
        "Edad": 22,
        "carnet": 1234567,
        "carrera": "Ingenieria industrial",
        "correo": "andres@example.com",
    },
    {
        "Nombre": "Valeria",
        "Edad": 24,
        "carnet": 1987450,
        "carrera": "Ingenieria Computacion",
        "correo": "valeria@example.com",
    },
]

if "estud_beca" not in st.session_state:
    st.session_state.estud_beca = list(ESTUDIANTES_INICIALES)


def agregar_estudiante(nombre, edad, carnet, carrera, correo):
    """Agrega un estudiante a la lista global (guardada en session_state)."""
    estudiante = {
        "Nombre": nombre,
        "Edad": int(edad),
        "carnet": int(carnet),
        "carrera": carrera,
        "correo": correo,
    }
    st.session_state.estud_beca.append(estudiante)


def carnet_existe(carnet):
    return any(e["carnet"] == int(carnet) for e in st.session_state.estud_beca)


# 3. Módulo de Estudiantes (Yahosca)
def modulo_estudiantes():
    st.title("Estudiantes")

    if "mensaje_ok" in st.session_state:
        st.success(st.session_state.pop("mensaje_ok"))

    tab_lista, tab_agregar = st.tabs(["Lista de estudiantes", "Agregar estudiante"])

    with tab_lista:
        st.subheader("Estudiantes registrados")
        st.dataframe(
            st.session_state.estud_beca,
            use_container_width=True,
            hide_index=True,
        )
        st.caption(f"Total: {len(st.session_state.estud_beca)} estudiantes")

    with tab_agregar:
        st.subheader("Agregar nuevo estudiante")
        with st.form(key="agregar_estudiante_form", clear_on_submit=True):
            nombre = st.text_input("Nombre")
            edad = st.number_input("Edad", min_value=0, max_value=120, step=1)
            carnet = st.number_input("Carnet", min_value=0, step=1, format="%d")
            carrera = st.text_input("Carrera")
            correo = st.text_input("Correo")

            enviado = st.form_submit_button("Agregar Estudiante")

        if enviado:
            if not nombre.strip() or not carrera.strip() or not correo.strip():
                st.error("Nombre, carrera y correo son obligatorios.")
            elif "@" not in correo:
                st.error("El correo no es válido.")
            elif carnet_existe(carnet):
                st.error(f"Ya existe un estudiante con el carnet {int(carnet)}.")
            else:
                agregar_estudiante(nombre.strip(), edad, carnet, carrera.strip(), correo.strip())
                st.session_state.mensaje_ok = f"Estudiante {nombre.strip()} agregado correctamente."
                st.rerun()  # refresca la tabla con el nuevo estudiante


# 4. Lista de páginas: un solo lugar para agregar o renombrar secciones
PAGINAS = ["Inicio", "Estudiantes", "Académico", "Consulta de becas"]

# 5. Barra lateral con el menú
st.sidebar.title("Sistema de Becas 🎓")
pagina = st.sidebar.radio("Navegación", PAGINAS)
st.sidebar.info("Sistema de Gestión y Seguimiento de Becas")

# 6. Mostrar contenido según la página elegida
if pagina == "Inicio":
    st.title("Sistema de Gestión y Seguimiento de Becas")
    st.write("Bienvenido.")

elif pagina == "Estudiantes":
    modulo_estudiantes()

elif pagina == "Académico":
    st.title("Académico")
    st.info("En construcción (Darlenne)")

elif pagina == "Consulta de becas":
    st.title("Consulta de becas")
    st.info("En construcción (Jeffry)")