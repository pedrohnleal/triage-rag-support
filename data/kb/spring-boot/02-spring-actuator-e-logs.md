# Spring Boot: Actuator e logs

## Exposição de endpoints do Spring Boot Actuator

No Spring Boot Actuator, nas versões recentes, apenas o endpoint `health` é exposto por HTTP por padrão. Para expor outros endpoints usa-se `management.endpoints.web.exposure.include` (por exemplo `health,info,metrics`). O caminho base padrão é `/actuator`. Para que o `health` mostre detalhes dos componentes, define-se `management.endpoint.health.show-details`.

## Porta de gerenciamento separada no Spring Boot

A propriedade `management.server.port` faz o Spring Boot Actuator atender os endpoints de gerenciamento em uma porta diferente da porta da aplicação, o que permite restringir o acesso a eles por regras de rede.

## Níveis de log no Spring Boot

O nível de log do Spring Boot é configurado por `logging.level.<pacote>`, por exemplo `logging.level.root=WARN` e `logging.level.org.springframework.web=DEBUG`. Os níveis são TRACE, DEBUG, INFO, WARN, ERROR, FATAL e OFF, e o nível padrão é INFO.
