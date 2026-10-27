"""Gera as versões do logótipo MAVISKY usadas no cartão de visita.

- logo-circular.png  : logótipo completo (com anel), fundo fundido com a cor do cartão
- logo-empilhado.png : drone-M + MAVISKY + tagline, sem o anel
- topografia.svg     : padrão de curvas de nível (decorativo)

Uso: python3 scripts/preparar_assets.py   (a partir da pasta cartao-visita)
"""
import math
import random
from PIL import Image, ImageChops, ImageDraw, ImageFilter

BG = (21, 23, 26)  # #15171A — antracite da paleta
SRC = "assets/logo-mavisky-original.jpg"


def radial_mask(size, center, r_full, r_zero, scale=4):
    """Máscara radial suave: 255 até r_full, 0 a partir de r_zero."""
    w, h = size
    m = Image.new("L", (w // scale, h // scale), 0)
    px = m.load()
    cx, cy = center[0] / scale, center[1] / scale
    for y in range(m.height):
        for x in range(m.width):
            d = math.hypot(x - cx, y - cy) * scale
            t = (r_zero - d) / (r_zero - r_full)
            px[x, y] = int(255 * max(0.0, min(1.0, t)))
    return m.resize(size, Image.BICUBIC)


img = Image.open(SRC).convert("RGB")
bg = Image.new("RGB", img.size, BG)
lit = ImageChops.lighter(img, bg)  # preto do original passa a ser a cor do cartão

# 1) Logótipo circular completo, com bordo transparente suave
circ = lit.copy()
circ.putalpha(radial_mask(img.size, (627, 627), 612, 627))
circ.save("assets/logo-circular.png", optimize=True)

# 2) Logótipo empilhado sem o anel (anel ~r590, hélices até ~r561)
mask = radial_mask(img.size, (627, 627), 563, 576)
# metade de baixo: só há texto (até ~r530), corta mais cedo o brilho do anel
low = radial_mask(img.size, (627, 627), 536, 550)
band = Image.new("L", img.size, 0)
ImageDraw.Draw(band).rectangle((0, 640, img.width, img.height), fill=255)
band = band.filter(ImageFilter.GaussianBlur(20))
mask = Image.composite(ImageChops.darker(mask, low), mask, band)
stack = Image.composite(lit, bg, mask).crop((110, 290, 1145, 915))
stack.save("assets/logo-empilhado.png", optimize=True)

# 3) Curvas de nível
random.seed(7)


def blob(cx, cy, r, phase, amp):
    pts = []
    for i in range(96):
        a = 2 * math.pi * i / 96
        rr = r * (1 + amp * (0.55 * math.sin(3 * a + phase) + 0.3 * math.sin(5 * a - 2 * phase) + 0.15 * math.sin(2 * a + 1.3)))
        pts.append((cx + rr * math.cos(a), cy + rr * 0.72 * math.sin(a)))
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"
    return d


paths = []
for (cx, cy, n, r0, step, ph) in [(820, 520, 14, 18, 22, 0.4), (60, 40, 9, 20, 24, 2.1)]:
    for k in range(n):
        paths.append(blob(cx, cy, r0 + k * step, ph + k * 0.09, 0.10 + 0.012 * k))
svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 910 610" preserveAspectRatio="xMidYMid slice">',
       '<g fill="none" stroke="#C47A45" stroke-width="1.1">']
svg += [f'<path d="{d}"/>' for d in paths]
svg += ["</g></svg>"]
open("assets/topografia.svg", "w").write("\n".join(svg))
print("ok")
