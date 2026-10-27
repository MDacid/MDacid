"""Exporta o cartão 3D: STEP (Fusion 360), STL por cor, DXF por camada.

Camadas (uma só cor por camada => apenas 2 trocas de filamento por impressão):
  z 0.0 – 0.6  base preta (cartão inteiro)
  z 0.6 – 1.0  cobre: elementos cobre + por baixo dos brancos
  z 1.0 – 1.4  branco: elementos brancos
"""
import math
import os
import sys

import cadquery as cq
import ezdxf
import trimesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geometria import RAIZ, as_polys, construir  # noqa: E402

Z_BASE, Z_COBRE, Z_BRANCO = 0.6, 1.0, 1.4

CORPOS = [  # nome, filamento (slot da Box), cor RGB, z0, z1
    ("1-base-preto", 1, (0.08, 0.09, 0.10), 0.0, Z_BASE),
    ("2-cobre", 2, (0.77, 0.48, 0.27), Z_BASE, Z_COBRE),
    ("3-branco", 3, (0.96, 0.96, 0.96), Z_COBRE, Z_BRANCO),
]


def pegadas(g):
    """Pegada 2D de cada corpo."""
    return {
        "1-base-preto": g["base"],
        "2-cobre": g["cobre"].union(g["branco"]).simplify(0.02).buffer(0),
        "3-branco": g["branco"].simplify(0.02).buffer(0),
    }


def _desvio(pts):
    """Distância máxima dos pontos à corda primeiro-último."""
    import numpy as np
    a, b = np.array(pts[0]), np.array(pts[-1])
    ab = b - a
    n = np.linalg.norm(ab)
    if n < 1e-9:
        return 1e9
    return max(abs(ab[0] * (p[1] - a[1]) - ab[1] * (p[0] - a[0])) / n for p in pts)


def _wire(coords, z, canto_graus=35.0):
    """Contorno -> wire com retas e splines (quebra nos cantos vivos)."""
    import numpy as np
    pts = [tuple(c) for c in list(coords)[:-1]]
    n = len(pts)
    P = np.array(pts)
    v1 = P - np.roll(P, 1, axis=0)
    v2 = np.roll(P, -1, axis=0) - P
    cosang = (v1 * v2).sum(1) / (np.linalg.norm(v1, axis=1) * np.linalg.norm(v2, axis=1) + 1e-12)
    cantos = [i for i in range(n) if cosang[i] < math.cos(math.radians(canto_graus))]
    V = lambda p: cq.Vector(p[0], p[1], z)  # noqa: E731
    try:
        if not cantos:
            return cq.Wire.assembleEdges([cq.Edge.makeSpline([V(p) for p in pts], periodic=True)])
        edges = []
        for k, i in enumerate(cantos):
            j = cantos[(k + 1) % len(cantos)]
            run = [pts[(i + t) % n] for t in range(((j - i) % n or n) + 1)]
            if len(run) == 2 or _desvio(run) < 0.004:
                edges.append(cq.Edge.makeLine(V(run[0]), V(run[-1])))
            else:
                edges.append(cq.Edge.makeSpline([V(p) for p in run]))
        return cq.Wire.assembleEdges(edges)
    except Exception:
        return cq.Wire.makePolygon([V(p) for p in pts], close=True)


def solido(geo, z0, z1):
    solids = []
    for p in as_polys(geo):
        face = cq.Face.makeFromWires(_wire(p.exterior.coords, z0), [_wire(i.coords, z0) for i in p.interiors])
        sol = cq.Solid.extrudeLinear(face, cq.Vector(0, 0, z1 - z0))
        if not sol.isValid() or abs(sol.Volume() - p.area * (z1 - z0)) > 0.02 * p.area * (z1 - z0) + 0.01:
            # recurso: polígono simples se a curva não ficou fiel
            face = cq.Face.makeFromWires(cq.Wire.makePolygon([cq.Vector(x, y, z0) for x, y in list(p.exterior.coords)[:-1]], close=True),
                                         [cq.Wire.makePolygon([cq.Vector(x, y, z0) for x, y in list(i.coords)[:-1]], close=True) for i in p.interiors])
            sol = cq.Solid.extrudeLinear(face, cq.Vector(0, 0, z1 - z0))
        solids.append(sol)
    return cq.Compound.makeCompound(solids)


def malha(solid, caminho):
    cq.exporters.export(solid, caminho, tolerance=0.01, angularTolerance=0.25)
    return trimesh.load(caminho)


def exportar(g, pasta=RAIZ):
    peg = pegadas(g)
    os.makedirs(os.path.join(pasta, "fusion360"), exist_ok=True)
    os.makedirs(os.path.join(pasta, "stl"), exist_ok=True)

    # STEP: montagem com 3 corpos coloridos
    assy = cq.Assembly(name="cartao_mavisky_3cores")
    solidos = {}
    for nome, _, cor, z0, z1 in CORPOS:
        solidos[nome] = solido(peg[nome], z0, z1)
        assy.add(solidos[nome], name=nome.replace("-", "_"), color=cq.Color(*cor))
    step = os.path.join(pasta, "fusion360", "cartao-mavisky-3cores.step")
    assy.export(step)

    # STL por cor (também servem para o QIDI Studio)
    malhas = {}
    for nome, *_ in CORPOS:
        malhas[nome] = malha(solidos[nome], os.path.join(pasta, "stl", f"cartao-mavisky-{nome}.stl"))

    # DXF: uma camada por cor (esboço editável no Fusion)
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    cores_aci = {"1-base-preto": 250, "2-cobre": 30, "3-branco": 7}
    for nome, *_ in CORPOS:
        layer = nome.upper().replace("-", "_")
        doc.layers.add(layer, color=cores_aci[nome])
        for p in as_polys(peg[nome]):
            for ring in [p.exterior, *p.interiors]:
                doc.modelspace().add_lwpolyline(list(ring.coords)[:-1], close=True, dxfattribs={"layer": layer})
    doc.saveas(os.path.join(pasta, "fusion360", "cartao-mavisky-camadas.dxf"))
    return malhas


if __name__ == "__main__":
    g = construir()
    malhas = exportar(g)
    for n, m in malhas.items():
        partes = m.split(only_watertight=False)
        maus = [p for p in partes if not p.is_watertight]
        print(n, "volume mm3:", round(m.volume, 1), "| peças:", len(partes), "não estanques:", len(maus))
