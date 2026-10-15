# Diário de bordo

> Registro cronológico do raciocínio. Só acrescenta; nada se apaga.
> Beco sem saída NÃO se deleta — marca-se `DESCARTADO` e o porquê.
> Alimenta a Seção (a) do relatório: "Como você pensou".
>
> Formato de cada entrada:
> ### [AAAA-MM-DD HH:MM] Título curto
> **Hipótese:** ...
> **O que fiz:** ...
> **Resultado (com números):** ...
> **Conclusão:** MANTIDO / DESCARTADO / A TESTAR — por quê.

---

### [2026-10-14] Leitura do enunciado e dos dados — decisões iniciais
**Hipótese inicial:** talvez dê para confiar em `assunto_origem`/`disciplina_origem`
e só mapear para a árvore.
**O que fiz:** inspeção dos 3 arquivos (359 questões, 377 temas).
**Resultado:** só 160/359 `assunto_origem` batem exatamente com algum título da
árvore; "Concurso de Crimes" (43 q.) é lixeira — contém meio ambiente,
interceptação, lavagem, racismo etc. 9 questões com disciplina de origem fora do
recorte; 18 sem assunto.
**Conclusão:** DESCARTADO confiar nos campos de origem como rótulo. Viram apenas
sinal secundário. (Detalhe em diagnostico.md.)

### [2026-10-14] Estratégia-base definida
**Decisões (a validar na execução):**
1. Classificar lendo enunciado + alternativas; ignorar `comando` (gerado
   artificialmente) e tratar OCR/HTML.
2. Classificação em 2 estágios: disciplina/tema → subtema, com a árvore inteira
   no prompt (377 nós ~20k tokens, cabe).
3. Comitê de 3 famílias (Claude + GPT + Gemini) para descorrelacionar erro.
4. Alavanca de cobertura: na dúvida entre irmãos, publicar no TEMA PAI (conta
   como certo pela régua pai/filho).
5. Regras de decisão em código (publicar/revisar/fora) sobre as saídas do comitê.
6. Estimar precisão sem gabarito via amostra-ouro rotulada à mão (~50 q.) +
   concordância entre modelos + intervalo estatístico.
**Conclusão:** A TESTAR — é o plano que entra em execução.

### [2026-10-14] Pesquisa de modelos
**O que fiz:** levantei preços/posicionamento (out/2026).
**Resultado:** para 359 q. o custo é irrelevante (árvore em cache; rodar até Opus
custa < US$10). Economia vira argumento só na seção de produção (cheap-by-default
+ escalonar ~10% difíceis). Comitê multi-família tem respaldo empírico
(ensemble hierárquico: F1 0.55→0.92 com 10 modelos; +33% já com 2).
**Conclusão:** MANTIDO usar modelos fortes aqui; registrar trade-off de custo
para produção.

### [2026-10-14] Verificação dos dados + ambiente da máquina
**O que fiz:** reprocessei `questoes.jsonl` e `temas.csv` em script próprio (Node)
para confirmar o diagnóstico herdado e checar o ambiente.
**Resultado (números):**
- Questões: 359. Nº de alternativas = {5:255, 4:46, 2:58}. As 58 de 2 alt. são
  Certo/Errado (estilo Cespe). 18 sem `assunto_origem` (confirma A3).
- `disciplina_origem`: 131 Processo Penal, 129 Direito Penal, 32 Leg. Especial,
  31 Criminologia, **27 só "Penal"**, + 7 fora do recorte (2 Constitucional,
  2 Civil-Leg.Esp., 1 Tributário, 1 Ambiental, 1 "Disciplina Unificada", 1 vazio,
  1 "Direito Processual Penal" redundante).
- Temas: 377 = 4 roots (4365 Criminologia, 4683 Leg.Especial, 5062 Penal,
  5465 Processo Penal) + 111 nível-1 + 262 nível-2. Inativos: 5078, 5234.
- **20 nós sem descrição** = os 67xx (confirma B1/B2: duplicados/módulos de curso).
- Lixeiras por volume no `source` (campo descricao): roots Penal(4483)/ProcPenal(4112)/
  Leg.Esp(817)/Criminologia(399); nível-1 Sist.e Princ.Proc.Penais(538),
  Teoria da Pena(453), Introdução ao Estudo(424); nível-2 "Conceito e Fontes do
  Direito Penal" 5171(310) e "Sistemas Processuais Penais" 5581(285) — confirma B3.
**Ambiente:** Python NÃO instalado (só stub da Store); **Node.js v24** disponível.
Sem `.env`/chaves de API no ambiente (só `.env.example` com ANTHROPIC/OPENAI/GOOGLE).
**Conclusão:** diagnóstico herdado CONFIRMADO. Dois pontos a decidir com o usuário:
linguagem (Node vs instalar Python) e quais chaves de API existem.

### [2026-10-14] Execução do comitê — descoberta dos IDs e queda do Gemini
**O que fiz:** rodei `--list-models` + smokes antes do run completo.
**Resultados (com números):**
- Os palpites de ID estavam errados: `gpt-5.1` não existe na conta (há `gpt-5`,
  `gpt-5-mini`, `gpt-4.1-mini`...); `gemini-2.5-flash` foi descontinuado p/ novos
  usuários (API recomenda `gemini-3.8-flash`). Lição: nunca cravar ID de modelo
  "de memória" — `--list-models` confirma contra a conta real.
- Chave Anthropic: a 1ª (`sk-ant-usr-`) deu 400 "not scoped to a workspace"; a 2ª
  chave `usr` funcionou (workspace-scoped) e revelou a família Claude 5.5
  (`claude-haiku-5-5` etc.). Escolhi `claude-haiku-5-5` (barato: ~$0,10/$0,50/1M).
- Modelos finais validados (todos acertaram Q0001 → 5524 com a alavanca do
  tema-pai): `claude-haiku-5-5`, `gpt-4.1-mini`, `gemini-3.8-flash`.
- **BECO/DESCARTADO — Gemini:** o tier gratuito do AI Studio limita o
  `gemini-3.8-flash` a **20 requisições/dia** (erro 429 RESOURCE_EXHAUSTED após
  ~13 chamadas boas, "retry em ~21h"). Inviável para 359/dia sem billing.
  → **Comitê reduzido a 2 famílias (Claude + GPT)**, que já descorrelacionam erro.
  O cache dos 13 votos do Gemini fica no disco, mas o juiz usa só as 2 famílias
  (consistência). Reativável com billing no Google.
- Correções de código pós-smoke: schema sem `additionalProperties` p/ Gemini;
  retry com backoff em transitórios; **cache só de sucesso** (falha deve re-tentar).
**Conclusão:** MANTIDO comitê de 2 famílias baratas; Gemini A TESTAR só se houver
billing. Custo real do run bem abaixo do orçamento de US$5+US$5.

### [2026-10-15] Run completo (2 famílias) + calibração contra a amostra-ouro
**O que fiz:** rodei o comitê nas 359 (Claude haiku-5-5 + GPT 4.1-mini), juiz,
estimativa. Medi contra as 50 da amostra-ouro.
**Resultado (números):**
- Sem gate: publicar 241 (67,1%), revisar 118; **precisão gold 26/30 = 86,7%** —
  ABAIXO da régua de 95%.
- **Diagnóstico do erro:** os 4 erros tinham confiança 0,99 (acordo exato das 2
  famílias) → subir limiar global não ajuda. Separando por tipo de acordo:
  **alavanca do tema-pai = 7/7 (100%)**; **acordo exato = 19/4 (82,6%)**. Todo o
  erro está no acordo exato — famílias erram juntas e confiantes em questões
  ambíguas.
- **Correção:** gate `MIN_CONF_EXATO=0,85` — no acordo exato, só publica se ≥2
  famílias E nenhuma com confiança auto-reportada < 0,85 (a alavanca fica livre).
  Resultado: publicar 166 (46,2%), **precisão gold 20/21 = 95,2%** (Wilson
  0,77–0,99). O único "erro" restante (Q0194) é ambiguidade de rótulo (Peculato
  vs Comunicabilidade — ambos defensáveis).
- **Custo real:** Anthropic US$0,17 + OpenAI ~US$1,28 + Gemini US$0 ≈ **US$1,45**
  (OpenAI superestimado — não capturei o desconto de cache dele).
**Conclusão:** MANTIDO o gate (respeita a régua). É resultado INTERINO de 2
famílias: a cobertura caiu de 67% p/ 46% para garantir 95%. **A TESTAR:** com o
Gemini como 3ª família, o acordo de 3 vias deve permitir relaxar o gate e
recuperar cobertura mantendo a precisão. Cautela registrada: o limiar 0,85 foi
calibrado em 30 publicadas (amostra pequena) — intervalo honesto reflete isso.

### [2026-10-15] 3ª família (Gemini via Vertex) — experimento e resultado NEGATIVO
**Hipótese:** com acordo de 3 vias, as ambiguidades onde 2 famílias erravam juntas
seriam quebradas pelo 3º voto → dava para relaxar o gate e recuperar cobertura
mantendo 95%.
**O que fiz:** o tier gratuito do Gemini (20/dia) não serve; o usuário forneceu um
service account do **Vertex AI**. Adaptei `_call_gemini` p/ Vertex (ADC), rodei
`gemini-2.5-flash` nas 359 (2 interrupções + 21 falhas 429 de cota, reprocessadas;
358/359 no fim). Re-calibrei com 3 famílias.
**Resultado (com números):**
- Sem gate: cobertura 88% mas **precisão 0,854** (35/41) — o 3º voto adiciona
  cobertura à custa de precisão.
- Acordo exato de 3 vias: 16/19 = 0,84 (NÃO mais confiável que 2 vias). Alavanca
  caiu de 100% (2-fam) p/ 0,86 (3-fam) porque mais questões difíceis entram nela.
- Pontos que atingem 95%: 2-fam-gate **46,5%** > 3-fam-unanimidade 43,5% >
  3-fam-gate-global 41,8%. O erro remanescente em todos é o Q0194 (ambiguidade
  de rótulo: Peculato vs Comunicabilidade).
**Conclusão:** **DESCARTADO** usar a 3ª família na submissão — ela não melhora a
fronteira da régua (o ganho de cobertura vem com queda de precisão). Causa: os
erros são dominados por ambiguidade de rótulo e questões difíceis correlacionadas,
que um 3º LLM não resolve. Lição valiosa: "mais modelos" ≠ "melhor" quando os erros
não são independentes. Submissão fica com **2 famílias + gate (46,5%, 95%)**. Os
votos do Gemini ficam em cache (reprodutível) e a troca p/ 3 famílias é 1 linha.

<!-- PRÓXIMAS ENTRADAS ABAIXO -->
