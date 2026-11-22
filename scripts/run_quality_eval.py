#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Avaliação de qualidade: executa C0 (palavras-chave + BM25) localmente, envia os 100 chamados às
rotas de C1, C2 e C3, aplica o juiz LLM e gera as tabelas de triagem, qualidade e propagação.
Respostas e vereditos ficam em cache em --out (raw_*.jsonl, judge_*.jsonl); --force refaz.

Uso:
  python scripts/run_quality_eval.py --granularity document
  python scripts/run_quality_eval.py --c0-only
  python scripts/run_quality_eval.py --agreement results/eval-100/judge_sample_20pct.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover
    pass

CATEGORIES = ["spring-boot", "docker", "azure", "sql-server", "nextjs"]
UNDEF = "indefinido"
API_CONFIGS = ["c1", "c2", "c3"]
TOPK = 5

# campos aceitos na resposta da API, em ordem de prioridade (aceita caminho com ponto)
FIELD_CANDIDATES = {
    "answer": ["answer", "resposta", "response", "text", "message", "output"],
    "category": ["category", "categoria", "predictedCategory", "triage.category", "triage.categoria",
                 "triagem.categoria", "triage.predictedCategory"],
    "confidence": ["confidence", "confianca", "triage.confidence", "triagem.confianca", "score"],
    "retrieved": ["retrieved", "retrievedChunks", "chunks", "contexts", "context", "documents", "hits", "passages", "sources"],
    "citations": ["citations", "citacoes", "references", "sources"],
    "abstained": ["abstained", "abstention", "abstencao", "noAnswer", "refused", "insufficientContext"],
}
ITEM_SOURCE_KEYS = ["source", "path", "file", "filename", "fileName", "document", "documentId", "doc", "uri", "url",
                    "metadata.source", "metadata.path", "metadata.file", "metadata.filename", "payload.source", "payload.path"]
ITEM_TEXT_KEYS = ["text", "content", "chunk", "page_content", "payload.text", "metadata.text", "snippet"]


# Utilidades de texto
def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(ch for ch in s if not unicodedata.combining(ch)).lower()


STOP = set("""a o as os de do da dos das em no na nos nas um uma uns umas e ou que se por para com sem ao aos como mais mas ja nao
ser ter foi sao esta estao isso isto ele ela eles elas meu minha meus minhas seu sua seus suas voce nosso nossa qual quais quando
onde porque pelo pela pelos pelas entre sobre ate tambem so ha mesmo depois antes essa esse essas esses aquele aquela""".split())
TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(s: str) -> list[str]:
    return [t for t in TOKEN_RE.findall(norm(s)) if t not in STOP and len(t) > 1]


def get_path(obj, path: str):
    cur = obj
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def first_value(obj, candidates):
    for c in candidates:
        v = get_path(obj, c)
        if v is not None:
            return v, c
    return None, None


def pct(num, den):
    return None if not den else 100.0 * num / den


def fmt(x, nd=1):
    if x is None:
        return "N/D"
    if isinstance(x, float) and math.isnan(x):
        return "N/D"
    return f"{x:.{nd}f}".replace(".", ",")


def table_text(headers, rows):
    rows = [[str(c) for c in r] for r in rows]
    w = [max(len(str(h)), *(len(r[i]) for r in rows)) if rows else len(str(h)) for i, h in enumerate(headers)]
    line = "+-" + "-+-".join("-" * x for x in w) + "-+"
    out = [line, "| " + " | ".join(str(h).ljust(w[i]) for i, h in enumerate(headers)) + " |", line]
    for r in rows:
        out.append("| " + " | ".join(r[i].ljust(w[i]) for i in range(len(headers))) + " |")
    out.append(line)
    return "\n".join(out)


def write_csv(path: Path, headers, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:  # BOM para o Excel
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)


# Base de conhecimento local (chunk = seção "## ")
def load_kb_chunks(kb_dir: Path):
    chunks = []
    for md in sorted(kb_dir.rglob("*.md")):
        rel = md.relative_to(kb_dir).as_posix()
        parts = rel.split("/")
        if len(parts) < 2 or parts[0] not in CATEGORIES:
            continue
        text = md.read_text(encoding="utf-8")
        for part in re.split(r"(?m)^##\s+", text)[1:]:
            title, _, body = part.partition("\n")
            chunks.append({"path": rel, "category": parts[0], "section": title.strip(),
                           "text": f"{title.strip()}\n{body.strip()}"})
    if not chunks:
        raise SystemExit(f"Nenhum chunk encontrado em {kb_dir}. Rode scripts/populate_kb.py primeiro.")
    return chunks


class BM25:
    def __init__(self, docs_tokens, k1=1.5, b=0.75):
        self.k1, self.b = k1, b
        self.N = len(docs_tokens)
        self.tf = [Counter(d) for d in docs_tokens]
        self.dl = [len(d) for d in docs_tokens]
        self.avgdl = sum(self.dl) / max(1, self.N)
        df = Counter()
        for d in docs_tokens:
            df.update(set(d))
        self.idf = {t: math.log(1 + (self.N - n + 0.5) / (n + 0.5)) for t, n in df.items()}

    def score(self, q_tokens, i):
        s, tf, dl = 0.0, self.tf[i], self.dl[i]
        for t in q_tokens:
            f = tf.get(t, 0)
            if f:
                s += self.idf.get(t, 0.0) * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
        return s


class LexicalIndex:
    def __init__(self, chunks):
        self.chunks = chunks
        self.bm25 = BM25([tokenize(c["text"]) for c in chunks])

    def search(self, query, category=None, k=TOPK):
        q = tokenize(query)
        scored = [(self.bm25.score(q, i), i) for i, c in enumerate(self.chunks) if category in (None, c["category"])]
        scored.sort(key=lambda x: (-x[0], x[1]))
        return [(s, self.chunks[i]) for s, i in scored[:k]]


# roteamento de C0 por palavras-chave (definido sem consulta aos chamados de teste)
KEYWORDS = {
    "spring-boot": ["spring boot", "spring", "springboot", "actuator", "hikari", "hikaricp", "bean", "beans", "jpa", "hibernate",
                    "maven", "gradle", "@transactional", "transactional", "@valid", "@restcontroller", "@service", "@autowired",
                    "application.properties", "application.yml", "starter", "jvm", "heap", "java", "jar", "controller", "dto"],
    "docker": ["docker", "dockerfile", "docker-compose", "docker compose", "compose", "contenir", "conteiner", "container",
               "imagem", "imagens", "volume", "volumes", "multi-stage", "dockerignore", ".dockerignore", "entrypoint", "healthcheck",
               "docker run", "docker build", "docker ps", "registry", "bind mount"],
    "azure": ["azure", "app service", "key vault", "resource group", "grupo de recursos", "container apps", "container app",
              "az login", "az ", "acr", "managed identity", "identidade gerenciada", "slot", "slots", "application insights",
              "assinatura", "subscription", "regiao", "orcamento", "rbac", "tag", "tags"],
    "sql-server": ["sql server", "sqlserver", "mssql", "sql", "t-sql", "tsql", "deadlock", "indice", "indices", "index", "clustered",
                   "backup", "restore", "collation", "stored procedure", "procedure", "tabela", "query", "consulta", "offset",
                   "fetch", ".ldf", "login", "isolamento", "read committed", "transacao", "banco de dados", "banco"],
    "nextjs": ["next.js", "nextjs", "next/image", "react", "app router", "pages router", "use client", "server component",
               "hidratacao", "hydration", "next.config", "next build", "next dev", "next start", "route.ts", "next_public",
               "jsx", "tsx", "pnpm", "npm", "ssr", "ssg", "front-end", "frontend", "bundle"],
}


def _kw_regex(kw: str):
    return re.compile(r"(?<![a-z0-9_])" + re.escape(norm(kw)) + r"(?![a-z0-9_])")


KW_COMPILED = {cat: [(_kw_regex(k), 2 if (" " in k or "." in k or "-" in k) else 1) for k in kws] for cat, kws in KEYWORDS.items()}


def route_keywords(question: str) -> str:
    q = norm(question)
    scores = {cat: sum(w * len(rx.findall(q)) for rx, w in rxs) for cat, rxs in KW_COMPILED.items()}
    best = max(scores.values())
    winners = [c for c, s in scores.items() if s == best]
    return winners[0] if best > 0 and len(winners) == 1 else UNDEF


# HTTP
def http_post_json(url, body, headers, timeout, retries=5):
    data = json.dumps(body).encode("utf-8")
    attempts, status, raw, t_ms = 0, 0, b"", 0.0
    for attempt in range(retries + 1):
        attempts += 1
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                status, raw = r.status, r.read()
        except urllib.error.HTTPError as e:
            status, raw = e.code, e.read() or b""
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            status, raw = 0, str(e).encode("utf-8")
        t_ms = (time.perf_counter() - t0) * 1000
        if status == 429 or status >= 500 or status == 0:
            if attempt < retries:
                time.sleep(min(60, 2 ** attempt))
                continue
        break
    try:
        parsed = json.loads(raw.decode("utf-8")) if raw else None
    except Exception:
        parsed = {"_raw": raw.decode("utf-8", "replace")[:2000]}
    return {"status": status, "latency_ms": round(t_ms, 1), "attempts": attempts, "body": parsed}


# Interpretação das respostas da API
def canon_category(v) -> str:
    if v is None:
        return UNDEF
    s = re.sub(r"[\s_]+", "-", norm(str(v)).strip())
    s = s.replace("next.js", "nextjs").replace("next-js", "nextjs")
    aliases = {"springboot": "spring-boot", "spring": "spring-boot", "sqlserver": "sql-server", "mssql": "sql-server",
               "sql": "sql-server", "next": "nextjs"}
    s = aliases.get(s, s)
    return s if s in CATEGORIES else UNDEF


class KnownPaths:
    """Mapeia qualquer string que contenha o nome de um arquivo da KB para 'categoria/arquivo.md'."""
    def __init__(self, chunks):
        self.by_base = {}
        for c in chunks:
            self.by_base[c["path"].rsplit("/", 1)[-1]] = c["path"]

    def resolve(self, raw: str):
        s = str(raw).replace("\\", "/")
        for base, rel in self.by_base.items():
            if base in s:
                return rel
        return None


def normalize_items(lst, known: KnownPaths):
    items = []
    for it in lst:
        if isinstance(it, str):
            items.append({"path": known.resolve(it), "text": it if len(it) > 80 else None, "raw_source": it[:200]})
            continue
        if not isinstance(it, dict):
            continue
        path, raw_src = None, None
        v, _ = first_value(it, ITEM_SOURCE_KEYS)
        if v is not None:
            raw_src = str(v)
            path = known.resolve(raw_src)
        if path is None:
            path = known.resolve(json.dumps(it, ensure_ascii=False))
        t, _ = first_value(it, ITEM_TEXT_KEYS)
        items.append({"path": path, "text": t if isinstance(t, str) else None, "raw_source": raw_src})
    return items


def parse_response(body, known: KnownPaths, retrieval_from_citations=False):
    out = {"answer": None, "category": None, "confidence": None, "retrieved": None, "citations": [], "api_abstained": None}
    if not isinstance(body, dict):
        return out
    a, _ = first_value(body, FIELD_CANDIDATES["answer"])
    out["answer"] = a if isinstance(a, str) else (json.dumps(a, ensure_ascii=False) if a is not None else None)
    c, _ = first_value(body, FIELD_CANDIDATES["category"])
    out["category"] = canon_category(c) if c is not None else None
    cf, _ = first_value(body, FIELD_CANDIDATES["confidence"])
    out["confidence"] = cf if isinstance(cf, (int, float)) else None
    ab, _ = first_value(body, FIELD_CANDIDATES["abstained"])
    if isinstance(ab, bool):
        out["api_abstained"] = ab
    elif isinstance(ab, str) and ab.lower() in ("true", "false"):
        out["api_abstained"] = ab.lower() == "true"
    # trechos recuperados: primeira chave candidata cujo valor seja lista
    retrieved = None
    for key in FIELD_CANDIDATES["retrieved"]:
        v = get_path(body, key)
        if isinstance(v, list):
            retrieved = normalize_items(v, known)
            break
    cits = None
    for key in FIELD_CANDIDATES["citations"]:
        v = get_path(body, key)
        if isinstance(v, list):
            cits = normalize_items(v, known)
            break
    out["citations"] = [x["path"] for x in (cits or []) if x["path"]]
    if retrieved is None and retrieval_from_citations and cits is not None:
        retrieved = cits
    out["retrieved"] = retrieved
    return out


# Relevância, Recall@5, MRR
class Relevance:
    def __init__(self, chunks, granularity="section"):
        self.granularity = granularity
        self.sec_tokens = {(c["path"], c["section"]): set(tokenize(c["text"])) for c in chunks}
        self.fallback_doc_level = 0

    def is_relevant(self, item, ticket) -> bool:
        if item.get("path") != ticket["expectedSource"]:
            return False
        if self.granularity == "document":
            return True
        text = item.get("text")
        if not text:
            self.fallback_doc_level += 1
            return True
        sec = self.sec_tokens.get((ticket["expectedSource"], ticket["expectedSection"]))
        if not sec:
            return True
        ctoks = set(tokenize(text))
        return len(sec & ctoks) / len(sec) >= 0.5

    def rank(self, retrieved, ticket):
        for i, it in enumerate((retrieved or [])[:TOPK], 1):
            if self.is_relevant(it, ticket):
                return i
        return None


# Execução das configurações
def load_jsonl(path: Path):
    rows = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                rows[r["ticketId"]] = r
    return rows


def append_jsonl(path: Path, row):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def run_api_config(cfg, tickets, args, outdir):
    raw_path = outdir / f"raw_{cfg}.jsonl"
    if args.force and raw_path.exists():
        raw_path.unlink()
    done = load_jsonl(raw_path)
    url = f"{args.base_url.rstrip('/')}/api/{cfg}/ask"
    headers = {"Content-Type": "application/json", "X-Run-Id": args.run_id}
    todo = [t for t in tickets if t["ticketId"] not in done or done[t["ticketId"]].get("status") != 200]
    if todo:
        print(f"[{cfg.upper()}] {len(todo)} chamados a executar ({len(tickets) - len(todo)} já em cache) -> {url}")
    for i, t in enumerate(todo, 1):
        res = http_post_json(url, {args.payload_key: t["question"]}, headers, args.timeout,
                             retries=1 if i == 1 else 5)
        if i == 1 and res["status"] == 0:
            raise SystemExit(f"API inacessível em {url} ({(res['body'] or {}).get('_raw', '')[:120]}). "
                             "Confira se o docker compose está de pé e o --base-url.")
        res["ticketId"] = t["ticketId"]
        done[t["ticketId"]] = res
        # reescreve o cache de forma idempotente (última tentativa vence)
        append_jsonl(raw_path, res)
        if i % 10 == 0 or i == len(todo):
            print(f"    {cfg.upper()} {i}/{len(todo)}  (último HTTP {res['status']}, {res['latency_ms']} ms)")
    # consolida (última linha por ticket vence)
    return load_jsonl(raw_path)


JUDGE_SYSTEM = (
    "Você é um avaliador rigoroso de FIDELIDADE de respostas geradas por um sistema de suporte técnico com recuperação de "
    "documentos (RAG). Sua tarefa é verificar se cada afirmação factual da RESPOSTA é sustentada pelo CONTEXTO fornecido.\n"
    "Regras:\n"
    "1. Decomponha a RESPOSTA em afirmações factuais atômicas (valores, nomes, comandos, regras, condições).\n"
    "2. Uma afirmação é 'supported' = true somente se o CONTEXTO a sustenta de forma explícita ou por paráfrase direta. "
    "Conhecimento externo, mesmo correto, NÃO conta: se não está no contexto, supported = false.\n"
    "3. Frases de cortesia, de encaminhamento ao atendente ou de recomendação genérica sem conteúdo factual não são afirmações.\n"
    "4. Se a RESPOSTA declara que não encontrou a informação, não sabe, ou que o contexto é insuficiente (abstenção), "
    "retorne abstained = true e claims = [].\n"
    "5. Não avalie se a resposta é útil ou completa; avalie apenas se o que foi afirmado é sustentado pelo contexto.\n"
    "Responda SOMENTE com JSON válido no formato: "
    '{"abstained": true|false, "claims": [{"text": "...", "supported": true|false}]}'
)


def build_judge_context(rec, kb_text_by_path, max_chars=12000):
    items = rec.get("retrieved") or []
    parts = []
    if any(it.get("text") for it in items):
        for it in items:
            if it.get("text"):
                parts.append(f"[Fonte: {it.get('path') or it.get('raw_source') or 'desconhecida'}]\n{it['text']}")
        basis = "retrieved_text"
    else:
        paths = []
        for p in [it.get("path") for it in items] + list(rec.get("citations") or []):
            if p and p not in paths:
                paths.append(p)
        for p in paths:
            if p in kb_text_by_path:
                parts.append(f"[Documento completo: {p}]\n{kb_text_by_path[p]}")
        basis = "kb_documents_of_retrieved_or_cited" if parts else "none"
    return "\n\n".join(parts)[:max_chars], basis


def call_judge(question, context, answer, args):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise SystemExit("OPENAI_API_KEY não definida (necessária para o juiz LLM). Use --skip-judge para pular.")
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    body = {
        "model": args.judge_model, "temperature": 0, "seed": 42,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": f"PERGUNTA:\n{question}\n\nCONTEXTO:\n{context or '(vazio)'}\n\nRESPOSTA:\n{answer}"},
        ],
    }
    res = http_post_json(f"{base}/chat/completions", body, {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}, args.timeout)
    if res["status"] != 200 or not isinstance(res["body"], dict):
        return {"error": f"HTTP {res['status']}", "usage": {}}
    try:
        msg = res["body"]["choices"][0]["message"]["content"]
        j = json.loads(msg)
        claims = [{"text": str(c.get("text", "")), "supported": bool(c.get("supported"))} for c in j.get("claims", []) if isinstance(c, dict)]
        return {"abstained": bool(j.get("abstained", False)), "claims": claims, "usage": res["body"].get("usage", {}), "error": None}
    except Exception as e:  # noqa: BLE001
        return {"error": f"parse: {e}", "usage": res["body"].get("usage", {})}


# Montagem dos registros por (config, chamado)
def build_records(cfg, tickets, raw, known, args):
    recs = {}
    for t in tickets:
        r = raw.get(t["ticketId"])
        rec = {"cfg": cfg, "ticket": t, "ok": False, "status": None, "latency_ms": None, "answer": None, "category": None,
               "confidence": None, "retrieved": None, "citations": [], "api_abstained": None, "error": None}
        if r is None:
            rec["error"] = "sem execução"
        else:
            rec["status"], rec["latency_ms"] = r.get("status"), r.get("latency_ms")
            if r.get("status") == 200:
                p = parse_response(r.get("body"), known, args.retrieval_from_citations)
                rec.update(p)
                rec["ok"] = True
            else:
                rec["error"] = f"HTTP {r.get('status')}"
        recs[t["ticketId"]] = rec
    return recs


def run_c0(tickets, index, args):
    recs = {}
    for t in tickets:
        cat = route_keywords(t["question"])
        hits = index.search(t["question"], category=None if cat == UNDEF else cat)
        retrieved = [{"path": c["path"], "text": c["text"], "raw_source": c["path"], "score": round(s, 3)} for s, c in hits]
        abst = None
        if args.c0_min_score is not None:
            abst = (not hits) or hits[0][0] < args.c0_min_score
        recs[t["ticketId"]] = {"cfg": "c0", "ticket": t, "ok": True, "status": 200, "latency_ms": None, "answer": None,
                               "category": cat, "confidence": None, "retrieved": retrieved, "citations": [],
                               "api_abstained": abst, "error": None}
    return recs


def evaluate_judge(cfg, recs, args, outdir, kb_text_by_path):
    jpath = outdir / f"judge_{cfg}.jsonl"
    if args.force and jpath.exists():
        jpath.unlink()
    cache = load_jsonl(jpath)
    todo = []
    for tid, rec in recs.items():
        if not rec["ok"]:
            continue
        rec["judge"] = None
        if rec["api_abstained"] is True or not (rec["answer"] or "").strip():
            # abstenção declarada pela API (ou resposta vazia): sem chamada ao juiz
            rec["judge"] = {"abstained": True, "claims": [], "usage": {}, "error": None, "skipped": True, "context_basis": "-"}
        elif tid in cache and not cache[tid].get("error"):
            rec["judge"] = cache[tid]
        else:
            todo.append(rec)
    if args.skip_judge:
        return
    if todo:
        print(f"[JUIZ {cfg.upper()}] {len(todo)} julgamentos ({args.judge_model}, temperature=0)")
    for i, rec in enumerate(todo, 1):
        ctx, basis = build_judge_context(rec, kb_text_by_path)
        j = call_judge(rec["ticket"]["question"], ctx, rec["answer"], args)
        j.update({"ticketId": rec["ticket"]["ticketId"], "context_basis": basis, "context_chars": len(ctx)})
        rec["judge"] = j
        append_jsonl(jpath, j)
        if i % 10 == 0 or i == len(todo):
            print(f"    juiz {cfg.upper()} {i}/{len(todo)}")


def final_abstained(rec):
    """Abstenção: indicador da API quando existir; senão veredito do juiz; senão None."""
    if rec["api_abstained"] is not None:
        return rec["api_abstained"]
    j = rec.get("judge")
    if j and not j.get("error"):
        return bool(j.get("abstained"))
    return None


def judge_counts(rec):
    j = rec.get("judge")
    if not j or j.get("error") or final_abstained(rec) is True:
        return None
    tot = len(j.get("claims", []))
    sup = sum(1 for c in j["claims"] if c.get("supported"))
    return (sup, tot)


# Métricas
def triage_metrics(recs):
    valid = [r for r in recs.values() if r["ok"] and r["category"] is not None]
    n = len(valid)
    correct = sum(1 for r in valid if r["category"] == r["ticket"]["expectedCategory"])
    per_class = {}
    for c in CATEGORIES:
        tp = sum(1 for r in valid if r["category"] == c and r["ticket"]["expectedCategory"] == c)
        fp = sum(1 for r in valid if r["category"] == c and r["ticket"]["expectedCategory"] != c)
        fn = sum(1 for r in valid if r["category"] != c and r["ticket"]["expectedCategory"] == c)
        p = tp / (tp + fp) if tp + fp else 0.0
        rc = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * p * rc / (p + rc) if p + rc else 0.0
        per_class[c] = {"precision": p, "recall": rc, "f1": f1, "support": tp + fn}
    macro = sum(v["f1"] for v in per_class.values()) / len(CATEGORIES)
    labels = CATEGORIES + [UNDEF]
    cm = {t: {p: 0 for p in labels} for t in CATEGORIES}
    for r in valid:
        cm[r["ticket"]["expectedCategory"]][r["category"] if r["category"] in labels else UNDEF] += 1
    amb = [r for r in valid if r["ticket"]["isAmbiguous"]]
    non = [r for r in valid if not r["ticket"]["isAmbiguous"]]
    acc = lambda lst: pct(sum(1 for r in lst if r["category"] == r["ticket"]["expectedCategory"]), len(lst))
    return {"n": n, "accuracy": pct(correct, n), "macro_f1": 100 * macro, "per_class": per_class, "cm": cm, "labels": labels,
            "acc_ambiguous": acc(amb), "n_ambiguous": len(amb), "acc_non_ambiguous": acc(non), "n_non_ambiguous": len(non)}


def quality_metrics(recs, rel: Relevance, have_retrieval=True):
    with_ans = [r for r in recs.values() if r["ok"] and r["ticket"]["hasAnswer"]]
    no_ans = [r for r in recs.values() if r["ok"] and not r["ticket"]["hasAnswer"]]
    m = {"n_with": len(with_ans), "n_without": len(no_ans)}
    if have_retrieval and with_ans and all(r["retrieved"] is not None for r in with_ans):
        ranks = [rel.rank(r["retrieved"], r["ticket"]) for r in with_ans]
        m["recall5"] = pct(sum(1 for x in ranks if x), len(ranks))
        m["mrr"] = sum(1 / x for x in ranks if x) / len(ranks)
    else:
        m["recall5"], m["mrr"] = None, None
    ab_no = [final_abstained(r) for r in no_ans]
    ab_with = [final_abstained(r) for r in with_ans]
    m["abstention_correct"] = pct(sum(1 for a in ab_no if a is True), sum(1 for a in ab_no if a is not None))
    m["refusal_wrong"] = pct(sum(1 for a in ab_with if a is True), sum(1 for a in ab_with if a is not None))
    # fidelidade e alucinação: chamados com solução e resposta não abstida
    sup = tot = n_eval = n_hall = 0
    for r in with_ans:
        c = judge_counts(r)
        if c is None:
            continue
        s, t = c
        n_eval += 1
        sup += s
        tot += t
        n_hall += 1 if s < t else 0
    m["fidelity"] = pct(sup, tot) if tot else None
    m["hallucination"] = pct(n_hall, n_eval) if n_eval else None
    m["n_judged"] = n_eval
    # respostas dadas a chamados sem solução
    ans_no = [r for r in no_ans if final_abstained(r) is False]
    m["answered_when_no_solution"] = len(ans_no)
    return m


def stratum_metrics(recs_subset, rel: Relevance):
    q = quality_metrics({r["ticket"]["ticketId"]: r for r in recs_subset}, rel)
    return q


# Saídas
def print_and_save_table1(triage_by_cfg, outdir):
    print("\n" + "=" * 100 + "\nTABELA 1 – Triagem (categoria prevista x categoria de referência, 100 chamados)\n" + "=" * 100)
    rows = []
    for cfg, m in triage_by_cfg.items():
        rows.append([cfg.upper(), m["n"], fmt(m["accuracy"]), fmt(m["macro_f1"]), f"{fmt(m['acc_ambiguous'])} (n={m['n_ambiguous']})",
                     f"{fmt(m['acc_non_ambiguous'])} (n={m['n_non_ambiguous']})"])
    hdr = ["Config", "n", "Acurácia %", "F1 macro %", "Acurácia ambíguos %", "Acurácia não ambíguos %"]
    print(table_text(hdr, rows))
    write_csv(outdir / "table1_triage_summary.csv", hdr, rows)
    pc_rows = []
    for cfg, m in triage_by_cfg.items():
        print(f"\nF1 por classe – {cfg.upper()}")
        sub = []
        for c in CATEGORIES:
            v = m["per_class"][c]
            sub.append([c, fmt(100 * v["precision"]), fmt(100 * v["recall"]), fmt(100 * v["f1"]), v["support"]])
            pc_rows.append([cfg, c, round(100 * v["precision"], 2), round(100 * v["recall"], 2), round(100 * v["f1"], 2), v["support"]])
        print(table_text(["Classe", "Precisão %", "Revocação %", "F1 %", "Suporte"], sub))
        print(f"\nMatriz de confusão – {cfg.upper()} (linhas = referência, colunas = previsto)")
        labels = m["labels"]
        print(table_text(["ref \\ prev"] + labels, [[t] + [m["cm"][t][p] for p in labels] for t in CATEGORIES]))
        write_csv(outdir / f"table1_confusion_{cfg}.csv", ["referencia"] + labels, [[t] + [m["cm"][t][p] for p in labels] for t in CATEGORIES])
    write_csv(outdir / "table1_per_class.csv", ["config", "classe", "precisao_pct", "revocacao_pct", "f1_pct", "suporte"], pc_rows)


def print_and_save_table2(qual_by_cfg, outdir, retrieval_note):
    print("\n" + "=" * 100 + "\nTABELA 2 – Recuperação, fidelidade e abstenção\n" + "=" * 100)
    hdr = ["Config", "Recall@5 %", "MRR", "Fidelidade %", "Alucinação %", "Abstenção correta %", "Recusa indevida %",
           "n com sol.", "n sem sol.", "n julgadas"]
    rows, csv_rows = [], []
    for cfg, m in qual_by_cfg.items():
        rows.append([cfg.upper(), fmt(m["recall5"]), fmt(m["mrr"], 3), fmt(m["fidelity"]), fmt(m["hallucination"]),
                     fmt(m["abstention_correct"]), fmt(m["refusal_wrong"]), m["n_with"], m["n_without"], m["n_judged"]])
        csv_rows.append([cfg, m["recall5"], m["mrr"], m["fidelity"], m["hallucination"], m["abstention_correct"],
                         m["refusal_wrong"], m["n_with"], m["n_without"], m["n_judged"]])
    print(table_text(hdr, rows))
    print("Definições: Recall@5 e MRR sobre os chamados COM solução; Fidelidade = afirmações sustentadas / afirmações totais "
          "(micro, respostas não abstidas aos chamados COM solução); Alucinação = % dessas respostas com ao menos 1 afirmação "
          "não sustentada; Abstenção correta sobre os SEM solução; Recusa indevida sobre os COM solução.")
    print("C0 não gera texto: fidelidade/alucinação não se aplicam; abstenção só existe com --c0-min-score.")
    if retrieval_note:
        print("AVISO:", retrieval_note)
    write_csv(outdir / "table2_quality.csv", ["config", "recall5_pct", "mrr", "fidelidade_pct", "alucinacao_pct", "abstencao_correta_pct",
                                              "recusa_indevida_pct", "n_com_solucao", "n_sem_solucao", "n_julgadas"], csv_rows)


def print_and_save_table3(all_recs, rel, outdir):
    print("\n" + "=" * 100 + "\nTABELA 3 – Propagação de erro de triagem (somente chamados COM solução)\n" + "=" * 100)
    c2 = all_recs.get("c2")
    if not c2:
        print("C2 indisponível: Tabela 3 não calculada.")
        return
    strata = {"triagem_certa": [], "triagem_errada": []}
    for tid, r in c2.items():
        t = r["ticket"]
        if not (r["ok"] and t["hasAnswer"] and r["category"] is not None):
            continue
        strata["triagem_certa" if r["category"] == t["expectedCategory"] else "triagem_errada"].append(tid)
    print(f"Estratificação pela triagem do C2: certa n={len(strata['triagem_certa'])}, errada n={len(strata['triagem_errada'])} "
          f"(mesmos chamados aplicados a todas as configurações)")
    if len(strata["triagem_errada"]) < 5:
        print("AVISO: poucos erros de triagem; a comparação é frágil.")
    hdr = ["Config", "Estrato", "n", "Recall@5 %", "MRR", "Fidelidade %", "Alucinação %", "Recusa indevida %"]
    rows, csv_rows, store = [], [], {}
    for cfg, recs in all_recs.items():
        if cfg == "c0":  # estratificação usa a triagem de C2
            continue
        for name, ids in strata.items():
            subset = [recs[i] for i in ids if i in recs]
            m = quality_metrics({r["ticket"]["ticketId"]: r for r in subset}, rel)
            store[(cfg, name)] = m
            rows.append([cfg.upper(), name, len(subset), fmt(m["recall5"]), fmt(m["mrr"], 3), fmt(m["fidelity"]), fmt(m["hallucination"]), fmt(m["refusal_wrong"])])
            csv_rows.append([cfg, name, len(subset), m["recall5"], m["mrr"], m["fidelity"], m["hallucination"], m["refusal_wrong"]])
    print(table_text(hdr, rows))
    # diferenças em pontos percentuais
    def delta(a, b, name, key):
        if (a, name) in store and (b, name) in store:
            x, y = store[(a, name)][key], store[(b, name)][key]
            return None if x is None or y is None else x - y
        return None
    drow, delta_csv = [], []
    for name in strata:
        for key, label in [("recall5", "Recall@5"), ("fidelity", "Fidelidade"), ("hallucination", "Alucinação")]:
            d21, d32 = delta("c2", "c1", name, key), delta("c3", "c2", name, key)
            drow.append([name, label, fmt(d21), fmt(d32)])
            delta_csv.append([name, label, d21, d32])
    print("\nDiferença em pontos percentuais (C2 − C1 = efeito do filtro; C3 − C2 = efeito do limiar)")
    print(table_text(["Estrato", "Métrica", "C2 − C1 (pp)", "C3 − C2 (pp)"], drow))
    write_csv(outdir / "table3_propagation.csv", ["config", "estrato", "n", "recall5_pct", "mrr", "fidelidade_pct",
                                                  "alucinacao_pct", "recusa_indevida_pct"], csv_rows)
    write_csv(outdir / "table3_deltas_pp.csv", ["estrato", "metrica", "c2_menos_c1_pp", "c3_menos_c2_pp"], delta_csv)


def export_per_ticket(all_recs, rel, outdir):
    rows = []
    for cfg, recs in all_recs.items():
        for tid, r in sorted(recs.items()):
            t = r["ticket"]
            rank = rel.rank(r["retrieved"], t) if (t["hasAnswer"] and r["retrieved"] is not None) else None
            jc = judge_counts(r)
            rows.append([cfg, tid, t["expectedCategory"], r["category"], (r["category"] == t["expectedCategory"]) if r["category"] else "",
                         t["hasAnswer"], t["isAmbiguous"], r["status"], r["latency_ms"], rank, final_abstained(r),
                         jc[1] if jc else "", jc[0] if jc else "", r["error"] or ""])
    write_csv(outdir / "per_ticket_results.csv", ["config", "ticketId", "categoria_ref", "categoria_prevista", "triagem_ok", "tem_solucao",
                                                  "ambiguo", "http", "latencia_cliente_ms", "rank_relevante", "abstenção", "afirmacoes_total",
                                                  "afirmacoes_sustentadas", "erro"], rows)


def export_manual_sample(all_recs, args, outdir):
    rng = random.Random(args.sample_seed)
    rows = []
    for cfg in API_CONFIGS:
        recs = all_recs.get(cfg, {})
        judged = [r for r in recs.values() if r.get("judge") and not r["judge"].get("error") and not r["judge"].get("skipped")]
        judged.sort(key=lambda r: r["ticket"]["ticketId"])
        k = math.ceil(0.2 * len(judged))
        for r in rng.sample(judged, k) if k else []:
            j = r["judge"]
            ctx_txt = "\n---\n".join((it.get("text") or "")[:600] for it in (r["retrieved"] or []) if it.get("text"))[:3000]
            claims = " || ".join(("[OK] " if c["supported"] else "[NÃO SUSTENTADA] ") + c["text"] for c in j.get("claims", []))
            all_ok = all(c["supported"] for c in j.get("claims", [])) if not j.get("abstained") else ""
            rows.append([cfg, r["ticket"]["ticketId"], r["ticket"]["hasAnswer"], r["ticket"]["question"], r["answer"], ctx_txt,
                         j.get("abstained"), all_ok, claims, "", "", ""])
    hdr = ["config", "ticketId", "tem_solucao", "pergunta", "resposta", "contexto_trechos", "juiz_abstencao", "juiz_tudo_sustentado",
           "juiz_afirmacoes", "manual_abstencao (S/N)", "manual_tudo_sustentado (S/N)", "comentarios"]
    p = outdir / "judge_sample_20pct.csv"
    write_csv(p, hdr, rows)
    print(f"\nAmostra para conferência manual (20% dos julgamentos por configuração, seed {args.sample_seed}): {len(rows)} linhas -> {p}")


def cohen_kappa(a, b):
    n = len(a)
    if not n:
        return None
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pa, pb = Counter(a), Counter(b)
    pe = sum((pa[k] / n) * (pb[k] / n) for k in set(a) | set(b))
    return None if pe == 1 else (po - pe) / (1 - pe)


def agreement(path: Path):
    def yn(v):
        v = (v or "").strip().lower()
        return True if v in ("s", "sim", "true", "1", "y", "yes") else False if v in ("n", "nao", "não", "false", "0", "no") else None
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    ab_j, ab_m, ok_j, ok_m = [], [], [], []
    for r in rows:
        a_j, a_m = yn(r["juiz_abstencao"]), yn(r["manual_abstencao (S/N)"])
        if a_m is not None and a_j is not None:
            ab_j.append(a_j)
            ab_m.append(a_m)
        s_j, s_m = yn(r["juiz_tudo_sustentado"]), yn(r["manual_tudo_sustentado (S/N)"])
        if s_j is not None and s_m is not None:
            ok_j.append(s_j)
            ok_m.append(s_m)
    print(f"Linhas na planilha: {len(rows)}")
    for name, a, b in [("Abstenção", ab_j, ab_m), ("Resposta totalmente sustentada", ok_j, ok_m)]:
        if a:
            agree = pct(sum(1 for x, y in zip(a, b) if x == y), len(a))
            k = cohen_kappa(a, b)
            print(f"{name}: concordância = {fmt(agree)}% (n={len(a)}), kappa de Cohen = {fmt(k, 3)}")
        else:
            print(f"{name}: sem linhas preenchidas.")


# Probe
def probe(tickets, known, args):
    t = tickets[0]
    print(f"Chamado de teste: {t['ticketId']} – {t['question']}\n")
    for cfg in API_CONFIGS:
        url = f"{args.base_url.rstrip('/')}/api/{cfg}/ask"
        res = http_post_json(url, {args.payload_key: t["question"]}, {"Content-Type": "application/json", "X-Run-Id": args.run_id}, args.timeout, retries=0)
        print("=" * 80 + f"\n{cfg.upper()}  HTTP {res['status']}  {res['latency_ms']} ms\n" + "=" * 80)
        print(json.dumps(res["body"], ensure_ascii=False, indent=2)[:3500])
        p = parse_response(res["body"], known, args.retrieval_from_citations)
        print("\n-> Interpretação do runner:")
        ans_msg = "OK" if p["answer"] else 'NÃO ENCONTRADA (ajuste FIELD_CANDIDATES["answer"])'
        cat_msg = p["category"] if p["category"] is not None else "não informada (esperado em C2/C3)"
        if p["retrieved"] is not None:
            ret_msg = "%d itens, fontes=%s" % (len(p["retrieved"]), [x["path"] for x in p["retrieved"]])
        else:
            ret_msg = "NÃO ENCONTRADO (Recall@5/MRR indisponíveis; exponha o top-5)"
        print("   resposta        : " + ans_msg)
        print("   categoria       : " + str(cat_msg))
        print("   top-5 recuperado: " + ret_msg)
        if p["retrieved"]:
            has_text = any(x.get("text") for x in p["retrieved"])
            print("   texto dos trechos: " + ("sim" if has_text else "não (relevância por documento; juiz usará o documento completo da KB)"))
        print("   citações        : " + str(p["citations"]))
        print("   abstenção (API) : " + str(p["api_abstained"]) + "\n")


# main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default="http://localhost:8080")
    ap.add_argument("--tickets", default="data/tickets-100.json")
    ap.add_argument("--kb", default="data/kb")
    ap.add_argument("--out", default="results/eval-100")
    ap.add_argument("--run-id", default="eval-100")
    ap.add_argument("--payload-key", default="question", help='chave do corpo JSON com a pergunta (padrão: "question")')
    ap.add_argument("--judge-model", default="gpt-4o-mini")
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--granularity", choices=["section", "document"], default="section",
                    help="relevância do trecho: mesma seção do gabarito (padrão) ou apenas mesmo documento")
    ap.add_argument("--sample-seed", type=int, default=42)
    ap.add_argument("--c0-min-score", type=float, default=None, help="limiar BM25 para abstenção do C0 (opcional; sem isso, abstenção = N/D)")
    ap.add_argument("--retrieval-from-citations", action="store_true", help="usa as citações como 'recuperados' se a API não expuser o top-5")
    ap.add_argument("--c0-only", action="store_true")
    ap.add_argument("--skip-api", action="store_true", help="não chama a API; usa apenas o cache em --out")
    ap.add_argument("--skip-judge", action="store_true")
    ap.add_argument("--force", action="store_true", help="refaz chamadas e julgamentos (ignora o cache)")
    ap.add_argument("--probe", action="store_true", help="envia 1 chamado a cada rota e mostra como o runner interpreta a resposta")
    ap.add_argument("--agreement", metavar="CSV", help="calcula concordância juiz x manual a partir do CSV preenchido e sai")
    args = ap.parse_args()

    if args.agreement:
        agreement(Path(args.agreement))
        return 0

    tickets = json.loads(Path(args.tickets).read_text(encoding="utf-8"))
    chunks = load_kb_chunks(Path(args.kb))
    known = KnownPaths(chunks)
    kb_text_by_path = {}
    for p in sorted({c["path"] for c in chunks}):
        kb_text_by_path[p] = (Path(args.kb) / p).read_text(encoding="utf-8")

    if args.probe:
        probe(tickets, known, args)
        return 0

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    rel = Relevance(chunks, args.granularity)
    started = datetime.now(timezone.utc).isoformat()

    all_recs = {}
    index = LexicalIndex(chunks)
    all_recs["c0"] = run_c0(tickets, index, args)

    if not args.c0_only:
        for cfg in API_CONFIGS:
            raw = run_api_config(cfg, tickets, args, outdir) if not args.skip_api else load_jsonl(outdir / f"raw_{cfg}.jsonl")
            all_recs[cfg] = build_records(cfg, tickets, raw, known, args)
            evaluate_judge(cfg, all_recs[cfg], args, outdir, kb_text_by_path)

    # avisos
    for cfg, recs in all_recs.items():
        bad = [r for r in recs.values() if not r["ok"]]
        if bad:
            print(f"AVISO [{cfg.upper()}]: {len(bad)} chamados sem resposta válida (ex.: {bad[0]['error']}); excluídos das métricas.")
    retrieval_note = None
    for cfg in API_CONFIGS:
        recs = all_recs.get(cfg)
        if recs and any(r["ok"] for r in recs.values()) and all(r["retrieved"] is None for r in recs.values() if r["ok"]):
            retrieval_note = ("a API não expôs os trechos recuperados (top-5): Recall@5/MRR indisponíveis para " + cfg.upper() +
                              ". Exponha o top-5 no modo de avaliação ou use --retrieval-from-citations (aproximação).")

    # tabelas
    triage = {cfg: triage_metrics(recs) for cfg, recs in all_recs.items() if cfg != "c1"}
    print_and_save_table1(triage, outdir)
    qual = {cfg: quality_metrics(recs, rel) for cfg, recs in all_recs.items()}
    print_and_save_table2(qual, outdir, retrieval_note)
    print_and_save_table3(all_recs, rel, outdir)
    export_per_ticket(all_recs, rel, outdir)
    if not args.skip_judge and not args.c0_only:
        export_manual_sample(all_recs, args, outdir)

    if rel.fallback_doc_level:
        print(f"\nNOTA: {rel.fallback_doc_level} verificações de relevância usaram nível de documento (trecho sem texto na resposta da API).")

    # metadados da rodada
    tok_in = tok_out = n_calls = 0
    for cfg in API_CONFIGS:
        for r in all_recs.get(cfg, {}).values():
            j = r.get("judge")
            if j and not j.get("skipped"):
                u = j.get("usage") or {}
                tok_in += u.get("prompt_tokens", 0)
                tok_out += u.get("completion_tokens", 0)
                n_calls += 1
    meta = {"started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(), "run_id": args.run_id,
            "base_url": args.base_url, "judge_model": args.judge_model, "judge_temperature": 0, "judge_seed": 42,
            "granularity": args.granularity, "tickets_file": args.tickets, "n_tickets": len(tickets),
            "judge_calls": n_calls, "judge_tokens_prompt": tok_in, "judge_tokens_completion": tok_out,
            "python": sys.version.split()[0], "argv": sys.argv[1:],
            "note": "Tokens do juiz não entram no custo por chamado."}
    (outdir / "run_metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nJuiz: {n_calls} chamadas, {tok_in} tokens de entrada, {tok_out} de saída (registrar à parte no custo).")
    print(f"Arquivos em {outdir}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
