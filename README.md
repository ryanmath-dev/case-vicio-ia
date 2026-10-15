# Case — Classificação de Tópicos (Vício / Método VDE)

Classifica **359 questões** jurídicas (Penal, Processo Penal, Legislação Penal
Especial, Criminologia) na árvore de **377 temas** (`dados/temas.csv`), decidindo
para cada uma: **publicar**, **revisar** ou **fora**.

A régua: das questões publicadas, **≥95% precisam estar certas** — onde "certo"
é o tema exato, o **pai direto** ou um **filho direto** dele (publicar num
**subtema irmão** é erro). Respeitada a régua, publicar mais é melhor.

## Como funciona (pipeline)

```
dados/questoes.jsonl ─┐
dados/temas.csv ──────┤
                      ▼
 [0] normalizar.py      limpa HTML/OCR, monta "enunciado + alternativas",
                        carrega a árvore (pai/filhos/irmãos), marca inativos
                      ▼
 [2] prompt.py          renderiza a árvore (355 nós selecionáveis) + o prompt v1
                      ▼
 [3] classificadores.py COMITÊ de 3 famílias (Claude + GPT + Gemini), saída JSON,
                        resposta crua salva em saidas/cache/ (reprodutível)
                      ▼
 [4] juiz.py            combina os 3 votos: régua pai/filho + alavanca do tema-pai
                        + proteção de lixeiras → saidas/publicacao.csv (359 linhas)
                      ▼
 [5] estimativa.py      precisão/cobertura previstas (concordância + amostra-ouro
                        + Wilson) → saidas/previsao.txt
```

A lógica de cada etapa e os becos sem saída estão em `docs/` (diário, experimentos,
diagnóstico, decisões manuais, custos, produção) e no relatório.

## Como rodar

Pré-requisitos: **Python 3.12** e chaves de API das 3 famílias.

```bash
# 1) ambiente
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt   # Windows
# (Linux/Mac: .venv/bin/python -m pip install -r requirements.txt)

# 2) chaves — copie .env.example para .env e preencha
#    ANTHROPIC_API_KEY / OPENAI_API_KEY / GOOGLE_API_KEY

# 3) confira os IDs de modelo de cada provedor (opcional, mas recomendado)
.venv\Scripts\python.exe src\classificadores.py --list-models

# 4) teste em 3 questões, depois rode todas
.venv\Scripts\python.exe src\classificadores.py --smoke 3
.venv\Scripts\python.exe src\classificadores.py --all

# 5) gera os entregáveis
.venv\Scripts\python.exe src\juiz.py          # -> saidas/publicacao.csv
.venv\Scripts\python.exe src\estimativa.py    # -> saidas/previsao.txt
```

A amostra-ouro já está rotulada em `docs/amostra_ouro.csv` (seed 42). Para
regenerar a seleção: `src\amostra_ouro.py --n 50 --seed 42` (preserva rótulos).

## Modelos usados

Comitê multi-família para **descorrelacionar erros** (famílias diferentes erram
de formas diferentes). IDs configuráveis por variável de ambiente
(`ANTHROPIC_MODEL` / `OPENAI_MODEL` / `GEMINI_MODEL`); padrões:

| Família | Modelo (padrão) | Observação |
|---|---|---|
| Anthropic | `claude-opus-4-8` | saída estruturada + cache de prompt na árvore; o Opus 4.8 rejeita `temperature` — a reprodutibilidade vem do cache |
| OpenAI | `gpt-5.1` | `temperature=0`, `seed` fixa, JSON schema estrito |
| Google | `gemini-2.5-pro` | `temperature=0`, `response_schema` |

> Confirme os IDs disponíveis na sua conta com `--list-models` e ajuste o `.env`
> se necessário.

## Reprodutibilidade, custo e tempo

- **Cache** (`saidas/cache/`, no `.gitignore`): a resposta crua de cada
  `(questão, modelo, versão_do_prompt)` é salva; nada é re-chamado. Apagar o
  cache força nova execução.
- **Custo/tempo**: ver `docs/custos.md` (preenchido após a execução). A árvore
  (~6,8k tokens) é idêntica nas 359 questões → cache de prompt reduz muito o
  custo repetido.

## Decisões tomadas à mão

Registradas em `docs/decisoes_manuais.md`. As principais:

1. **Excluir os 20 nós sem descrição (67xx)** da lista de candidatos — são
   duplicatas de ramo e módulos de curso "Parte 1/Parte 2", sem histórico; a
   equipe rotulou nos nós canônicos (47xx/5465). → 355 temas selecionáveis.
2. **Ignorar `comando`** (gerado artificialmente) e **não usar
   disciplina/assunto de origem** como rótulo (vêm errados do banco).
3. **Alavanca do tema-pai**: na dúvida entre subtemas irmãos, publicar no tema
   pai (conta como certo para qualquer filho).
4. **Limiares** de publicação (0.80; 0.92 em lixeiras suspeitas) — calibrados
   com a amostra-ouro.
5. **Amostra-ouro** de 50 questões (seed 42), rotulada à mão antes de o comitê
   rodar.

## Estrutura

```
dados/    entrada (questoes.jsonl, temas.csv, LEIA-ME.md, enunciado.pdf)
prompts/  prompts versionados (classificacao_v1.md)
src/      pipeline (normalizar, prompt, classificadores, juiz, estimativa, amostra_ouro)
saidas/   publicacao.csv, previsao.txt, cache/ (respostas cruas)
docs/     registros vivos + relatório
```
