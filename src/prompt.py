"""
Montagem do prompt de classificação.

- Renderiza a árvore de temas como lista compacta `id | caminho`, indentada por
  nível, apenas com temas ATIVOS e SELECIONÁVEIS.
- Exclui da lista de candidatos os 20 nós sem descrição (67xx): são duplicatas de
  ramo e módulos de curso ("Parte 1/Parte 2") sem filhos e sem histórico de
  questões no source. A equipe rotulou nos nós canônicos (47xx/5465), que têm
  descrição. Apresentar os 67xx só adiciona erro de convenção que nenhum modelo
  detecta. Decisão registrada em docs/decisoes_manuais.md.

O template vem de prompts/classificacao_vN.md (seções ## SYSTEM e ## USER).
"""
from __future__ import annotations

import re
from pathlib import Path

from normalizar import ArvoreTemas, Questao

ROOT = Path(__file__).resolve().parent.parent
PROMPTS = ROOT / "prompts"

VERSAO_PROMPT = "v1"


def temas_selecionaveis(arvore: ArvoreTemas) -> set[str]:
    """IDs que um modelo pode escolher: ativos e COM descrição (exclui 67xx)."""
    return {
        tid
        for tid, t in arvore.temas.items()
        if t.ativo and t.descricao.strip()
    }


def render_arvore(arvore: ArvoreTemas) -> str:
    """Lista compacta, agrupada por disciplina e ordenada pelo caminho."""
    sel = temas_selecionaveis(arvore)
    linhas: list[str] = []
    # ordena por caminho para manter a hierarquia visual coerente
    for t in sorted(arvore.temas.values(), key=lambda x: (x.disciplina, x.caminho)):
        if t.tema_id not in sel:
            continue
        indent = "  " * t.nivel
        linhas.append(f"{indent}{t.tema_id} | {t.caminho}")
    return "\n".join(linhas)


def _carregar_template(versao: str = VERSAO_PROMPT) -> tuple[str, str]:
    txt = (PROMPTS / f"classificacao_{versao}.md").read_text(encoding="utf-8")
    sys_m = re.search(r"## SYSTEM\s*\n(.*?)(?=\n## USER)", txt, re.S)
    usr_m = re.search(r"## USER\s*\n(.*)$", txt, re.S)
    if not sys_m or not usr_m:
        raise ValueError("Template sem seções ## SYSTEM / ## USER")
    return sys_m.group(1).strip(), usr_m.group(1).strip()


def montar(arvore_render: str, questao: Questao, versao: str = VERSAO_PROMPT) -> tuple[str, str]:
    """Retorna (system, user) prontos para enviar ao modelo."""
    system, user = _carregar_template(versao)
    user = user.replace("{ARVORE}", arvore_render).replace(
        "{QUESTAO}", questao.texto_classificacao()
    )
    return system, user


if __name__ == "__main__":
    from normalizar import carregar_questoes, carregar_temas

    arvore = carregar_temas()
    questoes = carregar_questoes()
    render = render_arvore(arvore)
    sel = temas_selecionaveis(arvore)

    print(f"Temas selecionáveis: {len(sel)} de {len(arvore.temas)} "
          f"(excluídos {len(arvore.temas) - len(sel)}: inativos + sem descrição)")
    nchar = len(render)
    print(f"Árvore renderizada: {nchar} chars (~{nchar // 4} tokens aprox.)")
    print("\n--- primeiras 15 linhas da árvore ---")
    print("\n".join(render.splitlines()[:15]))

    system, user = montar(render, questoes[0])
    print(f"\n--- prompt p/ {questoes[0].id}: system {len(system)} chars, "
          f"user {len(user)} chars (~{len(user)//4} tokens) ---")
