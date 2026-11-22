/**
 * Teste de carga de uma configuracao (C1, C2 ou C3) com os 20 chamados de data/tickets-k6-20.json,
 * em rodizio e sem pausa. As requisicoes de aquecimento usam X-Run-Id <LABEL>-warmup e ficam fora
 * das metricas. Grava o resumo em output/stats/<LABEL>-k6-<data>.json.
 *
 * Uso: k6 run --env CONFIG=c2 --env VUS=5 [--env DURATION=2m] k6/ticket-load.js
 * Outras variaveis: WARMUP_REQUESTS, LABEL, BASE_URL, SUMMARY_DIR, MAX_WARMUP_ABSTAIN.
 */
import http from 'k6/http';
import exec from 'k6/execution';
import { check } from 'k6';
import { SharedArray } from 'k6/data';
import { Counter, Gauge, Trend } from 'k6/metrics';

// configuracao
const CONFIG = String(__ENV.CONFIG || '').trim().toLowerCase();
if (!['c1', 'c2', 'c3'].includes(CONFIG)) {
  throw new Error(`Defina --env CONFIG=C1|C2|C3 (recebido: "${__ENV.CONFIG || ''}")`);
}
const VUS = parseInt(__ENV.VUS || '1', 10);
if (!(VUS >= 1)) throw new Error(`VUS invalido: "${__ENV.VUS}"`);
const DURATION = __ENV.DURATION || '2m';
const WARMUP = __ENV.WARMUP_REQUESTS === undefined ? 10 : parseInt(__ENV.WARMUP_REQUESTS, 10);
if (!(WARMUP >= 0)) throw new Error(`WARMUP_REQUESTS invalido: "${__ENV.WARMUP_REQUESTS}"`);
const LABEL = __ENV.LABEL || `${CONFIG}-vu${VUS}`;
const WARMUP_RUN_ID = `${LABEL}-warmup`;
if (WARMUP_RUN_ID.length > 64) throw new Error('LABEL longo demais: o app trunca X-Run-Id em 64 caracteres');
const MAX_WARMUP_ABSTAIN = __ENV.MAX_WARMUP_ABSTAIN === undefined ? 0.95 : parseFloat(__ENV.MAX_WARMUP_ABSTAIN);
if (!(MAX_WARMUP_ABSTAIN >= 0 && MAX_WARMUP_ABSTAIN <= 1)) throw new Error(`MAX_WARMUP_ABSTAIN invalido: "${__ENV.MAX_WARMUP_ABSTAIN}"`);
const BASE_URL = (__ENV.BASE_URL || 'http://localhost:8080').replace(/\/+$/, '');
const SUMMARY_DIR = (__ENV.SUMMARY_DIR || 'output/stats').replace(/[\\/]+$/, '');
const URL = `${BASE_URL}/api/${CONFIG}/ask`;

// open() so existe no contexto de inicializacao; o caminho e relativo a este script.
const tickets = new SharedArray('tickets', () => {
  const data = JSON.parse(open('../data/tickets-k6-20.json'));
  if (!Array.isArray(data) || data.length === 0) throw new Error('tickets-k6-20.json vazio ou invalido');
  data.forEach((t) => {
    if (!t.ticketId || !t.question) throw new Error(`Chamado sem ticketId/question: ${JSON.stringify(t)}`);
  });
  return data;
});

// metricas (apenas da medicao)
function latencyStats(name) {
  return {
    name,
    trend: new Trend(`${name}_ms`, true),
    n: new Counter(`${name}_n`),
    sum: new Counter(`${name}_sum`),
    sumsq: new Counter(`${name}_sumsq`),
  };
}
function addLatency(s, d) {
  s.trend.add(d);
  s.n.add(1);
  s.sum.add(d);
  s.sumsq.add(d * d);
}
const latOk = latencyStats('lat_ok');     // so HTTP 200
const latAll = latencyStats('lat_all');   // todas as respostas medidas
const cMeasured = new Counter('measured_requests');
const cOk = new Counter('measured_http_200');
const c429 = new Counter('measured_http_429');
const cOther = new Counter('measured_http_other'); // != 200 e != 429 (inclui status 0 = timeout/conexao)
const cAbstained = new Counter('measured_abstained'); // entre os 200: campo "abstained" = true
const gStart = new Gauge('measure_t0_ms');
const gEnd = new Gauge('measure_t1_ms');
const cWarmup = new Counter('warmup_requests_sent');
const cWarmupFail = new Counter('warmup_requests_failed');

export const options = {
  scenarios: {
    medicao: {
      executor: 'constant-vus',
      vus: VUS,
      duration: DURATION,
      gracefulStop: '70s', // deixa terminar as chamadas em voo (timeout da requisicao = 60 s)
    },
  },
  setupTimeout: '10m', // 10 chamadas sequenciais a um LLM podem passar do padrao de 60 s
  summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)', 'p(99)'],
};

// requisicao
function ask(ticket, runId, phase) {
  return http.post(
    URL,
    JSON.stringify({ ticketId: ticket.ticketId, question: ticket.question }),
    {
      headers: { 'Content-Type': 'application/json', 'X-Run-Id': runId },
      tags: { phase, name: `POST /api/${CONFIG}/ask` },
      timeout: '60s',
    },
  );
}

// aquecimento
export function setup() {
  let answered = 0;
  let abstained = 0;
  for (let i = 0; i < WARMUP; i++) {
    const t = tickets[i % tickets.length];
    const res = ask(t, WARMUP_RUN_ID, 'warmup');
    cWarmup.add(1);
    if (res.status !== 200) cWarmupFail.add(1);
    if (i === 0 && res.status === 0) {
      exec.test.abort(`Sem conexao com ${URL} (${res.error || 'erro desconhecido'}). O app esta no ar? docker compose up -d`);
    }
    if (res.status === 200) {
      answered += 1;
      try {
        if (res.json('abstained') === true) abstained += 1;
      } catch (e) { /* corpo nao-JSON: ignora */ }
    }
  }
  // abstencao em massa no aquecimento indica indice vazio ou desatualizado
  if (answered >= 5 && abstained / answered > MAX_WARMUP_ABSTAIN) {
    exec.test.abort(
      `${abstained} de ${answered} respostas de aquecimento foram abstencao (limite ${(MAX_WARMUP_ABSTAIN * 100).toFixed(0)}%). ` +
      'O indice do Qdrant provavelmente esta vazio ou desatualizado. Rode: python scripts/verify_index.py --reingest ' +
      '(ou MAX_WARMUP_ABSTAIN=1 para ignorar esta trava).');
  }
}

// medicao
export default function () {
  // iterationInTest e global entre os VUs, o que distribui os 20 chamados por igual
  const ticket = tickets[exec.scenario.iterationInTest % tickets.length];

  gStart.add(Date.now());
  const res = ask(ticket, LABEL, 'measure');
  gEnd.add(Date.now());

  const d = res.timings.duration;
  addLatency(latAll, d);
  cMeasured.add(1);

  if (res.status === 200) {
    cOk.add(1);
    addLatency(latOk, d);
    try {
      if (res.json('abstained') === true) cAbstained.add(1);
    } catch (e) { /* corpo nao-JSON: ignora */ }
  } else if (res.status === 429) {
    c429.add(1);
  } else {
    cOther.add(1);
  }
  check(res, { 'HTTP 200': (r) => r.status === 200 });
}

// resumo (desvio-padrao amostral agregado entre VUs, pois os Trends do k6 nao o expoem)
const num = (data, metric, key) => {
  const m = data.metrics[metric];
  return m && m.values && m.values[key] !== undefined ? m.values[key] : 0;
};
const round = (x, p = 3) => (x === null || x === undefined || Number.isNaN(x) ? null : Math.round(x * 10 ** p) / 10 ** p);

function latencySummary(data, s) {
  const tv = (data.metrics[`${s.name}_ms`] || {}).values || {};
  const n = num(data, `${s.name}_n`, 'count');
  const sum = num(data, `${s.name}_sum`, 'count');
  const sumsq = num(data, `${s.name}_sumsq`, 'count');
  let sd = null;
  if (n > 1) sd = Math.sqrt(Math.max(0, (sumsq - (sum * sum) / n) / (n - 1)));
  return {
    n,
    mean: n ? round(sum / n) : null, median: round(tv.med), p90: round(tv['p(90)']), p95: round(tv['p(95)']),
    p99: round(tv['p(99)']), stddev: round(sd), min: round(tv.min), max: round(tv.max),
  };
}

export function handleSummary(data) {
  const measured = num(data, 'measured_requests', 'count');
  const t0 = (data.metrics.measure_t0_ms || { values: {} }).values.min;
  const t1 = (data.metrics.measure_t1_ms || { values: {} }).values.max;
  const windowS = t0 && t1 ? (t1 - t0) / 1000 : null;
  const ok = num(data, 'measured_http_200', 'count');

  const out = {
    schema: 'tcc-k6-summary/1',
    label: LABEL,
    config: CONFIG.toUpperCase(),
    vus: VUS,
    duration: DURATION,
    base_url: BASE_URL,
    run_id: LABEL,
    warmup_run_id: WARMUP_RUN_ID,
    warmup_requests: num(data, 'warmup_requests_sent', 'count'),
    warmup_failed: num(data, 'warmup_requests_failed', 'count'),
    measure_start_utc: t0 ? new Date(t0).toISOString() : null,
    measure_end_utc: t1 ? new Date(t1).toISOString() : null,
    window_s: round(windowS),
    measured_requests: measured,
    http_200: ok,
    http_429: num(data, 'measured_http_429', 'count'),
    http_other: num(data, 'measured_http_other', 'count'),
    abstained_200: num(data, 'measured_abstained', 'count'),
    abstained_rate: ok > 0 ? round(num(data, 'measured_abstained', 'count') / ok, 4) : null,
    throughput_rps: windowS ? round(measured / windowS) : null,
    throughput_ok_rps: windowS ? round(ok / windowS) : null,
    latency_ok_ms: latencySummary(data, latOk),
    latency_all_ms: latencySummary(data, latAll),
  };

  const L = out.latency_ok_ms;
  const f = (x) => (x === null || x === undefined ? 'n/d' : x.toFixed(1));
  const text = [
    '',
    `=== ${LABEL} | ${out.config} | ${VUS} VU | ${DURATION} | aquecimento: ${out.warmup_requests} req descartadas ===`,
    `  requisicoes medidas : ${measured}  (HTTP 200: ${ok} | 429: ${out.http_429} | outros: ${out.http_other})`,
    `  vazao               : ${out.throughput_rps === null ? 'n/d' : out.throughput_rps.toFixed(3)} req/s  (janela ${windowS === null ? 'n/d' : windowS.toFixed(1)} s)`,
    `  latencia (HTTP 200) : media ${f(L.mean)} | mediana ${f(L.median)} | p95 ${f(L.p95)} | dp ${f(L.stddev)} ms`,
    `  abstencoes (de 200) : ${out.abstained_200}${out.abstained_rate === null ? '' : ` (${(out.abstained_rate * 100).toFixed(1)}%)`}  <- compare com a avaliacao de qualidade; ~100% = indice vazio`,
    out.abstained_rate !== null && out.abstained_rate >= 0.95
      ? '  !! ATENCAO: praticamente todas as respostas foram abstencao. Rode python scripts/verify_index.py e confira a indexacao da base antes de usar estes numeros.'
      : '',
    '',
  ].filter((l, i, a) => l !== '' || i === 0 || i === a.length - 1).join('\n');

  const d = new Date();
  const p2 = (n) => String(n).padStart(2, '0');
  const stamp = `${d.getUTCFullYear()}${p2(d.getUTCMonth() + 1)}${p2(d.getUTCDate())}-${p2(d.getUTCHours())}${p2(d.getUTCMinutes())}${p2(d.getUTCSeconds())}`;
  return {
    stdout: text,
    [`${SUMMARY_DIR}/${LABEL}-k6-${stamp}.json`]: JSON.stringify(out, null, 2),
  };
}
