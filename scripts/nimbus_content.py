# -*- coding: utf-8 -*-
"""
Conteúdo do experimento: base de conhecimento (KB), 80 chamados com solução (TICKETS),
20 sem solução (UNANSWERABLE) e exemplos few-shot da triagem (FEWSHOT).
As regras dos runbooks da plataforma Nimbus são fictícias.
"""


def S(sid, title, body):
    return {"id": sid, "title": title, "body": body}


RUNBOOK_INTRO = (
    "Documento interno SIMULADO da plataforma fictícia Nimbus, criado para o experimento. "
    "As regras abaixo não existem fora desta base de conhecimento."
)

# base de conhecimento
KB = [
    # Spring Boot
    {
        "category": "spring-boot",
        "label": "Spring Boot",
        "docs": [
            {
                "file": "01-spring-configuracao-e-perfis.md",
                "title": "Spring Boot: configuração e perfis",
                "type": "nota-tecnica",
                "sections": [
                    S("SB-T01", "Ativação de perfis no Spring Boot",
                      "No Spring Boot, o perfil ativo é definido pela propriedade `spring.profiles.active`, que pode vir de "
                      "`application.properties`, de um argumento de linha de comando (`--spring.profiles.active=hml`) ou da "
                      "variável de ambiente `SPRING_PROFILES_ACTIVE`. Arquivos `application-{perfil}.properties` (ou `.yml`) "
                      "são carregados além do arquivo base e sobrescrevem as propriedades de mesmo nome."),
                    S("SB-T02", "Variáveis de ambiente e vinculação relaxada no Spring Boot",
                      "O Spring Boot aplica vinculação relaxada (relaxed binding): a propriedade `spring.datasource.url` pode ser "
                      "fornecida pela variável de ambiente `SPRING_DATASOURCE_URL`, com letras maiúsculas e com pontos e hifens "
                      "substituídos por sublinhados. Variáveis de ambiente têm precedência sobre os valores de `application.properties`."),
                    S("SB-T03", "Porta do servidor no Spring Boot",
                      "A porta HTTP padrão de uma aplicação Spring Boot é 8080 e é alterada com `server.port`. O valor "
                      "`server.port=0` faz o Spring Boot escolher uma porta livre aleatória, útil em testes de integração. "
                      "Se a porta já estiver em uso, a aplicação falha na inicialização informando que a porta está ocupada."),
                ],
            },
            {
                "file": "02-spring-actuator-e-logs.md",
                "title": "Spring Boot: Actuator e logs",
                "type": "nota-tecnica",
                "sections": [
                    S("SB-T04", "Exposição de endpoints do Spring Boot Actuator",
                      "No Spring Boot Actuator, nas versões recentes, apenas o endpoint `health` é exposto por HTTP por padrão. "
                      "Para expor outros endpoints usa-se `management.endpoints.web.exposure.include` (por exemplo `health,info,metrics`). "
                      "O caminho base padrão é `/actuator`. Para que o `health` mostre detalhes dos componentes, define-se "
                      "`management.endpoint.health.show-details`."),
                    S("SB-T05", "Porta de gerenciamento separada no Spring Boot",
                      "A propriedade `management.server.port` faz o Spring Boot Actuator atender os endpoints de gerenciamento em uma "
                      "porta diferente da porta da aplicação, o que permite restringir o acesso a eles por regras de rede."),
                    S("SB-T06", "Níveis de log no Spring Boot",
                      "O nível de log do Spring Boot é configurado por `logging.level.<pacote>`, por exemplo `logging.level.root=WARN` "
                      "e `logging.level.org.springframework.web=DEBUG`. Os níveis são TRACE, DEBUG, INFO, WARN, ERROR, FATAL e OFF, "
                      "e o nível padrão é INFO."),
                ],
            },
            {
                "file": "03-spring-dados-e-validacao.md",
                "title": "Spring Boot: dados, transações e validação",
                "type": "nota-tecnica",
                "sections": [
                    S("SB-T07", "Pool de conexões HikariCP no Spring Boot",
                      "O Spring Boot usa o HikariCP como pool de conexões padrão. O tamanho máximo padrão é de 10 conexões "
                      "(`spring.datasource.hikari.maximum-pool-size`) e o tempo máximo de espera por uma conexão é de 30000 ms "
                      "(`spring.datasource.hikari.connection-timeout`). Quando o pool se esgota, as requisições aguardam até o "
                      "timeout e então falham com erro de tempo esgotado ao obter conexão."),
                    S("SB-T08", "Rollback com @Transactional no Spring",
                      "Por padrão, `@Transactional` faz rollback apenas para exceções não verificadas (`RuntimeException` e `Error`). "
                      "Exceções verificadas (checked) não provocam rollback, a menos que se use o atributo `rollbackFor`. Chamar um "
                      "método transacional a partir da mesma classe (auto-invocação) não passa pelo proxy e a transação não é aplicada."),
                    S("SB-T09", "Validação de entrada no Spring Boot",
                      "Para validar o corpo de uma requisição no Spring Boot, inclui-se a dependência `spring-boot-starter-validation`, "
                      "anota-se o parâmetro do controller com `@Valid` e os campos com anotações como `@NotBlank` e `@Size`. "
                      "Uma falha de validação gera `MethodArgumentNotValidException` e, por padrão, resposta HTTP 400."),
                ],
            },
            {
                "file": "04-spring-ciclo-de-vida-e-empacotamento.md",
                "title": "Spring Boot: ciclo de vida e empacotamento",
                "type": "nota-tecnica",
                "sections": [
                    S("SB-T10", "Encerramento gracioso no Spring Boot",
                      "Com `server.shutdown=graceful`, o servidor do Spring Boot deixa de aceitar novas requisições e aguarda as que "
                      "estão em andamento por até `spring.lifecycle.timeout-per-shutdown-phase`, cujo padrão é 30 segundos. "
                      "O valor padrão de `server.shutdown` é `immediate`, que encerra sem esperar."),
                    S("SB-T11", "Dependência circular entre beans no Spring Boot",
                      "A partir do Spring Boot 2.6, referências circulares entre beans são proibidas por padrão, e a aplicação falha "
                      "na inicialização apontando o ciclo. A solução recomendada é refatorar o código para quebrar o ciclo. "
                      "Como medida temporária, é possível usar `spring.main.allow-circular-references=true`."),
                    S("SB-T12", "Geração de imagem de contêiner pelo plugin do Spring Boot",
                      "O plugin do Maven `spring-boot:build-image` (no Gradle, `bootBuildImage`) gera uma imagem de contêiner com "
                      "Cloud Native Buildpacks, sem necessidade de Dockerfile. Exige um daemon Docker acessível na máquina de build."),
                ],
            },
            {
                "file": "05-runbook-nimbus-spring-boot.md",
                "title": "Runbook Nimbus: serviços Spring Boot",
                "type": "runbook-simulado",
                "sections": [
                    S("SB-R01", "Endpoint de saúde corporativo dos serviços Spring Boot",
                      "Todo serviço Spring Boot da plataforma Nimbus deve expor o endpoint `/actuator/health/nimbus` na porta de "
                      "gerenciamento 9091 (`management.server.port=9091`). O balanceador interno Nimbus-LB consulta esse endpoint a "
                      "cada 15 segundos e remove a instância da rotação após 3 falhas consecutivas."),
                    S("SB-R02", "Limite do pool de conexões nos serviços Spring Boot da Nimbus",
                      "O padrão Nimbus para o HikariCP é `maximum-pool-size=12` em homologação e 24 em produção. Valores acima de 24 "
                      "só podem ser usados com aprovação do Comitê de Arquitetura (CAE), registrada no ticket de mudança."),
                    S("SB-R03", "Segredos nos serviços Spring Boot da Nimbus",
                      "Segredos nunca ficam em `application.properties`. O Cofre Nimbus, que é o Azure Key Vault do serviço, é montado "
                      "como arquivos em `/run/nimbus/secrets`, e o serviço os lê com "
                      "`spring.config.import=optional:configtree:/run/nimbus/secrets/`."),
                    S("SB-R04", "Padrão de logs dos serviços Spring Boot da Nimbus",
                      "Em produção, os logs são emitidos em JSON no stdout, com os campos obrigatórios `traceId` e `tenantId`. "
                      "O nível é `INFO` para os pacotes `br.nimbus` e `WARN` para `org.springframework`. Logs sem `tenantId` são "
                      "descartados pelo coletor Nimbus-Logs."),
                    S("SB-R05", "Cabeçalho de tenant obrigatório nas APIs da Nimbus",
                      "Toda API da Nimbus exige o cabeçalho `X-Nimbus-Tenant`. Quando ele está ausente, a resposta é HTTP 400 com o "
                      "código de erro `NIM-4001` no corpo."),
                    S("SB-R06", "Encerramento dos serviços Spring Boot no orquestrador Nimbus",
                      "Os serviços usam `server.shutdown=graceful` com `spring.lifecycle.timeout-per-shutdown-phase=25s`, porque o "
                      "orquestrador Nimbus envia SIGKILL 30 segundos depois do SIGTERM."),
                    S("SB-R07", "Tentativas e timeouts de chamadas externas dos serviços Spring Boot",
                      "Chamadas HTTP de saída têm timeout de conexão de 2 segundos e de leitura de 6 segundos, com no máximo "
                      "3 tentativas e backoff exponencial iniciando em 200 ms. Chamadas ao serviço `pagamentos-core` não podem ser "
                      "repetidas automaticamente."),
                    S("SB-R08", "Nome e tag das imagens dos serviços Spring Boot da Nimbus",
                      "As imagens publicadas no registro interno devem seguir o formato "
                      "`registro.nimbus.local/servicos/<servico>:<aaaaMMdd>-<sha7>`, em que sha7 são os 7 primeiros caracteres do hash "
                      "do commit. A tag `latest` é proibida em homologação e produção."),
                    S("SB-R09", "Janela de deploy em produção dos serviços Spring Boot",
                      "Deploys em produção só ocorrem às terças e quintas-feiras, das 14h às 16h (horário de Brasília). Fora da janela "
                      "é exigido um ticket de exceção de nível P1, aprovado pelo gerente de plataforma."),
                    S("SB-R10", "Versão de Java dos serviços Spring Boot da Nimbus",
                      "Serviços novos devem usar Java 21 (LTS), com a imagem base `jre-21` do registro interno. Serviços legados em "
                      "Java 17 podem permanecer até o fim do ciclo de suporte definido pelo time de plataforma."),
                ],
            },
        ],
    },
    # Docker
    {
        "category": "docker",
        "label": "Docker",
        "docs": [
            {
                "file": "01-docker-imagens-e-dockerfile.md",
                "title": "Docker: imagens e Dockerfile",
                "type": "nota-tecnica",
                "sections": [
                    S("DK-T01", "Build em múltiplos estágios no Docker",
                      "O multi-stage build do Docker usa várias instruções `FROM` em um mesmo Dockerfile. O estágio final copia apenas "
                      "os artefatos necessários com `COPY --from=<estágio>`, descartando compiladores e dependências de build. "
                      "O resultado é uma imagem final menor e com menor superfície de ataque."),
                    S("DK-T02", "Cache de camadas no Dockerfile",
                      "No Docker, cada instrução do Dockerfile gera uma camada; se a instrução e seus arquivos de entrada não mudaram, "
                      "o cache é reaproveitado. Para aproveitá-lo, copiam-se primeiro os arquivos de dependências (como `pom.xml` ou "
                      "`package.json`) e instalam-se as dependências, e só depois o restante do código. Uma camada invalidada invalida "
                      "todas as camadas seguintes."),
                    S("DK-T03", "Arquivo .dockerignore",
                      "O arquivo `.dockerignore` lista caminhos excluídos do contexto de build, como `node_modules`, `.git` e `target`. "
                      "Ele reduz o tamanho do contexto enviado ao daemon, acelera o build e evita que arquivos como `.env` sejam "
                      "copiados para a imagem."),
                    S("DK-T04", "ENTRYPOINT, CMD e sinais no Docker",
                      "No Dockerfile, `ENTRYPOINT` define o executável fixo e `CMD` fornece argumentos padrão, que podem ser "
                      "sobrescritos no `docker run`. Na forma exec (`[\"java\",\"-jar\",\"app.jar\"]`) o processo principal recebe "
                      "sinais como SIGTERM diretamente; na forma shell, o processo principal é o `/bin/sh`, que pode não repassar o "
                      "sinal à aplicação."),
                ],
            },
            {
                "file": "02-docker-rede-e-portas.md",
                "title": "Docker: rede e portas",
                "type": "nota-tecnica",
                "sections": [
                    S("DK-T05", "Publicação de portas no Docker",
                      "No Docker, a instrução `EXPOSE` apenas documenta a porta. Para acessar o contêiner a partir do host é preciso "
                      "publicar a porta com `-p <host>:<contêiner>` no `docker run` ou com `ports:` no Compose, por exemplo `-p 8081:8080`."),
                    S("DK-T06", "Comunicação entre contêineres no Docker Compose",
                      "No Docker Compose, os serviços entram em uma rede padrão e se resolvem pelo nome do serviço como hostname. "
                      "Dentro de um contêiner, `localhost` aponta para o próprio contêiner, não para o host nem para outros serviços. "
                      "Por isso uma aplicação deve usar o nome do serviço do banco, por exemplo `banco:5432`."),
                    S("DK-T07", "Acesso ao host a partir de um contêiner Docker",
                      "No Docker Desktop, o nome `host.docker.internal` resolve para o host. No Linux é necessário adicionar "
                      "`--add-host=host.docker.internal:host-gateway` ao `docker run` para obter o mesmo efeito."),
                ],
            },
            {
                "file": "03-docker-dados-e-recursos.md",
                "title": "Docker: dados e recursos",
                "type": "nota-tecnica",
                "sections": [
                    S("DK-T08", "Volumes nomeados e bind mounts no Docker",
                      "No Docker, um volume nomeado é gerenciado pelo Docker e persiste depois que o contêiner é removido, enquanto um "
                      "bind mount mapeia uma pasta do host. O comando `docker compose down` preserva os volumes nomeados; "
                      "`docker compose down -v` remove os volumes nomeados e, com eles, os dados."),
                    S("DK-T09", "Limites de memória e código de saída 137 no Docker",
                      "O limite de memória de um contêiner é definido com `--memory` (ou `mem_limit` no Compose). Ao exceder o limite, "
                      "o kernel encerra o processo. O código de saída 137 indica SIGKILL, comum quando o kernel encerra o processo por "
                      "falta de memória; a confirmação é feita pelo campo `OOMKilled` em `docker inspect`."),
                    S("DK-T10", "Políticas de reinício no Docker",
                      "As políticas de reinício do Docker são `no` (padrão), `on-failure[:max]`, `always` e `unless-stopped`. "
                      "A política `unless-stopped` reinicia o contêiner sempre, exceto quando ele foi parado manualmente."),
                ],
            },
            {
                "file": "04-docker-compose-e-saude.md",
                "title": "Docker Compose: saúde e variáveis",
                "type": "nota-tecnica",
                "sections": [
                    S("DK-T11", "Healthcheck e depends_on no Docker Compose",
                      "No Docker Compose, o `healthcheck` define `test`, `interval`, `timeout` e `retries`. A opção `depends_on` sozinha "
                      "controla apenas a ordem de início, não a prontidão do serviço; para aguardar que o serviço esteja saudável usa-se "
                      "`depends_on` com `condition: service_healthy`."),
                    S("DK-T12", "Variáveis de ambiente no Docker Compose",
                      "No Compose, `environment:` define variáveis diretamente e `env_file:` as carrega de um arquivo. O arquivo `.env` "
                      "na pasta do projeto é usado para substituir `${VAR}` dentro do próprio `compose.yaml`. Variáveis definidas no "
                      "shell têm precedência sobre o arquivo `.env`."),
                ],
            },
            {
                "file": "05-runbook-nimbus-docker.md",
                "title": "Runbook Nimbus: contêineres Docker",
                "type": "runbook-simulado",
                "sections": [
                    S("DK-R01", "Imagens base aprovadas na Nimbus",
                      "Somente imagens base do registro interno `registro.nimbus.local/base/` são aceitas: `jre-21`, `node-20` e "
                      "`debian-slim`. Imagens obtidas diretamente do Docker Hub são bloqueadas pelo proxy do registro e o build falha "
                      "ao baixá-las."),
                    S("DK-R02", "Usuário não root nos contêineres da Nimbus",
                      "Todo Dockerfile da Nimbus deve declarar `USER 10001`. Contêineres que executam como root são reprovados na "
                      "varredura do pipeline com o código `NIM-SEC-12`."),
                    S("DK-R03", "Limites de recursos padrão dos contêineres da Nimbus",
                      "O padrão Nimbus por contêiner é de 512 MB de memória e 0,5 vCPU. Serviços que precisem de mais recursos exigem "
                      "parecer do time de capacidade. Uso acima de 80% da memória por 5 minutos gera alerta."),
                    S("DK-R04", "Labels obrigatórias nas imagens da Nimbus",
                      "Toda imagem deve ter as labels `nimbus.owner` (e-mail do time responsável), `nimbus.service` e `nimbus.tier`, "
                      "cujos valores possíveis são `gold`, `silver` e `bronze`. Sem `nimbus.owner` a imagem não é publicada."),
                    S("DK-R05", "Tamanho máximo das imagens da Nimbus",
                      "O tamanho máximo de uma imagem é de 350 MB comprimidos. Acima disso o build falha com o código `NIM-IMG-07`; "
                      "a recomendação é usar build em múltiplos estágios."),
                    S("DK-R06", "Healthcheck padrão dos contêineres da Nimbus",
                      "Todo contêiner de serviço deve declarar `HEALTHCHECK` com `--interval=20s --timeout=3s --retries=3`. "
                      "O comando de verificação deve retornar código 0 somente quando o serviço estiver pronto para receber tráfego."),
                    S("DK-R07", "Política de reinício na Nimbus",
                      "No ambiente de homologação, os serviços usam `restart: unless-stopped`. A política `always` é proibida porque "
                      "mascara falhas de inicialização em laço."),
                    S("DK-R08", "Volumes e dados persistentes na Nimbus",
                      "Dados persistentes só podem ficar em volumes nomeados com prefixo `nmb_`. Bind mounts são proibidos fora do "
                      "ambiente de desenvolvimento, e o comando `docker compose down -v` é bloqueado em homologação pelo wrapper "
                      "`nimbus-compose`."),
                    S("DK-R09", "Limpeza automática de imagens do registro Nimbus",
                      "Imagens sem uso há 30 dias são removidas automaticamente do registro interno, exceto as que possuem tag "
                      "iniciada por `release-`."),
                    S("DK-R10", "Faixa de portas publicadas na Nimbus",
                      "As portas publicadas no host de homologação devem estar na faixa de 18000 a 18999. Portas fora dessa faixa são "
                      "bloqueadas pela regra de firewall."),
                ],
            },
        ],
    },
    # Azure
    {
        "category": "azure",
        "label": "Azure",
        "docs": [
            {
                "file": "01-azure-conceitos-basicos.md",
                "title": "Azure: conceitos básicos",
                "type": "nota-tecnica",
                "sections": [
                    S("AZ-T01", "Grupos de recursos no Azure",
                      "Um resource group (grupo de recursos) do Azure é um contêiner lógico em que todo recurso pertence a exatamente "
                      "um grupo. Excluir o grupo exclui todos os recursos dentro dele, de forma irreversível, salvo recursos com "
                      "recuperação (soft delete). Antes de excluir, é possível mover recursos para outro grupo."),
                    S("AZ-T02", "Azure CLI: login e assinatura ativa",
                      "No Azure CLI, `az login` autentica o usuário, `az account set --subscription <id-ou-nome>` define a assinatura "
                      "ativa e `az account show` exibe a assinatura corrente. Os comandos operam sobre a assinatura ativa; por isso, "
                      "recursos que aparecem no portal mas não na CLI costumam indicar assinatura errada."),
                    S("AZ-T03", "Controle de acesso por função (RBAC) no Azure",
                      "No RBAC do Azure, as funções internas mais comuns são Owner (todos os acessos, inclusive atribuir permissões), "
                      "Contributor (gerencia recursos, mas não atribui acesso) e Reader (somente leitura). As atribuições são herdadas "
                      "da assinatura para o grupo de recursos e deste para o recurso."),
                ],
            },
            {
                "file": "02-azure-app-service-e-container-apps.md",
                "title": "Azure: App Service e Container Apps",
                "type": "nota-tecnica",
                "sections": [
                    S("AZ-T04", "Configurações de aplicativo no Azure App Service",
                      "No Azure App Service, as configurações de aplicativo (application settings) são entregues ao app como variáveis "
                      "de ambiente. Alterar uma configuração reinicia o aplicativo. Configurações marcadas como de slot ficam presas ao "
                      "slot e não acompanham a troca (swap)."),
                    S("AZ-T05", "Slots de implantação no Azure App Service",
                      "Os deployment slots do Azure App Service exigem plano Standard ou superior; não estão disponíveis nos planos "
                      "Free, Shared e Basic. A troca (swap) entre slots promove a versão de staging para produção sem indisponibilidade, "
                      "após o aquecimento da instância."),
                    S("AZ-T06", "Escala a zero no Azure Container Apps",
                      "No Azure Container Apps é possível definir `minReplicas` igual a 0, caso em que o aplicativo escala a zero réplicas "
                      "quando não há tráfego. A primeira requisição após a escala a zero sofre atraso de partida a frio (cold start). "
                      "Para evitar o atraso, define-se `minReplicas` com valor maior ou igual a 1."),
                ],
            },
            {
                "file": "03-azure-segredos-e-identidade.md",
                "title": "Azure: segredos, identidade e dados",
                "type": "nota-tecnica",
                "sections": [
                    S("AZ-T07", "Identidade gerenciada no Azure",
                      "A identidade gerenciada do Azure pode ser atribuída pelo sistema (ciclo de vida atrelado ao recurso) ou pelo "
                      "usuário (recurso independente, reutilizável). Ela elimina credenciais no código, mas exige que se atribua uma "
                      "função RBAC ao recurso que será acessado."),
                    S("AZ-T08", "Referências ao Key Vault no Azure App Service",
                      "No Azure App Service, o valor de uma configuração pode referenciar um segredo com "
                      "`@Microsoft.KeyVault(SecretUri=https://<cofre>.vault.azure.net/secrets/<segredo>/)`. A referência só é resolvida "
                      "se o app tiver identidade gerenciada com permissão de leitura de segredos no cofre; sem a permissão, a referência "
                      "aparece com erro de status e o valor não é resolvido."),
                    S("AZ-T09", "Firewall do Azure SQL Database",
                      "O Azure SQL Database bloqueia acessos por padrão e usa regras de firewall do servidor baseadas em IP. Quando o IP "
                      "do cliente não está autorizado, a conexão falha com o erro 40615. A solução é criar uma regra de IP ou habilitar a "
                      "opção que permite o acesso de serviços do Azure ao servidor."),
                ],
            },
            {
                "file": "04-azure-operacao-e-custos.md",
                "title": "Azure: operação, registro de contêineres e custos",
                "type": "nota-tecnica",
                "sections": [
                    S("AZ-T10", "Application Insights e Azure Monitor",
                      "O Application Insights, parte do Azure Monitor, coleta telemetria de requisições, dependências, exceções e "
                      "traces. A aplicação se conecta por uma connection string, e os dados podem ser consultados com KQL em um "
                      "workspace do Log Analytics."),
                    S("AZ-T11", "Tags e orçamentos no Azure Cost Management",
                      "As tags do Azure são pares nome-valor usados no Cost Management para agrupar custos. Orçamentos geram alertas "
                      "quando percentuais definidos são atingidos, mas não interrompem recursos automaticamente."),
                    S("AZ-T12", "Azure Container Registry e autenticação de imagens",
                      "No Azure Container Registry, `az acr login --name <registro>` autentica o Docker local, e as imagens seguem o "
                      "formato `<registro>.azurecr.io/<repositório>:<tag>`. Para que App Service ou Container Apps baixem imagens sem "
                      "usuário e senha, usa-se identidade gerenciada com a função AcrPull."),
                ],
            },
            {
                "file": "05-runbook-nimbus-azure.md",
                "title": "Runbook Nimbus: recursos no Azure",
                "type": "runbook-simulado",
                "sections": [
                    S("AZ-R01", "Convenção de nomes de recursos Azure na Nimbus",
                      "Os recursos Azure seguem o padrão `nmb-<ambiente>-<servico>-<tipo>`, por exemplo `nmb-prd-pedidos-kv`. Os "
                      "ambientes válidos são `dev`, `hml` e `prd`. Nomes fora do padrão são bloqueados pela Azure Policy `nimbus-naming`."),
                    S("AZ-R02", "Regiões permitidas no Azure da Nimbus",
                      "Somente as regiões Brazil South (principal) e East US 2 (recuperação de desastres) são permitidas. "
                      "Qualquer outra região é bloqueada por policy."),
                    S("AZ-R03", "Tags obrigatórias nos recursos Azure da Nimbus",
                      "Todo recurso deve ter as tags `centro-de-custo` (formato CC-0000, com quatro dígitos), `responsavel` e `ambiente`. "
                      "Recursos sem a tag `centro-de-custo` são desligados após 72 horas pela automação Nimbus-Guard."),
                    S("AZ-R04", "Orçamentos dos grupos de recursos de homologação da Nimbus",
                      "Cada grupo de recursos de homologação tem orçamento mensal padrão de R$ 1.500, com alertas em 70% e 90% do valor. "
                      "Os orçamentos de produção são definidos conforme o tier do serviço."),
                    S("AZ-R05", "Acesso privilegiado no Azure da Nimbus",
                      "Ninguém recebe a função Owner de forma permanente. O acesso privilegiado é obtido por elevação just-in-time, "
                      "com duração máxima de 4 horas, aprovada pelo gestor e registrada no ticket."),
                    S("AZ-R06", "Rotação de segredos no Key Vault da Nimbus",
                      "Todo segredo no Key Vault do serviço (`nmb-<ambiente>-<servico>-kv`) deve ser rotacionado a cada 90 dias. "
                      "O time responsável recebe alerta aos 75 dias."),
                    S("AZ-R07", "Escala dos Container Apps na Nimbus",
                      "Em homologação, os Container Apps usam `minReplicas: 0`. Em produção, o mínimo é de 2 réplicas em zonas de "
                      "disponibilidade distintas, e o máximo padrão é de 10 réplicas."),
                    S("AZ-R08", "Slots de implantação obrigatórios no App Service da Nimbus",
                      "Todo App Service de produção deve ter o slot `staging`. O deploy direto no slot de produção é proibido, e a troca "
                      "(swap) só pode ocorrer depois de o smoke test automático ficar verde."),
                    S("AZ-R09", "Acesso ao Azure SQL na Nimbus",
                      "O acesso ao Azure SQL ocorre por Private Endpoint. Em produção, regras de firewall por IP público são proibidas e "
                      "a opção de permitir serviços do Azure fica desabilitada."),
                    S("AZ-R10", "Telemetria no Application Insights da Nimbus",
                      "Todo serviço publicado envia telemetria ao Application Insights do ambiente (`nmb-<ambiente>-ai`). A amostragem é "
                      "de 20% em produção e 100% em homologação, e a retenção é de 90 dias em produção e 30 dias em homologação."),
                ],
            },
        ],
    },
    # SQL Server
    {
        "category": "sql-server",
        "label": "SQL Server",
        "docs": [
            {
                "file": "01-sqlserver-instalacao-e-acesso.md",
                "title": "SQL Server: instalação e acesso",
                "type": "nota-tecnica",
                "sections": [
                    S("SQ-T01", "SQL Server em contêiner Docker",
                      "A imagem `mcr.microsoft.com/mssql/server` exige as variáveis `ACCEPT_EULA=Y` e `MSSQL_SA_PASSWORD` e usa a porta "
                      "1433. A senha do usuário SA deve ter ao menos 8 caracteres e combinar três das quatro categorias (maiúsculas, "
                      "minúsculas, dígitos e símbolos); uma senha fraca faz o contêiner encerrar logo após iniciar."),
                    S("SQ-T02", "Logins, usuários e usuários órfãos no SQL Server",
                      "No SQL Server, o login existe no nível do servidor e o user no nível do banco. Ao restaurar um banco em outra "
                      "instância, o usuário pode ficar órfão (orphaned user), porque o SID do login é diferente. A correção é feita com "
                      "`ALTER USER <usuario> WITH LOGIN = <login>`."),
                    S("SQ-T03", "Collation no SQL Server",
                      "A collation define a comparação e a ordenação de textos no SQL Server; em `SQL_Latin1_General_CP1_CI_AS`, CI "
                      "significa case-insensitive e AS, accent-sensitive. Conflito de collation entre colunas ou bancos gera erro de "
                      "conflito de collation, resolvido com a cláusula `COLLATE`."),
                ],
            },
            {
                "file": "02-sqlserver-consultas-e-indices.md",
                "title": "SQL Server: consultas e índices",
                "type": "nota-tecnica",
                "sections": [
                    S("SQ-T04", "Paginação com OFFSET e FETCH no SQL Server",
                      "A paginação no SQL Server usa `ORDER BY <coluna> OFFSET n ROWS FETCH NEXT m ROWS ONLY`. As cláusulas OFFSET e "
                      "FETCH exigem `ORDER BY`; sem ele a ordem não é garantida. Para evitar registros repetidos entre páginas, o "
                      "ordenamento deve incluir uma coluna única como critério de desempate."),
                    S("SQ-T05", "Índices clusterizados e não clusterizados no SQL Server",
                      "Cada tabela do SQL Server pode ter apenas um índice clusterizado (clustered), que define a ordem física das "
                      "linhas; por padrão, a chave primária cria um. Podem existir vários índices não clusterizados (nonclustered), "
                      "que aceitam colunas adicionais com `INCLUDE`."),
                    S("SQ-T06", "Plano de execução e estatísticas no SQL Server",
                      "No SQL Server, `SET STATISTICS IO ON` e o plano de execução real ajudam a diagnosticar consultas lentas. "
                      "Operações Table Scan ou Index Scan em tabelas grandes sugerem falta de índice. O Query Store registra o histórico "
                      "de planos de execução."),
                    S("SQ-T07", "Parameter sniffing no SQL Server",
                      "O parameter sniffing ocorre quando o plano é compilado com os valores do primeiro parâmetro recebido e fica "
                      "inadequado para outros valores. Mitigações incluem `OPTION (RECOMPILE)`, `OPTIMIZE FOR` e o uso de plan forcing "
                      "no Query Store."),
                ],
            },
            {
                "file": "03-sqlserver-transacoes-e-bloqueios.md",
                "title": "SQL Server: transações e bloqueios",
                "type": "nota-tecnica",
                "sections": [
                    S("SQ-T08", "Níveis de isolamento e READ_COMMITTED_SNAPSHOT no SQL Server",
                      "O nível de isolamento padrão do SQL Server é READ COMMITTED, em que leituras ficam bloqueadas por escritas ainda "
                      "não confirmadas. Com `ALTER DATABASE <banco> SET READ_COMMITTED_SNAPSHOT ON`, o SQL Server passa a usar versões "
                      "de linha e os leitores deixam de bloquear os escritores."),
                    S("SQ-T09", "Deadlock no SQL Server",
                      "Um deadlock no SQL Server gera o erro 1205: o servidor escolhe uma vítima e reverte sua transação. A aplicação "
                      "deve repetir a transação. Para reduzir a ocorrência, acessa-se os objetos sempre na mesma ordem e mantêm-se as "
                      "transações curtas."),
                    S("SQ-T10", "Investigação de bloqueios no SQL Server",
                      "Para identificar bloqueios no SQL Server, consulta-se `sys.dm_exec_requests`, cuja coluna `blocking_session_id` "
                      "indica a sessão bloqueadora, ou usa-se `sp_who2`. O comando `KILL <spid>` encerra uma sessão."),
                ],
            },
            {
                "file": "04-sqlserver-backup-e-log.md",
                "title": "SQL Server: backup e log de transações",
                "type": "nota-tecnica",
                "sections": [
                    S("SQ-T11", "Modelos de recuperação e log cheio no SQL Server",
                      "Os modelos de recuperação do SQL Server são FULL, BULK_LOGGED e SIMPLE. No modelo FULL, o log de transações só é "
                      "truncado após um backup de log; sem backups de log, o arquivo `.ldf` cresce até encher o disco e ocorre o "
                      "erro 9002 (log de transações cheio)."),
                    S("SQ-T12", "Backup e restauração no SQL Server",
                      "O backup é feito com `BACKUP DATABASE <banco> TO DISK = '<caminho>'`. Na restauração, `RESTORE DATABASE ... WITH MOVE` "
                      "relocaliza arquivos quando os caminhos diferem; `WITH RECOVERY` finaliza a restauração e `WITH NORECOVERY` permite "
                      "aplicar backups adicionais."),
                ],
            },
            {
                "file": "05-runbook-nimbus-sql-server.md",
                "title": "Runbook Nimbus: bancos SQL Server",
                "type": "runbook-simulado",
                "sections": [
                    S("SQ-R01", "Padrão de nomes de bancos SQL Server na Nimbus",
                      "Os bancos seguem o padrão `nmb_<servico>_<ambiente>`, sem hifens, por exemplo `nmb_pedidos_prd`."),
                    S("SQ-R02", "Collation padrão dos bancos da Nimbus",
                      "Todos os bancos novos da Nimbus usam a collation `Latin1_General_100_CI_AI`, que é diferente do padrão da "
                      "instalação. Por isso a criação deve informar `COLLATE` de forma explícita."),
                    S("SQ-R03", "Contas de aplicação nos bancos da Nimbus",
                      "Aplicações nunca usam o login `sa`. Cada serviço tem um login `svc_<servico>` com as funções `db_datareader` e "
                      "`db_datawriter`. A função `db_owner` só é concedida com aprovação do time de DBA da Nimbus (DataGov)."),
                    S("SQ-R04", "Isolamento obrigatório nos bancos transacionais da Nimbus",
                      "Os bancos transacionais devem ter `READ_COMMITTED_SNAPSHOT ON`. A configuração é verificada semanalmente pelo "
                      "job `nmb_audit_rcsi`."),
                    S("SQ-R05", "Política de backup dos bancos de produção da Nimbus",
                      "Em produção, o backup FULL é diário às 02h, o diferencial ocorre a cada 6 horas e o backup de log a cada "
                      "15 minutos. A retenção é de 35 dias. Em homologação, o backup FULL é semanal, aos domingos."),
                    S("SQ-R06", "Timeouts de comando nos bancos da Nimbus",
                      "Consultas das aplicações têm timeout de 30 segundos. Relatórios em lote usam timeout de 300 segundos e devem "
                      "executar na réplica de leitura `nmb-ro`."),
                    S("SQ-R07", "Repetição de transações vítimas de deadlock na Nimbus",
                      "O serviço deve repetir no máximo 2 vezes a transação escolhida como vítima de deadlock (erro 1205), esperando "
                      "100 ms entre as tentativas. A terceira falha abre automaticamente um incidente de nível P3."),
                    S("SQ-R08", "Crescimento do arquivo de log nos bancos da Nimbus",
                      "Os arquivos de log têm crescimento fixo de 512 MB, e não em porcentagem, com limite de 50 GB por banco. "
                      "É gerado alerta quando 80% do limite é atingido."),
                    S("SQ-R09", "Dados de produção em ambientes de desenvolvimento na Nimbus",
                      "É proibido restaurar cópias de produção em ambientes de desenvolvimento. Os dados de desenvolvimento devem ser "
                      "anonimizados com o script `nmb_anonimiza.sql`."),
                    S("SQ-R10", "Manutenção de índices nos bancos da Nimbus",
                      "Índices com fragmentação entre 10% e 30% são reorganizados, e acima de 30% são reconstruídos. A manutenção "
                      "ocorre aos domingos, das 01h às 04h."),
                ],
            },
        ],
    },
    # Next.js
    {
        "category": "nextjs",
        "label": "Next.js",
        "docs": [
            {
                "file": "01-nextjs-roteamento-e-componentes.md",
                "title": "Next.js: roteamento e componentes",
                "type": "nota-tecnica",
                "sections": [
                    S("NX-T01", "App Router e Pages Router no Next.js",
                      "O Next.js possui dois sistemas de roteamento: o App Router (diretório `app/`, com layouts e Server Components) e o "
                      "Pages Router (diretório `pages/`). Eles podem coexistir, mas se ambos definirem a mesma rota ocorre conflito no "
                      "build; é preciso manter a rota em apenas um deles."),
                    S("NX-T02", "Server Components e Client Components no Next.js",
                      "No App Router do Next.js, os componentes são Server Components por padrão. Para usar `useState`, `useEffect` ou "
                      "manipuladores como `onClick`, o arquivo deve começar com a diretiva `'use client'`. Usar um hook de estado em um "
                      "Server Component gera erro de build."),
                    S("NX-T03", "Rotas dinâmicas no Next.js",
                      "No Next.js, uma pasta com nome entre colchetes, como `[id]`, cria uma rota dinâmica cujo valor chega em `params`. "
                      "O formato `[...slug]` captura vários segmentos de caminho."),
                ],
            },
            {
                "file": "02-nextjs-dados-e-ambiente.md",
                "title": "Next.js: dados e ambiente",
                "type": "nota-tecnica",
                "sections": [
                    S("NX-T04", "Variáveis de ambiente públicas no Next.js",
                      "No Next.js, variáveis definidas em `.env.local` ficam disponíveis apenas no servidor. Para chegar ao navegador, o "
                      "nome precisa começar com `NEXT_PUBLIC_`, e o valor é incorporado ao bundle no momento do build. Alterar a variável "
                      "depois, sem refazer o build, não muda o código do cliente."),
                    S("NX-T05", "Route Handlers no Next.js",
                      "No App Router do Next.js, um arquivo `route.ts` dentro de `app/api/<nome>/` define um endpoint e exporta funções "
                      "nomeadas por método HTTP, como `GET` e `POST`, usando os objetos padrão Request e Response."),
                    S("NX-T06", "Cache de fetch no Next.js",
                      "O comportamento de cache padrão do `fetch` no servidor do Next.js mudou entre versões maiores. Para dados sempre "
                      "atualizados usa-se `cache: 'no-store'` ou `export const dynamic = 'force-dynamic'`; para revalidar por tempo usa-se "
                      "`next: { revalidate: 60 }`."),
                ],
            },
            {
                "file": "03-nextjs-imagens-e-erros.md",
                "title": "Next.js: imagens, erros e proxy",
                "type": "nota-tecnica",
                "sections": [
                    S("NX-T07", "Imagens remotas com next/image no Next.js",
                      "Imagens remotas usadas com `next/image` precisam ser autorizadas em `images.remotePatterns` no `next.config.js`. "
                      "Sem isso, o Next.js lança erro informando que o hostname não está configurado."),
                    S("NX-T08", "Erros de hidratação no Next.js",
                      "Erros de hidratação ocorrem quando o HTML gerado no servidor difere do primeiro render no cliente, por exemplo ao "
                      "usar `Date.now()`, `Math.random()` ou `window` durante a renderização. A solução é mover esse código para "
                      "`useEffect` ou, em casos pontuais, usar `suppressHydrationWarning`."),
                    S("NX-T09", "Rewrites no Next.js para evitar CORS",
                      "A função `rewrites()` em `next.config.js` encaminha requisições de um caminho do Next.js, como "
                      "`/api/externo/:path*`, para outro destino. Isso serve de proxy e evita problemas de CORS quando o navegador "
                      "chamaria uma API em outra origem."),
                ],
            },
            {
                "file": "04-nextjs-build-e-implantacao.md",
                "title": "Next.js: build e implantação",
                "type": "nota-tecnica",
                "sections": [
                    S("NX-T10", "Comandos next dev, next build e next start",
                      "O comando `next dev` inicia o modo de desenvolvimento, `next build` gera o build de produção e `next start` serve "
                      "esse build. Executar `next start` sem build prévio falha pedindo a execução de `next build`."),
                    S("NX-T11", "Saída standalone do Next.js",
                      "Com `output: 'standalone'` no `next.config.js`, o Next.js gera `.next/standalone` com um servidor mínimo e apenas "
                      "as dependências necessárias, executado com `node server.js`. As pastas `.next/static` e `public` precisam ser "
                      "copiadas manualmente para o destino."),
                    S("NX-T12", "Porta do Next.js",
                      "A porta do Next.js é alterada com `next dev -p 4000` e `next start -p 4000`, ou pela variável de ambiente `PORT`."),
                ],
            },
            {
                "file": "05-runbook-nimbus-nextjs.md",
                "title": "Runbook Nimbus: aplicações Next.js",
                "type": "runbook-simulado",
                "sections": [
                    S("NX-R01", "Node e gerenciador de pacotes das aplicações Next.js da Nimbus",
                      "As aplicações Next.js da Nimbus usam Node 20 LTS e pnpm. O lockfile oficial é `pnpm-lock.yaml`, e o comando "
                      "`npm install` é bloqueado no pipeline com o código `NIM-FE-03`."),
                    S("NX-R02", "Variáveis públicas nas aplicações Next.js da Nimbus",
                      "Variáveis públicas devem usar o prefixo `NEXT_PUBLIC_NMB_`. É proibido colocar segredos em variáveis "
                      "`NEXT_PUBLIC_*`, e o linter `nimbus-env-lint` reprova o código que fizer isso."),
                    S("NX-R03", "Base path das aplicações Next.js da Nimbus",
                      "Os front-ends são servidos sob o caminho `/app/<servico>`, e o `next.config.js` deve definir "
                      "`basePath: '/app/<servico>'`."),
                    S("NX-R04", "Chamadas a APIs nas aplicações Next.js da Nimbus",
                      "O front-end não chama serviços internos diretamente do navegador. As chamadas passam por route handlers que "
                      "funcionam como BFF em `app/api/bff/`, os quais acessam o gateway de APIs Nimbus-GW."),
                    S("NX-R05", "Estratégia de cache nas aplicações Next.js da Nimbus",
                      "Páginas autenticadas devem usar `dynamic = 'force-dynamic'`. Páginas públicas de conteúdo revalidam a cada "
                      "300 segundos, com `revalidate: 300`."),
                    S("NX-R06", "Domínios de imagens autorizados nas aplicações Next.js da Nimbus",
                      "Os únicos domínios de imagem autorizados em `images.remotePatterns` são `cdn.nimbus.local` e "
                      "`assets.nimbus.local`. Outros domínios são reprovados na revisão de código."),
                    S("NX-R07", "Empacotamento em contêiner das aplicações Next.js da Nimbus",
                      "As imagens Next.js usam `output: 'standalone'`, com `PORT=3000` e `HOSTNAME=0.0.0.0`. O healthcheck consulta a "
                      "rota `/api/health`."),
                    S("NX-R08", "Limite de bundle das aplicações Next.js da Nimbus",
                      "O JavaScript inicial por rota deve ter no máximo 200 KB comprimidos. Acima disso o pipeline falha com o "
                      "código `NIM-FE-09`."),
                    S("NX-R09", "Internacionalização nas aplicações Next.js da Nimbus",
                      "O idioma padrão é `pt-BR` e o secundário é `en-US`. Os textos ficam em arquivos `messages/<locale>.json`, e "
                      "textos fixos no código são reprovados na revisão."),
                    S("NX-R10", "Cobertura mínima de testes nas aplicações Next.js da Nimbus",
                      "A cobertura mínima de testes é de 70% das linhas. Abaixo disso o merge é bloqueado."),
                ],
            },
        ],
    },
]

# chamados com solução: (seção, pergunta, resposta de referência, prioridade A/M/B, categoria ambígua)
TICKETS = [
    # Spring Boot (16)
    ("SB-T01",
     "Subi o serviço em homologação, mas ele está carregando as propriedades de dev. Como faço o Spring Boot usar o "
     "application-hml.properties sem mexer no jar?",
     "Definir o perfil ativo como `hml`, por exemplo pela variável de ambiente `SPRING_PROFILES_ACTIVE` ou pelo argumento "
     "`--spring.profiles.active=hml`. O arquivo `application-{perfil}.properties` correspondente (no caso, o de hml) é carregado e sobrescreve as propriedades de mesmo nome do arquivo base.",
     "M", None),
    ("SB-T02",
     "Quero sobrescrever a URL do banco no deploy usando variável de ambiente, mas não sei qual nome o Spring Boot espera "
     "para spring.datasource.url.",
     "O nome é `SPRING_DATASOURCE_URL`: letras maiúsculas, com pontos e hifens trocados por sublinhados (vinculação relaxada). "
     "A variável de ambiente tem precedência sobre `application.properties`.",
     "B", None),
    ("SB-T04",
     "Chamo /actuator/metrics na minha API e recebo 404, mas /actuator/health funciona. O que falta configurar?",
     "Nas versões recentes apenas o endpoint `health` é exposto por HTTP por padrão. É preciso incluir o endpoint em "
     "`management.endpoints.web.exposure.include`, por exemplo `health,info,metrics`.",
     "M", None),
    ("SB-T07",
     "No horário de pico a aplicação começa a lançar erro de timeout ao obter conexão com o banco. Qual é o limite padrão do "
     "pool e quanto tempo ele espera?",
     "O pool padrão (HikariCP) tem 10 conexões (`spring.datasource.hikari.maximum-pool-size`) e espera até 30000 ms "
     "(`spring.datasource.hikari.connection-timeout`) por uma conexão. Esgotado o pool, as requisições falham por tempo esgotado.",
     "A", None),
    ("SB-T08",
     "Meu método de serviço lança uma exceção checked depois de gravar no banco e o registro continua salvo, mesmo com "
     "@Transactional. Por quê?",
     "Por padrão `@Transactional` faz rollback apenas para `RuntimeException` e `Error`. Para exceções checked é necessário "
     "configurar o atributo `rollbackFor`.",
     "A", None),
    ("SB-T09",
     "Coloquei @NotBlank nos campos do DTO, mas o controller aceita valores vazios. O que preciso para a validação funcionar?",
     "Incluir a dependência `spring-boot-starter-validation` e anotar o parâmetro do controller com `@Valid`. "
     "A falha de validação gera `MethodArgumentNotValidException` e resposta HTTP 400 por padrão.",
     "M", None),
    ("SB-T11",
     "Depois de atualizar o Spring Boot a aplicação não sobe mais e reclama de dependência circular entre dois beans de serviço. "
     "Antes funcionava.",
     "A partir do Spring Boot 2.6 as referências circulares são proibidas por padrão. O recomendado é refatorar para quebrar o ciclo; "
     "como medida temporária pode-se usar `spring.main.allow-circular-references=true`.",
     "A", None),
    ("SB-R01",
     "O balanceador da Nimbus está tirando minha instância do ar. Qual endpoint e qual porta o serviço precisa expor para passar "
     "nas verificações de saúde?",
     "O serviço deve expor `/actuator/health/nimbus` na porta de gerenciamento 9091. O Nimbus-LB consulta a cada 15 segundos e remove "
     "a instância após 3 falhas consecutivas.",
     "A", None),
    ("SB-R02",
     "Preciso aumentar o pool de conexões do meu serviço em produção para 40. Posso configurar direto?",
     "Não diretamente. O padrão Nimbus é `maximum-pool-size=12` em homologação e 24 em produção; valores acima de 24 exigem aprovação "
     "do Comitê de Arquitetura (CAE), registrada no ticket de mudança.",
     "M", None),
    ("SB-R03",
     "Preciso guardar a senha do banco do meu serviço Spring Boot. Vi que o Azure tem Key Vault e que aqui existe o Cofre Nimbus. "
     "Onde isso deve ficar?",
     "Segredos nunca ficam em `application.properties`. Ficam no Cofre Nimbus (o Azure Key Vault do serviço), montado como arquivos em "
     "`/run/nimbus/secrets` e lido com `spring.config.import=optional:configtree:/run/nimbus/secrets/`.",
     "A", "azure"),
    ("SB-R04",
     "Meus logs de produção não aparecem na plataforma de logs, e eles já saem em JSON no stdout. O que pode estar errado?",
     "Os logs precisam conter os campos obrigatórios `traceId` e `tenantId`; logs sem `tenantId` são descartados pelo coletor Nimbus-Logs.",
     "M", None),
    ("SB-R05",
     "Chamei a API de pedidos e voltou HTTP 400 com o código NIM-4001. Que erro é esse?",
     "O cabeçalho `X-Nimbus-Tenant` está ausente. Toda API da Nimbus o exige e, sem ele, responde HTTP 400 com o código `NIM-4001`.",
     "B", None),
    ("SB-R06",
     "Meu serviço Spring Boot, rodando em contêiner, é morto no meio das requisições durante o deploy. Como configuro o encerramento "
     "considerando o orquestrador da Nimbus?",
     "Usar `server.shutdown=graceful` com `spring.lifecycle.timeout-per-shutdown-phase=25s`, porque o orquestrador Nimbus envia SIGKILL "
     "30 segundos depois do SIGTERM.",
     "M", "docker"),
    ("SB-R08",
     "Estou gerando a imagem do meu serviço Spring Boot com o build-image do Maven. Que nome e tag devo usar ao publicar no registro "
     "da Nimbus?",
     "O formato é `registro.nimbus.local/servicos/<servico>:<aaaaMMdd>-<sha7>`, em que sha7 são os 7 primeiros caracteres do hash do "
     "commit. A tag `latest` é proibida em homologação e produção.",
     "M", "docker"),
    ("SB-R09",
     "Posso fazer deploy do serviço em produção na segunda-feira de manhã?",
     "Não. Deploys em produção só ocorrem às terças e quintas-feiras, das 14h às 16h (horário de Brasília). Fora da janela é exigido "
     "ticket de exceção de nível P1, aprovado pelo gerente de plataforma.",
     "A", None),
    ("SB-T10",
     "Quando dou docker stop no contêiner da minha API Spring Boot, as requisições em andamento são cortadas. Como o Spring Boot "
     "pode esperá-las terminar?",
     "Ativar `server.shutdown=graceful`: o servidor deixa de aceitar novas requisições e aguarda as em andamento por até "
     "`spring.lifecycle.timeout-per-shutdown-phase`, cujo padrão é 30 segundos.",
     "M", "docker"),

    # Docker (16)
    ("DK-T01",
     "A imagem do meu app Java com Maven ficou com mais de 700 MB porque o JDK completo e o Maven vão junto. Como reduzo sem perder "
     "o build dentro do Docker?",
     "Usar build em múltiplos estágios: várias instruções `FROM` no mesmo Dockerfile, com o estágio final copiando apenas o artefato "
     "necessário por `COPY --from=<estágio>`.",
     "M", "spring-boot"),
    ("DK-T02",
     "Todo build do Dockerfile do meu app Next.js reinstala todas as dependências, mesmo quando só mudo um arquivo de código. "
     "Como acelero?",
     "Aproveitar o cache de camadas: copiar primeiro os arquivos de dependências (como `package.json`), instalar, e só depois copiar o "
     "restante do código. Uma camada invalidada invalida todas as seguintes.",
     "M", "nextjs"),
    ("DK-T04",
     "Meu contêiner demora cerca de 10 segundos para parar com docker stop. O Dockerfile termina com CMD java -jar app.jar, sem colchetes.",
     "Na forma shell o processo principal é o `/bin/sh`, que pode não repassar o SIGTERM à aplicação. A forma exec "
     "(`[\"java\",\"-jar\",\"app.jar\"]`) entrega o sinal diretamente ao processo principal.",
     "M", None),
    ("DK-T05",
     "Subi o contêiner com EXPOSE 8080 no Dockerfile, mas o navegador não abre localhost:8080. O que está faltando?",
     "`EXPOSE` apenas documenta a porta. É preciso publicá-la com `-p <host>:<contêiner>` no `docker run` ou com `ports:` no Compose.",
     "B", None),
    ("DK-T06",
     "Minha API em contêiner usa localhost:1433 para acessar o SQL Server, que roda como outro serviço no compose, e dá connection refused.",
     "Dentro de um contêiner `localhost` aponta para o próprio contêiner. No Compose os serviços se resolvem pelo nome do serviço como "
     "hostname; deve-se usar o nome do serviço do banco.",
     "A", "sql-server"),
    ("DK-T08",
     "Rodei docker compose down -v para limpar o ambiente e perdi todos os dados do banco de teste. Por que isso aconteceu?",
     "O `docker compose down -v` remove os volumes nomeados e, com eles, os dados. O `docker compose down` sem `-v` preserva os volumes nomeados.",
     "A", None),
    ("DK-T09",
     "Meu contêiner some do nada e o docker ps -a mostra código de saída 137. O que isso significa?",
     "O código 137 indica SIGKILL, comum quando o kernel encerra o processo por falta de memória. A confirmação é feita pelo campo "
     "`OOMKilled` em `docker inspect`; o limite é definido com `--memory`.",
     "M", None),
    ("DK-T11",
     "A API sobe antes de o banco ficar pronto e cai com erro de conexão, mesmo usando depends_on no compose.",
     "O `depends_on` sozinho controla apenas a ordem de início, não a prontidão. É preciso definir um `healthcheck` no serviço do banco e "
     "usar `depends_on` com `condition: service_healthy`.",
     "M", None),
    ("DK-R01",
     "Usei FROM node:20 no Dockerfile do meu app Next.js e o build falha ao baixar a imagem na esteira. Qual imagem base devo usar?",
     "Somente imagens do registro interno `registro.nimbus.local/base/` são aceitas (`jre-21`, `node-20` e `debian-slim`). Imagens do "
     "Docker Hub são bloqueadas pelo proxy do registro.",
     "A", "nextjs"),
    ("DK-R02",
     "A esteira reprovou minha imagem com o código NIM-SEC-12. O que devo fazer?",
     "O contêiner executa como root. Todo Dockerfile da Nimbus deve declarar `USER 10001`.",
     "A", None),
    ("DK-R03",
     "Quais limites de memória e CPU devo configurar por contêiner na Nimbus? Meu serviço Spring Boot usa bastante heap.",
     "O padrão Nimbus é de 512 MB de memória e 0,5 vCPU por contêiner. Mais recursos exigem parecer do time de capacidade, e uso acima "
     "de 80% da memória por 5 minutos gera alerta.",
     "M", "spring-boot"),
    ("DK-R04",
     "A publicação da imagem foi rejeitada dizendo que faltam labels. Quais são obrigatórias?",
     "`nimbus.owner` (e-mail do time responsável), `nimbus.service` e `nimbus.tier`, com valores `gold`, `silver` ou `bronze`. "
     "Sem `nimbus.owner` a imagem não é publicada.",
     "B", None),
    ("DK-R05",
     "O build falhou com o código NIM-IMG-07. O que significa?",
     "A imagem excede o limite de 350 MB comprimidos. A recomendação é usar build em múltiplos estágios.",
     "M", None),
    ("DK-R06",
     "Como devo configurar o HEALTHCHECK no Dockerfile conforme o padrão da Nimbus?",
     "Declarar `HEALTHCHECK` com `--interval=20s --timeout=3s --retries=3`; o comando deve retornar código 0 somente quando o serviço "
     "estiver pronto para receber tráfego.",
     "B", None),
    ("DK-R08",
     "Preciso persistir os dados do contêiner em homologação. Posso usar um bind mount de uma pasta do servidor?",
     "Não. Dados persistentes só podem ficar em volumes nomeados com prefixo `nmb_`; bind mounts são proibidos fora de desenvolvimento, "
     "e o `docker compose down -v` é bloqueado em homologação pelo wrapper `nimbus-compose`.",
     "M", None),
    ("DK-R10",
     "Publiquei meu contêiner na porta 9090 do host de homologação e ninguém consegue acessar. Por quê?",
     "As portas publicadas no host de homologação devem estar na faixa de 18000 a 18999; portas fora dela são bloqueadas pela regra de firewall.",
     "M", None),

    # Azure (16)
    ("AZ-T01",
     "Apaguei por engano um resource group de testes e sumiram também o banco e o app que estavam nele. Por que isso aconteceu?",
     "Excluir um grupo de recursos exclui todos os recursos dentro dele, de forma irreversível, salvo recursos com recuperação (soft delete). "
     "Antes de excluir é possível mover recursos para outro grupo.",
     "A", None),
    ("AZ-T02",
     "Rodo az webapp list e não aparecem os apps que vejo no portal. Já fiz login.",
     "Provavelmente a assinatura ativa está errada. Verificar com `az account show` e trocar com `az account set --subscription <id-ou-nome>`.",
     "B", None),
    ("AZ-T04",
     "Mudei uma configuração do meu App Service que roda um app Spring Boot e ele reiniciou sozinho. Isso é normal?",
     "Sim. As configurações de aplicativo do App Service são entregues como variáveis de ambiente, e alterar uma configuração reinicia o aplicativo.",
     "M", "spring-boot"),
    ("AZ-T05",
     "Quero usar deployment slots no meu App Service, mas a opção aparece desabilitada no plano Basic.",
     "Os deployment slots exigem plano Standard ou superior; não estão disponíveis em Free, Shared e Basic.",
     "B", None),
    ("AZ-T06",
     "O Container App fica lento apenas na primeira requisição depois de horas sem uso. Isso é um bug?",
     "Não. Com `minReplicas` igual a 0 o aplicativo escala a zero e a primeira requisição sofre partida a frio (cold start). Para evitar, "
     "definir `minReplicas` maior ou igual a 1.",
     "M", None),
    ("AZ-T08",
     "Coloquei @Microsoft.KeyVault(SecretUri=...) numa configuração do App Service e o valor não é resolvido.",
     "O app precisa ter identidade gerenciada com permissão de leitura de segredos no cofre; sem ela a referência aparece com erro de status "
     "e o valor não é resolvido.",
     "A", None),
    ("AZ-T09",
     "Minha aplicação não conecta ao Azure SQL e aparece o erro 40615 dizendo que o IP não tem permissão de acesso ao servidor.",
     "O IP do cliente não está autorizado no firewall do servidor. A solução é criar uma regra de IP ou habilitar a opção que permite o acesso "
     "de serviços do Azure ao servidor.",
     "A", "sql-server"),
    ("AZ-T12",
     "O App Service não consegue baixar a imagem do Azure Container Registry. Como autenticar sem usar usuário e senha?",
     "Usar identidade gerenciada com a função AcrPull. Localmente, o Docker é autenticado com `az acr login --name <registro>`.",
     "A", "docker"),
    ("AZ-R01",
     "Qual padrão de nome devo usar para o Key Vault do serviço de pedidos em produção?",
     "O padrão é `nmb-<ambiente>-<servico>-<tipo>`, portanto `nmb-prd-pedidos-kv`. Nomes fora do padrão são bloqueados pela Azure Policy `nimbus-naming`.",
     "B", None),
    ("AZ-R02",
     "Posso criar o App Service do meu projeto na região West Europe?",
     "Não. Somente Brazil South (principal) e East US 2 (recuperação de desastres) são permitidas; as demais são bloqueadas por policy.",
     "B", None),
    ("AZ-R03",
     "Um recurso que criei no Azure foi desligado sozinho três dias depois. Por quê?",
     "Provavelmente faltava a tag `centro-de-custo` (formato CC-0000). Recursos sem ela são desligados após 72 horas pela automação "
     "Nimbus-Guard. As tags obrigatórias são `centro-de-custo`, `responsavel` e `ambiente`.",
     "A", None),
    ("AZ-R04",
     "Recebi um alerta de orçamento do grupo de recursos de homologação. Qual é o orçamento e em que percentuais há alerta?",
     "O orçamento mensal padrão é de R$ 1.500, com alertas em 70% e 90% do valor.",
     "B", None),
    ("AZ-R05",
     "Preciso ser Owner da assinatura de produção por uma semana para fazer uma migração.",
     "Ninguém recebe Owner de forma permanente. O acesso é por elevação just-in-time, com duração máxima de 4 horas, aprovada pelo gestor "
     "e registrada no ticket.",
     "M", None),
    ("AZ-R07",
     "Quantas réplicas mínimas devo configurar no Container App em produção e em homologação?",
     "Em homologação `minReplicas: 0`; em produção o mínimo é de 2 réplicas em zonas de disponibilidade distintas, com máximo padrão de 10 réplicas.",
     "M", None),
    ("AZ-R08",
     "Posso publicar direto no App Service de produção do meu site Next.js, ou preciso de slot?",
     "Todo App Service de produção deve ter o slot `staging`. O deploy direto em produção é proibido, e o swap só pode ocorrer depois de o "
     "smoke test automático ficar verde.",
     "A", "nextjs"),
    ("AZ-R09",
     "Libero o IP da minha máquina no firewall do Azure SQL de produção para o serviço conseguir conectar?",
     "Não. O acesso ao Azure SQL é por Private Endpoint; em produção regras de firewall por IP público são proibidas e a opção de permitir "
     "serviços do Azure fica desabilitada.",
     "A", "sql-server"),

    # SQL Server (16)
    ("SQ-T01",
     "Subi o SQL Server em um contêiner e ele cai logo depois de iniciar. Defini MSSQL_SA_PASSWORD=123456.",
     "A senha não atende à política: deve ter ao menos 8 caracteres e combinar três das quatro categorias (maiúsculas, minúsculas, dígitos e "
     "símbolos). Uma senha fraca faz o contêiner encerrar logo após iniciar; também é necessário `ACCEPT_EULA=Y`.",
     "A", "docker"),
    ("SQ-T02",
     "Restaurei o backup em outro servidor e o usuário da aplicação não consegue entrar, mesmo existindo no banco.",
     "É um usuário órfão (orphaned user): o SID do login é diferente na nova instância. A correção é `ALTER USER <usuario> WITH LOGIN = <login>`.",
     "M", None),
    ("SQ-T04",
     "Minha listagem paginada com OFFSET/FETCH repete registros entre páginas e dá erro de sintaxe quando tiro o ORDER BY.",
     "OFFSET e FETCH exigem `ORDER BY`. Para evitar registros repetidos entre páginas, o ordenamento deve incluir uma coluna única como "
     "critério de desempate.",
     "M", None),
    ("SQ-T05",
     "Tentei criar um segundo índice clusterizado na tabela de pedidos e deu erro.",
     "Cada tabela pode ter apenas um índice clusterizado, e por padrão a chave primária já cria um. Podem existir vários índices não clusterizados (nonclustered).",
     "B", None),
    ("SQ-T08",
     "Minhas consultas de leitura ficam travadas esperando um UPDATE longo de outra sessão. Como evito isso sem usar NOLOCK?",
     "Ativar `ALTER DATABASE <banco> SET READ_COMMITTED_SNAPSHOT ON`, que passa a usar versões de linha e faz os leitores deixarem de bloquear os escritores.",
     "A", None),
    ("SQ-T09",
     "No meu serviço Spring Boot uma transação falhou com o erro 1205 do banco. O que é isso e como reduzo?",
     "É um deadlock: o SQL Server escolhe uma vítima e reverte sua transação. A aplicação deve repetir a transação; para reduzir, acessar os objetos "
     "sempre na mesma ordem e manter as transações curtas.",
     "A", "spring-boot"),
    ("SQ-T10",
     "O sistema está lento e suspeito de bloqueio. Como descubro quem está bloqueando quem?",
     "Consultar `sys.dm_exec_requests`, cuja coluna `blocking_session_id` indica a sessão bloqueadora, ou usar `sp_who2`. O comando `KILL <spid>` encerra uma sessão.",
     "M", None),
    ("SQ-T11",
     "O disco do servidor encheu por causa do arquivo .ldf e a aplicação recebeu o erro 9002.",
     "No modelo de recuperação FULL o log só é truncado após um backup de log; sem esses backups o arquivo `.ldf` cresce até encher o disco e ocorre o erro 9002.",
     "A", None),
    ("SQ-R02",
     "Criei um banco novo e a ordenação de texto ficou diferente da dos outros bancos da Nimbus. Qual collation devo usar?",
     "A collation padrão da Nimbus é `Latin1_General_100_CI_AI`, diferente do padrão da instalação; a criação deve informar `COLLATE` de forma explícita.",
     "B", None),
    ("SQ-R03",
     "Posso usar o usuário sa na connection string da minha API Next.js em homologação?",
     "Não. Aplicações nunca usam o login `sa`; cada serviço tem um login `svc_<servico>` com as funções `db_datareader` e `db_datawriter`. "
     "A função `db_owner` só é concedida com aprovação do time de DBA (DataGov).",
     "M", "nextjs"),
    ("SQ-R04",
     "Qual configuração de isolamento os bancos transacionais precisam ter para atender o padrão da Nimbus?",
     "Devem ter `READ_COMMITTED_SNAPSHOT ON`, verificado semanalmente pelo job `nmb_audit_rcsi`.",
     "B", None),
    ("SQ-R05",
     "Com que frequência são feitos os backups em produção e por quanto tempo ficam retidos?",
     "FULL diário às 02h, diferencial a cada 6 horas e backup de log a cada 15 minutos, com retenção de 35 dias.",
     "A", None),
    ("SQ-R07",
     "Quantas vezes meu serviço Spring Boot pode repetir uma transação que foi vítima de deadlock?",
     "No máximo 2 vezes, esperando 100 ms entre as tentativas. A terceira falha abre automaticamente um incidente de nível P3.",
     "M", "spring-boot"),
    ("SQ-R08",
     "Qual configuração de crescimento do arquivo de log devo usar nos bancos da Nimbus?",
     "Crescimento fixo de 512 MB, e não em porcentagem, com limite de 50 GB por banco; é gerado alerta quando 80% do limite é atingido.",
     "B", None),
    ("SQ-R09",
     "Posso restaurar um backup de produção no meu SQL Server de desenvolvimento para reproduzir um bug?",
     "Não. É proibido restaurar cópias de produção em desenvolvimento; os dados de desenvolvimento devem ser anonimizados com o script `nmb_anonimiza.sql`.",
     "A", None),
    ("SQ-R10",
     "Qual é a regra para manutenção de índices fragmentados e em que horário ela ocorre?",
     "Fragmentação entre 10% e 30% é reorganizada e acima de 30% é reconstruída, aos domingos das 01h às 04h.",
     "B", None),

    # Next.js (16)
    ("NX-T01",
     "Criei app/dashboard/page.tsx, mas já existe pages/dashboard.tsx e o build reclama de conflito.",
     "App Router e Pages Router podem coexistir, mas se ambos definem a mesma rota há conflito no build. É preciso manter a rota em apenas um deles.",
     "M", None),
    ("NX-T02",
     "Usei useState em um componente e o build deu erro dizendo que só funciona em Client Component.",
     "No App Router os componentes são Server Components por padrão. Para usar `useState` o arquivo deve começar com a diretiva `'use client'`.",
     "A", None),
    ("NX-T04",
     "Defini NEXT_PUBLIC_API_URL como variável de ambiente do contêiner Docker em produção, mas o navegador continua usando o valor antigo.",
     "Variáveis com prefixo `NEXT_PUBLIC_` são incorporadas ao bundle no momento do build. Alterá-las depois, sem refazer o build, não muda o código do cliente.",
     "A", "docker"),
    ("NX-T05",
     "Preciso criar um endpoint POST /api/contato dentro do próprio projeto Next.js. Como faço no App Router?",
     "Criar um arquivo `route.ts` dentro de `app/api/<nome>/` (no caso, a pasta contato) exportando a função `POST`, que usa os objetos padrão Request e Response.",
     "B", None),
    ("NX-T07",
     "O next/image quebra com erro de hostname não configurado ao carregar a foto de um bucket externo.",
     "Autorizar o domínio em `images.remotePatterns` no `next.config.js`; sem isso o Next.js lança erro informando que o hostname não está configurado.",
     "B", None),
    ("NX-T08",
     "Aparece erro de hidratação no console e a data exibida é diferente entre servidor e cliente.",
     "O HTML do servidor difere do primeiro render do cliente, por exemplo por uso de `Date.now()`, `Math.random()` ou `window`. Mover esse código para "
     "`useEffect` ou, em casos pontuais, usar `suppressHydrationWarning`.",
     "M", None),
    ("NX-T09",
     "Estou com erro de CORS ao chamar do navegador a API Spring Boot do backend. Dá para resolver no próprio Next.js?",
     "Sim, com `rewrites()` em `next.config.js`, que encaminha requisições de um caminho do Next.js para outro destino e funciona como proxy, evitando o CORS.",
     "M", "spring-boot"),
    ("NX-T11",
     "Quero gerar uma imagem Docker pequena do meu projeto Next.js. Qual configuração do Next.js ajuda e o que preciso copiar?",
     "Usar `output: 'standalone'` no `next.config.js`, que gera `.next/standalone` executado com `node server.js`. As pastas `.next/static` e `public` precisam ser copiadas manualmente.",
     "M", "docker"),
    ("NX-R01",
     "O pipeline barrou meu build com o código NIM-FE-03 quando rodei npm install.",
     "A Nimbus usa Node 20 LTS e pnpm; o lockfile oficial é `pnpm-lock.yaml` e o `npm install` é bloqueado no pipeline com o código `NIM-FE-03`.",
     "B", None),
    ("NX-R02",
     "Posso colocar a chave de API do provedor de e-mail em NEXT_PUBLIC_EMAIL_KEY?",
     "Não. É proibido colocar segredos em variáveis `NEXT_PUBLIC_*`, e variáveis públicas devem usar o prefixo `NEXT_PUBLIC_NMB_`; o linter `nimbus-env-lint` reprova o código.",
     "A", None),
    ("NX-R03",
     "Minha aplicação Next.js abre na plataforma, mas os arquivos estáticos retornam 404 no domínio da Nimbus.",
     "Os front-ends são servidos sob `/app/<servico>`, e o `next.config.js` deve definir `basePath: '/app/<servico>'`.",
     "M", None),
    ("NX-R04",
     "Posso chamar direto do navegador a API interna de clientes da Nimbus?",
     "Não. O front-end passa por route handlers que funcionam como BFF em `app/api/bff/`, os quais acessam o gateway Nimbus-GW.",
     "M", None),
    ("NX-R05",
     "Qual estratégia de cache devo usar para uma página autenticada e para uma página pública de conteúdo na Nimbus?",
     "Páginas autenticadas usam `dynamic = 'force-dynamic'`; páginas públicas de conteúdo revalidam a cada 300 segundos com `revalidate: 300`.",
     "M", None),
    ("NX-R06",
     "A imagem do avatar vem de images.exemplo.com e o revisor reprovou o código. Quais domínios são permitidos?",
     "Apenas `cdn.nimbus.local` e `assets.nimbus.local` em `images.remotePatterns`.",
     "B", None),
    ("NX-R07",
     "Que variáveis e porta devo usar ao empacotar o Next.js em contêiner na Nimbus, e qual rota de saúde?",
     "Usar `output: 'standalone'` com `PORT=3000` e `HOSTNAME=0.0.0.0`; o healthcheck consulta a rota `/api/health`.",
     "M", "docker"),
    ("NX-R08",
     "O pipeline falhou com o código NIM-FE-09 depois que adicionei uma biblioteca de gráficos.",
     "O JavaScript inicial por rota passou de 200 KB comprimidos, que é o limite; acima disso o pipeline falha com `NIM-FE-09`.",
     "B", None),
]

# chamados sem solução: (categoria, pergunta, prioridade, tipo "plataforma" ou "geral")
UNANSWERABLE = [
    ("spring-boot", "Qual é o tamanho máximo de corpo de requisição aceito pelos serviços Spring Boot da Nimbus?", "B", "plataforma"),
    ("spring-boot", "Como configuro o Spring Security como OAuth2 Resource Server para validar tokens JWT?", "M", "geral"),
    ("spring-boot", "Qual é a política da Nimbus para escolher entre Spring MVC e WebFlux em serviços novos?", "B", "plataforma"),
    ("spring-boot", "Como habilito cache distribuído com Redis em um serviço Spring Boot?", "M", "geral"),
    ("docker", "Qual é o SLA do time de plataforma da Nimbus para restaurar o registro interno de imagens em caso de indisponibilidade?", "A", "plataforma"),
    ("docker", "Como configuro um cluster Docker Swarm com 3 managers e secrets?", "B", "geral"),
    ("docker", "Como habilito BuildKit com cache remoto de camadas em um registry?", "M", "geral"),
    ("docker", "Qual é o processo da Nimbus para solicitar exceção à regra de executar contêineres como usuário não root?", "M", "plataforma"),
    ("azure", "Qual é o procedimento da Nimbus para solicitar aumento de cota de vCPU na região Brazil South?", "M", "plataforma"),
    ("azure", "Como configuro o Azure Front Door com WAF para proteger um App Service?", "M", "geral"),
    ("azure", "Qual é o RTO contratado para os serviços na região East US 2?", "A", "plataforma"),
    ("azure", "Como crio um cluster AKS com node pools do tipo spot?", "B", "geral"),
    ("sql-server", "Como configuro Always On Availability Groups entre duas instâncias do SQL Server?", "B", "geral"),
    ("sql-server", "Qual é o prazo de atendimento do time de DBA da Nimbus para solicitações de criação de novos bancos?", "M", "plataforma"),
    ("sql-server", "Como configuro criptografia TDE e faço a rotação do certificado?", "M", "geral"),
    ("sql-server", "A Nimbus permite usar tabelas temporais (system-versioned) em bancos de produção?", "B", "plataforma"),
    ("nextjs", "Como configuro autenticação com Auth.js usando login corporativo em uma aplicação Next.js?", "M", "geral"),
    ("nextjs", "Qual é o procedimento da Nimbus para testes end-to-end de aplicações Next.js?", "M", "plataforma"),
    ("nextjs", "Como uso Server Actions com formulários e validação no Next.js?", "B", "geral"),
    ("nextjs", "Qual é a política da Nimbus para uso de bibliotecas de componentes de interface (design system)?", "B", "plataforma"),
]

# exemplos few-shot da triagem (fora dos 100 chamados)
FEWSHOT = [
    ("O meu @RestController retorna 404 para uma rota que declarei com @GetMapping.", "spring-boot"),
    ("Como executo apenas os testes de integração do projeto com o Maven?", "spring-boot"),
    ("O docker run diz que o nome do contêiner já está em uso. Como resolvo?", "docker"),
    ("Como listo as imagens locais que mais ocupam espaço em disco?", "docker"),
    ("Como vejo o custo acumulado do mês corrente por grupo de recursos?", "azure"),
    ("O az login abre o navegador, mas a CLI continua dizendo que não estou autenticado.", "azure"),
    ("Como descubro a versão exata do SQL Server instalada na instância?", "sql-server"),
    ("Como altero o tipo de uma coluna de INT para BIGINT em uma tabela com muitos registros?", "sql-server"),
    ("A navegação entre páginas recarrega o site inteiro em vez de ser instantânea.", "nextjs"),
    ("Como adiciono uma fonte do Google ao projeto Next.js sem prejudicar o carregamento?", "nextjs"),
]
