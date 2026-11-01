# =============================================================================
# academico.py -> Módulo académico (Darlenne)
#
# Marcas de los comentarios:
#   # NUEVO:  -> algo que se agregó en esta versión
#   # CAMBIO: -> algo que ya existía y se modificó
# =============================================================================

import re   # NUEVO: Importación del módulo de expresiones regulares para validar el formato del semestre (AAAA-I o AAAA-II)

import streamlit as st
import pandas as pd
from archivos import guardar_datos   # Importación de la función para persistir los cambios del semestre en becas.json

# Definición de constantes globales para la evaluación de becas
PROMEDIO = 85.0
REPROBADO = 0

# NUEVO: Nota mínima requerida para aprobar una asignatura. Antes estaba fijo en 60
#        dentro de calcular_resultados; ahora se centraliza aquí y también lo usa el PDF.
NOTA_APROBATORIA = 60

# NUEVO: Clave de acceso administrativa requerida para habilitar la opción de eliminar semestres
CLAVE_ADMIN = "admin123"


# NUEVO: Valida el semestre ingresado. Devuelve una cadena vacía "" si es correcto, o un mensaje de error si falla.
#   - Solo se aceptan dos semestres por año: AAAA-I y AAAA-II (ej: 2026-I, 2026-II)
#   - Un estudiante no puede tener el mismo semestre registrado dos veces
def validar_semestre(datos: dict, carnet: str, semestre: str):
    semestre = semestre.strip().upper()   # Limpia espacios y convierte a mayúsculas ("2026-i" se normaliza como "2026-I")

    # re.fullmatch comprueba que la cadena cumpla exactamente: cuatro dígitos, un guion, y una 'I' o 'II'
    if not re.fullmatch(r"\d{4}-(I|II)", semestre):
        return "El semestre debe tener el formato AAAA-I o AAAA-II (ejemplo: 2026-I)"

    # Validación de duplicidad: Revisa que el semestre no esté previamente registrado en el historial del estudiante
    for registro in datos["academico"].get(carnet, []):
        if str(registro.get("Semestre", "")).strip().upper() == semestre:
            return f"El semestre {semestre} ya está registrado para este estudiante"

    return ""


# Función auxiliar para descomponer y ordenar el historial académico por fecha cronológica.
def clave_semestre(registro: dict):
    try:
        # Separa el año y el periodo (ej: "2026-I" -> anio="2026", periodo="I")
        anio, periodo = registro["Semestre"].strip().upper().split("-")
        # Retorna una tupla de ordenamiento: (Año numérico, 2 si es periodo II, o 1 si es periodo I)
        return (int(anio), 2 if periodo == "II" else 1)
    except (KeyError, AttributeError, ValueError):
        # Retorna valores por defecto si ocurre algún error de lectura en las claves
        return (0, 0)


# NUEVO: Arma la tabla del historial visualizada en el módulo Académico y en Consulta de becas.
#        Calcula la columna "Cumple requisitos" aplicando la misma regla de beca (promedio y reprobados).
#        Lo almacenado en becas.json permanece intacto; esto modifica únicamente la visualización.
def tabla_historial(historial: list):
    tabla = pd.DataFrame(historial)
    # Comprueba fila por fila si cumple con el promedio mínimo y el máximo de reprobadas permitidas
    cumple = (tabla["Promedio"] >= PROMEDIO) & (tabla["Reprobados"] <= REPROBADO)
    tabla["Cumple requisitos"] = cumple.map({True: "Sí", False: "No"})
    return tabla[["Semestre", "Promedio", "Reprobados", "Cumple requisitos"]]


# Función central: recibe los datos académicos, valida su integridad y registra formalmente el semestre del estudiante
def registro_semestre(datos: dict, carnet: str, semestre: str, asignaturas):
    # Condición de guarda: verifica si el carnet existe dentro de la base de datos de estudiantes
    if carnet not in datos["estudiantes"]:
        return "Su número de carnet no corresponde a ningún estudiante"
    
    # Valida que el campo del semestre no esté vacío
    if not semestre.strip():
        return "Debe específicar su semestre"
        
    # Valida el formato estructurado (AAAA-I / AAAA-II) y evita que esté duplicado
    error_semestre = validar_semestre(datos, carnet, semestre)
    if error_semestre:
        return error_semestre
        
    semestre = semestre.strip().upper()   # Normaliza el formato del semestre antes de almacenarlo
    
    if not asignaturas:
        return "Debe ingresar asignaturas"
        
    # Ejecuta el procesamiento y cálculo de notas de las asignaturas ingresadas
    resultados = calcular_resultados(asignaturas)
    
    # Obtiene o inicializa la lista del historial académico correspondiente al carnet
    Historial = datos["academico"].setdefault(carnet, [])
    
    # Construye el diccionario con la estructura completa del nuevo registro académico
    nuevo_registro = {
        "Semestre": semestre,
        "Promedio": resultados["Promedio"],
        "Aprobado": resultados["Aprobado"],
        "Reprobados": resultados["Reprobados"],
        # NUEVO: Almacena la lista detallada de asignaturas con sus respectivas notas. 
        #        Anteriormente se usaban solo para calcular el promedio y se descartaban; ahora el PDF las incluye.
        "Asignaturas": [{"Nombre": a["Nombre"], "Notas": a["Notas"]} for a in asignaturas],
    }
    
    # Inserta el nuevo registro en la lista del historial
    Historial.append(nuevo_registro)
    
    # NUEVO: Ordena automáticamente el historial cronológicamente, garantizando que el "último semestre" 
    #        (utilizado para evaluar la beca) corresponda siempre al más reciente, incluso si se registra de forma retroactiva.
    Historial.sort(key=clave_semestre)
    return "Se ha registrado su semestre"


# Función de consola interactiva (solicita cantidad y notas mediante input()/print()).
# Nota: Esta función NO se utiliza en la interfaz Streamlit (se mantiene por compatibilidad/legacy).
def solicitar_asignatura():
    asignaturas = []
    while True:
        try:
            cantidad = int(input("Ingrese cuantas asignaturas cursa actualmente:"))
            if cantidad > 0:
                break
            print("Debe ingresar al menos una asignatura")
        except ValueError:
            print("Debe de ingresar un número entero")

    for i in range(cantidad):
        nombre = input(f"Ingrese el nombre de su asignatura:{i + 1}")
        while True:
            try:
                notas = float(input(f"Ingresa su nota de:{nombre}"))
                if 0 <= notas <= 100:
                    break
                print("La nota debe de estar entre 0 y 100")
            except ValueError:
                print("Error, verifique su respuesta, (Recuerde que debe ingresar un valor numerico)")
         
        asignatura = {
            "Nombre": nombre,
            "Notas": notas
        }
        asignaturas.append(asignatura)

    return asignaturas


# Función matemática encargada de calcular el promedio aritmético, materias aprobadas y reprobadas
def calcular_resultados(asignaturas):
    # Suma total de las calificaciones obtenidas en todas las asignaturas
    suma_notas = sum(a["Notas"] for a in asignaturas)

    # Cálculo del promedio aritmético dividiendo la sumatoria entre el total de materias
    prom = suma_notas / len(asignaturas)

    # CAMBIO: Antes evaluaba explícitamente >=60; ahora utiliza la constante centralizada NOTA_APROBATORIA (valor equivalente: 60)
    aprobadas = sum(1 for a in asignaturas if a["Notas"] >= NOTA_APROBATORIA)

    # El número de reprobadas resulta de restar las aprobadas al total de materias cursadas
    reprobados = len(asignaturas) - aprobadas

    # Retorna un diccionario estructurado con los resultados analíticos calculados
    return {
        "Promedio": round(prom, 2),
        "Aprobado": prom >= PROMEDIO and reprobados == REPROBADO,  # Valida si cumple globalmente los requisitos de beca
        "Reprobados": reprobados,
    }


# Función para reiniciar el formulario de registro académico modificando la versión (aca_v) integrada en las keys de Streamlit.
# Al cambiar la key, Streamlit interpreta los componentes como elementos totalmente nuevos y limpios.
def reiniciar_formulario():
    st.session_state["aca_v"] = st.session_state.get("aca_v", 0) + 1
    st.session_state["aca_cantidad_ok"] = False   # Restablece la confirmación de la cantidad de asignaturas
    st.session_state["aca_bloqueado"] = False     # Permite nuevamente la edición de las notas


# Función principal del módulo académico llamada por la aplicación principal (app.py).
# Reemplaza los flujos de consola por componentes interactivos nativos de Streamlit.
def modulo_academico(datos: dict):
    st.title("Académico")

    # Condición de guarda: exige que existan estudiantes registrados antes de permitir acceso al módulo
    if not datos["estudiantes"]:
        st.warning("Primero debes registrar estudiantes.")
        return

    # Inicialización de las variables de estado en la sesión de Streamlit para controlar el flujo del formulario
    st.session_state.setdefault("aca_v", 0)
    st.session_state.setdefault("aca_cantidad_ok", False)
    st.session_state.setdefault("aca_bloqueado", False)

    # Renderiza un mensaje de éxito persistente si este fue almacenado antes de un rerun
    if "aca_mensaje" in st.session_state:
        st.success(st.session_state.pop("aca_mensaje"))

    # CAMBIO: Muestra el selector combinando "carnet - nombre" (idéntico al formato de Consulta de becas).
    #         format_func personaliza la visualización del menú desplegable sin alterar el valor devuelto (el carnet).
    carnet = st.selectbox(
        "Estudiante",
        list(datos["estudiantes"].keys()),
        format_func=lambda c: f"{c} - {datos['estudiantes'][c]['Nombre']}",
        key="aca_carnet",
    )

    # Si se cambia de estudiante activo, se limpia el formulario para evitar mezclar notas entre perfiles distintos
    if "aca_carnet_activo" in st.session_state and st.session_state["aca_carnet_activo"] != carnet:
        reiniciar_formulario()
    st.session_state["aca_carnet_activo"] = carnet

    v = st.session_state["aca_v"]
    cantidad_ok = st.session_state["aca_cantidad_ok"]
    bloqueado = st.session_state["aca_bloqueado"]

    st.caption(f"Las asignaturas quedarán asociadas al carnet {carnet}.")
    st.caption(f"Para mantener la beca: promedio de {PROMEDIO} o más y {REPROBADO} reprobadas.")

    # Campo de texto para ingresar el semestre a cursar
    semestre = st.text_input("Semestre (ej: 2026-I)", key=f"aca_semestre_{v}")

    # Control numérico para definir la cantidad de asignaturas. Se bloquea (disabled) una vez confirmada la cantidad.
    cantidad = st.number_input("Cantidad de asignaturas", min_value=1, step=1, value=1,
                               key=f"aca_cantidad_{v}", disabled=cantidad_ok)

    # Botones de control para confirmar la cantidad o reiniciar el proceso de captura
    if not cantidad_ok:
        if st.button("Confirmar cantidad de asignaturas"):
            st.session_state["aca_cantidad_ok"] = True
            st.rerun()
    else:
        if st.button("Empezar de nuevo"):
            reiniciar_formulario()
            st.rerun()

    asignaturas = []
    errores = []

    # Validación preliminar de campos vacíos o errores en el semestre
    if not semestre.strip():
        errores.append("Semestre")
    else:
        # NUEVO: Validación interactiva del semestre (formato y verificación de duplicidad)
        mensaje_semestre = validar_semestre(datos, carnet, semestre)
        if mensaje_semestre:
            errores.append(f"Semestre ({mensaje_semestre})")
            
    if not cantidad_ok:
        errores.append("Confirmar cantidad de asignaturas")

    # Renderiza dinámicamente las casillas de texto y notas únicamente después de confirmar la cantidad de asignaturas
    if cantidad_ok:
        for i in range(int(cantidad)):
            col1, col2 = st.columns([3, 1])
            # Se bloquean los campos si ya se calculó el promedio (para impedir ediciones directas sin desbloquear)
            nombre = col1.text_input(f"Asignatura {i + 1}", key=f"aca_nombre_{v}_{i}",
                                     disabled=bloqueado)
            # value=None inicializa la casilla vacía para verificar obligatoriedad de ingreso
            nota = col2.number_input("Nota", min_value=0.0, max_value=100.0,
                                     step=0.5, value=None, key=f"aca_nota_{v}_{i}",
                                     disabled=bloqueado)

            # Valida individualmente que cada componente posea datos válidos
            if not nombre.strip():
                errores.append(f"Asignatura {i + 1}")
            if nota is None:
                errores.append(f"Nota de asignatura {i + 1}")

            # Almacena de manera estructurada la asignatura completada exitosamente
            if nombre.strip() and nota is not None:
                asignaturas.append({"Nombre": nombre, "Notas": nota})

    # Despliega advertencias visuales si existen campos pendientes o erróneos en el formulario
    if errores:
        st.warning("Complete o corrija estos campos: " + ", ".join(errores) + ".")

    # Botón para procesar los cálculos de notas. Una vez accionado, bloquea la edición de notas.
    if cantidad_ok and not bloqueado:
        if st.button("Calcular promedio", disabled=bool(errores)):
            st.session_state["aca_bloqueado"] = True
            st.rerun()

    # Bloque de visualización tras calcular exitosamente el promedio del semestre
    if cantidad_ok and bloqueado and not errores:
        resultados = calcular_resultados(asignaturas)
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Promedio del semestre", resultados["Promedio"])
        col_b.metric("Asignaturas reprobadas", resultados["Reprobados"])
        col_c.metric("Cumple requisitos de beca", "Sí" if resultados["Aprobado"] else "No")

        # Botón para corregir notas: desbloquea las casillas y permite reestructurar el ingreso de calificaciones
        if st.button("Corregir notas"):
            st.session_state["aca_bloqueado"] = False
            st.rerun()

        # Botón principal para formalizar el registro del semestre y guardarlo en el archivo JSON
        if st.button("Registrar semestre", type="primary", disabled=bool(errores)):
            mensaje = registro_semestre(datos, carnet, semestre, asignaturas)
            if mensaje == "Se ha registrado su semestre":
                guardar_datos(datos)   # Persiste los cambios en el almacenamiento local (JSON)
                st.session_state["aca_mensaje"] = mensaje
                reiniciar_formulario() # Limpia los campos para facilitar un registro posterior
                st.rerun()
            else:
                st.error(mensaje)

    # Sección de visualización del historial académico en formato tabular interactivo
    st.subheader("Historial académico")
    historial = datos["academico"].get(carnet, [])
    if historial:
        # Renderiza la tabla utilizando la función auxiliar tabla_historial()
        st.dataframe(tabla_historial(historial), width="stretch", hide_index=True)
    else:
        st.info("Este estudiante aún no tiene semestres registrados.")

    # Panel colapsable de administración protegido mediante contraseña para eliminar registros de semestres
    with st.expander("Opciones de administrador"):
        clave = st.text_input("Clave de administrador", type="password", key="aca_clave")

        if clave != CLAVE_ADMIN:
            if clave:
                st.error("Clave incorrecta.")
        elif not historial:
            st.info("Este estudiante no tiene semestres para eliminar.")
        else:
            st.caption(f"Eliminar semestres del carnet {carnet}. Esta acción no se puede deshacer.")

            # Control de versión para limpiar la selección de elementos múltiples tras la eliminación
            vd = st.session_state.setdefault("aca_del_v", 0)

            # Mapea los registros existentes asociándolos con un identificador textual descriptivo
            opciones_eliminar = {}
            for i, registro in enumerate(historial):
                texto = (f"{i + 1}. {registro['Semestre']} | Promedio {registro['Promedio']} "
                         f"| Reprobados {registro['Reprobados']}")
                opciones_eliminar[texto] = i

            elegidos = st.multiselect("Semestres a eliminar", list(opciones_eliminar.keys()),
                                       key=f"aca_del_sel_{carnet}_{vd}")
            confirmar = st.checkbox("Confirmo que quiero eliminar los semestres seleccionados",
                                    key=f"aca_del_conf_{carnet}_{vd}")

            # Acción de borrado: requiere la selección de los elementos y la confirmación mediante casilla de verificación
            if st.button("Eliminar semestres seleccionados", disabled=not (elegidos and confirmar)):
                # Ordena los índices seleccionados de mayor a menor para evitar corrimientos indeseados al realizar pop()
                posiciones = sorted((opciones_eliminar[e] for e in elegidos), reverse=True)
                for posicion in posiciones:
                    historial.pop(posicion)
                    
                # Si el estudiante se queda sin semestres registrados, se elimina por completo su clave del diccionario académico
                if not historial:
                    datos["academico"].pop(carnet, None)
                    
                guardar_datos(datos)   # Actualiza los cambios persistentes en disco
                st.session_state["aca_mensaje"] = f"Se eliminaron {len(posiciones)} semestre(s)."
                st.session_state["aca_del_v"] = vd + 1
                st.rerun()