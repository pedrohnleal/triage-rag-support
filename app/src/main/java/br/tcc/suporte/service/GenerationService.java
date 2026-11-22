package br.tcc.suporte.service;

import br.tcc.suporte.metrics.RequestMetrics;
import br.tcc.suporte.metrics.RequestMetrics.Stage;
import org.springframework.ai.chat.messages.SystemMessage;
import org.springframework.ai.chat.messages.UserMessage;
import org.springframework.ai.chat.model.ChatModel;
import org.springframework.ai.chat.model.ChatResponse;
import org.springframework.ai.chat.prompt.Prompt;
import org.springframework.ai.document.Document;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;

/** Gera a resposta a partir dos trechos recuperados; sem contexto suficiente, responde NAO_ENCONTRADO. */
@Service
public class GenerationService {

    public static final String ABSTAIN_TOKEN = "NAO_ENCONTRADO";

    public record GenerationResult(String answer, boolean abstained) {}

    private final ChatModel chatModel;
    private final RequestMetrics metrics;
    private final String systemPrompt;

    public GenerationService(ChatModel chatModel, RequestMetrics metrics,
                             @Value("classpath:prompts/generation-system.txt") Resource prompt) throws IOException {
        this.chatModel = chatModel;
        this.metrics = metrics;
        this.systemPrompt = prompt.getContentAsString(StandardCharsets.UTF_8);
    }

    public GenerationResult generate(String question, List<Document> docs) {
        if (docs == null || docs.isEmpty()) {
            return new GenerationResult(ABSTAIN_TOKEN, true);
        }

        StringBuilder context = new StringBuilder("CONTEXTO:\n");
        for (int i = 0; i < docs.size(); i++) {
            Document d = docs.get(i);
            context.append('[').append(i + 1).append("] (fonte: ")
                    .append(d.getMetadata().getOrDefault("source", "desconhecida")).append(")\n")
                    .append(d.getText()).append("\n\n");
        }
        context.append("CHAMADO:\n").append(question);

        Prompt prompt = new Prompt(List.of(new SystemMessage(systemPrompt), new UserMessage(context.toString())));
        ChatResponse response = metrics.timed(Stage.GENERATION, () -> chatModel.call(prompt));
        metrics.recordUsage(Stage.GENERATION, response.getMetadata().getUsage());

        String answer = response.getResult().getOutput().getText().strip();
        return new GenerationResult(answer, answer.startsWith(ABSTAIN_TOKEN));
    }
}
