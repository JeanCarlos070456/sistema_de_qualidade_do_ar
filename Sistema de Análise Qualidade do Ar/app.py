# app.py
import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.features import CustomIcon
import plotly.graph_objects as go
import numpy as np
import os
from io import BytesIO
from datetime import datetime

# ============== CONFIGURAÇÃO INICIAL ==============
st.set_page_config(layout="wide", page_title="Análise da Qualidade do Ar - Santa Luzia")
st.markdown("<h2>Análise de Qualidade do Ar - Santa Luzia (DF)</h2>", unsafe_allow_html=True)

# ============== CARREGAMENTO DE DADOS ==============
gdf = gpd.read_file("pontos/pontos_coleta.shp")
df = pd.read_excel("data/Base de dados.xlsx")

# Unifica colunas de data e hora
df["DataHora"] = pd.to_datetime(
    df["Data-Hora"].astype(str) + " " + df["(Horário Padrão do Brasil)"].astype(str),
    errors="coerce"
)
df["Data"] = df["DataHora"].dt.date
df["Hora"] = df["DataHora"].dt.time

# ============== CLASSIFICAÇÕES ==============
def classificar_temperatura(temp):
    if temp < 18: return "Baixa"
    elif 18 <= temp <= 26: return "Ideal"
    elif 26 < temp <= 32: return "Alta"
    else: return "Risco"

def classificar_umidade(umid):
    if umid < 30: return "Muito Baixa"
    elif 30 <= umid <= 60: return "Baixa"
    else: return "Ideal"

def classificar_co2(co2):
    if co2 <= 450: return "Ideal"
    elif co2 <= 1000: return "Aceitável"
    elif co2 <= 2000: return "Alta"
    else: return "Risco"

df["Classificação Temp"] = df["Temperatura (°C) "].apply(classificar_temperatura)
df["Classificação RH"] = df["RH (%) "].apply(classificar_umidade)
df["Classificação CO2"] = df["CO2 (ppm) "].apply(classificar_co2)

# ============== SIDEBAR — FILTROS ==============
st.sidebar.title("Filtros")

datas_disponiveis = sorted(df["Data"].dropna().unique())
data_sel = st.sidebar.selectbox("Selecione o dia:", datas_disponiveis)

pontos_disponiveis = df["pontos"].unique().tolist()
pontos_sel = st.sidebar.multiselect("Ponto(s) de coleta:", pontos_disponiveis, default=pontos_disponiveis)

horarios_filtrados = df[df["Data"] == data_sel]["Hora"].dropna().unique().tolist()
hora_sel = st.sidebar.selectbox("Horário(s):", ["Todos"] + sorted(horarios_filtrados), index=0)

variavel = st.sidebar.selectbox("Variável para análise estatística:", [
    "Temperatura (°C)", "Umidade Relativa (%)", "CO2 (ppm)", "Ponto de Orvalho (°C)"
])

# ============== SIDEBAR — REFERÊNCIA TÉCNICA (Locais Abertos) ==============
st.sidebar.markdown("""
<style>
    .ref-tabela {
        border-collapse: collapse;
        font-size: 12px;
        margin-top: 10px;
    }
    .ref-tabela th, .ref-tabela td {
        border: 1px solid #ccc;
        padding: 5px 6px;
        text-align: left;
    }
</style>

<h4 style='margin-top: 20px;'>Referência de Classificação (Locais Abertos):</h4>
<table class="ref-tabela">
    <tr>
        <th>Parâmetro</th>
        <th>Norma Brasileira</th>
        <th>Valor de Referência</th>
        <th>Observação</th>
    </tr>
    <tr>
        <td><b>Temperatura</b></td>
        <td>ABNT NBR 16401-3:2022</td>
        <td>
            Baixa: &lt; 18 °C<br>
            Ideal: 18–26 °C<br>
            Alta: 26–32 °C<br>
            Risco: &gt; 32 °C
        </td>
        <td>Referência de conforto térmico. &gt; 32 °C indica risco.</td>
    </tr>
    <tr>
        <td><b>Umidade Relativa</b></td>
        <td>ABNT NBR 16401-3:2022</td>
        <td>
            Muito Baixa: &lt; 30%<br>
            Baixa: 30–60%<br>
            Ideal: &gt; 60%
        </td>
        <td>Umidade baixa aumenta risco respiratório.</td>
    </tr>
    <tr>
        <td><b>Dióxido de Carbono (CO₂)</b></td>
        <td>ABNT NBR 16401-3:2022 / Portaria GM/MS nº 3.523/1998</td>
        <td>
            Ideal: ≤ 450 ppm<br>
            Aceitável: ≤ 1000 ppm<br>
            Alta: ≤ 2000 ppm<br>
            Risco: &gt; 2000 ppm
        </td>
        <td>Em áreas abertas, valores altos indicam baixa dispersão.</td>
    </tr>
</table>
""", unsafe_allow_html=True)

# ============== SIDEBAR — LEGENDA DE CORES ==============
st.sidebar.markdown("""
<style>
    .tabela-legenda {
        border-collapse: collapse;
        margin-top: 10px;
        font-size: 12px;
    }
    .tabela-legenda td {
        padding: 4px 8px;
        border: 1px solid #ccc;
        text-align: center;
    }
</style>

<h5 style='margin-top:15px;'>Legenda de Classificação Visual:</h5>
<table class='tabela-legenda'>
<tr><td style='background-color:green; color:white;'>Ideal</td><td>Verde</td></tr>
<tr><td style='background-color:blue; color:white;'>Muito Baixa / Baixa</td><td>Azul</td></tr>
<tr><td style='background-color:#ffcc00; color:black;'>Aceitável</td><td>Amarelo</td></tr>
<tr><td style='background-color:orange; color:black;'>Alta</td><td>Laranja</td></tr>
<tr><td style='background-color:red; color:white;'>Risco</td><td>Vermelho</td></tr>
</table>
""", unsafe_allow_html=True)

# ============== SIDEBAR — COMPARATIVO (Interno × Externo) ==============
st.sidebar.markdown("---")
st.sidebar.subheader("Comparativo de Referências (Linhas nos Gráficos)")
ref_tipo = st.sidebar.radio(
    "Mostrar linhas de referência",
    options=["Interno (ABNT/ANVISA)", "Externo (INMET/Referência)", "Ambos"],
    index=2
)

st.sidebar.markdown("<small>🔧 Ajuste os valores externos conforme normais INMET locais.</small>", unsafe_allow_html=True)
ext_temp = st.sidebar.number_input("Temperatura externa de referência (°C)", value=22.0, step=0.5, format="%.1f")
ext_ur   = st.sidebar.number_input("Umidade externa de referência (%)", value=60.0, step=1.0, format="%.1f")
ext_co2  = st.sidebar.number_input("CO₂ externo de referência (ppm)", value=400.0, step=10.0, format="%.0f")

# ============== FILTRAGEM ==============
colunas_variavel = {
    "Temperatura (°C)": "Temperatura (°C) ",
    "Umidade Relativa (%)": "RH (%) ",
    "CO2 (ppm)": "CO2 (ppm) ",
    "Ponto de Orvalho (°C)": "Ponto de Orvalho (°C)"
}
col_sel = colunas_variavel[variavel]

df_filtrado = df[(df["Data"] == data_sel) & (df["pontos"].isin(pontos_sel))]
if hora_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Hora"] == hora_sel]

# ============== TABELA COM ESTILOS DE CLASSIFICAÇÃO ==============
def cor_classificacao(val):
    cores = {
        "Baixa": "background-color: blue; color: white",
        "Muito Baixa": "background-color: blue; color: white",
        "Ideal": "background-color: green; color: white",
        "Alta": "background-color: orange; color: black",
        "Risco": "background-color: red; color: white",
        "Aceitável": "background-color: #ffcc00; color: black"
    }
    return cores.get(val, "")

st.markdown("### Tabela de Coletas Filtradas")
styled_df = df_filtrado[[
    "pontos", "DataHora", "Temperatura (°C) ", "Classificação Temp",
    "RH (%) ", "Classificação RH", "CO2 (ppm) ", "Classificação CO2", "Ponto de Orvalho (°C)"
]].style.applymap(cor_classificacao, subset=["Classificação Temp", "Classificação RH", "Classificação CO2"])
st.dataframe(styled_df, use_container_width=True)

# ============== ESTATÍSTICAS POR PONTO ==============
estat = df_filtrado.groupby("pontos")[col_sel].agg(["mean", "std", "median", lambda x: x.max() - x.min()]).reset_index()
estat.columns = ["Ponto", "Média", "Desvio Padrão", "Mediana", "Amplitude"]

# ============== REFERÊNCIAS (Interno × Externo) ==============
INT_TEMP = 23.0     # interno "ideal" (dentro de 18–26°C)
INT_UR   = 52.5     # interno "ideal" (meio de 40–65%)
INT_CO2  = 450.0    # interno "ideal" prático; alternativa: 700 ppm acima do externo (NBR 17037)

def linhas_ref_x(fig, xs, ref_tipo, ref_int, ref_ext, nome_int, nome_ext):
    """Adiciona linhas de referência a um gráfico Plotly, conforme seleção."""
    if ref_tipo in ("Interno (ABNT/ANVISA)", "Ambos"):
        fig.add_trace(go.Scatter(x=xs, y=[ref_int]*len(xs),
                                 mode="lines", name=nome_int,
                                 line=dict(color="green", width=3, dash="dash")))
    if ref_tipo in ("Externo (INMET/Referência)", "Ambos"):
        fig.add_trace(go.Scatter(x=xs, y=[ref_ext]*len(xs),
                                 mode="lines", name=nome_ext,
                                 line=dict(color="gray", width=3, dash="dot")))

# ============== TABELA COMPARATIVA INTERN0 × EXTERNO ==============
st.markdown("### Referências usadas (Interno × Externo)")
tabela_ref = pd.DataFrame({
    "Parâmetro": ["Temperatura (°C)", "Umidade Relativa (%)", "CO₂ (ppm)"],
    "Interno (ABNT/ANVISA)": [
        "Ideal 18–26°C (linha 23°C)",
        "Ideal 40–65% (linha 52,5%)",
        "Ideal ≤ 450 ppm (ou até 700 ppm acima do externo pela NBR 17037)"
    ],
    "Externo (INMET/Referência)": [
        f"{ext_temp:.1f} °C (normal local informada)",
        f"{ext_ur:.1f} %",
        f"{ext_co2:.0f} ppm (background/local)"
    ]
})
st.dataframe(tabela_ref, use_container_width=True)

# ============== GRÁFICO DE BARRAS: Indicadores estatísticos da variável selecionada ==============
fig = go.Figure()
fig.add_trace(go.Bar(x=estat["Ponto"], y=estat["Média"], name="Média", marker_color="green"))
fig.add_trace(go.Bar(x=estat["Ponto"], y=estat["Desvio Padrão"], name="Desvio Padrão", marker_color="orange"))
fig.add_trace(go.Bar(x=estat["Ponto"], y=estat["Mediana"], name="Mediana", marker_color="blue"))
fig.add_trace(go.Bar(x=estat["Ponto"], y=estat["Amplitude"], name="Amplitude", marker_color="red"))
fig.update_layout(
    title=f"Indicadores Estatísticos - {variavel} ({data_sel})",
    xaxis_title="Ponto",
    yaxis_title=variavel,
    barmode="group"
)
st.plotly_chart(fig, use_container_width=True)

# ============== GRÁFICO DE LINHA: CO2 médio por ponto ==============
df_co2 = df[df["Data"] == data_sel].groupby("pontos")["CO2 (ppm) "].mean().reset_index()
fig_co2 = go.Figure()
fig_co2.add_trace(go.Scatter(
    x=df_co2["pontos"], y=df_co2["CO2 (ppm) "],
    mode="lines+markers", name="Média de CO2 (ppm)",
    line=dict(color="cyan", width=3)
))
linhas_ref_x(
    fig_co2,
    xs=df_co2["pontos"],
    ref_tipo=ref_tipo,
    ref_int=INT_CO2,
    ref_ext=ext_co2,
    nome_int="Interno (ideal) 450 ppm",
    nome_ext=f"Externo (ref) {ext_co2:.0f} ppm"
)
fig_co2.update_layout(title="Média de CO₂ por Ponto (com referências)", xaxis_title="Ponto", yaxis_title="ppm")
st.plotly_chart(fig_co2, use_container_width=True)

# ============== GRÁFICOS COMPARATIVOS (BARRAS + LINHAS DE REFERÊNCIA) ==============
df_mean = df[df["Data"] == data_sel].groupby("pontos").agg({
    "Temperatura (°C) ": "mean",
    "RH (%) ": "mean",
    "CO2 (ppm) ": "mean"
}).reset_index()

# Temperatura
fig_temp = go.Figure()
fig_temp.add_trace(go.Bar(x=df_mean["pontos"], y=df_mean["Temperatura (°C) "],
                          name="Temperatura Média", marker_color="tomato"))
linhas_ref_x(
    fig_temp, xs=df_mean["pontos"],
    ref_tipo=ref_tipo, ref_int=INT_TEMP, ref_ext=ext_temp,
    nome_int="Interno (ideal) 23°C",
    nome_ext=f"Externo (ref) {ext_temp:.1f}°C"
)
fig_temp.update_layout(title="Temperatura Média vs Referências", yaxis_title="°C")
st.plotly_chart(fig_temp, use_container_width=True)

# Umidade
fig_umid = go.Figure()
fig_umid.add_trace(go.Bar(x=df_mean["pontos"], y=df_mean["RH (%) "],
                          name="Umidade Média", marker_color="skyblue"))
linhas_ref_x(
    fig_umid, xs=df_mean["pontos"],
    ref_tipo=ref_tipo, ref_int=INT_UR, ref_ext=ext_ur,
    nome_int="Interno (ideal) 52,5%",
    nome_ext=f"Externo (ref) {ext_ur:.1f}%"
)
fig_umid.update_layout(title="Umidade Relativa Média vs Referências", yaxis_title="%")
st.plotly_chart(fig_umid, use_container_width=True)

# CO₂
fig_co2_ref = go.Figure()
fig_co2_ref.add_trace(go.Bar(x=df_mean["pontos"], y=df_mean["CO2 (ppm) "],
                             name="CO₂ Médio", marker_color="lightgreen"))
linhas_ref_x(
    fig_co2_ref, xs=df_mean["pontos"],
    ref_tipo=ref_tipo, ref_int=INT_CO2, ref_ext=ext_co2,
    nome_int="Interno (ideal) 450 ppm",
    nome_ext=f"Externo (ref) {ext_co2:.0f} ppm"
)
fig_co2_ref.update_layout(title="CO₂ Médio vs Referências", yaxis_title="ppm")
st.plotly_chart(fig_co2_ref, use_container_width=True)

# ============== MAPA INTERATIVO COM TOOLTIP ==============
m = folium.Map(location=[gdf.geometry.y.mean(), gdf.geometry.x.mean()], zoom_start=16, tiles="CartoDB positron")
icon_path = "icone_ponto.png"
icon = CustomIcon(icon_image=icon_path, icon_size=(40, 40), icon_anchor=(20, 40))

for idx, row in gdf.iterrows():
    ponto_nome = f"Ponto {idx + 1}"
    if ponto_nome not in pontos_sel:
        continue
    dados_ponto = df[(df["pontos"] == ponto_nome) & (df["Data"] == data_sel)]
    if not dados_ponto.empty:
        media = dados_ponto[col_sel].mean().round(2)
        std = dados_ponto[col_sel].std().round(2)
        mediana = dados_ponto[col_sel].median().round(2)
        amplitude = (dados_ponto[col_sel].max() - dados_ponto[col_sel].min()).round(2)
        tooltip = f"""
        <b>{ponto_nome}</b><br>
        {variavel}:<br>
        Média: {media}<br>
        Desvio Padrão: {std}<br>
        Mediana: {mediana}<br>
        Amplitude: {amplitude}
        """
        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            tooltip=tooltip,
            icon=icon
        ).add_to(m)

# Render folium
st_folium(m, width=1200, height=600)

# ============== SALVAR MAPA EM HTML (para screenshot) ==============
m_html_path = "mapa_qualidade.html"
m.save(m_html_path)

# ============== EXPORTAÇÃO PDF (GRÁFICOS + MAPA) ==============
# salvar os 3 gráficos comparativos como PNG (requer kaleido)
def salvar_graficos_png():
    arquivos = {}
    try:
        fig_temp_path = "grafico_temp_comparativo.png"
        fig_umid_path = "grafico_umid_comparativo.png"
        fig_co2c_path = "grafico_co2_comparativo.png"

        fig_temp.write_image(fig_temp_path, scale=2)
        fig_umid.write_image(fig_umid_path, scale=2)
        fig_co2_ref.write_image(fig_co2c_path, scale=2)

        arquivos["temp"] = fig_temp_path
        arquivos["umid"] = fig_umid_path
        arquivos["co2"]  = fig_co2c_path
        return arquivos, None
    except Exception as e:
        return None, f"Falha ao salvar gráficos (kaleido): {e}"

# capturar screenshot do mapa (HTML) como PNG via Selenium
def salvar_mapa_png(html_path, png_path="mapa_qualidade.png", width=1200, height=800, sleep_s=2):
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service as ChromeService
        from PIL import Image
        import time

        # Se tiver chromedriver em caminho específico, informe aqui:
        CHROME_DRIVER_PATH = None  # ex.: r"C:\Users\SeuUsuario\chromedriver.exe"

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument(f"--window-size={width},{height}")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

        if CHROME_DRIVER_PATH and os.path.exists(CHROME_DRIVER_PATH):
            driver = webdriver.Chrome(service=ChromeService(CHROME_DRIVER_PATH), options=options)
        else:
            driver = webdriver.Chrome(options=options)

        driver.get("file://" + os.path.abspath(html_path))
        time.sleep(sleep_s)  # aguarda tiles e ícones carregar
        driver.save_screenshot(png_path)
        driver.quit()

        # (opcional) recorte leve
        try:
            im = Image.open(png_path)
            crop = (5, 5, im.width-5, im.height-5)
            im = im.crop(crop)
            im.save(png_path)
        except Exception:
            pass

        return png_path, None
    except Exception as e:
        return None, f"Falha ao capturar screenshot do mapa (Selenium): {e}"

def gerar_pdf_relatorio(arquivos_png, tabela_ref_df, mapa_png=None, nome_arquivo="relatorio_completo.pdf"):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table as RLTable, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
    except Exception as e:
        st.error(f"⚠️ Falha ao importar reportlab: {e}\nInstale com: pip install reportlab")
        return None

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    W, H = A4
    styles = getSampleStyleSheet()
    story = []

    titulo = f"Relatório Comparativo – Interno × Externo"
    subtitulo = f"Data selecionada: {data_sel}  |  Pontos: {', '.join(pontos_sel)}"
    story.append(Paragraph(titulo, styles["Title"]))
    story.append(Paragraph(subtitulo, styles["Normal"]))
    story.append(Spacer(1, 10))

    # Tabela de referências
    story.append(Paragraph("Referências usadas (Interno × Externo)", styles["Heading2"]))
    tabela = [tabela_ref_df.columns.tolist()] + tabela_ref_df.values.tolist()
    tbl = RLTable(tabela, repeatRows=1, colWidths=[W*0.28, W*0.34, W*0.28])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("TEXTCOLOR", (0,0), (-1,0), colors.black),
        ("ALIGN", (0,0), (-1,-1), "LEFT"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,0), 9),
        ("FONTSIZE", (0,1), (-1,-1), 9),
        ("INNERGRID", (0,0), (-1,-1), 0.25, colors.grey),
        ("BOX", (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 12))

    # Gráficos
    story.append(Paragraph("Gráficos comparativos", styles["Heading2"]))
    for rotulo, caminho in [("Temperatura Média vs Referências", arquivos_png.get("temp")),
                            ("Umidade Relativa Média vs Referências", arquivos_png.get("umid")),
                            ("CO₂ Médio vs Referências", arquivos_png.get("co2"))]:
        if caminho and os.path.exists(caminho):
            story.append(Paragraph(rotulo, styles["Heading3"]))
            img = RLImage(caminho, width=W-72, height=(W-72)*0.55)
            story.append(img)
            story.append(Spacer(1, 8))

    # Mapa
    if mapa_png and os.path.exists(mapa_png):
        story.append(Paragraph("Mapa de pontos de coleta", styles["Heading2"]))
        img_map = RLImage(mapa_png, width=W-72, height=(W-72)*0.6)
        story.append(img_map)
        story.append(Spacer(1, 8))

    # Rodapé de referências
    refs = [
        "Interno: ABNT NBR 16401-2/3 (conforto e QAI), ANVISA RE 9/2003; NBR 17037/2023 (QAI).",
        "Externo: Normais Climatológicas INMET (1991–2020) para temperatura/umidade; CO₂ externo de referência (background local)."
    ]
    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Referências:</b>", styles["Normal"]))
    for r in refs:
        story.append(Paragraph(f"- {r}", styles["Normal"]))

    doc.build(story)

    buffer.seek(0)
    with open(nome_arquivo, "wb") as f:
        f.write(buffer.read())
    buffer.seek(0)
    return nome_arquivo

st.markdown("---")
st.subheader("📄 Exportar relatório (PDF)")

if st.button("Gerar PDF com Tabela, Gráficos e Mapa"):
    arquivos_png, err = salvar_graficos_png()
    if err:
        st.error(err)
    mapa_png, err_map = salvar_mapa_png(m_html_path, png_path="mapa_qualidade.png", width=1200, height=800, sleep_s=2)
    if err_map:
        st.warning(err_map + "  (o PDF será gerado sem o mapa)")
        mapa_png = None

    pdf_path = gerar_pdf_relatorio(arquivos_png or {}, tabela_ref, mapa_png=mapa_png, nome_arquivo="relatorio_qualidade_ar.pdf")
    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="⬇️ Baixar relatório (PDF)",
                data=f,
                file_name=f"relatorio_qualidade_ar_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf"
            )
    else:
        st.error("Não foi possível gerar o PDF. Confira as dependências (kaleido, reportlab, selenium, pillow) e o driver do navegador.")
