#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera as tabelas (tabelas.md) e os graficos (PNG) do artigo a partir de results/eval-100/,
output/metrics/requests.csv e output/stats/. Nao chama nenhuma API.
Sem --price-in/--price-out, a coluna de custo e o grafico de projecao sao omitidos.

Uso: python scripts/generate_article_assets.py --price-in 0.15 --price-out 0.60 --price-date 2026-10-19
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

try:  # seaborn e opcional
    import seaborn as sns
except ImportError:  # pragma: no cover
    sns = None

# constantes
INK, INK2, GRID, AXIS = "#0b0b0b", "#52514e", "#e6e5e1", "#c9c8c3"
# uma cor fixa por configuracao; C0 em cinza
CFG_COLOR = {"C0": "#7c7b76", "C1": "#2a78d6", "C2": "#eb6834", "C3": "#1baf7a"}
CFG_MARKER = {"C1": "o", "C2": "s", "C3": "^"}
STAGE_COLOR = {"triage": "#cfcec9", "search": "#97968f", "generation": "#5a5954"}
STAGE_LABEL = {"triage": "Triagem", "search": "Busca", "generation": "Geração"}
CLASS_LABEL = {"spring-boot": "Spring Boot", "docker": "Docker", "azure": "Azure",
               "sql-server": "SQL Server", "nextjs": "Next.js"}
SOURCE = "Fonte: Dados da pesquisa, 2026."
LOAD_CONFIGS = ["C1", "C2", "C3"]


# utilitarios
def br(x, d: int = 1, thousands: bool = True) -> str:
    """Formata no padrao brasileiro; NaN/None vira travessao."""
    if x is None or (isinstance(x, float) and math.isnan(x)) or pd.isna(x):
        return "—"
    s = f"{x:,.{d}f}" if thousands else f"{x:.{d}f}"
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def parse_pt(value):
    """'60,0' -> 60.0; '36,4 (n=22)' -> (36.4, 22)."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None, None
    if isinstance(value, (int, float)):
        return float(value), None
    m = re.match(r"^\s*(-?[\d.,]+)\s*(?:\(n\s*=\s*(\d+)\))?\s*$", str(value))
    if not m:
        return None, None
    num = m.group(1)
    num = num.replace(".", "").replace(",", ".") if "," in num else num
    return float(num), (int(m.group(2)) if m.group(2) else None)


def md_table(headers, rows, align=None) -> str:
    align = align or (["l"] + ["r"] * (len(headers) - 1))
    sep = ["---:" if a == "r" else (":---:" if a == "c" else ":---") for a in align]
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(sep) + " |"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def read_csv(path: Path, warn: list[str], required: bool = True):
    if not path.exists():
        if required:
            warn.append(f"Arquivo não encontrado: {path}")
        return None
    return pd.read_csv(path, encoding="utf-8-sig")


def to_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().eq("true")


# Tabelas 1-3 (qualidade)
def table1(qdir: Path, warn: list[str]) -> str | None:
    summ = read_csv(qdir / "table1_triage_summary.csv", warn)
    per = read_csv(qdir / "table1_per_class.csv", warn)
    if summ is None or per is None:
        return None
    summ.columns = ["config", "n", "acc", "f1", "acc_amb", "acc_nao"][: len(summ.columns)]
    per["config"] = per["config"].str.upper()
    classes = list(dict.fromkeys(per["classe"]))
    f1 = per.pivot(index="config", columns="classe", values="f1_pct")

    def amb(v):
        x, n = parse_pt(v)
        return "—" if x is None else br(x, 1) + (f" (n={n})" if n else "")

    headers = ["Configuração", "Acurácia (%)", "F1 macro (%)"] + [f"F1 {CLASS_LABEL.get(c, c)} (%)" for c in classes] \
        + ["Acurácia, ambíguos (%)", "Acurácia, não ambíguos (%)"]
    rows = []
    for _, r in summ.iterrows():
        cfg = str(r["config"]).upper()
        rows.append([cfg, br(parse_pt(r["acc"])[0]), br(parse_pt(r["f1"])[0])]
                    + [br(f1.loc[cfg, c]) if cfg in f1.index else "—" for c in classes]
                    + [amb(r["acc_amb"]), amb(r["acc_nao"])])
    n = int(summ["n"].iloc[0]) if "n" in summ else 100
    return (f"**Tabela 1 – Desempenho da triagem por configuração (n = {n} chamados)**\n\n"
            + md_table(headers, rows) + f"\n\n{SOURCE}\n\n"
            "Nota: C0 = regras por palavra-chave (chamados sem regra aplicável contam como erro); "
            "C2 = triagem por LLM; C3 = C2 com limiar de confiança. F1 macro = média simples do F1 das cinco classes.")


def table2(qdir: Path, warn: list[str]):
    q = read_csv(qdir / "table2_quality.csv", warn)
    if q is None:
        return None, None
    q["config"] = q["config"].str.upper()
    bad = [r["config"] for _, r in q.iterrows()
           if r["config"] in LOAD_CONFIGS and (r.get("recusa_indevida_pct", 0) >= 95 or r.get("recall5_pct", 1) == 0)]
    if bad:
        warn.append(f"QUALIDADE: {', '.join(bad)} com Recall@5 = 0% e/ou recusa indevida ≥ 95%. Isso indica que a busca voltou "
                    "vazia (índice do Qdrant vazio ou desatualizado), não baixa qualidade. Rode python scripts/verify_index.py "
                    "--reingest e refaça a rodada de qualidade antes de usar as Tabelas 2 e 3 e o Gráfico 1.")
    if (q["n_julgadas"].fillna(0) == 0).all():
        warn.append("QUALIDADE: nenhuma resposta foi julgada (n_julgadas = 0): fidelidade e alucinação ficam vazias "
                    "(travessão) e o Gráfico 1 sai sem o painel (c).")
    headers = ["Configuração", "Recall@5 (%)", "MRR", "Fidelidade (%)", "Alucinação (%)",
               "Abstenção correta (%)", "Recusa indevida (%)", "Respostas julgadas"]
    rows = []
    for _, r in q.iterrows():
        rows.append([r["config"], br(r["recall5_pct"]), br(r["mrr"], 3), br(r["fidelidade_pct"]),
                     br(r["alucinacao_pct"]), br(r["abstencao_correta_pct"]), br(r["recusa_indevida_pct"]),
                     br(r["n_julgadas"], 0)])
    n80, n20 = int(q["n_com_solucao"].iloc[0]), int(q["n_sem_solucao"].iloc[0])
    md = (f"**Tabela 2 – Qualidade da recuperação e da geração por configuração ({n80} chamados com solução e {n20} sem solução)**\n\n"
          + md_table(headers, rows) + f"\n\n{SOURCE}\n\n"
          f"Nota: Recall@5 e MRR calculados sobre os {n80} chamados com solução; abstenção correta, sobre os {n20} sem solução; "
          f"recusa indevida, sobre os {n80} com solução. Fidelidade e alucinação não se aplicam a C0 (sem geração); "
          "travessão indica métrica não calculada.")
    return md, q


def table3(qdir: Path, warn: list[str]) -> str | None:
    p = read_csv(qdir / "table3_propagation.csv", warn)
    d = read_csv(qdir / "table3_deltas_pp.csv", warn, required=False)
    if p is None:
        return None
    p["config"] = p["config"].str.upper()
    estrato = {"triagem_certa": "Triagem correta", "triagem_errada": "Triagem errada"}
    headers = ["Configuração", "Estrato", "n", "Recall@5 (%)", "MRR", "Fidelidade (%)", "Alucinação (%)", "Recusa indevida (%)"]
    rows = [[r["config"], estrato.get(r["estrato"], r["estrato"]), br(r["n"], 0), br(r["recall5_pct"]), br(r["mrr"], 3),
             br(r["fidelidade_pct"]), br(r["alucinacao_pct"]), br(r["recusa_indevida_pct"])] for _, r in p.iterrows()]
    md = ("**Tabela 3 – Propagação do erro de triagem: métricas por estrato (triagem correta × errada)**\n\n"
          + md_table(headers, rows, ["l", "l"] + ["r"] * 6))
    if d is not None and len(d):
        h2 = ["Estrato", "Métrica", "C2 − C1 (p.p.)", "C3 − C2 (p.p.)"]
        r2 = [[estrato.get(r["estrato"], r["estrato"]), r["metrica"],
               br(r["c2_menos_c1_pp"], 1), br(r["c3_menos_c2_pp"], 1)] for _, r in d.iterrows()]
        md += "\n\n**Tabela 3 (continuação) – Diferença entre configurações, em pontos percentuais**\n\n" + md_table(h2, r2, ["l", "l", "r", "r"])
    md += (f"\n\n{SOURCE}\n\nNota: C1 não usa triagem; o estrato de C1 refere-se à triagem que C2 faria para o mesmo chamado. "
           "C2 − C1 mede o efeito do filtro por categoria; C3 − C2, o efeito do limiar de confiança.")
    return md


# benchmark: carga
def load_k6(stats_dir: Path, warn: list[str]) -> dict[str, dict]:
    found: dict[str, list[tuple[str, Path, dict]]] = {}
    for p in sorted(stats_dir.glob("*-k6-*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8-sig"))
        except (ValueError, OSError) as e:
            warn.append(f"K6: não consegui ler {p.name}: {e}")
            continue
        if not str(d.get("schema", "")).startswith("tcc-k6-summary"):
            continue
        m = re.search(r"-k6-(\d{8}-\d{6})\.json$", p.name)
        found.setdefault(d["label"], []).append((m.group(1) if m else "", p, d))
    out = {}
    for label, items in found.items():
        items.sort(key=lambda t: t[0])
        if len(items) > 1:
            warn.append(f"K6: {len(items)} resumos para '{label}'; usando o mais recente ({items[-1][1].name}). "
                        "Se as rodadas anteriores eram descartáveis, mova-as para outra pasta.")
        out[label] = {**items[-1][2], "_file": items[-1][1].name}
    return out


def docker_summary(stats_dir: Path, label: str, k6: dict, containers: dict[str, str], warn: list[str]):
    """CPU e RAM (média e pico) por contêiner dentro da janela de medição do k6."""
    pat = re.compile(rf"^{re.escape(label)}-\d{{8}}-\d{{6}}\.csv$")
    files = sorted(p for p in stats_dir.glob(f"{label}-*.csv") if pat.match(p.name))
    if not files:
        warn.append(f"DOCKER STATS: nenhum CSV para '{label}' em {stats_dir} (CPU/RAM ficam '—').")
        return {}
    if len(files) > 1:
        warn.append(f"DOCKER STATS: {len(files)} CSVs para '{label}'; usando {files[-1].name}.")
    df = pd.read_csv(files[-1], encoding="utf-8-sig")
    try:
        df["ts"] = pd.to_datetime(df["timestamp_utc"], utc=True, format="ISO8601")
    except (ValueError, TypeError):  # pandas < 2.0
        df["ts"] = pd.to_datetime(df["timestamp_utc"], utc=True)
    t0, t1 = k6.get("measure_start_utc"), k6.get("measure_end_utc")
    if t0 and t1:
        df = df[(df["ts"] >= pd.Timestamp(t0)) & (df["ts"] <= pd.Timestamp(t1))]
    else:
        warn.append(f"DOCKER STATS: '{label}' sem janela do k6; usando o CSV inteiro (inclui aquecimento).")
    res = {}
    for role, name in containers.items():
        g = df[df["container"] == name]
        if g.empty:
            warn.append(f"DOCKER STATS: sem amostras de '{name}' na janela de '{label}'.")
            continue
        res[role] = {"cpu_avg": g["cpu_pct"].mean(), "cpu_peak": g["cpu_pct"].max(),
                     "mem_avg": g["mem_mib"].mean(), "mem_peak": g["mem_mib"].max(), "n": len(g)}
        win = k6.get("window_s") or 0
        if win and len(g) < 0.7 * win:
            warn.append(f"DOCKER STATS: '{label}'/{name} tem {len(g)} amostras para uma janela de {win:.0f} s (~1/s esperado).")
    return res


def build_benchmark(args, warn: list[str]):
    stats_dir = Path(args.stats_dir)
    k6 = load_k6(stats_dir, warn)
    if not k6:
        warn.append(f"BENCHMARK: nenhum resumo do k6 (*-k6-*.json) em {stats_dir}. Tabela 4 e Gráficos 2-4 serão omitidos.")
        return None
    req_path = Path(args.requests)
    if not req_path.exists():
        warn.append(f"BENCHMARK: {req_path} não existe; etapas e custo ficam '—'.")
        req = pd.DataFrame(columns=["run_id"])
    else:
        req = pd.read_csv(req_path, encoding="utf-8-sig", low_memory=False)
        for c in ["http_status", "total_ms", "triage_ms", "search_ms", "generation_ms", "triage_in_tokens",
                  "triage_out_tokens", "gen_in_tokens", "gen_out_tokens"]:
            req[c] = pd.to_numeric(req[c], errors="coerce")
        req["escalate_bool"] = to_bool(req["escalate_to_human"])

    have_price = args.price_in is not None and args.price_out is not None
    rows = {}
    for label, k in k6.items():
        cfg, vus = k["config"], int(k["vus"])
        if args.levels and vus not in args.levels:
            continue
        if cfg not in LOAD_CONFIGS:
            continue
        r = req[req["run_id"] == label]
        r_ok = r[r["http_status"] == 200]
        if len(r) != k["measured_requests"]:
            warn.append(f"CONSISTÊNCIA: '{label}' tem {k['measured_requests']} requisições medidas no k6, mas {len(r)} linhas "
                        f"com run_id='{label}' em requests.csv. Se houve mais de uma rodada com o mesmo rótulo, "
                        "mova/renomeie o requests.csv entre experimentos (o app anexa ao arquivo existente).")
        if (k.get("abstained_rate") or 0) >= 0.95:
            warn.append(f"BENCHMARK: '{label}' teve {br((k['abstained_rate'] or 0) * 100)}% de abstenções (praticamente todas). "
                        "Provável índice vazio/desatualizado (python scripts/verify_index.py): latência de geração e custo ficam subestimados.")
        if k.get("warmup_failed"):
            warn.append(f"BENCHMARK: '{label}' teve {k['warmup_failed']} falha(s) nas requisições de aquecimento (descartadas).")
        if k["http_429"] or k["http_other"]:
            warn.append(f"INFO: '{label}' teve {k['http_429']} resposta(s) HTTP 429 e {k['http_other']} outra(s) falha(s); "
                        "são resultado a reportar (o protocolo não repete requisições).")
        stage = {s: r_ok[f"{s}_ms"].mean() for s in ["triage", "search", "generation"]}
        stage["total_server"] = r_ok["total_ms"].mean()
        cost = None
        if have_price and len(r_ok):
            t_in = r_ok["triage_in_tokens"].fillna(0) + r_ok["gen_in_tokens"].fillna(0)
            t_out = r_ok["triage_out_tokens"].fillna(0) + r_ok["gen_out_tokens"].fillna(0)
            per_call = (t_in * args.price_in + t_out * args.price_out) / 1e6
            cost = {"mean": per_call.mean(), "n": len(per_call), "sum": per_call.sum()}
        rows[(cfg, vus)] = {
            "label": label, "k6": k, "stage": stage, "cost": cost,
            "esc_rate": r_ok["escalate_bool"].mean() * 100 if len(r_ok) else float("nan"),
            "docker": docker_summary(stats_dir, label, k,
                                     {"app": args.app_container, "db": args.db_container}, warn),
        }
    if not rows:
        warn.append("BENCHMARK: nenhum nível restou após o filtro de configurações/níveis.")
        return None
    levels = sorted({v for _, v in rows})
    expected = args.levels or [1, 5, 10]
    for cfg in LOAD_CONFIGS:
        for v in expected:
            if (cfg, v) not in rows:
                warn.append(f"BENCHMARK: falta a rodada {cfg} com {v} VU(s) (label esperado '{cfg.lower()}-vu{v}').")
    return {"rows": rows, "levels": levels, "configs": [c for c in LOAD_CONFIGS if any(k[0] == c for k in rows)]}


def table4(bm, args) -> str:
    rows, levels, cfgs = bm["rows"], bm["levels"], bm["configs"]
    keys = [(c, v) for c in cfgs for v in levels if (c, v) in rows]

    a_rows, b_rows, c_rows = [], [], []
    for c, v in keys:
        e = rows[(c, v)]
        L = e["k6"]["latency_ok_ms"]
        a_rows.append([c, v, br(e["k6"]["measured_requests"], 0), br(e["k6"]["http_429"], 0), br(L["mean"], 1), br(L["median"], 1),
                       br(L["p95"], 1), br(L["stddev"], 1), br(e["k6"]["throughput_ok_rps"], 3)])
        s = e["stage"]
        b_rows.append([c, v, br(s["triage"], 1), br(s["search"], 1), br(s["generation"], 1), br(s["total_server"], 1)])
        d = e["docker"]

        def pair(role, a, b, dec):
            return f"{br(d[role][a], dec)} / {br(d[role][b], dec)}" if role in d else "—"

        cost = br(e["cost"]["mean"], 6) if e["cost"] else "—"
        c_rows.append([c, v, pair("app", "cpu_avg", "cpu_peak", 1), pair("app", "mem_avg", "mem_peak", 0),
                       pair("db", "cpu_avg", "cpu_peak", 1), pair("db", "mem_avg", "mem_peak", 0), cost,
                       br(e["esc_rate"], 1)])

    ha = ["Configuração", "VUs", "Req. medidas", "HTTP 429", "Média (ms)", "Mediana (ms)", "P95 (ms)", "DP (ms)", "Vazão (req/s)"]
    hb = ["Configuração", "VUs", "Triagem (ms)", "Busca (ms)", "Geração (ms)", "Total no servidor (ms)"]
    hc = ["Configuração", "VUs", "CPU app, méd./pico (%)", "RAM app, méd./pico (MiB)", "CPU Qdrant, méd./pico (%)",
          "RAM Qdrant, méd./pico (MiB)", "Custo por chamado (US$)", "Escalonamento humano (%)"]
    idx = (f"Tamanho do índice vetorial (coleção kb_suporte): {br(args.index_size_mb, 1)} MB."
           if args.index_size_mb is not None else
           "Tamanho do índice vetorial: não informado (use --index-size-mb; ver `curl.exe http://localhost:6333/collections/kb_suporte`).")
    price = (f"Custo = (tokens de entrada × US$ {br(args.price_in, 4)} + tokens de saída × US$ {br(args.price_out, 4)}) ÷ 1.000.000, "
             f"por chamado HTTP 200, em média; preços por 1 milhão de tokens consultados em {args.price_date or 'data não informada'}. "
             "Tokens de embedding da consulta e do juiz LLM não entram."
             if args.price_in is not None and args.price_out is not None else
             "Custo não calculado: informe --price-in, --price-out e --price-date.")
    return (
        "**Tabela 4 – Desempenho sob carga, consumo de recursos e custo por chamado (1, 5 e 10 usuários virtuais)**\n\n"
        "*Painel A – Latência total (cliente, k6; respostas HTTP 200) e vazão*\n\n" + md_table(ha, a_rows)
        + "\n\n*Painel B – Latência média por etapa (log do serviço; respostas HTTP 200)*\n\n" + md_table(hb, b_rows)
        + "\n\n*Painel C – Recursos dos contêineres (docker stats, 1 amostra/s), custo e escalonamento*\n\n" + md_table(hc, c_rows)
        + f"\n\n{SOURCE}\n\n"
        "Nota: medição de 2 minutos por nível após 10 requisições de aquecimento descartadas; 20 chamados fixos em rodízio, sem cache. "
        "DP = desvio-padrão amostral. Vazão = respostas HTTP 200 ÷ janela de medição. CPU em % de um núcleo (teto de 200% no app e de 100% no Qdrant). "
        "A RAM corresponde apenas à camada de orquestração, pois o LLM é remoto. " + price + " " + idx)


# gráficos
def style():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans"],
        "font.size": 9, "axes.labelsize": 9, "axes.titlesize": 9, "xtick.labelsize": 9, "ytick.labelsize": 9,
        "legend.fontsize": 8.5, "text.color": INK, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
        "axes.edgecolor": AXIS, "axes.linewidth": 0.8, "axes.facecolor": "white", "figure.facecolor": "white",
        "axes.axisbelow": True, "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.7,
        "grid.linestyle": "-", "legend.frameon": False, "savefig.facecolor": "white",
    })


def clean(ax):
    if sns is not None:
        sns.despine(ax=ax, left=True)
    else:
        for s in ["top", "right", "left"]:
            ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", length=3, color=AXIS)


def fmt_axis(d):
    return FuncFormatter(lambda v, _: br(v, d))


def bar_labels(ax, bars, vals, d, pad=0.015):
    top = ax.get_ylim()[1]
    for b, v in zip(bars, vals):
        if v is None or pd.isna(v):
            continue
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + pad * top, br(v, d), ha="center", va="bottom",
                fontsize=8.5, color=INK)


def chart1(q2: pd.DataFrame, path: Path, dpi: int):
    q = q2.copy()
    cfgs = list(q["config"])
    has_fid = q[["fidelidade_pct", "alucinacao_pct"]].notna().any().any()
    n = 3 if has_fid else 2
    fig, axes = plt.subplots(1, n, figsize=(6.3, 3.0), gridspec_kw={"wspace": 0.45})
    x = np.arange(len(cfgs))
    cols = [CFG_COLOR[c] for c in cfgs]

    def panel(ax, col, title, d, ymax):
        vals = q[col].tolist()
        ax.set_ylim(0, ymax)
        bars = ax.bar(x, [0 if pd.isna(v) else v for v in vals], width=0.55, color=cols, edgecolor="white", linewidth=1.2)
        bar_labels(ax, bars, vals, d)
        ax.set_xticks(x, cfgs)
        ax.set_title(title, loc="left", color=INK, fontsize=9, pad=8)
        ax.yaxis.set_major_formatter(fmt_axis(0 if ymax > 5 else 1))
        clean(ax)

    panel(axes[0], "recall5_pct", "(a) Recall@5 (%)", 1, 112)
    panel(axes[1], "mrr", "(b) MRR", 2, 1.12)
    if has_fid:
        ax = axes[2]
        sub = q[q["config"].isin(LOAD_CONFIGS)]
        xs = np.arange(len(sub))
        w = 0.36
        ax.set_ylim(0, 112)
        b1 = ax.bar(xs - w / 2, sub["fidelidade_pct"].fillna(0), w, color=[CFG_COLOR[c] for c in sub["config"]],
                    edgecolor="white", linewidth=1.2)
        b2 = ax.bar(xs + w / 2, sub["alucinacao_pct"].fillna(0), w, color="white",
                    edgecolor=[CFG_COLOR[c] for c in sub["config"]], hatch="////", linewidth=1.2)
        bar_labels(ax, b1, sub["fidelidade_pct"], 0)
        bar_labels(ax, b2, sub["alucinacao_pct"], 0)
        ax.set_xticks(xs, sub["config"])
        ax.set_title("(c) Fidelidade e alucinação (%)", loc="left", color=INK, fontsize=9, pad=8)
        ax.yaxis.set_major_formatter(fmt_axis(0))
        ax.legend(handles=[Patch(facecolor=INK2, edgecolor="white", label="Fidelidade"),
                           Patch(facecolor="white", edgecolor=INK2, hatch="////", label="Alucinação")],
                  loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, fontsize=8, handlelength=1.4, columnspacing=1.0)
        clean(ax)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def _level_axis(ax, levels):
    ax.set_xticks(range(len(levels)), [str(v) for v in levels])
    ax.set_xlabel("Usuários virtuais (VUs)")


def chart2(bm, path: Path, dpi: int):
    rows, levels, cfgs = bm["rows"], bm["levels"], bm["configs"]
    fig, (a, b) = plt.subplots(1, 2, figsize=(6.3, 3.4), gridspec_kw={"wspace": 0.34, "width_ratios": [1, 1.4]})
    xs = np.arange(len(levels))
    top = 0
    for c in cfgs:
        med = [rows.get((c, v), {}).get("k6", {}).get("latency_ok_ms", {}).get("median") for v in levels]
        p95 = [rows.get((c, v), {}).get("k6", {}).get("latency_ok_ms", {}).get("p95") for v in levels]
        med = [np.nan if m is None else m for m in med]
        p95 = [np.nan if m is None else m for m in p95]
        top = max(top, np.nanmax(p95) if not np.all(np.isnan(p95)) else 0)
        a.plot(xs, med, color=CFG_COLOR[c], marker=CFG_MARKER[c], lw=2, ms=6.5, mec="white", mew=1.2)
        a.plot(xs, p95, color=CFG_COLOR[c], marker=CFG_MARKER[c], lw=1.4, ms=6.5, mfc="white", mec=CFG_COLOR[c],
               mew=1.4, ls=(0, (4, 2)))
    a.set_ylim(0, top * 1.45 if top else 1)
    a.yaxis.set_major_formatter(fmt_axis(0))
    a.set_ylabel("Latência total (ms)")
    a.set_title("(a) Mediana e p95", loc="left", color=INK, pad=8)
    _level_axis(a, levels)
    h = [Line2D([], [], color=CFG_COLOR[c], marker=CFG_MARKER[c], lw=2, ms=6, mec="white", label=c) for c in cfgs]
    h += [Line2D([], [], color=INK2, lw=2, label="Mediana"), Line2D([], [], color=INK2, lw=1.4, ls=(0, (4, 2)), label="P95")]
    a.legend(handles=h, loc="upper left", ncol=2, fontsize=8, columnspacing=1.0, handlelength=2.0)
    clean(a)

    # (b) média por etapa, empilhada; agrupada por nível, uma barra por configuração
    width, gap = 0.78, 1.0
    pos, ticks, tops = {}, [], 0
    for i, v in enumerate(levels):
        for j, c in enumerate(cfgs):
            pos[(c, v)] = i * (len(cfgs) + gap) + j
    for (c, v), xp in pos.items():
        if (c, v) not in rows:
            continue
        s = rows[(c, v)]["stage"]
        bottom = 0
        for st in ["triage", "search", "generation"]:
            val = 0 if pd.isna(s[st]) else s[st]
            b.bar(xp, val, width, bottom=bottom, color=STAGE_COLOR[st], edgecolor="white", linewidth=1.2)
            bottom += val
        tops = max(tops, bottom)
        b.text(xp, bottom * 1.015, br(bottom, 0, thousands=False), ha="center", va="bottom", fontsize=7, color=INK)
    b.set_ylim(0, tops * 1.45 if tops else 1)
    b.set_xticks([pos[k] for k in pos], [k[0] for k in pos], fontsize=8)
    for i, v in enumerate(levels):
        center = i * (len(cfgs) + gap) + (len(cfgs) - 1) / 2
        b.text(center, -0.13, f"{v} VU{'s' if v > 1 else ''}", transform=b.get_xaxis_transform(), ha="center", va="top",
               fontsize=9, color=INK2)
    b.yaxis.set_major_formatter(fmt_axis(0))
    b.set_ylabel("Latência média no servidor (ms)")
    b.set_title("(b) Média por etapa", loc="left", color=INK, pad=8)
    b.legend(handles=[Patch(facecolor=STAGE_COLOR[s], edgecolor="white", label=STAGE_LABEL[s]) for s in STAGE_COLOR],
             loc="upper left", ncol=3, fontsize=8, handlelength=1.2, columnspacing=0.9)
    clean(b)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def chart3(bm, path: Path, dpi: int):
    rows, levels, cfgs = bm["rows"], bm["levels"], bm["configs"]
    fig, ax = plt.subplots(figsize=(6.3, 3.2))
    xs = np.arange(len(levels))
    top, has429 = 0, False
    for c in cfgs:
        y = [rows[(c, v)]["k6"]["throughput_ok_rps"] if (c, v) in rows else np.nan for v in levels]
        top = max(top, np.nanmax(y) if not np.all(np.isnan(y)) else 0)
        ax.plot(xs, y, color=CFG_COLOR[c], marker=CFG_MARKER[c], lw=2, ms=7, mec="white", mew=1.2, label=c)
    for i, v in enumerate(levels):
        ys = [rows[(c, v)]["k6"]["throughput_ok_rps"] for c in cfgs if (c, v) in rows and rows[(c, v)]["k6"]["http_429"]]
        if ys:
            has429 = True
            ax.annotate("†", (xs[i], max(y for c in cfgs for y in [rows.get((c, v), {}).get("k6", {}).get("throughput_ok_rps", 0)])),
                        textcoords="offset points", xytext=(0, 7), ha="center", fontsize=11, color=INK)
    ax.set_ylim(0, top * 1.3 if top else 1)
    ax.set_xlim(-0.35, len(levels) - 0.65)
    ax.yaxis.set_major_formatter(fmt_axis(1))
    ax.set_ylabel("Vazão (respostas HTTP 200 por segundo)")
    _level_axis(ax, levels)
    ax.legend(loc="upper left", ncol=len(cfgs))
    clean(ax)
    if has429:
        fig.text(0.01, -0.02, "† nível com respostas HTTP 429 (quantidades na Tabela 4, painel A); a vazão conta só respostas HTTP 200.",
                 fontsize=8, color=INK2, ha="left", va="top")
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def projection(bm, args):
    """Custo médio por chamado por configuração (todas as rodadas HTTP 200) e projeção mensal."""
    out = {}
    for c in bm["configs"]:
        costs = [(e["cost"]["sum"], e["cost"]["n"]) for (cc, _), e in bm["rows"].items() if cc == c and e["cost"]]
        if not costs:
            continue
        esc = [e["esc_rate"] for (cc, _), e in bm["rows"].items() if cc == c and not pd.isna(e["esc_rate"])]
        out[c] = {"cpc": sum(s for s, _ in costs) / sum(n for _, n in costs), "esc": float(np.mean(esc)) if esc else 0.0}
    return out


def chart4(proj, args, path: Path, dpi: int):
    vols = args.volumes
    cfgs = list(proj)
    fig, axes = plt.subplots(1, len(vols), figsize=(6.3, 3.3), gridspec_kw={"wspace": 0.55})
    axes = np.atleast_1d(axes)
    human = args.human_cost_usd
    for ax, vol in zip(axes, vols):
        api = np.array([proj[c]["cpc"] * vol for c in cfgs])
        hum = np.array([(human * vol * proj[c]["esc"] / 100) if human else 0.0 for c in cfgs])
        xs = np.arange(len(cfgs))
        err = np.vstack([api * args.sens, api * args.sens])
        ax.bar(xs, api, 0.55, color=[CFG_COLOR[c] for c in cfgs], edgecolor="white", linewidth=1.2)
        if human:
            ax.bar(xs, hum, 0.55, bottom=api, color="white", edgecolor=[CFG_COLOR[c] for c in cfgs], hatch="////", linewidth=1.2)
        ax.errorbar(xs, api, yerr=err, fmt="none", ecolor=INK2, elinewidth=1.0, capsize=3, capthick=1.0)
        top = max((api * (1 + args.sens) + hum).max(), 1e-12)
        ax.set_ylim(0, top * 1.3)
        for x, a, h, c in zip(xs, api, hum, cfgs):
            ax.text(x, a * (1 + args.sens) + h + top * 0.03, br(a + h, 2), ha="center", va="bottom", fontsize=8, color=INK)
        labels = [f"{c}\nesc. {br(proj[c]['esc'], 0)}%" if proj[c]["esc"] > 0 else c for c in cfgs]
        ax.set_xticks(xs, labels, fontsize=8)
        ax.set_title(f"{br(vol, 0)} chamados/mês", loc="left", color=INK, fontsize=9, pad=8)
        ax.yaxis.set_major_formatter(fmt_axis(0 if top > 20 else 2))
        clean(ax)
    axes[0].set_ylabel("Custo mensal projetado (US$)")
    if human:
        fig.legend(handles=[Patch(facecolor=INK2, edgecolor="white", label="API (LLM)"),
                            Patch(facecolor="white", edgecolor=INK2, hatch="////", label="Escalonamento humano")],
                   loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.06), fontsize=8)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


# principal
def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):  # console cp1252 do Windows
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description="Gera Tabelas 1-4 (Markdown) e Gráficos 1-4 (PNG) do artigo.")
    ap.add_argument("--quality-dir", default=str(root / "results" / "eval-100"))
    ap.add_argument("--requests", default=str(root / "output" / "metrics" / "requests.csv"))
    ap.add_argument("--stats-dir", default=str(root / "output" / "stats"), help="docker stats (*.csv) e resumos do k6 (*-k6-*.json)")
    ap.add_argument("--out", default=str(root / "results" / "article"))
    ap.add_argument("--levels", type=int, nargs="*", default=[1, 5, 10], help="níveis de VUs esperados (padrão: 1 5 10)")
    ap.add_argument("--app-container", default="tcc-app")
    ap.add_argument("--db-container", default="tcc-qdrant")
    ap.add_argument("--price-in", type=float, help="US$ por 1 milhão de tokens de ENTRADA (página oficial do provedor)")
    ap.add_argument("--price-out", type=float, help="US$ por 1 milhão de tokens de SAÍDA (página oficial do provedor)")
    ap.add_argument("--price-date", help="data da consulta dos preços (AAAA-MM-DD); entra na nota da Tabela 4")
    ap.add_argument("--index-size-mb", type=float, help="tamanho do índice vetorial em MB (Qdrant)")
    ap.add_argument("--volumes", type=int, nargs=3, default=[1000, 10000, 100000], metavar=("BAIXO", "MEDIO", "ALTO"),
                    help="chamados/mês das 3 faixas HIPOTÉTICAS (padrão 1000 10000 100000: declare/ajuste no artigo)")
    ap.add_argument("--sens", type=float, default=0.25, help="variação (±) do custo por chamado na sensibilidade (padrão 0,25)")
    ap.add_argument("--human-cost-usd", type=float, help="custo hipotético (US$) de um chamado escalonado a humano; opcional")
    ap.add_argument("--dpi", type=int, default=300)
    args = ap.parse_args(argv)
    args.levels = sorted(set(args.levels)) if args.levels else None

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    warn: list[str] = []
    style()
    qdir = Path(args.quality_dir)
    md_parts, made, skipped = [], [], []

    # Tabelas 1-3 e Gráfico 1
    t1 = table1(qdir, warn)
    t2, q2 = table2(qdir, warn)
    t3 = table3(qdir, warn)
    for name, t in [("Tabela 1", t1), ("Tabela 2", t2), ("Tabela 3", t3)]:
        if t:
            md_parts.append(t)
            made.append(name)
        else:
            skipped.append(name)
    chart_caps = []
    if q2 is not None:
        chart1(q2, out / "grafico1_qualidade.png", args.dpi)
        made.append("Gráfico 1")
        chart_caps.append(("GRÁFICO 1 – Recall@5, MRR e, quando julgadas, fidelidade e alucinação por configuração", "grafico1_qualidade.png"))
    else:
        skipped.append("Gráfico 1")

    # Benchmark: Tabela 4 e Gráficos 2-4
    bm = build_benchmark(args, warn)
    if bm:
        md_parts.append(table4(bm, args))
        made.append("Tabela 4")
        chart2(bm, out / "grafico2_latencia.png", args.dpi)
        chart3(bm, out / "grafico3_vazao.png", args.dpi)
        made += ["Gráfico 2", "Gráfico 3"]
        chart_caps += [("GRÁFICO 2 – Latência total (mediana e p95, k6) e latência média por etapa (log do serviço) por nível de concorrência", "grafico2_latencia.png"),
                       ("GRÁFICO 3 – Vazão (respostas HTTP 200 por segundo) por nível de concorrência", "grafico3_vazao.png")]
        proj = projection(bm, args) if (args.price_in is not None and args.price_out is not None) else {}
        if proj:
            warn.append("PROJEÇÃO: volumes mensais de " + ", ".join(br(v, 0) for v in args.volumes) +
                        " chamados são HIPOTÉTICOS" + (" (padrão do script)" if args.volumes == [1000, 10000, 100000] else "") +
                        f"; sensibilidade de ±{br(args.sens * 100, 0)}% no custo por chamado. Declare ambos no artigo.")
            chart4(proj, args, out / "grafico4_projecao_custo.png", args.dpi)
            made.append("Gráfico 4")
            human = f" e custo hipotético de US$ {br(args.human_cost_usd, 2)} por chamado escalonado" if args.human_cost_usd else ""
            chart_caps.append((f"GRÁFICO 4 – Custo mensal projetado da API (US$) para 3 faixas hipotéticas de volume, com variação de ±{br(args.sens * 100, 0)}%{human}; "
                               "esc. = taxa de escalonamento humano medida no benchmark", "grafico4_projecao_custo.png"))
        else:
            skipped.append("Gráfico 4 (informe --price-in, --price-out e --price-date)")
    else:
        skipped += ["Tabela 4", "Gráfico 2", "Gráfico 3", "Gráfico 4"]

    # Markdown
    parts = ["<!-- Gerado por scripts/generate_article_assets.py em "
             f"{dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}. Não edite à mão: rode o script de novo. -->"]
    parts += md_parts
    if chart_caps:
        parts.append("**Legendas dos gráficos** (título acima da figura; fonte abaixo, conforme o Guia, seção 2.3)\n\n"
                     + "\n\n".join(f"{cap}  \n*Arquivo: {f}*  \n{SOURCE}" for cap, f in chart_caps))
    (out / "tabelas.md").write_text("\n\n".join(parts) + "\n", encoding="utf-8")

    # Checagens
    lines = ["CHECAGENS (leia antes de usar os números no artigo)", "=" * 60, ""]
    lines += [f"- {w}" for w in warn] or ["- Nenhum aviso."]
    lines += ["", f"Gerados : {', '.join(made) or '-'}", f"Omitidos: {', '.join(skipped) or '-'}"]
    (out / "checagens.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Saída em: {out}")
    print(f"Gerados : {', '.join(made) or '-'}")
    if skipped:
        print(f"Omitidos: {', '.join(skipped)}")
    if warn:
        print(f"\n{len(warn)} aviso(s) (também em checagens.txt):")
        for w in warn:
            print(f"  - {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
