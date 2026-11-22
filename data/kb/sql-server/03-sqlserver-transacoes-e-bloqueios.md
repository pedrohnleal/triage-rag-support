# SQL Server: transações e bloqueios

## Níveis de isolamento e READ_COMMITTED_SNAPSHOT no SQL Server

O nível de isolamento padrão do SQL Server é READ COMMITTED, em que leituras ficam bloqueadas por escritas ainda não confirmadas. Com `ALTER DATABASE <banco> SET READ_COMMITTED_SNAPSHOT ON`, o SQL Server passa a usar versões de linha e os leitores deixam de bloquear os escritores.

## Deadlock no SQL Server

Um deadlock no SQL Server gera o erro 1205: o servidor escolhe uma vítima e reverte sua transação. A aplicação deve repetir a transação. Para reduzir a ocorrência, acessa-se os objetos sempre na mesma ordem e mantêm-se as transações curtas.

## Investigação de bloqueios no SQL Server

Para identificar bloqueios no SQL Server, consulta-se `sys.dm_exec_requests`, cuja coluna `blocking_session_id` indica a sessão bloqueadora, ou usa-se `sp_who2`. O comando `KILL <spid>` encerra uma sessão.
