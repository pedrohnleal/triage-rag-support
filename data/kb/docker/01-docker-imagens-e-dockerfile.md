# Docker: imagens e Dockerfile

## Build em múltiplos estágios no Docker

O multi-stage build do Docker usa várias instruções `FROM` em um mesmo Dockerfile. O estágio final copia apenas os artefatos necessários com `COPY --from=<estágio>`, descartando compiladores e dependências de build. O resultado é uma imagem final menor e com menor superfície de ataque.

## Cache de camadas no Dockerfile

No Docker, cada instrução do Dockerfile gera uma camada; se a instrução e seus arquivos de entrada não mudaram, o cache é reaproveitado. Para aproveitá-lo, copiam-se primeiro os arquivos de dependências (como `pom.xml` ou `package.json`) e instalam-se as dependências, e só depois o restante do código. Uma camada invalidada invalida todas as camadas seguintes.

## Arquivo .dockerignore

O arquivo `.dockerignore` lista caminhos excluídos do contexto de build, como `node_modules`, `.git` e `target`. Ele reduz o tamanho do contexto enviado ao daemon, acelera o build e evita que arquivos como `.env` sejam copiados para a imagem.

## ENTRYPOINT, CMD e sinais no Docker

No Dockerfile, `ENTRYPOINT` define o executável fixo e `CMD` fornece argumentos padrão, que podem ser sobrescritos no `docker run`. Na forma exec (`["java","-jar","app.jar"]`) o processo principal recebe sinais como SIGTERM diretamente; na forma shell, o processo principal é o `/bin/sh`, que pode não repassar o sinal à aplicação.
