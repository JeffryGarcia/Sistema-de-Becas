import streamlit as st
import pandas as pd

# 1. Configuración de la página (debe ser el PRIMER comando de Streamlit)
st.set_page_config(
    page_title="Sistema de Becas",
    page_icon="🎓",
    layout="wide",
)

# Requisitos para mantener la beca (usados en el módulo Académico)
PROMEDIO = 85.0
REPROBADO = 0

# 2. Datos: todo vive en st.session_state para que NO se reinicie
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

# Historial académico: {carnet (str): [ {Semestre, Promedio, Aprobado, Reprobados}, ... ]}
if "academico" not in st.session_state:
    st.session_state.academico = {}


def obtener_datos():
    """Arma el diccionario `datos` que espera registro_semestre().

    - datos["estudiantes"]: {carnet (str): info del estudiante}
    - datos["academico"]:   el historial guardado en session_state
    """
    return {
        "estudiantes": {str(e["carnet"]): e for e in st.session_state.estud_beca},
        "academico": st.session_state.academico,
    }


# ---------------------------------------------------------------------------
# Lógica de Estudiantes (Yahosca)
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Lógica de Académico (Darlenne)
# ---------------------------------------------------------------------------
def registro_semestre(datos: dict, carnet: str, semestre: str, promedio: float, aprobadas: int, reprobadas: int):
    """Valida y registra el semestre de un estudiante.

    Devuelve (ok: bool, mensaje: str) para que la interfaz pueda mostrar
    st.success o st.error según el resultado.
    """
    if carnet not in datos["estudiantes"]:
        return False, "Su número de carnet no corresponde a ningún estudiante"
    if not semestre.strip():
        return False, "Debe especificar su semestre"
    if not (0.0 <= promedio <= 100):
        return False, "Ingrese un promedio entre 0.0 y 100.0"
    if not isinstance(aprobadas, int) or not isinstance(reprobadas, int):
        return False, "El número de asignaturas debe ser entero"
    if aprobadas < 0 or reprobadas < 0:
        return False, "El número de asignaturas no puede ser negativo"

    historial = datos["academico"].setdefault(carnet, [])
    historial.append(
        {
            "Semestre": semestre.strip(),
            "Promedio": promedio,
            "Aprobado": aprobadas,
            "Reprobados": reprobadas,
        }
    )
    return True, "Se ha registrado su semestre"


# ---------------------------------------------------------------------------
# Módulos de interfaz
# ---------------------------------------------------------------------------
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


def modulo_academico():
    st.title("Académico")

    if "mensaje_academico" in st.session_state:
        st.success(st.session_state.pop("mensaje_academico"))

    tab_registro, tab_historial = st.tabs(["Registrar semestre", "Historial académico"])

    datos = obtener_datos()
    opciones = {
        f'{e["carnet"]} - {e["Nombre"]}': str(e["carnet"])
        for e in st.session_state.estud_beca
    }

    with tab_registro:
        st.subheader("Registrar semestre")
        with st.form(key="registro_semestre_form", clear_on_submit=True):
            seleccion = st.selectbox("Estudiante", list(opciones.keys()))
            semestre = st.text_input("Semestre (ej: 2026-I)")
            promedio = st.number_input("Promedio", min_value=0.0, max_value=100.0, step=0.1)
            aprobadas = st.number_input("Asignaturas aprobadas", min_value=0, step=1)
            reprobadas = st.number_input("Asignaturas reprobadas", min_value=0, step=1)

            enviado = st.form_submit_button("Registrar semestre")

        if enviado:
            ok, mensaje = registro_semestre(
                datos,
                opciones[seleccion],
                semestre,
                float(promedio),
                int(aprobadas),
                int(reprobadas),
            )
            if ok:
                st.session_state.mensaje_academico = mensaje
                st.rerun()
            else:
                st.error(mensaje)

    with tab_historial:
        st.subheader("Historial académico")
        if not opciones:
            st.info("No hay estudiantes registrados.")
            return

        seleccion_h = st.selectbox("Estudiante", list(opciones.keys()), key="sel_historial")
        carnet_h = opciones[seleccion_h]
        historial = st.session_state.academico.get(carnet_h, [])

        if not historial:
            st.info("Este estudiante aún no tiene semestres registrados.")
        else:
            df = pd.DataFrame(historial)
            df["Cumple requisitos"] = (df["Promedio"] >= PROMEDIO) & (df["Reprobados"] == REPROBADO)
            df["Cumple requisitos"] = df["Cumple requisitos"].map({True: "Sí", False: "No"})
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(
                f"Requisitos: promedio ≥ {PROMEDIO} y {REPROBADO} asignaturas reprobadas."
            )


# ---------------------------------------------------------------------------
# Navegación
# ---------------------------------------------------------------------------
PAGINAS = ["Inicio", "Estudiantes", "Académico", "Consulta de becas"]

st.sidebar.title("Sistema de Becas 🎓")
pagina = st.sidebar.radio("Navegación", PAGINAS)
st.sidebar.info("Sistema de Gestión y Seguimiento de Becas")

if pagina == "Inicio":
    st.title("Sistema de Gestión y Seguimiento de Becas")
    st.write("Bienvenido.")

elif pagina == "Estudiantes":
    modulo_estudiantes()

elif pagina == "Académico":
    modulo_academico()

elif pagina == "Consulta de becas":
    st.title("Consulta de becas")
    st.info("En construcción (Jeffry)")