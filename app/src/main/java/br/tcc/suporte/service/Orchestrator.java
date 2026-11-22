package br.tcc.suporte.service;

import br.tcc.suporte.api.AskRequest;
import br.tcc.suporte.api.AskResponse;
import br.tcc.suporte.api.AskResponse.Source;
import br.tcc.suporte.config.AppProperties;
import br.tcc.suporte.domain.Category;
import br.tcc.suporte.domain.TriageResult;
import br.tcc.suporte.metrics.RequestMetrics;
import br.tcc.suporte.service.GenerationService.GenerationResult;
import org.springframework.ai.document.Document;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * C1: busca no índice inteiro e geração.
 * C2: triagem, busca filtrada pela categoria prevista e geração.
 * C3: como C2, mas abaixo do limiar de confiança busca sem filtro e sinaliza para humano.
 * C0 fica em scripts/run_quality_eval.py.
 */
@Service
public class Orchestrator {

    private final TriageService triage;
    private final RetrievalService retrieval;
    private final GenerationService generation;
    private final RequestMetrics metrics;
    private final double threshold;

    public Orchestrator(TriageService triage, RetrievalService retrieval, GenerationService generation,
                        RequestMetrics metrics, AppProperties props) {
        this.triage = triage;
        this.retrieval = retrieval;
        this.generation = generation;
        this.metrics = metrics;
        this.threshold = props.triage().confidenceThreshold();
    }

    public AskResponse c1(AskRequest req) {
        metrics.describe("C1", req.ticketId());
        List<Document> docs = retrieval.search(req.question(), Optional.empty());
        return answer("C1", req, null, false, false, docs);
    }

    public AskResponse c2(AskRequest req) {
        metrics.describe("C2", req.ticketId());
        TriageResult t = triage.classify(req.question());
        Optional<Category> filter = Optional.ofNullable(t.category());   // triagem inválida: sem filtro
        List<Document> docs = retrieval.search(req.question(), filter);
        return answer("C2", req, t, filter.isPresent(), false, docs);
    }

    public AskResponse c3(AskRequest req) {
        metrics.describe("C3", req.ticketId());
        TriageResult t = triage.classify(req.question());
        boolean lowConfidence = t.category() == null || t.confidence() < threshold;
        Optional<Category> filter = lowConfidence ? Optional.empty() : Optional.of(t.category());
        List<Document> docs = retrieval.search(req.question(), filter);
        return answer("C3", req, t, filter.isPresent(), lowConfidence, docs);
    }

    private AskResponse answer(String config, AskRequest req, TriageResult t, boolean filterApplied,
                               boolean escalate, List<Document> docs) {
        GenerationResult g = generation.generate(req.question(), docs);
        metrics.outcome(filterApplied, escalate, g.abstained());

        List<Source> sources = new ArrayList<>();
        for (int i = 0; i < docs.size(); i++) {
            Document d = docs.get(i);
            Object chunk = d.getMetadata().get("chunk_index");
            sources.add(new Source(i + 1,
                    String.valueOf(d.getMetadata().get("source")),
                    String.valueOf(d.getMetadata().get("category")),
                    chunk instanceof Number n ? n.intValue() : null,
                    d.getScore()));
        }
        return new AskResponse(metrics.requestId(), config, req.ticketId(), g.answer(), g.abstained(),
                t == null || t.category() == null ? null : t.category().name(),
                t == null ? null : t.confidence(),
                filterApplied, escalate, sources);
    }
}
