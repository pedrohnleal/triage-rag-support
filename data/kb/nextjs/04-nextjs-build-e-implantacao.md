# Next.js: build e implantação

## Comandos next dev, next build e next start

O comando `next dev` inicia o modo de desenvolvimento, `next build` gera o build de produção e `next start` serve esse build. Executar `next start` sem build prévio falha pedindo a execução de `next build`.

## Saída standalone do Next.js

Com `output: 'standalone'` no `next.config.js`, o Next.js gera `.next/standalone` com um servidor mínimo e apenas as dependências necessárias, executado com `node server.js`. As pastas `.next/static` e `public` precisam ser copiadas manualmente para o destino.

## Porta do Next.js

A porta do Next.js é alterada com `next dev -p 4000` e `next start -p 4000`, ou pela variável de ambiente `PORT`.
