package br.tcc.suporte.metrics;

import br.tcc.suporte.domain.Category;
import org.springframework.ai.chat.metadata.Usage;
import org.springframework.stereotype.Component;
import org.springframework.web.context.annotation.RequestScope;

import java.time.Instant;
import java.util.Locale;
import java.util.UUID;
import java.util.function.Supplier;

/** Medições de uma requisição. Etapas não executadas ficam vazias no CSV, e não zero. */
@Component
@RequestScope
public class RequestMetrics {

    public enum Stage { TRIAGE, SEARCH, GENERATION }

    public static final String CSV_HEADER = String.join(",",
            "started_at_utc", "request_id", "run_id", "config", "ticket_id", "http_status",
            "total_ms", "triage_ms", "search_ms", "generation_ms",
            "triage_in_tokens", "triage_out_tokens", "gen_in_tokens", "gen_out_tokens", "total_tokens",
            "predicted_category", "triage_confidence", "filter_applied", "escalate_to_human",
            "abstained", "error");

    private final String requestId = UUID.randomUUID().toString();
    private final Instant startedAt = Instant.now();
    private final long startNanos = System.nanoTime();

    private String runId, config, ticketId, predictedCategory, error;
    private Long triageNanos, searchNanos, generationNanos;
    private Integer triageIn, triageOut, genIn, genOut;
    private Double confidence;
    private Boolean filterApplied, escalate, abstained;

    public String requestId() { return requestId; }

    public void setRunId(String runId) { this.runId = runId; }

    public void describe(String config, String ticketId) {
        this.config = config;
        this.ticketId = ticketId;
    }

    public void triageOutcome(Category category, double confidence) {
        this.predictedCategory = category == null ? "INVALID" : category.name();
        this.confidence = confidence;
    }

    public void outcome(boolean filterApplied, boolean escalate, boolean abstained) {
        this.filterApplied = filterApplied;
        this.escalate = escalate;
        this.abstained = abstained;
    }

    public void fail(String message) {
        if (this.error == null && message != null) {
            String oneLine = message.replaceAll("\\s+", " ").trim();
            this.error = oneLine.length() > 200 ? oneLine.substring(0, 200) : oneLine;
        }
    }

    /** Mede a duração da etapa, inclusive quando ela lança exceção. */
    public <T> T timed(Stage stage, Supplier<T> action) {
        long t0 = System.nanoTime();
        try {
            return action.get();
        } finally {
            long d = System.nanoTime() - t0;
            switch (stage) {
                case TRIAGE -> triageNanos = d;
                case SEARCH -> searchNanos = d;
                case GENERATION -> generationNanos = d;
            }
        }
    }

    public void recordUsage(Stage stage, Usage usage) {
        if (usage == null) return;
        Integer in = usage.getPromptTokens();
        Integer out = usage.getCompletionTokens();
        if (stage == Stage.TRIAGE) { triageIn = in; triageOut = out; }
        else if (stage == Stage.GENERATION) { genIn = in; genOut = out; }
    }

    public String toCsvRow(int httpStatus) {
        long totalNanos = System.nanoTime() - startNanos;
        int totalTokens = nz(triageIn) + nz(triageOut) + nz(genIn) + nz(genOut);
        return String.join(",",
                startedAt.toString(), requestId, csv(runId), csv(config), csv(ticketId),
                String.valueOf(httpStatus),
                ms(totalNanos), ms(triageNanos), ms(searchNanos), ms(generationNanos),
                str(triageIn), str(triageOut), str(genIn), str(genOut), String.valueOf(totalTokens),
                csv(predictedCategory),
                confidence == null ? "" : String.format(Locale.ROOT, "%.3f", confidence),
                str(filterApplied), str(escalate), str(abstained), csv(error));
    }

    private static int nz(Integer v) { return v == null ? 0 : v; }

    private static String str(Object v) { return v == null ? "" : v.toString(); }

    private static String ms(Long nanos) {
        return nanos == null ? "" : String.format(Locale.ROOT, "%.3f", nanos / 1_000_000.0);
    }

    private static String ms(long nanos) { return String.format(Locale.ROOT, "%.3f", nanos / 1_000_000.0); }

    private static String csv(String v) {
        if (v == null) return "";
        boolean quote = v.contains(",") || v.contains("\"") || v.contains("\n") || v.contains("\r");
        String e = v.replace("\"", "\"\"");
        return quote ? "\"" + e + "\"" : e;
    }
}
