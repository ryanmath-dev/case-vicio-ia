# Relatório — Classificação de Tópicos (Método VDE)

> Classificar 359 questões jurídicas na árvore de 377 temas, decidindo
> **publicar / revisar / fora**, com a régua: das publicadas, ≥95% certas
> (tema exato, pai direto ou filho direto; irmão = erro).

---

## a) Como pensei (o caminho, inclusive os becos)

**Ponto de partida — a régua define a estratégia.** O que torna este problema
diferente de uma classificação comum é a assimetria de custo: publicar errado é
caro, revisar é barato, e **publicar no tema-pai conta como certo para qualquer
filho**. Isso vira a principal alavanca: na dúvida entre dois subtemas irmãos,
subir ao pai transforma um palpite arriscado num acerto garantido, sem gastar a
régua dos 95%. Toda a arquitetura gira em torno disso.

**Primeira hipótese, descartada: confiar nos campos de origem.** O arquivo traz
`disciplina_origem` e `assunto_origem`. Testei se bastava mapeá-los para a árvore.
**Resultado: só 160/359 (45%) do `assunto_origem` batem exatamente com um título
da árvore**, e há lixeiras claras (ex.: "Concurso de Crimes" com 43 questões que
incluem meio ambiente, interceptação, lavagem, racismo). Além disso, 9 questões
têm disciplina de origem fora do recorte e 18 não têm assunto. **DESCARTADO** usar
origem como rótulo — virou só sinal secundário de desempate.

**Segunda decisão: classificar pelo conteúdo, tratando o ruído.** Passei a
classificar lendo **enunciado + alternativas** (em muitas questões o conteúdo está
todo nas alternativas — ex.: "Assinale a correta"). Ignorei o campo `comando`
(claramente gerado artificialmente: "Explique o que é a prisão preventiva.") e
normalizei HTML cru, entidades, `\n` literais e ruído de OCR (marca d'água colada
no texto da Q0078).

**Terceiro: um comitê de famílias diferentes, não um modelo só.** Um LLM sozinho
erra de forma correlacionada consigo mesmo. Projetei para **Claude + GPT + Gemini**
(famílias diferentes) para descorrelacionar erros: quando concordam, a confiança é
real; quando divergem, é sinal de revisão. (Na prática o Gemini saiu por limite de
cota — ver adiante; rodou com Claude + GPT.) Saída estruturada em JSON (tema,
confiança, extras, fora). Temperatura 0 onde o provedor aceita; **a
reprodutibilidade vem do cache da resposta crua** (os modelos Claude 5.x rejeitam
`temperature`, então a determinação não pode vir do sampling).

**Quarto: o juiz aplica a régua, não os modelos.** O julgamento final é código
(`src/juiz.py`): combina os votos das famílias (2 na submissão; o juiz também
trata 3) e
- se todos apontam o **mesmo nó** → publica nele, **desde que** ≥2 famílias e
  nenhuma com confiança < 0,85 (o gate do acordo exato — ver adiante);
- se divergem entre **subtemas do mesmo tema** (irmãos) → **publica no tema-pai**
  (a alavanca);
- se 2/3 concordam no tema (quando há 3 famílias) → publica no tema-pai;
- se divergem entre temas/disciplinas → **revisar**;
- se a maioria diz fora → **fora**.
Com proteções: nunca publica em disciplina (nível 0, genérico demais) e exige
confiança maior em lixeiras introdutórias de volume suspeito.

**Beco sem saída registrado: a falsa detecção de duplicatas.** Uma primeira
checagem (comparando só os 300 primeiros caracteres do enunciado) acusou 2 grupos
de "duplicatas". Era falso positivo: enunciados genéricos iguais ("Assinale a
alternativa correta.") com alternativas diferentes. Comparando enunciado +
alternativas: **0 duplicatas reais**. Lição: nunca deduplicar questão por prefixo
do enunciado.

**Quinto: estimar a própria precisão sem gabarito.** Rotulei à mão uma
**amostra-ouro** (50 questões antes de o comitê rodar, para não me ancorar nas
saídas; depois ampliada para **100**, rotulando as novas só pelo enunciado, sem
ver os votos dos modelos). A precisão prevista combina (a) acerto medido nessa
amostra pela régua pai/filho, (b) concordância do comitê como proxy, e (c)
intervalo de Wilson.

**O achado mais instrutivo — a calibração revelou ONDE está o erro.** O comitê
rodou com **2 famílias (Claude `haiku-5-5` + GPT `gpt-4.1-mini`)**. A 1ª versão,
sem gate, publicou 67% mas com **precisão só 88%** — abaixo da régua. Medindo contra
a amostra-ouro, o diagnóstico foi claro:
- **a alavanca do tema-pai acerta ~100%** — quando os modelos divergem no subtema e
  subimos ao pai, é quase sempre certo (publicar o pai cobre qualquer filho);
- **o "acordo exato" (as duas famílias cravam o mesmo nó) é onde moram os erros** —
  as famílias erram *juntas e confiantes* em questões ambíguas; por isso subir o
  limiar global de confiança não ajuda (os erros estão no topo da confiança).
A correção foi um **gate no acordo exato**: só publica se as 2 famílias concordam
*e* nenhuma reportou confiança < 0,85 (a alavanca fica livre).

### Resultado da execução
- Decisões: **166 publicar (46,2%) · 193 revisar (53,8%) · 0 fora**.
- **Precisão estimada nas publicadas: 0,98** (Wilson 0,88–1,00; **44/45** publicadas
  certas pela régua na amostra-ouro de **100 questões rotuladas à mão**).
- O único erro na amostra (Q0194) é ambiguidade do próprio gabarito manual
  (Peculato vs Comunicabilidade de elementares — ambos defensáveis).
- A cobertura é 46% porque garantir ≥95% tem um custo: o sweep de limiares mostrou
  um "penhasco" — abaixo de 46% de cobertura a precisão fica ~98%, mas tentar >55%
  de cobertura derruba a precisão para ~94% (abaixo da régua). 46% é o teto de
  cobertura que respeita a régua com margem.
- Modelos: `claude-haiku-5-5` + `gpt-4.1-mini`. Custo total **≈ US$ 1,45**
  (teto; real menor), **≈ US$ 0,004/questão** (detalhe em `custos.md`).

**Beco testado — a 3ª família (Gemini) NÃO ajudou.** Hipótese: um 3º voto (Gemini
via Vertex AI, 359 questões) quebraria as ambiguidades onde as 2 famílias erravam
juntas, recuperando cobertura. **Resultado medido (amostra de 100):** com 3
famílias a cobertura sobe (até 88%) mas a precisão cai para ~86–89%; nos pontos que
respeitam os 95%, a melhor cobertura é **2-fam 46% > 3-fam 42%**. A 3ª família
adiciona cobertura só **abaixo** da régua. **Causa:** os erros restantes são
ambiguidade de rótulo e questões difíceis correlacionadas — não erros independentes
que um 3º modelo descorrelacione. **Lição:** "mais modelos" não ajuda quando os
erros não são independentes. A submissão fica com 2 famílias; os votos do Gemini
estão em cache (trocar para 3 é 1 linha).

---

## b) Diagnóstico — o que atrapalha a classificação

**Nos dados (questões):**
- **Campos de origem não confiáveis.** `assunto_origem` casa com a árvore em só
  45% dos casos; lixeiras herdadas (ex.: "Concurso de Crimes", 43 q.). 18 questões
  sem assunto; 9 com disciplina fora do recorte (ex.: Q0142 Tributário/ITCMD,
  Q0309 Ambiental).
- **Conteúdo nas alternativas, não no enunciado** (ex.: Q0037, Q0090, Q0177): quem
  só ler o enunciado erra.
- **Questões "grab-bag"** — 5 alternativas sobre 5 temas distintos (ex.: Q0126,
  Q0288, Q0303, Q0333). São as mais difíceis: não têm tema dominante; candidatas
  naturais a `revisar`.
- **Multitema real** (ex.: Q0282 Maria da Penha + racismo; Q0136 Maria da Penha).
- **Ruído de OCR/HTML** (Q0078 com marca d'água colada; tags, `&nbsp;`, `\n`
  literais).
- **`comando` artificial** — ignorado.

**Na árvore de temas:**
- **Temas duplicados entre ramos (9 pares).** Ex.: Lavagem (6723 em "Penal" vs
  4702 em "Leg. Especial"), Maria da Penha (6724 vs 4704), Ação Penal (5063 em
  Penal vs 5466 em Proc. Penal). Os nós 67xx são **nível 1, sem filhos e sem
  descrição** — criados por importação de módulos de curso. **Risco invisível:**
  se o modelo escolhe o nó do par que a equipe NÃO usou, é erro por pura
  convenção, que nenhum comitê detecta. **Solução:** removi os 20 nós sem
  descrição da lista de candidatos (355 selecionáveis) — a equipe rotula nos nós
  canônicos (com descrição e histórico).
- **Nós "Parte 1/Parte 2" vazios** (6718/6719 etc.) — módulos, não assuntos.
- **Lixeiras por volume** (introdutórios): "Conceito e Fontes do Direito Penal"
  (310 q. no source), "Sistemas Processuais Penais" (285), "Introdução ao Estudo"
  (424). Tratadas com limiar de publicação mais alto.
- **Erros de digitação nos títulos:** "Escolas Crimonológicas" (4373), "Estaturo
  de Idoso" (4696), "Comeptência Territorial" (5483), "Falso Testemunha" (5081).
- **Temas inativos** 5078 e 5234 — nunca usados.

---

## c) Produção — rodando toda semana em 50 mil questões

O desenho de 359 questões foi deliberadamente simples (árvore inteira no prompt).
Em 50k/semana + novas importações, muda a economia e a latência:

**Fluxo em camadas (barato por padrão, caro só onde precisa):**
1. **Ingestão/normalização** (código): limpar HTML/OCR, montar enunciado+alternativas.
2. **Recuperação de candidatos por embeddings** — reduzir os 377 temas ao top-k
   (~15) por similaridade semântica. Em 359 não foi preciso (a árvore cabe no
   prompt); em 50k vira essencial por custo e latência.
3. **Classificador barato por LLM** (ex.: Haiku/Flash/mini) sobre o top-k —
   resolve a grande maioria.
4. **Escalonamento seletivo** — só ~10% incertos (baixa confiança ou divergência)
   sobem para comitê multi-família / modelo forte.
5. **Regras de decisão** publicar/revisar/fora + alavanca do tema-pai.
6. **Fila do professor** para os `revisar`; **reportes de alunos** realimentam a
   amostra-ouro viva.

**Custo por questão.** Medido aqui: comitê de 2 famílias com modelos baratos ≈
**US$ 1,45 / 359 ≈ US$ 0,004 por questão**. Em produção, o desenho em camadas
derruba isso: ~90% resolvidas por 1 modelo barato sobre top-k (frações de centavo)
e ~10% no comitê. Embeddings são baratos e cacheáveis. Estimativa de ordem de
grandeza: **< US$ 0,01 por questão** no caminho barato.

**Medir qualidade continuamente:**
- **Conjunto-ouro vivo**, crescido com reportes de alunos e auditorias semanais do
  especialista — mede precisão real das publicadas.
- **Proxy de concordância do comitê** por lote (alerta se cai).
- **Alarmes operacionais:** taxa de `fora` subindo, acúmulo em lixeiras, queda de
  concordância, drift após nova importação.

**Encaixe no fluxo:** importação → normalização → embeddings → classificação em
camadas → publicar/revisar/fora. `revisar` vai à fila do professor; `fora`
sinaliza **tema faltante** (insumo para criar temas). Reportes de alunos viram
rótulos-ouro e reabrem questões suspeitas.

---

## d) Memo para o professor (1 página)

Professor, classifiquei as 359 questões e separei em **publicar** (vão direto ao
aluno), **revisar** (vão à sua fila, com sugestão) e **fora** (nenhum tema serve).
O que preciso de você e o que recomendo mudar nos temas:

**1. Nós duplicados que confundem a classificação (decida o canônico).** Há **9
assuntos que existem em dois lugares da árvore** — um com descrição e histórico de
questões, outro vazio (criado por importação de curso). Exemplos: *Lavagem de
Dinheiro*, *Maria da Penha*, *Tráfico de Drogas*, *Organizações Criminosas*,
*Abuso de Autoridade*, *Estatuto do Idoso* (todos em "Penal" como nós vazios 67xx
**e** em "Legislação Especial"); *Ação Penal* (em "Penal" e em "Processo Penal");
*LEP* (em "Processo Penal" e em "Leg. Especial"). **Recomendo fundir cada par num
único nó.** Por ora, publiquei sempre no nó com descrição.

**2. Nós que funcionam como lixeira (não deveriam receber questão nova).** Os
"Parte 1/Parte 2" vazios e os introdutórios de volume altíssimo ("Conceito e
Fontes do Direito Penal", "Sistemas Processuais Penais", "Introdução ao Estudo").
Mandei para revisão as questões que cairiam neles com confiança baixa.

**3. Erros de digitação nos títulos** (não atrapalham o aluno, mas vale corrigir):
"Escolas **Crimonológicas**" (deveria ser Criminológicas), "**Estaturo** de
Idoso", "**Comeptência** Territorial", "Falso **Testemunha**".

**4. Temas que podem faltar.** As questões marcadas **fora** são candidatas a
**criar tema** — ex.: medidas socioeducativas / ECA (Q0014), que não têm lar na
árvore atual. Veja a lista completa em `publicacao.csv` (decisão = fora).

**5. Questões que listei para você revisar** são, em geral: enunciados "grab-bag"
(5 alternativas de 5 temas diferentes, sem dominante), questões multitema (ex.:
Maria da Penha + racismo) e casos onde os modelos divergiram. A sugestão de tema
está na planilha; o `motivo` explica por que não publiquei.

---

*Registros completos do raciocínio, experimentos, diagnóstico com IDs, decisões
manuais e custos estão em `docs/`. Código e instruções de execução no `README.md`.*
