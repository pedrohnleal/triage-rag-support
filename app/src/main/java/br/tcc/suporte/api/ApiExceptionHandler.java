package br.tcc.suporte.api;

import br.tcc.suporte.metrics.RequestMetrics;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ai.retry.NonTransientAiException;
import org.springframework.ai.retry.TransientAiException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.client.ResourceAccessException;

import java.util.Map;

/**
 * Converte falhas da API externa em status HTTP. Como as retentativas estão desativadas,
 * um limite de taxa do provedor aparece como 429 no CSV e no k6.
 */
@RestControllerAdvice
public class ApiExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(ApiExceptionHandler.class);

    private final RequestMetrics metrics;

    public ApiExceptionHandler(RequestMetrics metrics) {
        this.metrics = metrics;
    }

    @ExceptionHandler({NonTransientAiException.class, TransientAiException.class, ResourceAccessException.class})
    public ResponseEntity<Map<String, Object>> upstream(RuntimeException ex) {
        String msg = String.valueOf(ex.getMessage());
        // Heurística: o Spring AI inclui o código HTTP do provedor na mensagem da exceção.
        boolean rateLimited = msg.contains("429");
        HttpStatus status = rateLimited ? HttpStatus.TOO_MANY_REQUESTS : HttpStatus.BAD_GATEWAY;
        metrics.fail((rateLimited ? "RATE_LIMIT: " : "UPSTREAM: ") + msg);
        log.warn("Falha na API externa ({}): {}", status.value(), msg);
        return ResponseEntity.status(status).body(Map.of(
                "status", status.value(),
                "error", rateLimited ? "rate_limited" : "upstream_error"));
    }
}
