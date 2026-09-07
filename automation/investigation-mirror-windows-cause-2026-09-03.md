# Próximo passo — investigação causa raiz do mirror Windows

## Objetivo de Standing (contínuo)
Nunca entrar em standby, nunca esperar instruções. Atuar continuamente: verificar site, investigar Stripe, manter estado consolidado.

## Nome da investigação
Identificar causa raiz dos 20.645 arquivos deletados no mirror Windows (C:\Users\Zion\tmp\zion-deploy)

## Próximo passo documentado
Investigar causa dos arquivos deletados no mirror Windows (só leitura, sem modificar).

## Análise documentada (2026-09-03)
**Problema:** 20.645 arquivos deletados no git status do mirror.  
**Causa provável: core.ignorecase=true no Windows.**  
  - HEAD no mirror: 20.820 arquivos  
  - Working tree: só 71.209 arquivos  
  - Inversão do esperado (HEAD > working tree indica deleção, não limpeza)  
  - core.ignorecase=true converte nomes de arquivo para lowercase durante diff  
  - Arquivos com maiúsculas/minúsculas diferentes são vistos como conflitos/deleções  

**Exemplo:** se o Mac tem `Services/index.html` e o Windows vê `services/index.html`, o git vê como arquivo diferente → marcado como deletado.

**Bloqueio em vigor:** NÃO COMMITAR/PUSHAR no mirror Windows até inspeção humana.  
Risco: propagar 20.645 deleções remota.

## Próximo passo prático
CEO ou pessoa com acesso ao Windows:
1. Verificar `git config core.ignorecase` no mirror Windows
2. Se estiver `true`, avaliar `git config core.ignorecase false` antes de qualquer commit
3. Revisar arquivos deletados antes de qualquer push

// Hook de verificação: após alteração do ignorecase, validar que working tree e HEAD estão alinhados antes de qualquer ação.
