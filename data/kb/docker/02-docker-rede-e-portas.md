# Docker: rede e portas

## Publicação de portas no Docker

No Docker, a instrução `EXPOSE` apenas documenta a porta. Para acessar o contêiner a partir do host é preciso publicar a porta com `-p <host>:<contêiner>` no `docker run` ou com `ports:` no Compose, por exemplo `-p 8081:8080`.

## Comunicação entre contêineres no Docker Compose

No Docker Compose, os serviços entram em uma rede padrão e se resolvem pelo nome do serviço como hostname. Dentro de um contêiner, `localhost` aponta para o próprio contêiner, não para o host nem para outros serviços. Por isso uma aplicação deve usar o nome do serviço do banco, por exemplo `banco:5432`.

## Acesso ao host a partir de um contêiner Docker

No Docker Desktop, o nome `host.docker.internal` resolve para o host. No Linux é necessário adicionar `--add-host=host.docker.internal:host-gateway` ao `docker run` para obter o mesmo efeito.
