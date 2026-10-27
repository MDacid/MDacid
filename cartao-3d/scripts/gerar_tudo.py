"""Regenera tudo a partir do dados.json de um cartão: geometria, STEP/STL/DXF, G-code e projetos QIDI Studio.

Uso (na pasta cartao-3d):
  python3 scripts/gerar_tudo.py                 # cartão MAVISKY (esta pasta)
  python3 scripts/gerar_tudo.py mavi3dprint     # cartão numa subpasta com o seu dados.json
Requisitos: python3 com shapely, fonttools, scikit-image, scipy, pillow, trimesh, cadquery, ezdxf;
            prusa-slicer 2.7 (apt install prusa-slicer) e xvfb-run.
"""
import json
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
SAIDA = os.path.abspath(os.path.join(RAIZ, sys.argv[1])) if len(sys.argv) > 1 else RAIZ
env = dict(os.environ, CARTAO_SAIDA=SAIDA)
pref = json.load(open(os.path.join(SAIDA, "dados.json"), encoding="utf-8")).get("ficheiro", "cartao-mavisky")


def correr(*args):
    subprocess.run([sys.executable, *args], cwd=SAIDA, env=env, check=True)


for s in ["geometria.py", "pre_visualizar.py", "exportar.py", "fatiar.py", "projeto_qidi.py"]:
    print(f"== {s}")
    correr(os.path.join(AQUI, s), *(["previews"] if s == "pre_visualizar.py" else []))
correr(os.path.join(AQUI, "verificar_gcode.py"), f"gcode/{pref}-1x-qidi-plus4-box.gcode", "previews/simulacao-gcode.png")
correr(os.path.join(AQUI, "estatisticas.py"), f"gcode/{pref}-1x-qidi-plus4-box.gcode", f"gcode/{pref}-12x-qidi-plus4-box.gcode")
