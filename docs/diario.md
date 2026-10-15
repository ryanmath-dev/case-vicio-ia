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

<!-- PRÓXIMAS ENTRADAS ABAIXO -->
