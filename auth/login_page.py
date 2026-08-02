import html
import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

import streamlit as st
from streamlit_lottie import st_lottie

from .auth_utils import (
    get_user_display_name,
    get_user_email,
    extract_name_from_email,
    login_with_supabase,
    sign_up_with_supabase,
    logout_user,
)

_LOTTIE_PATH = Path(__file__).resolve().parent.parent / "assets" / "gradient_loader.json"


@lru_cache(maxsize=1)
def _load_login_lottie() -> Optional[dict]:
    """Carrega a animação Lottie do login."""
    try:
        with open(_LOTTIE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _render_login_lottie(key: str = "login_lottie") -> None:
    """Exibe o Lottie na coluna direita."""
    animation = _load_login_lottie()
    if not animation:
        return
    st_lottie(animation, height=340, key=key, loop=True, quality="high")


def _inject_login_css() -> None:
    """CSS e tipografia para as telas de autenticação (layout card minimalista)."""
    st.markdown(
        """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
    :root {
        --sisso-bg: #F8FAFC;
        --sisso-brand: #0F172A;
        --sisso-text: #1E293B;
        --sisso-muted: #64748B;
        --sisso-border: #E2E8F0;
        --sisso-accent: #2563EB;
        --sisso-accent-hover: #1D4ED8;
        --sisso-warn: #F59E0B;
        --sisso-card-max: 920px;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    #MainMenu,
    footer,
    header {
        display: none !important;
        visibility: hidden !important;
    }

    [data-testid="stSidebar"],
    [data-testid="stSidebarCollapsedControl"] {
        display: none !important;
    }

    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewContainer"] > .main {
        background: var(--sisso-bg) !important;
    }

    /* Card visual via container centralizado */
    .main .block-container {
        max-width: var(--sisso-card-max) !important;
        padding-top: 0 !important;
        padding-bottom: 1.5rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        margin-top: 4rem !important;
        margin-bottom: 3rem !important;
        background: #ffffff !important;
        border: 1px solid var(--sisso-border) !important;
        border-left: 3px solid var(--sisso-accent) !important;
        border-radius: 12px !important;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06), 0 8px 24px rgba(15, 23, 42, 0.04) !important;
        overflow: hidden !important;
    }

    .sisso-brand {
        background: transparent;
        color: var(--sisso-text);
        padding: 1.5rem 0 0.5rem 0;
        text-align: left;
        margin: 0;
    }

    .sisso-lottie-wrap {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 360px;
        padding: 1rem 0.5rem;
    }

    .sisso-lottie-wrap > div {
        width: 100%;
    }

    @media (max-width: 768px) {
        .sisso-lottie-wrap {
            min-height: 220px;
            padding: 0.5rem 0 1rem 0;
        }
    }

    .sisso-brand-mark {
        display: inline-flex;
        align-items: center;
        gap: 0.6rem;
        margin-bottom: 0.5rem;
    }

    .sisso-brand-name {
        font-size: 1.125rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        margin: 0;
        color: var(--sisso-brand);
    }

    .sisso-brand-title {
        font-size: 1.5rem;
        font-weight: 600;
        line-height: 1.25;
        margin: 0 0 0.35rem 0;
        color: var(--sisso-text);
    }

    .sisso-brand-sub {
        font-size: 0.8125rem;
        font-weight: 400;
        color: var(--sisso-muted);
        margin: 0;
        line-height: 1.4;
    }

    .sisso-status {
        display: flex;
        align-items: flex-start;
        gap: 0.85rem;
        margin: 1.25rem 0 1rem 0;
    }

    .sisso-status-icon {
        flex-shrink: 0;
        width: 40px;
        height: 40px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #EFF6FF;
    }

    .sisso-status-icon.warn {
        background: #FFFBEB;
    }

    .sisso-status-title {
        font-size: 1rem;
        font-weight: 600;
        color: var(--sisso-text);
        margin: 0 0 0.2rem 0;
    }

    .sisso-status-desc {
        font-size: 0.8125rem;
        color: var(--sisso-muted);
        margin: 0;
        line-height: 1.45;
    }

    .sisso-meta {
        background: var(--sisso-bg);
        border: 1px solid var(--sisso-border);
        border-radius: 8px;
        padding: 0.85rem 1rem;
        margin: 0 0 1rem 0;
    }

    .sisso-meta-row {
        display: flex;
        flex-direction: column;
        gap: 0.15rem;
        margin-bottom: 0.65rem;
    }

    .sisso-meta-row:last-child {
        margin-bottom: 0;
    }

    .sisso-meta-label {
        font-size: 0.6875rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--sisso-muted);
    }

    .sisso-meta-value {
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--sisso-text);
    }

    .sisso-hint {
        font-size: 0.8125rem;
        color: var(--sisso-muted);
        line-height: 1.45;
        margin: 0 0 0.75rem 0;
    }

    .sisso-divider {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin: 0.85rem 0 0.5rem 0;
        color: var(--sisso-muted);
        font-size: 0.75rem;
        font-weight: 500;
    }

    .sisso-divider::before,
    .sisso-divider::after {
        content: "";
        flex: 1;
        height: 1px;
        background: var(--sisso-border);
    }

    .sisso-section-label {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--sisso-text);
        margin: 0.25rem 0 0.25rem 0;
    }

    .sisso-spacer-top {
        height: 1.25rem;
    }

    /* Inputs */
    .stTextInput label,
    [data-testid="stTextInput"] label,
    [data-testid="stWidgetLabel"] p {
        font-size: 0.8125rem !important;
        font-weight: 500 !important;
        color: var(--sisso-text) !important;
    }

    [data-testid="stTextInput"] input {
        border-radius: 8px !important;
        border: 1px solid var(--sisso-border) !important;
        font-size: 0.875rem !important;
        padding: 0.55rem 0.75rem !important;
        color: var(--sisso-text) !important;
    }

    [data-testid="stTextInput"] input:focus {
        border-color: var(--sisso-accent) !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
    }

    /* Botões primários */
    .stButton > button[kind="primary"],
    .stFormSubmitButton > button[kind="primary"],
    button[data-testid="baseButton-primary"],
    button[kind="primary"] {
        background: var(--sisso-accent) !important;
        border: 1px solid var(--sisso-accent) !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        padding: 0.55rem 1rem !important;
        min-height: 2.5rem !important;
        box-shadow: none !important;
    }

    .stButton > button[kind="primary"]:hover,
    .stFormSubmitButton > button[kind="primary"]:hover,
    button[data-testid="baseButton-primary"]:hover,
    button[kind="primary"]:hover {
        background: var(--sisso-accent-hover) !important;
        border-color: var(--sisso-accent-hover) !important;
    }

    /* Botões secundários / outline */
    .stButton > button[kind="secondary"],
    button[data-testid="baseButton-secondary"],
    button[kind="secondary"] {
        background: #ffffff !important;
        border: 1px solid var(--sisso-border) !important;
        color: var(--sisso-text) !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        padding: 0.55rem 1rem !important;
        min-height: 2.5rem !important;
        box-shadow: none !important;
    }

    .stButton > button[kind="secondary"]:hover,
    button[data-testid="baseButton-secondary"]:hover,
    button[kind="secondary"]:hover {
        border-color: #CBD5E1 !important;
        background: var(--sisso-bg) !important;
    }

    /* Tabs limpas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0 !important;
        border-bottom: 1px solid var(--sisso-border) !important;
        background: transparent !important;
    }

    .stTabs [data-baseweb="tab"] {
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        color: var(--sisso-muted) !important;
        padding: 0.65rem 1rem !important;
        border-radius: 0 !important;
    }

    .stTabs [aria-selected="true"] {
        color: var(--sisso-accent) !important;
    }

    .stTabs [data-baseweb="tab-highlight"] {
        background-color: var(--sisso-accent) !important;
    }

    .stTabs [data-baseweb="tab-border"] {
        display: none !important;
    }

    .stCaption, [data-testid="stCaptionContainer"] {
        font-size: 0.75rem !important;
        color: var(--sisso-muted) !important;
    }

    [data-testid="stAlert"] {
        border-radius: 8px !important;
        font-size: 0.8125rem !important;
    }
</style>
        """,
        unsafe_allow_html=True,
    )


def _render_brand_header(subtitle: str = "Gestão de Segurança e Saúde Ocupacional") -> None:
    """Cabeçalho escuro do card (bloco HTML autocontido)."""
    st.markdown(
        f"""
<div class="sisso-brand">
  <div class="sisso-brand-mark">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <path d="M12 3l7 3v5c0 4.5-3 8.2-7 9.5C8 19.2 5 15.5 5 11V6l7-3z" stroke="#2563EB" stroke-width="1.75" fill="none"/>
      <path d="M9.5 12.2l1.8 1.8 3.7-4" stroke="#3B82F6" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    <p class="sisso-brand-name">SISSO</p>
  </div>
  <p class="sisso-brand-title">Monitoramento</p>
  <p class="sisso-brand-sub">{subtitle}</p>
</div>
        """,
        unsafe_allow_html=True,
    )


def show_login_page():
    """Página de login: Google OIDC ou e-mail/senha (Supabase Auth)."""
    _inject_login_css()

    col_left, col_right = st.columns([1.05, 0.95], gap="large")

    with col_left:
        _render_brand_header()
        st.markdown('<div class="sisso-spacer-top"></div>', unsafe_allow_html=True)

        if st.button("Entrar com Google", type="secondary", width="stretch"):
            try:
                st.login()
            except Exception as e:
                st.error(f"Erro ao iniciar login: {e}")

        st.markdown('<div class="sisso-divider">ou</div>', unsafe_allow_html=True)

        tab_login, tab_signup = st.tabs(["Entrar", "Criar conta"])

        with tab_login:
            with st.form("supabase_login_form"):
                email = st.text_input("E-mail", placeholder="seu@email.com")
                password = st.text_input("Senha", type="password")
                submitted = st.form_submit_button("Entrar", type="primary", width="stretch")
                if submitted:
                    ok, err = login_with_supabase(email, password)
                    if ok:
                        st.success("Login realizado.")
                        st.rerun()
                    else:
                        st.error(err)

        with tab_signup:
            st.caption("A conta fica pendente até um administrador aprovar o acesso.")
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
                signed = st.form_submit_button("Criar conta", type="primary", width="stretch")
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

    with col_right:
        _render_login_lottie(key="login_lottie")


def show_pending_approval_page():
    """Página para usuários com solicitação pendente de aprovação."""
    _inject_login_css()

    user_name = get_user_display_name()
    user_email = get_user_email()
    user_info = st.session_state.get("user_info") or {}
    full_name = html.escape(str(user_info.get("full_name") or user_name or ""))
    email_safe = html.escape(str(user_email or "—"))

    col_left, col_right = st.columns([1.05, 0.95], gap="large")

    with col_left:
        _render_brand_header()
        st.markdown(
            f"""
<div class="sisso-status">
  <div class="sisso-status-icon">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <circle cx="12" cy="12" r="8.25" stroke="#2563EB" stroke-width="1.75"/>
      <path d="M12 8v4.2l2.8 1.6" stroke="#2563EB" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  </div>
  <div>
    <p class="sisso-status-title">Aguardando aprovação</p>
    <p class="sisso-status-desc">Sua solicitação foi enviada e está sendo analisada por um administrador.</p>
  </div>
</div>
<div class="sisso-meta">
  <div class="sisso-meta-row">
    <span class="sisso-meta-label">Nome</span>
    <span class="sisso-meta-value">{full_name}</span>
  </div>
  <div class="sisso-meta-row">
    <span class="sisso-meta-label">E-mail</span>
    <span class="sisso-meta-value">{email_safe}</span>
  </div>
</div>
<p class="sisso-hint">Assim que o acesso for aprovado, entre novamente com Google ou e-mail e senha.</p>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Sair / Trocar de conta", type="secondary", width="stretch"):
            logout_user()

    with col_right:
        _render_login_lottie(key="pending_lottie")


def show_access_denied_page():
    """Página para usuários não autorizados, com formulário de solicitação."""
    _inject_login_css()

    user_name = html.escape(str(get_user_display_name() or ""))
    user_email = get_user_email()
    email_safe = html.escape(str(user_email or "—"))

    col_left, col_right = st.columns([1.05, 0.95], gap="large")

    with col_left:
        _render_brand_header()
        st.markdown(
            f"""
<div class="sisso-status">
  <div class="sisso-status-icon warn">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <path d="M12 4.5L21 20H3L12 4.5z" stroke="#F59E0B" stroke-width="1.75" stroke-linejoin="round"/>
      <path d="M12 10v4.5M12 17.2v.3" stroke="#F59E0B" stroke-width="1.75" stroke-linecap="round"/>
    </svg>
  </div>
  <div>
    <p class="sisso-status-title">Acesso restrito</p>
    <p class="sisso-status-desc">Este e-mail ainda não está autorizado. Solicite acesso abaixo.</p>
  </div>
</div>
<div class="sisso-meta">
  <div class="sisso-meta-row">
    <span class="sisso-meta-label">Usuário</span>
    <span class="sisso-meta-value">{user_name}</span>
  </div>
  <div class="sisso-meta-row">
    <span class="sisso-meta-label">E-mail</span>
    <span class="sisso-meta-value">{email_safe}</span>
  </div>
</div>
<p class="sisso-section-label">Solicitar acesso</p>
<p class="sisso-hint">Preencha os dados. Um administrador analisará sua solicitação.</p>
            """,
            unsafe_allow_html=True,
        )

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
            submitted = st.form_submit_button("Enviar solicitação", type="primary", width="stretch")

            if submitted:
                if not user_email:
                    st.error("Não foi possível identificar seu e-mail. Faça login novamente.")
                elif not (full_name or "").strip():
                    st.error("Informe seu nome completo.")
                else:
                    _submit_access_request(user_email, full_name.strip())

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Tentar novamente", type="secondary", width="stretch"):
                st.rerun()
        with col_btn2:
            if st.button("Sair / Trocar de conta", type="secondary", width="stretch"):
                logout_user()

    with col_right:
        _render_login_lottie(key="denied_lottie")

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
                st.success('Seu acesso já está ativo. Clique em "Tentar novamente".')
                return

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
            st.success("Solicitação enviada. Aguarde a aprovação do administrador.")
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
        if st.button("Sair do sistema", width="stretch"):
            logout_user()


def show_user_status():
    """Mostra status do usuário na sidebar."""
    from .auth_utils import get_user_info, get_user_role, is_admin, is_editor

    user_info = get_user_info()
    if user_info:
        with st.sidebar:
            st.markdown("### Usuário logado")

            st.markdown(f"**{user_info.get('full_name', 'Usuário')}**")
            st.caption(user_info.get("email", ""))

            role = get_user_role()
            if role == "admin":
                st.markdown("**Administrador**")
            elif role == "editor":
                st.markdown("**Editor**")
            else:
                st.markdown("**Visualizador**")

            st.markdown("**Permissões:**")
            if is_admin():
                st.markdown("Acesso total")
            elif is_editor():
                st.markdown("Editar dados")
            else:
                st.markdown("Visualizar dados")

            st.markdown("---")
