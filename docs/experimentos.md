# Experimentos (log com números)

> Versão quantitativa do diário. Toda rodada que produz um número entra aqui.
> Alimenta a Seção (a) do relatório.

| # | Data | Hipótese | Setup (modelo/prompt/amostra) | Métrica | Resultado | Conclusão |
|---|------|----------|-------------------------------|---------|-----------|-----------|
| 0 | 2026-10-14 | assunto_origem serve de rótulo | match exato título↔árvore, n=359 | % match | 160/359 (45%) | DESCARTADO |
|   |      |          |                               |         |           |           |

## Notas de métrica
- **Precisão (publicadas):** fração das publicadas corretas pela régua (tema exato
  ou pai/filho). Estimada (sem gabarito) via amostra-ouro + concordância.
- **Cobertura:** fração das 359 publicadas.
- **Proxy de concordância:** % de questões em que ≥2 das 3 famílias caem no mesmo
  ramo (pai/filho).
- Intervalos: Wilson (proporção) ou bootstrap.
