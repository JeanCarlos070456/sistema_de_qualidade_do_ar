from io import BytesIO
from math import cos, log, pi, radians, tan
from pathlib import Path
from tempfile import TemporaryDirectory

import requests
from PIL import Image, ImageDraw, ImageFont

from settings import POINTS_COORDS, ICON_PATH


TILE_SIZE = 256
USER_AGENT = "sistema_de_qualidade_do_ar/1.0"
TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"


def _latlon_to_world_pixels(lat: float, lon: float, zoom: int) -> tuple[float, float]:
    scale = TILE_SIZE * (2**zoom)
    x = (lon + 180.0) / 360.0 * scale
    lat_rad = radians(lat)
    y = (
        (1.0 - log(tan(lat_rad) + 1.0 / cos(lat_rad)) / pi)
        / 2.0
        * scale
    )
    return x, y


def _fit_zoom(points: list[dict], width: int, height: int, padding: int) -> int:
    if len(points) <= 1:
        return 17

    usable_w = max(width - 2 * padding, 100)
    usable_h = max(height - 2 * padding, 100)

    for zoom in range(19, 0, -1):
        xs = []
        ys = []
        for p in points:
            x, y = _latlon_to_world_pixels(p["lat"], p["lon"], zoom)
            xs.append(x)
            ys.append(y)

        span_x = max(xs) - min(xs)
        span_y = max(ys) - min(ys)

        if span_x <= usable_w and span_y <= usable_h:
            return zoom

    return 1


def _download_tile(z: int, x: int, y: int) -> Image.Image:
    max_tile = 2**z
    if x < 0 or y < 0 or x >= max_tile or y >= max_tile:
        return Image.new("RGB", (TILE_SIZE, TILE_SIZE), "white")

    url = TILE_URL.format(z=z, x=x, y=y)
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    return Image.open(BytesIO(resp.content)).convert("RGB")


def _load_pin_icon(target_height: int = 60) -> Image.Image | None:
    icon_path = Path(ICON_PATH)
    if not icon_path.exists():
        return None

    icon = Image.open(icon_path).convert("RGBA")
    width, height = icon.size

    if height <= 0:
        return icon

    scale = target_height / height
    new_width = max(1, int(width * scale))
    new_height = max(1, int(height * scale))

    return icon.resize((new_width, new_height), Image.LANCZOS)


def _load_font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def _safe_round(value, ndigits=2):
    if value is None:
        return 0
    try:
        if value != value:
            return 0
    except Exception:
        pass
    return round(float(value), ndigits)


def _build_point_summaries(df_filtrado, pontos_sel, col_sel, variavel):
    grouped = df_filtrado.groupby("pontos")
    summaries = []

    for nome, coords in POINTS_COORDS.items():
        if nome not in pontos_sel:
            continue
        if nome not in grouped.groups:
            continue

        dados_ponto = grouped.get_group(nome)

        media = _safe_round(dados_ponto[col_sel].mean(), 2)
        std = _safe_round(dados_ponto[col_sel].std() if len(dados_ponto) > 1 else 0, 2)
        mediana = _safe_round(dados_ponto[col_sel].median(), 2)
        amplitude = _safe_round(dados_ponto[col_sel].max() - dados_ponto[col_sel].min(), 2)

        summaries.append(
            {
                "nome": nome,
                "lat": coords["lat"],
                "lon": coords["lon"],
                "variavel": variavel,
                "media": media,
                "std": std,
                "mediana": mediana,
                "amplitude": amplitude,
            }
        )

    return summaries


def _measure_info_box(draw, point, title_font, body_font):
    linhas = [
        point["nome"],
        f'{point["variavel"]}',
        f'Média: {point["media"]}',
        f'Desvio: {point["std"]}',
        f'Mediana: {point["mediana"]}',
        f'Amplitude: {point["amplitude"]}',
    ]

    widths = []
    heights = []

    for i, linha in enumerate(linhas):
        font = title_font if i == 0 else body_font
        bbox = draw.textbbox((0, 0), linha, font=font)
        widths.append(bbox[2] - bbox[0])
        heights.append(bbox[3] - bbox[1])

    box_width = max(widths) + 24
    box_height = sum(heights) + 24 + (len(linhas) - 1) * 6

    return linhas, heights, box_width, box_height


def _draw_info_box(draw, x, y, point, title_font, body_font):
    linhas, heights, box_width, box_height = _measure_info_box(
        draw, point, title_font, body_font
    )

    draw.rounded_rectangle(
        (x, y, x + box_width, y + box_height),
        radius=12,
        fill=(255, 255, 255, 235),
        outline=(60, 60, 60, 180),
        width=2,
    )

    cursor_y = y + 10
    for i, linha in enumerate(linhas):
        font = title_font if i == 0 else body_font
        draw.text((x + 12, cursor_y), linha, fill="black", font=font)
        cursor_y += heights[i] + 6

    return box_width, box_height


def _rects_overlap(a, b, gap=10):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return not (
        ax2 + gap < bx1 or
        bx2 + gap < ax1 or
        ay2 + gap < by1 or
        by2 + gap < ay1
    )


def _clamp_box(x, y, box_w, box_h, width, height, margin=20, top_reserved=70):
    x = max(margin, min(x, width - box_w - margin))
    y = max(top_reserved, min(y, height - box_h - margin))
    return x, y


def _pick_box_position(
    px,
    anchor_y,
    box_w,
    box_h,
    width,
    height,
    occupied_rects,
):
    candidates = [
        (px + 22, anchor_y - box_h - 10),         # direita superior
        (px - box_w - 22, anchor_y - box_h - 10), # esquerda superior
        (px + 22, anchor_y + 10),                 # direita inferior
        (px - box_w - 22, anchor_y + 10),         # esquerda inferior
        (px - box_w // 2, anchor_y - box_h - 20), # centro superior
        (px - box_w // 2, anchor_y + 15),         # centro inferior
    ]

    for cand_x, cand_y in candidates:
        cand_x, cand_y = _clamp_box(
            cand_x, cand_y, box_w, box_h, width, height
        )
        rect = (cand_x, cand_y, cand_x + box_w, cand_y + box_h)

        if not any(_rects_overlap(rect, r) for r in occupied_rects):
            return cand_x, cand_y, rect

    # fallback: procura uma coluna vertical livre
    step = 18
    for test_y in range(80, max(81, height - box_h - 20), step):
        for test_x in range(20, max(21, width - box_w - 20), step):
            rect = (test_x, test_y, test_x + box_w, test_y + box_h)
            if not any(_rects_overlap(rect, r) for r in occupied_rects):
                return test_x, test_y, rect

    # último fallback
    cand_x, cand_y = _clamp_box(20, 80, box_w, box_h, width, height)
    rect = (cand_x, cand_y, cand_x + box_w, cand_y + box_h)
    return cand_x, cand_y, rect


def export_static_map(
    df_filtrado,
    pontos_sel,
    col_sel,
    variavel,
    width: int = 1200,
    height: int = 800,
    padding: int = 80,
):
    temp_dir = TemporaryDirectory()
    output_path = Path(temp_dir.name) / "mapa_pontos.png"

    selected_points = _build_point_summaries(
        df_filtrado=df_filtrado,
        pontos_sel=pontos_sel,
        col_sel=col_sel,
        variavel=variavel,
    )

    if not selected_points:
        raise ValueError("Nenhum ponto selecionado para exportar o mapa.")

    zoom = _fit_zoom(selected_points, width, height, padding)

    pixel_points = []
    for p in selected_points:
        world_x, world_y = _latlon_to_world_pixels(p["lat"], p["lon"], zoom)
        pixel_points.append(
            {
                **p,
                "world_x": world_x,
                "world_y": world_y,
            }
        )

    xs = [p["world_x"] for p in pixel_points]
    ys = [p["world_y"] for p in pixel_points]

    if len(pixel_points) == 1:
        center_x = xs[0]
        center_y = ys[0]
    else:
        center_x = (min(xs) + max(xs)) / 2.0
        center_y = (min(ys) + max(ys)) / 2.0

    left = center_x - width / 2.0
    top = center_y - height / 2.0
    right = center_x + width / 2.0
    bottom = center_y + height / 2.0

    tile_x_min = int(left // TILE_SIZE)
    tile_y_min = int(top // TILE_SIZE)
    tile_x_max = int(right // TILE_SIZE)
    tile_y_max = int(bottom // TILE_SIZE)

    stitched = Image.new(
        "RGB",
        (
            (tile_x_max - tile_x_min + 1) * TILE_SIZE,
            (tile_y_max - tile_y_min + 1) * TILE_SIZE,
        ),
        "white",
    )

    for tx in range(tile_x_min, tile_x_max + 1):
        for ty in range(tile_y_min, tile_y_max + 1):
            tile = _download_tile(zoom, tx, ty)
            px = (tx - tile_x_min) * TILE_SIZE
            py = (ty - tile_y_min) * TILE_SIZE
            stitched.paste(tile, (px, py))

    crop_left = int(left - tile_x_min * TILE_SIZE)
    crop_top = int(top - tile_y_min * TILE_SIZE)
    crop_right = crop_left + width
    crop_bottom = crop_top + height

    final_map = stitched.crop(
        (crop_left, crop_top, crop_right, crop_bottom)
    ).convert("RGBA")

    draw = ImageDraw.Draw(final_map)
    pin_icon = _load_pin_icon(target_height=60)
    title_font = _load_font(24)
    body_font = _load_font(18)
    map_title_font = _load_font(28)

    title = "Mapa dos pontos de coleta"
    title_bbox = draw.textbbox((20, 20), title, font=map_title_font)
    draw.rounded_rectangle(
        (
            title_bbox[0] - 10,
            title_bbox[1] - 8,
            title_bbox[2] + 10,
            title_bbox[3] + 8,
        ),
        radius=10,
        fill=(255, 255, 255, 230),
        outline=(80, 80, 80, 180),
        width=1,
    )
    draw.text((20, 20), title, fill="black", font=map_title_font)

    occupied_rects = []

    # ordena por longitude para reduzir colisões entre caixas centrais
    pixel_points = sorted(pixel_points, key=lambda p: p["lon"])

    for p in pixel_points:
        px = int(p["world_x"] - left)
        py = int(p["world_y"] - top)

        if pin_icon is not None:
            icon = pin_icon.copy()
            icon_w, icon_h = icon.size
            paste_x = px - icon_w // 2
            paste_y = py - icon_h
            final_map.alpha_composite(icon, (paste_x, paste_y))
            anchor_y = paste_y
        else:
            r = 10
            draw.ellipse(
                (px - r, py - r, px + r, py + r),
                fill="red",
                outline="white",
                width=2,
            )
            icon_h = 20
            anchor_y = py - 20

        _, _, box_w, box_h = _measure_info_box(
            draw, p, title_font, body_font
        )

        box_x, box_y, rect = _pick_box_position(
            px=px,
            anchor_y=anchor_y,
            box_w=box_w,
            box_h=box_h,
            width=width,
            height=height,
            occupied_rects=occupied_rects,
        )

        _draw_info_box(
            draw=draw,
            x=box_x,
            y=box_y,
            point=p,
            title_font=title_font,
            body_font=body_font,
        )

        occupied_rects.append(rect)

        # conector
        box_center_y = box_y + box_h // 2
        if box_x > px:
            line_end_x = box_x
        elif box_x + box_w < px:
            line_end_x = box_x + box_w
        else:
            line_end_x = px

        line_start_x = px
        line_start_y = anchor_y + 12 if pin_icon is not None else py

        draw.line(
            (line_start_x, line_start_y, line_end_x, box_center_y),
            fill=(40, 40, 40, 180),
            width=2,
        )

    final_map.convert("RGB").save(output_path, format="PNG", optimize=True)
    return temp_dir, output_path