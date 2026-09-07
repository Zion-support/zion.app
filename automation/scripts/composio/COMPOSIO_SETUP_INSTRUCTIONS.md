================================================================================
COMPOSIO SETUP — Zion Tech Group
================================================================================
Documento: 2026-09-01
Email: kleber@ziontechgroup.com
Status: SDK 0.21.0 instalado | Chave atual INVALIDA (401) | Browser OPERacional
================================================================================

SUMARIO EXECUTIVO
------------------
O Composio SDK esta instalado (v0.21.0) e o navegador (browser_exec) funciona.
No entanto, a chave API atual (ck_-AV0X5k4D8R-FbO9i7mi) retorna 401 Invalid API key.

Para resolver, voce precisa:
  1. Gerar uma nova API key no dashboard Composio
  2. (Opcional) Conectar OnePassword

Quando a nova key estiver disponivel, os scripts criados estao prontos para usar.


PASSO 1: GERAR NOVA API KEY COMPOSIO
--------------------------------------------------------------------------------
URLs diretos:
  - Login:        https://login.composio.dev
  - Dashboard:    https://dashboard.composio.dev
  - Platform:     https://platform.composio.dev

Passos detalhados:

1.1 Login no Composio
    Acesse: https://login.composio.dev
    Faça login com GOOGLE ou GITHUB
    Email: kleber@ziontechgroup.com

    IMPORTANTE: Esta etapa precisa ser feita por voce (autenticacao OAuth).
    O navegador pode levar voce ate a pagina de login, mas voce precisa:
    - Selecionar sua conta Google/GitHub
    - Informar senha se necessário
    - Aceitar a autorizacao do Composio

1.2 Gerar API Key
    a. Apos login, vá para: https://dashboard.composio.dev
    b. No menu lateral, clique em: Settings (engrenagem)
    c. Em Settings, clique em: API Keys (ou "Project Settings > API Keys")
    
    OBSERVACAO: Se o dashboard mostrar "Platform" em vez de "Dashboard",
    use o toggle no canto superior esquerdo para alternar entre as visoes.
    
    d. Clique em: "Create API Key" ou "Generate New Key"
    e. Nome sugerido: zion-automation-2026
    f. Permissões: selecionar as scopes necessarias (pelo menos tools:execute)
    g. Copie a chave gerada (formato: ak_...)

    A chave deve começar com "ak_" (diferente da chave antiga que comecava com "ck_")

1.3 Configurar no ambiente
    Adicione ao seu ambiente:
    
    export COMPOSIO_API_KEY="ak_..."

    Ou adicione ao arquivo .env do projeto:
    
    echo 'COMPOSIO_API_KEY=ak_...' >> /Users/miami2/zion.app/automation/.env

    Ou use o arquivo .hermes/.env:
    
    echo 'COMPOSIO_API_KEY=ak_...' >> ~/.hermes/.env


PASSO 2: CONECTAR ONEPASSWORD (OPCIONAL)
--------------------------------------------------------------------------------
Prerequisitos:
  - Conta 1Password ativa
  - Acesso ao app 1Password ou 1Password Connect

2.1 Criar Service Account no 1Password
    Opcao A — Via dashboard 1Password.com:
      1. Acesse: https://1password.com/downloads/connect
      2. Faça login na sua conta 1Password
      3. Vá para: Settings > Service Accounts
      4. Clique em "Create Service Account"
      5. Nome: zion-automation
      6. Vaults: selecione os vaults que o Composio pode acessar
      7. Salve o token gerado (mostra apenas uma vez!)
    
    Opcao B — Via app 1Password:
      1. Abra o app 1Password
      2. Settings (engrenagem) > Service Accounts
      3. Create new service account
      4. Copie o OP_SERVICE_ACCOUNT_TOKEN

2.2 Configurar no Composio
    Via dashboard:
      1. Acesse: https://dashboard.composio.dev/integrations
      2. Busque por "1Password" ou "one_password"
      3. Clique em "Connect"
      4. Preencha:
         - OP_SERVICE_ACCOUNT_TOKEN: (o token gerado)
         - OP_CONNECT_HOST: vault.1password.com (ou seu host custom)
      5. Salve

    Via CLI/python (quando tiver a API key valida):
      export COMPOSIO_API_KEY="ak_..."
      export OP_SERVICE_ACCOUNT_TOKEN="..."
      export OP_CONNECT_HOST="vault.1password.com"
      
      python3 scripts/composio/onepassword_composio_setup.py


PASSO 3: SCRIPT DE VERIFICAÇÃO
--------------------------------------------------------------------------------
Assim que tiver a chave valida, verifique com:

    export COMPOSIO_API_KEY="ak_..."
    python3 -c "
    import os, composio
    s = composio.Composio(api_key=os.environ['COMPOSIO_API_KEY'])
    tools = s.tools.get_raw_composio_tools(tools=['GITHUB_GET_REPOSITORY'])
    print(f'OK: {len(tools)} tools — chave valida')
    "

Se retornar "OK: 1 tools", a chave esta valida e funcionando.


PASSO 4: CONNECTAR CONTAS PRIORITÁRIAS
--------------------------------------------------------------------------------
Depois de ter a API key valida, conecte as aplicacoes do Zion:

    export COMPOSIO_API_KEY="ak_..."
    
    # Ver status atual
    python3 scripts/composio/composio_account_manager.py status
    
    # Conectar Gmail (para outreach)
    python3 scripts/composio/composio_account_manager.py connect gmail
    
    # Conectar GitHub (para repos)
    python3 scripts/composio/composio_account_manager.py connect github
    
    # Conectar Notion (para wiki/docs)
    python3 scripts/composio/composio_account_manager.py connect notion
    
    # Conectar Linear (para issues)
    python3 scripts/composio/composio_account_manager.py connect linear
    
    # Conectar Slack (para comunicação)
    python3 scripts/composio/composio_account_manager.py connect slack
    
    # Conectar HubSpot (para CRM)
    python3 scripts/composio/composio_account_manager.py connect hubspot

Para cada conexao, o script gera uma URL de OAuth. Abra no navegador e autorize.

Alternativa: usar o script de integracao completa:

    python3 scripts/composio/composio_integrate_all.py


LISTA COMPLETA DE APLICACOES DISPONÍVEIS NO COMPOSIO
--------------------------------------------------------------------------------
(organizadas por prioridade para Zion)

OAuth (precisam de autorização via navegador):
 gmail         — Email outreach e triage
 github        — Repositórios e issues
 notion        — Wiki e documentação
 linear        — Issue tracking
 slack         — Comunicação
 hubspot       — CRM
 google_calendar — Agendamento
 google_drive  — Arquivos
 calendly      — Agendamento de reuniões
 linkedin      — Rede social profissional
 supabase      — Banco de dados
 discord       — Comunidade
 airtable      — Planilhas avançadas
 stripe        — Pagamentos
 whatsapp      — Mensagens

API Key (configuração direta):
 resend        — Infra de email (100K contatos)
 brevo         — Email marketing
 serpapi       — Busca Google
 tavily        — Busca AI
 firecrawl     — Web scraping
 onepassword   — Gerenciamento de credenciais (OP_SERVICE_ACCOUNT_TOKEN)


ARQUIVOS CRIADOS
--------------------------------------------------------------------------------
scripts/composio/composio_cli-wrapper.py        — Wrapper CLI existente
scripts/composio/composio_account_manager.py   — Gerenciador de contas (NOVO)
scripts/composio/composio_integrate_all.py     — Integração em lote (NOVO)
scripts/composio/onepassword_composio_setup.py — Setup OnePassword (NOVO)
scripts/composio/composio_browser_auth.py      — Auth via navegador (NOVO)


STATUS DO BROWSER
--------------------------------------------------------------------------------
O navegador (browser_exec) funciona perfeitamente para:
  ✓ Navegar até páginas do Composio
  ✓ Preencher formularios (ex: email no login)
  ✓ Capturar informações da página
  
NÃO funciona para:
  ✗ Completar OAuth (login Google/GitHub) — requer interação humana
  ✗ Aprovar telas de consentimento OAuth
  ✗ Criar contas em serviços externos


PROBLEMAS CONHECIDOS
--------------------------------------------------------------------------------
1. Chave API atual (ck_-AV0X5k4D8R-FbO9i7mi) é INVALIDA
   - Retorna 401 em todas as chamadas
   - Formato antigo (ck_) precisa ser substituído por chave nova (ak_)

2. Wrapper CLI faz "login" artificialmente
   - O script composio_cli-wrapper.py imprime "✓ Autenticado" mesmo com chave invalida
   - Isso é um falso positivo — a chave realmente não funciona

3. OAuth necessita interação humana
   - Login Google/GitHub requer que você entre com sua conta
   - Telas de consentimento OAuth exigem sua aprovacao


PRÓXIMOS PASSOS (quando você tiver a chave)
--------------------------------------------------------------------------------
1. Fornecer a nova API key (ak_...) para o ambiente
2. Executar: python3 scripts/composio/composio_account_manager.py status
3. Conectar aplicacoes prioritárias (gmail, github, notion, etc.)
4. Configurar OnePassword se desejado
5. Testar scripts de automação com a chave valida


EMERGENCY FALLBACK (se nada funcionar)
--------------------------------------------------------------------------------
Se o dashboard Composio nao estiver acessivel ou houver problema:

1. Verifique no navegador:
   https://app.composio.dev
   https://dashboard.composio.dev

2. Verifique sua conta:
   https://login.composio.dev

3. Docs oficiais:
   https://docs.composio.dev

4. Suporte Composio:
   https://composio.dev/contact

5. GitHub Issues:
   https://github.com/ComposioHQ/composio/issues


================================================================================
Documento gerado: 2026-09-01
Zion Tech Group — Composio Integration Setup
================================================================================
