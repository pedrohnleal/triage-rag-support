# Azure: conceitos básicos

## Grupos de recursos no Azure

Um resource group (grupo de recursos) do Azure é um contêiner lógico em que todo recurso pertence a exatamente um grupo. Excluir o grupo exclui todos os recursos dentro dele, de forma irreversível, salvo recursos com recuperação (soft delete). Antes de excluir, é possível mover recursos para outro grupo.

## Azure CLI: login e assinatura ativa

No Azure CLI, `az login` autentica o usuário, `az account set --subscription <id-ou-nome>` define a assinatura ativa e `az account show` exibe a assinatura corrente. Os comandos operam sobre a assinatura ativa; por isso, recursos que aparecem no portal mas não na CLI costumam indicar assinatura errada.

## Controle de acesso por função (RBAC) no Azure

No RBAC do Azure, as funções internas mais comuns são Owner (todos os acessos, inclusive atribuir permissões), Contributor (gerencia recursos, mas não atribui acesso) e Reader (somente leitura). As atribuições são herdadas da assinatura para o grupo de recursos e deste para o recurso.
