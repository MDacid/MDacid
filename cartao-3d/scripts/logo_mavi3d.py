"""Logótipo MAVI 3D PRINT redesenhado em vetor (a partir do banner da marca).

Coordenadas de desenho em "px do banner" (Y para baixo), depois convertidas.
Cores: cobre (engrenagem, M, "3D PRINT", barra) e branco/prata (impressora,
anel, "D", "MAVI", barra). O "3" é recortado no cobre (fica a cor de fundo).
"""
import math
import os
import sys

from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geometria import rounded_rect, texto  # noqa: E402

C = (104.0, 68.0)   # centro da engrenagem
GAP = 3.0           # separação mínima entre peças (px)


def _engrenagem(n=12, r_raiz=55.0, r_ponta=63.0, r_furo=47.0):
    corpo = Point(C).buffer(r_raiz, quad_segs=48)
    dentes = []
    for k in range(n):
        a = 2 * math.pi * k / n - math.pi / 2          # um dente virado para cima
        meia_base, meia_ponta = 8.0 / r_raiz, 5.5 / r_ponta
        pts = [(C[0] + r * math.cos(a + s * m), C[1] + r * math.sin(a + s * m))
               for r, m, s in [(r_raiz - 2, meia_base, -1), (r_ponta, meia_ponta, -1),
                               (r_ponta, meia_ponta, 1), (r_raiz - 2, meia_base, 1)]]
        dentes.append(Polygon(pts))
    g = unary_union([corpo] + dentes).difference(Point(C).buffer(r_furo, quad_segs=48))
    return g


def _impressora():
    topo = box(74, 30, 156, 44).difference(box(83, 35, 147, 39.5))
    cabeca = rounded_rect(104, 25, 125, 47, 2.5)
    cabeca = cabeca.difference(box(108, 39.5, 121, 41.5))       # frisos da cabeça
    bico = Polygon([(110, 46.5), (119, 46.5), (116.5, 56), (112.5, 56)])
    # tubo de filamento (arco por cima, da cabeça ao canto do pórtico)
    arco = [(133 + 14 * math.cos(math.radians(a)), 24 - 14 * math.sin(math.radians(a))) for a in range(180, -1, -6)]
    tubo = LineString([(119, 27)] + arco + [(147, 31)]).buffer(1.7, cap_style=2, join_style=1)
    postes = [box(76, 44, 86, 94), box(146, 44, 156, 94)]
    base = box(68, 94, 161, 101)
    return unary_union([topo, cabeca, bico, tubo, base] + postes)


def _m_cobre(recorte_3=1.0):
    # bloco esquerdo inteiro + V ao centro + braço direito (a zona do "D" fica escura)
    m = Polygon([(89, 50), (99, 50), (116, 62), (133, 50), (143, 50), (143, 58.5),
                 (114, 77), (114, 92), (89, 92)])
    tres, w3 = texto("3", "ExtraBold", 11.5)
    tres = affinity.scale(tres, 1, -1, origin=(0, 0))           # Y para baixo
    tres = affinity.translate(tres, 101 - w3 / 2, 88.5)
    return m.difference(tres.buffer(recorte_3))   # 1.0 = largo, para se ver na impressão 3D


def _d_branco():
    d, wd = texto("D", "Bold", 10.5)
    d = affinity.scale(d, 1, -1, origin=(0, 0))
    return affinity.translate(d, 131 - wd / 2, 88)


def _texto_centrado(s, peso, cap, x0, x1, y_base):
    """Texto com altura de maiúsculas `cap` exata; a largura x0..x1 é atingida
    ajustando o espaçamento entre letras (como no logótipo original)."""
    t, w0 = texto(s, peso, cap)
    em = cap / 0.7                      # Montserrat: maiúsculas = 0.7 em
    tracking = ((x1 - x0) - w0) / (max(1, len(s) - 1) * em)
    if tracking < 0:                    # não cabe: reduz a altura
        k = (x1 - x0) / w0
        t, w = texto(s, peso, cap * k)
    else:
        t, w = texto(s, peso, cap, tracking=tracking)
    t = affinity.scale(t, 1, -1, origin=(0, 0))
    return affinity.translate(t, x0, y_base), cap


def desenhar(recorte_3=1.0):
    """Devolve (branco, cobre) em px do banner, Y para baixo.
    recorte_3: folga à volta do "3" escuro (1.0 para impressão 3D, menor para papel)."""
    impressora = _impressora()
    sep = impressora.buffer(GAP, join_style=2)
    eng = _engrenagem().difference(sep)
    eng = eng.difference(box(140, 27, 200, 99))                # engrenagem aberta à direita (como no original)
    anel = Point(C).buffer(44, quad_segs=48).difference(Point(C).buffer(38, quad_segs=48))
    anel = anel.difference(box(68, 25, 161, 101).buffer(1.5, join_style=2))  # só por fora da impressora
    m = _m_cobre(recorte_3).difference(sep)
    d = _d_branco()

    mavi, cap_mavi = _texto_centrado("MAVI", "Black", 34, 26, 182, 166)
    tdp, _ = _texto_centrado("3D PRINT", "ExtraBold", 18, 22, 187, 190)
    barra_c = Polygon([(21, 196), (130, 196), (124, 204), (21, 204)])
    barra_b = Polygon([(134, 196), (186, 196), (186, 204), (128, 204)])

    branco = unary_union([impressora, anel, d, mavi, barra_b])
    cobre = unary_union([eng, m, tdp, barra_c])
    return branco, cobre


def em_mm(geo, altura_mm, x_centro, y_topo):
    """px do banner -> mm do cartão (Y para cima), escala pela altura total do logótipo."""
    y0, y1 = 6.0, 204.0
    s = altura_mm / (y1 - y0)
    g = affinity.translate(geo, -104.0, -y0)
    g = affinity.scale(g, s, -s, origin=(0, 0))
    return affinity.translate(g, x_centro, y_topo)


LARGURA_RELATIVA = (186.0 - 21.0) / (204.0 - 6.0)   # largura / altura do logótipo


def svg(caminho, px_por_unidade=4.0):
    """SVG com efeito metálico (prata e cobre em gradiente), fundo transparente."""
    branco, cobre = desenhar(recorte_3=0.35)

    def path(g):
        from geometria import as_polys
        d = []
        for p in as_polys(g):
            for ring in [p.exterior, *p.interiors]:
                pts = list(ring.coords)
                d.append("M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in pts) + "Z")
        return " ".join(d)

    x0, y0, x1, y1 = 18, 4, 190, 207
    out = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} {y0} {x1 - x0} {y1 - y0}" width="{(x1 - x0) * px_por_unidade:.0f}" height="{(y1 - y0) * px_por_unidade:.0f}">
<defs>
 <linearGradient id="cobre" x1="0" y1="0" x2="0.35" y2="1">
  <stop offset="0" stop-color="#F0A672"/><stop offset="0.45" stop-color="#C47A45"/><stop offset="1" stop-color="#8E4E26"/>
 </linearGradient>
 <linearGradient id="prata" x1="0" y1="0" x2="0.2" y2="1">
  <stop offset="0" stop-color="#FFFFFF"/><stop offset="0.55" stop-color="#E4E6E9"/><stop offset="1" stop-color="#A9ADB3"/>
 </linearGradient>
 <filter id="sombra" x="-10%" y="-10%" width="120%" height="120%">
  <feDropShadow dx="0" dy="0.8" stdDeviation="0.9" flood-color="#000" flood-opacity="0.55"/>
 </filter>
</defs>
<g filter="url(#sombra)" fill-rule="evenodd">
 <path fill="url(#cobre)" d="{path(cobre)}"/>
 <path fill="url(#prata)" d="{path(branco)}"/>
</g>
</svg>
'''
    open(caminho, "w").write(out)


if __name__ == "__main__":
    from PIL import Image, ImageDraw
    from geometria import as_polys
    branco, cobre = desenhar()
    k = 5
    im = Image.new("RGB", (210 * k, 220 * k), (38, 42, 48))
    d = ImageDraw.Draw(im)
    for geo, cor in ((cobre, (196, 122, 69)), (branco, (235, 236, 238))):
        for p in as_polys(geo):
            m = Image.new("L", im.size, 0)
            md = ImageDraw.Draw(m)
            md.polygon([((x - 0) * k, (y - 0) * k) for x, y in p.exterior.coords], fill=255)
            for i in p.interiors:
                md.polygon([(x * k, y * k) for x, y in i.coords], fill=0)
            im.paste(cor, mask=m)
    saida = sys.argv[1] if len(sys.argv) > 1 else "logo_mavi3d_teste.png"
    im.save(saida)
    print(saida)
