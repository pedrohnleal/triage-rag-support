# Runbook Nimbus: aplicações Next.js

Documento interno SIMULADO da plataforma fictícia Nimbus, criado para o experimento. As regras abaixo não existem fora desta base de conhecimento.

## Node e gerenciador de pacotes das aplicações Next.js da Nimbus

As aplicações Next.js da Nimbus usam Node 20 LTS e pnpm. O lockfile oficial é `pnpm-lock.yaml`, e o comando `npm install` é bloqueado no pipeline com o código `NIM-FE-03`.

## Variáveis públicas nas aplicações Next.js da Nimbus

Variáveis públicas devem usar o prefixo `NEXT_PUBLIC_NMB_`. É proibido colocar segredos em variáveis `NEXT_PUBLIC_*`, e o linter `nimbus-env-lint` reprova o código que fizer isso.

## Base path das aplicações Next.js da Nimbus

Os front-ends são servidos sob o caminho `/app/<servico>`, e o `next.config.js` deve definir `basePath: '/app/<servico>'`.

## Chamadas a APIs nas aplicações Next.js da Nimbus

O front-end não chama serviços internos diretamente do navegador. As chamadas passam por route handlers que funcionam como BFF em `app/api/bff/`, os quais acessam o gateway de APIs Nimbus-GW.

## Estratégia de cache nas aplicações Next.js da Nimbus

Páginas autenticadas devem usar `dynamic = 'force-dynamic'`. Páginas públicas de conteúdo revalidam a cada 300 segundos, com `revalidate: 300`.

## Domínios de imagens autorizados nas aplicações Next.js da Nimbus

Os únicos domínios de imagem autorizados em `images.remotePatterns` são `cdn.nimbus.local` e `assets.nimbus.local`. Outros domínios são reprovados na revisão de código.

## Empacotamento em contêiner das aplicações Next.js da Nimbus

As imagens Next.js usam `output: 'standalone'`, com `PORT=3000` e `HOSTNAME=0.0.0.0`. O healthcheck consulta a rota `/api/health`.

## Limite de bundle das aplicações Next.js da Nimbus

O JavaScript inicial por rota deve ter no máximo 200 KB comprimidos. Acima disso o pipeline falha com o código `NIM-FE-09`.

## Internacionalização nas aplicações Next.js da Nimbus

O idioma padrão é `pt-BR` e o secundário é `en-US`. Os textos ficam em arquivos `messages/<locale>.json`, e textos fixos no código são reprovados na revisão.

## Cobertura mínima de testes nas aplicações Next.js da Nimbus

A cobertura mínima de testes é de 70% das linhas. Abaixo disso o merge é bloqueado.
