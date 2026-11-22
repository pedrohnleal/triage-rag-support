# Next.js: imagens, erros e proxy

## Imagens remotas com next/image no Next.js

Imagens remotas usadas com `next/image` precisam ser autorizadas em `images.remotePatterns` no `next.config.js`. Sem isso, o Next.js lança erro informando que o hostname não está configurado.

## Erros de hidratação no Next.js

Erros de hidratação ocorrem quando o HTML gerado no servidor difere do primeiro render no cliente, por exemplo ao usar `Date.now()`, `Math.random()` ou `window` durante a renderização. A solução é mover esse código para `useEffect` ou, em casos pontuais, usar `suppressHydrationWarning`.

## Rewrites no Next.js para evitar CORS

A função `rewrites()` em `next.config.js` encaminha requisições de um caminho do Next.js, como `/api/externo/:path*`, para outro destino. Isso serve de proxy e evita problemas de CORS quando o navegador chamaria uma API em outra origem.
