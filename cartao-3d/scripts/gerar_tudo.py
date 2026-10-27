"""Regenera tudo a partir de dados.json: geometria, STEP/STL/DXF, G-code e projetos QIDI Studio.

Uso (na pasta cartao-3d):  python3 scripts/gerar_tudo.py
Requisitos: python3 com shapely, fonttools, scikit-image, scipy, pillow, trimesh, cadquery, ezdxf;
            prusa-slicer 2.7 (apt install prusa-slicer) e xvfb-run.
"""
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
for s in ["geometria.py", "pre_visualizar.py", "exportar.py", "fatiar.py", "projeto_qidi.py"]:
    print(f"== {s}")
    subprocess.run([sys.executable, os.path.join(AQUI, s)] + (["previews"] if s == "pre_visualizar.py" else []),
                   cwd=RAIZ, check=True)
subprocess.run([sys.executable, os.path.join(AQUI, "verificar_gcode.py"),
                "gcode/cartao-mavisky-1x-qidi-plus4-box.gcode", "previews/simulacao-gcode.png"], cwd=RAIZ, check=True)
subprocess.run([sys.executable, os.path.join(AQUI, "estatisticas.py"),
                "gcode/cartao-mavisky-1x-qidi-plus4-box.gcode", "gcode/cartao-mavisky-12x-qidi-plus4-box.gcode"],
               cwd=RAIZ, check=True)
