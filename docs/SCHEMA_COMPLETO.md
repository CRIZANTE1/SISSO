# 📊 Schema Completo do Banco de Dados - SISSO

**Última atualização:** 2025-01-29  
**Banco de Dados:** PostgreSQL (Supabase)  
**Schema:** `public`

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Tabelas Principais](#tabelas-principais)
3. [Tabelas de Investigação](#tabelas-de-investigação)
4. [Tabelas de Suporte](#tabelas-de-suporte)
5. [Enums e Tipos Customizados](#enums-e-tipos-customizados)
6. [Foreign Keys](#foreign-keys)
7. [Políticas RLS](#políticas-rls)
8. [Índices e Constraints](#índices-e-constraints)

---

## 🎯 Visão Geral

O banco de dados SISSO é composto por **17 tabelas** organizadas em diferentes módulos:

- **Gestão de Usuários e Perfis:** `profiles`, `employees`
- **Acidentes e Incidentes:** `accidents`, `near_misses`, `nonconformities`
- **Investigação de Acidentes:** `accidents_investigation`, `evidence`, `timeline`, `fault_tree_nodes`, `involved_people`, `nbr_standards`
- **Ações e Anexos:** `actions`, `attachments`
- **KPIs e Métricas:** `kpi_monthly`, `hours_worked_monthly`
- **Feedback e Logs:** `feedbacks`, `user_logs`
- **Configuração:** `sites`

**Todas as tabelas possuem RLS (Row Level Security) habilitado.**

---

## 📦 Tabelas Principais

### 1. `profiles`

Tabela central de perfis de usuários do sistema.

| Coluna | Tipo | Nullable | Default | Descrição |
|--------|------|----------|---------|-----------|
| `id` | `uuid` | ❌ | `uuid_generate_v4()` | **PK** - Identificador único |
| `email` | `text` | ❌ | - | Email do usuário (UNIQUE) |
| `full_name` | `text` | ✅ | - | Nome completo |
| `role` | `text` | ❌ | - | Função: `admin`, `editor`, `viewer` |
| `status` | `text` | ✅ | `'ativo'` | Status: `ativo`, `inativo`, `suspenso`, `pendente` |
| `plan` | `text` | ✅ | `'trial'` | Plano: `trial`, `basic`, `premium`, `dev_ilimitado`, `enterprise` |
| `company_name` | `text` | ✅ | - | Nome da empresa |
| `employees_count` | `integer` | ✅ | - | Quantidade de funcionários |
| `contact_email` | `text` | ✅ | - | Email de contato |
| `created_at` | `timestamptz` | ✅ | `now()` | Data de criação |
| `updated_at` | `timestamptz` | ✅ | `now()` | Data de atualização |

**Constraints:**
- `PRIMARY KEY (id)`
- `UNIQUE (email)`
- `CHECK (role IN ('admin', 'editor', 'viewer'))`
- `CHECK (status IN ('ativo', 'inativo', 'suspenso', 'pendente'))`
- `CHECK (plan IN ('trial', 'basic', 'premium', 'dev_ilimitado', 'enterprise'))`

---

### 2. `accidents`

Tabela principal de acidentes registrados no sistema.

| Coluna | Tipo | Nullable | Default | Descrição |
|--------|------|----------|---------|-----------|
| `id` | `uuid` | ❌ | `uuid_generate_v4()` | **PK** - Identificador único |
| `title` | `text` | ✅ | - | Título do acidente |
| `description` | `text` | ✅ | - | Descrição detalhada |
| `occurred_at` | `date` | ❌ | - | Data de ocorrência |
| `occurrence_date` | `timestamptz` | ✅ | - | Data/hora completa de ocorrência |
| `type` | `accident_type` | ❌ | - | Tipo: `fatal`, `lesao`, `sem_lesao` |
| `classification` | `text` | ✅ | - | Classificação |
| `body_part` | `text` | ✅ | - | Parte do corpo afetada |
| `lost_days` | `integer` | ✅ | `0` | Dias perdidos |
| `root_cause` | `text` | ✅ | - | Causa raiz |
| `status` | `text` | ✅ | `'fechado'` | Status: `aberto`, `em_andamento`, `fechado` |
| `registry_number` | `text` | ✅ | - | Número de registro |
| `base_location` | `text` | ✅ | - | Local da base (manual) |
| `site_id` | `uuid` | ✅ | - | **FK** → `sites.id` |
| `class_injury` | `boolean` | ✅ | `false` | Acidente com lesão |
| `class_community` | `boolean` | ✅ | `false` | Acidente com lesão na comunidade |
| `class_environment` | `boolean` | ✅ | `false` | Impacto ao meio ambiente |
| `class_process_safety` | `boolean` | ✅ | `false` | Segurança de processo |
| `class_asset_damage` | `boolean` | ✅ | `false` | Dano ao patrimônio |
| `class_near_miss` | `boolean` | ✅ | `false` | Quase acidente |
| `severity_level` | `severity_level_enum` | ✅ | - | Gravidade: `Low`, `Medium`, `High`, `Catastrophic` |
| `estimated_loss_value` | `numeric(15,2)` | ✅ | - | Valor estimado de perda |
| `product_released` | `text` | ✅ | - | Produto liberado |
| `volume_released` | `numeric(10,2)` | ✅ | - | Volume liberado (m³) |
| `volume_recovered` | `numeric(10,2)` | ✅ | - | Volume recuperado (m³) |
| `release_duration_hours` | `numeric(10,2)` | ✅ | - | Duração do vazamento (horas) |
| `equipment_involved` | `text` | ✅ | - | Equipamento envolvido |
| `area_affected` | `area_affected_enum` | ✅ | - | Área afetada: `Soil`, `Water`, `Not Applicable`, `Other` |
| `employee_id` | `uuid` | ✅ | - | **FK** → `employees.id` |
| `created_by` | `uuid` | ✅ | - | **FK** → `profiles.id` |
| `created_at` | `timestamptz` | ✅ | `now()` | Data de criação |

**Constraints:**
- `PRIMARY KEY (id)`
- `FOREIGN KEY (site_id) REFERENCES sites(id)`
- `FOREIGN KEY (employee_id) REFERENCES employees(id)`
- `FOREIGN KEY (created_by) REFERENCES profiles(id)`
- `CHECK (status IN ('aberto', 'em_andamento', 'fechado'))`

---

### 3. `employees`

Cadastro de funcionários/colaboradores.

| Coluna | Tipo | Nullable | Default | Descrição |
|--------|------|----------|---------|-----------|
| `id` | `uuid` | ❌ | `gen_random_uuid()` | **PK** - Identificador único |
| `full_name` | `text` | ✅ | - | Nome completo |
| `document_id` | `text` | ✅ | - | CPF/Identidade |
| `job_title` | `text` | ✅ | - | Cargo/Função |
| `department` | `text` | ✅ | - | Departamento |
| `admission_date` | `date` | ✅ | - | Data de admissão |
| `termination_date` | `date` | ✅ | - | Data de desligamento |
| `email` | `text` | ✅ | - | Email |
| `user_id` | `uuid` | ✅ | - | **FK** → `profiles.id` (opcional) |
| `status` | `text` | ✅ | `'active'` | Status: `active`, `inactive` |
| `created_at` | `timestamptz` | ✅ | `now()` | Data de criação |
| `updated_at` | `timestamptz` | ✅ | `now()` | Data de atualização |

**Constraints:**
- `PRIMARY KEY (id)`
- `FOREIGN KEY (user_id) REFERENCES profiles(id)`

---

### 4. `sites`

Cadastro de bases/sites da empresa.

| Coluna | Tipo | Nullable | Default | Descrição |
|--------|------|----------|---------|-----------|
| `id` | `uuid` | ❌ | `gen_random_uuid()` | **PK** - Identificador único |
| `code` | `text` | ❌ | - | Código único do site (UNIQUE) |
| `name` | `text` | ❌ | - | Nome do site |
| `type` | `text` | ✅ | - | Tipo de site |
| `description` | `text` | ✅ | - | Descrição |
| `is_active` | `boolean` | ✅ | `true` | Site ativo |
| `created_at` | `timestamptz` | ✅ | `now()` | Data de criação |
| `updated_at` | `timestamptz` | ✅ | `now()` | Data de atualização |

**Constraints:**
- `PRIMARY KEY (id)`
- `UNIQUE (code)`

---

### 5. `near_misses`

Registro de quase acidentes.

| Coluna | Tipo | Nullable | Default | Descrição |
|--------|------|----------|---------|-----------|
| `id` | `uuid` | ❌ | `uuid_generate_v4()` | **PK** - Identificador único |
| `occurred_at` | `date` | ❌ | - | Data de ocorrência |
| `description` | `text` | ✅ | - | Descrição |
| `potential_severity` | `text` | ✅ | - | Gravidade potencial |
| `status` | `text` | ✅ | `'aberto'` | Status: `aberto`, `tratando`, `fechado` |
| `created_by` | `uuid` | ✅ | - | **FK** → `profiles.id` |
| `created_at` | `timestamptz` | ✅ | `now()` | Data de criação |

**Constraints:**
- `PRIMARY KEY (id)`
- `FOREIGN KEY (created_by) REFERENCES profiles(id)`
- `CHECK (status IN ('aberto', 'tratando', 'fechado'))`

---

### 6. `nonconformities`

Registro de não conformidades.

| Coluna | Tipo | Nullable | Default | Descrição |
|--------|------|----------|---------|-----------|
| `id` | `uuid` | ❌ | `uuid_generate_v4()` | **PK** - Identificador único |
| `opened_at` | `date` | ❌ | - | Data de abertura |
| `occurred_at` | `date` | ✅ | - | Data de ocorrência |
| `standard_ref` | `text` | ✅ | - | Referência da norma |
| `severity` | `text` | ✅ | - | Gravidade: `leve`, `moderada`, `grave`, `critica` |
| `description` | `text` | ✅ | - | Descrição |
| `status` | `text` | ✅ | `'aberta'` | Status: `aberta`, `tratando`, `encerrada` |
| `created_by` | `uuid` | ✅ | - | **FK** → `profiles.id` |
| `created_at` | `timestamptz` | ✅ | `now()` | Data de criação |

**Constraints:**
- `PRIMARY KEY (id)`
- `FOREIGN KEY (created_by) REFERENCES profiles(id)`
- `CHECK (severity IN ('leve', 'moderada', 'grave', 'critica'))`
- `CHECK (status IN ('aberta', 'tratando', 'encerrada'))`

---

### 7. `actions`

Plano de ações (5W2H) vinculado a acidentes, quase acidentes ou não conformidades.

| Coluna | Tipo | Nullable | Default | Descrição |
|--------|------|----------|---------|-----------|
| `id` | `uuid` | ❌ | `uuid_generate_v4()` | **PK** - Identificador único |
| `entity_type` | `text` | ❌ | - | Tipo: `accident`, `near_miss`, `nonconformity` |
| `entity_id` | `uuid` | ❌ | - | ID da entidade relacionada |
| `what` | `text` | ❌ | - | O que fazer |
| `who` | `text` | ✅ | - | Quem fará |
| `when_date` | `date` | ✅ | - | Quando fazer |
| `where_text` | `text` | ✅ | - | Onde fazer |
| `why` | `text` | ✅ | - | Por que fazer |
| `how` | `text` | ✅ | - | Como fazer |
| `how_much` | `numeric` | ✅ | - | Quanto custa |
| `status` | `text` | ✅ | `'aberta'` | Status: `aberta`, `em_andamento`, `em_execucao`, `fechada`, `concluida`, `cancelada` |
| `created_by` | `uuid` | ✅ | - | **FK** → `profiles.id` |
| `created_at` | `timestamptz` | ✅ | `now()` | Data de criação |

**Constraints:**
- `PRIMARY KEY (id)`
- `FOREIGN KEY (created_by) REFERENCES profiles(id)`
- `CHECK (entity_type IN ('accident', 'near_miss', 'nonconformity'))`
- `CHECK (status IN ('aberta', 'em_andamento', 'em_execucao', 'fechada', 'concluida', 'cancelada'))`

---

### 8. `attachments`

Anexos (fotos, documentos) vinculados a entidades.

| Coluna | Tipo | Nullable | Default | Descrição |
|--------|------|----------|---------|-----------|
| `id` | `uuid` | ❌ | `uuid_generate_v4()` | **PK** - Identificador único |
| `bucket` | `text` | ❌ | `'evidencias'` | Bucket do Supabase Storage |
| `path` | `text` | ❌ | - | Caminho do arquivo |
| `entity_type` | `text` | ❌ | - | Tipo: `accident`, `near_miss`, `nonconformity`, `action` |
| `entity_id` | `uuid` | ❌ | - | ID da entidade relacionada |
| `uploaded_by` | `text` | ✅ | - | **FK** → `profiles.email` |
| `uploaded_at` | `timestamptz` | ✅ | `now()` | Data de upload |

**Constraints:**
- `PRIMARY KEY (id)`
- `FOREIGN KEY (uploaded_by) REFERENCES profiles(email)`
- `CHECK (entity_type IN ('accident', 'near_miss', 'nonconformity', 'action'))`

---

### 9. `kpi_monthly`

KPIs mensais calculados (Taxa de Frequência, Taxa de Gravidade, etc.).

| Coluna | Tipo | Nullable | Default | Descrição |
|--------|------|----------|---------|-----------|
| `id` | `uuid` | ❌ | `uuid_generate_v4()` | **PK** - Identificador único |
| `period` | `date` | ❌ | - | Período (mês/ano) |
| `created_by` | `uuid` | ❌ | - | **FK** → `profiles.id` |
| `accidents_total` | `integer` | ✅ | `0` | Total de acidentes |
| `fatalities` | `integer` | ✅ | `0` | Fatalidades |
| `lost_days_total` | `integer` | ✅ | `0` | Total de dias perdidos |
| `hours` | `numeric` | ✅ | `0` | Horas trabalhadas |
| `frequency_rate` | `numeric` | ✅ | `0` | Taxa de frequência |
| `severity_rate` | `numeric` | ✅ | `0` | Taxa de gravidade |
| `debited_days` | `integer` | ✅ | `0` | Dias debitados |
| `created_at` | `timestamptz` | ✅ | `now()` | Data de criação |
| `updated_at` | `timestamptz` | ✅ | `now()` | Data de atualização |

**Constraints:**
- `PRIMARY KEY (id)`
- `FOREIGN KEY (created_by) REFERENCES profiles(id)`
- `UNIQUE (period, created_by)`

---

### 10. `hours_worked_monthly`

Horas trabalhadas mensais por usuário.

| Coluna | Tipo | Nullable | Default | Descrição |
|--------|------|----------|---------|-----------|
| `id` | `uuid` | ❌ | `uuid_generate_v4()` | **PK** - Identificador único |
| `year` | `integer` | ❌ | - | Ano |
| `month` | `integer` | ❌ | - | Mês (1-12) |
| `hours` | `numeric` | ❌ | - | Horas trabalhadas (>= 0) |
| `created_by` | `uuid` | ✅ | - | **FK** → `profiles.id` |

**Constraints:**
- `PRIMARY KEY (id)`
- `FOREIGN KEY (created_by) REFERENCES profiles(id)`
- `CHECK (month >= 1 AND month <= 12)`
- `CHECK (hours >= 0)`
- `UNIQUE (year, month, created_by)`

---

### 11. `feedbacks`

Feedbacks, sugestões e relatos de erros dos usuários.

| Coluna | Tipo | Nullable | Default | Descrição |
|--------|------|----------|---------|-----------|
| `id` | `uuid` | ❌ | `uuid_generate_v4()` | **PK** - Identificador único |
| `user_id` | `uuid` | ❌ | - | **FK** → `profiles.id` |
| `type` | `text` | ❌ | - | Tipo: `erro`, `sugestao`, `melhoria`, `outro` |
| `title` | `text` | ❌ | - | Título |
| `description` | `text` | ❌ | - | Descrição |
| `status` | `text` | ✅ | `'aberto'` | Status: `aberto`, `em_analise`, `resolvido`, `rejeitado` |
| `priority` | `text` | ✅ | `'media'` | Prioridade: `baixa`, `media`, `alta` |
| `created_by` | `uuid` | ✅ | - | **FK** → `profiles.id` |
| `created_at` | `timestamptz` | ✅ | `now()` | Data de criação |
| `updated_at` | `timestamptz` | ✅ | `now()` | Data de atualização |
| `resolved_at` | `timestamptz` | ✅ | - | Data de resolução |
| `admin_notes` | `text` | ✅ | - | Notas do administrador |

**Constraints:**
- `PRIMARY KEY (id)`
- `FOREIGN KEY (user_id) REFERENCES profiles(id)`
- `FOREIGN KEY (created_by) REFERENCES profiles(id)`
- `CHECK (type IN ('erro', 'sugestao', 'melhoria', 'outro'))`
- `CHECK (status IN ('aberto', 'em_analise', 'resolvido', 'rejeitado'))`
- `CHECK (priority IN ('baixa', 'media', 'alta'))`

---

### 12. `user_logs`

Logs temporários de ações dos usuários no sistema.

| Coluna | Tipo | Nullable | Default | Descrição |
|--------|------|----------|---------|-----------|
| `id` | `uuid` | ❌ | `uuid_generate_v4()` | **PK** - Identificador único |
| `user_id` | `uuid` | ❌ | - | **FK** → `profiles.id` |
| `action_type` | `text` | ❌ | - | Tipo: `create`, `update`, `delete`, `view`, `export`, `import`, `login`, `logout`, `upload`, `download`, `other` |
| `entity_type` | `text` | ❌ | - | Tipo de entidade afetada |
| `entity_id` | `uuid` | ✅ | - | ID da entidade relacionada |
| `description` | `text` | ❌ | - | Descrição detalhada |
| `ip_address` | `text` | ✅ | - | Endereço IP |
| `user_agent` | `text` | ✅ | - | User agent do navegador |
| `metadata` | `jsonb` | ✅ | - | Dados adicionais em JSON |
| `created_by` | `uuid` | ✅ | - | **FK** → `profiles.id` |
| `created_at` | `timestamptz` | ✅ | `now()` | Data de criação |
| `expires_at` | `timestamptz` | ✅ | - | Data de expiração |

**Constraints:**
- `PRIMARY KEY (id)`
- `FOREIGN KEY (user_id) REFERENCES profiles(id)`
- `FOREIGN KEY (created_by) REFERENCES profiles(id)`
- `CHECK (action_type IN ('create', 'update', 'delete', 'view', 'export', 'import', 'login', 'logout', 'upload', 'download', 'other'))`

---

## 🔍 Tabelas de Investigação

### 13. `accidents_investigation`

Tabela de investigações de acidentes (legado - não utilizada atualmente).

| Coluna | Tipo | Nullable | Default | Descrição |
|--------|------|----------|---------|-----------|
| `id` | `uuid` | ❌ | `gen_random_uuid()` | **PK** - Identificador único |
| `top_event_description` | `text` | ❌ | - | Descrição do evento topo |
| `status` | `accident_status_enum` | ✅ | `'Open'` | Status: `Open`, `Closed` |
| `created_by` | `uuid` | ✅ | - | **FK** → `auth.users.id` |
| `created_at` | `timestamptz` | ✅ | `now()` | Data de criação |

**Constraints:**
- `PRIMARY KEY (id)`
- `FOREIGN KEY (created_by) REFERENCES auth.users(id)`

**Nota:** Esta tabela é legado. As investigações são feitas diretamente na tabela `accidents`.

---

### 14. `evidence`

Evidências (fotos/vídeos) coletadas durante a investigação.

| Coluna | Tipo | Nullable | Default | Descrição |
|--------|------|----------|---------|-----------|
| `id` | `uuid` | ❌ | `gen_random_uuid()` | **PK** - Identificador único |
| `accident_id` | `uuid` | ❌ | - | **FK** → `accidents.id` |
| `image_url` | `text` | ✅ | - | URL da imagem no Storage |
| `description` | `text` | ✅ | - | Descrição da evidência |
| `uploaded_at` | `timestamptz` | ✅ | `now()` | Data de upload |
| `uploaded_by` | `uuid` | ✅ | - | **FK** → `auth.users.id` |

**Constraints:**
- `PRIMARY KEY (id)`
- `FOREIGN KEY (accident_id) REFERENCES accidents(id) ON DELETE CASCADE`
- `FOREIGN KEY (uploaded_by) REFERENCES auth.users(id)`

---

### 15. `timeline`

Linha do tempo de eventos durante a investigação.

| Coluna | Tipo | Nullable | Default | Descrição |
|--------|------|----------|---------|-----------|
| `id` | `uuid` | ❌ | `gen_random_uuid()` | **PK** - Identificador único |
| `accident_id` | `uuid` | ❌ | - | **FK** → `accidents.id` |
| `event_time` | `timestamptz` | ❌ | - | Data/hora do evento |
| `description` | `text` | ❌ | - | Descrição do evento |
| `created_at` | `timestamptz` | ✅ | `now()` | Data de criação |
| `created_by` | `uuid` | ✅ | - | **FK** → `auth.users.id` |

**Constraints:**
- `PRIMARY KEY (id)`
- `FOREIGN KEY (accident_id) REFERENCES accidents(id) ON DELETE CASCADE`
- `FOREIGN KEY (created_by) REFERENCES auth.users(id)`

---

### 16. `fault_tree_nodes`

Nós da árvore de falhas (Fault Tree Analysis).

| Coluna | Tipo | Nullable | Default | Descrição |
|--------|------|----------|---------|-----------|
| `id` | `uuid` | ❌ | `gen_random_uuid()` | **PK** - Identificador único |
| `accident_id` | `uuid` | ❌ | - | **FK** → `accidents.id` |
| `parent_id` | `uuid` | ✅ | - | **FK** → `fault_tree_nodes.id` (self-reference) |
| `label` | `text` | ❌ | - | Rótulo/descrição do nó |
| `type` | `text` | ❌ | - | Tipo: `root`, `hypothesis`, `fact` |
| `status` | `text` | ❌ | `'pending'` | Status: `pending`, `validated`, `discarded` |
| `is_basic_cause` | `boolean` | ✅ | `FALSE` | Indica se o nó é uma causa básica (marcado manualmente pelo usuário) |
| `is_contributing_cause` | `boolean` | ✅ | `FALSE` | Indica se o nó é uma causa contribuinte (marcado manualmente pelo usuário) |
| `nbr_standard_id` | `integer` | ✅ | - | **FK** → `nbr_standards.id` |
| `created_at` | `timestamptz` | ✅ | `now()` | Data de criação |
| `created_by` | `uuid` | ✅ | - | **FK** → `auth.users.id` |

**Constraints:**
- `PRIMARY KEY (id)`
- `FOREIGN KEY (accident_id) REFERENCES accidents(id)`
- `FOREIGN KEY (parent_id) REFERENCES fault_tree_nodes(id)`
- `FOREIGN KEY (nbr_standard_id) REFERENCES nbr_standards(id)`
- `FOREIGN KEY (created_by) REFERENCES auth.users(id)`
- `CHECK (type IN ('root', 'hypothesis', 'fact'))`
- `CHECK (status IN ('pending', 'validated', 'discarded'))`

**Estrutura Hierárquica:**
- `parent_id = NULL` → Nó raiz (Top Event)
- `parent_id = <uuid>` → Nó filho (hipótese ou fato)

---

### 17. `involved_people`

Pessoas envolvidas na investigação (motoristas, vítimas, testemunhas, comissão).

| Coluna | Tipo | Nullable | Default | Descrição |
|--------|------|----------|---------|-----------|
| `id` | `uuid` | ❌ | `gen_random_uuid()` | **PK** - Identificador único |
| `accident_id` | `uuid` | ❌ | - | **FK** → `accidents.id` |
| `person_type` | `text` | ❌ | - | Tipo: `Driver`, `Injured`, `Commission_Member`, `Witness` |
| `name` | `text` | ❌ | - | Nome completo |
| `registration_id` | `text` | ✅ | - | Matrícula/CPF |
| `job_title` | `text` | ✅ | - | Cargo/Função profissional |
| `company` | `text` | ✅ | - | Empresa |
| `age` | `integer` | ✅ | - | Idade |
| `time_in_role` | `text` | ✅ | - | Tempo na função |
| `aso_date` | `date` | ✅ | - | Data do ASO |
| `training_status` | `text` | ✅ | - | Status de treinamento (ou função na comissão) |
| `commission_role` | `text` | ✅ | - | Função na comissão: `Coordenador`, `Membro`, `Relator`, `Secretário`, etc. |
| `created_at` | `timestamptz` | ✅ | `now()` | Data de criação |
| `created_by` | `uuid` | ✅ | - | **FK** → `auth.users.id` (nullable) |

**Constraints:**
- `PRIMARY KEY (id)`
- `FOREIGN KEY (accident_id) REFERENCES accidents(id)`
- `FOREIGN KEY (created_by) REFERENCES auth.users(id)`
- `CHECK (person_type IN ('Driver', 'Injured', 'Commission_Member', 'Witness'))`

**Nota:** O campo `created_by` aponta para `auth.users.id`, mas o código usa `profiles.id`. O campo é nullable e não é preenchido para evitar erros de FK.

---

### 18. `nbr_standards`

Catálogo de códigos NBR 14280 para classificação técnica.

| Coluna | Tipo | Nullable | Default | Descrição |
|--------|------|----------|---------|-----------|
| `id` | `integer` | ❌ | `nextval(...)` | **PK** - Identificador único (SERIAL) |
| `category` | `text` | ❌ | - | Categoria: `unsafe_act`, `unsafe_condition`, `personal_factor` |
| `code` | `text` | ❌ | - | Código NBR (ex: `50.30.05.000`) (UNIQUE) |
| `description` | `text` | ❌ | - | Descrição do código |
| `created_at` | `timestamptz` | ✅ | `now()` | Data de criação |

**Constraints:**
- `PRIMARY KEY (id)`
- `UNIQUE (code)`
- `CHECK (category IN ('unsafe_act', 'unsafe_condition', 'personal_factor'))`

**Dados de Exemplo:**
- **Unsafe Acts:** `50.30.05.000`, `50.30.20.000`, `50.60.50.000`, etc.
- **Unsafe Conditions:** `60.20.10.000`, `60.40.50.000`, `60.10.30.000`, etc.
- **Personal Factors:** `40.30.00.000`, `40.30.30.000`, `40.60.00.000`, etc.

---

## 🔗 Foreign Keys

### Resumo de Relacionamentos

```
profiles (id)
  ├── accidents.created_by
  ├── actions.created_by
  ├── attachments.uploaded_by (via email)
  ├── feedbacks.user_id
  ├── feedbacks.created_by
  ├── hours_worked_monthly.created_by
  ├── kpi_monthly.created_by
  ├── near_misses.created_by
  ├── nonconformities.created_by
  └── user_logs.user_id
  └── user_logs.created_by

accidents (id)
  ├── fault_tree_nodes.accident_id
  └── involved_people.accident_id

sites (id)
  └── accidents.site_id

employees (id)
  └── accidents.employee_id

nbr_standards (id)
  └── fault_tree_nodes.nbr_standard_id

fault_tree_nodes (id)
  └── fault_tree_nodes.parent_id (self-reference)

accidents (id)
  ├── evidence.accident_id
  ├── timeline.accident_id
  ├── fault_tree_nodes.accident_id
  └── involved_people.accident_id

accidents_investigation (id) [LEGADO - Não utilizada]

auth.users (id) [Supabase Auth]
  ├── accidents_investigation.created_by
  ├── evidence.uploaded_by
  ├── timeline.created_by
  ├── fault_tree_nodes.created_by
  └── involved_people.created_by
```

---

## 🔒 Políticas RLS (Row Level Security)

**Todas as tabelas possuem RLS habilitado.**

### Padrão de Políticas

#### 1. **Tabelas com Isolamento por Usuário**
- `accidents`, `actions`, `near_misses`, `nonconformities`, `hours_worked_monthly`, `kpi_monthly`
- **SELECT/UPDATE/DELETE:** Usuário vê apenas seus próprios registros OU é admin
- **INSERT:** Usuário só pode criar registros com `created_by = seu_id`

#### 2. **Tabelas com Acesso Público (RLS permissivo)**
- `accidents_investigation`, `evidence`, `timeline`, `fault_tree_nodes`, `involved_people`, `nbr_standards`
- **Todas as operações:** `qual = true` (acesso público)

#### 3. **Tabelas Especiais**

**`profiles`:**
- **ALL:** Acesso para usuários autenticados (`auth.jwt() ->> 'email' IS NOT NULL`)

**`sites`:**
- **SELECT:** Usuários autenticados podem visualizar
- **INSERT/UPDATE/DELETE:** Apenas admins

**`feedbacks`:**
- **SELECT:** Usuário vê seus próprios feedbacks OU é admin
- **INSERT:** Usuário só pode criar com `user_id = seu_id`
- **UPDATE:** Usuário só pode atualizar seus próprios feedbacks com `status = 'aberto'` OU é admin

**`user_logs`:**
- **SELECT:** Usuário vê seus próprios logs OU é admin
- **INSERT:** Sistema pode inserir logs para qualquer usuário

**`attachments`:**
- **SELECT/UPDATE/DELETE:** Usuário vê apenas seus próprios anexos OU é admin
- **INSERT:** Usuário só pode criar com `uploaded_by = seu_email`

**`employees`:**
- **SELECT/UPDATE/DELETE:** Usuário vê apenas seus próprios funcionários (`user_id = seu_id`) OU é admin
- **INSERT:** Usuário só pode criar com `user_id = seu_id`

---

## 📊 Enums e Tipos Customizados

### `accident_type`
```sql
CREATE TYPE accident_type AS ENUM ('fatal', 'lesao', 'sem_lesao');
```

### `severity_level_enum`
```sql
CREATE TYPE severity_level_enum AS ENUM ('Low', 'Medium', 'High', 'Catastrophic');
```

### `area_affected_enum`
```sql
CREATE TYPE area_affected_enum AS ENUM ('Soil', 'Water', 'Not Applicable', 'Other');
```

### `accident_status_enum`
```sql
CREATE TYPE accident_status_enum AS ENUM ('Open', 'Closed');
```

---

## ⚠️ Observações Importantes

### 1. **Tabelas Legado**
- `accidents_investigation` não é mais utilizada. As investigações são feitas diretamente na tabela `accidents`.
- `evidence` e `timeline` ainda referenciam `accidents_investigation.id`, mas deveriam referenciar `accidents.id`. **Requer migração.**

### 2. **Foreign Keys para `auth.users`**
- Várias tabelas (`evidence`, `timeline`, `fault_tree_nodes`, `involved_people`) têm `created_by` apontando para `auth.users.id`.
- O código Python usa `profiles.id` (obtido via `get_user_id()`).
- **Solução atual:** O campo `created_by` é deixado como `NULL` para evitar erros de FK.

### 3. **RLS e Service Role**
- Todas as operações CRUD no código Python usam `get_service_role_client()` para contornar RLS.
- Validações de segurança são feitas **no código** (verificando `created_by` e `is_admin()`).

### 4. **Unique Constraints**
- `profiles.email` → UNIQUE
- `sites.code` → UNIQUE
- `nbr_standards.code` → UNIQUE
- `hours_worked_monthly(year, month, created_by)` → UNIQUE
- `kpi_monthly(period, created_by)` → UNIQUE

---

## 📝 Notas de Migração Futura

1. ✅ **CONCLUÍDO:** `evidence.accident_id` agora referencia `accidents.id`
2. ✅ **CONCLUÍDO:** `timeline.accident_id` agora referencia `accidents.id`
3. **Alterar `involved_people.created_by`** de `auth.users.id` para `profiles.id` (ou remover FK)
4. **Alterar `fault_tree_nodes.created_by`** de `auth.users.id` para `profiles.id` (ou remover FK)
5. **Considerar remover `accidents_investigation`** se não for mais utilizada

---

**Documento gerado automaticamente a partir do banco de dados Supabase.**

