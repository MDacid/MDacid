"""Geometria 2D do cartão MAVISKY para impressão 3D em 3 cores.

Tudo em milímetros, origem no canto inferior esquerdo do cartão, Y para cima.
Devolve três conjuntos de polígonos (shapely):
  base   -> cartão (preto)
  cobre  -> elementos cobre/laranja
  branco -> elementos brancos

O M e o lettering MAVISKY são traçados a partir do logótipo original;
as partes do drone (hélices, motores, braços, lente) são redesenhadas em
vetor, porque no logótipo são um render fotorrealista sem contornos limpos.
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from scipy import ndimage
from shapely import affinity
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
from shapely.ops import unary_union
from skimage import measure

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
LOGO = os.path.join(RAIZ, "..", "cartao-visita", "assets", "logo-mavisky-original.jpg")
FONTES = os.path.join(RAIZ, "fontes")

# ---------------------------------------------------------------- formato
CARD_W, CARD_H, CARD_R = 85.0, 55.0, 3.0
MIN_TRACO = 0.42  # largura mínima de traço (bico 0.4 mm)
LARG_LOGO = 36.0  # largura do bloco do logótipo (mm)
CAP_TAG = 2.3     # altura das maiúsculas da tagline (mm)
CAP_FUNCAO = 2.2

# Recorte do logótipo (px do original) onde está o logo empilhado sem o anel
CROP_X0, CROP_Y0 = 110, 290


# ================================================================ utilitários
def rounded_rect(x0, y0, x1, y1, r):
    return box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, quad_segs=16) if r > 0 else box(x0, y0, x1, y1)


def ellipse(cx, cy, a, b, n=180):
    return Polygon([(cx + a * math.cos(2 * math.pi * i / n), cy + b * math.sin(2 * math.pi * i / n)) for i in range(n)])


def as_polys(g):
    if g.is_empty:
        return []
    if isinstance(g, Polygon):
        return [g]
    return [p for p in getattr(g, "geoms", []) if isinstance(p, Polygon) and not p.is_empty]


def engrossar(g, d):
    """Engrossa uniformemente (d mm para cada lado) — usado no texto pequeno."""
    return g.buffer(d, quad_segs=8, join_style=1)


def tracos_finos(g, minimo=MIN_TRACO):
    """Área (mm2) de partes mais finas que `minimo` — só para verificação."""
    r = minimo / 2
    aberto = g.buffer(-r, quad_segs=8).buffer(r, quad_segs=8)
    fino = g.difference(aberto).buffer(-0.04).buffer(0.04)
    return sum(p.area for p in as_polys(fino) if p.area > 0.01)


# ================================================================ logótipo raster
def _mascaras():
    im = np.asarray(Image.open(LOGO).convert("RGB")).astype(float) / 255
    im = im[CROP_Y0:CROP_Y0 + 625, CROP_X0:CROP_X0 + 1035]
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    mx, mn = im.max(-1), im.min(-1)
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    d = np.maximum(mx - mn, 1e-6)
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    branco = (mx > 0.55) & (s < 0.22)
    cobre = (h > 8) & (h < 42) & (s > 0.45) & (mx > 0.30)
    return branco, cobre


def _limpar(mask, area_min=400):
    lab, n = ndimage.label(mask)
    if n == 0:
        return mask
    areas = ndimage.sum(mask, lab, range(1, n + 1))
    keep = np.isin(lab, [i + 1 for i, a in enumerate(areas) if a >= area_min])
    return keep


def _tracar(mask, x_rect, y_rect):
    """Contornos sub-pixel de uma máscara numa janela (coords do recorte)."""
    x0, x1 = x_rect
    y0, y1 = y_rect
    m = np.zeros_like(mask)
    m[y0:y1, x0:x1] = mask[y0:y1, x0:x1]
    m = _limpar(m)
    f = ndimage.gaussian_filter(np.pad(m.astype(float), 4), 1.1)
    geo = Polygon()
    for c in measure.find_contours(f, 0.5):
        if len(c) < 8:
            continue
        p = Polygon([(cc - 4, rr - 4) for rr, cc in c]).buffer(0)
        geo = geo.symmetric_difference(p)
    return geo.simplify(0.35)


# ================================================================ drone vetorial (px do recorte, Y para baixo)
def _drone_cobre(eixo):
    """Hélices, motores, braços e lente (lado esquerdo + espelho)."""
    esq = []
    # hélice: anel elíptico
    helice = ellipse(205, 52, 178, 27)
    esq.append(helice.difference(helice.buffer(-14, quad_segs=16)))  # anel de 0.54 mm
    # cubo, veio e campânula do motor
    esq.append(rounded_rect(198, 25, 238, 42, 5))
    esq.append(box(211, 40, 225, 70))
    esq.append(rounded_rect(180, 66, 258, 94, 6))
    # corpo do motor: contorno (preto por dentro)
    esq.append(rounded_rect(166, 106, 260, 160, 10))
    # braços até à perna do M
    esq.append(LineString([(214, 160), (285, 192), (352, 226)]).buffer(9, cap_style=2, join_style=1))
    esq.append(LineString([(252, 100), (300, 142), (352, 196)]).buffer(7, cap_style=2, join_style=1))
    lado = unary_union(esq)
    espelho = affinity.scale(lado, xfact=-1, origin=(eixo, 0))
    # lente
    lente = unary_union([
        Point(514, 297).buffer(58, quad_segs=32).difference(Point(514, 297).buffer(46, quad_segs=32)),
        Point(514, 297).buffer(24, quad_segs=32),
    ])
    return unary_union([lado, espelho, lente])


def _drone_branco():
    return Point(519, 290).buffer(7.5, quad_segs=16)  # brilho na lente


# ================================================================ texto
class _FlatPen(BasePen):
    def __init__(self, glyphset, passos=10):
        super().__init__(glyphset)
        self.contornos, self.atual, self.passos = [], [], passos

    def _moveTo(self, p):
        self.atual = [p]

    def _lineTo(self, p):
        self.atual.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self.atual[-1]
        for i in range(1, self.passos + 1):
            t = i / self.passos
            u = 1 - t
            self.atual.append((u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
                               u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1]))

    def _qCurveToOne(self, p1, p2):
        p0 = self.atual[-1]
        for i in range(1, self.passos + 1):
            t = i / self.passos
            u = 1 - t
            self.atual.append((u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
                               u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]))

    def _closePath(self):
        if len(self.atual) > 2:
            self.contornos.append(self.atual)
        self.atual = []

    _endPath = _closePath


_FONT_CACHE = {}


def _font(peso):
    if peso not in _FONT_CACHE:
        _FONT_CACHE[peso] = TTFont(os.path.join(FONTES, f"Montserrat-{peso}.ttf"))
    return _FONT_CACHE[peso]


PESO_ESPECIAL = {"@": "Black"}  # o @ da Montserrat tem traços muito finos
# glifos com braços curtos que o fatiador perde com bico 0.4: engrossar (mm por lado)
ENGROSSAR_GLIFO = {"t": 0.08, "+": 0.09, "f": 0.05}


def texto(s, peso, altura_maiusc, tracking=0.0):
    """Texto -> polígonos, origem na linha de base à esquerda. altura em mm (altura das maiúsculas)."""
    f = _font(peso)
    upm = f["head"].unitsPerEm
    cap = f["OS/2"].sCapHeight or 700
    esc = altura_maiusc / cap
    x, partes = 0.0, []
    for ch in s:
        fc = _font(PESO_ESPECIAL.get(ch, peso))
        cmap, gs, hmtx = fc.getBestCmap(), fc.getGlyphSet(), fc["hmtx"]
        gname = cmap.get(ord(ch))
        if gname is None:
            gname = cmap.get(ord("?"))
        pen = _FlatPen(gs)
        gs[gname].draw(pen)
        g = Polygon()
        for c in pen.contornos:
            g = g.symmetric_difference(Polygon(c).buffer(0))
        if ch in ENGROSSAR_GLIFO and not g.is_empty:
            g = g.buffer(ENGROSSAR_GLIFO[ch] / esc, join_style=2)
        if not g.is_empty:
            partes.append(affinity.translate(g, x, 0))
        x += hmtx[gname][0] + tracking * upm
    x -= tracking * upm
    geo = affinity.scale(unary_union(partes), esc, esc, origin=(0, 0))
    return geo, x * esc


def colocar(geo, x, y, alinhar="esq", largura=None):
    if alinhar == "centro":
        x -= largura / 2
    return affinity.translate(geo, x, y)


# ================================================================ ícones de contacto (centrados em 0,0)
def _icone(nome, t=3.4):
    w = 0.48
    h = t / 2
    if nome == "telefone":
        ext = rounded_rect(-1.15, -h, 1.15, h, 0.45)
        g = ext.difference(rounded_rect(-1.15 + w, -h + 0.85, 1.15 - w, h - w, 0.1))
        return g  # a parte de baixo, sólida, faz de botão
    if nome == "email":
        ext = rounded_rect(-h, -1.15, h, 1.15, 0.3)
        g = ext.difference(ext.buffer(-w))
        v = LineString([(-h + 0.25, 1.0), (0, -0.05), (h - 0.25, 1.0)]).buffer(w / 2, join_style=1)
        return g.union(v).intersection(ext)
    if nome == "site":
        c = Point(0, 0).buffer(h, quad_segs=32)
        g = c.difference(c.buffer(-w))
        g = g.union(box(-h, -w / 2, h, w / 2))
        mer = ellipse(0, 0, 0.62, h)
        g = g.union(mer.difference(mer.buffer(-0.46)))
        return g.intersection(c)
    if nome == "instagram":
        ext = rounded_rect(-h, -h, h, h, 0.95)
        g = ext.difference(ext.buffer(-w))
        anel = Point(0, 0).buffer(0.80, quad_segs=32)
        return g.union(anel.difference(anel.buffer(-0.46)))
    raise ValueError(nome)


# ================================================================ cartão completo
def _ajustar(geo, largura, larg_max, nome):
    """Encolhe para caber; avisa se o texto ficar abaixo do mínimo imprimível."""
    k = min(1.0, larg_max / largura)
    if k < 0.97:
        print(f"  aviso: '{nome}' encolhido para {k:.0%} para caber — encurte o texto", file=sys.stderr)
    return affinity.scale(geo, k, k, origin=(0, 0)), k


def construir(dados_path=os.path.join(RAIZ, "dados.json")):
    """Layout do cartão. Regras de texto para bico 0.4 mm:
    Montserrat Bold, maiúsculas >= 2.2 mm -> hastes ~0.49 mm e vãos ~0.44 mm."""
    dados = json.load(open(dados_path, encoding="utf-8"))
    branco_m, cobre_m = _mascaras()

    # zona útil acima do rodapé
    Y_RODAPE = 4.6           # linha de base da tagline
    Y0, Y1 = 10.0, CARD_H - 4.0
    YC = (Y0 + Y1) / 2

    # --- logótipo (px do recorte) -----------------------------------------
    m_letra = _tracar(branco_m, (320, 720), (95, 395))
    minx, _, maxx, _ = m_letra.bounds
    eixo = (minx + maxx) / 2
    mavi = _tracar(branco_m, (0, 568), (400, 545))
    sky = _tracar(cobre_m, (568, 1035), (400, 545))
    logo_b = unary_union([m_letra, mavi, _drone_branco()])
    logo_c = unary_union([sky, _drone_cobre(eixo)]).difference(m_letra)  # M por cima dos braços

    bx0, by0, bx1, by1 = unary_union([logo_b, logo_c]).bounds
    s = LARG_LOGO / (bx1 - bx0)
    X_LOGO = 4.0 + LARG_LOGO / 2
    topo = YC + (by1 - by0) * s / 2

    def px2mm(g):
        g = affinity.translate(g, -(bx0 + bx1) / 2, -by0)
        g = affinity.scale(g, s, -s, origin=(0, 0))
        return affinity.translate(g, X_LOGO, topo)

    branco = [px2mm(logo_b)]
    cobre = [px2mm(logo_c)]

    # --- rodapé: tagline em toda a largura -------------------------------
    tag, tag_w = texto(dados["tagline"], "Bold", CAP_TAG, tracking=0.16)
    tag, k = _ajustar(tag, tag_w, CARD_W - 8.0, "tagline")
    branco.append(colocar(tag, CARD_W / 2, Y_RODAPE, "centro", tag_w * k))

    # --- divisória ----------------------------------------------------------
    X_DIV = 4.0 + LARG_LOGO + 3.0
    cobre.append(LineString([(X_DIV, Y0 + 2.0), (X_DIV, Y1 - 2.0)]).buffer(0.32, cap_style=1))

    # --- bloco de contactos -------------------------------------------------
    X_TXT = X_DIV + 2.8
    larg_max = CARD_W - 3.4 - X_TXT
    CAP_NOME, CAP_C, ICON, GAP_I, PASSO = 3.0, 2.2, 3.3, 1.1, 5.0
    linhas = [("telefone", dados["telefone"]), ("email", dados["email"]),
              ("site", dados["site"]), ("instagram", dados["instagram"])]
    altura = CAP_NOME + 2.3 + CAP_FUNCAO + 4.4 + (len(linhas) - 1) * PASSO + ICON / 2
    y = YC + altura / 2 - CAP_NOME
    nome, w = texto(dados["nome"], "Bold", CAP_NOME, tracking=0.01)
    nome, _ = _ajustar(nome, w, larg_max, "nome")
    branco.append(colocar(nome, X_TXT, y))
    y -= 2.3 + CAP_FUNCAO
    funcao, w = texto(dados["funcao"].replace("·", "•"), "Bold", CAP_FUNCAO, tracking=0.08)
    funcao, _ = _ajustar(funcao, w, larg_max, "funcao")
    cobre.append(colocar(funcao, X_TXT, y))
    y -= 4.4 + ICON / 2 - CAP_FUNCAO / 2
    for ic, txt in linhas:
        cobre.append(affinity.translate(_icone(ic, ICON), X_TXT + ICON / 2, y))
        t, w = texto(txt, "Bold", CAP_C, tracking=0.02)
        t, k = _ajustar(t, w, larg_max - ICON - GAP_I, ic)
        branco.append(colocar(t, X_TXT + ICON + GAP_I, y - CAP_C * k / 2))
        y -= PASSO

    base = rounded_rect(0, 0, CARD_W, CARD_H, CARD_R)
    branco = unary_union(branco).intersection(base.buffer(-1.0))
    cobre = unary_union(cobre).intersection(base.buffer(-1.0))
    return {"base": base, "cobre": cobre, "branco": branco, "dados": dados}


if __name__ == "__main__":
    g = construir()
    for k in ("base", "cobre", "branco"):
        print(k, round(g[k].area, 1), "mm2", len(as_polys(g[k])), "polígonos",
              "| finos <0.42mm:", round(tracos_finos(g[k]), 2), "mm2")
