import streamlit as st
from .auth_utils import get_user_display_name, get_user_email

def show_login_page():
    """Página de login inicial."""
    st.title("🛡️ Sistema SSO - Monitoramento")
    st.subheader("Sistema de Gestão de Segurança e Saúde Ocupacional")
    
    st.markdown("""
    <div style="text-align: center; padding: 2rem; background: linear-gradient(90deg, #1f77b4 0%, #17a2b8 100%); 
                border-radius: 10px; color: white; margin: 2rem 0;">
        <h2>🔐 Autenticação Obrigatória</h2>
        <p>Por favor, faça login com sua conta Google para acessar o sistema.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### Acesso Seguro")
        st.markdown("""
        - ✅ **Autenticação via Google OAuth**
        - ✅ **Controle de acesso baseado em papéis**
        - ✅ **Isolamento de dados por usuário**
        - ✅ **Sessões seguras**
        """)
        
        st.markdown("---")
        
        if st.button("🔗 Fazer Login com Google", type="primary", use_container_width=True):
            try:
                st.login()  # Função nativa do Streamlit para OIDC
            except Exception as e:
                st.error(f"Erro ao iniciar login: {e}")
        
        st.markdown("---")
        
        st.info("""
        **Instruções:**
        1. Clique no botão acima para fazer login
        2. Autorize o acesso com sua conta Google
        3. Se for seu primeiro acesso, um perfil será criado automaticamente
        4. Administradores podem gerenciar permissões na seção Admin
        """)

def show_access_denied_page():
    """Página para usuários não autorizados."""
    st.title("🛡️ Sistema SSO - Monitoramento")
    
    user_name = get_user_display_name()
    user_email = get_user_email()
    
    st.markdown("""
    <div style="text-align: center; padding: 2rem; background: #fff3cd; 
                border: 1px solid #ffeaa7; border-radius: 10px; margin: 2rem 0;">
        <h2>🚫 Acesso Restrito</h2>
        <p>Seu e-mail não está autorizado a acessar este sistema.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.warning(f"**Usuário:** {user_name}")
        st.warning(f"**E-mail:** {user_email}")
        
        st.markdown("---")
        
        st.error("""
        **Motivo do bloqueio:**
        - Seu e-mail não está cadastrado no sistema
        - Sua conta pode ter sido desativada
        - Você pode não ter as permissões necessárias
        """)
        
        st.markdown("---")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🔄 Tentar Novamente", use_container_width=True):
                st.rerun()
        
        with col_btn2:
            if st.button("🚪 Sair / Trocar de Conta", use_container_width=True):
                try:
                    st.logout()
                except Exception:
                    st.rerun()
        
        st.markdown("---")
        
        st.info("""
        **Solução:**
        - Entre em contato com o administrador do sistema
        - Solicite o cadastro do seu e-mail
        - Verifique se está usando a conta Google correta
        """)

def show_logout_button():
    """Botão de logout na sidebar."""
    with st.sidebar:
        st.markdown("---")
        if st.button("🚪 Sair do Sistema", use_container_width=True):
            try:
                st.logout()
            except Exception as e:
                st.error(f"Erro ao fazer logout: {str(e)}")
                # Limpa a sessão manualmente se necessário
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

def show_user_status():
    """Mostra status do usuário na sidebar."""
    from .auth_utils import get_user_info, get_user_role, is_admin, is_editor
    
    user_info = get_user_info()
    if user_info:
        with st.sidebar:
            st.markdown("### 👤 Usuário Logado")
            
            # Avatar e nome
            st.markdown(f"**{user_info.get('full_name', 'Usuário')}**")
            st.caption(user_info.get('email', ''))
            
            # Papel com cor
            role = get_user_role()
            if role == 'admin':
                st.markdown("🔴 **Administrador**")
            elif role == 'editor':
                st.markdown("🟡 **Editor**")
            else:
                st.markdown("🟢 **Visualizador**")
            
            # Permissões
            st.markdown("**Permissões:**")
            if is_admin():
                st.markdown("✅ Acesso total")
            elif is_editor():
                st.markdown("✅ Editar dados")
            else:
                st.markdown("✅ Visualizar dados")
            
            st.markdown("---")
