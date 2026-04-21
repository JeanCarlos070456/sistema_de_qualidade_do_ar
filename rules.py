import pandas as pd


def classificar_temperatura(temp):
    if pd.isna(temp):
        return "N/D"
    if temp < 18:
        return "Baixa"
    if temp <= 26:
        return "Ideal"
    if temp <= 32:
        return "Alta"
    return "Risco"


def classificar_umidade(umid):
    if pd.isna(umid):
        return "N/D"
    if umid < 30:
        return "Muito Baixa"
    if umid <= 60:
        return "Baixa"
    return "Ideal"


def classificar_co2(co2):
    if pd.isna(co2):
        return "N/D"
    if co2 <= 450:
        return "Ideal"
    if co2 <= 1000:
        return "Aceitável"
    if co2 <= 2000:
        return "Alta"
    return "Risco"


def cor_classificacao(val):
    cores = {
        "Baixa": "background-color: blue; color: white",
        "Muito Baixa": "background-color: blue; color: white",
        "Ideal": "background-color: green; color: white",
        "Alta": "background-color: orange; color: black",
        "Risco": "background-color: red; color: white",
        "Aceitável": "background-color: #ffcc00; color: black",
        "N/D": "background-color: #999999; color: white",
    }
    return cores.get(val, "")