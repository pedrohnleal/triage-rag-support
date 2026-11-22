package br.tcc.suporte.api;

import jakarta.validation.constraints.NotBlank;

public record AskRequest(String ticketId, @NotBlank String question) {}
