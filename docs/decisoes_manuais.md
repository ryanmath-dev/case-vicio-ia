# Decisões tomadas à mão

> O README do case exige registrar toda decisão manual e o porquê.
> Inclui: regras-limiar escolhidas, questões reclassificadas na mão, nó canônico
> escolhido entre temas duplicados, e a rotulagem da amostra-ouro.

| # | Data | Decisão | Por quê | Afeta |
|---|------|---------|---------|-------|
| 1 | 2026-10-14 | Excluir da lista de candidatos os 20 nós sem descrição (67xx) | São duplicatas de ramo (B1) e módulos de curso "Parte 1/Parte 2" (B2), sem filhos e sem histórico de questões no source. A equipe rotulou nos nós canônicos (47xx/5465, que têm descrição). Apresentá-los só gera erro de convenção que nenhum modelo detecta. | `src/prompt.py:temas_selecionaveis` — 355 selecionáveis de 377 |
| 2 | 2026-10-14 | Ignorar o campo `comando`; não usar disciplina/assunto de origem como rótulo | `comando` é gerado artificialmente (A7); os campos de origem vêm errados do banco (A1/A2). | `src/normalizar.py`, prompt v1 |
| 3 | 2026-10-14 | Prompt instrui o modelo a subir ao TEMA PAI na dúvida entre irmãos | Implementa a alavanca da régua já no 1º estágio (além de reforçar no juiz). | `prompts/classificacao_v1.md` |
| 4 | 2026-10-14 | Modelos: `claude-haiku-5-5` + `gpt-4.1-mini` (baratos) | Orçamento real US$5+US$5; o case diz que modelo caro não pesa. Projeção ~US$0,7 total. | `src/classificadores.py` |
| 5 | 2026-10-16 | Comitê de **2 famílias** (Claude + GPT); Gemini testado e **excluído** | Gemini free = 20 req/dia; rodei via Vertex AI (gemini-2.5-flash, 359). Medido contra 100 questões-ouro: a 3ª família NÃO melhora a fronteira da régua (só adiciona cobertura abaixo de 95%). Votos em cache; troca p/ 3 é 1 linha. | `src/classificadores.py:PROVIDERS` |
| 6 | 2026-10-15 | `max_tokens` do Anthropic 1024→2048 | 25/359 truncavam o JSON (haiku-5-5 escreve raciocínio longo). | `src/classificadores.py:_call_anthropic` |
| 7 | 2026-10-16 | **Gate `MIN_CONF_EXATO=0,85`** no acordo exato | A amostra-ouro mostrou que o erro mora no "acordo exato", não na alavanca (~100%). Exigir ≥2 famílias + nenhuma hesitante. Medido em 100 questões-ouro: precisão **0,978 (44/45)**, Wilson 0,88–1,00. Sweep fino confirma que 0,85 é o ponto de máxima cobertura (46%) ainda ≥95%. | `src/juiz.py` |

## Amostra-ouro (rotulagem manual para estimar precisão)
- Seed usada: **42** (50 iniciais) + **123** (mais 50) → **100 questões**
- Tamanho: **100 questões** (ampliada em 2026-10-16 para estreitar o intervalo;
  as 50 iniciais foram preservadas). Precisão medida da submissão: **44/45 = 0,978**
  (Wilson 0,88–1,00).
- **Medição imparcial:** as 50 iniciais foram rotuladas ANTES de o comitê rodar;
  as +50 (ampliação) foram rotuladas lendo **só o enunciado**, sem olhar os votos
  dos modelos. Em nenhum caso o rótulo viu a saída do comitê.
- Critério de rótulo: tema que a questão de fato aborda (não o assunto_origem).
  Quando a questão é multitema sem dominante claro, rotulei no **tema pai**
  (nível 1), espelhando a mesma alavanca que o juiz usa — é justo pela régua.
- Distribuição (n=100): Penal 40, Processo Penal 36, Leg. Especial 13,
  Criminologia 10, fora 1. Arquivo: `docs/amostra_ouro.csv`.
- Casos difíceis / de baixa confiança no rótulo (candidatos naturais a `revisar`):
  - **Q0014** → `fora`: trata de medidas socioeducativas/ECA (HC em vara da
    infância); nenhum tema da árvore cobre (disciplina de origem "Unificada").
  - **Q0126, Q0303, Q0333, Q0288, Q0347**: enunciados "grab-bag" (5 alternativas
    de temas distintos). Ancorei no tema da **alternativa correta** (ex.: Q0126
    extraterritorialidade → 5182; Q0333 positivismo → 4373) ou no assunto quando
    não havia dominante (Q0288 → 5066 Concurso de Crimes). Baixa confiança — são
    exatamente o tipo que o diagnóstico aponta como difícil.
  - **Q0016, Q0151**: multi-subtema de prisões → rotulei no tema 5517 (Prisões
    em Espécie), não num subtema específico.
  - **Q0280**: crime contra a honra com forte carga processual (queixa, exceção
    da verdade) → ancorei no material (5120), mas ProcPenal/Ação Penal defensável.
