# Cartão de visita — MAVI 3D PRINT

Cartão 85 × 55 mm (frente + verso) com o logótipo MAVI 3D PRINT, **redesenhado em vetor**
a partir do banner da marca (`assets/banner-referencia.png`). Por ser vetorial, sai nítido
a qualquer tamanho, com efeito metálico prata e cobre. Paleta e fonte iguais às do
cartão MAVISKY (antracite `#15171A`, cobre `#C47A45`, Montserrat).

- **Frente:** logótipo completo, com textura subtil de camadas de impressão 3D.
- **Verso:** logótipo, nome, função, telefone e site (`mavi` a branco, `3dprint` a cobre, como no banner).

## Arquivos

- `cartao-visita-mavi3dprint-grafica.pdf`: para a gráfica, 2 páginas (frente e verso),
  91 × 61 mm = 85 × 55 mm + 3 mm de sangria, fontes embutidas.
- `cartao-visita-mavi3dprint.html`: fonte editável (procurar `EDITAR`).
- `previews/`: frente e verso no formato final.
- `assets/logo-mavi3dprint.svg`: logótipo vetorial (também serve para site, redes, etc.).
  É gerado por `../cartao-3d/scripts/logo_mavi3d.py`.

Depois de editar o HTML, correr nesta pasta:

```
node scripts/gerar.js
```
