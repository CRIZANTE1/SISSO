# 🔍 Módulo de Investigação de Acidentes

## Visão Geral

Módulo completo de investigação de acidentes baseado em **Fault Tree Analysis (FTA)** e **NBR 14280**, implementado com arquitetura **multi-acidente** e interface **wizard guiada** que transforma o processo burocrático em um assistente intuitivo que guia o raciocínio do investigador.

## 🏗️ Arquitetura

### Princípio Fundamental
- **Multi-acidente**: Todos os dados (evidências, timeline, nós da árvore) estão estritamente vinculados a um `accident_id` específico
- **Context Manager**: Sidebar gerencia seleção/criação de acidentes
- **Session State**: `st.session_state['current_accident']` armazena o ID do acidente ativo
- **Filtragem Rigorosa**: Todas as queries filtram por `accident_id`
- **Fluxo Integrado**: Acidentes são criados na página "Acidentes" e selecionados para investigação

## 📋 Estrutura do Banco de Dados

### Tabela Principal: `accidents`
```sql
- id (UUID, PK)
- title (TEXT) - Título do acidente
- description (TEXT) - Descrição detalhada
- occurrence_date (TIMESTAMP) - Data/hora de ocorrência
- occurred_at (TIMESTAMP) - Data de ocorrência (alternativa)
- type (TEXT) - Tipo (fatal, lesão, sem lesão)
- classification (TEXT) - Classificação
- lost_days (INTEGER) - Dias perdidos
- root_cause (TEXT) - Causa raiz
- status (TEXT) - 'Open'/'Closed' ou 'aberto'/'fechado'
- registry_number (TEXT) - Número do registro
- base_location (TEXT) - Local da base
- created_at (TIMESTAMP)
- created_by (UUID, FK para auth.users)
```

### Tabela Catálogo: `nbr_standards`
```sql
- id (SERIAL, PK) - INTEGER, não UUID
- category (TEXT) - 'unsafe_act', 'unsafe_condition', 'personal_factor', 'accident_type'
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

### Políticas RLS

Todas as tabelas têm RLS habilitado com políticas públicas para testes. **IMPORTANTE**: Ajuste as políticas RLS conforme sua necessidade de segurança antes de produção:
- Filtro por `created_by` (usuário)
- Filtro por organização/tenant
- Controle de acesso baseado em roles (Admin, Editor, Viewer)

## 🔄 Fluxo Completo da Aplicação

### 1. Criar Acidente (Página "Acidentes")

**Localização:** Menu "📊 Análise" → "Acidentes"

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
4. ✅ Acidente criado e disponível para investigação

### 2. Selecionar Acidente para Investigação

**Localização:** Menu "📊 Análise" → "Investigação de Acidentes"

**Sidebar - Context Manager:**

**Seleção de Investigação Existente:**
- Dropdown lista todos os acidentes criados na página "Acidentes"
- Cada opção mostra: "Descrição do acidente... | tipo | DD/MM/YYYY"
- Ao selecionar, salva `accident_id` em `st.session_state['current_accident']`
- Atualiza a página automaticamente

**Criação de Nova Investigação (Alternativa):**
- Expander com formulário
- Campos: Título (obrigatório), Descrição, Data de Ocorrência
- Ao criar, define `st.session_state['current_accident']` e recarrega

### 3. Verificação de Estado

```python
accident_id = st.session_state.get('current_accident')

if not accident_id:
    st.info("Por favor, selecione uma investigação...")
    return  # Para execução
```

### 4. Wizard de Investigação (4 Passos)

Após selecionar o acidente, siga os 4 passos do wizard:

#### 📸 Passo 1: Contexto e Evidências
- Exibe detalhes do acidente (título, descrição, data)
- Preenche dados do relatório Vibra (campos expandidos)
- Upload de imagens → Supabase Storage → Registro em `evidence`
- Galeria em grid (3 colunas)
- Filtro: `WHERE accident_id = :accident_id`

#### 📅 Passo 2: Linha do Tempo
- Formulário: Data, Hora, Descrição
- Insere em `timeline` com `accident_id`
- Visualização ordenada por `event_time`
- Reconstrói sequência temporal do acidente
- Filtro: `WHERE accident_id = :accident_id`

#### 🌳 Passo 3: Árvore de Porquês (FTA)
- **Root Node Automático**: Verifica se existe nó `type='root'` para o `accident_id`
  - Se não existe, cria automaticamente usando `accidents.title`
- **Interface Conversacional**: 
  - Pergunta: "Por que isso aconteceu?"
  - Seleção: "Para qual evento/causa você quer adicionar uma nova causa?"
  - Feedback: "Por que **[Evento Selecionado]** aconteceu?"
- **Visualização Graphviz**:
  - 🟢 Verde = Validado (Causa confirmada)
  - 🔴 Vermelho = Descartado (Causa descartada)
  - ⚪ Cinza = Pendente (Em análise)
  - 🟠 Laranja (Borda) = Validado mas sem código NBR
- **Adição de nós**:
  - Seleção de nó pai (dropdown contextual)
  - Tipo: `hypothesis` ou `fact`
  - Label (descrição)
- **Validação de Hipóteses**:
  - Lista todos os nós `type='hypothesis'`
  - Botões: ✅ Confirmar/Verdadeiro (Verde) / ❌ Descartar/Falso (Vermelho) / ⏳ Em Análise (Cinza)
  - Atualiza `status` do nó
- **Fallback**: Lista quando Graphviz não disponível
- Filtro: `WHERE accident_id = :accident_id`

#### 📋 Passo 4: Classificação Oficial (NBR 14280)
- **Bloqueio Inteligente**: Só desbloqueia quando há pelo menos 1 causa validada
- **Busca Inteligente**: 
  - Campo de busca por palavras-chave (ex: "treinamento")
  - Filtro por categoria:
    - Falha Humana (Ato Inseguro)
    - Condição do Ambiente
    - Fator Pessoal
    - Tipo de Acidente
  - Resultados filtrados mostram código + descrição completa
- Busca nós validados: `WHERE accident_id = :accident_id AND status = 'validated'`
- Para cada nó validado:
  - Selectbox de categoria NBR
  - Selectbox de código NBR (filtrado por categoria e busca)
  - Botão "Salvar Classificação"
  - Atualiza `nbr_standard_id` do nó

### Barra de Progresso Visual

- **4 Passos Definidos** com indicadores visuais:
  - 🟢 Verde: Passo concluído
  - 🟡 Amarelo: Passo atual
  - ⚪ Cinza: Passo futuro
- **Navegação com Botões**: "Anterior" e "Próximo" em cada passo
- **Bloqueios Inteligentes**: Passo 4 só desbloqueia quando há causas validadas

## 🧭 Fluxo de Pensamento Implementado

O sistema segue o fluxo lógico:

```
O que houve? → Por que houve? → O que é isso na norma? → Como resolver?
```

1. **O Cenário**: Registrar evento topo, upload de fotos/vídeos, linha do tempo
2. **O Porquê - Árvore**: Construir árvore de falhas, validar hipóteses, identificar causas
3. **A Tradução - NBR 14280**: Classificar causas validadas com códigos NBR
4. **Solução**: Criar plano de ação (futuro)

## 🔧 Funções do Serviço (`services/investigation.py`)

### Gerenciamento de Acidentes
- `create_accident(title, description, occurrence_date, ...)` → Retorna `accident_id`
- `get_accidents()` → Lista todas as investigações (normaliza campos)
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

A tabela `nbr_standards` foi populada com registros iniciais:

### Atos Inseguros (códigos 50.30.xx.xxx, 50.60.xx.xxx)
- 50.30.05.000 - Usar equipamento de maneira imprópria
- 50.30.20.000 - Tornar inoperante dispositivo de segurança
- 50.60.50.000 - Deixar de prender, desligar ou sinalizar
- 50.30.10.000 - Usar equipamento inseguro
- 50.30.40.000 - Assumir posição ou postura insegura
- E mais...

### Condições Inseguras (códigos 60.10.xx.xxx, 60.20.xx.xxx, 60.30.xx.xxx, 60.40.xx.xxx)
- 60.20.10.000 - Mal projetado
- 60.40.50.000 - Equipamento sem identificação
- 60.10.30.000 - Problemas de espaço e circulação
- 60.40.40.000 - Conexão elétrica descoberta
- 60.20.30.000 - Constituído por material inadequado
- E mais...

### Fatores Pessoais (códigos 40.xx.xx.xxx)
- 40.30.00.000 - Falta de conhecimento ou experiência
- 40.30.30.000 - Falta de conhecimento
- 40.60.00.000 - Desajustamento físico
- 40.30.60.000 - Falta de experiência ou especialização
- 40.80.00.000 - Desajustamento emocional
- E mais...

### Tipos de Acidente (códigos 10.xx.xx.xxx, 20.xx.xx.xxx, 30.xx.xx.xxx, 40.xx.xx.xxx, 50.xx.xx.xxx)
- Vários códigos de classificação de tipos de acidentes

## ⚙️ Configuração Necessária

### 1. Bucket de Storage

O código usa o bucket **`evidencias`** que já existe no projeto. Se você preferir usar um bucket específico chamado **`evidence`**, você pode:

1. Criar o bucket no Supabase Storage
2. Configurá-lo como público ou privado (conforme necessidade)
3. Atualizar a linha correspondente em `services/investigation.py`:
   ```python
   bucket = "evidence"  # ao invés de "evidencias"
   ```

### 2. Instalação de Dependências

```bash
pip install -r requirements.txt
```

**Nota sobre Graphviz**: Para visualização completa da árvore de falhas, você também precisa instalar o Graphviz no sistema:

- **Windows**: Baixe do [site oficial](https://graphviz.org/download/) ou use `choco install graphviz`
- **Linux**: `sudo apt-get install graphviz` (Ubuntu/Debian) ou `sudo yum install graphviz` (RHEL/CentOS)
- **macOS**: `brew install graphviz`

Se o Graphviz não estiver instalado, o sistema funcionará normalmente, mas mostrará a árvore em formato de lista ao invés de gráfico.

### 3. Verificação das Tabelas

Execute no SQL Editor do Supabase para verificar se as tabelas foram criadas:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('nbr_standards', 'accidents', 'evidence', 'timeline', 'fault_tree_nodes');
```

## 🎯 Como Usar

1. **Crie um acidente**: No menu do Streamlit, vá para "Acidentes" na seção "📊 Análise" e crie um novo acidente

2. **Acesse a investigação**: No menu, vá para "Investigação de Acidentes" na seção "📊 Análise"

3. **Selecione o acidente**: Na sidebar, selecione o acidente que deseja investigar

4. **Siga o wizard**: Complete os 4 passos:
   - **Passo 1**: Colete evidências e preencha dados do contexto
   - **Passo 2**: Construa a timeline de eventos
   - **Passo 3**: Construa a árvore de falhas (FTA)
     - Adicione o nó raiz (criado automaticamente)
     - Adicione hipóteses como filhos
     - Valide ou descarte hipóteses
     - Adicione fatos confirmados
   - **Passo 4**: Classifique tecnicamente vinculando códigos NBR aos nós validados

## 🎨 Melhorias de UX

### Terminologia Natural
- **Antes**: "Selecione o Parent Node ID para adicionar Child"  
- **Agora**: "Por que **[Evento Selecionado]** aconteceu?"

### Feedback Visual Instantâneo (Semáforo)
- 🟢 **Verde** (`validated`): Causa confirmada - Pode ser classificada com código NBR
- 🔴 **Vermelho** (`discarded`): Causa descartada - Riscado no gráfico
- ⚪ **Cinza** (`pending`): Em análise - Precisa ser validada ou descartada
- 🟠 **Laranja** (Borda): Causa confirmada que precisa de classificação NBR

### Busca Inteligente para NBR
- Campo de busca por palavras-chave
- Filtro por categoria
- Resultados filtrados mostram código + descrição completa
- Feedback visual do código selecionado

### Tooltips e Ajuda Contextual
Cada campo importante tem ajuda explicando:
- **Upload de Fotos**: "Faça upload de fotos que documentem o acidente..."
- **Adicionar Causa**: "Liste todas as causas possíveis, mesmo que não tenha certeza..."
- **Validar**: "Use quando tiver evidências que confirmam/descartam esta causa"
- **Buscar NBR**: "Digite palavras relacionadas à causa..."

## 🔐 Segurança

⚠️ **IMPORTANTE**: As políticas RLS estão configuradas para acesso público apenas para testes. Antes de colocar em produção:

1. Revise e ajuste as políticas RLS conforme seu modelo de segurança
2. Implemente controle de acesso baseado em usuário/organização
3. Considere usar políticas baseadas em roles (Admin, Editor, Viewer)
4. Filtro por `created_by` para usuários comuns
5. Admins podem ver todos os acidentes

## 🐛 Troubleshooting

### Erro: "Por favor, selecione uma investigação"
- **Causa**: `st.session_state['current_accident']` está vazio
- **Solução**: Selecione uma investigação na sidebar ou crie uma nova na página "Acidentes"

### Erro ao fazer upload de imagem
- **Causa**: Bucket não configurado ou permissões incorretas
- **Solução**: Verifique se o bucket `evidencias` existe e está público (ou com políticas adequadas)

### Árvore de falhas não renderiza
- **Causa**: Graphviz não instalado no sistema
- **Solução**: Instale Graphviz (veja seção Configuração) ou use o modo lista (fallback automático)

### Root node não aparece
- **Causa**: Nó raiz não foi criado automaticamente
- **Solução**: Acesse a aba "Árvore de Falhas" - o sistema criará automaticamente

### Erro ao buscar padrões NBR
- **Causa**: Tabela `nbr_standards` não foi populada corretamente
- **Solução**: Execute a migration `seed_nbr_standards_safe` novamente se necessário

### Evidências não aparecem
- **Causa**: Bucket não configurado ou permissões incorretas
- **Solução**: Verifique se o bucket `evidencias` existe e está público (ou com políticas adequadas)

## 📁 Arquivos Criados

1. **`services/investigation.py`**: Serviço com todas as funções de banco de dados
2. **`pages/investigation.py`**: Página principal do Streamlit (versão wizard/guided)
3. **`utils/report_generator.py`**: Gerador de relatórios PDF (futuro)
4. **`requirements.txt`**: Atualizado com `graphviz>=0.20.0`

## 📝 Próximos Passos (Opcional)

- [ ] Adicionar passo 5: "Plano de Ação"
- [ ] Exportação de relatório PDF da investigação completa
- [ ] Busca e filtros avançados na sidebar
- [ ] Comentários/notas aos nós da árvore
- [ ] Versionamento da árvore de falhas
- [ ] Métricas e estatísticas da investigação
- [ ] Integração completa com módulo de Acidentes existente
- [ ] Notificações quando investigação é fechada
- [ ] Histórico de alterações (auditoria)
- [ ] Sugestões automáticas de códigos NBR baseadas em palavras-chave
- [ ] Modo "revisão" para investigações fechadas

## 🎯 Diferenciais da Versão Atual

1. ✅ **Multi-acidente**: Sidebar gerencia contexto
2. ✅ **Session State**: Estado persistente entre recarregamentos
3. ✅ **Root Node Automático**: Criado automaticamente ao acessar árvore
4. ✅ **Filtragem Rigorosa**: Todas as queries filtram por `accident_id`
5. ✅ **Estrutura Hierárquica**: Árvore de falhas com auto-referência
6. ✅ **NBR Standards**: ID INTEGER (não UUID) para melhor performance
7. ✅ **Wizard Guiado**: Interface passo a passo intuitiva
8. ✅ **Terminologia Natural**: Perguntas conversacionais ao invés de jargão técnico
9. ✅ **Feedback Visual**: Semáforo de cores para status das causas
10. ✅ **Busca Inteligente**: NBR fácil de encontrar com busca por palavras-chave
11. ✅ **Fluxo Integrado**: Acidentes criados na página "Acidentes" e investigados separadamente

---

**Desenvolvido conforme especificações NBR 14280 e metodologia FTA**

**Transformado de banco de dados burocrático em assistente intuitivo que guia o raciocínio do investigador** 🎯
