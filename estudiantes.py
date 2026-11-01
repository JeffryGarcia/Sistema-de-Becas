# =============================================================================
# estudiantes.py -> Módulo de ESTUDIANTES (Yahosca)
#
# Los estudiantes se guardan en el diccionario `datos` así:
#   datos["estudiantes"] = { "carnet (como texto)": {datos del estudiante} }
# Marcas de los comentarios:
#   # NUEVO:  -> algo que se agregó en esta versión
#   # CAMBIO: -> algo que ya existía y se modificó
# =============================================================================

import re   # NUEVO: Importación del módulo de expresiones regulares para validar nombre, carnet, carrera y correo mediante patrones estrictos
from pathlib import Path
import streamlit as st
from archivos import guardar_datos
from academico import CLAVE_ADMIN   # Importación de la clave administrativa compartida desde el módulo Académico

# NUEVO: Centralización de las reglas de validación en constantes globales para facilitar su mantenimiento y modificación
EDAD_MIN = 16     # Edad mínima permitida para ser considerado estudiante universitario
EDAD_MAX = 60     # Edad máxima aceptada dentro del sistema
# Patrón Regex para textos: Palabras formadas solo por letras (incluyendo tildes y ñ), separadas por espacio, guion o apóstrofe.
# Ejemplo válido: "María López", "Ingenieria en sistemas". No acepta números ni símbolos especiales.
PATRON_TEXTO = r"[^\W\d_]+(?:[ '\-][^\W\d_]+)*"
# Patrón Regex para carnet: Exclusivamente números, con una longitud de 6 o 7 dígitos, prohibiendo que comience con el dígito 0.
PATRON_CARNET = r"[1-9]\d{5,6}"
# Patrón Regex para correo: Estructura estándar texto@dominio.extension, sin espacios intermedios.
PATRON_CORREO = r"[^@\s]+@[^@\s]+\.[A-Za-z]{2,}"

# Obtiene la ruta base del directorio actual de app.py utilizando pathlib
BASE_DIR = Path(__file__).parent
LOGO = BASE_DIR / "assets" / "logo_claro.png"

# Verificación rápida opcional para depuración de la existencia del archivo de logotipo
if not LOGO.exists():
    st.error(f"No se encontró el logotipo en la ruta: {LOGO}")
else:
    st.logo(str(LOGO), size="large")

# Diccionario con estudiantes iniciales de ejemplo (utilizado únicamente la primera vez que se inicializa el sistema)
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


# Función de negocio: Agrega un estudiante al diccionario principal. Retorna True si se añade exitosamente, o False en caso contrario.
def agregar_estudiante(datos, nombre, edad, carnet, carrera, correo):
    # Condición de guarda: Si algún campo está vacío o en cero, emite una alerta y frena el registro
    if nombre == "" or edad == 0 or carnet == 0 or carrera == "" or correo == "":
        st.error("Por favor, complete todos los campos.")
        return False

    # Almacena el perfil del estudiante empleando su número de carnet transformado en cadena (texto) como clave única del diccionario
    datos["estudiantes"][str(int(carnet))] = {
        "Nombre": nombre,
        "Edad": int(edad),
        "carnet": int(carnet),
        "carrera": carrera,
        "correo": correo,
    }
    return True


# Función principal que renderiza el módulo "Estudiantes" dentro de la interfaz web de Streamlit
def modulo_estudiantes(datos):
    st.title("Estudiantes")

    # Muestra un mensaje temporal de éxito persistido en session_state tras agregar o eliminar registros
    if "est_mensaje" in st.session_state:
        st.success(st.session_state.pop("est_mensaje"))

    # Estructura la vista en dos pestañas (tabs): una para visualizar la lista general y otra para el formulario de registro
    tab_lista, tab_agregar = st.tabs(["Lista de estudiantes", "Agregar estudiante"])

    # Se procesa primero la pestaña de adición y luego la lista para garantizar que la tabla refleje los datos actualizados al instante
    with tab_agregar:
        st.subheader("Agregar nuevo estudiante")
        st.caption("Completa todos los campos y presiona el botón para registrarlo.")

        # CAMBIO: Se eliminó el uso de st.form. Dentro de los formularios nativos de Streamlit no se validaba en vivo
        #         hasta pulsar el botón de envío, impidiendo deshabilitarlo. Ahora se valida dinámicamente campo por campo.
        # NUEVO: Control de versión (est_add_v) para limpiar los campos del formulario tras agregar un estudiante con éxito
        va = st.session_state.setdefault("est_add_v", 0)

        # Fila 1: Campos de Nombre y Carnet distribuidos en dos columnas paralelas
        col1, col2 = st.columns(2)
        nombre = col1.text_input("Nombre", placeholder="Ej: María López", key=f"est_nombre_{va}")
        # CAMBIO: El campo de carnet migró de number_input a text_input para permitir la validación directa de su formato estructurado
        carnet_texto = col2.text_input("Carnet", placeholder="Ej: 1234567", key=f"est_carnet_{va}")

        # Fila 2: Campos de Edad y Carrera distribuidos en dos columnas paralelas
        col3, col4 = st.columns(2)
        # CAMBIO: Se define value=None para mantener la casilla inicialmente vacía en lugar de precargar un cero predeterminado
        edad = col3.number_input("Edad", min_value=0, max_value=120, step=1, value=None,
                                   key=f"est_edad_{va}")
        carrera = col4.text_input("Carrera", placeholder="Ej: Ingenieria civil",
                                  key=f"est_carrera_{va}")

        # Fila 3: Campo de Correo electrónico abarcando todo el ancho disponible de la pantalla
        correo = st.text_input("Correo", placeholder="ejemplo@correo.com", key=f"est_correo_{va}")

        # NUEVO: Acumulador de errores dinámico para recolectar las fallas de validación en tiempo real
        errores = []

        # Validación del campo Nombre: obligatorio, con caracteres alfabéticos válidos y longitud mínima de 2 caracteres
        if not nombre.strip():
            errores.append("Nombre")
        elif len(nombre.strip()) < 2 or not re.fullmatch(PATRON_TEXTO, nombre.strip()):
            errores.append("Nombre (solo letras y espacios, mínimo 2 letras)")

        # Validación del campo Carnet: obligatorio, estrictamente numérico, de 6 o 7 dígitos, sin iniciar en 0 y no duplicado
        if not carnet_texto.strip():
            errores.append("Carnet")
        elif not re.fullmatch(PATRON_CARNET, carnet_texto.strip()):
            errores.append("Carnet (solo números, de 6 o 7 dígitos y sin empezar en 0)")
        elif carnet_texto.strip() in datos["estudiantes"]:
            errores.append(f"Carnet (ya existe un estudiante con el carnet {carnet_texto.strip()})")

        # Validación del campo Edad: obligatorio y comprendido dentro de los límites del rango universitario establecido
        if edad is None:
            errores.append("Edad")
        elif not EDAD_MIN <= edad <= EDAD_MAX:
            errores.append(f"Edad (debe estar entre {EDAD_MIN} y {EDAD_MAX} años)")

        # (Nota: La validación estricta de carrera se mantiene comentada opcionalmente en el código fuente original)
        # if not carrera.strip():
        #     errores.append("Carrera")
        # elif len(carrera.strip()) < 3 or not re.fullmatch(PATRON_TEXTO, carrera.strip()):
        #     errores.append("Carrera (solo letras y espacios, mínimo 3 letras)")

        # Validación del campo Correo: obligatorio y adaptado al patrón formal de estructura de e-mail
        if not correo.strip():
            errores.append("Correo")
        elif not re.fullmatch(PATRON_CORREO, correo.strip()):
            errores.append("Correo (formato ejemplo@correo.com)")

        # NUEVO: Despliegue dinámico de avisos advirtiendo los campos faltantes o con formato incorrecto
        if errores:
            st.warning("Complete o corrija estos campos: " + ", ".join(errores) + ".")

        # CAMBIO: Sustitución de st.form_submit_button por un botón convencional condicionado mediante disabled=bool(errores).
        #         De esta manera, el botón se bloquea automáticamente impidiendo registros defectuosos si hay campos inválidos.
        if st.button("Agregar estudiante", type="primary", width="stretch",
                     disabled=bool(errores)):
            if agregar_estudiante(datos, nombre.strip(), int(edad), int(carnet_texto.strip()),
                                  carrera.strip(), correo.strip()):
                guardar_datos(datos)   # Persiste los cambios estructurales guardándolos directamente en becas.json
                # NUEVO: Almacena el mensaje de confirmación, incrementa el índice de versión del formulario y recarga la app
                st.session_state["est_mensaje"] = f"Estudiante {nombre.strip()} agregado correctamente."
                st.session_state["est_add_v"] = va + 1
                st.rerun()

    with tab_lista:
        st.subheader("Estudiantes registrados")

        # Campo de búsqueda en vivo: filtra la tabla de manera reactiva conforme el usuario introduce texto (nombre o carnet)
        buscar = st.text_input("Buscar", placeholder="Escribe un nombre o un carnet...")

        # Construcción de la lista filtrada de estudiantes según los criterios ingresados en el buscador
        lista = []
        for estudiante in datos["estudiantes"].values():
            if buscar.lower() in estudiante["Nombre"].lower() or buscar in str(estudiante["carnet"]):
                lista.append(estudiante)

        # Renderizado de la tabla de datos y pie de página informativo con métricas de conteo de registros mostrados
        st.dataframe(lista, width="stretch", hide_index=True)
        st.caption(f"Mostrando {len(lista)} de {len(datos['estudiantes'])} estudiantes")

        # Panel colapsable de opciones de administrador protegido por contraseña para eliminar registros de estudiantes
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

                # Control de versión para limpiar la selección de elementos múltiples tras la eliminación
                vd = st.session_state.setdefault("est_del_v", 0)

                # Mapea y estructura las opciones del selector múltiple visualizando 'carnet - nombre' y asociándolas al carnet clave
                opciones_eliminar = {}
                for carnet_est, est in datos["estudiantes"].items():
                    opciones_eliminar[f"{carnet_est} - {est['Nombre']}"] = carnet_est

                elegidos = st.multiselect("Estudiantes a eliminar", list(opciones_eliminar.keys()),
                                          key=f"est_del_sel_{vd}")
                confirmar = st.checkbox("Confirmo que quiero eliminar a los estudiantes seleccionados",
                                        key=f"est_del_conf_{vd}")

                # Acción de eliminación masiva: se ejecuta solo si se seleccionan estudiantes y se marca la casilla de confirmación
                if st.button("Eliminar estudiantes seleccionados", disabled=not (elegidos and confirmar)):
                    for etiqueta in elegidos:
                        carnet_borrar = opciones_eliminar[etiqueta]
                        # Elimina el perfil del estudiante del diccionario principal...
                        datos["estudiantes"].pop(carnet_borrar, None)
                        # ...y remueve también su historial académico asociado, evitando registros huérfanos en el sistema
                        datos["academico"].pop(carnet_borrar, None)
                        
                    guardar_datos(datos)   # Actualiza y guarda los cambios persistentes en el archivo JSON
                    st.session_state["est_mensaje"] = f"Se eliminaron {len(elegidos)} estudiante(s)."
                    st.session_state["est_del_v"] = vd + 1
                    st.rerun()