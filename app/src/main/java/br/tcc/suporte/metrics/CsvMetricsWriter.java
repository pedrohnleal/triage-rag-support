package br.tcc.suporte.metrics;

import br.tcc.suporte.config.AppProperties;
import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;

/** Uma linha por requisição, com flush imediato. */
@Component
public class CsvMetricsWriter {

    private static final Logger log = LoggerFactory.getLogger(CsvMetricsWriter.class);

    private final Path path;
    private BufferedWriter out;

    public CsvMetricsWriter(AppProperties props) {
        this.path = Path.of(props.metrics().csvPath()).toAbsolutePath();
    }

    @PostConstruct
    void init() throws IOException {
        Files.createDirectories(path.getParent());
        boolean newFile = !Files.exists(path) || Files.size(path) == 0;
        out = Files.newBufferedWriter(path, StandardCharsets.UTF_8,
                StandardOpenOption.CREATE, StandardOpenOption.APPEND);
        if (newFile) {
            out.write(RequestMetrics.CSV_HEADER);
            out.newLine();
            out.flush();
        }
        log.info("Métricas por requisição serão gravadas em {}", path);
    }

    public synchronized void append(String row) {
        try {
            out.write(row);
            out.newLine();
            out.flush();
        } catch (IOException e) {
            log.error("Falha ao gravar métrica em {}", path, e);
        }
    }

    @PreDestroy
    synchronized void close() throws IOException {
        if (out != null) out.close();
    }
}
