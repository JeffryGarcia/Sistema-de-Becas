# =============================================================================
# reporte_pdf.py -> Genera el REPORTE EN PDF de un estudiante (módulo NUEVO)
#
# Se usa así (desde consulta_becas.py):
#     pdf_bytes = generar_pdf(estudiante, historial, estado, motivo)
#
# Este módulo NO decide si hay beca: recibe el estado y el motivo ya calculados por
# estado_beca() de consulta_becas.py, así el PDF siempre dice lo mismo que la pantalla.
#
# Necesita instalar la librería reportlab:   pip install reportlab
# =============================================================================

from datetime import date
from io import BytesIO
from pathlib import Path   # NUEVO: para encontrar el logo en la carpeta assets
from xml.sax.saxutils import escape   # protege los textos por si traen símbolos como < o &

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (Image, KeepTogether, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)   # NUEVO: Image, para el logo

# Las mismas reglas de la beca que usa todo el sistema (viven en academico.py)
from academico import NOTA_APROBATORIA, PROMEDIO, REPROBADO

# ---------- Colores ----------
# CAMBIO: el PDF ahora usa el azul UNI y el blanco, igual que la interfaz (antes vino y dorado)
AZUL = colors.HexColor("#003485")        # azul UNI: encabezado, títulos y encabezados de tabla
ACENTO = colors.HexColor("#5b9bff")      # azul claro: línea decorativa bajo el encabezado
# Logo en blanco (el mismo que usa la app), se dibuja sobre el encabezado azul
LOGO = Path(__file__).parent / "assets" / "logo_claro.png"
GRIS_CLARO = colors.HexColor("#f1f5f9")  # fondo de filas alternas y recuadros
GRIS_LINEA = colors.HexColor("#cbd5e1")  # líneas de las tablas
GRIS_TEXTO = colors.HexColor("#64748b")  # textos secundarios
VERDE = colors.HexColor("#15803d")
ROJO = colors.HexColor("#b91c1c")

# Color fuerte y color suave para cada estado de beca (mismos tres estados de la pantalla)
COLORES_ESTADO = {
    "Con beca": (VERDE, colors.HexColor("#dcfce7")),
    "Sin beca": (ROJO, colors.HexColor("#fee2e2")),
    "Sin registro": (GRIS_TEXTO, colors.HexColor("#e2e8f0")),
}

# ---------- Estilos de texto ----------
TEXTO = ParagraphStyle("texto", fontName="Helvetica", fontSize=10, leading=13)
ETIQUETA = ParagraphStyle("etiqueta", parent=TEXTO, fontSize=8, textColor=GRIS_TEXTO)
TITULO = ParagraphStyle("titulo", parent=TEXTO, fontName="Helvetica-Bold", fontSize=14.5,
                        leading=18, textColor=colors.white)
SUBTITULO = ParagraphStyle("subtitulo", parent=TEXTO, fontSize=10, textColor=colors.HexColor("#cbd5e1"))
SECCION = ParagraphStyle("seccion", parent=TEXTO, fontName="Helvetica-Bold", fontSize=12,
                         leading=15, textColor=AZUL, spaceBefore=12, spaceAfter=5)
NOTA_PIE = ParagraphStyle("nota_pie", parent=TEXTO, fontSize=8.5, textColor=GRIS_TEXTO)

ANCHO = A4[0] - 4 * cm   # ancho útil de la hoja (con 2 cm de margen a cada lado)


# Convierte un valor a texto seguro para meterlo en un Paragraph
def _t(valor):
    return escape(str(valor))


# Si cumple los requisitos de la beca en ese semestre (la misma regla que usa el sistema)
def _cumple(registro):
    return registro["Promedio"] >= PROMEDIO and registro["Reprobados"] <= REPROBADO


# Estilo común de las tablas de datos: encabezado azul, filas alternas y líneas finas
def _estilo_tabla():
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
        ("GRID", (0, 0), (-1, -1), 0.5, GRIS_LINEA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ])


# Dibuja el pie de página: fecha de generación y número de página
def _pie_pagina(lienzo, doc):
    lienzo.saveState()
    lienzo.setFont("Helvetica", 8)
    lienzo.setFillColor(GRIS_TEXTO)
    lienzo.drawString(2 * cm, 1.2 * cm, f"Generado el {date.today():%d/%m/%Y}")
    lienzo.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Página {doc.page}")
    lienzo.restoreState()


# Recibe los datos de UN estudiante y devuelve el PDF como bytes (listo para st.download_button).
#   estudiante -> diccionario con Nombre, Edad, carnet, carrera, correo
#   historial  -> lista de semestres del estudiante (puede estar vacía)
#   estado     -> "Con beca", "Sin beca" o "Sin registro" (viene de estado_beca)
#   motivo     -> texto que explica el estado (viene de estado_beca)
def generar_pdf(estudiante: dict, historial: list, estado: str, motivo: str) -> bytes:
    documento = []   # aquí se van agregando las piezas del PDF, de arriba hacia abajo

    # ---------- 1. Encabezado ----------
    # CAMBIO: el encabezado ahora tiene el logo a la izquierda y los textos a la derecha
    #         (antes eran solo los dos textos). Si no se encuentra el logo, se deja vacío
    #         y el PDF se genera igual.
    logo = ""
    if LOGO.exists():
        logo = Image(str(LOGO), width=3.4 * cm, height=3.4 * cm * 180 / 361)   # 361x180 = proporción del logo
    encabezado = Table(
        [[logo, [Paragraph("Sistema de Gestión y Seguimiento de Becas", TITULO),
                 Paragraph("Reporte académico del estudiante", SUBTITULO)]]],
        colWidths=[4.4 * cm, ANCHO - 4.4 * cm],
    )
    encabezado.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), AZUL),
        ("LINEBELOW", (0, 0), (-1, -1), 3, ACENTO),   # NUEVO: línea azul claro abajo
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ]))
    documento += [encabezado, Spacer(1, 14)]

    # ---------- 2. Datos del estudiante ----------
    def dato(etiqueta, valor):
        # Cada dato es una etiqueta pequeña gris y debajo el valor
        return [Paragraph(etiqueta.upper(), ETIQUETA), Paragraph(f"<b>{_t(valor)}</b>", TEXTO)]

    datos = Table(
        [[dato("Nombre", estudiante["Nombre"]), dato("Carnet", estudiante["carnet"])],
         [dato("Carrera", estudiante["carrera"]), dato("Edad", f"{estudiante['Edad']} años")],
         [dato("Correo", estudiante["correo"]), ""]],
        colWidths=[ANCHO * 0.6, ANCHO * 0.4],
    )
    datos.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GRIS_CLARO),
        ("BOX", (0, 0), (-1, -1), 0.5, GRIS_LINEA),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    documento += [datos, Spacer(1, 12)]

    # ---------- 3. Estado de la beca (recuadro de color) ----------
    color_fuerte, color_suave = COLORES_ESTADO[estado]
    estilo_estado = ParagraphStyle("estado", parent=TEXTO, fontName="Helvetica-Bold", fontSize=14,
                                   leading=17, textColor=colors.white, alignment=1)  # 1 = centrado
    caja_beca = Table(
        [[Paragraph(_t(estado), estilo_estado),
          [Paragraph(f"<b>{_t(motivo)}</b>", TEXTO),
           Spacer(1, 3),
           Paragraph(f"Requisitos: promedio de {PROMEDIO} o más y máximo {REPROBADO} "
                     f"asignatura(s) reprobada(s). Se evalúa con el último semestre registrado.",
                     NOTA_PIE)]]],
        colWidths=[4 * cm, ANCHO - 4 * cm],
    )
    caja_beca.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), color_fuerte),
        ("BACKGROUND", (1, 0), (1, 0), color_suave),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (1, 0), (1, 0), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    documento.append(caja_beca)

    # ---------- 4. Resumen e historial (solo si tiene semestres registrados) ----------
    if not historial:
        documento += [Spacer(1, 16),
                      Paragraph("Este estudiante aún no tiene semestres registrados.", TEXTO)]
    else:
        promedios = [r["Promedio"] for r in historial]
        promedio_general = sum(promedios) / len(promedios)

        # Tres tarjetas: semestres cursados, promedio general y último promedio
        estilo_cifra = ParagraphStyle("cifra", parent=TEXTO, fontName="Helvetica-Bold",
                                      fontSize=18, leading=22, textColor=AZUL)

        def tarjeta(etiqueta, valor):
            return [Paragraph(etiqueta.upper(), ETIQUETA), Paragraph(_t(valor), estilo_cifra)]

        resumen = Table(
            [[tarjeta("Semestres cursados", len(historial)),
              tarjeta("Promedio general", f"{promedio_general:.2f}"),
              tarjeta("Último promedio", f"{promedios[-1]:.2f}")]],
            colWidths=[ANCHO / 3] * 3,
        )
        resumen.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, GRIS_LINEA),
            ("LINEAFTER", (0, 0), (1, 0), 0.5, GRIS_LINEA),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        documento += [Spacer(1, 12), resumen]

        # Tabla general: una fila por semestre
        documento.append(Paragraph("Historial por semestre", SECCION))
        filas = [["Semestre", "Promedio", "Reprobadas", "Cumple requisitos"]]
        for registro in historial:
            cumple = _cumple(registro)
            color = "#15803d" if cumple else "#b91c1c"
            filas.append([
                _t(registro["Semestre"]),
                f"{registro['Promedio']:.2f}",
                str(registro["Reprobados"]),
                Paragraph(f'<font color="{color}"><b>{"Sí" if cumple else "No"}</b></font>', TEXTO),
            ])
        tabla_general = Table(filas, colWidths=[ANCHO * 0.25] * 4, repeatRows=1)
        tabla_general.setStyle(_estilo_tabla())
        documento.append(tabla_general)

        # Detalle: las notas de cada asignatura, semestre por semestre
        documento.append(Paragraph("Calificaciones por asignatura", SECCION))
        for registro in historial:
            bloque = [Paragraph(
                f"<b>Semestre {_t(registro['Semestre'])}</b>  ·  promedio {registro['Promedio']:.2f}",
                TEXTO), Spacer(1, 4)]

            asignaturas = registro.get("Asignaturas")
            if asignaturas:
                filas = [["Asignatura", "Nota", "Estado"]]
                for asignatura in asignaturas:
                    nota = asignatura["Notas"]
                    aprobada = nota >= NOTA_APROBATORIA
                    color = "#15803d" if aprobada else "#b91c1c"
                    filas.append([
                        Paragraph(_t(asignatura["Nombre"]), TEXTO),
                        f"{nota:g}",
                        Paragraph(f'<font color="{color}">{"Aprobada" if aprobada else "Reprobada"}</font>',
                                  TEXTO),
                    ])
                tabla = Table(filas, colWidths=[ANCHO * 0.6, ANCHO * 0.15, ANCHO * 0.25], repeatRows=1)
                tabla.setStyle(_estilo_tabla())
                bloque.append(tabla)
            else:
                # Semestres registrados antes de que el sistema guardara las asignaturas
                bloque.append(Paragraph("Detalle de asignaturas no disponible para este semestre.",
                                        NOTA_PIE))

            # KeepTogether evita que un semestre se corte entre dos páginas si cabe completo
            documento += [KeepTogether(bloque), Spacer(1, 10)]

        documento.append(Paragraph(
            f"Una asignatura se considera aprobada con nota de {NOTA_APROBATORIA:g} o más.", NOTA_PIE))

    # ---------- 5. Armar el PDF en memoria (sin crear archivos en el disco) ----------
    memoria = BytesIO()
    SimpleDocTemplate(
        memoria, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm, bottomMargin=2 * cm,
        title=f"Reporte académico - {estudiante['Nombre']}", author="Sistema de Becas",
    ).build(documento, onFirstPage=_pie_pagina, onLaterPages=_pie_pagina)
    return memoria.getvalue()