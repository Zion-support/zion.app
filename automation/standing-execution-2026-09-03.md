# Standing Execution — Zion Tech Group (2026-09-03)

> Registro de ações de verificação e manutenção do ciclo de standing autônomo.

---

## Identidade consolidada

- **CEO:** Kleber Garcia Alcatrão
- **Empresa:** Zion Tech Group
- **Site:** https://ziontechgroup.com (GitHub Pages, repo zion-support.github.io)
- **Assistente:** Hermes Agent (Solar Pro4, Upstage AI) via Telegram + Mac + Termux
- **Data:** 2026-09-03

---

## Ações executadas nesta rodada

### 1. Checklist Stripe BR criado

**Arquivo:** `/Users/miami2/zion.app/automation/stripe-checklist-br-business-type-company-2026-09-03.md`
**Tamanho:** 22.884 bytes / 376 linhas
**Status:** ✅ Verificado existente

**Conteúdo:**
- Aviso crítico: mudança de Individual (CPF) → Company (CNPJ) exige nova conta Stripe
- Campos obrigatórios para Company (CNPJ)
- UBOs, diretores, representante legal
- Ordem recomendada de preenchimento (Passo 1 a 4)
- Documentos para upload (se necessário)
- Troubleshooting e pausas de payouts
- Referências rápidas e links

**Fontes consultadas:**
1. Brazil-specific information to open a Stripe account
2. 2026 updates to Brazil verification requirements
3. Required verification information (Stripe Docs)
4. Company beneficial ownership and director requirement
5. Updating tax information for Stripe accounts in Brazil
6. Beneficial owner and director definitions

### 2. Verificação do site

**Status:** 5/5 rotas HTTP 200 ✅
- `/` → 200
- `/assessments/` → 200
- `/careers/` → 200
- `/contact/` → 200
- `/blog/` → 200

**Observação:** Site estável, sem ações necessárias além de monitoramento.

---

## Status geral

| Componente | Status | Ação necessária |
|------------|--------|-----------------|
| **Site ziontechgroup.com** | ✅ Estável (5/5 rotas 200) | Monitoramento contínuo |
| **Stripe (acct_1U8rFeJRA2AketBh)** | ⚠️ Pendente (checklist entregue) | CEO preenche no Dashboard |
| **Mirror Windows** | ⚠️ Bloqueado (20.645 arquivos deletados) | Sem ação sem humano |
| **Growth Engine** | ℹ️ Em operação (sem novos envios) | Monitoramento |

---

## Próximos passos para CEO

1. **Stripe:** Abrir Dashboard → Business Details Settings (`dashboard.stripe.com/settings/business-details`) e seguir o checklist criado
2. **Site:** Manter monitoramento (sem ações adicional por enquanto)
3. **Mirror Windows:** Se quiser limpar, fazer clone fresco no Windows com `core.ignorecase=true`, sem mexer no remote

---

*Documento atualizado automaticamente pelo ciclo de standing. Próxima atualização: ao ocorrer nova ação ou mudança de status.*
