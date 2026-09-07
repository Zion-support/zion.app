# Checklist Stripe BR — Business Type: Company (CNPJ)

> **Aviso crítico (2026):** Se o tipo de negócio precisa mudar de *individual* (CPF) para *company* (CNPJ), **um novo Stripe account deve ser criado**. Não é apenas atualização de campos no mesmo account.  
> Fonte: [Updating tax information for Stripe accounts in Brazil](https://support.stripe.com/questions/updating-tax-information-for-stripe-accounts-in-brazil)

---

## Visão geral — o que esse checklist cobre

Este checklist enumera os campos e documentos que o Stripe exige para contas de **Legal Entity (CNPJ)** no Brasil, baseado nos documentos oficiais do Stripe (2025–2026). O CEO (Kleber Garcia Alcatrão) deve usá-lo como guia ao preencher o Dashboard.

### Fontes consultadas

1. [Brazil-specific information to open a Stripe account](https://support.stripe.com/questions/brazil-specific-information-to-open-a-stripe-account)
2. [2026 updates to Brazil verification requirements](https://support.stripe.com/questions/2025-updates-to-brazil-verification-requirements)
3. [Required verification information (Stripe Docs)](https://docs.stripe.com/connect/required-verification-information)
4. [Company beneficial ownership and director requirement](https://support.stripe.com/questions/company-beneficial-ownership-and-director-requirement)
5. [Updating tax information for Stripe accounts in Brazil](https://support.stripe.com/questions/updating-tax-information-for-stripe-accounts-in-brazil)
6. [Beneficial owner and director definitions](https://support.stripe.com/questions/beneficial-owner-and-director-definitions)

---

## Parte 1 — Ação preliminar: decidir se cria conta nova ou atualiza

| Sinal | Ação |
|-------|------|
| O account atual é **Individual (CPF)** e você precisa de **Company (CNPJ)** | **Criar novo Stripe account** — não é possível mudar o tipo de negócio no mesmo account |
| O account atual já é **Company (CNPJ)** mas os dados estão desatualizados/incompletos | Atualizar no Dashboard existente |
| Não se sabe qual é o tipo atual | Abrir Dashboard → Business Details Settings e verificar |

**Como verificar no Dashboard:**
1. Logar em [dashboard.stripe.com](https://dashboard.stripe.com/login)
2. Ir para **Settings → Business Details** (`dashboard.stripe.com/settings/business-details`)
3. Verificar **Business type** e **Tax ID** (CPF ou CNPJ)

---

## Parte 2 — Campos obrigatórios para Company (CNPJ)

### 2.1 — Informações da empresa (Business Details)

| Campo | O que preencher | Observação |
|-------|----------------|-------------|
| **Legal business name** | Razão social da empresa (conforme CNPJ) | Deve corresponder exatamente ao CNPJ registrado na Receita Federal. Não pode ser alterado após verificação. |
| **CNPJ** | Número do CNPJ de 14 dígitos (XX.XXX.XXX/XXXX-XX) | Deve estar **ativo** na Receita Federal. Verificar antes: [Consulta CNPJ](https://solucoes.receita.fazenda.gov.br/Servicos/cnpjreva/Cnpjreva_Solicitacao.asp) |
| **Business address** | Endereço fiscal da empresa no Brasil | Deve ser endereço físico (não PO Box). Corresponder ao CNPJ. |
| **Website** | URL do site da empresa (ex: https://ziontechgroup.com) | Se não tiver site, pode usar link de app store ou perfil social. O conteúdo do site deve corresponder ao nome da empresa e descrição do produto. |
| **Description of business** | Descrição da atividade da empresa | Selecione a indústria e descreva. Usado internamente pelo Stripe, não é enviado a autoridades fiscais. |
| **Business type** | **Company (CNPJ)** | Selecione explicitamente "Company" no formulário de tipos de negócio. |
| **Business representative** | Representante legal da empresa no Brasil | Ver Parte 3 |

**Onde preencher no Dashboard:**
- `dashboard.stripe.com/settings/business-details` — Business Details Settings
- `dashboard.stripe.com/account/details` — Account details (se for conta direta)

---

### 2.2 — Representante legal (Business Representative)

| Campo | O que preencher | Observação |
|-------|----------------|-------------|
| **Nome completo** | Nome do representante legal (pessoa física) | Deve ser um dos diretores ou sócios com poder de representação. Deve ter **CPF** e ser **residente no Brasil**. |
| **CPF do representante** | CPF de 11 dígitos | **Obrigatório.** Verificar status: [Consulta CPF](https://servicos.receita.fazenda.gov.br/Servicos/CPF/ConsultaSituacao/ConsultaPublica.asp) — deve estar **regular/ativo**. |
| **Data de nascimento** | DD/MM/AAAA | Confirmar com documento de identidade. |
| **Endereço do representante** | Endereço residencial no Brasil | Não pode ser PO Box. Deve ser endereço físico completo (rua, número, complemento, bairro, cidade, estado, CEP). |
| **Email do representante** | Email pessoal ou profissional | Usado para comunicação do Stripe. |
| **Telefone do representante** | Número de contato no Brasil | Preferível com DDD. |
| **Documento de identidade** | RG, CNH, ou passaporte (se não tiver CPF) | Foto colorida do documento. Deve estar válido (não expirado). |
| **Selfie com documento** | Foto da pessoa segurando o documento de identidade | Prova de vida (proof of life). Obrigatório para verificação de identidade. |

**Documentos aceitáveis para identidade (fonte: Stripe acceptable verification documents — Brazil):**
- Cartão de Identidade (RG)
- CNH (Carteira Nacional de Habilitação)
- Passaporte (para estrangeiros sem CPF)
- Documentos devem ser **coloridos**, **não expirados**, **não cortados**, **não processados/transcodificados**

---

### 2.3 — Sócios e controladores com 25%+ de ownership (UBOs — Ultimate Beneficial Owners)

**Definição (Stripe):** UBOs são indivíduos que possuem 25% ou mais da empresa, direta ou indiretamente, OU exercem controle significativo sobre ela (CEO, CFO, diretores, etc.).

**Atenção:** Se a empresa é **non-profit, government entity ou public corporation**, deve fornecer **todos os diretores, officers e executivos** (não apenas os com 25%+).

| Campo | O que preencher | Observação |
|-------|----------------|-------------|
| **Nome completo** | Nome de cada UBO | Deve corresponder ao nome registrado no CNPJ (ou nos documentos comprobatórios). |
| **CPF** | CPF de cada UBO | **Obrigatório** para brasileiros. Estrangeiros residentes no Brasil com CPF também fornecem CPF. Estrangeiros não residentes: ver Parte 5. |
| **Percentual de ownership** | % de participação de cada UBO | Deve somar 25%+ para quem é UBO. |
| **Data de nascimento** | DD/MM/AAAA | Para cada UBO. |
| **Endereço** | Endereço de cada UBO no Brasil | Deve ser endereço físico completo. |
| **Documento de identidade** | RG, CNH ou passaporte | Para cada UBO que precisa de verificação. |
| **Selfie com documento** | Para cada UBO que precisa de verificação | Prova de vida. |

**Confirmação via CNPJ (Stripe faz match automático):**
O Stripe verificaprogramaticamente os nomes dos UBOs contra o registro CNPJ. Se os nomes não batem, pode ser necessário:
- Upload de **documento de relação** (contrato social, estatuto social, ou ata de constituição) mostrando o nome completo e CPF do UBO, com mandato válido e assinatura do representante legal.
- Ou uso do **template de atestaçao da Stripe** para estruturas complexas.

**Error codes (para referência):**
- `verification_missing_owners` — nomes dos owners não correspondem ao registro CNPJ → adicionar persons com nomes que correspondem, ou upload `documents.proof_of_ultimate_beneficial_ownership`
- `verification_missing_directors` — nomes dos diretores não correspondem → adicionar persons, ou upload `documents.proof_of_registration`

---

### 2.4 — Diretores (Directors)

**Definição (Stripe):** Diretores são membros do conselho administrativo ou fiscal da empresa.

| Campo | O que preencher |
|-------|----------------|
| **Nome completo de cada diretor** | Conforme CNPJ ou documento comprobatório |
| **CPF de cada diretor** | Obrigatório para brasileiros |
| **Data de nascimento** | Para cada diretor |
| **Cargo/Função** | Presidente, Vice-presidente, Diretor, etc. |

**Observação:** Se os sócios/titulares forem **todos empresas** (pessoa jurídica) e não indivíduos, o Stripe pode pedir os diretores em vez dos owners. Nesses casos, usar `company.directors_provided` e fornecer os diretores via persons.

---

### 2.5 — Estrangeiros: sócios/diretores não residentes no Brasil

Se houver sócios, diretores ou UBOs que são **não brasileiros vivendo fora do Brasil**:

1. **Deve haver um representante legal no Brasil** com CPF e endereço no Brasil que assine um **poder de representação (Power of Attorney)** em favor do Stripe Brazil.
2. O representante legal no Brasil é o responsável pela conta.
3. Os estrangeiros devem ter seus dados registrados (nome, nacionalidade, data de nascimento, percentual de ownership), mas o CPF não se aplica — o representante brasileiro com CPF assume a responsabilidade legal.

**Documento necessário:** Poder de Attorney (procuração) com clausula específica para representação perante o Stripe Brazil, assinado pelo proprietário da empresa e reconhecido por escrito (ou com firma de tabelião).

---

## Parte 3 — Documentos para upload (se necessário)

### 3.1 — Documentos de identidade pessoal

Para cada pessoa que precisa de verificação de identidade (representante legal, UBOs, diretores):

| Tipo | Formato aceito | Requisitos |
|------|----------------|-------------|
| RG | JPEG ou PNG (foto original) | Colorido, não expirado, todos os bordas visíveis, não cortado |
| CNH | JPEG ou PNG (foto original) | Colorido, não expirada, todos os bordas visíveis, não cortada |
| Passaporte | JPEG ou PNG (foto original) | Colorido, não expirado, página de dados completa visível |
| Selfie com documento | JPEG ou PNG | Foto original (não screenshot), pessoa segurando documento, rosto e documento visíveis |

**Regra geral:** O formato deve estar no máximo um passo removido do original. Copias digitalizadas devem ser em PDF ou JPEG/PNG direto do scanner. Screenshots de documentos não são aceitos.

### 3.2 — Documentos de comprovação de relação (ownership/director)

**Para estrutura de propriedade simples:**

| Documento | O que deve conter |
|-----------|-------------------|
| Contrato Social | Nome da empresa, CNPJ, nome completo e CPF de cada sócio/owner, cargo, percentual, data de constituição |
| Ata de constituição ou alteração | Mesmas informações acima |
| Estatuto Social | Para empresas com estatuto, deve conter nome e CPF dos sócios/diretores |

**Documentos devem conter:**
- Nome da entidade legal e CNPJ
- Designação expressa de owner ou diretor com nome completo e CPF da pessoa, com termo de mandato válido
- Assinatura do representante legal da empresa

### 3.3 — Templates de atestaçao da Stripe (para estruturas complexas)

Para empresas com camadas intermediárias (holding companies, trusts, subsidiárias) que separam os UBOs finais da empresa operacional:

- **Template UBO attestation:** [Baixar PDF](https://docs.stripecdn.com/6e82842bfc01bd0b1c46d77f7d46b69673a9ca965ed2ad9ef53139f98abdbbaf.pdf)
- **Template Director attestation:** [Baixar PDF](https://docs.stripecdn.com/715ffef45157ff700bc368a4011659ee23bc8ba3c68746c5c15948a6eee1591f.pdf)

Preencha e faça upload conforme instruções.

### 3.4 — Prova de autorização (Proof of Authorization)

O Stripe exige confirmar que a pessoa que abriu a conta Stripe tem autoridade para agir em nome da empresa.

**Documentos aceitáveis (Relationship tab):**
- Poder de Attorney (procuração) com cláusula específica para o Stripe
- Documento que mostra o representante legal é um dos executive officers da empresa (conforme contrato social ou estatuto)
- Documento que mostra o representante legal foi appointado conforme os estatutos da empresa

---

## Parte 4 — Informações financeiras (Central Bank of Brazil — BCB)

O BCB exige que o Stripe colete **informações de capacidade financeira**.

| Pessoa | Faixa de receita/revenue mensal |
|--------|----------------------------------|
| **Individual (CPF)** | - Novo (sem receita) <br> - Menos de R$5.000 <br> - R$5.000–R$10.000 <br> - R$10.000–R$20.000 <br> - Mais que R$20.000 |
| **Legal Entity (CNPJ)** | - Novo (sem receita) <br> - Menos de R$5.000 <br> - R$5.000–R$30.000 <br> - R$30.000–R$400.000 <br> - Mais que R$400.000 |

**O que selecionar:** Escolha a faixa que melhor representa a **receita bruta mensal** esperada/projecionada da empresa.

---

## Parte 5 — Bank account (conta bancária para payouts)

| Campo | O que preencher |
|-------|----------------|
| **Banco** | Banco brasileiro (ex: Bradesco, Itaú, Caixa, Santander, BB, etc.) |
| **Agência** | Número da agência |
| **Conta** | Número da conta corrente |
| **Tipo de conta** | Conta corrente (não poupança) |
| **CPF/CNPJ associado** | A conta deve estar **nomeada pelo CPF ou CNPJ** registrado no Stripe |

**Regra:** A conta bancária deve estar sob o CPF ou CNPJ associado à conta Stripe. Se o Stripe usa CNPJ, a conta deve estar no nome da empresa (CNPJ), não no CPF de um sócio.

**Bancos suportados no Brasil:** Consulte [Supported bank accounts in Brazil](https://support.stripe.com/questions/supported-bank-accounts-in-brazil) para lista atualizada.

---

## Parte 6 — Ordem recomendada de preenchimento

Siga esta ordem para minimizar rework e rejeições:

### Passo 1 — Preparação (antes de abrir o Dashboard)
1. [ ] Verificar status do CNPJ: [Consulta CNPJ](https://solucoes.receita.fazenda.gov.br/Servicos/cnpjreva/Cnpjreva_Solicitacao.asp) — deve estar **ATIVO**
2. [ ] Verificar status de cada CPF envolvido: [Consulta CPF](https://servicos.receita.fazenda.gov.br/Servicos/CPF/ConsultaSituacao/ConsultaPublica.asp) — deve estar **REGULAR/ATIVO**
3. [ ] Recolher documentos de identidade de todas as pessoas que precisam de verificação (RG, CNH, passaporte)
4. [ ] Tirar selfies com documento para cada pessoa
5. [ ] Recolher documento comprobatório de relação (contrato social, estatuto, ata) se a empresa tem estrutura que precise de prova de ownership
6. [ ] Preparar poder de attorney se houver sócios/diretores estrangeiros não residentes
7. [ ] Identificar a conta bancária correta (nomeada pelo CNPJ da empresa)

### Passo 2 — Preenchimento no Dashboard
8. [ ] Logar em [dashboard.stripe.com](https://dashboard.stripe.com/login)
9. [ ] Ir para **Settings → Business Details** (`dashboard.stripe.com/settings/business-details`)
10. [ ] Preencher **Legal business name** (razão social conforme CNPJ)
11. [ ] Preencher **CNPJ** (14 dígitos)
12. [ ] Preencher **Business address** (endereço fiscal no Brasil)
13. [ ] Preencher **Website** (URL do site)
14. [ ] Preencher **Description of business** (indústria + descrição)
15. [ ] Selecionar **Business type = Company (CNPJ)**
16. [ ] Preencher **Business representative** (nome, CPF, data de nascimento, endereço, email, telefone)
17. [ ] Preencher **UBOs** (nome, CPF, percentual, data de nascimento, endereço para cada)
18. [ ] Preencher **Directores** (nome, CPF, cargo para cada)
19. [ ] Preencher **Financial capacity** (faixa de receita mensal da empresa)
20. [ ] Preencher ou confirmar **Bank account** (conta corrente sob o CNPJ da empresa)

### Passo 3 — Upload de documentos (se solicitado)
21. [ ] Upload de documento de identidade do representante legal (se solicitado)
22. [ ] Upload de selfie com documento do representante legal (se solicitado)
23. [ ] Upload de documento de identidade de cada UBO (se solicitado)
24. [ ] Upload de selfie com documento de cada UBO (se solicitado)
25. [ ] Upload de documento de identidade de cada diretor (se solicitado)
26. [ ] Upload de documento comprobatório de ownership (contrato social, estatuto) se `verification_missing_owners`
27. [ ] Upload de documento comprobatório de director se `verification_missing_directors`
28. [ ] Upload de template de atestaçao da Stripe se estrutura complexa
29. [ ] Upload de poder de attorney se houver representante legal estrangeiro

### Passo 4 — Revisão e política de mudanças
30. [ ] Revisar todas as informações antes de finalizar
31. [ ] **Importante:** Após verificação, **não é possível mudar o CNPJ ou o tipo de business type**. Se algo estiver errado, será necessário criar nova conta.
32. [ ] Monitorar o Dashboard por banners vermelhos de verificação pendente
33. [ ] Verificar email associado ao account para comunicações do Stripe

---

## Parte 7 — O que NÃO fazer

| O que evitar | Por que evitar |
|--------------|----------------|
| Usar CPF pessoal no campo CNPJ (se sócio não tem CNPJ) | Gera erro; CNPJ é obrigatório para company |
| Usar screenshot de documento de identidade | Não é aceito — deve ser foto original ou digitalização direta |
| Usar documento expirado | Será rejeitado |
| Usar documento cortado ou com bordas cortadas | Será rejeitado |
| usar documento processado/transcodificado (ex: PDF convertido de JPEG) | Deve ser no máximo um passo do original |
| Preencher CNPJ incorreto (com dígito verificador errado) | Verificação vai falhar |
| Preencher CPF incorreto | Verificação vai falhar; CPF deve estar regular na Receita Federal |
| Usar endereço de e-mail temporário ou que não será monitorado | Comunicações do Stripe podem ser perdidas |
| Mudar o CNPJ ou business type após verificação | Não é permitido — se errar, cria-se conta nova |

---

## Parte 8 — Troubleshooting e pausas de payouts

### 8.1 — Se os payouts forem pausados

O Stripe pode pausar payouts se:
- Informações obrigatórias não forem fornecidas
- Documentos não forem verificados dentro do prazo
- CNPJ ou CPF não estiverem ativos na Receita Federal
- Nomes dos UBOs/diretores não corresponderem ao CNPJ

**Prazos típicos:**
- 28 dias a partir da data limite para fornecer informações antes que payouts sejam pausados
- 90 dias a partir da data limite para fornecer informações antes que **payments** sejam pausados

**Ação:**
1. Verificar o Dashboard — deve haver um banner vermelho com "Review details"
2. Verificar email para mensagens do Stripe
3. Fornecer documentos/ informações faltantes
4. Aguardar até 24 horas para reprocessamento após upload

### 8.2 — Se a verificação falhar por mismatch de nome

Se o nome informado não corresponde ao registro CNPJ:
- Verificar o nome exato no CNPJ (pode ser nome comercial diferente de nome civil)
- Se necessário, fornecer documento comprobatório (contrato social, ata) mostrando o nome e CPF
- Para estruturas complexas, usar template de atestaçao da Stripe

### 8.3 — CNPJ ou CPF inativo/cancelado

Se o CNPJ ou CPF estiver **inativo, cancelado ou pendente de regularização**:
- A conta pode ter restrições ou limitações
- Verificar status: [Consulta CNPJ](https://solucoes.receita.fazenda.gov.br/Servicos/cnpjreva/Cnpjreva_Solicitacao.asp) ou [Consulta CPF](https://servicos.receita.fazenda.gov.br/Servicos/CPF/ConsultaSituacao/ConsultaPublica.asp)
- Se estiver inativo, regularizar com a Receita Federal antes de usar o Stripe

---

## Parte 9 — Referências rápidas e links úteis

| Recurso | URL |
|---------|-----|
| Dashboard Stripe | https://dashboard.stripe.com/login |
| Business Details Settings | https://dashboard.stripe.com/settings/business-details |
| Account details | https://dashboard.stripe.com/account/details |
| Consulta CNPJ (Receita Federal) | https://solucoes.receita.fazenda.gov.br/Servicos/cnpjreva/Cnpjreva_Solicitacao.asp |
| Consulta CPF (Receita Federal) | https://servicos.receita.fazenda.gov.br/Servicos/CPF/ConsultaSituacao/ConsultaPublica.asp |
| Documentos aceitáveis (Brazil) | https://docs.stripe.com/acceptable-verification-documents?country=BR |
| Brazil verification troubleshooting | https://support.stripe.com/questions/brazil-specific-account-verification-troubleshooting |
| Updating tax info (BR) | https://support.stripe.com/questions/updating-tax-information-for-stripe-accounts-in-brazil |
| Brazil-specific info to open account | https://support.stripe.com/questions/brazil-specific-information-to-open-a-stripe-account |
| Company beneficial ownership requirement | https://support.stripe.com/questions/company-beneficial-ownership-and-director-requirement |
| 2026 Brazil verification updates | https://support.stripe.com/questions/2025-updates-to-brazil-verification-requirements |
| Supported bank accounts in Brazil | https://support.stripe.com/questions/supported-bank-accounts-in-brazil |

---

## Parte 10 — Checklist resumido (para impressão / referência rápida)

### Antes de começar
- [ ] Decidir: cria conta nova (CPF→CNPJ) ou atualiza account existente (CNPJ)
- [ ] Verificar CNPJ ativo naReceita Federal
- [ ] Verificar CPF de todos os envolvidos ativo naReceita Federal
- [ ] Recolher documentos de identidade (RG, CNH, passaporte)
- [ ] Tirar selfies com documentos
- [ ] Preparar contrato social / estatuto social se necessário
- [ ] Preparar poder de attorney se houver sócios estrangeiros
- [ ] Identificar conta bancária sob o CNPJ da empresa

### Preenchimento no Dashboard
- [ ] Business name (razão social)
- [ ] CNPJ (14 dígitos)
- [ ] Business address (endereço fiscal Brasil)
- [ ] Website URL
- [ ] Description of business
- [ ] Business type = Company (CNPJ)
- [ ] Business representative (nome, CPF, Nascimento, endereço, email, telefone)
- [ ] UBOs (nome, CPF, %, Nascimento, endereço)
- [ ] Directors (nome, CPF, cargo)
- [ ] Financial capacity (faixa de receita)
- [ ] Bank account (conta corrente sob CNPJ)

### Upload de documentos (se necessário)
- [ ] ID do representante legal
- [ ] Selfie com ID do representante legal
- [ ] ID de cada UBO
- [ ] Selfie com ID de cada UBO
- [ ] ID de cada diretor
- [ ] Contrato social / documento comprobatório de ownership (se `verification_missing_owners`)
- [ ] Documento comprobatório de director (se `verification_missing_directors`)
- [ ] Template atestaçao Stripe (se estrutura complexa)
- [ ] Poder de attorney (se representante legal estrangeiro)

### Após preencher
- [ ] Revisar todas as informações
- [ ] Verificar banner vermelho no Dashboard
- [ ] Verificar email para comunicações Stripe
- [ ] Lembrete: após verificação, CNPJ e business type não podem ser alterados

---

*Documento criado em 2026-09-03 por Hermes Agent (Solar Pro4, Upstage AI) para Kleber Garcia Alcatrão, CEO da Zion Tech Group. Baseado em documentos oficiais do Stripe (2025–2026). Última atualização de fontes: September 2026.*

*Stripe account referenciado neste contexto: acct_1U8rFeJRA2AketBh (Zion Holdings) — sem campos pending requirements visíveis via API pública; ação permanece com CEO no Dashboard.*
