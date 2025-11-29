# 🔍 Módulo de Investigação de Acidentes v2.0

## Visão Geral

Módulo completo de investigação de acidentes baseado em **Fault Tree Analysis (FTA)** e **NBR 14280**, implementado com arquitetura **multi-acidente** usando `session_state`.

## 🏗️ Arquitetura

### Princípio Fundamental
- **Multi-acidente**: Todos os dados (evidências, timeline, nós da árvore) estão estritamente vinculados a um `accident_id` específico
- **Context Manager**: Sidebar gerencia seleção/criação de acidentes
- **Session State**: `st.session_state['current_accident']` armazena o ID do acidente ativo
- **Filtragem Rigorosa**: Todas as queries filtram por `accident_id`

## 📋 Estrutura do Banco de Dados

### Tabela Principal: `accidents`
```sql
- id (UUID, PK)
- title (TEXT) - Título do acidente
- description (TEXT) - Descrição detalhada
- occurrence_date (TIMESTAMP) - Data/hora de ocorrência
- status (TEXT) - 'Open' ou 'Closed'
- created_at (TIMESTAMP)
- created_by (UUID, FK para auth.users)
```

### Tabela Catálogo: `nbr_standards`
```sql
- id (SERIAL, PK) - INTEGER, não UUID
- category (TEXT) - 'unsafe_act', 'unsafe_condition', 'personal_factor'
- code (TEXT, UNIQUE) - Ex: '50.30.05.000'
- description (TEXT)
- created_at (TIMESTAMP)
```

### Tabelas Filhas (FK para `accidents.id`)

#### `evidence`
```sql
- id (UUID, PK)
- accident_id (UUID, FK → accidents.id ON DELETE CASCADE)
- image_url (TEXT)
- description (TEXT)
- uploaded_at (TIMESTAMP)
- uploaded_by (UUID, FK → auth.users)
```

#### `timeline`
```sql
- id (UUID, PK)
- accident_id (UUID, FK → accidents.id ON DELETE CASCADE)
- event_time (TIMESTAMP)
- description (TEXT)
- created_at (TIMESTAMP)
- created_by (UUID, FK → auth.users)
```

#### `fault_tree_nodes`
```sql
- id (UUID, PK)
- accident_id (UUID, FK → accidents.id ON DELETE CASCADE)
- parent_id (UUID, FK → fault_tree_nodes.id, NULLABLE) - Auto-referência para árvore
- label (TEXT) - Descrição do nó
- type (TEXT) - 'root', 'hypothesis', 'fact'
- status (TEXT) - 'pending', 'validated', 'discarded'
- nbr_standard_id (INTEGER, FK → nbr_standards.id, NULLABLE) - Apenas para nós validados
- created_at (TIMESTAMP)
- created_by (UUID, FK → auth.users)
```

## 🚀 Fluxo da Aplicação

### 1. Sidebar - Context Manager

**Seleção de Investigação Existente:**
- Dropdown lista todas as investigações
- Ao selecionar, salva `accident_id` em `st.session_state['current_accident']`
- Atualiza a página automaticamente

**Criação de Nova Investigação:**
- Expander com formulário
- Campos: Título (obrigatório), Descrição, Data de Ocorrência
- Ao criar, define `st.session_state['current_accident']` e recarrega

### 2. Verificação de Estado

```python
accident_id = st.session_state.get('current_accident')

if not accident_id:
    st.info("Por favor, selecione uma investigação...")
    return  # Para execução
```

### 3. Abas Principais (só renderizam se `accident_id` existe)

#### **Aba 1: Cenário e Evidências**
- Exibe detalhes do acidente (título, descrição, data)
- Upload de imagens → Supabase Storage → Registro em `evidence`
- Galeria em grid (3 colunas)
- Filtro: `WHERE accident_id = :accident_id`

#### **Aba 2: Cronologia**
- Formulário: Data, Hora, Descrição
- Insere em `timeline` com `accident_id`
- Visualização ordenada por `event_time`
- Filtro: `WHERE accident_id = :accident_id`

#### **Aba 3: Árvore de Falhas**
- **Root Node Automático**: Verifica se existe nó `type='root'` para o `accident_id`
  - Se não existe, cria automaticamente usando `accidents.title`
- Visualização Graphviz:
  - Verde = Validado
  - Vermelho = Descartado
  - Cinza = Pendente
- Adição de nós:
  - Seleção de nó pai (dropdown)
  - Tipo: `hypothesis` ou `fact`
  - Label (descrição)
- Validação de Hipóteses:
  - Lista todos os nós `type='hypothesis'`
  - Botões: Validar / Descartar / Pendente
  - Atualiza `status` do nó
- Filtro: `WHERE accident_id = :accident_id`

#### **Aba 4: Classificação Técnica**
- Busca nós validados: `WHERE accident_id = :accident_id AND status = 'validated'`
- Para cada nó validado:
  - Selectbox de categoria NBR
  - Selectbox de código NBR (filtrado por categoria)
  - Botão "Salvar Classificação"
  - Atualiza `nbr_standard_id` do nó

## 🔧 Funções do Serviço (`services/investigation.py`)

### Gerenciamento de Acidentes
- `create_accident(title, description, occurrence_date)` → Retorna `accident_id`
- `get_accidents()` → Lista todas as investigações
- `get_accident(accident_id)` → Detalhes de uma investigação
- `update_accident_status(accident_id, status)` → Atualiza status

### Evidências
- `upload_evidence_image(accident_id, file_bytes, filename, description)` → Upload + registro
- `get_evidence(accident_id)` → Lista evidências do acidente

### Timeline
- `add_timeline_event(accident_id, event_time, description)` → Adiciona evento
- `get_timeline(accident_id)` → Lista eventos ordenados

### Árvore de Falhas
- `get_root_node(accident_id)` → Busca nó raiz
- `create_root_node(accident_id, label)` → Cria nó raiz automaticamente
- `add_fault_tree_node(accident_id, parent_id, label, node_type)` → Adiciona nó
- `get_tree_nodes(accident_id)` → Lista todos os nós
- `update_node_status(node_id, status)` → Atualiza status (validated/discarded/pending)

### Classificação NBR
- `get_nbr_standards(category)` → Lista padrões (opcionalmente filtrado)
- `link_nbr_standard_to_node(node_id, nbr_standard_id)` → Vincula padrão
- `get_validated_nodes(accident_id)` → Nós validados com padrões NBR

## 📊 Dados Iniciais

A tabela `nbr_standards` foi populada com **15 registros** (5 por categoria):

### Atos Inseguros
- 50.30.05.000 - Usar equipamento de maneira imprópria
- 50.30.20.000 - Tornar inoperante dispositivo de segurança
- 50.60.50.000 - Deixar de prender, desligar ou sinalizar
- 50.30.10.000 - Usar equipamento inseguro
- 50.30.40.000 - Assumir posição ou postura insegura

### Condições Inseguras
- 60.20.10.000 - Mal projetado
- 60.40.50.000 - Equipamento sem identificação
- 60.10.30.000 - Problemas de espaço e circulação
- 60.40.40.000 - Conexão elétrica descoberta
- 60.20.30.000 - Constituído por material inadequado

### Fatores Pessoais
- 40.30.00.000 - Falta de conhecimento ou experiência
- 40.30.30.000 - Falta de conhecimento
- 40.60.00.000 - Desajustamento físico
- 40.30.60.000 - Falta de experiência ou especialização
- 40.80.00.000 - Desajustamento emocional

## 🔐 Segurança (RLS)

Todas as tabelas têm RLS habilitado com políticas públicas para testes.

⚠️ **IMPORTANTE**: Antes de produção, ajuste as políticas RLS conforme seu modelo de segurança:
- Filtro por `created_by` (usuário)
- Filtro por organização/tenant
- Controle de acesso baseado em roles

## 🎯 Diferenciais da v2.0

1. ✅ **Multi-acidente**: Sidebar gerencia contexto
2. ✅ **Session State**: Estado persistente entre recarregamentos
3. ✅ **Root Node Automático**: Criado automaticamente ao acessar árvore
4. ✅ **Filtragem Rigorosa**: Todas as queries filtram por `accident_id`
5. ✅ **Estrutura Hierárquica**: Árvore de falhas com auto-referência
6. ✅ **NBR Standards**: ID INTEGER (não UUID) para melhor performance

## 🐛 Troubleshooting

### Erro: "Por favor, selecione uma investigação"
- **Causa**: `st.session_state['current_accident']` está vazio
- **Solução**: Selecione uma investigação na sidebar ou crie uma nova

### Root node não aparece
- **Causa**: Nó raiz não foi criado automaticamente
- **Solução**: Acesse a aba "Árvore de Falhas" - o sistema criará automaticamente

### Evidências não aparecem
- **Causa**: Bucket não configurado ou permissões incorretas
- **Solução**: Verifique se o bucket `evidencias` existe e está público (ou com políticas adequadas)

### Graphviz não renderiza
- **Causa**: Graphviz não instalado no sistema
- **Solução**: Instale Graphviz (veja README) ou use o modo lista (fallback automático)

## 📝 Próximos Passos (Opcional)

- [ ] Exportação de relatório PDF da investigação completa
- [ ] Busca e filtros avançados na sidebar
- [ ] Comentários/notas aos nós da árvore
- [ ] Versionamento da árvore de falhas
- [ ] Métricas e estatísticas da investigação
- [ ] Integração com módulo de Acidentes existente
- [ ] Notificações quando investigação é fechada
- [ ] Histórico de alterações (auditoria)

---

**Desenvolvido conforme especificações NBR 14280 e metodologia FTA**

