# Azure: App Service e Container Apps

## Configurações de aplicativo no Azure App Service

No Azure App Service, as configurações de aplicativo (application settings) são entregues ao app como variáveis de ambiente. Alterar uma configuração reinicia o aplicativo. Configurações marcadas como de slot ficam presas ao slot e não acompanham a troca (swap).

## Slots de implantação no Azure App Service

Os deployment slots do Azure App Service exigem plano Standard ou superior; não estão disponíveis nos planos Free, Shared e Basic. A troca (swap) entre slots promove a versão de staging para produção sem indisponibilidade, após o aquecimento da instância.

## Escala a zero no Azure Container Apps

No Azure Container Apps é possível definir `minReplicas` igual a 0, caso em que o aplicativo escala a zero réplicas quando não há tráfego. A primeira requisição após a escala a zero sofre atraso de partida a frio (cold start). Para evitar o atraso, define-se `minReplicas` com valor maior ou igual a 1.
