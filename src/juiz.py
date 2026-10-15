"""
Estágio 4 — juiz do comitê + regras de decisão (publicar / revisar / fora).

Lê as saídas cacheadas das 3 famílias (saidas/cache/) e, para cada questão,
combina os votos aplicando:
  - a RÉGUA pai/filho (acerto = nó exato, pai direto ou filho direto);
  - a ALAVANCA DO TEMA-PAI: na dúvida entre subtemas irmãos, publicar no tema
    pai (conta como certo para qualquer filho) — ganha cobertura sem furar 95%;
  - proteção de LIXEIRAS: nunca publicar em disciplina (nível 0); exigir
    acordo/confiança maiores nos temas introdutórios de volume suspeito.

Gera saidas/publicacao.csv (359 linhas):
  id, decisao, tema_central_id, extras_ids(;), confianca, motivo

Uso:
  .venv\\Scripts\\python.exe src\\juiz.py            # usa o cache; gera o CSV
  .venv\\Scripts\\python.exe src\\juiz.py --resumo   # só estatísticas
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from normalizar import ArvoreTemas, Questao, carregar_questoes, carregar_temas  # noqa: E402
from classificadores import PROVIDERS, VERSAO_PROMPT, _cache_path, _ler_cache, _DISPATCH  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# --- parâmetros de decisão (DECISÕES MANUAIS — ver docs/decisoes_manuais.md) ---
CONF_PUBLICAR = 0.80          # confiança combinada mínima para publicar
CONF_PUBLICAR_LIXEIRA = 0.92  # exigência maior se o nó é lixeira suspeita

# Temas introdutórios / de volume suspeito (diagnostico B3): publicar só com
# acordo forte. (Os nós vazios 67xx/"Parte" já nem são selecionáveis.)
LIXEIRAS_SUSPEITAS = {
    "5171",  # Penal > Conceito e Fontes do Direito Penal (310 no source)
    "5581",  # Processo Penal > Sistemas Processuais Penais (285)
    "5170",  # Penal > Introdução ao Estudo do Direito Penal (424)
    "5580",  # Processo Penal > Sistemas e Princípios Processuais Penais (538)
}


# =============================================================================
# Helpers de árvore
# =============================================================================
def tema_pai(arvore: ArvoreTemas, tid: str) -> str | None:
    """Ancestral de nível 1 (o 'tema'). Para nível 2 → pai; nível 1 → ele mesmo;
    nível 0 (disciplina) → None (não serve como alvo de publicação)."""
    t = arvore.get(tid)
    if not t:
        return None
    if t.nivel == 2:
        return t.parent_id
    if t.nivel == 1:
        return t.tema_id
    return None  # disciplina


def disciplina_de(arvore: ArvoreTemas, tid: str) -> str | None:
    t = arvore.get(tid)
    while t and t.parent_id:
        t = arvore.get(t.parent_id)
    return t.tema_id if t else None


# =============================================================================
# Decisão para uma questão
# =============================================================================
class Decisao:
    def __init__(self, decisao, tema, extras, conf, motivo):
        self.decisao = decisao
        self.tema_central_id = tema
        self.extras_ids = extras
        self.confianca = round(conf, 3)
        self.motivo = motivo


def _votos_validos(arvore: ArvoreTemas, parsed_list: list[dict]) -> list[dict]:
    """Mantém só votos cujo tema_central_id é um nó existente (ou marca fora)."""
    out = []
    for p in parsed_list:
        if not isinstance(p, dict):
            continue
        if p.get("fora"):
            out.append({"fora": True, "conf": float(p.get("confianca") or 0)})
            continue
        tid = str(p.get("tema_central_id") or "").strip()
        if arvore.get(tid):
            out.append({
                "fora": False, "tid": tid,
                "conf": float(p.get("confianca") or 0),
                "extras": [str(x) for x in (p.get("extras_ids") or []) if arvore.get(str(x))],
            })
    return out


def decidir(arvore: ArvoreTemas, votos: list[dict]) -> Decisao:
    n = len(votos)
    if n == 0:
        return Decisao("revisar", "", [], 0.3, "sem votos válidos do comitê")

    foras = [v for v in votos if v.get("fora")]
    dentro = [v for v in votos if not v.get("fora")]

    # fora: maioria dos modelos diz que nenhum tema serve
    if len(foras) >= 2 or (n == 1 and len(foras) == 1):
        return Decisao("fora", "", [], _media([v["conf"] for v in foras]),
                       f"{len(foras)}/{n} modelos: nenhum tema da árvore serve")

    if not dentro:
        return Decisao("revisar", "", [], 0.3, "votos insuficientes")

    tids = [v["tid"] for v in dentro]
    temas = [tema_pai(arvore, t) for t in tids]
    discs = [disciplina_de(arvore, t) for t in tids]
    conf_media = _media([v["conf"] for v in dentro])
    extras = _consolidar_extras(dentro)

    # penaliza acordo parcial (se houve fora minoritário)
    penal_fora = 0.1 * len(foras)

    # --- caso 1: todos no MESMO nó exato ---
    if len(set(tids)) == 1:
        tid = tids[0]
        conf = min(0.99, 0.6 + 0.13 * len(dentro) + 0.2 * conf_media) - penal_fora
        return _finalizar(arvore, tid, extras, conf, dentro, foras, n,
                          f"{len(dentro)}/{n} modelos no mesmo nó")

    # --- caso 2: mesmo TEMA (nível 1) entre todos os votos dentro ---
    if len(set(temas)) == 1 and temas[0] is not None:
        tid_pai = temas[0]
        # alavanca: publica no tema-pai (cobre qualquer filho)
        conf = min(0.98, 0.58 + 0.12 * len(dentro) + 0.18 * conf_media) - penal_fora
        return _finalizar(arvore, tid_pai, extras, conf, dentro, foras, n,
                          "subtemas divergentes sob o mesmo tema → publica no tema-pai (alavanca)")

    # --- caso 3: 2/3 concordam no tema (nível 1) ---
    if n >= 3:
        cont = Counter(t for t in temas if t)
        maj, cnt = cont.most_common(1)[0]
        if cnt >= 2:
            conf = min(0.95, 0.5 + 0.12 * cnt + 0.15 * conf_media) - penal_fora
            return _finalizar(arvore, maj, extras, conf, dentro, foras, n,
                              f"{cnt}/{n} modelos no mesmo tema → publica no tema-pai")

    # --- caso 4: divergência real → revisar (sugestão = maior confiança) ---
    melhor = max(dentro, key=lambda v: v["conf"])
    mesma_disc = len(set(d for d in discs if d)) == 1
    motivo = ("divergência entre modelos"
              + (" (mesma disciplina)" if mesma_disc else " (disciplinas diferentes)"))
    return Decisao("revisar", melhor["tid"], extras, min(0.6, conf_media), motivo)


def _finalizar(arvore, tid, extras, conf, dentro, foras, n, motivo) -> Decisao:
    """Aplica proteção de lixeira e o limiar de publicação."""
    t = arvore.get(tid)
    # nunca publicar em disciplina (nível 0)
    if t and t.nivel == 0:
        return Decisao("revisar", tid, extras, min(0.55, conf),
                       "cairia em disciplina (nível 0 / genérico) — revisar")
    limiar = CONF_PUBLICAR_LIXEIRA if tid in LIXEIRAS_SUSPEITAS else CONF_PUBLICAR
    if conf >= limiar:
        extras = [e for e in extras if e != tid]
        return Decisao("publicar", tid, extras, conf, "")
    return Decisao("revisar", tid, extras, conf,
                   motivo + " — confiança abaixo do limiar p/ publicar")


def _consolidar_extras(dentro: list[dict]) -> list[str]:
    c = Counter()
    centrais = {v["tid"] for v in dentro}
    for v in dentro:
        for e in v.get("extras", []):
            if e not in centrais:
                c[e] += 1
    return [e for e, _ in c.most_common(3)]


def _media(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


# =============================================================================
# Orquestração: lê cache, decide, grava CSV
# =============================================================================
def carregar_votos(qid: str) -> list[dict]:
    out = []
    for prov in PROVIDERS:
        model = _DISPATCH[prov][1]()
        r = _ler_cache(_cache_path(qid, prov, model, VERSAO_PROMPT))
        if r and r.ok and r.parsed:
            out.append(r.parsed)
    return out


def gerar(resumo_only: bool = False) -> None:
    arvore = carregar_temas()
    questoes = carregar_questoes()

    linhas = []
    faltando = 0
    stats = Counter()
    for q in questoes:
        parsed_list = carregar_votos(q.id)
        if not parsed_list:
            faltando += 1
        votos = _votos_validos(arvore, parsed_list)
        d = decidir(arvore, votos)
        stats[d.decisao] += 1
        linhas.append((q.id, d))

    print("=== Resumo das decisões ===")
    for k in ("publicar", "revisar", "fora"):
        print(f"  {k:9} {stats[k]:4}  ({100*stats[k]/len(questoes):.1f}%)")
    if faltando:
        print(f"  ATENÇÃO: {faltando} questões sem nenhum voto em cache "
              f"(rode src/classificadores.py --all primeiro)")

    if resumo_only:
        return

    out = ROOT / "saidas" / "publicacao.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "decisao", "tema_central_id", "extras_ids", "confianca", "motivo"])
        for qid, d in linhas:
            w.writerow([qid, d.decisao, d.tema_central_id,
                        ";".join(d.extras_ids), d.confianca, d.motivo])
    print(f"\npublicacao.csv -> {out} ({len(linhas)} linhas)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--resumo", action="store_true", help="só estatísticas, não grava CSV")
    args = ap.parse_args()
    gerar(resumo_only=args.resumo)


if __name__ == "__main__":
    main()
