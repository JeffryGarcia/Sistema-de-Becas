# =============================================================================
# academico.py -> Módulo académico (Darlenne)
#
# Marcas de los comentarios:
#   # NUEVO:  -> algo que se agregó en esta versión
#   # CAMBIO: -> algo que ya existía y se modificó
# =============================================================================

import re
from datetime import date   # NUEVO: para limitar el año del semestre a un rango razonable

import streamlit as st
import pandas as pd
from archivos import guardar_o_detener

# Definición de constantes globales para la evaluación de becas
PROMEDIO = 85.0
REPROBADO = 0

# Nota mínima requerida para aprobar una asignatura
NOTA_APROBATORIA = 60

# Clave de acceso administrativa requerida para habilitar la opción de eliminar semestres
CLAVE_ADMIN = "admin123"

# NUEVO: Reglas de validación de asignaturas y semestre, centralizadas para modificarlas fácilmente
MAX_ASIGNATURAS = 6           # Máximo de asignaturas por semestre
LARGO_MIN_ASIGNATURA = 2      # Mínimo de caracteres del nombre de una asignatura
LARGO_MAX_ASIGNATURA = 60     # Máximo de caracteres del nombre de una asignatura
ANIO_MIN_SEMESTRE = 2000      # Año más antiguo aceptado para un semestre
# Letras (con tildes/ñ) y números, más espacio . , ' - ( ) & : / +   (ej: "Cálculo II", "Física I (Lab)")
PATRON_ASIGNATURA = r"(?:[^\W_]|[ .,'\-()&:/+])+"


# NUEVO: Quita espacios sobrantes ("  Cálculo   II " -> "Cálculo II")
def limpiar_nombre(nombre) -> str:
    return " ".join(str(nombre).split())


# NUEVO: Valida el nombre de UNA asignatura. Devuelve "" si es correcto o el mensaje de error.
def validar_nombre_asignatura(nombre) -> str:
    nombre = limpiar_nombre(nombre)
    if not nombre:
        return "el nombre está vacío"
    if len(nombre) < LARGO_MIN_ASIGNATURA:
        return f"mínimo {LARGO_MIN_ASIGNATURA} caracteres"
    if len(nombre) > LARGO_MAX_ASIGNATURA:
        return f"máximo {LARGO_MAX_ASIGNATURA} caracteres"
    if not re.fullmatch(PATRON_ASIGNATURA, nombre):
        return "contiene caracteres no permitidos"
    if not re.search(r"[^\W\d_]", nombre):
        return "debe contener al menos una letra"
    return ""


# NUEVO: Valida TODA la lista de asignaturas (respaldo de seguridad en el backend, además de la interfaz).
#        Devuelve "" si todo está bien o un mensaje de error.
def validar_asignaturas(asignaturas) -> str:
    if not asignaturas:
        return "Debe ingresar al menos una asignatura"
    if len(asignaturas) > MAX_ASIGNATURAS:
        return f"No puede registrar más de {MAX_ASIGNATURAS} asignaturas por semestre"

    vistos = set()
    for i, a in enumerate(asignaturas, start=1):
        error = validar_nombre_asignatura(a.get("Nombre", ""))
        if error:
            return f"Asignatura {i}: {error}"

        clave = limpiar_nombre(a["Nombre"]).lower()
        if clave in vistos:
            return f"Asignatura {i}: '{limpiar_nombre(a['Nombre'])}' está repetida"
        vistos.add(clave)

        nota = a.get("Notas")
        # bool es subclase de int, se excluye explícitamente
        if isinstance(nota, bool) or not isinstance(nota, (int, float)):
            return f"Asignatura {i}: la nota debe ser un número"
        if nota != nota:   # NaN
            return f"Asignatura {i}: la nota no es válida"
        if not 0 <= nota <= 100:
            return f"Asignatura {i}: la nota debe estar entre 0 y 100"
    return ""


# Valida el semestre ingresado. Devuelve "" si es correcto, o un mensaje de error si falla.
#   - Solo se aceptan dos semestres por año: AAAA-I y AAAA-II (ej: 2026-I, 2026-II)
#   - CAMBIO: el año debe estar entre ANIO_MIN_SEMESTRE y el año siguiente al actual
#   - Un estudiante no puede tener el mismo semestre registrado dos veces
def validar_semestre(datos: dict, carnet: str, semestre: str):
    semestre = str(semestre).strip().upper()

    if not re.fullmatch(r"\d{4}-(I|II)", semestre):
        return "El semestre debe tener el formato AAAA-I o AAAA-II (ejemplo: 2026-I)"

    # NUEVO: rango de años permitido (evita "0001-I" o "9999-II")
    anio = int(semestre[:4])
    anio_max = date.today().year + 1
    if not ANIO_MIN_SEMESTRE <= anio <= anio_max:
        return f"El año del semestre debe estar entre {ANIO_MIN_SEMESTRE} y {anio_max}"

    for registro in datos["academico"].get(carnet, []):
        if str(registro.get("Semestre", "")).strip().upper() == semestre:
            return f"El semestre {semestre} ya está registrado para este estudiante"

    return ""


# Función auxiliar para ordenar el historial académico por fecha cronológica.
def clave_semestre(registro: dict):
    try:
        anio, periodo = registro["Semestre"].strip().upper().split("-")
        return (int(anio), 2 if periodo == "II" else 1)
    except (KeyError, AttributeError, ValueError):
        return (0, 0)


# Arma la tabla del historial visualizada en el módulo Académico y en Consulta de becas.
def tabla_historial(historial: list):
    tabla = pd.DataFrame(historial)
    cumple = (tabla["Promedio"] >= PROMEDIO) & (tabla["Reprobados"] <= REPROBADO)
    tabla["Cumple requisitos"] = cumple.map({True: "Sí", False: "No"})
    return tabla[["Semestre", "Promedio", "Reprobados", "Cumple requisitos"]]


# Función central: valida y registra formalmente el semestre del estudiante
def registro_semestre(datos: dict, carnet: str, semestre: str, asignaturas):
    if carnet not in datos["estudiantes"]:
        return "Su número de carnet no corresponde a ningún estudiante"

    if not str(semestre).strip():
        return "Debe especificar su semestre"

    error_semestre = validar_semestre(datos, carnet, semestre)
    if error_semestre:
        return error_semestre

    semestre = semestre.strip().upper()

    # CAMBIO: validación completa de asignaturas (vacías, repetidas, notas fuera de rango, etc.)
    error_asignaturas = validar_asignaturas(asignaturas)
    if error_asignaturas:
        return error_asignaturas

    # NUEVO: se guardan los nombres limpios y las notas redondeadas a 2 decimales
    limpias = [{"Nombre": limpiar_nombre(a["Nombre"]), "Notas": round(float(a["Notas"]), 2)}
               for a in asignaturas]

    resultados = calcular_resultados(limpias)

    Historial = datos["academico"].setdefault(carnet, [])

    nuevo_registro = {
        "Semestre": semestre,
        "Promedio": resultados["Promedio"],
        "Aprobado": resultados["Aprobado"],
        "Reprobados": resultados["Reprobados"],
        "Asignaturas": limpias,
    }

    Historial.append(nuevo_registro)
    Historial.sort(key=clave_semestre)
    return "Se ha registrado su semestre"


# Función de consola interactiva (legacy, NO se usa en Streamlit).
def solicitar_asignatura():
    asignaturas = []
    while True:
        try:
            cantidad = int(input("Ingrese cuantas asignaturas cursa actualmente:"))
            if 0 < cantidad <= MAX_ASIGNATURAS:   # CAMBIO: también respeta el máximo
                break
            print(f"Debe ingresar entre 1 y {MAX_ASIGNATURAS} asignaturas")
        except ValueError:
            print("Debe de ingresar un número entero")

    for i in range(cantidad):
        while True:   # CAMBIO: el nombre también se valida en consola
            nombre = limpiar_nombre(input(f"Ingrese el nombre de su asignatura:{i + 1}"))
            error = validar_nombre_asignatura(nombre)
            if not error:
                break
            print(f"Nombre no válido: {error}")
        while True:
            try:
                notas = float(input(f"Ingresa su nota de:{nombre}"))
                if 0 <= notas <= 100:
                    break
                print("La nota debe de estar entre 0 y 100")
            except ValueError:
                print("Error, verifique su respuesta, (Recuerde que debe ingresar un valor numerico)")

        asignaturas.append({"Nombre": nombre, "Notas": notas})

    return asignaturas


# Calcula el promedio aritmético, materias aprobadas y reprobadas
def calcular_resultados(asignaturas):
    # NUEVO: evita ZeroDivisionError si por error llega una lista vacía
    if not asignaturas:
        raise ValueError("No hay asignaturas para calcular el promedio")

    suma_notas = sum(a["Notas"] for a in asignaturas)
    prom = suma_notas / len(asignaturas)
    aprobadas = sum(1 for a in asignaturas if a["Notas"] >= NOTA_APROBATORIA)
    reprobados = len(asignaturas) - aprobadas

    return {
        "Promedio": round(prom, 2),
        "Aprobado": prom >= PROMEDIO and reprobados == REPROBADO,
        "Reprobados": reprobados,
    }


def reiniciar_formulario():
    st.session_state["aca_v"] = st.session_state.get("aca_v", 0) + 1
    st.session_state["aca_cantidad_ok"] = False
    st.session_state["aca_bloqueado"] = False


def modulo_academico(datos: dict):
    st.title("Académico")

    if not datos["estudiantes"]:
        st.warning("Primero debes registrar estudiantes.")
        return

    st.session_state.setdefault("aca_v", 0)
    st.session_state.setdefault("aca_cantidad_ok", False)
    st.session_state.setdefault("aca_bloqueado", False)

    if "aca_mensaje" in st.session_state:
        st.success(st.session_state.pop("aca_mensaje"))

    carnet = st.selectbox(
        "Estudiante",
        list(datos["estudiantes"].keys()),
        format_func=lambda c: f"{c} - {datos['estudiantes'][c]['Nombre']}",
        key="aca_carnet",
    )

    if "aca_carnet_activo" in st.session_state and st.session_state["aca_carnet_activo"] != carnet:
        reiniciar_formulario()
    st.session_state["aca_carnet_activo"] = carnet

    v = st.session_state["aca_v"]
    cantidad_ok = st.session_state["aca_cantidad_ok"]
    bloqueado = st.session_state["aca_bloqueado"]

    st.caption(f"Las asignaturas quedarán asociadas al carnet {carnet}.")
    st.caption(f"Para mantener la beca: promedio de {PROMEDIO} o más y {REPROBADO} reprobadas.")

    # CAMBIO: el semestre se bloquea al calcular el promedio (antes se podía cambiar después de calcular)
    #         y se limita a 7 caracteres ("2026-II")
    semestre = st.text_input("Semestre (ej: 2026-I)", key=f"aca_semestre_{v}",
                             max_chars=7, disabled=bloqueado)

    # CAMBIO: el campo empieza VACÍO (value=None) y ya no usa min_value/max_value.
    #         Con límites en el widget, Streamlit rechaza en silencio un 0 o un 7 escrito a mano y sigue
    #         devolviendo el último valor válido, así que el botón quedaba habilitado aunque se viera un valor
    #         incorrecto. Sin límites, el valor llega tal cual a Python y lo validamos nosotros.
    cantidad = st.number_input(f"Cantidad de asignaturas (de 1 a {MAX_ASIGNATURAS})", step=1,
                               value=None, format="%d", placeholder=f"Entre 1 y {MAX_ASIGNATURAS}",
                               key=f"aca_cantidad_{v}", disabled=cantidad_ok)

    # NUEVO: Errores previos (semestre y cantidad). Se calculan ANTES de los botones
    #        para poder deshabilitar "Confirmar cantidad" si algo está mal.
    errores_previos = []

    if not semestre.strip():
        errores_previos.append("Semestre")
    else:
        mensaje_semestre = validar_semestre(datos, carnet, semestre)
        if mensaje_semestre:
            errores_previos.append(f"Semestre ({mensaje_semestre})")

    # NUEVO: la cantidad puede llegar vacía (None) o fuera de rango; se exige un entero entre 1 y el máximo
    #        Mensajes distintos para vacío, menos de 1 y más del máximo.
    if cantidad is None:
        cantidad_valida = False
        errores_previos.append(f"Cantidad de asignaturas (ingresa un número entre 1 y {MAX_ASIGNATURAS})")
    elif cantidad != int(cantidad) or not 1 <= cantidad <= MAX_ASIGNATURAS:
        cantidad_valida = False
        errores_previos.append(f"Cantidad de asignaturas (debe ser un número entero entre 1 y {MAX_ASIGNATURAS})")
    else:
        cantidad_valida = True

    # CAMBIO: el botón de confirmar queda deshabilitado si el semestre o la cantidad no son válidos
    if not cantidad_ok:
        if st.button("Confirmar cantidad de asignaturas", disabled=bool(errores_previos)):
            st.session_state["aca_cantidad_ok"] = True
            st.rerun()
    else:
        if st.button("Empezar de nuevo"):
            reiniciar_formulario()
            st.rerun()

    asignaturas = []
    errores = list(errores_previos)

    if not cantidad_ok:
        errores.append("Confirmar cantidad de asignaturas")

    if cantidad_ok and cantidad_valida:
        vistos = set()   # NUEVO: para detectar nombres de asignaturas repetidos
        for i in range(int(cantidad)):
            col1, col2 = st.columns([3, 1])
            nombre = col1.text_input(f"Asignatura {i + 1}", key=f"aca_nombre_{v}_{i}",
                                     max_chars=LARGO_MAX_ASIGNATURA, disabled=bloqueado)
            nota = col2.number_input("Nota", min_value=0.0, max_value=100.0,
                                     step=0.5, value=None, key=f"aca_nota_{v}_{i}",
                                     disabled=bloqueado)

            nombre_limpio = limpiar_nombre(nombre)
            asignatura_ok = True

            # CAMBIO: validación completa del nombre (antes solo se revisaba que no estuviera vacío)
            if not nombre_limpio:
                errores.append(f"Asignatura {i + 1}")
                asignatura_ok = False
            else:
                error_nombre = validar_nombre_asignatura(nombre_limpio)
                if error_nombre:
                    errores.append(f"Asignatura {i + 1} ({error_nombre})")
                    asignatura_ok = False
                elif nombre_limpio.lower() in vistos:
                    errores.append(f"Asignatura {i + 1} (repetida: '{nombre_limpio}')")
                    asignatura_ok = False
                else:
                    vistos.add(nombre_limpio.lower())

            if nota is None:
                errores.append(f"Nota de asignatura {i + 1}")
                asignatura_ok = False

            if asignatura_ok:
                asignaturas.append({"Nombre": nombre_limpio, "Notas": nota})

    if errores:
        st.warning("Complete o corrija estos campos: " + ", ".join(errores) + ".")

    if cantidad_ok and not bloqueado:
        if st.button("Calcular promedio", disabled=bool(errores)):
            st.session_state["aca_bloqueado"] = True
            st.rerun()

    # CAMBIO: "Corregir notas" se muestra siempre que esté bloqueado (antes solo si no había errores)
    if cantidad_ok and bloqueado:
        if st.button("Corregir notas"):
            st.session_state["aca_bloqueado"] = False
            st.rerun()

    # CAMBIO: además de no tener errores, se exige que haya asignaturas completas y que coincidan con la cantidad
    if cantidad_ok and bloqueado and not errores and asignaturas and len(asignaturas) == int(cantidad):
        resultados = calcular_resultados(asignaturas)
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Promedio del semestre", resultados["Promedio"])
        col_b.metric("Asignaturas reprobadas", resultados["Reprobados"])
        col_c.metric("Cumple requisitos de beca", "Sí" if resultados["Aprobado"] else "No")

        if st.button("Registrar semestre", type="primary", disabled=bool(errores)):
            mensaje = registro_semestre(datos, carnet, semestre, asignaturas)
            if mensaje == "Se ha registrado su semestre":
                guardar_o_detener(datos)
                st.session_state["aca_mensaje"] = mensaje
                reiniciar_formulario()
                st.rerun()
            else:
                st.error(mensaje)

    st.subheader("Historial académico")
    historial = datos["academico"].get(carnet, [])
    if historial:
        st.dataframe(tabla_historial(historial), width="stretch", hide_index=True)
    else:
        st.info("Este estudiante aún no tiene semestres registrados.")

    with st.expander("Opciones de administrador"):
        clave = st.text_input("Clave de administrador", type="password", key="aca_clave")

        if clave != CLAVE_ADMIN:
            if clave:
                st.error("Clave incorrecta.")
        elif not historial:
            st.info("Este estudiante no tiene semestres para eliminar.")
        else:
            st.caption(f"Eliminar semestres del carnet {carnet}. Esta acción no se puede deshacer.")

            vd = st.session_state.setdefault("aca_del_v", 0)

            opciones_eliminar = {}
            for i, registro in enumerate(historial):
                texto = (f"{i + 1}. {registro['Semestre']} | Promedio {registro['Promedio']} "
                         f"| Reprobados {registro['Reprobados']}")
                opciones_eliminar[texto] = i

            elegidos = st.multiselect("Semestres a eliminar", list(opciones_eliminar.keys()),
                                       key=f"aca_del_sel_{carnet}_{vd}")
            confirmar = st.checkbox("Confirmo que quiero eliminar los semestres seleccionados",
                                    key=f"aca_del_conf_{carnet}_{vd}")

            if st.button("Eliminar semestres seleccionados", disabled=not (elegidos and confirmar)):
                posiciones = sorted((opciones_eliminar[e] for e in elegidos), reverse=True)
                for posicion in posiciones:
                    historial.pop(posicion)

                if not historial:
                    datos["academico"].pop(carnet, None)

                guardar_o_detener(datos)
                st.session_state["aca_mensaje"] = f"Se eliminaron {len(posiciones)} semestre(s)."
                st.session_state["aca_del_v"] = vd + 1
                st.rerun()