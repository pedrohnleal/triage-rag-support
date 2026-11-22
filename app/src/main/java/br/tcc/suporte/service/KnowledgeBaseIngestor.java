package br.tcc.suporte.service;

import br.tcc.suporte.config.AppProperties;
import br.tcc.suporte.domain.Category;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ai.document.Document;
import org.springframework.ai.transformer.splitter.TokenTextSplitter;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.ai.vectorstore.filter.FilterExpressionBuilder;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;
import java.util.stream.Stream;

/**
 * Indexa data/kb/<categoria>/ com os metadados category, source e chunk_index.
 * Os ids são derivados da fonte e da posição, então reindexar não duplica trechos.
 */
@Service
public class KnowledgeBaseIngestor {

    private static final Logger log = LoggerFactory.getLogger(KnowledgeBaseIngestor.class);

    private final VectorStore vectorStore;
    private final AppProperties props;

    public KnowledgeBaseIngestor(VectorStore vectorStore, AppProperties props) {
        this.vectorStore = vectorStore;
        this.props = props;
    }

    public Map<String, Object> ingest(boolean reset) throws IOException {
        Path root = Path.of(props.kb().path());
        int chunkSize = props.kb().chunkSize();
        TokenTextSplitter splitter = new TokenTextSplitter(chunkSize, 350, 5, 10_000, true);

        long t0 = System.nanoTime();
        int files = 0;
        Map<String, Integer> chunksPerCategory = new LinkedHashMap<>();

        for (Category category : Category.values()) {
            Path dir = root.resolve(category.folderName());
            if (!Files.isDirectory(dir)) {
                log.warn("Pasta da base de conhecimento não encontrada: {}", dir);
                chunksPerCategory.put(category.name(), 0);
                continue;
            }
            if (reset) {
                vectorStore.delete(new FilterExpressionBuilder().eq("category", category.name()).build());
            }

            List<Path> paths;
            try (Stream<Path> s = Files.list(dir)) {
                paths = s.filter(p -> {
                    String n = p.getFileName().toString().toLowerCase(Locale.ROOT);
                    return n.endsWith(".md") || n.endsWith(".txt");
                }).sorted().toList();
            }

            List<Document> batch = new ArrayList<>();
            for (Path p : paths) {
                String source = category.folderName() + "/" + p.getFileName();
                Document whole = new Document(Files.readString(p, StandardCharsets.UTF_8),
                        Map.of("category", category.name(), "source", source));
                List<Document> parts = splitter.split(List.of(whole));
                for (int i = 0; i < parts.size(); i++) {
                    Map<String, Object> meta = new HashMap<>();
                    meta.put("category", category.name());
                    meta.put("source", source);
                    meta.put("chunk_index", i);
                    String id = UUID.nameUUIDFromBytes((source + "#" + i).getBytes(StandardCharsets.UTF_8)).toString();
                    batch.add(Document.builder().id(id).text(parts.get(i).getText()).metadata(meta).build());
                }
                files++;
            }
            if (!batch.isEmpty()) vectorStore.add(batch);
            chunksPerCategory.put(category.name(), batch.size());
        }

        int total = chunksPerCategory.values().stream().mapToInt(Integer::intValue).sum();
        Map<String, Object> summary = new LinkedHashMap<>();
        summary.put("files", files);
        summary.put("chunks", total);
        summary.put("chunksPerCategory", chunksPerCategory);
        summary.put("chunkSizeTokens", chunkSize);
        summary.put("elapsedMs", (System.nanoTime() - t0) / 1_000_000);
        return summary;
    }
}
