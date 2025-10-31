# Tabelas Necessárias do Sistema

Baseado na análise do código atual, estas são as tabelas que devem existir no banco de dados:

## ✅ Tabelas Obrigatórias (Usadas no Código)

### 1. **profiles** ⭐ OBRIGATÓRIA
- **Uso**: Sistema de autenticação e perfis de usuário
- **Operações**: INSERT, SELECT, UPDATE, UPSERT
- **Arquivos que usam**:
  - `auth/auth_utils.py` - Autenticação
  - `services/trial_manager.py` - Criação de trial users
  - `pages/6_Admin_Dados_Basicos.py` - Admin
  - `pages/8_Perfil_Usuario.py` - Perfil do usuário
  - `components/filters.py` - Filtros
- **RLS**: Sim, habilitado
- **NÃO DEVE SER LIMPADA**

### 2. **accidents** ⭐ OBRIGATÓRIA
- **Uso**: Registro de acidentes de trabalho
- **Operações**: INSERT, SELECT, UPDATE
- **Arquivos que usam**:
  - `pages/2_Acidentes.py` - Página principal de acidentes
  - `pages/8_Perfil_Usuario.py` - Perfil do usuário
  - `services/kpi.py` - Cálculo de KPIs
  - `services/uploads.py` - Importação CSV
  - `pages/6_Admin_Dados_Basicos.py` - Admin
- **RLS**: Sim, habilitado
- **Campo `created_by`**: UUID do usuário (tabela profiles.id)

### 3. **near_misses** ⭐ OBRIGATÓRIA
- **Uso**: Registro de quase-acidentes
- **Operações**: INSERT, SELECT, DELETE (anexos)
- **Arquivos que usam**:
  - `pages/3_Quase_Acidentes.py` - Página principal
- **RLS**: Sim, habilitado
- **Campo `created_by`**: UUID do usuário (tabela profiles.id)

### 4. **nonconformities** ⭐ OBRIGATÓRIA
- **Uso**: Registro de não conformidades
- **Operações**: INSERT, SELECT, DELETE (anexos)
- **Arquivos que usam**:
  - `pages/4_Nao_Conformidades.py` - Página principal
- **RLS**: Sim, habilitado
- **Campo `created_by`**: UUID do usuário (tabela profiles.id)

### 5. **attachments** ⭐ OBRIGATÓRIA
- **Uso**: Anexos/evidências (fotos, PDFs, etc.)
- **Operações**: INSERT, SELECT, DELETE
- **Arquivos que usam**:
  - `services/uploads.py` - Upload e gerenciamento
  - `pages/2_Acidentes.py` - Evidências de acidentes
  - `pages/3_Quase_Acidentes.py` - Evidências de quase-acidentes
  - `pages/4_Nao_Conformidades.py` - Evidências de não conformidades
- **RLS**: Sim, habilitado
- **Relaciona com**: accidents, near_misses, nonconformities

### 6. **hours_worked_monthly** ⭐ OBRIGATÓRIA
- **Uso**: Horas trabalhadas por mês
- **Operações**: INSERT, SELECT, UPSERT
- **Arquivos que usam**:
  - `pages/2_Acidentes.py` - Análise de dias trabalhados
  - `services/kpi.py` - Cálculo de KPIs
  - `services/uploads.py` - Importação CSV
  - `pages/6_Admin_Dados_Basicos.py` - Admin
- **RLS**: Sim, habilitado
- **Campo `created_by`**: UUID do usuário (tabela profiles.id)

### 7. **employees** ⭐ OBRIGATÓRIA
- **Uso**: Funcionários
- **Operações**: INSERT, SELECT, UPDATE, DELETE
- **Arquivos que usam**:
  - `pages/2_Acidentes.py` - Seleção de funcionário
  - `pages/3_Quase_Acidentes.py` - Seleção de funcionário
  - `pages/4_Nao_Conformidades.py` - Seleção de funcionário
  - `services/employees.py` - CRUD completo
- **Campos**: id, email, full_name, department, admission_date, user_id

### 8. **sites** ⭐ OBRIGATÓRIA
- **Uso**: Sites/locações
- **Operações**: INSERT, SELECT
- **Arquivos que usam**:
  - `pages/4_Nao_Conformidades.py` - Seleção de site
  - `pages/6_Admin_Dados_Basicos.py` - Admin (CRUD)
- **Campos**: id, code, name, type, description, is_active

### 9. **kpi_monthly** ⚠️ PODE SER TABELA OU VIEW
- **Uso**: KPIs calculados mensalmente
- **Operações**: INSERT, SELECT, UPDATE
- **Arquivos que usam**:
  - `services/kpi.py` - Cálculo e busca de KPIs
  - `pages/6_Admin_Dados_Basicos.py` - Recalcular KPIs
- **Observação**: Pode ser uma VIEW materializada ou TABELA
- **Campo `created_by`**: UUID do usuário (se for tabela)

## ⚠️ Tabelas que Existem no Banco mas Não são Usadas no Código

### 10. **admin_users** ⚠️ EXISTE MAS NÃO USADA
- **Status no Banco**: ✅ Existe (BASE TABLE)
- **Uso no Código**: ❌ Não encontrado uso no código atual
- **Observação**: Tabela existe no banco mas não é referenciada no código
- **Recomendação**: Pode ser uma tabela legada ou planejada para uso futuro

### 11. **actions** ⚠️ EXISTE MAS NÃO USADA
- **Status no Banco**: ✅ Existe (BASE TABLE)
- **Uso no Código**: ❌ Não encontrado uso direto no código atual
- **Documentação RLS**: Sim (POLITICAS_RLS.md menciona)
- **Observação**: Tabela existe, mencionada na documentação, mas código atual não usa
- **Recomendação**: Pode ser funcionalidade planejada mas não implementada ainda

## ⚠️ Tabelas Mencionadas no Código mas Não Existem

### 12. **contractors** ⚠️ CÓDIGO EXISTE, TABELA NÃO
- **Uso no Código**: ✅ Código existe em `pages/6_Admin_Dados_Basicos.py`
- **Status no Banco**: ❌ Não existe
- **Documentação**: Sim (ARQUITETURA.md menciona)
- **Recomendação**: Criar tabela ou remover código relacionado

### 13. **kpi_monthly** ⚠️ PODE SER VIEW
- **Uso no Código**: ✅ Usado em `services/kpi.py` e `pages/6_Admin_Dados_Basicos.py`
- **Status no Banco**: ❓ Pode ser VIEW (não aparece como BASE TABLE)
- **Operações**: INSERT, SELECT, UPDATE (se for tabela)
- **Recomendação**: Verificar se é VIEW ou criar como tabela se necessário

---

## 📊 Resumo Baseado nas Tabelas Reais do Banco

### ✅ Tabelas que Existem no Banco (10):
1. `accidents` ⭐ OBRIGATÓRIA
2. `actions` ⚠️ Existe mas não usada no código
3. `admin_users` ⚠️ Existe mas não usada no código
4. `attachments` ⭐ OBRIGATÓRIA
5. `employees` ⭐ OBRIGATÓRIA
6. `hours_worked_monthly` ⭐ OBRIGATÓRIA
7. `near_misses` ⭐ OBRIGATÓRIA
8. `nonconformities` ⭐ OBRIGATÓRIA
9. `profiles` ⭐ OBRIGATÓRIA (NÃO LIMPAR)
10. `sites` ⭐ OBRIGATÓRIA

### ❌ Tabelas que Não Existem mas Código Usa:
- `contractors` (código existe mas tabela não)
- `kpi_monthly` (pode ser VIEW, não aparece como BASE TABLE)

### 📝 Tabelas Mencionadas na Documentação:
- `actions` - Existe mas não é usada no código atual
- `admin_users` - Existe mas não é usada no código atual

---

## 🔍 Como Verificar no Banco

Execute este SQL para listar todas as tabelas:

```sql
SELECT 
    table_name,
    table_type
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE'
ORDER BY table_name;
```

Para ver VIEWs:

```sql
SELECT 
    table_name
FROM information_schema.views 
WHERE table_schema = 'public'
ORDER BY table_name;
```

