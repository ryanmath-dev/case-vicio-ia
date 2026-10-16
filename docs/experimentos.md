# Experimentos (log com números)

> Versão quantitativa do diário. Toda rodada que produz um número entra aqui.
> Alimenta a Seção (a) do relatório.

| # | Data | Hipótese | Setup (modelo/prompt/amostra) | Métrica | Resultado | Conclusão |
|---|------|----------|-------------------------------|---------|-----------|-----------|
| 0 | 2026-10-14 | assunto_origem serve de rótulo | match exato título↔árvore, n=359 | % match | 160/359 (45%) | DESCARTADO |
| 1 | 2026-10-15 | Comitê 2 famílias sem gate publica bem | Claude haiku-5-5 + GPT 4.1-mini, juiz régua+alavanca | prec. gold / cobertura | 26/30 = 0.867 / 67.1% | ABAIXO da régua (95%) |
| 2 | 2026-10-15 | Alavanca do tema-pai é segura | separar publicadas da amostra por tipo de acordo | prec. por tipo | alavanca 7/7=1.00; acordo-exato 19/4=0.826 | CONFIRMADO: erro mora no acordo exato |
| 3 | 2026-10-15 | Gate de confiança no acordo exato atinge a régua | exigir min(conf dos modelos)≥limiar só no acordo exato | prec. gold / cobertura | 0.85→0.952(20/21)/46.5% · 0.90→1.00(12/12)/35.4% | MANTIDO limiar 0.85 |
| 4 | 2026-10-15 | 3ª família (Gemini/Vertex) recupera cobertura mantendo 95% | adicionar gemini-2.5-flash (359 votos), re-calibrar | prec. gold / cobertura | sem gate: 0.854/88% · gate global 0.85: 0.95/41.8% · unanimidade 0.85: 0.952/43.5% | **DESCARTADO**: 3 famílias NÃO melhoram a fronteira (mais cobertura só com menos precisão) |
| 5 | 2026-10-15 | Comparação dos pontos a 95% | melhor cobertura sujeito a prec.≥95% | cobertura | 2-fam 46.5% > 3-fam-unân 43.5% > 3-fam-global 41.8% | MANTIDO 2 famílias na submissão |
| 6 | 2026-10-16 | Amostra-ouro n=50 subestima a precisão | ampliar p/ n=100, re-medir | prec. gold (2-fam gate 0.85) | 0.95 (n=50) → **0.978 (44/45, n=100)** [0.88-1.00] | CONFIRMADO: régua atendida c/ margem |
| 7 | 2026-10-16 | Existe ponto >46% cobertura com ≥95%? | sweep fino do gate (2 fam), n=100 | prec / cobertura | 0.70→0.948/59.6% · 0.80→0.946/54.3% · 0.82→0.978/46.2% | NÃO: "penhasco"; 46% é o teto p/ ≥95% |
| 8 | 2026-10-16 | 3 famílias melhoram a fronteira (n=100)? | re-medir 3-fam vs 2-fam | melhor cobertura a ≥95% | 2-fam 46.2% > 3-fam-global 41.8% | DESCARTADO: 3ª família não ajuda |

## Notas de métrica
- **Precisão (publicadas):** fração das publicadas corretas pela régua (tema exato
  ou pai/filho). Estimada (sem gabarito) via amostra-ouro + concordância.
- **Cobertura:** fração das 359 publicadas.
- **Proxy de concordância:** fração de pares de famílias cujos nós caem no mesmo
  ramo (pai/filho). Na submissão (2 famílias) é simplesmente se as duas concordam
  por ramo.
- Intervalos: Wilson (proporção) ou bootstrap.
