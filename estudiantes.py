# =============================================================================
# estudiantes.py -> Módulo de ESTUDIANTES (Yahosca)
#
# Los estudiantes se guardan en el diccionario `datos` así:
#   datos["estudiantes"] = { "carnet (como texto)": {datos del estudiante} }
# =============================================================================

import streamlit as st
from archivos import guardar_datos

# Estudiantes de ejemplo (solo se usan la primera vez que corre el sistema)
ESTUDIANTES_INICIALES = {
    "5647097": {"Nombre": "Luis", "Edad": 18, "carnet": 5647097,
                "carrera": "Ingenieria electronica", "correo": "luis@example.com"},
    "150408": {"Nombre": "Elena", "Edad": 21, "carnet": 150408,
               "carrera": "Ingenieria civil", "correo": "elena@example.com"},
    "9876542": {"Nombre": "Martin", "Edad": 25, "carnet": 9876542,
                "carrera": "Ingenieria en sistemas", "correo": "mar@example.com"},
    "1234567": {"Nombre": "Andres", "Edad": 22, "carnet": 1234567,
                "carrera": "Ingenieria industrial", "correo": "andres@example.com"},
    "1987450": {"Nombre": "Valeria", "Edad": 24, "carnet": 1987450,
                "carrera": "Ingenieria Computacion", "correo": "valeria@example.com"},
}


# Agrega un estudiante a los datos. Devuelve True si se agregó, False si no.
def agregar_estudiante(datos, nombre, edad, carnet, carrera, correo):
    # Si falta algún campo, avisamos y no agregamos nada
    if nombre == "" or edad == 0 or carnet == 0 or carrera == "" or correo == "":
        st.error("Por favor, complete todos los campos.")
        return False

    # Guardamos al estudiante usando su carnet (como texto) de clave
    datos["estudiantes"][str(int(carnet))] = {
        "Nombre": nombre,
        "Edad": int(edad),
        "carnet": int(carnet),
        "carrera": carrera,
        "correo": correo,
    }
    return True


# Lo que se ve en la página "Estudiantes"
def modulo_estudiantes(datos):
    st.title("Estudiantes")

    # Dos pestañas: la lista y el formulario para agregar
    tab_lista, tab_agregar = st.tabs(["Lista de estudiantes", "Agregar estudiante"])

    # Llenamos primero "agregar" y después la lista,
    # así la tabla ya sale actualizada cuando se agrega alguien.
    with tab_agregar:
        st.subheader("Agregar nuevo estudiante")
        st.caption("Completa todos los campos y presiona el botón para registrarlo.")

        # El formulario se limpia solo después de enviarlo
        with st.form(key="agregar_estudiante_form", clear_on_submit=True):
            # Fila 1: nombre y carnet, uno al lado del otro
            col1, col2 = st.columns(2)
            nombre = col1.text_input("Nombre", placeholder="Ej: María López")
            carnet = col2.number_input("Carnet", min_value=0, step=1, format="%d")

            # Fila 2: edad y carrera
            col3, col4 = st.columns(2)
            edad = col3.number_input("Edad", min_value=0, max_value=120, step=1)
            carrera = col4.text_input("Carrera", placeholder="Ej: Ingenieria civil")

            # Fila 3: correo (ocupa todo el ancho)
            correo = st.text_input("Correo", placeholder="ejemplo@correo.com")

            # Botón principal, ocupa todo el ancho
            enviado = st.form_submit_button(
                "Agregar estudiante", type="primary", width="stretch"
            )

        # Esto solo corre cuando se presiona el botón
        if enviado:
            if "@" not in correo:
                st.error("El correo no es válido.")
            elif str(int(carnet)) in datos["estudiantes"]:
                st.error(f"Ya existe un estudiante con el carnet {int(carnet)}.")
            elif agregar_estudiante(datos, nombre.strip(), edad, carnet, carrera.strip(), correo.strip()):
                guardar_datos(datos)  # lo escribe en becas.json
                st.success(f"Estudiante {nombre.strip()} agregado correctamente.")

    with tab_lista:
        st.subheader("Estudiantes registrados")

        # Buscador: filtra la tabla mientras se escribe un nombre o carnet
        buscar = st.text_input("Buscar", placeholder="Escribe un nombre o un carnet...")

        # Nos quedamos solo con los estudiantes que coinciden con la búsqueda
        # (si no se escribe nada, aparecen todos)
        lista = []
        for estudiante in datos["estudiantes"].values():
            if buscar.lower() in estudiante["Nombre"].lower() or buscar in str(estudiante["carnet"]):
                lista.append(estudiante)

        st.dataframe(lista, width="stretch", hide_index=True)
        st.caption(f"Mostrando {len(lista)} de {len(datos['estudiantes'])} estudiantes")