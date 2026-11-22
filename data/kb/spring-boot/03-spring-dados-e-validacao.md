# Spring Boot: dados, transações e validação

## Pool de conexões HikariCP no Spring Boot

O Spring Boot usa o HikariCP como pool de conexões padrão. O tamanho máximo padrão é de 10 conexões (`spring.datasource.hikari.maximum-pool-size`) e o tempo máximo de espera por uma conexão é de 30000 ms (`spring.datasource.hikari.connection-timeout`). Quando o pool se esgota, as requisições aguardam até o timeout e então falham com erro de tempo esgotado ao obter conexão.

## Rollback com @Transactional no Spring

Por padrão, `@Transactional` faz rollback apenas para exceções não verificadas (`RuntimeException` e `Error`). Exceções verificadas (checked) não provocam rollback, a menos que se use o atributo `rollbackFor`. Chamar um método transacional a partir da mesma classe (auto-invocação) não passa pelo proxy e a transação não é aplicada.

## Validação de entrada no Spring Boot

Para validar o corpo de uma requisição no Spring Boot, inclui-se a dependência `spring-boot-starter-validation`, anota-se o parâmetro do controller com `@Valid` e os campos com anotações como `@NotBlank` e `@Size`. Uma falha de validação gera `MethodArgumentNotValidException` e, por padrão, resposta HTTP 400.
