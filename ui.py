import streamlit as st


VARIABLE_MAP = {
    "Temperatura (°C)": "Temperatura (°C)",
    "Umidade Relativa (%)": "RH (%)",
    "CO2 (ppm)": "CO2 (ppm)",
    "Ponto de Orvalho (°C)": "Ponto de Orvalho (°C)",
}


def render_sidebar(df):
    st.sidebar.title("Filtros")

    datas_disponiveis = sorted(df["Data"].dropna().unique())
    data_sel = st.sidebar.selectbox("Selecione o dia:", datas_disponiveis)

    pontos_disponiveis = sorted(df["pontos"].dropna().unique().tolist())
    pontos_sel = st.sidebar.multiselect(
        "Ponto(s) de coleta:",
        pontos_disponiveis,
        default=pontos_disponiveis,
    )

    horarios_filtrados = (
        df[df["Data"] == data_sel]["HoraStr"].dropna().unique().tolist()
    )
    hora_sel = st.sidebar.selectbox(
        "Horário(s):",
        ["Todos"] + sorted(horarios_filtrados),
        index=0,
    )

    variavel = st.sidebar.selectbox(
        "Variável para análise estatística:",
        list(VARIABLE_MAP.keys()),
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("Comparativo de Referências")
    ref_tipo = st.sidebar.radio(
        "Mostrar linhas de referência",
        options=["Interno (ABNT/ANVISA)", "Externo (INMET/Referência)", "Ambos"],
        index=2,
    )

    ext_temp = st.sidebar.number_input(
        "Temperatura externa de referência (°C)",
        value=22.0,
        step=0.5,
        format="%.1f",
    )
    ext_ur = st.sidebar.number_input(
        "Umidade externa de referência (%)",
        value=60.0,
        step=1.0,
        format="%.1f",
    )
    ext_co2 = st.sidebar.number_input(
        "CO₂ externo de referência (ppm)",
        value=400.0,
        step=10.0,
        format="%.0f",
    )

    render_sidebar_tables()

    return {
        "data_sel": data_sel,
        "pontos_sel": pontos_sel,
        "hora_sel": hora_sel,
        "variavel": variavel,
        "col_sel": VARIABLE_MAP[variavel],
        "ref_tipo": ref_tipo,
        "ext_temp": ext_temp,
        "ext_ur": ext_ur,
        "ext_co2": ext_co2,
    }


def render_sidebar_tables():
    st.sidebar.markdown(
        """
        <h4 style='margin-top: 20px;'>Referência de Classificação (Locais Abertos):</h4>
        <table style="border-collapse: collapse; font-size: 12px; margin-top: 10px;">
            <tr>
                <th style="border:1px solid #ccc;padding:5px;">Parâmetro</th>
                <th style="border:1px solid #ccc;padding:5px;">Valor de Referência</th>
            </tr>
            <tr>
                <td style="border:1px solid #ccc;padding:5px;"><b>Temperatura</b></td>
                <td style="border:1px solid #ccc;padding:5px;">Baixa &lt; 18 | Ideal 18–26 | Alta 26–32 | Risco &gt; 32</td>
            </tr>
            <tr>
                <td style="border:1px solid #ccc;padding:5px;"><b>Umidade</b></td>
                <td style="border:1px solid #ccc;padding:5px;">Muito Baixa &lt; 30 | Baixa 30–60 | Ideal &gt; 60</td>
            </tr>
            <tr>
                <td style="border:1px solid #ccc;padding:5px;"><b>CO₂</b></td>
                <td style="border:1px solid #ccc;padding:5px;">Ideal ≤ 450 | Aceitável ≤ 1000 | Alta ≤ 2000 | Risco &gt; 2000</td>
            </tr>
        </table>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown(
        """
        <h5 style='margin-top:15px;'>Legenda de Classificação Visual:</h5>
        <table style='border-collapse: collapse; margin-top: 10px; font-size: 12px;'>
            <tr><td style='padding:4px 8px;border:1px solid #ccc;background-color:green;color:white;'>Ideal</td><td style='padding:4px 8px;border:1px solid #ccc;'>Verde</td></tr>
            <tr><td style='padding:4px 8px;border:1px solid #ccc;background-color:blue;color:white;'>Muito Baixa / Baixa</td><td style='padding:4px 8px;border:1px solid #ccc;'>Azul</td></tr>
            <tr><td style='padding:4px 8px;border:1px solid #ccc;background-color:#ffcc00;color:black;'>Aceitável</td><td style='padding:4px 8px;border:1px solid #ccc;'>Amarelo</td></tr>
            <tr><td style='padding:4px 8px;border:1px solid #ccc;background-color:orange;color:black;'>Alta</td><td style='padding:4px 8px;border:1px solid #ccc;'>Laranja</td></tr>
            <tr><td style='padding:4px 8px;border:1px solid #ccc;background-color:red;color:white;'>Risco</td><td style='padding:4px 8px;border:1px solid #ccc;'>Vermelho</td></tr>
        </table>
        """,
        unsafe_allow_html=True,
    )