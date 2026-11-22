package br.tcc.suporte.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.DefaultValue;

@ConfigurationProperties(prefix = "app")
public record AppProperties(
        @DefaultValue Triage triage,
        @DefaultValue Retrieval retrieval,
        @DefaultValue Kb kb,
        @DefaultValue Metrics metrics) {

    public record Triage(@DefaultValue("0.70") double confidenceThreshold) {}

    public record Retrieval(@DefaultValue("5") int topK) {}

    public record Kb(@DefaultValue("./data/kb") String path, @DefaultValue("512") int chunkSize) {}

    public record Metrics(@DefaultValue("./output/metrics/requests.csv") String csvPath) {}
}
