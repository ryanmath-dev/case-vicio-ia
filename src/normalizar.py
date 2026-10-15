"""
Estágio 0 — ingestão e normalização.

Responsabilidades:
  1. Carregar as 359 questões (questoes.jsonl).
  2. Limpar o enunciado (HTML cru + ruído de OCR) e montar o TEXTO DE
     CLASSIFICAÇÃO = enunciado limpo + alternativas rotuladas.
     -> O campo `comando` é IGNORADO de propósito (parece gerado artificialmente;
        ver docs/diagnostico.md A7).
  3. Carregar a árvore de 377 temas (temas.csv) numa estrutura navegável
     (pais, filhos, caminho), marcando inativos e lixeiras conhecidas.

Tudo aqui é determinístico e offline — não depende de chaves de API.

Uso como script (gera uma amostra normalizada para inspeção humana):
    .venv\\Scripts\\python.exe src\\normalizar.py
"""
from __future__ import annotations

import csv
import html
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DADOS = ROOT / "dados"

# --- temas que NUNCA devem ser usados (status inativo; CLAUDE.md §3) ---
TEMAS_INATIVOS = {"5078", "5234"}


# =============================================================================
# Limpeza de texto (HTML + OCR)
# =============================================================================
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t ]+")
_NL_RE = re.compile(r"\s*\n\s*")


def limpar_texto(bruto: str | None) -> str:
    """Remove HTML, decodifica entidades e normaliza espaços.

    Mantém o conteúdo intacto (não tenta 'consertar' OCR — os modelos são
    robustos a isso e qualquer correção automática arriscaria alterar sentido).
    """
    if not bruto:
        return ""
    txt = str(bruto)
    # sequências de escape LITERAIS (dois chars \ + n) que aparecem no meio do
    # texto de origem — ex. Q0003 "Ministério\nPúblico". Viram espaço.
    txt = re.sub(r"\\[nrt]", " ", txt)
    # <br> e </p> viram quebra de linha antes de remover as tags
    txt = re.sub(r"(?i)<br\s*/?>", "\n", txt)
    txt = re.sub(r"(?i)</p>", "\n", txt)
    # tabs reais
    txt = txt.replace("\t", " ")
    # remove tags restantes
    txt = _TAG_RE.sub(" ", txt)
    # decodifica entidades (&nbsp; &ordm; &aacute; ...)
    txt = html.unescape(txt)
    # normaliza espaços e quebras
    txt = _WS_RE.sub(" ", txt)
    txt = _NL_RE.sub("\n", txt)
    return txt.strip()


# =============================================================================
# Questões
# =============================================================================
@dataclass
class Questao:
    id: str
    enunciado: str                 # limpo
    alternativas: dict[str, str]   # rótulo -> texto limpo
    disciplina_origem: str         # pista fraca (não é rótulo)
    assunto_origem: str            # pista fraca (não é rótulo)
    comando_bruto: str             # guardado só para registro; NÃO usar

    @property
    def is_certo_errado(self) -> bool:
        return set(self.alternativas.keys()) <= {"C", "E"} or len(self.alternativas) == 2

    def texto_classificacao(self) -> str:
        """Texto que vai ao modelo: enunciado + alternativas rotuladas."""
        linhas = [self.enunciado] if self.enunciado else []
        if self.alternativas:
            linhas.append("\nAlternativas:")
            for rot, txt in self.alternativas.items():
                linhas.append(f"({rot}) {txt}")
        return "\n".join(linhas).strip()


def carregar_questoes(caminho: Path | None = None) -> list[Questao]:
    caminho = caminho or (DADOS / "questoes.jsonl")
    out: list[Questao] = []
    with caminho.open(encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            d = json.loads(linha)
            alts = {k: limpar_texto(v) for k, v in (d.get("alternativas") or {}).items()}
            out.append(
                Questao(
                    id=d["id"],
                    enunciado=limpar_texto(d.get("enunciado_html")),
                    alternativas=alts,
                    disciplina_origem=(d.get("disciplina_origem") or "").strip(),
                    assunto_origem=(d.get("assunto_origem") or "").strip(),
                    comando_bruto=(d.get("comando") or "").strip(),
                )
            )
    return out


# =============================================================================
# Árvore de temas
# =============================================================================
@dataclass
class Tema:
    tema_id: str
    parent_id: str | None
    disciplina: str
    nivel: int
    titulo: str
    caminho: str
    descricao: str
    status: str
    filhos: list[str] = field(default_factory=list)

    @property
    def ativo(self) -> bool:
        return self.status == "active" and self.tema_id not in TEMAS_INATIVOS


class ArvoreTemas:
    def __init__(self, temas: dict[str, Tema]):
        self.temas = temas

    def __getitem__(self, tid: str) -> Tema:
        return self.temas[tid]

    def get(self, tid: str) -> Tema | None:
        return self.temas.get(tid)

    def pai(self, tid: str) -> Tema | None:
        t = self.temas.get(tid)
        if not t or not t.parent_id:
            return None
        return self.temas.get(t.parent_id)

    def filhos(self, tid: str) -> list[Tema]:
        t = self.temas.get(tid)
        return [self.temas[c] for c in t.filhos] if t else []

    def irmaos(self, tid: str) -> list[Tema]:
        t = self.temas.get(tid)
        if not t or not t.parent_id:
            return []
        return [self.temas[c] for c in self.temas[t.parent_id].filhos if c != tid]

    def ramo_valido(self, publicado: str, gabarito: str) -> bool:
        """Régua pai/filho: publicar em `publicado` conta como certo quando o
        gabarito é o próprio nó, o pai direto ou um filho direto dele."""
        if publicado == gabarito:
            return True
        tp = self.pai(publicado)
        if tp and tp.tema_id == gabarito:
            return True
        tg = self.pai(gabarito)
        if tg and tg.tema_id == publicado:
            return True
        return False

    def sem_descricao(self) -> list[str]:
        return [tid for tid, t in self.temas.items() if not t.descricao.strip()]


def carregar_temas(caminho: Path | None = None) -> ArvoreTemas:
    caminho = caminho or (DADOS / "temas.csv")
    temas: dict[str, Tema] = {}
    with caminho.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            temas[row["tema_id"]] = Tema(
                tema_id=row["tema_id"],
                parent_id=(row["parent_id"] or None),
                disciplina=row["disciplina"],
                nivel=int(row["nivel"]),
                titulo=row["titulo"],
                caminho=row["caminho"],
                descricao=row.get("descricao", ""),
                status=row.get("status", "active"),
            )
    # ligar filhos
    for t in temas.values():
        if t.parent_id and t.parent_id in temas:
            temas[t.parent_id].filhos.append(t.tema_id)
    return ArvoreTemas(temas)


# =============================================================================
# CLI: gera amostra normalizada para inspeção humana
# =============================================================================
def _main() -> None:
    questoes = carregar_questoes()
    arvore = carregar_temas()
    print(f"Questões carregadas: {len(questoes)}")
    print(f"Temas carregados:    {len(arvore.temas)}")
    print(f"  ativos: {sum(1 for t in arvore.temas.values() if t.ativo)}")
    print(f"  inativos: {[t.tema_id for t in arvore.temas.values() if not t.ativo]}")

    out = ROOT / "saidas" / "normalizado_amostra.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for q in questoes[:12]:
            f.write(f"===== {q.id}  (disc_orig={q.disciplina_origem!r} "
                    f"assunto_orig={q.assunto_origem!r} CE={q.is_certo_errado}) =====\n")
            f.write(q.texto_classificacao())
            f.write("\n\n")
    print(f"Amostra normalizada (12 primeiras) -> {out}")


if __name__ == "__main__":
    _main()
