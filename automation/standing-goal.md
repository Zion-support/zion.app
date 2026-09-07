# Objetivo de Standing — Zion Tech Group
# Status: ATIVO — ciclo contínuo sem standby

## Objetivo
Nunca entrar em standby, nunca esperar instruções. Atuar continuamente: verificar site, investigar Stripe, manter estado consolidado.

## Estado atual (2026-09-03)
- ✅ Site: 5/5 rotas HTTP 200
- ✅ Git reconcile: aplicado (commit a8df93dc3)
- 🚨 Stripe: pending — aguarda CEO (dashboard.stripe.com/settings/update)
- ⚠️ Mirror Windows (C:\Users\Zion\tmp\zion-deploy): 20.645 arquivos deletados detectados — NÃO COMMITAR/PUSHAR sem inspeção

## Próximo passo
Investigar causa dos arquivos deletados no mirror Windows (só leitura, sem modificar).
