#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera data/tickets-100.json, data/tickets-k6-20.json, data/triage-fewshot-10.json e
data/dataset-manifest.json a partir de nimbus_content.py.

Uso: python scripts/build_tickets.py [--kb data/kb] [--out data] [--seed 20261016]
"""
import argparse
import json
import random
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nimbus_content as C  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover
    pass

CATEGORIES = [c["category"] for c in C.KB]
PRIO = {"A": "alta", "M": "média", "B": "baixa"}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(ch for ch in s if not unicodedata.combining(ch)).lower()


def section_index():
    idx = {}
    for cat in C.KB:
        for doc in cat["docs"]:
            for sec in doc["sections"]:
                idx[sec["id"]] = {"category": cat["category"], "file": f"{cat['category']}/{doc['file']}",
                                  "title": sec["title"], "body": sec["body"], "doc_type": doc["type"]}
    return idx


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kb", default="data/kb", help="pasta da KB gerada por populate_kb.py (para conferir que os arquivos existem)")
    ap.add_argument("--out", default="data", help="pasta de saída")
    ap.add_argument("--seed", type=int, default=20261016, help="seed do embaralhamento e da seleção do k6")
    args = ap.parse_args()

    idx = section_index()
    errors, warnings = [], []

    # chamados com solução
    answerable = []
    for sid, question, answer, prio, amb in C.TICKETS:
        if sid not in idx:
            errors.append(f"seção inexistente: {sid}")
            continue
        sec = idx[sid]
        # toda expressão entre crases da resposta de referência precisa existir no texto da seção-fonte
        body_n = norm(sec["title"] + " " + sec["body"])
        for tok in re.findall(r"`([^`]+)`", answer):
            if norm(tok) not in body_n:
                errors.append(f"{sid}: trecho `{tok}` da resposta não está na seção-fonte")
        if amb is not None and amb not in CATEGORIES:
            errors.append(f"{sid}: ambiguousWith inválido ({amb})")
        if amb == sec["category"]:
            errors.append(f"{sid}: ambiguousWith igual à categoria esperada")
        answerable.append({
            "question": question, "expectedCategory": sec["category"], "priority": PRIO[prio],
            "hasAnswer": True, "expectedSource": sec["file"], "expectedSection": sec["title"],
            "referenceAnswer": answer, "isAmbiguous": amb is not None, "ambiguousWith": amb,
            "kbSectionId": sid, "sourceType": sec["doc_type"],
        })

    unanswerable = []
    for cat, question, prio, kind in C.UNANSWERABLE:
        if cat not in CATEGORIES:
            errors.append(f"categoria inválida em sem-solução: {cat}")
        unanswerable.append({
            "question": question, "expectedCategory": cat, "priority": PRIO[prio],
            "hasAnswer": False, "expectedSource": None, "expectedSection": None,
            "referenceAnswer": None, "isAmbiguous": False, "ambiguousWith": None,
            "kbSectionId": None, "sourceType": None, "unanswerableKind": kind,
        })

    # validações
    cnt_ans = Counter(t["expectedCategory"] for t in answerable)
    cnt_un = Counter(t["expectedCategory"] for t in unanswerable)
    for cat in CATEGORIES:
        if cnt_ans[cat] != 16:
            errors.append(f"{cat}: {cnt_ans[cat]} chamados com solução (esperado 16)")
        if cnt_un[cat] != 4:
            errors.append(f"{cat}: {cnt_un[cat]} chamados sem solução (esperado 4)")
    if len(answerable) != 80 or len(unanswerable) != 20:
        errors.append(f"totais incorretos: {len(answerable)} com solução, {len(unanswerable)} sem solução")
    n_amb = sum(t["isAmbiguous"] for t in answerable)
    if n_amb < 15:
        errors.append(f"apenas {n_amb} chamados ambíguos (mínimo 15)")

    # uma seção-fonte por chamado, com notas técnicas e runbooks
    src_counter = Counter(t["kbSectionId"] for t in answerable)
    for sid, n in src_counter.items():
        if n > 1:
            errors.append(f"seção usada por {n} chamados: {sid}")
    by_type = Counter(t["sourceType"] for t in answerable)

    # perguntas duplicadas
    qs = [t["question"] for t in answerable + unanswerable]
    if len(set(qs)) != len(qs):
        errors.append("há perguntas duplicadas")

    # os arquivos de referência precisam existir em data/kb
    kb_dir = Path(args.kb)
    if kb_dir.exists():
        for t in answerable:
            if not (kb_dir / t["expectedSource"]).exists():
                errors.append(f"arquivo ausente em {kb_dir}: {t['expectedSource']} (rode populate_kb.py)")
    else:
        warnings.append(f"{kb_dir} não existe; existência dos arquivos não conferida")

    # few-shot não pode coincidir com os 100
    fewshot = [{"question": q, "category": c} for q, c in C.FEWSHOT]
    for fs in fewshot:
        if fs["question"] in qs:
            errors.append(f"few-shot repetido entre os 100: {fs['question']}")
    cnt_fs = Counter(f["category"] for f in fewshot)
    for cat in CATEGORIES:
        if cnt_fs[cat] != 2:
            errors.append(f"few-shot: {cat} tem {cnt_fs[cat]} exemplos (esperado 2)")

    if errors:
        print("FALHA NAS VALIDAÇÕES:")
        for e in errors:
            print("  -", e)
        return 1

    # ordem e ids
    rng = random.Random(args.seed)
    allt = answerable + unanswerable
    rng.shuffle(allt)
    for i, t in enumerate(allt, 1):
        t["ticketId"] = f"T{i:03d}"
        t["status"] = "candidato-aguardando-validacao"
        t["validatedBy"] = []
    ordered_keys = ["ticketId", "question", "expectedCategory", "priority", "hasAnswer", "expectedSource",
                    "expectedSection", "referenceAnswer", "isAmbiguous", "ambiguousWith", "kbSectionId",
                    "sourceType", "unanswerableKind", "status", "validatedBy"]
    allt = [{k: t.get(k) for k in ordered_keys if k in t or k == "unanswerableKind" and not t["hasAnswer"]} for t in allt]
    allt.sort(key=lambda t: t["ticketId"])

    # subconjunto do k6
    rng_k = random.Random(args.seed + 1)
    k6 = []
    for cat in CATEGORIES:
        ans = [t for t in allt if t["expectedCategory"] == cat and t["hasAnswer"]]
        amb = [t for t in ans if t["isAmbiguous"]]
        non = [t for t in ans if not t["isAmbiguous"]]
        un = [t for t in allt if t["expectedCategory"] == cat and not t["hasAnswer"]]
        pick = [rng_k.choice(amb)] + rng_k.sample(non, 2) + [rng_k.choice(un)]
        k6.extend(pick)
    rng_k.shuffle(k6)
    k6_out = [{"ticketId": t["ticketId"], "question": t["question"], "expectedCategory": t["expectedCategory"],
               "hasAnswer": t["hasAnswer"]} for t in k6]
    if len(k6_out) != 20 or sum(not t["hasAnswer"] for t in k6_out) < 4:
        print("FALHA: subconjunto do k6 inválido")
        return 1

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    dump = lambda p, o: p.write_text(json.dumps(o, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    dump(out / "tickets-100.json", allt)
    dump(out / "tickets-k6-20.json", k6_out)
    dump(out / "triage-fewshot-10.json", fewshot)
    dump(out / "dataset-manifest.json", {
        "seed": args.seed,
        "totals": {"tickets": len(allt), "with_answer": len(answerable), "without_answer": len(unanswerable),
                   "ambiguous": n_amb, "k6_subset": len(k6_out), "k6_without_answer": sum(not t["hasAnswer"] for t in k6_out)},
        "answerable_by_category": dict(cnt_ans), "unanswerable_by_category": dict(cnt_un),
        "answerable_by_source_type": dict(by_type),
        "ambiguous_by_category": dict(Counter(t["expectedCategory"] for t in answerable if t["isAmbiguous"])),
        "priority": dict(Counter(t["priority"] for t in allt)),
        "validations": "todas aprovadas", "warnings": warnings,
        "status": "gerado e validado por script",
    })

    print(f"OK: {len(allt)} chamados ({len(answerable)} com solução, {len(unanswerable)} sem solução), "
          f"{n_amb} ambíguos, k6 = {len(k6_out)} (sem solução: {sum(not t['hasAnswer'] for t in k6_out)})")
    print(f"    fontes: {dict(by_type)}")
    for w in warnings:
        print("AVISO:", w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
