# Spring Boot: ciclo de vida e empacotamento

## Encerramento gracioso no Spring Boot

Com `server.shutdown=graceful`, o servidor do Spring Boot deixa de aceitar novas requisições e aguarda as que estão em andamento por até `spring.lifecycle.timeout-per-shutdown-phase`, cujo padrão é 30 segundos. O valor padrão de `server.shutdown` é `immediate`, que encerra sem esperar.

## Dependência circular entre beans no Spring Boot

A partir do Spring Boot 2.6, referências circulares entre beans são proibidas por padrão, e a aplicação falha na inicialização apontando o ciclo. A solução recomendada é refatorar o código para quebrar o ciclo. Como medida temporária, é possível usar `spring.main.allow-circular-references=true`.

## Geração de imagem de contêiner pelo plugin do Spring Boot

O plugin do Maven `spring-boot:build-image` (no Gradle, `bootBuildImage`) gera uma imagem de contêiner com Cloud Native Buildpacks, sem necessidade de Dockerfile. Exige um daemon Docker acessível na máquina de build.
