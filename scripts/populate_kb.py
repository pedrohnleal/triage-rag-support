#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera a base de conhecimento em data/kb/<categoria>/ e data/kb-manifest.json a partir de
nimbus_content.py. A pasta define a categoria usada no índice.

Uso: python scripts/populate_kb.py [--out data/kb] [--clean] [--dry-run]
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nimbus_content as C  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover
    pass


def render_doc(doc: dict) -> str:
    lines = [f"# {doc['title']}", ""]
    if doc["type"] == "runbook-simulado":
        lines += [C.RUNBOOK_INTRO, ""]
    for sec in doc["sections"]:
        lines += [f"## {sec['title']}", "", sec["body"], ""]
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="data/kb", help="pasta de saída (padrão: data/kb)")
    ap.add_argument("--clean", action="store_true", help="remove .md existentes nas pastas de categoria antes de gerar")
    ap.add_argument("--dry-run", action="store_true", help="só valida e mostra o que seria escrito")
    args = ap.parse_args()

    out = Path(args.out)
    problems = []

    # validações da fonte
    seen_files, seen_ids = {}, {}
    for cat in C.KB:
        for doc in cat["docs"]:
            if doc["file"] in seen_files:
                problems.append(f"arquivo duplicado: {doc['file']}")
            seen_files[doc["file"]] = cat["category"]
            for sec in doc["sections"]:
                if sec["id"] in seen_ids:
                    problems.append(f"id de seção duplicado: {sec['id']}")
                seen_ids[sec["id"]] = (cat["category"], doc["file"])
    if problems:
        print("ERRO na fonte de conteúdo:\n  " + "\n  ".join(problems))
        return 1

    manifest = {"documents": [], "totals": {}}
    n_docs = n_secs = n_words = 0

    for cat in C.KB:
        folder = out / cat["category"]
        if not args.dry_run:
            folder.mkdir(parents=True, exist_ok=True)
            if args.clean:
                for old in folder.glob("*.md"):
                    old.unlink()
        for doc in cat["docs"]:
            text = render_doc(doc)
            words = len(text.split())
            rel = f"{cat['category']}/{doc['file']}"
            manifest["documents"].append({
                "path": rel,
                "category": cat["category"],
                "title": doc["title"],
                "type": doc["type"],
                "sections": [{"id": s["id"], "title": s["title"]} for s in doc["sections"]],
                "words": words,
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "origin": "autoria própria (síntese técnica)" if doc["type"] == "nota-tecnica"
                          else "simulado pelo grupo (regras fictícias)",
            })
            n_docs += 1
            n_secs += len(doc["sections"])
            n_words += words
            if args.dry_run:
                print(f"[dry-run] {rel}  ({len(doc['sections'])} seções, {words} palavras)")
            else:
                (folder / doc["file"]).write_text(text, encoding="utf-8", newline="\n")

    manifest["totals"] = {"documents": n_docs, "sections": n_secs, "words": n_words,
                          "categories": [c["category"] for c in C.KB]}

    if not args.dry_run:
        (out.parent / "kb-manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (out.parent / "KB_README.md").write_text(KB_README, encoding="utf-8", newline="\n")

    print(f"OK: {n_docs} documentos, {n_secs} seções, ~{n_words} palavras em {out}/")
    print("Próximo passo: reindexar o Qdrant com `category` = nome da pasta e chunk = seção (`## `).")
    return 0


KB_README = """# Base de conhecimento

Gerada por `scripts/populate_kb.py` a partir de `scripts/nimbus_content.py`; não edite os .md à mão.

- `01` a `04` de cada categoria: notas técnicas.
- `05-runbook-nimbus-*.md`: manual interno simulado da plataforma fictícia Nimbus.
- `data/kb-manifest.json`: documentos, seções, contagem de palavras e SHA-256.
"""

if __name__ == "__main__":
    sys.exit(main())
