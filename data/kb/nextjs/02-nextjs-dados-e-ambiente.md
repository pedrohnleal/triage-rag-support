# Next.js: dados e ambiente

## Variáveis de ambiente públicas no Next.js

No Next.js, variáveis definidas em `.env.local` ficam disponíveis apenas no servidor. Para chegar ao navegador, o nome precisa começar com `NEXT_PUBLIC_`, e o valor é incorporado ao bundle no momento do build. Alterar a variável depois, sem refazer o build, não muda o código do cliente.

## Route Handlers no Next.js

No App Router do Next.js, um arquivo `route.ts` dentro de `app/api/<nome>/` define um endpoint e exporta funções nomeadas por método HTTP, como `GET` e `POST`, usando os objetos padrão Request e Response.

## Cache de fetch no Next.js

O comportamento de cache padrão do `fetch` no servidor do Next.js mudou entre versões maiores. Para dados sempre atualizados usa-se `cache: 'no-store'` ou `export const dynamic = 'force-dynamic'`; para revalidar por tempo usa-se `next: { revalidate: 60 }`.
