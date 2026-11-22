# Azure: operação, registro de contêineres e custos

## Application Insights e Azure Monitor

O Application Insights, parte do Azure Monitor, coleta telemetria de requisições, dependências, exceções e traces. A aplicação se conecta por uma connection string, e os dados podem ser consultados com KQL em um workspace do Log Analytics.

## Tags e orçamentos no Azure Cost Management

As tags do Azure são pares nome-valor usados no Cost Management para agrupar custos. Orçamentos geram alertas quando percentuais definidos são atingidos, mas não interrompem recursos automaticamente.

## Azure Container Registry e autenticação de imagens

No Azure Container Registry, `az acr login --name <registro>` autentica o Docker local, e as imagens seguem o formato `<registro>.azurecr.io/<repositório>:<tag>`. Para que App Service ou Container Apps baixem imagens sem usuário e senha, usa-se identidade gerenciada com a função AcrPull.
