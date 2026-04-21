from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"

EXCEL_PATH = DATA_DIR / "Base de dados.xlsx"
ICON_PATH = ASSETS_DIR / "icone_ponto.png"

APP_TITLE = "Análise da Qualidade do Ar - Santa Luzia (DF)"
PAGE_TITLE = "Análise da Qualidade do Ar - Santa Luzia"

# Ajuste aqui as coordenadas reais dos 3 pontos
POINTS_COORDS = {
    "Ponto 1": {"lat": -15.77512, "lon": -47.98996},
    "Ponto 2": {"lat": -15.77394, "lon": -47.98632},
    "Ponto 3": {"lat": -15.78031, "lon": -47.98043},
    "Ponto 4": {"lat": -15.77639, "lon": -47.99554},
}

MAP_CENTER = {
    "lat": sum(p["lat"] for p in POINTS_COORDS.values()) / len(POINTS_COORDS),
    "lon": sum(p["lon"] for p in POINTS_COORDS.values()) / len(POINTS_COORDS),
}
MAP_ZOOM = 16

INTERNAL_REFERENCES = {
    "temp": 23.0,
    "umid": 52.5,
    "co2": 450.0,
}