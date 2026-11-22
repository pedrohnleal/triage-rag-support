# Next.js: roteamento e componentes

## App Router e Pages Router no Next.js

O Next.js possui dois sistemas de roteamento: o App Router (diretório `app/`, com layouts e Server Components) e o Pages Router (diretório `pages/`). Eles podem coexistir, mas se ambos definirem a mesma rota ocorre conflito no build; é preciso manter a rota em apenas um deles.

## Server Components e Client Components no Next.js

No App Router do Next.js, os componentes são Server Components por padrão. Para usar `useState`, `useEffect` ou manipuladores como `onClick`, o arquivo deve começar com a diretiva `'use client'`. Usar um hook de estado em um Server Component gera erro de build.

## Rotas dinâmicas no Next.js

No Next.js, uma pasta com nome entre colchetes, como `[id]`, cria uma rota dinâmica cujo valor chega em `params`. O formato `[...slug]` captura vários segmentos de caminho.
