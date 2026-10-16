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
 [3] classificadores.py COMITÊ de 2 famílias (Claude + GPT), saída JSON, resposta
                        crua salva em saidas/cache/ (reprodutível). Gemini foi
                        testado como 3ª família (ver docs) mas não entrou.
                      ▼
 [4] juiz.py            combina os votos: régua pai/filho + alavanca do tema-pai +
                        gate de confiança + proteção de lixeiras → publicacao.csv
                      ▼
 [5] estimativa.py      precisão/cobertura previstas (concordância + amostra-ouro
                        + Wilson) → saidas/previsao.txt
```

A lógica de cada etapa e os becos sem saída estão em `docs/` (diário, experimentos,
diagnóstico, decisões manuais, custos, produção) e no relatório.

## Como rodar

Pré-requisitos: **Python 3.12** e chaves de API das 2 famílias da submissão
(Anthropic + OpenAI). O Gemini é opcional (só para reproduzir o experimento da 3ª
família) e usa Vertex AI.

```bash
# 1) ambiente
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt   # Windows
# (Linux/Mac: .venv/bin/python -m pip install -r requirements.txt)

# 2) chaves — copie .env.example para .env e preencha
#    ANTHROPIC_API_KEY / OPENAI_API_KEY  (obrigatórias p/ a submissão)
#    Gemini (opcional, experimento): GEMINI_BACKEND=vertex +
#    GOOGLE_CLOUD_PROJECT + GOOGLE_APPLICATION_CREDENTIALS (service account)

# 3) confira os IDs de modelo de cada provedor (recomendado — evita IDs inválidos)
.venv\Scripts\python.exe src\classificadores.py --list-models

# 4) teste em 3 questões, depois rode todas (comitê de 2 famílias por padrão)
.venv\Scripts\python.exe src\classificadores.py --smoke 3
.venv\Scripts\python.exe src\classificadores.py --all

# 5) gera os entregáveis
.venv\Scripts\python.exe src\juiz.py          # -> saidas/publicacao.csv
.venv\Scripts\python.exe src\estimativa.py    # -> saidas/previsao.txt
```

A amostra-ouro já está rotulada em `docs/amostra_ouro.csv` (**100 questões**,
seed 42 + 123). Para regenerar/expandir a seleção use `src\amostra_ouro.py`
(preserva rótulos existentes).

## Modelos usados

Comitê multi-família para **descorrelacionar erros** (famílias diferentes erram
de formas diferentes). IDs configuráveis por variável de ambiente
(`ANTHROPIC_MODEL` / `OPENAI_MODEL` / `GEMINI_MODEL`); padrões (validados via
`--list-models` — os palpites iniciais `gpt-5.1`/`gemini-2.5-pro` não existiam):

| Família | Modelo (padrão) | Papel | Observação |
|---|---|---|---|
| Anthropic | `claude-haiku-5-5` | submissão | saída estruturada + cache de prompt na árvore; modelos Claude 5.x rejeitam `temperature` — a reprodutibilidade vem do cache |
| OpenAI | `gpt-4.1-mini` | submissão | `temperature=0`, `seed` fixa, JSON schema estrito |
| Google | `gemini-2.5-flash` (via Vertex AI) | experimento | 3ª família testada; **não entrou** na submissão (não melhorou a fronteira da régua — ver `docs/`) |

> Modelos escolhidos **baratos** de propósito: o case diz que usar o modelo mais
> caro não pesa; quem faz o trabalho é a régua + alavanca + comitê. Custo real
> ~US$1,45 nas 359. Confirme os IDs disponíveis na sua conta com `--list-models`.

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
4. **Gate de confiança no acordo exato** (`MIN_CONF_EXATO=0.85`): a calibração na
   amostra-ouro mostrou que os erros moram no "acordo exato" das famílias; só
   publicar nó específico quando ambas concordam E nenhuma hesita. Limiares de
   lixeira (0.80/0.92) também calibrados.
5. **Comitê de 2 famílias** (Claude+GPT): o Gemini (3ª família, via Vertex) foi
   testado mas não melhorou a fronteira da régua (ver `docs/experimentos.md`).
6. **Amostra-ouro** de 100 questões (seed 42 + 123), rotulada à mão (as 50
   iniciais antes de o comitê rodar; as +50 lendo só o enunciado, sem ver as
   saídas dos modelos) → medição imparcial.

## Estrutura

```
dados/    entrada (questoes.jsonl, temas.csv, LEIA-ME.md, enunciado.pdf)
prompts/  prompts versionados (classificacao_v1.md)
src/      pipeline (normalizar, prompt, classificadores, juiz, estimativa, amostra_ouro)
saidas/   publicacao.csv, previsao.txt, cache/ (respostas cruas)
docs/     registros vivos + relatório
```
