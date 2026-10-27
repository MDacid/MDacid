"""Fatia o cartão para a QIDI Plus 4 + QIDI Box (PrusaSlicer + G-code oficial QIDI).

1. Monta um 3MF (formato PrusaSlicer) com o cartão como um objeto de 3 partes:
   base -> filamento 1 (preto), cobre -> 2, branco -> 3.
2. Fatia com slicer/qidi-plus4-box-3cores.ini.
3. Substitui cada marcador "; MAVI_TOOLCHANGE a b z" pelo G-code de troca de
   filamento do perfil oficial "X-Plus 4 0.4 nozzle" do QIDI Studio, com os
   valores que o QIDI Studio calcularia (temperaturas, caudal, purgas).

Uso: python3 scripts/fatiar.py
"""
import os
import re
import subprocess
import sys
import zipfile

import trimesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geometria import CARD_H, CARD_W, RAIZ  # noqa: E402

INI = os.path.join(RAIZ, "slicer", "qidi-plus4-box-3cores.ini")
STL = os.path.join(RAIZ, "stl")
PARTES = [("base preto", "cartao-mavisky-1-base-preto.stl", 1),
          ("cobre", "cartao-mavisky-2-cobre.stl", 2),
          ("branco", "cartao-mavisky-3-branco.stl", 3)]

BED = 305.0
# Volumes de purga (mm3) por troca [de][para], índices 0..2 = preto, cobre, branco.
# Baixos de propósito: a 1.ª camada de cada cor nova fica tapada pela seguinte,
# por isso um resto da cor anterior não se vê.
PURGA = {(0, 1): 180.0, (1, 2): 260.0, (0, 2): 450.0, (1, 0): 120.0, (2, 0): 120.0, (2, 1): 150.0}
FIL_AREA = 3.14159265 * (1.75 / 2) ** 2
MAX_VOL_SPEED = 18.0
TEMP_RANGE_HIGH = 240
TEMP_PRINT = 210
RETRACT_TOOLCHANGE = 2.0
MAX_PRINT_HEIGHT = 280.0


# ------------------------------------------------------------------ 3MF PrusaSlicer
def _mesh_xml(m):
    v = "".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in m.vertices)
    t = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in m.faces)
    return v, t


def montar_3mf(caminho, posicoes):
    malhas = []
    for nome, f, ext in PARTES:
        m = trimesh.load(os.path.join(STL, f))
        m.apply_translation((-CARD_W / 2, -CARD_H / 2, 0))  # objeto centrado na origem
        malhas.append((nome, m, ext))
    verts, tris, vols, off, tri_off = [], [], [], 0, 0
    for nome, m, ext in malhas:
        v, _ = _mesh_xml(m)
        verts.append(v)
        tris.append("".join(f'<triangle v1="{a + off}" v2="{b + off}" v3="{c + off}"/>' for a, b, c in m.faces))
        vols.append((nome, ext, tri_off, tri_off + len(m.faces) - 1))
        off += len(m.vertices)
        tri_off += len(m.faces)
    items = "".join(f'<item objectid="1" transform="1 0 0 0 1 0 0 0 1 {x:.3f} {y:.3f} 0" printable="1"/>' for x, y in posicoes)
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
             'xmlns:slic3rpe="http://schemas.slic3r.org/3mf/2017/06">\n'
             '<metadata name="slic3rpe:Version3mf">1</metadata>\n<metadata name="Title">Cartao MAVISKY 3 cores</metadata>\n'
             f'<resources><object id="1" type="model"><mesh><vertices>{"".join(verts)}</vertices>'
             f'<triangles>{"".join(tris)}</triangles></mesh></object></resources>\n'
             f'<build>{items}</build>\n</model>\n')
    vol_xml = "".join(
        f'<volume firstid="{a}" lastid="{b}">'
        f'<metadata type="volume" key="name" value="{n}"/>'
        f'<metadata type="volume" key="volume_type" value="ModelPart"/>'
        f'<metadata type="volume" key="extruder" value="{e}"/>'
        f'<metadata type="volume" key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>'
        '<mesh edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>'
        '</volume>' for n, e, a, b in vols)
    cfg = ('<?xml version="1.0" encoding="UTF-8"?>\n<config>\n'
           f'<object id="1" instances_count="{len(posicoes)}">'
           '<metadata type="object" key="name" value="cartao-mavisky"/>'
           '<metadata type="object" key="extruder" value="1"/>'
           f'{vol_xml}</object>\n</config>\n')
    ct = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
          '<Default Extension="config" ContentType="application/xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
            '</Relationships>')
    with zipfile.ZipFile(caminho, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model)
        z.writestr("Metadata/Slic3r_PE_model.config", cfg)


def grelha(cols, linhas, gap=5.0):
    w = cols * CARD_W + (cols - 1) * gap
    h = linhas * CARD_H + (linhas - 1) * gap
    x0 = (BED - w) / 2 + CARD_W / 2
    y0 = (BED - h) / 2 + CARD_H / 2
    return [(x0 + c * (CARD_W + gap), y0 + r * (CARD_H + gap)) for r in range(linhas) for c in range(cols)]


# ------------------------------------------------------------------ troca de filamento (G-code oficial QIDI)
def troca(prev, nxt, max_layer_z):
    e_feed = int(60.0 * MAX_VOL_SPEED / FIL_AREA)
    vol = PURGA.get((prev, nxt), 300.0)
    comprimento = vol / FIL_AREA
    n = min(4, max(1, round(vol / 135.0)))
    flush = [comprimento / n if i < n else 0.0 for i in range(4)]
    L = []
    a = L.append
    if max_layer_z < 12:
        a("G1 Z15 F1200")
    elif max_layer_z + 3 > MAX_PRINT_HEIGHT:
        a(f"G0 Z{MAX_PRINT_HEIGHT:g} F1200")
    else:
        a(f"G0 Z{max_layer_z + 3:.3f} F1200")
    a(f"TOOL_CHANGE_START F={prev} T={nxt}")
    a("DISABLE_ALL_SENSOR")
    a(f"G1 E-5 F{e_feed}")
    a(f"CUT_FILAMENT T={prev}")
    a("MOVE_TO_TRASH")
    a("M400")
    a(f"M104 S{TEMP_RANGE_HIGH}")
    a("M106 S0")
    a("M106 P2 S0")
    a(f"UNLOAD_T{prev}")
    a("G92 E0")
    a("M83")
    a("G1 E2 F50")
    a(f"T{nxt}")
    a(f"SET_HEATER_TEMPERATURE HEATER=extruder TARGET={TEMP_RANGE_HIGH} WAIT=1")
    a("M400")
    a("M106 S60")
    a("; FLUSH_START")
    a("G1 E1 F50")
    for k, (fr, f) in enumerate([(0.58, e_feed), (0.02, 50), (0.18, e_feed), (0.02, 50), (0.18, e_feed), (0.02, 50)]):
        a(f"G1 E{65.5 * fr:.3f} F{f}")
    a(f"G1 E-{RETRACT_TOOLCHANGE:g} F1800")
    a("; FLUSH_END")
    for i, fl in enumerate(flush):
        if fl <= 1:
            continue
        a("M400")
        a("M106 S255")
        a("G91")
        a("G1 X-5 F60")
        a("G1 X5 F60")
        a("G90")
        a("CLEAR_FLUSH")
        a("M400")
        a("M106 S60")
        a("; FLUSH_START")
        a(f"G1 E{RETRACT_TOOLCHANGE:g} F300")
        for fr, f in [(0.58, e_feed), (0.02, 50), (0.18, e_feed), (0.02, 50), (0.18, e_feed), (0.02, 50)]:
            a(f"G1 E{fl * fr:.3f} F{f}")
        a(f"G1 E-{RETRACT_TOOLCHANGE:g} F1800")
        a("; FLUSH_END")
    a(f"M104 S{TEMP_PRINT}")
    a("M400")
    a("M106 S255")
    a("G91")
    a("G1 X-5 F60")
    a("G1 X5 F60")
    a("G90")
    a(f"M109 S{TEMP_PRINT}")
    a("G92 E0")
    a("M400")
    a("CLEAR_FLUSH")
    a("CLEAR_OOZE")
    a("M400")
    a("M106 S0")
    a("TOOL_CHANGE_END")
    a("G1 Y305 F9000")
    a("ENABLE_ALL_SENSOR")
    usado = 65.5 * 1.0 + 1 + 2 + sum(flush)  # mm de filamento novo deitado fora
    return L, usado


def pos_processar(gcode_path):
    txt = open(gcode_path, encoding="utf-8").read().split("\n")
    out, purgado, pendente_deret, trocas, saltar_t = [], 0.0, False, 0, False
    for ln in txt:
        # o PrusaSlicer acrescenta o seu próprio "Tn" depois do G-code de troca:
        # o bloco QIDI (ou o G-code de início) já o faz, por isso sai daqui
        if saltar_t and re.fullmatch(r"T\d", ln.strip()):
            saltar_t = False
            continue
        m = re.match(r"; MAVI_TOOLCHANGE (-?\d+) (\d+) ([\d.]+)", ln)
        if m:
            prev, nxt, z = int(m.group(1)), int(m.group(2)), float(m.group(3))
            saltar_t = True
            if prev == nxt or prev < 0 or prev > 2:
                continue  # seleção inicial: já tratada no G-code de início (T[initial_tool])
            bloco, usado = troca(prev, nxt, z)
            out.append(f"; ===== troca de filamento T{prev} -> T{nxt} (G-code oficial QIDI Plus 4 + Box) =====")
            out.extend(bloco)
            out.append("; ===== fim da troca =====")
            purgado += usado
            pendente_deret = True
            trocas += 1
            continue
        # o bloco QIDI termina com o filamento recolhido 2 mm: repor antes da 1.ª extrusão
        if pendente_deret and re.match(r"G1 (?=.*[XY])(?=.*E\.?\d)", ln):
            out.append(f"G1 E{RETRACT_TOOLCHANGE:g} F1800 ; repor recolha da troca")
            pendente_deret = False
        out.append(ln)
    open(gcode_path, "w", encoding="utf-8").write("\n".join(out))
    return trocas, purgado


def miniaturas(gcode_path, posicoes, cartao_png):
    """Embute miniaturas PNG (96x96 e 272x272) no formato lido pelo Klipper/QIDI."""
    import base64
    import io

    from PIL import Image

    card = Image.open(cartao_png).convert("RGBA")
    xs = [x for x, _ in posicoes]
    ys = [y for _, y in posicoes]
    x0, x1 = min(xs) - CARD_W / 2 - 4, max(xs) + CARD_W / 2 + 4
    y0, y1 = min(ys) - CARD_H / 2 - 4, max(ys) + CARD_H / 2 + 4
    lado = max(x1 - x0, y1 - y0)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    blocos = []
    for px in (96, 272):
        im = Image.new("RGBA", (px, px), (0, 0, 0, 0))
        k = px / lado
        cw, ch = max(1, round(CARD_W * k)), max(1, round(CARD_H * k))
        c = card.resize((cw, ch), Image.LANCZOS)
        for x, y in posicoes:
            im.alpha_composite(c, (round(px / 2 + (x - cx) * k - cw / 2), round(px / 2 - (y - cy) * k - ch / 2)))
        buf = io.BytesIO()
        im.save(buf, "PNG", optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode()
        linhas = [b64[i:i + 78] for i in range(0, len(b64), 78)]
        blocos.append(";\n; thumbnail begin {0}x{0} {1}\n".format(px, len(b64)) +
                      "\n".join("; " + ln for ln in linhas) + "\n; thumbnail end\n;\n")
    txt = open(gcode_path, encoding="utf-8").read()
    i = txt.index("\n") + 1  # depois da 1.ª linha ("; generated by ...")
    open(gcode_path, "w", encoding="utf-8").write(txt[:i] + "\n" + "".join(blocos) + txt[i:])


def fatiar(nome, posicoes, pasta_out):
    os.makedirs(pasta_out, exist_ok=True)
    pasta_3mf = os.path.join(RAIZ, "slicer", "prusaslicer")
    os.makedirs(pasta_3mf, exist_ok=True)
    mf = os.path.join(pasta_3mf, f"{nome}.3mf")
    montar_3mf(mf, posicoes)
    gc = os.path.join(pasta_out, f"{nome}.gcode")
    cmd = ["prusa-slicer", "--export-gcode", "--load", INI, "--dont-arrange", "--output", gc, mf]
    if not os.environ.get("DISPLAY"):
        cmd = ["xvfb-run", "-a"] + cmd
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(gc):
        print(r.stdout[-3000:], r.stderr[-3000:])
        raise SystemExit("PrusaSlicer falhou")
    trocas, purgado_mm = pos_processar(gc)
    cartao_png = os.path.join(RAIZ, "previews", "vista-topo-recortada.png")
    if os.path.exists(cartao_png):
        miniaturas(gc, posicoes, cartao_png)
    return mf, gc, trocas, purgado_mm


if __name__ == "__main__":
    pasta = os.path.join(RAIZ, "gcode")
    for nome, pos in [("cartao-mavisky-1x-qidi-plus4-box", [(BED / 2, BED / 2)]),
                      ("cartao-mavisky-12x-qidi-plus4-box", grelha(3, 4))]:
        mf, gc, trocas, purgado = fatiar(nome, pos, pasta)
        print(nome, "| trocas:", trocas, "| purga ~", round(purgado * FIL_AREA * 1.24 / 1000, 2), "g")
