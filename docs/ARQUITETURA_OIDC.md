# 🔐 Arquitetura de Autenticação OIDC

## Visão Geral

O sistema implementa uma arquitetura de autenticação moderna baseada em **OIDC (OpenID Connect)** com Google como provedor de identidade, proporcionando segurança máxima sem armazenamento de senhas.

## 🏗️ Arquitetura em 3 Camadas

### 1. **Autenticação OIDC** - Login via Google
- **Provedor**: Google OAuth 2.0
- **Protocolo**: OpenID Connect (OIDC)
- **Segurança**: Sem armazenamento de senhas
- **Implementação**: `st.login()` nativo do Streamlit

### 2. **Autorização RBAC** - Controle de Acesso
- **Modelo**: Role-Based Access Control (RBAC)
- **Papéis**: Admin, Editor, Viewer
- **Verificação**: Baseada em dados do Supabase
- **Implementação**: Middleware de permissões

### 3. **Isolamento Multi-Tenant** - Segregação de Dados
- **Escopo**: Por usuário individual
- **Isolamento**: Row Level Security (RLS)
- **Dados**: Cada usuário vê apenas seus registros
- **Implementação**: Políticas RLS no PostgreSQL

## 📁 Estrutura de Arquivos

```
auth/
├── __init__.py
├── auth_utils.py      # Funções de autenticação
└── login_page.py      # Interface de login

managers/
├── __init__.py
└── supabase_config.py # Configuração do banco
```

## ⚙️ Configuração

### 1. Secrets do Streamlit (`.streamlit/secrets.toml`)

```toml
[supabase]
url = "https://seu-projeto.supabase.co"
key = "sua-anon-key-publica"
service_role_key = "sua-service-role-key-secreta"

[database]
connection_string = "postgresql://user:pass@host:port/db"
```

### 2. Variáveis de Ambiente (Alternativa)

```env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_ANON_KEY=sua-anon-key-publica
SUPABASE_SERVICE_ROLE_KEY=sua-service-role-key-secreta
```

## 🚀 Implementação Passo a Passo

### Passo 1: Configuração do Streamlit OIDC

No arquivo principal da aplicação (`app.py`):

```python
import streamlit as st
from auth.auth_utils import require_login, show_user_info

def main():
    st.set_page_config(
        page_title="Sistema SSO",
        page_icon="🛡️",
        layout="wide"
    )
    
    # 1. Verifica se usuário está logado via OIDC
    if not is_user_logged_in():
        show_login_page()
        st.stop()
    
    # 2. Verifica autorização na base de dados
    if not authenticate_user():
        show_access_denied_page()
        st.stop()
    
    # 3. Aplicação principal
    st.write("Bem-vindo ao sistema!")
```

### Passo 2: Funções de Autenticação (`auth/auth_utils.py`)

```python
import streamlit as st

def is_oidc_available():
    """Verifica se o login OIDC está configurado."""
    return hasattr(st, 'user') and hasattr(st.user, 'is_logged_in')

def is_user_logged_in():
    """Verifica se o usuário está logado via OIDC."""
    return is_oidc_available() and st.user.is_logged_in

def get_user_email() -> str | None:
    """Retorna o e-mail do usuário logado."""
    if is_user_logged_in() and hasattr(st.user, 'email'):
        return st.user.email.lower().strip()
    return None

def authenticate_user() -> bool:
    """Verifica o usuário na base de dados."""
    user_email = get_user_email()
    if not user_email:
        return False

    # Verifica se já está autenticado na sessão
    if st.session_state.get('authenticated_user_email') == user_email:
        return True

    # Verifica na base de dados
    user_info = check_user_in_database(user_email)
    
    if not user_info:
        return False

    # Salva informações do usuário na sessão
    st.session_state.user_info = user_info
    st.session_state.role = user_info.get('role', 'viewer')
    st.session_state.authenticated_user_email = user_email
    
    return True

def check_permission(level: str = 'editor'):
    """Verifica permissões e bloqueia se necessário."""
    if level == 'admin' and not is_admin():
        st.error("❌ Acesso restrito a Administradores.")
        st.stop()
    elif level == 'editor' and not can_edit():
        st.error("❌ Você não tem permissão para editar.")
        st.stop()
```

### Passo 3: Interface de Login (`auth/login_page.py`)

```python
import streamlit as st

def show_login_page():
    """Página de login inicial."""
    st.title("🛡️ Sistema SSO - Monitoramento")
    
    st.markdown("""
    <div style="text-align: center; padding: 2rem; background: linear-gradient(90deg, #1f77b4 0%, #17a2b8 100%); 
                border-radius: 10px; color: white; margin: 2rem 0;">
        <h2>🔐 Autenticação Obrigatória</h2>
        <p>Por favor, faça login com sua conta Google para acessar o sistema.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔗 Fazer Login com Google", type="primary"):
        try:
            st.login()  # Função nativa do Streamlit para OIDC
        except Exception as e:
            st.error(f"Erro ao iniciar login: {e}")

def show_access_denied_page():
    """Página para usuários não autorizados."""
    st.title("🚫 Acesso Restrito")
    
    user_name = get_user_display_name()
    user_email = get_user_email()
    
    st.warning(f"**Usuário:** {user_name}")
    st.warning(f"**E-mail:** {user_email}")
    
    if st.button("🚪 Sair / Trocar de Conta"):
        try:
            st.logout()
        except Exception:
            st.rerun()
```

## 🗄️ Estrutura do Banco de Dados

### Tabela de Perfis de Usuário

```sql
CREATE TABLE public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name TEXT,
  role TEXT NOT NULL CHECK (role IN ('admin','editor','viewer')),
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Políticas RLS

```sql
-- Políticas RLS para profiles
CREATE POLICY "Users can view their own profile" ON profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile" ON profiles
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Admins can view all profiles" ON profiles
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE id = auth.uid() 
            AND role = 'admin'
        )
    );
```

## ⚙️ Configuração do Streamlit Cloud

Para usar OIDC no Streamlit Cloud:

1. **Authentication provider**: Google
2. **Domain**: Seu domínio (opcional)
3. **Allowed emails**: Lista de e-mails permitidos (opcional)

### Configuração no Painel do Streamlit Cloud:

1. Acesse seu app no Streamlit Cloud
2. Vá em Settings > Authentication
3. Ative "Enable authentication"
4. Selecione "Google" como provider
5. Configure Client ID e Client Secret

## 🔒 Recursos de Segurança Implementados

### ✅ **Sem armazenamento de senhas**
- Toda autenticação via Google OAuth
- Credenciais gerenciadas pelo Google
- Tokens JWT seguros

### ✅ **Controle de acesso baseado em papéis (RBAC)**
- Admin: Acesso total
- Editor: Criação e edição
- Viewer: Apenas visualização

### ✅ **Sessões seguras**
- Dados do usuário na `st.session_state`
- Verificação de permissões em cada página
- Logout seguro com limpeza de sessão

### ✅ **Isolamento de dados**
- Row Level Security (RLS)
- Cada usuário vê apenas seus dados
- Políticas granulares por tabela

### ✅ **Verificação de permissões**
- Middleware em cada página crítica
- Verificação automática de papéis
- Bloqueio de acesso não autorizado

## 📝 Exemplo de Uso em Páginas

```python
# Em qualquer página que precise de permissões
from auth.auth_utils import check_permission, is_admin

def minha_pagina():
    # Verifica se é admin
    check_permission('admin')
    
    # Ou verifica permissão específica
    if is_admin():
        st.write("Conteúdo apenas para admins")
    else:
        st.write("Conteúdo para todos")
```

## 🎯 Vantagens desta Abordagem

### **Segurança**
- Não armazena senhas
- Usa Google como provedor confiável
- Tokens JWT seguros
- RLS no banco de dados

### **Simplicidade**
- Apenas `st.login()` e `st.logout()`
- Interface nativa do Streamlit
- Configuração mínima necessária

### **Flexibilidade**
- Fácil de adaptar para diferentes provedores OIDC
- Suporte a múltiplos usuários
- Papéis customizáveis

### **Escalabilidade**
- Suporta milhares de usuários
- Isolamento automático de dados
- Performance otimizada

### **Manutenibilidade**
- Código organizado em módulos
- Separação clara de responsabilidades
- Fácil de testar e debugar

## 🔧 Troubleshooting

### Problemas Comuns

1. **Erro de OIDC não configurado**
   - Verifique se o Streamlit Cloud tem autenticação ativada
   - Confirme as credenciais do Google

2. **Usuário não autorizado**
   - Verifique se o e-mail está na tabela `profiles`
   - Confirme se o usuário tem um papel válido

3. **Erro de conexão com Supabase**
   - Verifique as variáveis de ambiente
   - Confirme se as políticas RLS estão corretas

### Comandos de Debug

```python
# Verificar se OIDC está disponível
print(f"OIDC disponível: {is_oidc_available()}")
print(f"Usuário logado: {is_user_logged_in()}")
print(f"E-mail: {get_user_email()}")
print(f"Papel: {get_user_role()}")
```

## 📚 Referências

- [Streamlit Authentication](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management#authentication)
- [Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
- [OpenID Connect](https://openid.net/connect/)
- [Supabase RLS](https://supabase.com/docs/guides/auth/row-level-security)

---

**Esta arquitetura garante máxima segurança e facilidade de uso, sendo ideal para aplicações corporativas que precisam de controle de acesso robusto.**
