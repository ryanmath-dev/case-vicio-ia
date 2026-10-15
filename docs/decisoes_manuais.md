# Decisões tomadas à mão

> O README do case exige registrar toda decisão manual e o porquê.
> Inclui: regras-limiar escolhidas, questões reclassificadas na mão, nó canônico
> escolhido entre temas duplicados, e a rotulagem da amostra-ouro.

| # | Data | Decisão | Por quê | Afeta |
|---|------|---------|---------|-------|
| 1 | 2026-10-14 | Excluir da lista de candidatos os 20 nós sem descrição (67xx) | São duplicatas de ramo (B1) e módulos de curso "Parte 1/Parte 2" (B2), sem filhos e sem histórico de questões no source. A equipe rotulou nos nós canônicos (47xx/5465, que têm descrição). Apresentá-los só gera erro de convenção que nenhum modelo detecta. | `src/prompt.py:temas_selecionaveis` — 355 selecionáveis de 377 |
| 2 | 2026-10-14 | Ignorar o campo `comando`; não usar disciplina/assunto de origem como rótulo | `comando` é gerado artificialmente (A7); os campos de origem vêm errados do banco (A1/A2). | `src/normalizar.py`, prompt v1 |
| 3 | 2026-10-14 | Prompt instrui o modelo a subir ao TEMA PAI na dúvida entre irmãos | Implementa a alavanca da régua já no 1º estágio (além de reforçar no juiz). | `prompts/classificacao_v1.md` |

## Amostra-ouro (rotulagem manual para estimar precisão)
- Seed usada: **42** (`src/amostra_ouro.py --n 50 --seed 42`)
- Tamanho: **50 questões**
- **Rotulada ANTES de o comitê rodar** (os modelos ainda não tinham sido chamados)
  → medição imparcial, sem ancoragem nas saídas dos modelos.
- Critério de rótulo: tema que a questão de fato aborda (não o assunto_origem).
  Quando a questão é multitema sem dominante claro, rotulei no **tema pai**
  (nível 1), espelhando a mesma alavanca que o juiz usa — é justo pela régua.
- Distribuição: Penal 17, Processo Penal 16, Criminologia 9, Leg. Especial 7,
  fora 1. Arquivo: `docs/amostra_ouro.csv`.
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
