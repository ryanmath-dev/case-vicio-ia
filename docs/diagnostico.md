# Diagnóstico dos dados e da árvore de temas

> O que atrapalha uma máquina (ou um humano) a classificar certo.
> SEMPRE com IDs de exemplo. Alimenta a Seção (b) e o Memo ao professor (d).
> Marcar cada achado: [CONFIRMADO] (visto nos dados) / [A VERIFICAR].

## A. Defeitos nas QUESTÕES

### A1. `assunto_origem` não é confiável — lixeiras [CONFIRMADO]
- Só 160/359 batem exatamente com um título da árvore.
- Lixeira clara: **"Concurso de Crimes" (43 q.)** acumula temas alheios —
  ex.: Q0010 (meio ambiente), Q0011 (interceptação/lavagem), Q0051 (racismo),
  Q0062 (extraterritorialidade), Q0078 (Estatuto do Desarmamento).

### A2. `disciplina_origem` trocada ou fora do recorte [CONFIRMADO]
- Q0142 → "Direito Tributário" (ITCMD): forte candidata a **fora**.
- Q0014 → "Disciplina Unificada" / medidas socioeducativas (ECA).
- Q0016, Q0218 → "Direito Constitucional" mas tratam de prisão/doc. falso.
- Q0137, Q0277 → "Direito Civil - Legislação Especial" (investigação; crime c/ idoso).
- Q0169 → "Direito Processual Penal" (rótulo redundante), Q0309 → "Direito Ambiental".

### A3. Questões sem `assunto_origem` (18) [CONFIRMADO]
- Ex.: Q0016, Q0024, Q0035, Q0036, Q0070, Q0137, Q0170, Q0187, Q0203, Q0218,
  Q0289, Q0293, Q0304, Q0318, Q0327, Q0345, Q0348. Q0036 também sem disciplina.

### A4. Enunciados "vazios" — conteúdo todo nas alternativas [CONFIRMADO]
- Ex.: Q0037, Q0090, Q0177, Q0192, Q0205, Q0239, Q0333, Q0339 ("Assinale a
  alternativa correta." + alternativas de temas variados). Classificador TEM de
  ler as alternativas, não só o enunciado.

### A5. Questões multitema [CONFIRMADO]
- Q0282 (Maria da Penha + racismo), Q0222 (direito penal do inimigo + JECRIM).
  Candidatas a `revisar` ou a usar `extras_ids`.

### A6. Ruído de OCR / HTML cru [CONFIRMADO]
- Ex.: Q0078 ("EM oossstomnioconcunsos..."), "\n" literais, tags <br>, &nbsp;,
  <i>/<span>. Normalizar antes de classificar.

### A7. Campo `comando` artificial [CONFIRMADO]
- Ex.: "Explique o que é a prisão preventiva." (Q0033). Parece gerado; IGNORAR.

### A8. Formatos mistos de questão [CONFIRMADO]
- 255 com 5 alternativas, 46 com 4, 58 Certo/Errado (estilo Cespe).

### A9. Duplicatas [CONFIRMADO]
- Grupo 1: Q0037, Q0172, Q0331, Q0354. Grupo 2: Q0090, Q0205, Q0222, Q0268,
  Q0282, Q0299, Q0321, Q0333, Q0339. (Verificar se é duplicata real ou colisão
  de prefixo na deduplicação.)

## B. Defeitos na ÁRVORE DE TEMAS

### B1. Temas duplicados entre disciplinas [CONFIRMADO]
- Aparecem em "Penal" (nós 67xx, SEM descrição) e também em "Legislação Especial":
  Lavagem (6723 vs 4702), Maria da Penha (6724 vs 4704), Tráfico de Drogas
  (6728 vs 4708), Organizações Criminosas (6725 vs 4705), Abuso de Autoridade
  (6716 vs 4684), Meio Ambiente (6717 vs 4688). LEP em Proc. Penal (6734) e em
  Leg. Especial (4703). → Precisa decidir o nó canônico.

### B2. Nós "Parte 1/Parte 2" vazios e sem descrição [CONFIRMADO]
- Ex.: 6718/6719 (Adm. Pública), 6720/6721 (Patrimônio), 6726/6727 (Teoria da
  Pena), 6732/6733 (Competência), 6737/6738 (Sentença), 6735/6736 (Provas/
  Recursos). Parecem módulos de curso, não assuntos. Candidatos a lixeira — não
  publicar neles.

### B3. Lixeiras por volume (contagem na própria descrição) [A VERIFICAR]
- "Conceito e Fontes do Direito Penal" (310), "Sistemas Processuais Penais" (285),
  "Princípios do Processo Penal" (253), "Lei penal no Tempo" (227), "Conceitos e
  Espécies de Prisão" (209). Volumes altos demais para temas introdutórios —
  tratar com cautela ao publicar.

### B4. Temas inativos [CONFIRMADO]
- 5078 (Direito penal econômico), 5234 (Tratados e convenções). NUNCA usar.

### B5. Erros de digitação nos títulos [CONFIRMADO]
- "Escolas Crimonológicas" (4373), "Estaturo de Idoso" (4696), "Comeptência
  Territorial" (5483), "Falso Testemunha" (5081). Não afeta classificação, mas
  entra no memo ao professor.

## C. Implicações para a estratégia
- Régua pai/filho + irmão=erro ⇒ subir ao tema pai quando a dúvida é entre irmãos.
- Lixeiras (B2/B3) ⇒ nelas, preferir `revisar` a `publicar`.
- A3/A4/A5 ⇒ fortes candidatas a `revisar`.
- A2 extremos (Q0142) ⇒ `fora`.
