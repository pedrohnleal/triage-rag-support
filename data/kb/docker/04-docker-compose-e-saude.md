# Docker Compose: saúde e variáveis

## Healthcheck e depends_on no Docker Compose

No Docker Compose, o `healthcheck` define `test`, `interval`, `timeout` e `retries`. A opção `depends_on` sozinha controla apenas a ordem de início, não a prontidão do serviço; para aguardar que o serviço esteja saudável usa-se `depends_on` com `condition: service_healthy`.

## Variáveis de ambiente no Docker Compose

No Compose, `environment:` define variáveis diretamente e `env_file:` as carrega de um arquivo. O arquivo `.env` na pasta do projeto é usado para substituir `${VAR}` dentro do próprio `compose.yaml`. Variáveis definidas no shell têm precedência sobre o arquivo `.env`.
