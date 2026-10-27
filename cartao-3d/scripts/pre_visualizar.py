"""Imagem de pré-visualização (vista de cima) do cartão 3D."""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geometria import CARD_H, CARD_W, as_polys, construir  # noqa: E402

CORES = {"base": (24, 25, 28), "cobre": (196, 122, 69), "branco": (240, 240, 240)}


def render(g, saida, ppm=24):
    W, H = int(CARD_W * ppm), int(CARD_H * ppm)
    pad = int(3 * ppm)
    im = Image.new("RGB", (W + 2 * pad, H + 2 * pad), (232, 232, 228))

    def xy(pts):
        return [(pad + x * ppm, pad + (CARD_H - y) * ppm) for x, y in pts]

    camadas = [("base", g["base"]), ("cobre", g["cobre"].union(g["branco"])), ("branco", g["branco"])]
    cor_sub = {"base": CORES["base"], "cobre": CORES["cobre"], "branco": CORES["branco"]}
    for nome, geo in camadas:
        for p in as_polys(geo):  # cada polígono numa máscara própria (buracos corretos)
            m = Image.new("L", im.size, 0)
            md = ImageDraw.Draw(m)
            md.polygon(xy(p.exterior.coords), fill=255)
            for i in p.interiors:
                md.polygon(xy(i.coords), fill=0)
            im.paste(cor_sub[nome], mask=m)
    im.save(saida)


def render_recortado(g, saida, ppm=12):
    """Só o cartão, fundo transparente (usado nas miniaturas do G-code)."""
    render(g, saida, ppm)
    im = Image.open(saida).convert("RGBA")
    pad = int(3 * ppm)
    im = im.crop((pad, pad, im.width - pad, im.height - pad))
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=int(3 * ppm), fill=255)
    im.putalpha(m)
    im.save(saida)


if __name__ == "__main__":
    pasta = sys.argv[1] if len(sys.argv) > 1 else "previews"
    os.makedirs(pasta, exist_ok=True)
    g = construir()
    render(g, os.path.join(pasta, "vista-topo.png"))
    render_recortado(g, os.path.join(pasta, "vista-topo-recortada.png"))
    print(pasta)
