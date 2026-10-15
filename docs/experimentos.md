# Experimentos (log com números)

> Versão quantitativa do diário. Toda rodada que produz um número entra aqui.
> Alimenta a Seção (a) do relatório.

| # | Data | Hipótese | Setup (modelo/prompt/amostra) | Métrica | Resultado | Conclusão |
|---|------|----------|-------------------------------|---------|-----------|-----------|
| 0 | 2026-10-14 | assunto_origem serve de rótulo | match exato título↔árvore, n=359 | % match | 160/359 (45%) | DESCARTADO |
| 1 | 2026-10-15 | Comitê 2 famílias sem gate publica bem | Claude haiku-5-5 + GPT 4.1-mini, juiz régua+alavanca | prec. gold / cobertura | 26/30 = 0.867 / 67.1% | ABAIXO da régua (95%) |
| 2 | 2026-10-15 | Alavanca do tema-pai é segura | separar publicadas da amostra por tipo de acordo | prec. por tipo | alavanca 7/7=1.00; acordo-exato 19/4=0.826 | CONFIRMADO: erro mora no acordo exato |
| 3 | 2026-10-15 | Gate de confiança no acordo exato atinge a régua | exigir min(conf dos modelos)≥limiar só no acordo exato | prec. gold / cobertura | 0.85→0.952(20/21)/46.5% · 0.90→1.00(12/12)/35.4% | MANTIDO limiar 0.85 (interino 2 famílias) |

## Notas de métrica
- **Precisão (publicadas):** fração das publicadas corretas pela régua (tema exato
  ou pai/filho). Estimada (sem gabarito) via amostra-ouro + concordância.
- **Cobertura:** fração das 359 publicadas.
- **Proxy de concordância:** % de questões em que ≥2 das 3 famílias caem no mesmo
  ramo (pai/filho).
- Intervalos: Wilson (proporção) ou bootstrap.
