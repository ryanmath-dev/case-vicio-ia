# Custos, tokens e tempo

> Alimenta o README e a Seção (c). Registrar por etapa/modelo.
> Preços de referência (out/2026, por 1M tokens, entrada/saída):
>   Claude Haiku 5.5: 0,10 / 0,50  | Sonnet 5.5: 2 / 10  | Opus 5.5: 4 / 20
>   GPT-6 Luna: 0,10 / 0,50        | GPT-6 Sol: 2 / 10
>   Gemini 3.8 Flash: 0,75 / 3,75 (promo)
> Batch API: -50%. Cache de leitura reduz muito o custo da árvore repetida.

## Modelos escolhidos (restrição real: US$5 na OpenAI + US$5 na Anthropic)
O case diz que "usar o modelo mais caro não pesa"; a régua + alavanca do tema-pai
+ acordo de 3 famílias é que fazem o trabalho. Então escolhi modelos **baratos e
capazes** por família, não os topos de linha:

| Família | Modelo | Preço in/out (1M) | Por quê |
|---|---|---|---|
| Anthropic | `claude-haiku-4-5` (planejado) | 1 / 5 | Opus 4.8 daria ~$3,3/359 (perto do limite). Haiku é seguro. Chave `usr` sem workspace — pendente. |
| OpenAI | `gpt-4.1-mini` | 0,40 / 1,60 | API previsível (JSON schema+temp+seed); `gpt-5.1` nem existe na conta. |
| Google | `gemini-3.8-flash` | tier AI Studio | `gemini-2.5-flash` descontinuado p/ novos usuários. |

## Medições (smoke, 1 questão)
| Modelo | Tokens in | Tokens out |
|---|---|---|
| gpt-4.1-mini | 8.567 | 106 |
| gemini-3.8-flash | 9.026 | 126 |

## Projeção para 359 questões (por provedor)
- **OpenAI gpt-4.1-mini**: ~359×8,6k in ≈ 3,1M tokens. Com cache de prefixo
  automático (árvore idêntica), estimativa **≈ US$0,5**. Output irrisório.
- **Gemini 3.8-flash**: tier do AI Studio (grátis/baixo) → **≈ US$0**.
- **Anthropic Haiku 4.5** (quando a chave funcionar): com prompt caching na árvore,
  **≈ US$0,6** (bem abaixo dos $5).
- **Total previsto do comitê ≈ US$1,1** — dentro do orçamento com folga.

## Custo REAL do run (359 questões, 2 famílias)
Calculado do `usage` salvo no cache (`tmp/custo.mjs`):

| Família | Modelo | Chamadas | Tokens in | Tokens out | Cache read | Custo US$ |
|---|---|---|---|---|---|---|
| Anthropic | claude-haiku-5-5 | 359 | 145.868 | 198.195 | 5.070.828 | **0,168** |
| OpenAI | gpt-4.1-mini | 359 | 3.083.637 | 31.706 | (n/d*) | **~1,284** |
| Gemini | gemini-3.8-flash | 13 | — | — | — | 0 (free, cota) |

\* não capturei `cached_tokens` da resposta OpenAI → o $1,28 é **sem** o desconto
de cache de prefixo (superestimado; real provavelmente ~$0,7–1,0).

- **Custo total ≈ US$ 1,45** (teto; real menor). **Por questão ≈ US$ 0,004**.
- **Tempo:** OpenAI 438s; Anthropic ~1.090s (1ª passada) + 173s (25 reprocessadas).
- O prompt caching da Anthropic foi decisivo: 5,07M tokens lidos do cache a 0,1× —
  por isso o Anthropic saiu a só US$0,17 apesar de 359 chamadas.
- Folga enorme no orçamento (US$5+US$5): dá p/ adicionar o Gemini (3ª família) e
  ainda re-rodar várias vezes.
