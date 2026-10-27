# Cartão de visita — MAVISKY

Cartão 85 × 55 mm (frente + verso) com o novo logótipo MAVISKY
(Filmagens Aéreas & FPV), na paleta da marca: antracite `#15171A`,
cobre `#C47A45`, branco `#F5F5F5`, cinza `#6B6F73`; fonte Montserrat.

- **Frente:** logótipo circular completo sobre fundo antracite com curvas de nível em cobre.
- **Verso:** logótipo empilhado (sem o anel) + nome, função e contactos; slogan "Imagens que vão mais longe".

## Arquivos

- `cartao-visita-mavisky-grafica.pdf` — para a gráfica: 2 páginas (frente, verso),
  91 × 61 mm = 85 × 55 mm + 3 mm de sangria em cada lado, fontes embutidas, RGB.
- `cartao-visita-mavisky.html` — fonte editável; abre no navegador para pré-visualizar.
- `previews/frente.png`, `previews/verso.png` — imagens do formato final (sem sangria).
- `assets/` — logótipo original, versões recortadas para o cartão, fonte e padrão topográfico.
- `scripts/` — `preparar_assets.py` (recorta o logótipo) e `gerar.js` (gera PDF e PNG).

## Antes de imprimir

Os contactos no verso são **exemplos** (procurar `EDITAR` no HTML):
nome, função, telefone, email, site e Instagram. Depois de editar:

```
node scripts/gerar.js
```

Sugestão de impressão: papel 350–400 g mate, laminação soft-touch;
opcional hot-stamping cobre no anel e em "SKY".
