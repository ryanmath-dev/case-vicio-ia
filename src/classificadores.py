"""
Estágio 3 — comitê multi-família (Anthropic + OpenAI + Google).

Objetivo: para cada questão, obter uma classificação independente de 3 famílias
de modelos diferentes, para descorrelacionar erros (CLAUDE.md §6).

Princípios:
  - Saída estruturada (JSON) com schema fixo: tema_central_id, confianca,
    extras_ids, fora, raciocinio.
  - CACHE obrigatório: a resposta crua de cada (questão, modelo, versao_prompt)
    é salva em saidas/cache/. Nunca re-chamamos o que já está em cache
    (reprodutibilidade + economia). O cache É o mecanismo de reprodutibilidade —
    o Opus 4.8 não aceita temperature=0 (a API rejeita), então a determinação
    vem do cache, não do sampling.
  - IDs de modelo vêm de variáveis de ambiente (ANTHROPIC_MODEL / OPENAI_MODEL /
    GEMINI_MODEL) com defaults; use --list-models para descobrir IDs válidos.

Uso:
  .venv\\Scripts\\python.exe src\\classificadores.py --list-models
  .venv\\Scripts\\python.exe src\\classificadores.py --smoke 3
  .venv\\Scripts\\python.exe src\\classificadores.py --all
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent))
from normalizar import Questao, carregar_questoes, carregar_temas  # noqa: E402
from prompt import VERSAO_PROMPT, partes, render_arvore  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "saidas" / "cache"
load_dotenv(ROOT / ".env")

# --- IDs de modelo (override por env) -------------------------------------
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-4-8")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.1")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")

PROVIDERS = ("anthropic", "openai", "gemini")

# --- schema de saída (compartilhado entre provedores) ---------------------
JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "raciocinio": {"type": "string"},
        "tema_central_id": {"type": "string"},
        "confianca": {"type": "number"},
        "extras_ids": {"type": "array", "items": {"type": "string"}},
        "fora": {"type": "boolean"},
    },
    "required": ["raciocinio", "tema_central_id", "confianca", "extras_ids", "fora"],
    "additionalProperties": False,
}


@dataclass
class Resultado:
    provider: str
    model: str
    questao_id: str
    versao_prompt: str
    parsed: dict | None
    raw: str
    ok: bool
    erro: str = ""
    usage: dict | None = None


# =============================================================================
# Cache
# =============================================================================
def _cache_path(questao_id: str, provider: str, model: str, versao: str) -> Path:
    # modelo pode ter caracteres estranhos -> hash curto no nome
    mh = hashlib.sha1(model.encode()).hexdigest()[:8]
    return CACHE_DIR / f"{questao_id}__{provider}__{mh}__{versao}.json"


def _ler_cache(path: Path) -> Resultado | None:
    if not path.exists():
        return None
    d = json.loads(path.read_text(encoding="utf-8"))
    return Resultado(**d)


def _salvar_cache(path: Path, r: Resultado) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(r), ensure_ascii=False, indent=2), encoding="utf-8")


# =============================================================================
# Parsing tolerante de JSON
# =============================================================================
def _parse_json(texto: str) -> dict | None:
    if not texto:
        return None
    t = texto.strip()
    # remove cercas ```json ... ```
    if t.startswith("```"):
        t = t.split("```", 2)[1] if t.count("```") >= 2 else t
        t = t[4:] if t.lower().startswith("json") else t
    try:
        return json.loads(t)
    except Exception:
        # tenta pegar o primeiro {...}
        i, j = t.find("{"), t.rfind("}")
        if 0 <= i < j:
            try:
                return json.loads(t[i : j + 1])
            except Exception:
                return None
    return None


# =============================================================================
# Chamadas por provedor
# =============================================================================
def _call_anthropic(system: str, bloco_arvore: str, bloco_questao: str, model: str) -> tuple[str, dict]:
    import anthropic

    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=model,
        max_tokens=1024,
        system=[
            {"type": "text", "text": system},
            {"type": "text", "text": bloco_arvore, "cache_control": {"type": "ephemeral"}},
        ],
        messages=[{"role": "user", "content": bloco_questao}],
        output_config={"format": {"type": "json_schema", "schema": JSON_SCHEMA}},
    )
    texto = next((b.text for b in resp.content if b.type == "text"), "")
    usage = {
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
        "cache_read": getattr(resp.usage, "cache_read_input_tokens", 0),
        "cache_write": getattr(resp.usage, "cache_creation_input_tokens", 0),
    }
    return texto, usage


def _call_openai(system: str, bloco_arvore: str, bloco_questao: str, model: str) -> tuple[str, dict]:
    from openai import OpenAI

    client = OpenAI()
    resp = client.chat.completions.create(
        model=model,
        temperature=0,
        seed=7,
        messages=[
            {"role": "system", "content": system + "\n\n" + bloco_arvore},
            {"role": "user", "content": bloco_questao},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "classificacao", "schema": JSON_SCHEMA, "strict": True},
        },
    )
    texto = resp.choices[0].message.content or ""
    usage = {
        "input_tokens": resp.usage.prompt_tokens,
        "output_tokens": resp.usage.completion_tokens,
    }
    return texto, usage


def _call_gemini(system: str, bloco_arvore: str, bloco_questao: str, model: str) -> tuple[str, dict]:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    resp = client.models.generate_content(
        model=model,
        contents=bloco_questao,
        config=types.GenerateContentConfig(
            system_instruction=system + "\n\n" + bloco_arvore,
            temperature=0,
            response_mime_type="application/json",
            response_schema=JSON_SCHEMA,
        ),
    )
    texto = resp.text or ""
    usage = {}
    um = getattr(resp, "usage_metadata", None)
    if um:
        usage = {
            "input_tokens": getattr(um, "prompt_token_count", None),
            "output_tokens": getattr(um, "candidates_token_count", None),
        }
    return texto, usage


_DISPATCH = {
    "anthropic": (_call_anthropic, lambda: ANTHROPIC_MODEL),
    "openai": (_call_openai, lambda: OPENAI_MODEL),
    "gemini": (_call_gemini, lambda: GEMINI_MODEL),
}


# =============================================================================
# Classificação de uma questão por um provedor (com cache)
# =============================================================================
def classificar(
    questao: Questao,
    bloco_arvore: str,
    system: str,
    provider: str,
    versao: str = VERSAO_PROMPT,
    forcar: bool = False,
) -> Resultado:
    call_fn, model_fn = _DISPATCH[provider]
    model = model_fn()
    path = _cache_path(questao.id, provider, model, versao)
    if not forcar:
        cached = _ler_cache(path)
        if cached is not None:
            return cached

    # a questão é a parte volátil; reusa a formatação de prompt.partes()
    # (o 1º arg só alimenta o bloco da árvore, que já temos — passamos "")
    _, _, bloco_questao = partes("", questao, versao)

    try:
        texto, usage = call_fn(system, bloco_arvore, bloco_questao, model)
        parsed = _parse_json(texto)
        r = Resultado(
            provider=provider, model=model, questao_id=questao.id, versao_prompt=versao,
            parsed=parsed, raw=texto, ok=parsed is not None, usage=usage,
            erro="" if parsed is not None else "JSON não parseável",
        )
    except Exception as e:  # noqa: BLE001
        r = Resultado(
            provider=provider, model=model, questao_id=questao.id, versao_prompt=versao,
            parsed=None, raw="", ok=False, erro=f"{type(e).__name__}: {e}", usage=None,
        )
    _salvar_cache(path, r)
    return r


# =============================================================================
# CLI
# =============================================================================
def _list_models() -> None:
    print("Modelos configurados:")
    print(f"  ANTHROPIC_MODEL = {ANTHROPIC_MODEL}")
    print(f"  OPENAI_MODEL    = {OPENAI_MODEL}")
    print(f"  GEMINI_MODEL    = {GEMINI_MODEL}")
    print()
    # OpenAI
    try:
        from openai import OpenAI
        ids = sorted(m.id for m in OpenAI().models.list().data)
        gpt = [i for i in ids if i.startswith(("gpt", "o1", "o3", "o4"))]
        print(f"OpenAI: {len(ids)} modelos. Candidatos gpt/o*:")
        print("  " + ", ".join(gpt[:40]))
    except Exception as e:  # noqa: BLE001
        print(f"OpenAI: erro ao listar — {type(e).__name__}: {e}")
    print()
    # Gemini
    try:
        from google import genai
        client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
        names = [m.name for m in client.models.list()]
        gen = [n for n in names if "gemini" in n]
        print(f"Gemini: {len(names)} modelos. Com 'gemini':")
        print("  " + ", ".join(gen[:40]))
    except Exception as e:  # noqa: BLE001
        print(f"Gemini: erro ao listar — {type(e).__name__}: {e}")
    print()
    # Anthropic
    try:
        import anthropic
        ids = [m.id for m in anthropic.Anthropic().models.list().data]
        print(f"Anthropic: {len(ids)} modelos: {', '.join(ids[:20])}")
    except Exception as e:  # noqa: BLE001
        print(f"Anthropic: erro ao listar — {type(e).__name__}: {e}")


def _run(n: int | None, providers: tuple[str, ...], forcar: bool) -> None:
    arvore = carregar_temas()
    questoes = carregar_questoes()
    if n:
        questoes = questoes[:n]
    arvore_render = render_arvore(arvore)
    system, bloco_arvore, _ = partes(arvore_render, questoes[0])

    t0 = time.time()
    total, cache_hits, erros = 0, 0, 0
    for i, q in enumerate(questoes, 1):
        for prov in providers:
            path = _cache_path(q.id, prov, _DISPATCH[prov][1](), VERSAO_PROMPT)
            ja = path.exists()
            r = classificar(q, bloco_arvore, system, prov, forcar=forcar)
            total += 1
            cache_hits += 1 if (ja and not forcar) else 0
            if not r.ok:
                erros += 1
                print(f"  [ERRO] {q.id} {prov}: {r.erro}")
        if i % 20 == 0 or i == len(questoes):
            print(f"  {i}/{len(questoes)} questões | {total} chamadas | "
                  f"cache_hits={cache_hits} erros={erros} | {time.time()-t0:.0f}s")
    print(f"Concluído: {total} resultados, {erros} erros, {time.time()-t0:.0f}s")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list-models", action="store_true", help="lista IDs de modelo de cada provedor")
    ap.add_argument("--smoke", type=int, metavar="N", help="roda as N primeiras questões")
    ap.add_argument("--all", action="store_true", help="roda todas as 359")
    ap.add_argument("--providers", default=",".join(PROVIDERS),
                    help="comma: anthropic,openai,gemini")
    ap.add_argument("--forcar", action="store_true", help="ignora cache e re-chama")
    args = ap.parse_args()

    if args.list_models:
        _list_models()
        return
    provs = tuple(p.strip() for p in args.providers.split(",") if p.strip())
    if args.smoke:
        _run(args.smoke, provs, args.forcar)
    elif args.all:
        _run(None, provs, args.forcar)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
