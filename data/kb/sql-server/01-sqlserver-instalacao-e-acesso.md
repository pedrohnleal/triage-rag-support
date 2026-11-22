# SQL Server: instalação e acesso

## SQL Server em contêiner Docker

A imagem `mcr.microsoft.com/mssql/server` exige as variáveis `ACCEPT_EULA=Y` e `MSSQL_SA_PASSWORD` e usa a porta 1433. A senha do usuário SA deve ter ao menos 8 caracteres e combinar três das quatro categorias (maiúsculas, minúsculas, dígitos e símbolos); uma senha fraca faz o contêiner encerrar logo após iniciar.

## Logins, usuários e usuários órfãos no SQL Server

No SQL Server, o login existe no nível do servidor e o user no nível do banco. Ao restaurar um banco em outra instância, o usuário pode ficar órfão (orphaned user), porque o SID do login é diferente. A correção é feita com `ALTER USER <usuario> WITH LOGIN = <login>`.

## Collation no SQL Server

A collation define a comparação e a ordenação de textos no SQL Server; em `SQL_Latin1_General_CP1_CI_AS`, CI significa case-insensitive e AS, accent-sensitive. Conflito de collation entre colunas ou bancos gera erro de conflito de collation, resolvido com a cláusula `COLLATE`.
