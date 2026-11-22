# SQL Server: consultas e índices

## Paginação com OFFSET e FETCH no SQL Server

A paginação no SQL Server usa `ORDER BY <coluna> OFFSET n ROWS FETCH NEXT m ROWS ONLY`. As cláusulas OFFSET e FETCH exigem `ORDER BY`; sem ele a ordem não é garantida. Para evitar registros repetidos entre páginas, o ordenamento deve incluir uma coluna única como critério de desempate.

## Índices clusterizados e não clusterizados no SQL Server

Cada tabela do SQL Server pode ter apenas um índice clusterizado (clustered), que define a ordem física das linhas; por padrão, a chave primária cria um. Podem existir vários índices não clusterizados (nonclustered), que aceitam colunas adicionais com `INCLUDE`.

## Plano de execução e estatísticas no SQL Server

No SQL Server, `SET STATISTICS IO ON` e o plano de execução real ajudam a diagnosticar consultas lentas. Operações Table Scan ou Index Scan em tabelas grandes sugerem falta de índice. O Query Store registra o histórico de planos de execução.

## Parameter sniffing no SQL Server

O parameter sniffing ocorre quando o plano é compilado com os valores do primeiro parâmetro recebido e fica inadequado para outros valores. Mitigações incluem `OPTION (RECOMPILE)`, `OPTIMIZE FOR` e o uso de plan forcing no Query Store.
