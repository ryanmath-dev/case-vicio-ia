# CLAUDE.md — Case: Classificação de Tópicos (Vício / Método VDE)

> Este arquivo é lido automaticamente pelo Claude Code em toda interação.
> São as regras permanentes do projeto. Se alguma regra mudar, edite AQUI.

## 1. Objetivo
Classificar **359 questões** jurídicas (Direito Penal, Processo Penal, Legislação
Penal Especial, Criminologia) na árvore de **377 temas** (`dados/temas.csv`).
Para cada questão, decidir: **publicar**, **revisar** ou **fora**.

Entregáveis avaliados: `publicacao.csv`, `previsao.txt`, relatório (≤5 págs) e
código com README. O que pesa: **cobertura com precisão ≥95% nas publicadas**,
**quão bem a previsão acerta o resultado real**, e a **clareza do raciocínio**.

## 2. A RÉGUA (regra inviolável)
- Das questões **publicadas**, pelo menos **95% precisam estar certas**.
- Conta como **certo**: o tema exato que a equipe atribuiu, OU um nó do mesmo
  ramo — o **pai direto** ou um **filho direto** dele.
- Conta como **ERRO**: publicar num **subtema irmão** (outro subtema do mesmo tema).
- Respeitada a régua, **publicar mais é melhor**; o resto vai para revisar.
- **Alavanca estratégica:** na dúvida entre dois subtemas irmãos, publicar no
  **TEMA PAI** é seguro (conta como certo para qualquer filho). É a principal
  forma de ganhar cobertura sem furar os 95%.

## 3. Regras de decisão
- **publicar** — alta confiança + concordância entre os classificadores + não cai
  em lixeira genérica. `tema_central_id` obrigatório.
- **revisar** — divergência entre modelos, confiança baixa, questão multitema sem
  tema dominante, ou cai em lixeira suspeita. `tema_central_id` = melhor sugestão;
  `motivo` obrigatório.
- **fora** — nenhum tema da árvore serve (ex.: questão de outra disciplina).
  `tema_central_id` vazio; `motivo` obrigatório.
- **Nunca** usar tema inativo (`status != active`): `5078` (Direito penal
  econômico) e `5234` (Tratados e convenções em matéria criminal).

## 4. Os dados mentem (não confiar cegamente)
- **NÃO** usar `assunto_origem` nem `disciplina_origem` como rótulo. São pistas
  fracas e enviesadas (há lixeiras e disciplinas trocadas). Usar só como sinal
  secundário / desempate.
- Classificar lendo **enunciado + alternativas**. **Ignorar** o campo `comando`
  (parece gerado artificialmente). Tratar ruído de OCR e HTML cru.

## 5. Contrato de saída
`saidas/publicacao.csv` — **359 linhas**, uma por questão:
`id, decisao, tema_central_id, extras_ids(;), confianca(0-1), motivo`
- `tema_central_id`: obrigatório em publicar/revisar; vazio em fora.
- `motivo`: obrigatório em revisar/fora.
`saidas/previsao.txt` — formato exato do `dados/LEIA-ME.md`.

## 6. Modelos (comitê multi-família)
- Anthropic (Claude) + OpenAI (GPT) + Google (Gemini). Famílias diferentes para
  **descorrelacionar erros** — é o que faz o comitê valer a pena.
- Temperatura **0**; seeds fixas onde o provedor permitir.
- Salvar a **resposta crua** de cada modelo em `saidas/cache/` (chave:
  id_questao + modelo + versao_do_prompt). Reprodutibilidade e economia: nunca
  re-chamar o que já está em cache.
- Chaves de API por variável de ambiente (`.env`, no `.gitignore`). **Nunca
  commitar chave.**

## 7. REGRA DE OURO — registrar o raciocínio em tempo real
O relatório exige o **caminho, inclusive os becos sem saída**. Isso não se
reconstrói no fim. Portanto, DURANTE a execução:
1. Antes de cada experimento/decisão técnica → escreva a **HIPÓTESE** em
   `docs/diario.md`.
2. Depois → registre o **RESULTADO com números**, mesmo (sobretudo) quando falha.
   Beco sem saída **nunca se apaga**: marque `DESCARTADO` e explique por quê.
3. Métrica numérica → também em `docs/experimentos.md` (tabela).
4. Defeito de dados/temas → `docs/diagnostico.md`, sempre com **IDs de exemplo**.
5. Decisão tomada à mão → `docs/decisoes_manuais.md`.
6. Tokens / custo / tempo por etapa → `docs/custos.md`.
7. Ideia para a seção de produção → `docs/producao.md`.
8. **Um commit por experimento/etapa**, com mensagem explicando o PORQUÊ.

## 8. Mapa registro → relatório (não esquecer nada)
| Seção do relatório | Fonte |
|---|---|
| a) Como pensei (+ becos sem saída) | `docs/diario.md` + `docs/experimentos.md` |
| b) Diagnóstico | `docs/diagnostico.md` |
| c) Produção (50k/semana, custo, monitoramento, fluxo) | `docs/producao.md` + `docs/custos.md` |
| d) Memo para o professor (1 pág) | `docs/diagnostico.md` (nós a fundir, temas a criar, questões a revisar) |
| README (rodar, modelos, custo, tempo, decisões à mão) | `docs/custos.md` + `docs/decisoes_manuais.md` |

## 9. Estimar a própria precisão SEM gabarito
- Rotular à mão uma **amostra aleatória (~50 questões, seed fixa)** → guardar em
  `docs/amostra_ouro.csv`; registrar o ato em `docs/decisoes_manuais.md`.
- Estimar precisão das publicadas combinando: (a) concordância entre modelos como
  proxy; (b) acerto medido na amostra-ouro; (c) intervalo por Wilson/bootstrap.
- `previsao.txt` tem de **bater com o resultado real** — é critério de avaliação.
  Ser honesto no intervalo vale mais do que chutar um número bonito.

## 10. Estrutura de pastas
```
dados/    entrada (questoes.jsonl, temas.csv, LEIA-ME.md, entrega_modelo.csv, enunciado.pdf)
prompts/  prompts versionados (um arquivo por etapa/modelo)
src/      pipeline (normalização, classificadores, juiz, regras, estimativa)
saidas/   publicacao.csv, previsao.txt, cache/ (respostas cruas)
docs/     registros vivos (diario, experimentos, diagnostico, ...) + relatório
```
