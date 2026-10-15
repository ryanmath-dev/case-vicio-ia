"""
Estágio 5 — estimar a própria precisão SEM gabarito e gerar previsao.txt.

Combina três sinais (CLAUDE.md §9):
  (a) CONCORDÂNCIA do comitê como proxy de precisão nas publicadas;
  (b) ACERTO medido na AMOSTRA-OURO rotulada à mão (docs/amostra_ouro.csv),
      pela régua pai/filho;
  (c) INTERVALO por Wilson (proporção) na amostra-ouro.

Gera saidas/previsao.txt no formato do dados/LEIA-ME.md.

Uso:
  .venv\\Scripts\\python.exe src\\estimativa.py
"""
from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from normalizar import ArvoreTemas, carregar_temas  # noqa: E402
from classificadores import PROVIDERS, VERSAO_PROMPT, _cache_path, _ler_cache, _DISPATCH  # noqa: E402
from juiz import tema_pai  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PUBLICACAO = ROOT / "saidas" / "publicacao.csv"
AMOSTRA = ROOT / "docs" / "amostra_ouro.csv"
SAIDA = ROOT / "saidas" / "previsao.txt"


# =============================================================================
# Intervalo de Wilson
# =============================================================================
def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    """Retorna (p_hat, low, high) do intervalo de Wilson para k sucessos em n."""
    if n == 0:
        return (0.0, 0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    center = (p + z * z / (2 * n)) / d
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d
    return (p, max(0.0, center - half), min(1.0, center + half))


# =============================================================================
# Concordância do comitê (proxy)
# =============================================================================
def concordancia_por_ramo(arvore: ArvoreTemas, qid: str) -> float | None:
    """Fração de pares de modelos cujos nós caem no mesmo ramo (régua pai/filho).
    None se houver menos de 2 votos dentro da árvore."""
    nos = []
    for prov in PROVIDERS:
        r = _ler_cache(_cache_path(qid, prov, _DISPATCH[prov][1](), VERSAO_PROMPT))
        if r and r.ok and r.parsed and not r.parsed.get("fora"):
            tid = str(r.parsed.get("tema_central_id") or "").strip()
            if arvore.get(tid):
                nos.append(tid)
    if len(nos) < 2:
        return None
    pares = okok = 0
    for i in range(len(nos)):
        for j in range(i + 1, len(nos)):
            pares += 1
            if arvore.ramo_valido(nos[i], nos[j]):
                okok += 1
    return okok / pares if pares else None


# =============================================================================
# Carregamento de publicacao + amostra-ouro
# =============================================================================
def ler_publicacao() -> list[dict]:
    if not PUBLICACAO.exists():
        return []
    with PUBLICACAO.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ler_amostra() -> dict[str, str]:
    """id -> tema_ouro (rótulo manual). Ignora linhas sem rótulo."""
    if not AMOSTRA.exists():
        return {}
    out = {}
    with AMOSTRA.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ouro = (row.get("tema_ouro") or "").strip()
            if ouro:
                out[row["id"].strip()] = ouro
    return out


# =============================================================================
# Estimativa
# =============================================================================
def estimar() -> str:
    arvore = carregar_temas()
    pub = ler_publicacao()
    if not pub:
        return "ERRO: saidas/publicacao.csv não existe. Rode src/juiz.py primeiro."

    n_total = len(pub)
    publicadas = [r for r in pub if r["decisao"] == "publicar"]
    n_pub = len(publicadas)
    cobertura = n_pub / n_total if n_total else 0.0

    # --- (a) concordância média do comitê nas publicadas ---
    concs = [c for r in publicadas if (c := concordancia_por_ramo(arvore, r["id"])) is not None]
    conc_media = sum(concs) / len(concs) if concs else None

    # --- (b)/(c) acerto na amostra-ouro, restrito às publicadas ---
    ouro = ler_amostra()
    pub_por_id = {r["id"]: r for r in publicadas}
    acertos = n_av = 0
    erros_ex = []
    for qid, tema_ouro in ouro.items():
        r = pub_por_id.get(qid)
        if not r:
            continue  # não foi publicada → fora da base de precisão
        n_av += 1
        if arvore.ramo_valido(r["tema_central_id"], tema_ouro):
            acertos += 1
        else:
            erros_ex.append((qid, r["tema_central_id"], tema_ouro))
    p_ouro, low_ouro, high_ouro = wilson(acertos, n_av) if n_av else (None, None, None)

    # --- cobertura: intervalo por Wilson tratando "publicar" como sucesso em n_total ---
    _, cob_low, cob_high = wilson(n_pub, n_total)

    # --- precisão prevista: usa a amostra-ouro se houver amostra suficiente;
    #     senão recai na concordância do comitê (mais incerto) ---
    if n_av >= 10 and p_ouro is not None:
        prec = p_ouro
        prec_low, prec_high = low_ouro, high_ouro
        base = f"amostra-ouro ({acertos}/{n_av} publicadas certas pela régua)"
    elif conc_media is not None:
        prec = conc_media
        # intervalo largo (proxy, não medição): ±0.08 heurístico
        prec_low, prec_high = max(0.0, prec - 0.08), min(1.0, prec + 0.08)
        base = f"concordância do comitê (proxy; amostra-ouro insuficiente: {n_av} publicadas rotuladas)"
    else:
        prec, prec_low, prec_high = 0.0, 0.0, 1.0
        base = "sem sinais suficientes"

    txt = []
    txt.append(f"precisao_prevista: {prec:.2f}")
    txt.append(f"precisao_intervalo: {prec_low:.2f}-{prec_high:.2f}")
    txt.append(f"cobertura_prevista: {cobertura:.2f}")
    txt.append(f"cobertura_intervalo: {cob_low:.2f}-{cob_high:.2f}")
    txt.append("")
    txt.append("Como cheguei nestes números")
    txt.append("-" * 40)
    txt.append(f"- Base de {n_total} questões; {n_pub} publicadas ({100*cobertura:.1f}%), "
               f"{sum(1 for r in pub if r['decisao']=='revisar')} revisar, "
               f"{sum(1 for r in pub if r['decisao']=='fora')} fora.")
    txt.append(f"- Precisão estimada a partir de: {base}.")
    if conc_media is not None:
        txt.append(f"- Concordância média do comitê nas publicadas (proxy): {conc_media:.3f} "
                   f"(fração de pares de modelos no mesmo ramo pai/filho).")
    if n_av:
        txt.append(f"- Amostra-ouro: {n_av} das publicadas estavam na amostra rotulada à mão; "
                   f"{acertos} certas pela régua (pai/filho). Wilson 95%: "
                   f"{low_ouro:.2f}-{high_ouro:.2f}.")
        if erros_ex:
            ex = "; ".join(f"{q}(pub {a} vs ouro {o})" for q, a, o in erros_ex[:5])
            txt.append(f"- Exemplos de erro na amostra: {ex}.")
    txt.append(f"- Cobertura = publicadas/total = {n_pub}/{n_total}; "
               f"intervalo de Wilson 95%: {cob_low:.2f}-{cob_high:.2f}.")
    txt.append("- Honestidade do intervalo: a precisão real tende ao limite inferior quando a "
               "amostra-ouro é pequena; a régua pai/filho favorece acerto porque publicamos no "
               "tema-pai na dúvida entre irmãos.")
    return "\n".join(txt)


def main() -> None:
    conteudo = estimar()
    print(conteudo)
    if not conteudo.startswith("ERRO"):
        SAIDA.parent.mkdir(parents=True, exist_ok=True)
        SAIDA.write_text(conteudo + "\n", encoding="utf-8")
        print(f"\n-> {SAIDA}")


if __name__ == "__main__":
    main()
