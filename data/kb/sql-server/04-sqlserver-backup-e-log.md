# SQL Server: backup e log de transações

## Modelos de recuperação e log cheio no SQL Server

Os modelos de recuperação do SQL Server são FULL, BULK_LOGGED e SIMPLE. No modelo FULL, o log de transações só é truncado após um backup de log; sem backups de log, o arquivo `.ldf` cresce até encher o disco e ocorre o erro 9002 (log de transações cheio).

## Backup e restauração no SQL Server

O backup é feito com `BACKUP DATABASE <banco> TO DISK = '<caminho>'`. Na restauração, `RESTORE DATABASE ... WITH MOVE` relocaliza arquivos quando os caminhos diferem; `WITH RECOVERY` finaliza a restauração e `WITH NORECOVERY` permite aplicar backups adicionais.
