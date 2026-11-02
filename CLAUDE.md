# Instruções para o Claude

## Entrega de ficheiros

- **Gravar sempre os ficheiros finais na pasta Transferências (Downloads) do computador
  "MD" do utilizador**, através do Remote Control (`list_computer_folders` /
  `request_computer_folder`, pasta "Downloads").
- Se o computador não estiver acessível, enviar os ficheiros como anexo na conversa,
  dizer ao utilizador que não foi possível gravar em Transferências e porquê (por exemplo,
  a app do Claude no Windows precisa de ser atualizada ou o Remote Control está desligado).
- Continuar também a fazer commit e push no repositório, como até aqui.

## Projetos

- `cartao-visita/`: cartão impresso MAVISKY (PDF para gráfica).
- `cartao-visita-mavi3dprint/`: cartão impresso MAVI 3D PRINT.
- `cartao-3d/`: cartões para impressão 3D em 3 cores na QIDI Plus 4 + QIDI Box
  (MAVISKY na raiz, MAVI 3D PRINT em `cartao-3d/mavi3dprint/`). Regenerar com
  `python3 scripts/gerar_tudo.py [pasta]`.
- Responder em português de Portugal.
