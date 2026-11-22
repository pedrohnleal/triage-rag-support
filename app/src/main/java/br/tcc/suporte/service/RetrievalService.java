package br.tcc.suporte.service;

import br.tcc.suporte.config.AppProperties;
import br.tcc.suporte.domain.Category;
import br.tcc.suporte.metrics.RequestMetrics;
import br.tcc.suporte.metrics.RequestMetrics.Stage;
import org.springframework.ai.document.Document;
import org.springframework.ai.vectorstore.SearchRequest;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.ai.vectorstore.filter.FilterExpressionBuilder;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

/**
 * Busca top-k, com ou sem filtro por category. O tempo medido inclui a chamada à API de
 * embeddings que vetoriza a consulta.
 */
@Service
public class RetrievalService {

    private final VectorStore vectorStore;
    private final RequestMetrics metrics;
    private final int topK;

    public RetrievalService(VectorStore vectorStore, RequestMetrics metrics, AppProperties props) {
        this.vectorStore = vectorStore;
        this.metrics = metrics;
        this.topK = props.retrieval().topK();
    }

    public List<Document> search(String query, Optional<Category> categoryFilter) {
        SearchRequest.Builder request = SearchRequest.builder().query(query).topK(topK);
        categoryFilter.ifPresent(c ->
                request.filterExpression(new FilterExpressionBuilder().eq("category", c.name()).build()));
        SearchRequest built = request.build();
        return metrics.timed(Stage.SEARCH, () -> vectorStore.similaritySearch(built));
    }
}
