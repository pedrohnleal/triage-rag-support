package br.tcc.suporte.service;

import br.tcc.suporte.domain.Category;
import br.tcc.suporte.domain.TriageResult;
import br.tcc.suporte.metrics.RequestMetrics;
import br.tcc.suporte.metrics.RequestMetrics.Stage;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ai.chat.messages.SystemMessage;
import org.springframework.ai.chat.messages.UserMessage;
import org.springframework.ai.chat.model.ChatModel;
import org.springframework.ai.chat.model.ChatResponse;
import org.springframework.ai.chat.prompt.Prompt;
import org.springframework.ai.openai.OpenAiChatOptions;
import org.springframework.ai.openai.api.ResponseFormat;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;

/** Triagem de C2 e C3: categoria e confiança em JSON. */
@Service
public class TriageService {

    private static final Logger log = LoggerFactory.getLogger(TriageService.class);

    private final ChatModel chatModel;
    private final RequestMetrics metrics;
    private final ObjectMapper mapper;
    private final String systemPrompt;

    public TriageService(ChatModel chatModel, RequestMetrics metrics, ObjectMapper mapper,
                         @Value("classpath:prompts/triage-system.txt") Resource prompt) throws IOException {
        this.chatModel = chatModel;
        this.metrics = metrics;
        this.mapper = mapper;
        // O prompt é montado como mensagem pronta (sem PromptTemplate), pois contém chaves JSON.
        this.systemPrompt = prompt.getContentAsString(StandardCharsets.UTF_8);
    }

    public TriageResult classify(String question) {
        Prompt prompt = new Prompt(
                List.of(new SystemMessage(systemPrompt), new UserMessage(question)),
                OpenAiChatOptions.builder()
                        .responseFormat(ResponseFormat.builder().type(ResponseFormat.Type.JSON_OBJECT).build())
                        .build());

        ChatResponse response = metrics.timed(Stage.TRIAGE, () -> chatModel.call(prompt));
        metrics.recordUsage(Stage.TRIAGE, response.getMetadata().getUsage());

        TriageResult result = parse(response.getResult().getOutput().getText());
        metrics.triageOutcome(result.category(), result.confidence());
        return result;
    }

    private TriageResult parse(String raw) {
        try {
            String json = raw.strip().replaceAll("^```(?:json)?\\s*|\\s*```$", "");
            JsonNode node = mapper.readTree(json);
            Category category = Category.parse(node.path("category").asText("")).orElse(null);
            double confidence = Math.max(0.0, Math.min(1.0, node.path("confidence").asDouble(0.0)));
            return new TriageResult(category, confidence);
        } catch (Exception e) {
            log.warn("Resposta de triagem não interpretável: {}", raw);
            return new TriageResult(null, 0.0);
        }
    }
}
