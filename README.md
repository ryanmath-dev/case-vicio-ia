# Case Vício — Classificação de Tópicos (área de IA / Método VDE)

Classifica 359 questões jurídicas na árvore de 377 temas da plataforma,
decidindo entre **publicar**, **revisar** e **fora**, sob a régua de
**≥95% de precisão nas publicadas**.

> ⚙️ Em construção. Este README será completado com: como rodar, o passo a passo
> que gera `saidas/publicacao.csv`, modelos usados, custo aproximado e tempo.

## Estrutura
- `dados/` — entrada do case (questões, árvore de temas, LEIA-ME, enunciado).
- `prompts/` — prompts versionados.
- `src/` — pipeline (normalização → comitê de modelos → juiz → regras → estimativa).
- `saidas/` — `publicacao.csv`, `previsao.txt` e cache de chamadas.
- `docs/` — registros do raciocínio e o relatório final.
- `CLAUDE.md` — regras permanentes do projeto (lidas pelo agente a cada sessão).

## Entregáveis (checklist)
- [ ] `saidas/publicacao.csv` (359 linhas)
- [ ] `saidas/previsao.txt`
- [ ] Relatório (≤5 págs): como pensei · diagnóstico · produção · memo ao professor
- [ ] Código + este README

## Como rodar
_(a preencher)_
```
cp .env.example .env   # preencher ANTHROPIC/OPENAI/GOOGLE
# ...
```
