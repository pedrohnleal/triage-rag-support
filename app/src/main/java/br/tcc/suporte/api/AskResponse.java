package br.tcc.suporte.api;

import java.util.List;

public record AskResponse(
        String requestId,
        String configuration,
        String ticketId,
        String answer,
        boolean abstained,
        String predictedCategory,
        Double triageConfidence,
        boolean filterApplied,
        boolean escalateToHuman,
        List<Source> sources) {

    /** Trechos recuperados, em ordem de ranking (base para Recall@5 e MRR). */
    public record Source(int rank, String source, String category, Integer chunkIndex, Double score) {}
}
