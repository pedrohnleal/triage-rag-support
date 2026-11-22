package br.tcc.suporte.metrics;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

/**
 * Grava no CSV a medição de cada requisição /api/** (tempo no servidor). O cabeçalho
 * X-Run-Id identifica a rodada, por exemplo "c2-vu5" ou "c2-vu5-warmup".
 */
@Component
public class MetricsInterceptor implements HandlerInterceptor {

    private final RequestMetrics metrics;      // @RequestScope
    private final CsvMetricsWriter writer;

    public MetricsInterceptor(RequestMetrics metrics, CsvMetricsWriter writer) {
        this.metrics = metrics;
        this.writer = writer;
    }

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        String runId = request.getHeader("X-Run-Id");
        if (runId != null && runId.length() > 64) runId = runId.substring(0, 64);
        metrics.setRunId(runId);
        response.setHeader("X-Request-Id", metrics.requestId());
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response,
                                Object handler, Exception ex) {
        int status = response.getStatus();
        if (ex != null) {                       // exceção não tratada (500)
            if (status < 400) status = 500;
            metrics.fail(ex.getClass().getSimpleName() + ": " + ex.getMessage());
        }
        writer.append(metrics.toCsvRow(status));
    }
}
