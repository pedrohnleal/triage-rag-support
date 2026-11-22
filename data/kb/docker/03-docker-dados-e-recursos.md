# Docker: dados e recursos

## Volumes nomeados e bind mounts no Docker

No Docker, um volume nomeado é gerenciado pelo Docker e persiste depois que o contêiner é removido, enquanto um bind mount mapeia uma pasta do host. O comando `docker compose down` preserva os volumes nomeados; `docker compose down -v` remove os volumes nomeados e, com eles, os dados.

## Limites de memória e código de saída 137 no Docker

O limite de memória de um contêiner é definido com `--memory` (ou `mem_limit` no Compose). Ao exceder o limite, o kernel encerra o processo. O código de saída 137 indica SIGKILL, comum quando o kernel encerra o processo por falta de memória; a confirmação é feita pelo campo `OOMKilled` em `docker inspect`.

## Políticas de reinício no Docker

As políticas de reinício do Docker são `no` (padrão), `on-failure[:max]`, `always` e `unless-stopped`. A política `unless-stopped` reinicia o contêiner sempre, exceto quando ele foi parado manualmente.
