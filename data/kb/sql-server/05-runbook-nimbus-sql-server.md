# Runbook Nimbus: bancos SQL Server

Documento interno SIMULADO da plataforma fictícia Nimbus, criado para o experimento. As regras abaixo não existem fora desta base de conhecimento.

## Padrão de nomes de bancos SQL Server na Nimbus

Os bancos seguem o padrão `nmb_<servico>_<ambiente>`, sem hifens, por exemplo `nmb_pedidos_prd`.

## Collation padrão dos bancos da Nimbus

Todos os bancos novos da Nimbus usam a collation `Latin1_General_100_CI_AI`, que é diferente do padrão da instalação. Por isso a criação deve informar `COLLATE` de forma explícita.

## Contas de aplicação nos bancos da Nimbus

Aplicações nunca usam o login `sa`. Cada serviço tem um login `svc_<servico>` com as funções `db_datareader` e `db_datawriter`. A função `db_owner` só é concedida com aprovação do time de DBA da Nimbus (DataGov).

## Isolamento obrigatório nos bancos transacionais da Nimbus

Os bancos transacionais devem ter `READ_COMMITTED_SNAPSHOT ON`. A configuração é verificada semanalmente pelo job `nmb_audit_rcsi`.

## Política de backup dos bancos de produção da Nimbus

Em produção, o backup FULL é diário às 02h, o diferencial ocorre a cada 6 horas e o backup de log a cada 15 minutos. A retenção é de 35 dias. Em homologação, o backup FULL é semanal, aos domingos.

## Timeouts de comando nos bancos da Nimbus

Consultas das aplicações têm timeout de 30 segundos. Relatórios em lote usam timeout de 300 segundos e devem executar na réplica de leitura `nmb-ro`.

## Repetição de transações vítimas de deadlock na Nimbus

O serviço deve repetir no máximo 2 vezes a transação escolhida como vítima de deadlock (erro 1205), esperando 100 ms entre as tentativas. A terceira falha abre automaticamente um incidente de nível P3.

## Crescimento do arquivo de log nos bancos da Nimbus

Os arquivos de log têm crescimento fixo de 512 MB, e não em porcentagem, com limite de 50 GB por banco. É gerado alerta quando 80% do limite é atingido.

## Dados de produção em ambientes de desenvolvimento na Nimbus

É proibido restaurar cópias de produção em ambientes de desenvolvimento. Os dados de desenvolvimento devem ser anonimizados com o script `nmb_anonimiza.sql`.

## Manutenção de índices nos bancos da Nimbus

Índices com fragmentação entre 10% e 30% são reorganizados, e acima de 30% são reconstruídos. A manutenção ocorre aos domingos, das 01h às 04h.
