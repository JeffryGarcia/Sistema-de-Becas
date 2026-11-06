# =============================================================================
# reporte_pdf.py -> Genera el REPORTE EN PDF de un estudiante
#
# Se usa así (desde consulta_becas.py):
#     pdf_bytes = generar_pdf(estudiante, historial, estado, motivo)
#
# Este módulo NO decide si hay beca: recibe el estado y el motivo ya calculados por
# estado_beca() de consulta_becas.py, así el PDF siempre dice lo mismo que la pantalla.
#
# Necesita instalar la librería reportlab:   pip install reportlab
#
# Marcas de los comentarios:
#   # NUEVO:  -> algo que se agregó en esta versión
#   # CAMBIO: -> algo que ya existía y se modificó
# =============================================================================

from datetime import date
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape   # protege los textos por si traen símbolos como < o &

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (Flowable, KeepTogether, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

from academico import NOTA_APROBATORIA, PROMEDIO, REPROBADO

# ---------- Colores: los MISMOS valores que las variables de style.css ----------
# CAMBIO: antes usaba un azul distinto (#003485); ahora cada color corresponde a una variable del CSS.
BANNER_A = colors.HexColor("#254d73")     # --banner-a   (inicio del degradado del banner)
BANNER_B = colors.HexColor("#0f2842")     # --banner-b   (final del degradado del banner)
ACENTO = colors.HexColor("#003366")       # --acento / --uni-azul: encabezados de tabla, bordes de énfasis
LINEA_BANNER = colors.HexColor("#2b7fd4") # azul claro del membrete (línea inferior del banner)
TEXTO_TITULO = colors.HexColor("#0d233a") # --texto-titulo
TEXTO_COLOR = colors.HexColor("#16293d")  # --texto
GRIS_TEXTO = colors.HexColor("#52687d")   # --texto-suave
GRIS_CLARO = colors.HexColor("#ecf2f7")   # --superficie: fondo de ficha, tarjetas y filas alternas
GRIS_LINEA = colors.HexColor("#cbd8e3")   # --borde
VERDE = colors.HexColor("#06472b")        # --verde  (Con beca)
ROJO = colors.HexColor("#d64545")         # --rojo   (Sin beca)
INFO = colors.HexColor("#3d688f")         # --info   (Sin registro)

# Logo del banner de Inicio (el mismo que usa app.py)
LOGO = Path(__file__).parent / "assets" / "logo_becas.png"


# NUEVO: Mezcla un color con blanco para obtener su versión suave (equivale al color-mix(... 12%, transparent) del CSS)
def _suave(color, f=0.12):
    return colors.Color(color.red * f + (1 - f), color.green * f + (1 - f), color.blue * f + (1 - f))


# Color de cada estado de beca (mismos tres estados y mismos colores que la pantalla)
COLOR_ESTADO = {"Con beca": VERDE, "Sin beca": ROJO, "Sin registro": INFO}

# ---------- Estilos de texto ----------
TEXTO = ParagraphStyle("texto", fontName="Helvetica", fontSize=10, leading=13, textColor=TEXTO_COLOR)
ETIQUETA = ParagraphStyle("etiqueta", parent=TEXTO, fontSize=7.5, leading=10, textColor=GRIS_TEXTO)
TITULO = ParagraphStyle("titulo", parent=TEXTO, fontName="Helvetica-Bold", fontSize=15,
                        leading=19, textColor=colors.white)
SUBTITULO = ParagraphStyle("subtitulo", parent=TEXTO, fontSize=10, textColor=colors.HexColor("#dbe4ec"))
SECCION = ParagraphStyle("seccion", parent=TEXTO, fontName="Helvetica-Bold", fontSize=12.5,
                         leading=16, textColor=TEXTO_TITULO, spaceBefore=14, spaceAfter=6)
NOTA_PIE = ParagraphStyle("nota_pie", parent=TEXTO, fontSize=8.5, textColor=GRIS_TEXTO)

ANCHO = A4[0] - 4 * cm   # ancho útil de la hoja (con 2 cm de margen a cada lado)


def _t(valor):
    return escape(str(valor))


def _num(valor, defecto=0.0):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return defecto


def _cumple(registro):
    return _num(registro.get("Promedio")) >= PROMEDIO and _num(registro.get("Reprobados")) <= REPROBADO


# NUEVO: Encabezado dibujado a mano para reproducir el banner de la interfaz:
#        degradado azul con esquinas redondeadas, logo SG UNI a la izquierda, línea divisoria
#        y los textos a la derecha (antes era una tabla de color sólido).
class Encabezado(Flowable):
    def __init__(self, ancho, alto=3.1 * cm):
        super().__init__()
        self.width = ancho
        self.height = alto

    def wrap(self, ancho_disp, alto_disp):
        return self.width, self.height

    def draw(self):
        c = self.canv
        w, h = self.width, self.height
        c.saveState()

        # Fondo: degradado en diagonal entre los dos azules del banner, recortado con esquinas redondeadas
        recorte = c.beginPath()
        recorte.roundRect(0, 0, w, h, 12)
        c.clipPath(recorte, stroke=0, fill=0)
        c.linearGradient(0, h, w, 0, (BANNER_A, BANNER_B), extend=False)

        # Línea de acento en la parte inferior (como el membrete de la interfaz)
        c.setFillColor(LINEA_BANNER)
        c.rect(0, 0, w, 3, stroke=0, fill=1)

        x_texto = 0.8 * cm
        if LOGO.exists():
            lector = ImageReader(str(LOGO))
            iw, ih = lector.getSize()
            lh = h - 1.2 * cm                      # alto máximo del logo
            lw = lh * iw / ih                      # se conserva la proporción real de la imagen
            if lw > 4.6 * cm:                      # si es muy ancho, se limita por el ancho
                lw = 4.6 * cm
                lh = lw * ih / iw
            x_logo = 0.7 * cm
            c.drawImage(lector, x_logo, (h - lh) / 2, lw, lh, mask="auto")

            # Línea divisoria vertical entre el logo y los textos (como el border-right del banner)
            x_div = x_logo + lw + 0.45 * cm
            c.setStrokeColor(colors.Color(1, 1, 1, alpha=0.35))
            c.setLineWidth(0.8)
            c.line(x_div, h * 0.22, x_div, h * 0.78)
            x_texto = x_div + 0.55 * cm

        # Textos, centrados verticalmente y con salto de línea automático
        disp = w - x_texto - 0.6 * cm
        titulo = Paragraph("Sistema de Gestión y Seguimiento de Becas", TITULO)
        subtitulo = Paragraph("Reporte académico del estudiante", SUBTITULO)
        _, h1 = titulo.wrap(disp, h)
        _, h2 = subtitulo.wrap(disp, h)
        arriba = (h + h1 + h2 + 4) / 2
        titulo.drawOn(c, x_texto, arriba - h1)
        subtitulo.drawOn(c, x_texto, arriba - h1 - 4 - h2)

        c.restoreState()


# Estilo común de las tablas de datos: encabezado azul UNI, filas alternas y líneas finas
def _estilo_tabla():
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACENTO),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
        ("GRID", (0, 0), (-1, -1), 0.5, GRIS_LINEA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ])


def _pie_pagina(lienzo, doc):
    lienzo.saveState()
    lienzo.setFont("Helvetica", 8)
    lienzo.setFillColor(GRIS_TEXTO)
    lienzo.drawString(2 * cm, 1.2 * cm, f"SG UNI  ·  Generado el {date.today():%d/%m/%Y}")
    lienzo.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Página {doc.page}")
    lienzo.restoreState()


# NUEVO: Ficha del estudiante, reproduce plantillas/ficha.html:
#        nombre + carrera a la izquierda, etiqueta (pill) con el estado a la derecha,
#        carnet / edad / correo en tres columnas y el motivo en un recuadro con borde de color.
def _ficha(estudiante, estado, motivo):
    color = COLOR_ESTADO.get(estado, INFO)
    suave = _suave(color)
    interior = ANCHO - 34   # ancho disponible dentro de la ficha (descontando bordes y márgenes)

    estilo_nombre = ParagraphStyle("nombre", parent=TEXTO, fontName="Helvetica-Bold",
                                   fontSize=17, leading=21, textColor=TEXTO_TITULO)
    estilo_pill = ParagraphStyle("pill", parent=TEXTO, fontName="Helvetica-Bold", fontSize=9,
                                 leading=11, textColor=color, alignment=1)

    # Etiqueta redondeada del estado (pill)
    pill = Table([[Paragraph(_t(estado), estilo_pill)]], colWidths=[3.3 * cm])
    pill.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), suave),
        ("BOX", (0, 0), (-1, -1), 0.9, color),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    superior = Table(
        [[[Paragraph(_t(estudiante.get("Nombre", "—")), estilo_nombre),
           Paragraph(_t(estudiante.get("carrera", "—")), ParagraphStyle("carrera", parent=TEXTO,
                                                                       textColor=GRIS_TEXTO))],
          pill]],
        colWidths=[interior - 3.3 * cm, 3.3 * cm],
    )
    superior.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    def dato(etiqueta, valor):
        return [Paragraph(etiqueta.upper(), ETIQUETA), Paragraph(f"<b>{_t(valor)}</b>", TEXTO)]

    edad = estudiante.get("Edad")
    datos = Table(
        [[dato("Carnet", estudiante.get("carnet", "—")),
          dato("Edad", f"{edad} años" if edad not in (None, "") else "—"),
          dato("Correo", estudiante.get("correo", "—"))]],
        colWidths=[interior * 0.24, interior * 0.2, interior * 0.56],
    )
    datos.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.5, GRIS_LINEA),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    # Recuadro del motivo: fondo suave y borde izquierdo del color del estado
    cuadro_motivo = Table([[Paragraph(_t(motivo), TEXTO)]], colWidths=[interior])
    cuadro_motivo.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), suave),
        ("LINEBEFORE", (0, 0), (0, -1), 3.5, color),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))

    # Contenedor de la ficha: fondo gris azulado y borde izquierdo de énfasis (como .ficha)
    ficha = Table([[superior], [datos], [cuadro_motivo]], colWidths=[ANCHO])
    ficha.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GRIS_CLARO),
        ("BOX", (0, 0), (-1, -1), 0.5, GRIS_LINEA),
        ("LINEBEFORE", (0, 0), (0, -1), 5, ACENTO),
        ("LEFTPADDING", (0, 0), (-1, -1), 20),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, 0), 14),
        ("TOPPADDING", (0, 1), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -2), 4),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 14),
    ]))
    return ficha


def generar_pdf(estudiante: dict, historial: list, estado: str, motivo: str) -> bytes:
    documento = []

    # ---------- 1. Encabezado (banner con logo) ----------
    documento += [Encabezado(ANCHO), Spacer(1, 14)]

    # ---------- 2. Ficha del estudiante con su estado ----------
    documento.append(_ficha(estudiante, estado, motivo))
    documento += [Spacer(1, 5),
                  Paragraph(f"Requisitos: promedio de {PROMEDIO} o más y máximo {REPROBADO} "
                            f"asignatura(s) reprobada(s). Se evalúa con el último semestre registrado.",
                            NOTA_PIE)]

    # ---------- 3. Resumen e historial (solo si tiene semestres registrados) ----------
    if not historial:
        documento += [Spacer(1, 16),
                      Paragraph("Este estudiante aún no tiene semestres registrados.", TEXTO)]
    else:
        promedios = [_num(r.get("Promedio")) for r in historial]
        promedio_general = sum(promedios) / len(promedios)

        estilo_cifra = ParagraphStyle("cifra", parent=TEXTO, fontName="Helvetica-Bold",
                                      fontSize=20, leading=24, textColor=TEXTO_TITULO)

        def tarjeta(etiqueta, valor):
            return [Paragraph(etiqueta.upper(), ETIQUETA), Paragraph(_t(valor), estilo_cifra)]

        # CAMBIO: tres tarjetas separadas, con borde izquierdo de énfasis, igual que las métricas de la interfaz
        hueco = 0.4 * cm
        ancho_t = (ANCHO - 2 * hueco) / 3
        resumen = Table(
            [[tarjeta("Semestres cursados", len(historial)), "",
              tarjeta("Promedio general", f"{promedio_general:.2f}"), "",
              tarjeta("Último promedio", f"{promedios[-1]:.2f}")]],
            colWidths=[ancho_t, hueco, ancho_t, hueco, ancho_t],
        )
        estilo_resumen = [("LEFTPADDING", (0, 0), (-1, -1), 12),
                          ("TOPPADDING", (0, 0), (-1, -1), 8),
                          ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]
        for col in (0, 2, 4):
            estilo_resumen += [("BACKGROUND", (col, 0), (col, 0), GRIS_CLARO),
                               ("BOX", (col, 0), (col, 0), 0.5, GRIS_LINEA),
                               ("LINEBEFORE", (col, 0), (col, 0), 5, ACENTO)]
        for col in (1, 3):
            estilo_resumen += [("LEFTPADDING", (col, 0), (col, 0), 0)]
        resumen.setStyle(TableStyle(estilo_resumen))
        documento += [Spacer(1, 14), resumen]

        documento.append(Paragraph("Historial por semestre", SECCION))
        filas = [["Semestre", "Promedio", "Reprobadas", "Cumple requisitos"]]
        for registro in historial:
            cumple = _cumple(registro)
            color = VERDE.hexval()[2:] if cumple else ROJO.hexval()[2:]
            filas.append([
                _t(registro.get("Semestre", "—")),
                f"{_num(registro.get('Promedio')):.2f}",
                str(registro.get("Reprobados", "—")),
                Paragraph(f'<font color="#{color}"><b>{"Sí" if cumple else "No"}</b></font>', TEXTO),
            ])
        tabla_general = Table(filas, colWidths=[ANCHO * 0.25] * 4, repeatRows=1)
        tabla_general.setStyle(_estilo_tabla())
        documento.append(tabla_general)

        documento.append(Paragraph("Calificaciones por asignatura", SECCION))
        for registro in historial:
            bloque = [Paragraph(
                f"<b>Semestre {_t(registro.get('Semestre', '—'))}</b>  ·  "
                f"promedio {_num(registro.get('Promedio')):.2f}", TEXTO), Spacer(1, 4)]

            asignaturas = registro.get("Asignaturas")
            if asignaturas:
                filas = [["Asignatura", "Nota", "Estado"]]
                for asignatura in asignaturas:
                    nota = _num(asignatura.get("Notas"))
                    aprobada = nota >= NOTA_APROBATORIA
                    color = VERDE.hexval()[2:] if aprobada else ROJO.hexval()[2:]
                    filas.append([
                        Paragraph(_t(asignatura.get("Nombre", "—")), TEXTO),
                        f"{nota:g}",
                        Paragraph(f'<font color="#{color}">{"Aprobada" if aprobada else "Reprobada"}</font>',
                                  TEXTO),
                    ])
                tabla = Table(filas, colWidths=[ANCHO * 0.6, ANCHO * 0.15, ANCHO * 0.25], repeatRows=1)
                tabla.setStyle(_estilo_tabla())
                bloque.append(tabla)
            else:
                bloque.append(Paragraph("Detalle de asignaturas no disponible para este semestre.",
                                        NOTA_PIE))

            documento += [KeepTogether(bloque), Spacer(1, 10)]

        documento.append(Paragraph(
            f"Una asignatura se considera aprobada con nota de {NOTA_APROBATORIA:g} o más.", NOTA_PIE))

    # ---------- 4. Armar el PDF en memoria ----------
    memoria = BytesIO()
    SimpleDocTemplate(
        memoria, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm, bottomMargin=2 * cm,
        title=f"Reporte académico - {estudiante.get('Nombre', '')}", author="Sistema de Becas SG UNI",
    ).build(documento, onFirstPage=_pie_pagina, onLaterPages=_pie_pagina)
    return memoria.getvalue()