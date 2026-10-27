"""Consumo real por filamento (inclui purgas da troca) e tempo, a partir do G-code final."""
import re
import sys

DENS, AREA = 1.24, 3.14159265 * 0.875 ** 2


def stats(path):
    tool, e = 0, [0.0, 0.0, 0.0]
    tempo = None
    for ln in open(path, encoding="utf-8"):
        if ln.startswith("; estimated printing time (normal mode)"):
            tempo = ln.split("=")[1].strip()
        c = ln.split(";")[0].strip()
        m = re.fullmatch(r"T(\d)", c)
        if m:
            tool = int(m.group(1))
            continue
        if c.startswith(("G1 ", "G0 ")):
            d = re.search(r"E(-?[\d.]+)", c)
            if d:
                e[tool] += float(d.group(1))
    g = [v * AREA * DENS / 1000 for v in e]
    return g, tempo


if __name__ == "__main__":
    for p in sys.argv[1:]:
        g, t = stats(p)
        print(f"{p}: preto {g[0]:.2f} g | cobre {g[1]:.2f} g | branco {g[2]:.2f} g | total {sum(g):.2f} g | tempo (sem trocas) {t}")
