# Triagem e RAG no suporte técnico

Código, dados e resultados do artigo *Triage and Retrieval-Augmented Generation Integrated into Technical Support: An Experimental Evaluation of Architectures Regarding Performance, Faithfulness, and Cost*.

O experimento compara quatro configurações sobre 100 chamados simulados: C0 (palavras-chave + BM25), C1 (RAG sem filtro), C2 (triagem por LLM + busca filtrada pela categoria) e C3 (C2 com limiar de confiança de 0,70 e busca global abaixo dele). O microsserviço usa Spring Boot 3.5, Spring AI 1.0.3, Qdrant 1.14.1 e gpt-4o-mini.

## Estrutura

```
app/            microsserviço (rotas /api/c1|c2|c3/ask, /admin/ingest e /admin/info)
data/           base de conhecimento (kb/), chamados e manifestos
k6/             teste de carga
scripts/        geração dos dados, avaliação de qualidade, benchmark, tabelas e gráficos
output/         log por requisição (metrics/requests.csv) e docker stats + resumos do k6 (stats/)
results/        respostas e vereditos do juiz em cache, conferência manual e metadados da rodada
```

`data/` é gerado por `scripts/populate_kb.py` e `scripts/build_tickets.py` a partir de `scripts/nimbus_content.py`. A conferência manual da amostra do juiz está em `results/eval-100/judge_sample_20pct.csv`.

## Recalcular tabelas e gráficos (sem API)

Python 3.9+ e `pip install -r requirements.txt`.

```bash
python scripts/populate_kb.py --clean
python scripts/build_tickets.py

mkdir -p results/recomputed
cp results/eval-100/raw_c*.jsonl results/eval-100/judge_c*.jsonl results/recomputed/
OPENAI_API_KEY=cache python scripts/run_quality_eval.py --skip-api --granularity document --out results/recomputed
python scripts/run_quality_eval.py --agreement results/eval-100/judge_sample_20pct.csv

python scripts/generate_article_assets.py --quality-dir results/recomputed \
    --price-in 0.15 --price-out 0.60 --price-date 2026-10-19
```

As tabelas e os gráficos vão para `results/article/` (Tabelas 3 a 6 e Figuras 2 a 5 do artigo). A chave da API não é usada quando todos os julgamentos estão em cache. O recálculo é feito em `results/recomputed/` porque o script regrava `judge_sample_20pct.csv` na pasta de saída.

## Nova rodada (com API)

Requer Docker, k6, Python 3.9+ e uma chave da OpenAI com acesso ao `gpt-4o-mini-2024-07-18`. Os resultados não se repetem exatamente, pois o provedor não garante determinismo mesmo com `temperature = 0` e `seed = 42`.

```bash
cp .env.example .env        # preencher OPENAI_API_KEY e exportá-la também no terminal
docker compose up -d --build
curl -X POST "http://localhost:8080/admin/ingest?reset=true"
curl -X PUT http://localhost:6333/collections/kb_suporte/index \
     -H "Content-Type: application/json" -d '{"field_name":"category","field_schema":"keyword"}'
python scripts/verify_index.py
python scripts/run_quality_eval.py --granularity document
```

Benchmark (Windows/PowerShell): `.\scripts\rodar-benchmark.ps1`, que roda os nove níveis (C1 a C3 com 1, 5 e 10 VUs, 2 min cada) e gera as tabelas e os gráficos. Para um nível isolado: `k6 run --env CONFIG=c2 --env VUS=5 k6/ticket-load.js`.

## Observações

- `search_ms` inclui a chamada à API de embeddings, além da consulta ao Qdrant.
- O cabeçalho `X-Run-Id` separa as rodadas em `requests.csv` (`smoke`, `eval-100`, `c2-vu5`, `c2-vu5-warmup` etc.).
- O `.gitattributes` desativa a conversão de fim de linha para preservar os SHA-256 dos prompts e da base.
- Todos os dados são simulados; a plataforma Nimbus e as regras de seus manuais são fictícias.
