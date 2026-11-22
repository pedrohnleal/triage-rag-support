package br.tcc.suporte.domain;

import java.util.Locale;
import java.util.Optional;

/** Categorias de triagem, uma por pasta da base de conhecimento. */
public enum Category {
    SPRING_BOOT, DOCKER, AZURE, SQL_SERVER, NEXTJS;

    public String folderName() {
        return name().toLowerCase(Locale.ROOT).replace('_', '-');
    }

    /** Aceita variações como "Next.js", "sql server" e "SPRING-BOOT". */
    public static Optional<Category> parse(String raw) {
        if (raw == null) return Optional.empty();
        String norm = raw.toUpperCase(Locale.ROOT).replaceAll("[^A-Z0-9]", "");
        for (Category c : values()) {
            if (c.name().replace("_", "").equals(norm)) return Optional.of(c);
        }
        return Optional.empty();
    }
}
