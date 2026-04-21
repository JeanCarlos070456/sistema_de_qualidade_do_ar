from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

import plotly
import plotly.io as pio
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    Image as RLImage,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table as RLTable,
    TableStyle,
)


def _configure_kaleido():
    plotlyjs_path = (
        Path(plotly.__file__).resolve().parent / "package_data" / "plotly.min.js"
    )

    if not plotlyjs_path.exists():
        raise FileNotFoundError(
            f"Arquivo plotly.min.js não encontrado em: {plotlyjs_path}"
        )

    pio.kaleido.scope.plotlyjs = plotlyjs_path.as_uri()


def export_plotly_figures(fig_temp, fig_umid, fig_co2):
    _configure_kaleido()

    temp_dir = TemporaryDirectory()
    base = Path(temp_dir.name)

    temp_path = base / "temp.png"
    umid_path = base / "umid.png"
    co2_path = base / "co2.png"

    fig_temp.write_image(str(temp_path), format="png", engine="kaleido", scale=2)
    fig_umid.write_image(str(umid_path), format="png", engine="kaleido", scale=2)
    fig_co2.write_image(str(co2_path), format="png", engine="kaleido", scale=2)

    return temp_dir, {
        "temp": temp_path,
        "umid": umid_path,
        "co2": co2_path,
    }


def generate_pdf(tabela_ref_df, png_paths, data_sel, pontos_sel, mapa_path=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    W, H = A4
    story = []

    story.append(Paragraph("Relatório Comparativo – Interno × Externo", styles["Title"]))
    story.append(Paragraph(f"Data selecionada: {data_sel}", styles["Normal"]))
    story.append(Paragraph(f"Pontos: {', '.join(pontos_sel)}", styles["Normal"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Referências usadas", styles["Heading2"]))
    tabela = [tabela_ref_df.columns.tolist()] + tabela_ref_df.values.tolist()
    tbl = RLTable(tabela, repeatRows=1, colWidths=[W * 0.28, W * 0.34, W * 0.28])
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    story.append(tbl)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Gráficos comparativos", styles["Heading2"]))
    for titulo, key in [
        ("Temperatura Média vs Referências", "temp"),
        ("Umidade Relativa Média vs Referências", "umid"),
        ("CO₂ Médio vs Referências", "co2"),
    ]:
        path = png_paths.get(key)
        if path and path.exists():
            story.append(Paragraph(titulo, styles["Heading3"]))
            story.append(RLImage(str(path), width=W - 72, height=(W - 72) * 0.55))
            story.append(Spacer(1, 8))

    if mapa_path and Path(mapa_path).exists():
        story.append(PageBreak())
        story.append(Paragraph("Mapa dos pontos de coleta", styles["Heading2"]))
        story.append(Spacer(1, 8))
        story.append(RLImage(str(mapa_path), width=W - 72, height=(W - 72) * 0.65))

    doc.build(story)
    buffer.seek(0)
    return buffer