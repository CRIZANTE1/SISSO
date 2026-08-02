import streamlit as st
from .auth_utils import (
    get_user_display_name,
    get_user_email,
    extract_name_from_email,
    login_with_supabase,
    sign_up_with_supabase,
    logout_user,
)


def show_login_page():
    """Página de login: Google OIDC ou e-mail/senha (Supabase Auth)."""
    st.title("🛡️ Sistema SISSO - Monitoramento")
    st.subheader("Sistema de Gestão de Segurança e Saúde Ocupacional")

    st.markdown("""
    <div style="text-align: center; padding: 2rem; background: linear-gradient(90deg, #1f77b4 0%, #17a2b8 100%);
                border-radius: 10px; color: white; margin: 2rem 0;">
        <h2>🔐 Autenticação Obrigatória</h2>
        <p>Entre com Google ou com e-mail e senha para acessar o sistema.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### Acesso Seguro")
        st.markdown("""
        - ✅ **Google OAuth** ou **e-mail/senha**
        - ✅ **Controle de acesso baseado em papéis**
        - ✅ **Isolamento de dados por usuário**
        - ✅ **Sessões seguras**
        """)

        st.markdown("---")

        if st.button("🔗 Fazer Login com Google", type="primary", width='stretch'):
            try:
                st.login()
            except Exception as e:
                st.error(f"Erro ao iniciar login: {e}")

        st.markdown(
            "<p style='text-align:center;color:#666;margin:1rem 0;'>——— ou ———</p>",
            unsafe_allow_html=True,
        )

        tab_login, tab_signup = st.tabs(["Entrar com e-mail", "Criar conta"])

        with tab_login:
            with st.form("supabase_login_form"):
                email = st.text_input("E-mail", placeholder="seu@email.com")
                password = st.text_input("Senha", type="password")
                submitted = st.form_submit_button("Entrar", type="primary", width='stretch')
                if submitted:
                    ok, err = login_with_supabase(email, password)
                    if ok:
                        st.success("Login realizado!")
                        st.rerun()
                    else:
                        st.error(err)

        with tab_signup:
            st.caption(
                "A conta fica pendente até um administrador aprovar o acesso."
            )
            with st.form("supabase_signup_form"):
                full_name = st.text_input("Nome completo", placeholder="Seu nome")
                email_new = st.text_input("E-mail", key="signup_email", placeholder="seu@email.com")
                password_new = st.text_input(
                    "Senha",
                    type="password",
                    key="signup_password",
                    help="Mínimo de 6 caracteres",
                )
                password_confirm = st.text_input(
                    "Confirmar senha",
                    type="password",
                    key="signup_password_confirm",
                )
                signed = st.form_submit_button("Criar conta", type="primary", width='stretch')
                if signed:
                    if password_new != password_confirm:
                        st.error("As senhas não coincidem.")
                    else:
                        ok, msg = sign_up_with_supabase(email_new, password_new, full_name)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

        st.markdown("---")

        st.info("""
        **Instruções:**
        1. Entre com Google **ou** com e-mail e senha
        2. Se ainda não tiver cadastro aprovado, solicite acesso ou crie uma conta
        3. Aguarde a aprovação do administrador
        """)


def show_pending_approval_page():
    """Página para usuários com solicitação pendente de aprovação."""
    st.title("🛡️ Sistema SISSO - Monitoramento")

    user_name = get_user_display_name()
    user_email = get_user_email()
    user_info = st.session_state.get("user_info") or {}
    full_name = user_info.get("full_name") or user_name

    st.markdown("""
    <div style="text-align: center; padding: 2rem; background: #e7f3ff;
                border: 1px solid #b6d4fe; border-radius: 10px; margin: 2rem 0;">
        <h2>⏳ Aguardando Aprovação</h2>
        <p>Sua solicitação de acesso foi enviada e está sendo analisada.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info(f"**Nome:** {full_name}")
        st.info(f"**E-mail:** {user_email}")
        st.success(
            "Assim que o administrador aprovar, você poderá acessar o sistema "
            "com o mesmo método de login (Google ou e-mail/senha)."
        )

        st.markdown("---")
        if st.button("🚪 Sair / Trocar de Conta", width='stretch'):
            logout_user()


def show_access_denied_page():
    """Página para usuários não autorizados, com formulário de solicitação."""
    st.title("🛡️ Sistema SISSO - Monitoramento")

    user_name = get_user_display_name()
    user_email = get_user_email()

    st.markdown("""
    <div style="text-align: center; padding: 2rem; background: #fff3cd;
                border: 1px solid #ffeaa7; border-radius: 10px; margin: 2rem 0;">
        <h2>🚫 Acesso Restrito</h2>
        <p>Seu e-mail ainda não está autorizado a acessar este sistema.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.warning(f"**Usuário:** {user_name}")
        st.warning(f"**E-mail:** {user_email}")

        st.markdown("---")
        st.subheader("📝 Solicitar Acesso")
        st.caption("Preencha os dados abaixo. Um administrador analisará sua solicitação.")

        default_name = extract_name_from_email(user_email) if user_email else ""
        with st.form("access_request_form"):
            full_name = st.text_input(
                "Nome completo",
                value=default_name,
                placeholder="Seu nome completo",
            )
            st.text_input(
                "E-mail",
                value=user_email or "",
                disabled=True,
                help="O e-mail vem da sua conta de login e não pode ser alterado.",
            )
            submitted = st.form_submit_button("📨 Enviar Solicitação", type="primary", width='stretch')

            if submitted:
                if not user_email:
                    st.error("Não foi possível identificar seu e-mail. Faça login novamente.")
                elif not (full_name or "").strip():
                    st.error("Informe seu nome completo.")
                else:
                    _submit_access_request(user_email, full_name.strip())

        st.markdown("---")

        col_btn1, col_btn2 = st.columns(2)

        with col_btn1:
            if st.button("🔄 Tentar Novamente", width='stretch'):
                st.rerun()

        with col_btn2:
            if st.button("🚪 Sair / Trocar de Conta", width='stretch'):
                logout_user()


def _submit_access_request(email: str, full_name: str) -> None:
    """Cria (ou reativa) perfil com status pendente para aprovação do admin."""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            st.error("Erro ao conectar com o banco de dados. Tente novamente.")
            return

        email_norm = email.lower().strip()
        existing = (
            supabase.table("profiles")
            .select("id, status")
            .eq("email", email_norm)
            .execute()
        )

        if existing.data:
            status = (existing.data[0].get("status") or "").lower().strip()
            if status == "pendente":
                st.info("Você já possui uma solicitação pendente. Aguarde a aprovação do administrador.")
                st.session_state.pending_approval = True
                st.rerun()
                return
            if status == "ativo":
                st.success("Seu acesso já está ativo. Clique em \"Tentar Novamente\".")
                return

            # Reabre solicitação (ex.: estava inativo/rejeitado)
            result = (
                supabase.table("profiles")
                .update({
                    "full_name": full_name,
                    "status": "pendente",
                    "role": "viewer",
                    "plan": "trial",
                })
                .eq("email", email_norm)
                .execute()
            )
        else:
            result = (
                supabase.table("profiles")
                .insert({
                    "email": email_norm,
                    "full_name": full_name,
                    "role": "viewer",
                    "status": "pendente",
                    "plan": "trial",
                })
                .execute()
            )

        if result.data:
            st.success("✅ Solicitação enviada. Aguarde a aprovação do administrador.")
            st.session_state.pending_approval = True
            st.session_state.user_info = {
                "email": email_norm,
                "full_name": full_name,
                "role": "viewer",
                "status": "pendente",
                "pending_approval": True,
            }
            st.rerun()
        else:
            st.error("Não foi possível registrar a solicitação. Tente novamente.")
    except Exception as e:
        st.error(f"Erro ao enviar solicitação: {str(e)}")


def show_logout_button():
    """Botão de logout na sidebar."""
    with st.sidebar:
        st.markdown("---")
        if st.button("🚪 Sair do Sistema", width='stretch'):
            logout_user()


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
