"""
Seleciona a amostra-ouro para rotulagem manual (CLAUDE.md §9).

Amostra aleatória com SEED FIXA (reprodutível) das 359 questões. Gera
docs/amostra_ouro.csv com o texto de classificação de cada questão e a coluna
`tema_ouro` em branco, para rotular à mão. NÃO sobrescreve rótulos já feitos.

Uso:
  .venv\\Scripts\\python.exe src\\amostra_ouro.py --n 50 --seed 42
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
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    questoes = carregar_questoes()
    rng = random.Random(args.seed)
    escolhidas = sorted(rng.sample(questoes, args.n), key=lambda q: q.id)

    # preserva rótulos já existentes
    existentes: dict[str, str] = {}
    if SAIDA.exists():
        with SAIDA.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                existentes[row["id"]] = row.get("tema_ouro", "")

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with SAIDA.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "tema_ouro", "disciplina_origem", "assunto_origem", "texto"])
        for q in escolhidas:
            texto = q.texto_classificacao().replace("\n", " ⏎ ")
            w.writerow([q.id, existentes.get(q.id, ""), q.disciplina_origem,
                        q.assunto_origem, texto])
    print(f"Amostra de {len(escolhidas)} questões (seed={args.seed}) -> {SAIDA}")
    print("IDs:", " ".join(q.id for q in escolhidas))


if __name__ == "__main__":
    main()
