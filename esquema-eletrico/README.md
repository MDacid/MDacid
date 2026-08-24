# Esquema elétrico — Novo Quadro (controlo de acesso / tráfego)

Esquema técnico (rev. 01) baseado no memorando oficial do cliente
("Esquema Geral — protecoes.docx", 5 páginas), que substitui a versão
anterior deste esquema (feita em cima de um esboço fotografado à mão).

Arquitetura: quadro existente → disjuntor dedicado (a dimensionar) →
cabo L+N+PE até o novo quadro → interruptor-seccionador geral → DPS
Tipo 2 → distribuição interna 230VAC → RCBO1 (30mA Tipo A, alimenta
fonte 24VDC) / RCBO2 (30mA Tipo A, alimenta fonte 48/54VDC). A 24VDC
alimenta PLC, bobinas dos 3 relés e 2 semáforos (relé comanda o foco a
partir de uma saída do PLC). A 48/54VDC sai do quadro para um Switch
PoE (fisicamente fora do quadro, na zona das redes), que alimenta
câmaras, intercomunicador(es) e um equipamento "EX232 Remora → FM430".
Mini-PC e UPS (Eaton 5S 700i, 700VA/420W) também ficam fora do quadro.

## Arquivos

- `quadro-qe1-esquema.pdf` — esquema em 7 folhas A3, pronto para impressão/anexo.
- `quadro-qe1-esquema.html` — mesmo conteúdo, aberto em qualquer navegador.

## Conteúdo das folhas

1. Capa / arquitetura geral consolidada (equivalente à seção 9 do memorando)
2. Alimentação a partir do quadro existente + entrada do novo quadro —
   `-Q0` (no quadro existente), `-Q1` interruptor-seccionador, `-F0` DPS T2,
   `-Q2`/RCBO1, `-Q3`/RCBO2, e os pontos em aberto de instalação de terra
3. Circuito 24VDC (dentro do quadro) — fonte 24VDC, proteções DC
   individuais, PLC, bobinas dos relés `-K1..-K3`, Semáforo 1, Semáforo 2,
   detalhe "comando dos focos"
4. Circuito 48/54VDC e Switch PoE (fora do quadro) — fonte 48/54VDC,
   proteção DC, saída do quadro, Switch PoE alimentando câmaras/intercom/EX232→FM430
5. Mini-PC e UPS (fora do quadro) — alimentação do mini-PC em aberto;
   UPS Eaton 5S 700i com cargas de backup ainda em análise
6. Lista de bornes (`-X0` a `-X4`, `-PE`)
7. Lista de material (BOM) preliminar

Cada folha marca com um retângulo tracejado "NOVO QUADRO" o que fica
fisicamente dentro do quadro, conforme delimitação física definida no
memorando do cliente (seção 4).

## Pontos em aberto no próprio memorando do cliente (não resolvidos por mim)

- **Instalação de terra**: regime TT/TN-S/TN-C-S existente, disponibilidade
  de PE no quadro existente, separação N/PE, ponto de separação PEN,
  continuidade do PE e proteções diferenciais a montante — tudo por
  confirmar em obra. Assume-se provisoriamente 3 condutores L+N+PE vindos
  do quadro existente (marcado `*` no esquema), sem eletrodo de terra
  independente para o novo quadro nesta fase.
- **Alimentação do Mini-PC**: ainda não decidido se vem diretamente do
  novo quadro, da UPS, ou da infraestrutura elétrica existente da zona
  de redes.
- **Cargas de backup da UPS**: ainda em análise se a UPS Eaton 5S 700i
  deve alimentar a fonte 24VDC, a fonte 48/54VDC (Switch PoE), o Mini-PC,
  ou alguma combinação — depende da potência real instalada e da
  autonomia pretendida.
- **Mapeamento relé → foco de semáforo**: o memorando descreve o padrão
  genérico (saída do PLC → bobina do relé → contacto → +24VDC → foco do
  semáforo) mas não especifica quantos focos por semáforo nem qual relé
  aciona qual cor. Assumi 3 relés genéricos (`-K1..-K3`) repetindo o
  padrão, um por saída do PLC — confirmar com o projeto de sinalização.
- Disjuntor dedicado no quadro existente (`-Q0`), fonte 24VDC, fonte
  48/54VDC, PLC, Switch PoE e Mini-PC estão sem modelo/potência
  definidos — os valores no BOM são só indicativos.

## Sobre o formato EPLAN

Este esquema foi gerado sem acesso ao EPLAN Electric P8 (software
proprietário licenciado, não disponível neste ambiente). Ele segue as
convenções do EPLAN (tags `=`/`+`/`-`, numeração de folha, carimbo) para
facilitar a migração, mas **não é um projeto nativo `.elk`/`.edz`**.

Para levar ao EPLAN:

1. Abrir um projeto novo, criar a estrutura de páginas conforme as 7 folhas
   acima (mesmos nomes de folha/tag sugeridos).
2. Redesenhar os símbolos usando os blocos de função/macros padrão do
   EPLAN (interruptor-seccionador, DPS, RCBO, fonte, relé, régua de
   bornes) em vez dos símbolos simplificados deste PDF.
3. Usar a numeração automática de fios do EPLAN após montar as páginas
   reais (os números de borne aqui são preliminares/funcionais).
