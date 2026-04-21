from base64 import b64encode
from pathlib import Path

import folium
import streamlit as st
from folium.features import CustomIcon

from settings import POINTS_COORDS, ICON_PATH


def _build_icon():
    icon_file = Path(ICON_PATH)
    if not icon_file.exists():
        return None

    encoded = b64encode(icon_file.read_bytes()).decode("utf-8")
    icon_url = f"data:image/png;base64,{encoded}"

    return CustomIcon(
        icon_image=icon_url,
        icon_size=(36, 36),
        icon_anchor=(18, 36),
        popup_anchor=(0, -30),
    )


def render_map(df_filtrado, col_sel, variavel, pontos_sel):
    grouped = df_filtrado.groupby("pontos")

    pontos_mapa = []
    for ponto_nome, coords in POINTS_COORDS.items():
        if ponto_nome not in pontos_sel:
            continue
        if ponto_nome not in grouped.groups:
            continue

        dados_ponto = grouped.get_group(ponto_nome)

        media = round(dados_ponto[col_sel].mean(), 2)
        std = round(dados_ponto[col_sel].std() if len(dados_ponto) > 1 else 0, 2)
        mediana = round(dados_ponto[col_sel].median(), 2)
        amplitude = round(dados_ponto[col_sel].max() - dados_ponto[col_sel].min(), 2)

        popup = f"""
        <div style="font-size:14px;">
            <b>{ponto_nome}</b><br>
            {variavel}:<br>
            Média: {media}<br>
            Desvio Padrão: {std}<br>
            Mediana: {mediana}<br>
            Amplitude: {amplitude}
        </div>
        """

        pontos_mapa.append(
            {
                "nome": ponto_nome,
                "lat": coords["lat"],
                "lon": coords["lon"],
                "popup": popup,
            }
        )

    if not pontos_mapa:
        st.warning("Nenhum ponto disponível para exibir no mapa.")
        return

    lat_media = sum(p["lat"] for p in pontos_mapa) / len(pontos_mapa)
    lon_media = sum(p["lon"] for p in pontos_mapa) / len(pontos_mapa)

    m = folium.Map(
        location=[lat_media, lon_media],
        zoom_start=16,
        tiles="OpenStreetMap",
    )

    bounds = []

    for p in pontos_mapa:
        marker_kwargs = {
            "location": [p["lat"], p["lon"]],
            "popup": folium.Popup(p["popup"], max_width=300),
            "tooltip": p["nome"],
        }

        custom_icon = _build_icon()
        if custom_icon is not None:
            marker_kwargs["icon"] = custom_icon
        else:
            marker_kwargs["icon"] = folium.Icon(color="blue", icon="info-sign")

        folium.Marker(**marker_kwargs).add_to(m)
        bounds.append([p["lat"], p["lon"]])

    if len(bounds) == 1:
        m.location = bounds[0]
        m.zoom_start = 17
    else:
        m.fit_bounds(bounds, padding=(30, 30))

    st.components.v1.html(m._repr_html_(), height=620, scrolling=False)