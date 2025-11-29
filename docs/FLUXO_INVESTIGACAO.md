# 🔄 Fluxo de Investigação de Acidentes

## Visão Geral

O sistema agora segue um fluxo integrado onde os acidentes são criados na página "Acidentes" e depois selecionados para investigação na página "Investigação de Acidentes".

## 📋 Fluxo Completo

```
1. Criar Acidente → Página "Acidentes"
   ↓
2. Selecionar Acidente → Página "Investigação" (Sidebar)
   ↓
3. Preencher Investigação → Passos 1-4 (Wizard)
```

## 🎯 Passo a Passo

### Passo 1: Criar Acidente

**Localização:** Página "Acidentes" (menu "📊 Análise")

1. Acesse a aba "➕ Novo Acidente"
2. Preencha os dados do acidente:
   - Data de ocorrência
   - Tipo (fatal, lesão, sem lesão)
   - Classificação
   - Descrição
   - Dias perdidos
   - Causa raiz
   - Status
3. Clique em "💾 Salvar Acidente"
4. ✅ Acidente criado com sucesso!

**Resultado:** O acidente é salvo na tabela `accidents` e fica disponível para investigação.

### Passo 2: Selecionar Acidente para Investigação

**Localização:** Página "Investigação de Acidentes" (menu "📊 Análise")

1. Na **sidebar**, você verá um selectbox "Acidente:"
2. O selectbox lista todos os acidentes criados na página "Acidentes"
3. Cada opção mostra:
   - Título/Descrição do acidente
   - Tipo do acidente
   - Data de ocorrência
4. Selecione o acidente desejado
5. ✅ Investigação iniciada!

**Resultado:** O `accident_id` é armazenado em `st.session_state['current_accident']` e os passos de investigação são habilitados.

### Passo 3: Preencher Investigação (Wizard)

Após selecionar o acidente, siga os 4 passos:

1. **📸 Passo 1: Contexto e Evidências**
   - Preenche dados do relatório Vibra
   - Adiciona evidências (fotos)
   - Salva dados gerais

2. **📅 Passo 2: Linha do Tempo**
   - Adiciona eventos cronológicos
   - Reconstrói sequência temporal

3. **🌳 Passo 3: Árvore de Porquês**
   - Constrói árvore de falhas (FTA)
   - Valida hipóteses
   - Identifica causas

4. **📋 Passo 4: Classificação Oficial**
   - Vincula códigos NBR 14280
   - Classifica causas validadas

## 🔧 Integração Técnica

### Tabela Única: `accidents`

Ambas as páginas usam a mesma tabela `accidents`:

- **Página Acidentes**: Cria acidentes com campos básicos
- **Página Investigação**: Busca acidentes e adiciona campos de investigação

### Mapeamento de Campos

A função `get_accidents()` normaliza os dados:

```python
# Se title não existir, usa description
title = acc.get("title") or acc.get("description", "Acidente sem título")

# Se occurrence_date não existir, usa occurred_at
occurrence_date = acc.get("occurrence_date") or acc.get("occurred_at")

# Normaliza status: 'aberto'/'fechado' <-> 'Open'/'Closed'
status = "Open" if acc.get("status", "aberto").lower() in ["aberto", "open"] else "Closed"
```

### Filtros de Segurança

- **Admin**: Vê todos os acidentes
- **Usuário comum**: Vê apenas seus próprios acidentes (filtrado por `created_by`)

## 📊 Estrutura de Dados

### Campos Básicos (Página Acidentes)
- `occurred_at`: Data de ocorrência
- `type`: Tipo (fatal, lesão, sem lesão)
- `classification`: Classificação
- `description`: Descrição
- `lost_days`: Dias perdidos
- `root_cause`: Causa raiz
- `status`: Status (aberto/fechado)

### Campos Expandidos (Página Investigação)
- `title`: Título (se não existir, usa description)
- `occurrence_date`: Data/hora completa
- `registry_number`: Número do registro
- `base_location`: Local da base
- Campos de classificação (booleans)
- Campos de vazamento/processo
- Campos de meio ambiente

## 🎨 Interface do Usuário

### Sidebar - Seleção de Acidente

```
┌─────────────────────────────┐
│ Selecionar Acidente para    │
│ Investigação                │
│                             │
│ [Selectbox com acidentes]   │
│                             │
│ 💡 Crie o acidente na       │
│    página 'Acidentes'      │
│    primeiro                 │
└─────────────────────────────┘
```

### Selectbox Formatado

Cada opção mostra:
```
"Descrição do acidente... | tipo | DD/MM/YYYY"
```

Exemplo:
```
"Queda durante manutenção... | lesao | 15/01/2024"
```

## ⚠️ Validações

1. **Acidente não selecionado:**
   - Mostra mensagem informativa
   - Instrui a criar acidente na página "Acidentes"

2. **Nenhum acidente encontrado:**
   - Mostra aviso
   - Exibe instruções de como criar

3. **Filtro por usuário:**
   - Usuários comuns só veem seus acidentes
   - Admins veem todos

## 🔄 Sincronização

- Acidentes criados na página "Acidentes" aparecem **imediatamente** na página "Investigação"
- Não é necessário recarregar ou fazer refresh
- O selectbox é atualizado automaticamente

## 📝 Exemplo de Uso

1. **Usuário cria acidente:**
   - Vai em "Acidentes" → "➕ Novo Acidente"
   - Preenche: "Queda de funcionário", tipo "lesão", data "15/01/2024"
   - Salva

2. **Usuário inicia investigação:**
   - Vai em "Investigação de Acidentes"
   - Na sidebar, seleciona "Queda de funcionário... | lesao | 15/01/2024"
   - Preenche os 4 passos do wizard

3. **Resultado:**
   - Acidente completo com investigação detalhada
   - Dados do relatório Vibra preenchidos
   - Árvore de falhas construída
   - Códigos NBR vinculados

---

**Fluxo integrado: Acidentes → Investigação** ✅

