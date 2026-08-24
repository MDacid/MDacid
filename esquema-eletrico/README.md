# Esquema elétrico — Quadro QE1 (alimentação)

Esquema preliminar do quadro elétrico com base na arquitetura de alimentação
fornecida (entrada 230V AC, 3 fontes DC — 24V, 48/54V PoE e alimentação
dedicada de mini-PC/gateway —, 3 relés, disjuntores de proteção, CLP,
semáforos, leitor QR, câmeras PoE e mini-PC/gateway).

## Arquivos

- `quadro-qe1-esquema.pdf` — esquema em 7 folhas A3, pronto para impressão/anexo.
- `quadro-qe1-esquema.html` — mesmo conteúdo, aberto em qualquer navegador.

## Conteúdo das folhas

1. Capa / diagrama de blocos geral
2. Alimentação geral CA (`=QE1+ALM`) — entrada 230V, `-Q1`, DPS `-F0`
3. Fonte 24V DC e distribuição (`=QE1+24V`) — `-F1`, `-Q2.x`, CLP, `-K1..K3`, semáforos, leitor QR
4. Fonte 48/54V DC e switch PoE (`=QE1+PoE`) — `-F2`, `-SW1`, câmeras, leitor QR (alternativa)
5. Alimentação mini-PC/gateway (`=QE1+PC`) — `-F3`, `-PC1`
6. Lista de bornes (`-X0` a `-X5`, `-PE`)
7. Lista de material (BOM) preliminar

## Premissas assumidas (não informadas pelo cliente — validar antes de fabricar)

- Entrada monofásica 230V AC (L+N+PE); se a instalação for trifásica, `-Q1`
  e a distribuição precisam ser redesenhados.
- `-K1, -K2, -K3` são relés de interface convencionais 24VDC comandados por
  saídas digitais do CLP (`-A1`), não relés de segurança certificados. Se a
  função real for parada de segurança (E-STOP, proteção de porta), o
  esquema da folha 3 precisa ser refeito com relé de segurança
  categoria/PL adequados (ex. Pilz PNOZ, Schmersal) — **essa informação
  não foi confirmada e é crítica para a segurança da instalação.**
- Correntes/potências das fontes e disjuntores são estimativas de projeto
  preliminar; dimensionar pela carga real de cada equipamento.
- Modelo do CLP e do mini-PC/gateway não foram informados — a fonte `-F3`
  (folha 5) depende da tensão exigida pelo modelo escolhido.
- Tensão PoE (802.3af = 48V / 802.3at = 54V) deve ser confirmada com o
  datasheet das câmeras e do leitor QR antes de especificar `-F2`.

## Sobre o formato EPLAN

Este esquema foi gerado sem acesso ao EPLAN Electric P8 (software
proprietário licenciado, não disponível neste ambiente). Ele segue as
convenções do EPLAN (tags `=`/`+`/`-`, numeração de folha, carimbo) para
facilitar a migração, mas **não é um projeto nativo `.elk`/`.edz`**.

Para levar ao EPLAN:

1. Abrir um projeto novo, criar a estrutura de páginas conforme as 7 folhas
   acima (mesmos nomes de folha/tag sugeridos).
2. Redesenhar os símbolos usando os blocos de função/macros padrão do
   EPLAN (disjuntor, fonte, relé, régua de bornes) em vez dos símbolos
   simplificados deste PDF.
3. Usar a numeração automática de fios do EPLAN após montar as páginas
   reais (os números de borne aqui são preliminares/funcionais).
