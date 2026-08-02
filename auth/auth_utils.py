import streamlit as st
import re
from managers.supabase_config import get_supabase_client
from typing import Optional, Dict, Any, Tuple
from utils.simple_logger import get_logger

_SUPABASE_SESSION_KEYS = (
    "auth_provider",
    "supabase_user",
    "supabase_access_token",
    "supabase_refresh_token",
)


def is_oidc_available():
    """Verifica se o login OIDC está configurado."""
    return hasattr(st, 'user') and hasattr(st.user, 'is_logged_in')


def is_oidc_logged_in() -> bool:
    """True se autenticado via Google OIDC (Streamlit)."""
    return is_oidc_available() and bool(st.user.is_logged_in)


def is_supabase_logged_in() -> bool:
    """True se autenticado via Supabase Auth (e-mail/senha)."""
    return st.session_state.get("auth_provider") == "supabase" and bool(
        st.session_state.get("supabase_user")
        and st.session_state.get("supabase_access_token")
    )


def is_user_logged_in() -> bool:
    """Verifica se o usuário está logado via OIDC ou Supabase Auth."""
    return is_oidc_logged_in() or is_supabase_logged_in()


def _store_supabase_session(session) -> None:
    """Persiste tokens e usuário Supabase no session_state."""
    user = session.user
    st.session_state.auth_provider = "supabase"
    st.session_state.supabase_user = {
        "id": getattr(user, "id", None),
        "email": (getattr(user, "email", None) or "").lower().strip(),
        "user_metadata": getattr(user, "user_metadata", None) or {},
    }
    st.session_state.supabase_access_token = session.access_token
    st.session_state.supabase_refresh_token = session.refresh_token


def restore_supabase_session() -> bool:
    """Restaura sessão Supabase a partir dos tokens salvos (entre reruns)."""
    if is_oidc_logged_in():
        return False

    access = st.session_state.get("supabase_access_token")
    refresh = st.session_state.get("supabase_refresh_token")
    if not access or not refresh:
        return False

    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        response = supabase.auth.set_session(access, refresh)
        session = getattr(response, "session", None) or response
        if getattr(session, "access_token", None):
            _store_supabase_session(session)
            return True
    except Exception as e:
        get_logger().warning(f"Falha ao restaurar sessão Supabase: {e}")
        for key in _SUPABASE_SESSION_KEYS:
            st.session_state.pop(key, None)
    return False


def login_with_supabase(email: str, password: str) -> Tuple[bool, str]:
    """
    Login com e-mail/senha via Supabase Auth.
    Retorna (sucesso, mensagem_erro_ou_vazia).
    """
    logger = get_logger()
    email_norm = (email or "").lower().strip()
    if not email_norm or not password:
        return False, "Informe e-mail e senha."

    try:
        supabase = get_supabase_client()
        if not supabase:
            return False, "Erro de conexão com o serviço de autenticação."

        response = supabase.auth.sign_in_with_password({
            "email": email_norm,
            "password": password,
        })
        session = getattr(response, "session", None)
        if not session or not getattr(session, "user", None):
            return False, "Não foi possível iniciar a sessão. Verifique e-mail e senha."

        _store_supabase_session(session)
        # Limpa autenticação de app anterior para forçar revalidação em profiles
        for key in ("authenticated_user_email", "user_info", "user_id", "role", "pending_approval"):
            st.session_state.pop(key, None)
        logger.info(f"Login Supabase OK: {email_norm}")
        return True, ""
    except Exception as e:
        msg = str(e).lower()
        logger.warning(f"Falha login Supabase ({email_norm}): {e}")
        if "invalid login" in msg or "invalid credentials" in msg:
            return False, "E-mail ou senha inválidos."
        if "email not confirmed" in msg or "not confirmed" in msg:
            return False, "E-mail ainda não confirmado. Verifique sua caixa de entrada."
        return False, f"Erro ao fazer login: {e}"


def sign_up_with_supabase(email: str, password: str, full_name: str) -> Tuple[bool, str]:
    """
    Cria conta no Supabase Auth e perfil pendente em profiles.
    Retorna (sucesso, mensagem).
    """
    logger = get_logger()
    email_norm = (email or "").lower().strip()
    name = (full_name or "").strip() or extract_name_from_email(email_norm)

    if not email_norm or not password:
        return False, "Informe e-mail e senha."
    if len(password) < 6:
        return False, "A senha deve ter pelo menos 6 caracteres."

    try:
        supabase = get_supabase_client()
        if not supabase:
            return False, "Erro de conexão com o serviço de autenticação."

        response = supabase.auth.sign_up({
            "email": email_norm,
            "password": password,
            "options": {"data": {"full_name": name}},
        })
        user = getattr(response, "user", None)
        session = getattr(response, "session", None)

        if not user:
            return False, "Não foi possível criar a conta. Tente outro e-mail."

        # Perfil pendente (service role para bypass RLS)
        from managers.supabase_config import get_service_role_client
        admin = get_service_role_client()
        if admin:
            existing = (
                admin.table("profiles")
                .select("id, status")
                .eq("email", email_norm)
                .execute()
            )
            if existing.data:
                status = (existing.data[0].get("status") or "").lower()
                if status != "ativo":
                    admin.table("profiles").update({
                        "full_name": name,
                        "status": "pendente",
                        "role": "viewer",
                        "plan": "trial",
                    }).eq("email", email_norm).execute()
            else:
                admin.table("profiles").insert({
                    "email": email_norm,
                    "full_name": name,
                    "role": "viewer",
                    "status": "pendente",
                    "plan": "trial",
                }).execute()

        if session and getattr(session, "user", None):
            _store_supabase_session(session)
            for key in ("authenticated_user_email", "user_info", "user_id", "role"):
                st.session_state.pop(key, None)
            st.session_state.pending_approval = True
            return True, "Conta criada. Aguarde a aprovação do administrador."

        return True, (
            "Conta criada. Se o projeto exigir confirmação de e-mail, "
            "verifique sua caixa de entrada e depois faça login. "
            "O acesso ao sistema depende da aprovação do administrador."
        )
    except Exception as e:
        msg = str(e).lower()
        logger.warning(f"Falha sign_up Supabase ({email_norm}): {e}")
        if "already registered" in msg or "already been registered" in msg or "user already" in msg:
            return False, "Este e-mail já está cadastrado. Use Entrar ou recupere a senha."
        return False, f"Erro ao criar conta: {e}"


def get_user_email() -> Optional[str]:
    """Retorna o e-mail do usuário logado (OIDC ou Supabase)."""
    if is_oidc_logged_in() and hasattr(st.user, "email") and st.user.email:
        return st.user.email.lower().strip()
    if is_supabase_logged_in():
        email = (st.session_state.get("supabase_user") or {}).get("email")
        if email:
            return email.lower().strip()
    return None


def get_user_display_name() -> str:
    """Retorna o nome de exibição do usuário."""
    if is_oidc_logged_in() and hasattr(st.user, "name") and st.user.name:
        return st.user.name
    if is_supabase_logged_in():
        user = st.session_state.get("supabase_user") or {}
        meta = user.get("user_metadata") or {}
        name = meta.get("full_name") or meta.get("name")
        if name:
            return name
        info = st.session_state.get("user_info") or {}
        if info.get("full_name"):
            return info["full_name"]
    return get_user_email() or "Usuário Desconhecido"


def extract_name_from_email(email: str) -> str:
    """
    Extrai e formata o nome a partir do email.
    Exemplo: 'joao.silva@gmail.com' -> 'Joao Silva'
    """
    if not email:
        return ""

    # Pega a parte antes do @
    username = email.split('@')[0].strip()

    # Substitui pontos, underscores, traços e números por espaços
    name_parts = re.sub(r'[._\-0-9]+', ' ', username).split()

    # Capitaliza cada palavra e junta com espaços
    formatted_name = ' '.join([part.capitalize() for part in name_parts if part])

    return formatted_name if formatted_name else username.capitalize()


def authenticate_user() -> bool:
    """Verifica o usuário na base de dados."""
    user_email = get_user_email()
    if not user_email:
        return False

    # Verifica se já está autenticado na sessão
    if st.session_state.get('authenticated_user_email') == user_email:
        # Verifica o status do trial para sessões existentes (não bloqueia admins ou planos ilimitados)
        try:
            from services.trial_manager import check_trial_status
            trial_info = check_trial_status(user_email)

            # Não bloqueia se tiver acesso ilimitado
            if trial_info.get('unlimited_access', False):
                pass  # Continua normalmente
            elif trial_info.get('is_trial_expired', False) and trial_info.get('has_trial', False):
                # Se o trial expirou, encerra a sessão
                st.error("Seu período de trial expirou.")
                return False
        except:
            pass  # Se não tiver o trial manager, continua normalmente
        return True

    # Busca informações do usuário na base de dados
    user_info = check_user_in_database(user_email)

    if not user_info:
        return False

    # Solicitação ainda aguardando aprovação
    if user_info.get("pending_approval"):
        st.session_state.pending_approval = True
        st.session_state.user_info = user_info
        st.session_state.authenticated_user_email = None
        return False

    # Verifica o status do trial (não bloqueia admins ou planos ilimitados)
    try:
        from services.trial_manager import check_trial_status
        trial_info = check_trial_status(user_email)

        # Não bloqueia se tiver acesso ilimitado
        if trial_info.get('unlimited_access', False):
            pass  # Continua normalmente
        elif trial_info.get('is_trial_expired', False) and trial_info.get('has_trial', False):
            st.error("Seu período de trial expirou.")
            return False
    except:
        pass  # Se não tiver o trial manager, continua normalmente

    # Salva informações do usuário na sessão
    st.session_state.pending_approval = False
    st.session_state.user_info = user_info
    st.session_state.role = user_info.get('role', 'viewer')
    st.session_state.authenticated_user_email = user_email
    st.session_state.user_id = user_info.get('id')

    return True


def require_login():
    """Middleware que exige autenticação para acessar a página."""
    restore_supabase_session()

    if not is_user_logged_in():
        from auth.login_page import show_login_page
        show_login_page()
        st.stop()

    if not authenticate_user():
        from auth.login_page import show_access_denied_page, show_pending_approval_page
        if st.session_state.get("pending_approval"):
            show_pending_approval_page()
        else:
            show_access_denied_page()
        st.stop()

    # Verifica status do trial após autenticação (não bloqueia admins ou planos ilimitados)
    try:
        from services.trial_manager import check_trial_status
        user_email = get_user_email()
        if user_email:
            trial_info = check_trial_status(user_email)

            # Não bloqueia se tiver acesso ilimitado
            if trial_info.get('unlimited_access', False):
                pass  # Continua normalmente
            elif trial_info.get('is_trial_expired', False) and trial_info.get('has_trial', False):
                from services.trial_manager import show_trial_expired_page
                show_trial_expired_page()
                st.stop()
    except ImportError:
        pass  # Se não tiver o trial manager, continua normalmente


def check_user_in_database(email: str) -> Optional[Dict[str, Any]]:
    """Verifica se o usuário existe na base de dados e retorna suas informações."""
    logger = get_logger()
    try:
        logger.info(f"Verificando usuário na base de dados: {email}")

        # Usa sempre Service Role para evitar problemas de RLS
        logger.info("Usando Service Role para verificação de usuário")
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()

        if not supabase:
            logger.error("Cliente Supabase Service Role não disponível")
            st.error("Erro de conexão com o banco de dados. Tente novamente.")
            return None

        # Busca perfil do usuário
        logger.info(f"Executando query para buscar perfil: {email}")
        response = supabase.table("profiles").select("*").eq("email", email).execute()

        logger.info(f"Resposta da query: {response}")
        logger.info(f"Dados retornados: {response.data if hasattr(response, 'data') else 'N/A'}")

        if response.data and len(response.data) > 0:
            profile = response.data[0]
            status = (profile.get("status") or "").lower().strip()
            logger.info(f"Perfil encontrado para {email}: role={profile.get('role', 'viewer')}, status={status}")

            # Solicitação aguardando aprovação do administrador
            if status == "pendente":
                return {
                    "id": profile.get("id"),
                    "email": profile.get("email", email),
                    "full_name": profile.get("full_name", ""),
                    "role": profile.get("role", "viewer"),
                    "status": "pendente",
                    "pending_approval": True,
                }

            # Conta desativada ou rejeitada
            if status in ("inativo", "rejeitado"):
                logger.warning(f"Usuário {email} com status '{status}' — acesso negado")
                return None

            return {
                "id": profile.get("id"),
                "email": profile.get("email", email),
                "full_name": profile.get("full_name", ""),
                "role": profile.get("role", "viewer"),
                "status": status or "ativo",
            }

        # Sem perfil: não cria automaticamente — usuário deve solicitar acesso
        logger.info(f"Usuário {email} não encontrado em profiles — acesso depende de solicitação/aprovação")

        # FUNÇÃO DE EMERGÊNCIA: Se for o email específico do admin, tenta criar perfil
        if email == 'bboycrysforever@gmail.com':
            logger.warning("Tentativa de acesso do admin principal - criando perfil de emergência")
            try:
                # Tenta criar perfil admin de emergência
                profile_data = {
                    "email": email,
                    "full_name": "Cristian Ferreira",
                    "role": "admin",
                    "status": "ativo",
                    "plan": "dev_ilimitado",
                }

                logger.info(f"Criando perfil de emergência para {email}")
                response = supabase.table("profiles").insert(profile_data).execute()

                if response.data:
                    logger.info(f"Perfil de emergência criado com sucesso para {email}")
                    # Retorna o UUID do perfil criado
                    profile = response.data[0]
                    return {
                        "id": profile.get("id"),
                        "email": email,
                        "full_name": "Cristian Ferreira",
                        "role": "admin",
                        "status": "ativo",
                    }
                else:
                    logger.error("Falha ao criar perfil de emergência")
            except Exception as emergency_error:
                logger.error(f"Erro ao criar perfil de emergência: {emergency_error}")
                # Se for erro de chave duplicada, significa que o perfil já existe
                if "duplicate key value violates unique constraint" in str(emergency_error):
                    logger.info("Perfil já existe, tentando buscar dados existentes")
                    try:
                        existing_profile = supabase.table("profiles").select("*").eq("email", email).execute()
                        if existing_profile.data and len(existing_profile.data) > 0:
                            profile = existing_profile.data[0]
                            logger.info(f"Perfil encontrado após erro de duplicação: {email}")
                            return {
                                "id": profile.get("id"),
                                "email": profile.get("email", email),
                                "full_name": profile.get("full_name", "Cristian Ferreira"),
                                "role": profile.get("role", "admin"),
                                "status": profile.get("status", "ativo"),
                            }
                    except Exception as fallback_error:
                        logger.error(f"Erro ao buscar perfil existente: {fallback_error}")

        return None

    except Exception as e:
        logger.error(f"Erro ao verificar usuário na base de dados: {str(e)}")
        st.error(f"Erro ao verificar usuário na base de dados: {str(e)}")
        return None


def create_user_profile(email: str) -> Optional[Dict[str, Any]]:
    """Cria um novo perfil de usuário - APENAS para administradores."""
    logger = get_logger()
    logger.warning(f"Tentativa de criação de perfil para {email} - função desabilitada para criação automática")
    return None


def get_user_role() -> str:
    """Retorna o papel do usuário."""
    return st.session_state.get('role', 'viewer')


def is_admin() -> bool:
    """Verifica se o usuário é admin."""
    return get_user_role() == 'admin'


def is_editor() -> bool:
    """Verifica se o usuário é editor ou admin."""
    role = get_user_role()
    return role in ['admin', 'editor']


def can_edit() -> bool:
    """Verifica se o usuário pode editar."""
    return is_editor()


def check_permission(level: str = 'editor'):
    """Verifica permissões e bloqueia se necessário."""
    if level == 'admin' and not is_admin():
        st.error("❌ Acesso restrito a Administradores.")
        st.stop()
    elif level == 'editor' and not can_edit():
        st.error("❌ Você não tem permissão para editar.")
        st.stop()


def get_user_id() -> Optional[str]:
    """Retorna o ID do usuário atual."""
    return st.session_state.get('user_id')


def get_user_info() -> Optional[Dict[str, Any]]:
    """Retorna informações completas do usuário."""
    return st.session_state.get('user_info')


def _clear_app_session_keys() -> None:
    """Remove chaves de autenticação do app e da sessão Supabase."""
    keys = list(st.session_state.keys())
    for key in keys:
        if key.startswith("user_") or key in (
            "authenticated_user_email",
            "role",
            "user_id",
            "user_info",
            "pending_approval",
            *_SUPABASE_SESSION_KEYS,
        ):
            del st.session_state[key]


def logout_user():
    """Faz logout do usuário (OIDC e/ou Supabase) e limpa a sessão."""
    was_oidc = is_oidc_logged_in()
    was_supabase = is_supabase_logged_in() or bool(st.session_state.get("supabase_access_token"))

    try:
        if was_supabase:
            try:
                supabase = get_supabase_client()
                if supabase:
                    supabase.auth.sign_out()
            except Exception as sign_out_err:
                get_logger().warning(f"Erro ao fazer sign_out Supabase: {sign_out_err}")

        _clear_app_session_keys()

        if was_oidc:
            try:
                st.logout()
                return
            except Exception:
                pass

        st.rerun()
    except Exception as e:
        st.error(f"Erro ao fazer logout: {str(e)}")
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


def show_user_info():
    """Mostra informações do usuário logado na sidebar."""
    user_info = get_user_info()
    if user_info:
        with st.sidebar:
            st.markdown("---")
            st.markdown(f"**Usuário:** {user_info.get('full_name', 'N/A')}")
            st.markdown(f"**Papel:** {user_info.get('role', 'viewer').title()}")

            if st.button("🚪 Logout"):
                logout_user()
