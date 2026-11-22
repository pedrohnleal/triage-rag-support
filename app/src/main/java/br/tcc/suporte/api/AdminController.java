package br.tcc.suporte.api;

import br.tcc.suporte.service.KnowledgeBaseIngestor;
import org.springframework.boot.SpringBootVersion;
import org.springframework.core.env.Environment;
import org.springframework.core.io.ClassPathResource;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.io.IOException;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.Map;

/** Rotas administrativas: indexação da base e parâmetros efetivos do serviço. */
@RestController
@RequestMapping("/admin")
public class AdminController {

    private final KnowledgeBaseIngestor ingestor;
    private final Environment env;

    public AdminController(KnowledgeBaseIngestor ingestor, Environment env) {
        this.ingestor = ingestor;
        this.env = env;
    }

    /** POST /admin/ingest?reset=true apaga os trechos de cada categoria antes de reindexar. */
    @PostMapping("/ingest")
    public Map<String, Object> ingest(@RequestParam(defaultValue = "false") boolean reset) throws IOException {
        return ingestor.ingest(reset);
    }

    /** Modelos, parâmetros, versões e SHA-256 dos prompts. */
    @GetMapping("/info")
    public Map<String, Object> info() throws IOException, NoSuchAlgorithmException {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("chatModel", env.getProperty("spring.ai.openai.chat.options.model"));
        m.put("temperature", env.getProperty("spring.ai.openai.chat.options.temperature"));
        m.put("seed", env.getProperty("spring.ai.openai.chat.options.seed"));
        m.put("maxTokens", env.getProperty("spring.ai.openai.chat.options.max-tokens"));
        m.put("embeddingModel", env.getProperty("spring.ai.openai.embedding.options.model"));
        m.put("topK", env.getProperty("app.retrieval.top-k"));
        m.put("chunkSizeTokens", env.getProperty("app.kb.chunk-size"));
        m.put("confidenceThreshold", env.getProperty("app.triage.confidence-threshold"));
        m.put("javaVersion", System.getProperty("java.version"));
        m.put("springBootVersion", SpringBootVersion.getVersion());
        m.put("triagePromptSha256", sha256("prompts/triage-system.txt"));
        m.put("generationPromptSha256", sha256("prompts/generation-system.txt"));
        return m;
    }

    private static String sha256(String classpathResource) throws IOException, NoSuchAlgorithmException {
        byte[] bytes = new ClassPathResource(classpathResource).getContentAsByteArray();
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
    }
}
