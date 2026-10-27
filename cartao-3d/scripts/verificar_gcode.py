"""Verifica um G-code: cor (ferramenta) por camada e simulação visual das trajetórias reais.

Uso: python3 scripts/verificar_gcode.py ficheiro.gcode [saida.png]
"""
import re
import sys
from collections import defaultdict

from PIL import Image, ImageDraw

COR = {0: (27, 28, 31), 1: (196, 122, 69), 2: (245, 245, 245)}


def ler(path):
    tool, z, x, y, w = None, 0.0, 0.0, 0.0, 0.42
    por_camada = defaultdict(lambda: defaultdict(float))
    segs = []
    for ln in open(path, encoding="utf-8"):
        if ln.startswith(";Z:"):
            z = round(float(ln[3:]), 2)
            continue
        if ln.startswith(";WIDTH:"):
            w = float(ln[7:])
            continue
        c = ln.split(";")[0].strip()
        m = re.fullmatch(r"T(\d)", c)
        if m:
            tool = int(m.group(1))
            continue
        if c.startswith(("G0 ", "G1 ")):
            d = dict(re.findall(r"([XYZEF])(-?[\d.]+)", c))
            nx, ny = float(d.get("X", x)), float(d.get("Y", y))
            e = float(d.get("E", 0))
            if e > 0 and ("X" in d or "Y" in d) and z > 0:
                por_camada[z][tool] += e
                segs.append((tool, z, x, y, nx, ny, w))
            x, y = nx, ny
    return por_camada, segs


def simular(segs, saida, ppm=20, margem=2.0):
    xs = [s[2] for s in segs] + [s[4] for s in segs]
    ys = [s[3] for s in segs] + [s[5] for s in segs]
    x0, x1, y0, y1 = min(xs) - margem, max(xs) + margem, min(ys) - margem, max(ys) + margem
    im = Image.new("RGB", (int((x1 - x0) * ppm), int((y1 - y0) * ppm)), (232, 232, 228))
    d = ImageDraw.Draw(im)
    for t, z, ax, ay, bx, by, w in sorted(segs, key=lambda s: s[1]):
        p = [((ax - x0) * ppm, (y1 - ay) * ppm), ((bx - x0) * ppm, (y1 - by) * ppm)]
        c = COR.get(t, (255, 0, 0))
        d.line(p, fill=c, width=max(1, int(w * ppm)))
        r = w * ppm / 2
        for px, py in p:
            d.ellipse((px - r, py - r, px + r, py + r), fill=c)
    im.save(saida)


if __name__ == "__main__":
    camadas, segs = ler(sys.argv[1])
    for z in sorted(camadas):
        print(f"  z={z:4.2f}  " + "  ".join(f"T{t}: {v:8.1f} mm" for t, v in sorted(camadas[z].items())))
    if len(sys.argv) > 2:
        # só o cartão (ignora a linha de purga do início, que está fora dele)
        segs = [s for s in segs if s[1] > 0.2 or (s[0] == 0 and abs(s[2] - s[4]) < 60 and abs(s[3] - s[5]) < 60)]
        xs = sorted(s[2] for s in segs if s[1] >= 0.4)
        segs = [s for s in segs if s[1] >= 0.4 or (min(xs) - 1 <= s[2] <= max(xs) + 1)]
        simular([s for s in segs if s[1] >= 0.4], sys.argv[2])
