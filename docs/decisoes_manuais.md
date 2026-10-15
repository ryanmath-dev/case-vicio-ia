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
- Seed usada: ___
- Tamanho: ___ questões
- Critério de rótulo: tema que a questão de fato aborda (não o assunto_origem).
- Arquivo: `docs/amostra_ouro.csv`
- Observações de rotulagem (casos difíceis, dúvidas):
