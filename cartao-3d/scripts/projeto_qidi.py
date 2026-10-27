"""Gera projetos .3mf nativos do QIDI Studio (Plus 4 + Box, 3 cores).

O cartão é um objeto com 3 partes, cada uma já atribuída ao seu filamento:
  parte "base preto" -> filamento 1 (slot 1 da Box)
  parte "cobre"      -> filamento 2 (slot 2)
  parte "branco"     -> filamento 3 (slot 3)
As definições vêm dos perfis oficiais da QIDI (slicer/perfis-qidi-oficiais),
com as alterações deste projeto (sem torre de purga, Arachne afinado, purgas baixas).
Formato seguido: src/libslic3r/Format/qds_3mf.cpp do QIDI Studio.
"""
import io
import json
import os
import sys
import zipfile

import trimesh
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fatiar import BED, PARTES, PURGA, STL, grelha  # noqa: E402
from geometria import CARD_H, CARD_W, RAIZ  # noqa: E402

PERFIS = os.path.join(RAIZ, "slicer", "perfis-qidi-oficiais")
VERSAO = "02.07.02.73"
CORES = ["#15171A", "#C47A45", "#F5F5F5"]
PRINTER = "X-Plus 4 0.4 nozzle"
PROCESS = "0.20mm Standard @XPlus4"
FILAMENT = "QIDI PLA Basic @Qidi X-Plus 4 0.4 nozzle"

ALTERACOES_PROCESSO = {
    "enable_prime_tower": "0",       # 2 trocas apenas: a purga vai para o caixote, sem torre
    "wall_generator": "arachne",
    "min_feature_size": "10%",       # afinado por medição para o texto pequeno
    "min_bead_width": "60%",
}
META = {"name", "inherits", "from", "instantiation", "setting_id", "type", "compatible_printers",
        "compatible_printers_condition", "compatible_prints", "compatible_prints_condition",
        "filament_id", "printer_settings_id", "is_custom_defined", "description"}


def _cadeia(*nomes):
    d = {}
    for n in nomes:
        d.update(json.load(open(os.path.join(PERFIS, n + ".json"), encoding="utf-8")))
    return {k: v for k, v in d.items() if k not in META}


def project_settings():
    maquina = _cadeia("fdm_machine_x_common", PRINTER)
    processo = _cadeia("fdm_process_common", PROCESS)
    filamento = _cadeia("fdm_filament_common", "QIDI PLA Basic@X4", FILAMENT)
    cfg = {}
    cfg.update(maquina)
    cfg.update(processo)
    for k, v in filamento.items():
        cfg[k] = (v * 3) if isinstance(v, list) and len(v) == 1 else v
    cfg.update(ALTERACOES_PROCESSO)
    matriz = []
    for a in range(3):
        for b in range(3):
            matriz.append("0" if a == b else f"{PURGA.get((a, b), 300.0):g}")
    cfg.update({
        "name": "project_settings",
        "from": "project",
        "version": VERSAO,
        "printer_settings_id": PRINTER,
        "print_settings_id": PROCESS,
        "filament_settings_id": [FILAMENT] * 3,
        "inherits_group": ["", "", "", "", ""],
        "different_settings_to_system": [";".join(sorted(ALTERACOES_PROCESSO)), "", "", "", ""],
        "filament_colour": CORES,
        "filament_map": ["1", "1", "1"],
        "flush_volumes_matrix": matriz,
        "flush_multiplier": ["1"],
        "curr_bed_type": "Textured PEI Plate",
        "print_sequence": "by layer",
    })
    return cfg


def _mesh(m):
    v = "\n".join(f'     <vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in m.vertices)
    t = "\n".join(f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in m.faces)
    return f"    <mesh>\n     <vertices>\n{v}\n     </vertices>\n     <triangles>\n{t}\n     </triangles>\n    </mesh>\n"


def gerar(caminho, posicoes, miniatura_png):
    malhas = []
    for nome, f, ext in PARTES:
        m = trimesh.load(os.path.join(STL, f))
        m.apply_translation((-CARD_W / 2, -CARD_H / 2, 0))
        malhas.append((nome, m, ext))

    ns = ('xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
          'xmlns:QIDIStudio="http://schemas.qiditech.com/package/2021" '
          'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p"')

    # sub-objetos (uma malha por parte)
    sub = [f'<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" {ns}>\n'
           f' <metadata name="QIDIStudio:3mfVersion">1</metadata>\n <resources>\n']
    for i, (nome, m, _) in enumerate(malhas, start=1):
        sub.append(f'  <object id="{i}" p:UUID="{i:08x}-81cb-4c03-9d28-80fed5dfa1dc" type="model">\n{_mesh(m)}  </object>\n')
    sub.append(" </resources>\n <build/>\n</model>\n")

    obj_id = len(malhas) + 1
    comps = "".join(
        f'    <component p:path="/3D/Objects/object_1.model" objectid="{i}" '
        f'p:UUID="{i - 1:08x}-b206-40ff-9872-83e8017abed1" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n'
        for i in range(1, len(malhas) + 1))
    items = "".join(
        f'  <item objectid="{obj_id}" p:UUID="{k + 2:08x}-b1ec-4553-aec9-835e5b724bb4" '
        f'transform="1 0 0 0 1 0 0 0 1 {x:.4f} {y:.4f} 0" printable="1"/>\n'
        for k, (x, y) in enumerate(posicoes))
    principal = (f'<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" {ns}>\n'
                 f' <metadata name="Application">QIDIStudio-{VERSAO}</metadata>\n'
                 ' <metadata name="QIDIStudio:3mfVersion">1</metadata>\n'
                 ' <metadata name="Title">Cartao MAVISKY 3 cores</metadata>\n'
                 ' <metadata name="Designer">MAVISKY</metadata>\n'
                 ' <resources>\n'
                 f'  <object id="{obj_id}" p:UUID="00000001-61cb-4c03-9d28-80fed5dfa1dc" type="model">\n'
                 f'   <components>\n{comps}   </components>\n  </object>\n'
                 ' </resources>\n'
                 f' <build p:UUID="2c7c17d8-22b5-4d84-8835-1976022ea369">\n{items} </build>\n</model>\n')

    partes = "".join(
        f'    <part id="{i}" subtype="normal_part">\n'
        f'      <metadata key="name" value="{nome}"/>\n'
        '      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n'
        f'      <metadata key="extruder" value="{ext}"/>\n'
        f'      <mesh_stat face_count="{len(m.faces)}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n'
        '    </part>\n' for i, (nome, m, ext) in enumerate(malhas, start=1))
    instancias = "".join(
        '    <model_instance>\n'
        f'      <metadata key="object_id" value="{obj_id}"/>\n'
        f'      <metadata key="instance_id" value="{k}"/>\n'
        f'      <metadata key="identify_id" value="{100 + k}"/>\n'
        '    </model_instance>\n' for k in range(len(posicoes)))
    montagem = "".join(
        f'   <assemble_item object_id="{obj_id}" instance_id="{k}" transform="1 0 0 0 1 0 0 0 1 {x:.4f} {y:.4f} 0" offset="0 0 0" />\n'
        for k, (x, y) in enumerate(posicoes))
    face_total = sum(len(m.faces) for _, m, _ in malhas)
    model_settings = ('<?xml version="1.0" encoding="UTF-8"?>\n<config>\n'
                      f'  <object id="{obj_id}">\n'
                      '    <metadata key="name" value="cartao-mavisky"/>\n'
                      '    <metadata key="extruder" value="1"/>\n'
                      f'    <metadata face_count="{face_total}"/>\n'
                      f'{partes}  </object>\n'
                      '  <plate>\n'
                      '    <metadata key="plater_id" value="1"/>\n'
                      '    <metadata key="plater_name" value=""/>\n'
                      '    <metadata key="locked" value="false"/>\n'
                      '    <metadata key="thumbnail_file" value="Metadata/plate_1.png"/>\n'
                      f'{instancias}  </plate>\n'
                      f'  <assemble>\n{montagem}  </assemble>\n</config>\n')

    content_types = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                     '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
                     ' <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
                     ' <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
                     ' <Default Extension="png" ContentType="image/png"/>\n'
                     ' <Default Extension="gcode" ContentType="text/x.gcode"/>\n</Types>\n')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
            ' <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
            ' <Relationship Target="/Metadata/plate_1.png" Id="rel-2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail"/>\n'
            '</Relationships>\n')
    model_rels = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                  '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
                  ' <Relationship Target="/3D/Objects/object_1.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
                  '</Relationships>\n')

    # miniatura do prato
    card = Image.open(miniatura_png).convert("RGBA")
    px = 512
    im = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    k = px / BED
    cw, ch = round(CARD_W * k), round(CARD_H * k)
    c = card.resize((cw, ch), Image.LANCZOS)
    for x, y in posicoes:
        im.alpha_composite(c, (round(x * k - cw / 2), round(px - y * k - ch / 2)))
    buf = io.BytesIO()
    im.save(buf, "PNG")

    with zipfile.ZipFile(caminho, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", principal)
        z.writestr("3D/_rels/3dmodel.model.rels", model_rels)
        z.writestr("3D/Objects/object_1.model", "".join(sub))
        z.writestr("Metadata/model_settings.config", model_settings)
        z.writestr("Metadata/project_settings.config", json.dumps(project_settings(), indent=4, ensure_ascii=False))
        z.writestr("Metadata/plate_1.png", buf.getvalue())


if __name__ == "__main__":
    pasta = os.path.join(RAIZ, "qidi-studio")
    os.makedirs(pasta, exist_ok=True)
    mini = os.path.join(RAIZ, "previews", "vista-topo-recortada.png")
    for nome, pos in [("cartao-mavisky-1x-QIDIStudio.3mf", [(BED / 2, BED / 2)]),
                      ("cartao-mavisky-12x-QIDIStudio.3mf", grelha(3, 4))]:
        gerar(os.path.join(pasta, nome), pos, mini)
        print(os.path.join(pasta, nome))
