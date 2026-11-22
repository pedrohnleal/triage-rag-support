package br.tcc.suporte.api;

import br.tcc.suporte.service.Orchestrator;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** Rotas das configurações C1, C2 e C3. */
@RestController
@RequestMapping("/api")
public class AskController {

    private final Orchestrator orchestrator;

    public AskController(Orchestrator orchestrator) {
        this.orchestrator = orchestrator;
    }

    @PostMapping("/c1/ask")
    public AskResponse c1(@Valid @RequestBody AskRequest request) {
        return orchestrator.c1(request);
    }

    @PostMapping("/c2/ask")
    public AskResponse c2(@Valid @RequestBody AskRequest request) {
        return orchestrator.c2(request);
    }

    @PostMapping("/c3/ask")
    public AskResponse c3(@Valid @RequestBody AskRequest request) {
        return orchestrator.c3(request);
    }
}
