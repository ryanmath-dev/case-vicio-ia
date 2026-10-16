"""
Seleciona/expande a amostra-ouro para rotulagem manual (CLAUDE.md §9).

Amostra aleatória com SEED FIXA (reprodutível). É **aditiva e não-destrutiva**:
- preserva TODAS as linhas e rótulos já existentes em docs/amostra_ouro.csv;
- adiciona `--add` novas questões amostradas do complemento (com `--seed`),
  até o arquivo ter no mínimo o total desejado.

Foi assim que a amostra de 100 foi construída: 50 iniciais (seed 42) + 50
adicionais (seed 123), sem nunca descartar rótulos.

Uso:
  # cria as 50 iniciais
  .venv\\Scripts\\python.exe src\\amostra_ouro.py --add 50 --seed 42
  # amplia com mais 50 (preserva as 50 já rotuladas)
  .venv\\Scripts\\python.exe src\\amostra_ouro.py --add 50 --seed 123
"""
from __future__ import annotations

import argparse
import csv
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from normalizar import carregar_questoes  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SAIDA = ROOT / "docs" / "amostra_ouro.csv"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--add", type=int, default=50,
                    help="quantas questões NOVAS amostrar do complemento")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    questoes = {q.id: q for q in carregar_questoes()}

    # lê o que já existe (preserva rótulos e linhas)
    existentes: dict[str, str] = {}
    if SAIDA.exists():
        with SAIDA.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                existentes[row["id"]] = row.get("tema_ouro", "")

    # amostra NOVAS do complemento (nunca repete as já presentes)
    resto = sorted(set(questoes) - set(existentes))
    rng = random.Random(args.seed)
    novas = rng.sample(resto, min(args.add, len(resto)))

    todos = sorted(set(existentes) | set(novas))
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with SAIDA.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "tema_ouro", "disciplina_origem", "assunto_origem", "texto"])
        for qid in todos:
            q = questoes[qid]
            texto = q.texto_classificacao().replace("\n", " ⏎ ")
            w.writerow([qid, existentes.get(qid, ""), q.disciplina_origem,
                        q.assunto_origem, texto])
    print(f"Amostra agora com {len(todos)} questões "
          f"({len(novas)} novas, seed={args.seed}) -> {SAIDA}")


if __name__ == "__main__":
    main()
