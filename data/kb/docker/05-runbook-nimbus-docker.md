# Runbook Nimbus: contêineres Docker

Documento interno SIMULADO da plataforma fictícia Nimbus, criado para o experimento. As regras abaixo não existem fora desta base de conhecimento.

## Imagens base aprovadas na Nimbus

Somente imagens base do registro interno `registro.nimbus.local/base/` são aceitas: `jre-21`, `node-20` e `debian-slim`. Imagens obtidas diretamente do Docker Hub são bloqueadas pelo proxy do registro e o build falha ao baixá-las.

## Usuário não root nos contêineres da Nimbus

Todo Dockerfile da Nimbus deve declarar `USER 10001`. Contêineres que executam como root são reprovados na varredura do pipeline com o código `NIM-SEC-12`.

## Limites de recursos padrão dos contêineres da Nimbus

O padrão Nimbus por contêiner é de 512 MB de memória e 0,5 vCPU. Serviços que precisem de mais recursos exigem parecer do time de capacidade. Uso acima de 80% da memória por 5 minutos gera alerta.

## Labels obrigatórias nas imagens da Nimbus

Toda imagem deve ter as labels `nimbus.owner` (e-mail do time responsável), `nimbus.service` e `nimbus.tier`, cujos valores possíveis são `gold`, `silver` e `bronze`. Sem `nimbus.owner` a imagem não é publicada.

## Tamanho máximo das imagens da Nimbus

O tamanho máximo de uma imagem é de 350 MB comprimidos. Acima disso o build falha com o código `NIM-IMG-07`; a recomendação é usar build em múltiplos estágios.

## Healthcheck padrão dos contêineres da Nimbus

Todo contêiner de serviço deve declarar `HEALTHCHECK` com `--interval=20s --timeout=3s --retries=3`. O comando de verificação deve retornar código 0 somente quando o serviço estiver pronto para receber tráfego.

## Política de reinício na Nimbus

No ambiente de homologação, os serviços usam `restart: unless-stopped`. A política `always` é proibida porque mascara falhas de inicialização em laço.

## Volumes e dados persistentes na Nimbus

Dados persistentes só podem ficar em volumes nomeados com prefixo `nmb_`. Bind mounts são proibidos fora do ambiente de desenvolvimento, e o comando `docker compose down -v` é bloqueado em homologação pelo wrapper `nimbus-compose`.

## Limpeza automática de imagens do registro Nimbus

Imagens sem uso há 30 dias são removidas automaticamente do registro interno, exceto as que possuem tag iniciada por `release-`.

## Faixa de portas publicadas na Nimbus

As portas publicadas no host de homologação devem estar na faixa de 18000 a 18999. Portas fora dessa faixa são bloqueadas pela regra de firewall.
