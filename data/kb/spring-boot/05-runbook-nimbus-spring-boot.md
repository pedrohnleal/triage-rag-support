# Runbook Nimbus: serviços Spring Boot

Documento interno SIMULADO da plataforma fictícia Nimbus, criado para o experimento. As regras abaixo não existem fora desta base de conhecimento.

## Endpoint de saúde corporativo dos serviços Spring Boot

Todo serviço Spring Boot da plataforma Nimbus deve expor o endpoint `/actuator/health/nimbus` na porta de gerenciamento 9091 (`management.server.port=9091`). O balanceador interno Nimbus-LB consulta esse endpoint a cada 15 segundos e remove a instância da rotação após 3 falhas consecutivas.

## Limite do pool de conexões nos serviços Spring Boot da Nimbus

O padrão Nimbus para o HikariCP é `maximum-pool-size=12` em homologação e 24 em produção. Valores acima de 24 só podem ser usados com aprovação do Comitê de Arquitetura (CAE), registrada no ticket de mudança.

## Segredos nos serviços Spring Boot da Nimbus

Segredos nunca ficam em `application.properties`. O Cofre Nimbus, que é o Azure Key Vault do serviço, é montado como arquivos em `/run/nimbus/secrets`, e o serviço os lê com `spring.config.import=optional:configtree:/run/nimbus/secrets/`.

## Padrão de logs dos serviços Spring Boot da Nimbus

Em produção, os logs são emitidos em JSON no stdout, com os campos obrigatórios `traceId` e `tenantId`. O nível é `INFO` para os pacotes `br.nimbus` e `WARN` para `org.springframework`. Logs sem `tenantId` são descartados pelo coletor Nimbus-Logs.

## Cabeçalho de tenant obrigatório nas APIs da Nimbus

Toda API da Nimbus exige o cabeçalho `X-Nimbus-Tenant`. Quando ele está ausente, a resposta é HTTP 400 com o código de erro `NIM-4001` no corpo.

## Encerramento dos serviços Spring Boot no orquestrador Nimbus

Os serviços usam `server.shutdown=graceful` com `spring.lifecycle.timeout-per-shutdown-phase=25s`, porque o orquestrador Nimbus envia SIGKILL 30 segundos depois do SIGTERM.

## Tentativas e timeouts de chamadas externas dos serviços Spring Boot

Chamadas HTTP de saída têm timeout de conexão de 2 segundos e de leitura de 6 segundos, com no máximo 3 tentativas e backoff exponencial iniciando em 200 ms. Chamadas ao serviço `pagamentos-core` não podem ser repetidas automaticamente.

## Nome e tag das imagens dos serviços Spring Boot da Nimbus

As imagens publicadas no registro interno devem seguir o formato `registro.nimbus.local/servicos/<servico>:<aaaaMMdd>-<sha7>`, em que sha7 são os 7 primeiros caracteres do hash do commit. A tag `latest` é proibida em homologação e produção.

## Janela de deploy em produção dos serviços Spring Boot

Deploys em produção só ocorrem às terças e quintas-feiras, das 14h às 16h (horário de Brasília). Fora da janela é exigido um ticket de exceção de nível P1, aprovado pelo gerente de plataforma.

## Versão de Java dos serviços Spring Boot da Nimbus

Serviços novos devem usar Java 21 (LTS), com a imagem base `jre-21` do registro interno. Serviços legados em Java 17 podem permanecer até o fim do ciclo de suporte definido pelo time de plataforma.
