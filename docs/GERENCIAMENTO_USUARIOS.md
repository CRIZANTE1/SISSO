# 👥 Gerenciamento de Usuários e Papéis (Roles)

## Visão Geral

O sistema utiliza controle de acesso baseado em papéis (**RBAC** — Role-Based Access Control) com três níveis de permissão. A gestão dos usuários é feita exclusivamente por administradores através da página **Admin → Usuários**.

## Papéis Disponíveis

| Papel | Permissões |
|-------|-----------|
| **Administrador** (`admin`) | Acesso total: cria/edita/exclui registros, gerencia usuários, acessa logs, recalcula KPIs, vê dados de todos os usuários |
| **Editor** (`editor`) | Cria e edita registros próprios (acidentes, quase-acidentes, N/C, ações). Não acessa administração |
| **Visualizador** (`viewer`) | Apenas leitura. Visualiza dashboards, KPIs e relatórios, mas não pode criar nem editar registros |

## Fluxo de Criação de Usuário

### 1. Auto-cadastro (Solicitação de Acesso)

1. Usuário acessa o sistema e faz login via Google OAuth
2. Se o e-mail não estiver cadastrado, o sistema mostra a tela "Solicitar Acesso"
3. Usuário preenche nome e empresa, e envia a solicitação
4. O perfil é criado com:
   - **role:** `viewer` (padrão para novos usuários)
   - **status:** `pendente`
   - **plan:** `trial`
5. Um administrador precisa aprovar a solicitação

### 2. Criação Manual pelo Admin

1. Admin acessa **Admin → Usuários**
2. Preenche o formulário "Adicionar Novo Usuário":
   - **E-mail** (obrigatório)
   - **Papel**: Visualizador, Editor ou Administrador
   - **Senha** (opcional — se informada, cria login por e-mail/senha no Supabase Auth; sem senha, o usuário acessa apenas via Google OAuth)
   - **Usuário Ativo**: define se já entra como `ativo`
3. Se o e-mail já existir, o perfil é **atualizado** (role, status) em vez de duplicado

### 3. Aprovação de Solicitações Pendentes

Na seção **⏳ Solicitações Pendentes** da aba Usuários:

- Cada solicitação mostra nome, e-mail e dois botões: **Aprovar** e **Rejeitar**
- **Aprovar**: muda o status para `ativo` (mantém o role atual — geralmente `viewer`)
- **Rejeitar**: muda o status para `inativo`
- Após aprovação, o admin pode alterar o papel do usuário via edição inline (ver abaixo)

## Edição Inline de Papéis e Status

A tabela de **Usuários Cadastrados** usa um editor interativo (`st.data_editor`) que permite alterar papel e status diretamente, sem necessidade de re-preencher formulários.

### Colunas Editáveis

| Coluna | Tipo | Opções |
|--------|------|--------|
| **Papel** | Dropdown | Administrador / Editor / Visualizador |
| **Status** | Dropdown | ativo / inativo / pendente / suspenso |

As demais colunas (Nome, Email, Plano, Criado em) são somente leitura.

### Como Editar

1. Na aba **Usuários**, localize o usuário na tabela
2. Clique na célula da coluna **Papel** ou **Status** e selecione o novo valor no dropdown
3. Clique em **💾 Salvar Alterações**
4. O sistema persiste as mudanças no banco de dados (tabela `profiles`)

### Desfazer Alterações

O botão **🔄 Desfazer Alterações** restaura a tabela aos valores originais do banco, descartando qualquer edição não salva.

### Proteção contra Auto-rebaixamento

O administrador **não pode remover o próprio papel de admin**. Se tentar alterar o próprio papel para `editor` ou `viewer`, o sistema bloqueia a operação e exibe:

> ⚠️ Você não pode remover seu próprio papel de administrador!

Isso garante que sempre haja pelo menos um administrador no sistema.

## Status de Usuário

| Status | Significado |
|--------|------------|
| `ativo` | Usuário com acesso normal ao sistema |
| `inativo` | Usuário bloqueado (não consegue acessar) |
| `pendente` | Solicitação de acesso aguardando aprovação |
| `suspenso` | Usuário temporariamente suspenso |

## Estrutura no Banco de Dados

A tabela `profiles` armazena as informações de cada usuário:

```sql
CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    role TEXT NOT NULL CHECK (role IN ('admin', 'editor', 'viewer')),
    status TEXT DEFAULT 'ativo' CHECK (status IN ('ativo', 'inativo', 'pendente', 'suspenso')),
    plan TEXT DEFAULT 'trial' CHECK (plan IN ('trial', 'basic', 'premium', 'dev_ilimitado', 'enterprise')),
    company_name TEXT,
    employees_count INTEGER,
    contact_email TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

## Verificações de Permissão no Código

As funções de autorização estão em `auth/auth_utils.py`:

| Função | Retorna `True` para |
|--------|---------------------|
| `is_admin()` | Apenas `admin` |
| `is_editor()` | `admin` e `editor` |
| `can_edit()` | Idêntico a `is_editor()` |

O bloqueio de páginas administrativas é feito com `check_permission('admin')`, que chama `st.stop()` se o usuário não for admin.

---

**Atualizado em:** Agosto 2026
