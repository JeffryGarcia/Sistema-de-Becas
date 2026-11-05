# =============================================================================
# estudiantes.py -> Módulo de ESTUDIANTES (Yahosca)
#
# Los estudiantes se guardan en el diccionario `datos` así:
#   datos["estudiantes"] = { "carnet (como texto)": {datos del estudiante} }
# Marcas de los comentarios:
#   # NUEVO:  -> algo que se agregó en esta versión
#   # CAMBIO: -> algo que ya existía y se modificó
# =============================================================================

import re
from pathlib import Path
import streamlit as st
from archivos import guardar_o_detener
from academico import CLAVE_ADMIN
from carreras import CARRERAS, canonica   # NUEVO: catálogo oficial de carreras

# Reglas de validación centralizadas
EDAD_MIN = 16
EDAD_MAX = 60
# NUEVO: Límites de longitud para evitar textos absurdamente largos
NOMBRE_MIN = 2
NOMBRE_MAX = 60
CORREO_MAX = 100

# Palabras formadas solo por letras (con tildes y ñ), separadas por UN espacio, guion o apóstrofe.
PATRON_TEXTO = r"[^\W\d_]+(?:[ '\-][^\W\d_]+)*"
# Carnet: solo números, 6 o 7 dígitos, sin empezar en 0.
PATRON_CARNET = r"[1-9]\d{5,6}"
# CAMBIO: Correo más estricto: usuario con caracteres válidos, dominio con puntos y extensión de 2+ letras.
PATRON_CORREO = r"[A-Za-z0-9._%+\-]+@(?:[A-Za-z0-9](?:[A-Za-z0-9\-]*[A-Za-z0-9])?\.)+[A-Za-z]{2,}"



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


# NUEVO: ÚNICA fuente de reglas de validación. La usan tanto la interfaz (en vivo) como agregar_estudiante
#        (respaldo), así nunca pueden quedar desincronizadas. Devuelve una lista de errores (vacía si todo está bien).
def validar_estudiante(datos, nombre, edad, carnet_texto, carrera, correo):
    errores = []
    nombre = (nombre or "").strip()
    carnet_texto = (carnet_texto or "").strip()
    carrera = (carrera or "").strip()
    correo = (correo or "").strip()

    # --- Nombre ---
    if not nombre:
        errores.append("Nombre")
    elif len(nombre) < NOMBRE_MIN or not re.fullmatch(PATRON_TEXTO, nombre):
        errores.append(f"Nombre (solo letras, mínimo {NOMBRE_MIN}; un solo espacio entre palabras)")
    elif len(nombre) > NOMBRE_MAX:
        errores.append(f"Nombre (máximo {NOMBRE_MAX} caracteres)")

    # --- Carnet ---
    if not carnet_texto:
        errores.append("Carnet")
    elif not re.fullmatch(PATRON_CARNET, carnet_texto):
        errores.append("Carnet (solo números, de 6 o 7 dígitos y sin empezar en 0)")
    elif carnet_texto in datos["estudiantes"]:
        errores.append(f"Carnet (ya existe un estudiante con el carnet {carnet_texto})")

    # --- Edad ---
    if edad is None:
        errores.append("Edad")
    elif edad != int(edad):
        errores.append("Edad (debe ser un número entero)")
    elif not EDAD_MIN <= edad <= EDAD_MAX:
        errores.append(f"Edad (debe estar entre {EDAD_MIN} y {EDAD_MAX} años)")

    # --- Carrera --- (CAMBIO: ahora debe ser una carrera del catálogo oficial)
    if not carrera:
        errores.append("Carrera")
    elif canonica(carrera) is None:
        errores.append("Carrera (elige una de la lista)")

    # --- Correo ---
    if not correo:
        errores.append("Correo")
    elif len(correo) > CORREO_MAX:
        errores.append(f"Correo (máximo {CORREO_MAX} caracteres)")
    elif (not re.fullmatch(PATRON_CORREO, correo) or ".." in correo
          or correo.split("@")[0].startswith(".") or correo.split("@")[0].endswith(".")):
        errores.append("Correo (formato ejemplo@correo.com)")
    else:
        # NUEVO: no se permite que dos estudiantes compartan el mismo correo
        for est in datos["estudiantes"].values():
            if str(est.get("correo", "")).strip().lower() == correo.lower():
                errores.append("Correo (ya lo usa otro estudiante)")
                break

    return errores


# Agrega un estudiante al diccionario principal. Retorna True si se añade, False si no.
# CAMBIO: antes solo verificaba campos vacíos/cero; ahora re-valida todo con validar_estudiante().
def agregar_estudiante(datos, nombre, edad, carnet, carrera, correo):
    errores = validar_estudiante(datos, nombre, edad, str(carnet), carrera, correo)
    if errores:
        st.error("No se pudo registrar: " + ", ".join(errores) + ".")
        return False

    datos["estudiantes"][str(int(carnet))] = {
        "Nombre": nombre.strip(),
        "Edad": int(edad),
        "carnet": int(carnet),
        "carrera": canonica(carrera),   # CAMBIO: siempre se guarda el nombre oficial de la carrera
        "correo": correo.strip().lower(),   # CAMBIO: el correo se guarda en minúsculas
    }
    return True


def modulo_estudiantes(datos):
    st.title("Estudiantes")

    if "est_mensaje" in st.session_state:
        st.success(st.session_state.pop("est_mensaje"))

    tab_lista, tab_agregar = st.tabs(["Lista de estudiantes", "Agregar estudiante"])

    with tab_agregar:
        st.subheader("Agregar nuevo estudiante")
        st.caption("Completa todos los campos y presiona el botón para registrarlo.")

        va = st.session_state.setdefault("est_add_v", 0)

        col1, col2 = st.columns(2)
        # CAMBIO: max_chars en los campos de texto para impedir entradas excesivas
        nombre = col1.text_input("Nombre", placeholder="Ej: María López",
                                 max_chars=NOMBRE_MAX, key=f"est_nombre_{va}")
        carnet_texto = col2.text_input("Carnet", placeholder="Ej: 1234567",
                                       max_chars=7, key=f"est_carnet_{va}")

        col3, col4 = st.columns(2)
        # CAMBIO: los límites del widget ahora son los reales (antes 0-120, la regla se validaba aparte)
        edad = col3.number_input("Edad", min_value=EDAD_MIN, max_value=EDAD_MAX, step=1, value=None,
                                 key=f"est_edad_{va}")
        # CAMBIO: la carrera se elige de la lista oficial (antes era texto libre)
        carrera = col4.selectbox("Carrera", CARRERAS, index=None,
                                 placeholder="Elige una carrera", key=f"est_carrera_{va}")

        correo = st.text_input("Correo", placeholder="ejemplo@correo.com",
                               max_chars=CORREO_MAX, key=f"est_correo_{va}")

        # CAMBIO: toda la validación vive en validar_estudiante()
        errores = validar_estudiante(datos, nombre, edad, carnet_texto, carrera, correo)

        if errores:
            st.warning("Complete o corrija estos campos: " + ", ".join(errores) + ".")

        if st.button("Agregar estudiante", type="primary", width="stretch",
                     disabled=bool(errores)):
            if agregar_estudiante(datos, nombre, edad, int(carnet_texto.strip()),
                                  carrera, correo):
                guardar_o_detener(datos)
                st.session_state["est_mensaje"] = f"Estudiante {nombre.strip()} agregado correctamente."
                st.session_state["est_add_v"] = va + 1
                st.rerun()

    with tab_lista:
        st.subheader("Estudiantes registrados")

        buscar = st.text_input("Buscar", placeholder="Escribe un nombre o un carnet...",
                               max_chars=NOMBRE_MAX).strip()   # CAMBIO: se ignoran espacios al inicio/fin

        lista = []
        for estudiante in datos["estudiantes"].values():
            if buscar.lower() in estudiante["Nombre"].lower() or buscar in str(estudiante["carnet"]):
                lista.append(estudiante)

        st.dataframe(lista, width="stretch", hide_index=True)
        st.caption(f"Mostrando {len(lista)} de {len(datos['estudiantes'])} estudiantes")

        with st.expander("Opciones de administrador"):
            clave = st.text_input("Clave de administrador", type="password", key="est_clave")

            if clave != CLAVE_ADMIN:
                if clave:
                    st.error("Clave incorrecta.")
            elif not datos["estudiantes"]:
                st.info("No hay estudiantes para eliminar.")
            else:
                st.caption("Al eliminar un estudiante también se elimina todo su historial "
                           "académico. Esta acción no se puede deshacer.")

                vd = st.session_state.setdefault("est_del_v", 0)

                opciones_eliminar = {}
                for carnet_est, est in datos["estudiantes"].items():
                    opciones_eliminar[f"{carnet_est} - {est['Nombre']}"] = carnet_est

                elegidos = st.multiselect("Estudiantes a eliminar", list(opciones_eliminar.keys()),
                                          key=f"est_del_sel_{vd}")
                confirmar = st.checkbox("Confirmo que quiero eliminar a los estudiantes seleccionados",
                                        key=f"est_del_conf_{vd}")

                if st.button("Eliminar estudiantes seleccionados", disabled=not (elegidos and confirmar)):
                    for etiqueta in elegidos:
                        carnet_borrar = opciones_eliminar[etiqueta]
                        datos["estudiantes"].pop(carnet_borrar, None)
                        datos["academico"].pop(carnet_borrar, None)

                    guardar_o_detener(datos)
                    st.session_state["est_mensaje"] = f"Se eliminaron {len(elegidos)} estudiante(s)."
                    st.session_state["est_del_v"] = vd + 1
                    st.rerun()