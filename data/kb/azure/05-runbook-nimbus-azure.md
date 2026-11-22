# Runbook Nimbus: recursos no Azure

Documento interno SIMULADO da plataforma fictícia Nimbus, criado para o experimento. As regras abaixo não existem fora desta base de conhecimento.

## Convenção de nomes de recursos Azure na Nimbus

Os recursos Azure seguem o padrão `nmb-<ambiente>-<servico>-<tipo>`, por exemplo `nmb-prd-pedidos-kv`. Os ambientes válidos são `dev`, `hml` e `prd`. Nomes fora do padrão são bloqueados pela Azure Policy `nimbus-naming`.

## Regiões permitidas no Azure da Nimbus

Somente as regiões Brazil South (principal) e East US 2 (recuperação de desastres) são permitidas. Qualquer outra região é bloqueada por policy.

## Tags obrigatórias nos recursos Azure da Nimbus

Todo recurso deve ter as tags `centro-de-custo` (formato CC-0000, com quatro dígitos), `responsavel` e `ambiente`. Recursos sem a tag `centro-de-custo` são desligados após 72 horas pela automação Nimbus-Guard.

## Orçamentos dos grupos de recursos de homologação da Nimbus

Cada grupo de recursos de homologação tem orçamento mensal padrão de R$ 1.500, com alertas em 70% e 90% do valor. Os orçamentos de produção são definidos conforme o tier do serviço.

## Acesso privilegiado no Azure da Nimbus

Ninguém recebe a função Owner de forma permanente. O acesso privilegiado é obtido por elevação just-in-time, com duração máxima de 4 horas, aprovada pelo gestor e registrada no ticket.

## Rotação de segredos no Key Vault da Nimbus

Todo segredo no Key Vault do serviço (`nmb-<ambiente>-<servico>-kv`) deve ser rotacionado a cada 90 dias. O time responsável recebe alerta aos 75 dias.

## Escala dos Container Apps na Nimbus

Em homologação, os Container Apps usam `minReplicas: 0`. Em produção, o mínimo é de 2 réplicas em zonas de disponibilidade distintas, e o máximo padrão é de 10 réplicas.

## Slots de implantação obrigatórios no App Service da Nimbus

Todo App Service de produção deve ter o slot `staging`. O deploy direto no slot de produção é proibido, e a troca (swap) só pode ocorrer depois de o smoke test automático ficar verde.

## Acesso ao Azure SQL na Nimbus

O acesso ao Azure SQL ocorre por Private Endpoint. Em produção, regras de firewall por IP público são proibidas e a opção de permitir serviços do Azure fica desabilitada.

## Telemetria no Application Insights da Nimbus

Todo serviço publicado envia telemetria ao Application Insights do ambiente (`nmb-<ambiente>-ai`). A amostragem é de 20% em produção e 100% em homologação, e a retenção é de 90 dias em produção e 30 dias em homologação.
