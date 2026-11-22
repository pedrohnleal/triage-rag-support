package br.tcc.suporte.domain;

/** {@code category} é nula quando a resposta do modelo não pôde ser interpretada. */
public record TriageResult(Category category, double confidence) {}
