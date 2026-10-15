# Notas para a Seção (c) — Produção

> Como isto rodaria toda semana em 50 mil questões + novas importações.
> Ir anotando ideias conforme surgem na execução.

## Pontos a cobrir (exigidos pelo enunciado)
- [ ] Que IA em cada ponto: embeddings, classificador treinado, LLM, agentes,
      revisão humana.
- [ ] Custo por questão (derivar de docs/custos.md).
- [ ] Como medir qualidade continuamente.
- [ ] Encaixe no fluxo: importação de questões, fila de revisão, reportes de alunos.

## Rascunho de arquitetura
- Estágio 0 — ingestão/normalização (código): limpar HTML/OCR.
- Estágio 1 — recuperação de candidatos: **embeddings** reduzem 377 temas a top-k
  (aqui, com 359 q., não foi preciso — a árvore inteira cabe no prompt; em 50k/sem
  vira necessário por custo/latência). [registrar como decisão de escala]
- Estágio 2 — classificação barata por LLM (cheap-by-default: Haiku 5.5 / Luna).
- Estágio 3 — escalonar ~10% incertos a modelo forte / comitê.
- Estágio 4 — regras publicar/revisar/fora + alavanca do tema-pai.
- Estágio 5 — fila do professor; reportes de alunos realimentam o conjunto-ouro.

## Monitoramento contínuo
- Conjunto-ouro vivo (crescido com reportes de alunos) para medir precisão real.
- Alarmes: taxa de "fora", acúmulo em lixeiras, queda de concordância do comitê.
- Amostragem semanal auditada por especialista.

## Custo (preencher de custos.md)
- US$/questão no desenho barato vs. no comitê forte.
