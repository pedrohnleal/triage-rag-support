#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Confere se o indice do Qdrant corresponde a data/kb: todos os arquivos indexados, nenhum trecho
de arquivo inexistente e metadado "category" igual a pasta. Com --reingest, reindexa antes.

Uso: python scripts/verify_index.py [--reingest]
Saida: 0 = confere; 1 = divergencia; 2 = servico inacessivel.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

CATEGORIES = ["spring-boot", "docker", "azure", "sql-server", "nextjs"]


def expected_category(folder: str) -> str:
    """Mesma regra de Category.java."""
    return folder.upper().replace("-", "_")


def http_json(url: str, method: str = "GET", body: dict | None = None, timeout: float = 30.0):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw.strip() else {}


def kb_files(kb_dir: Path) -> dict[str, str]:
    """{'docker/01-x.md': 'DOCKER'} para cada arquivo da base."""
    out = {}
    for folder in CATEGORIES:
        d = kb_dir / folder
        if not d.is_dir():
            continue
        for p in sorted(d.iterdir()):
            if p.is_file() and p.suffix.lower() in (".md", ".txt"):
                out[f"{folder}/{p.name}"] = expected_category(folder)
    return out


def scroll_all(qdrant: str, collection: str):
    points, offset = [], None
    while True:
        body = {"limit": 256, "with_payload": True, "with_vector": False}
        if offset is not None:
            body["offset"] = offset
        res = http_json(f"{qdrant}/collections/{collection}/points/scroll", "POST", body)["result"]
        points += res.get("points", [])
        offset = res.get("next_page_offset")
        if offset is None:
            return points


def meta(payload: dict, key: str):
    """O Spring AI grava os metadados na raiz do payload; aceita tambem payload['metadata'][key]."""
    if key in payload:
        return payload[key]
    nested = payload.get("metadata")
    return nested.get(key) if isinstance(nested, dict) else None


def main(argv=None) -> int:
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description="Confere o indice do Qdrant contra data/kb.")
    ap.add_argument("--kb", default=str(root / "data" / "kb"))
    ap.add_argument("--qdrant", default="http://localhost:6333", help="URL REST do Qdrant")
    ap.add_argument("--collection", default="kb_suporte")
    ap.add_argument("--app", default="http://localhost:8080", help="URL do microsservico (para --reingest)")
    ap.add_argument("--reingest", action="store_true", help="chama POST /admin/ingest?reset=true antes de conferir")
    args = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    expected = kb_files(Path(args.kb))
    if not expected:
        print(f"ERRO: nenhum documento em {args.kb}/<categoria>/. Rode scripts/populate_kb.py.")
        return 1

    if args.reingest:
        print(f"Reindexando via {args.app}/admin/ingest?reset=true (usa a API de embeddings; leva alguns segundos)...")
        try:
            summary = http_json(f"{args.app}/admin/ingest?reset=true", "POST", {}, timeout=600)
        except (urllib.error.URLError, OSError, ValueError) as e:
            print(f"ERRO: não consegui chamar o app em {args.app}: {e}\nO contêiner tcc-app está no ar? (docker compose up -d)")
            return 2
        print(f"  app respondeu: {summary.get('files')} arquivos, {summary.get('chunks')} trechos "
              f"{json.dumps(summary.get('chunksPerCategory'), ensure_ascii=False)}")

    try:
        info = http_json(f"{args.qdrant}/collections/{args.collection}")["result"]
        points = scroll_all(args.qdrant, args.collection)
    except urllib.error.HTTPError as e:
        print(f"ERRO: Qdrant respondeu HTTP {e.code} para a coleção '{args.collection}'. "
              "A coleção existe? (o app a cria ao iniciar, com initialize-schema: true)")
        return 2
    except (urllib.error.URLError, OSError, ValueError, KeyError) as e:
        print(f"ERRO: não consegui ler o Qdrant em {args.qdrant}: {e}\nO contêiner tcc-qdrant está no ar?")
        return 2

    chunks_by_source: Counter = Counter()
    cats_by_source: dict[str, set] = defaultdict(set)
    for pt in points:
        payload = pt.get("payload") or {}
        src = meta(payload, "source")
        chunks_by_source[str(src)] += 1
        cats_by_source[str(src)].add(str(meta(payload, "category")))

    print(f"\nColeção '{args.collection}' em {args.qdrant}: {len(points)} trechos (points_count informado: "
          f"{info.get('points_count')}; status: {info.get('status')})")
    print(f"Base em {args.kb}: {len(expected)} documentos em {len({c for c in expected.values()})} categorias\n")

    print(f"{'Categoria':<12} {'docs na base':>12} {'docs indexados':>15} {'trechos':>8}")
    for folder in CATEGORIES:
        cat = expected_category(folder)
        in_kb = [s for s, c in expected.items() if c == cat]
        indexed = [s for s in in_kb if chunks_by_source.get(s)]
        print(f"{cat:<12} {len(in_kb):>12} {len(indexed):>15} {sum(chunks_by_source.get(s, 0) for s in in_kb):>8}")

    missing = sorted(s for s in expected if not chunks_by_source.get(s))
    stale = sorted(s for s in chunks_by_source if s not in expected)
    wrong_cat = sorted(s for s in expected if chunks_by_source.get(s) and cats_by_source[s] != {expected[s]})

    problems = []
    if not points:
        problems.append("O índice está VAZIO.")
    if missing:
        problems.append(f"{len(missing)} documento(s) da base NÃO estão no índice: " + ", ".join(missing[:8]) + (" ..." if len(missing) > 8 else ""))
    if stale:
        problems.append(f"{len(stale)} fonte(s) no índice NÃO existem em {args.kb} (resto de teste ou base antiga): "
                        + ", ".join(f"{s} ({chunks_by_source[s]} trecho(s))" for s in stale[:8]))
    if wrong_cat:
        problems.append("Metadado 'category' diferente da pasta (o filtro de C2/C3 espera "
                        + "SPRING_BOOT/DOCKER/AZURE/SQL_SERVER/NEXTJS): "
                        + ", ".join(f"{s} -> {sorted(cats_by_source[s])}" for s in wrong_cat[:6]))

    print()
    if not problems:
        print("OK: o índice confere com a base. Pode rodar a avaliação de qualidade e o benchmark.")
        return 0
    print("PROBLEMAS ENCONTRADOS:")
    for p in problems:
        print(f"  - {p}")
    print("\nCorreção: python scripts/verify_index.py --reingest")
    if stale or wrong_cat:
        print("Se sobrarem fontes obsoletas ou categorias erradas após --reingest (o reset só apaga por categoria válida), "
              "recrie a coleção:\n  curl.exe -X DELETE http://localhost:6333/collections/kb_suporte\n"
              "  docker compose restart app     # o app recria a coleção ao iniciar\n  python scripts/verify_index.py --reingest")
    return 1


if __name__ == "__main__":
    sys.exit(main())
