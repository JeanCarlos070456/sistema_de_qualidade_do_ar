from pathlib import Path
import pandas as pd
import streamlit as st

from settings import EXCEL_PATH
from rules import (
    classificar_temperatura,
    classificar_umidade,
    classificar_co2,
)

REQUIRED_COLUMNS = [
    "Data-Hora",
    "(Horário Padrão do Brasil)",
    "pontos",
    "Temperatura (°C)",
    "RH (%)",
    "CO2 (ppm)",
    "Ponto de Orvalho (°C)",
]


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    return df


def validate_columns(df: pd.DataFrame) -> None:
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            "Colunas obrigatórias ausentes no Excel: " + ", ".join(missing)
        )


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    if not Path(EXCEL_PATH).exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {EXCEL_PATH}")

    df = pd.read_excel(EXCEL_PATH)
    df = normalize_columns(df)
    validate_columns(df)

    df["DataHora"] = pd.to_datetime(
        df["Data-Hora"].astype(str).str.strip() + " " + df["(Horário Padrão do Brasil)"].astype(str).str.strip(),
        errors="coerce",
    )
    df["Data"] = df["DataHora"].dt.date
    df["Hora"] = df["DataHora"].dt.time
    df["HoraStr"] = df["DataHora"].dt.strftime("%H:%M:%S")

    numeric_columns = [
        "Temperatura (°C)",
        "RH (%)",
        "CO2 (ppm)",
        "Ponto de Orvalho (°C)",
    ]
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["Classificação Temp"] = df["Temperatura (°C)"].apply(classificar_temperatura)
    df["Classificação RH"] = df["RH (%)"].apply(classificar_umidade)
    df["Classificação CO2"] = df["CO2 (ppm)"].apply(classificar_co2)

    df["pontos"] = df["pontos"].astype(str).str.strip()

    return df


def filter_data(df: pd.DataFrame, data_sel, pontos_sel, hora_sel):
    filtrado = df[(df["Data"] == data_sel) & (df["pontos"].isin(pontos_sel))].copy()
    if hora_sel != "Todos":
        filtrado = filtrado[filtrado["HoraStr"] == hora_sel].copy()
    return filtrado


def build_statistics(df_filtrado: pd.DataFrame, col_sel: str) -> pd.DataFrame:
    if df_filtrado.empty:
        return pd.DataFrame(columns=["Ponto", "Média", "Desvio Padrão", "Mediana", "Amplitude"])

    estat = (
        df_filtrado.groupby("pontos")[col_sel]
        .agg(
            mean="mean",
            std="std",
            median="median",
            amplitude=lambda x: x.max() - x.min(),
        )
        .reset_index()
    )

    estat.columns = ["Ponto", "Média", "Desvio Padrão", "Mediana", "Amplitude"]
    return estat.fillna(0)