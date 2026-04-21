import pandas as pd
import plotly.graph_objects as go

from settings import INTERNAL_REFERENCES


def linhas_ref_x(fig, xs, ref_tipo, ref_int, ref_ext, nome_int, nome_ext):
    if ref_tipo in ("Interno (ABNT/ANVISA)", "Ambos"):
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=[ref_int] * len(xs),
                mode="lines",
                name=nome_int,
                line=dict(color="green", width=3, dash="dash"),
            )
        )
    if ref_tipo in ("Externo (INMET/Referência)", "Ambos"):
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=[ref_ext] * len(xs),
                mode="lines",
                name=nome_ext,
                line=dict(color="gray", width=3, dash="dot"),
            )
        )


def build_reference_table(ext_temp, ext_ur, ext_co2):
    return pd.DataFrame(
        {
            "Parâmetro": ["Temperatura (°C)", "Umidade Relativa (%)", "CO₂ (ppm)"],
            "Interno (ABNT/ANVISA)": [
                "Ideal 18–26°C (linha 23°C)",
                "Ideal 40–65% (linha 52,5%)",
                "Ideal ≤ 450 ppm",
            ],
            "Externo (INMET/Referência)": [
                f"{ext_temp:.1f} °C",
                f"{ext_ur:.1f} %",
                f"{ext_co2:.0f} ppm",
            ],
        }
    )


def chart_statistics(estat, variavel, data_sel):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=estat["Ponto"], y=estat["Média"], name="Média", marker_color="green"))
    fig.add_trace(go.Bar(x=estat["Ponto"], y=estat["Desvio Padrão"], name="Desvio Padrão", marker_color="orange"))
    fig.add_trace(go.Bar(x=estat["Ponto"], y=estat["Mediana"], name="Mediana", marker_color="blue"))
    fig.add_trace(go.Bar(x=estat["Ponto"], y=estat["Amplitude"], name="Amplitude", marker_color="red"))
    fig.update_layout(
        title=f"Indicadores Estatísticos - {variavel} ({data_sel})",
        xaxis_title="Ponto",
        yaxis_title=variavel,
        barmode="group",
    )
    return fig


def chart_co2(df_filtrado, ref_tipo, ext_co2):
    df_co2 = df_filtrado.groupby("pontos")["CO2 (ppm)"].mean().reset_index()
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df_co2["pontos"],
            y=df_co2["CO2 (ppm)"],
            mode="lines+markers",
            name="Média de CO₂ (ppm)",
            line=dict(color="cyan", width=3),
        )
    )
    linhas_ref_x(
        fig,
        xs=df_co2["pontos"],
        ref_tipo=ref_tipo,
        ref_int=INTERNAL_REFERENCES["co2"],
        ref_ext=ext_co2,
        nome_int="Interno (ideal) 450 ppm",
        nome_ext=f"Externo (ref) {ext_co2:.0f} ppm",
    )
    fig.update_layout(title="Média de CO₂ por Ponto", xaxis_title="Ponto", yaxis_title="ppm")
    return fig


def chart_means(df_filtrado, ref_tipo, ext_temp, ext_ur, ext_co2):
    df_mean = (
        df_filtrado.groupby("pontos")[["Temperatura (°C)", "RH (%)", "CO2 (ppm)"]]
        .mean()
        .reset_index()
    )

    fig_temp = go.Figure()
    fig_temp.add_trace(go.Bar(x=df_mean["pontos"], y=df_mean["Temperatura (°C)"], name="Temperatura Média", marker_color="tomato"))
    linhas_ref_x(fig_temp, df_mean["pontos"], ref_tipo, INTERNAL_REFERENCES["temp"], ext_temp, "Interno 23°C", f"Externo {ext_temp:.1f}°C")
    fig_temp.update_layout(title="Temperatura Média vs Referências", yaxis_title="°C")

    fig_umid = go.Figure()
    fig_umid.add_trace(go.Bar(x=df_mean["pontos"], y=df_mean["RH (%)"], name="Umidade Média", marker_color="skyblue"))
    linhas_ref_x(fig_umid, df_mean["pontos"], ref_tipo, INTERNAL_REFERENCES["umid"], ext_ur, "Interno 52,5%", f"Externo {ext_ur:.1f}%")
    fig_umid.update_layout(title="Umidade Relativa Média vs Referências", yaxis_title="%")

    fig_co2 = go.Figure()
    fig_co2.add_trace(go.Bar(x=df_mean["pontos"], y=df_mean["CO2 (ppm)"], name="CO₂ Médio", marker_color="lightgreen"))
    linhas_ref_x(fig_co2, df_mean["pontos"], ref_tipo, INTERNAL_REFERENCES["co2"], ext_co2, "Interno 450 ppm", f"Externo {ext_co2:.0f} ppm")
    fig_co2.update_layout(title="CO₂ Médio vs Referências", yaxis_title="ppm")

    return fig_temp, fig_umid, fig_co2