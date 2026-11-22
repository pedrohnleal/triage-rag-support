# Azure: segredos, identidade e dados

## Identidade gerenciada no Azure

A identidade gerenciada do Azure pode ser atribuída pelo sistema (ciclo de vida atrelado ao recurso) ou pelo usuário (recurso independente, reutilizável). Ela elimina credenciais no código, mas exige que se atribua uma função RBAC ao recurso que será acessado.

## Referências ao Key Vault no Azure App Service

No Azure App Service, o valor de uma configuração pode referenciar um segredo com `@Microsoft.KeyVault(SecretUri=https://<cofre>.vault.azure.net/secrets/<segredo>/)`. A referência só é resolvida se o app tiver identidade gerenciada com permissão de leitura de segredos no cofre; sem a permissão, a referência aparece com erro de status e o valor não é resolvido.

## Firewall do Azure SQL Database

O Azure SQL Database bloqueia acessos por padrão e usa regras de firewall do servidor baseadas em IP. Quando o IP do cliente não está autorizado, a conexão falha com o erro 40615. A solução é criar uma regra de IP ou habilitar a opção que permite o acesso de serviços do Azure ao servidor.
