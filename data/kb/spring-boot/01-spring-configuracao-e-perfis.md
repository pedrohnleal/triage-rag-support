# Spring Boot: configuração e perfis

## Ativação de perfis no Spring Boot

No Spring Boot, o perfil ativo é definido pela propriedade `spring.profiles.active`, que pode vir de `application.properties`, de um argumento de linha de comando (`--spring.profiles.active=hml`) ou da variável de ambiente `SPRING_PROFILES_ACTIVE`. Arquivos `application-{perfil}.properties` (ou `.yml`) são carregados além do arquivo base e sobrescrevem as propriedades de mesmo nome.

## Variáveis de ambiente e vinculação relaxada no Spring Boot

O Spring Boot aplica vinculação relaxada (relaxed binding): a propriedade `spring.datasource.url` pode ser fornecida pela variável de ambiente `SPRING_DATASOURCE_URL`, com letras maiúsculas e com pontos e hifens substituídos por sublinhados. Variáveis de ambiente têm precedência sobre os valores de `application.properties`.

## Porta do servidor no Spring Boot

A porta HTTP padrão de uma aplicação Spring Boot é 8080 e é alterada com `server.port`. O valor `server.port=0` faz o Spring Boot escolher uma porta livre aleatória, útil em testes de integração. Se a porta já estiver em uso, a aplicação falha na inicialização informando que a porta está ocupada.
