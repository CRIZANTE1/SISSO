import streamlit as st
from managers.supabase_config import get_supabase_client
from typing import Optional, Dict, Any
from utils.simple_logger import get_logger

def is_oidc_available():
    """Verifica se o login OIDC está configurado."""
    return hasattr(st, 'user') and hasattr(st.user, 'is_logged_in')

def is_user_logged_in():
    """Verifica se o usuário está logado via OIDC."""
    return is_oidc_available() and st.user.is_logged_in

def get_user_email() -> Optional[str]:
    """Retorna o e-mail do usuário logado."""
    if is_user_logged_in() and hasattr(st.user, 'email'):
        return st.user.email.lower().strip()
    return None

def get_user_display_name() -> str:
    """Retorna o nome de exibição do usuário."""
    if is_user_logged_in() and hasattr(st.user, 'name'):
        return st.user.name
    return get_user_email() or "Usuário Desconhecido"

def authenticate_user() -> bool:
    """Verifica o usuário na base de dados."""
    user_email = get_user_email()
    if not user_email:
        return False

    # Verifica se já está autenticado na sessão
    if st.session_state.get('authenticated_user_email') == user_email:
        # Verifica o status do trial para sessões existentes
        try:
            from services.trial_manager import check_trial_status
            trial_info = check_trial_status(user_email)
            if trial_info.get('is_trial_expired', False) and trial_info.get('has_trial', False):
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

    # Verifica o status do trial
    try:
        from services.trial_manager import check_trial_status
        trial_info = check_trial_status(user_email)
        
        if trial_info.get('is_trial_expired', False) and trial_info.get('has_trial', False):
            st.error("Seu período de trial expirou.")
            return False
    except:
        pass  # Se não tiver o trial manager, continua normalmente

    # Salva informações do usuário na sessão
    st.session_state.user_info = user_info
    st.session_state.role = user_info.get('role', 'viewer')
    st.session_state.authenticated_user_email = user_email
    st.session_state.user_id = user_info.get('id')
    
    return True

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
            logger.info(f"Perfil encontrado para {email}: role={profile.get('role', 'viewer')}")
            return {
                "id": profile["email"],  # Usa email como ID
                "email": profile.get("email", email),
                "full_name": profile.get("full_name", ""),
                "role": profile.get("role", "viewer")
            }
        
        # Se não encontrou perfil, tenta criar automaticamente com trial de 14 dias
        logger.info(f"Usuário {email} não encontrado, criando perfil com trial automático")
        
        try:
            # Importa o trial manager e cria usuário com trial
            from services.trial_manager import create_new_trial_user
            trial_info = create_new_trial_user(email)
            
            if trial_info.get('new_user'):
                logger.info(f"Usuário de trial criado com sucesso: {email}")
                st.success("Bem-vindo! Você tem 14 dias de acesso gratuito ao sistema.")
                
                return {
                    "id": email,
                    "email": email,
                    "full_name": "",
                    "role": "viewer"
                }
            else:
                logger.warning(f"Falha ao criar usuário de trial para: {email}")
                # Ainda tenta encontrar o perfil mesmo que tenha falhado a criação
                response = supabase.table("profiles").select("*").eq("email", email).execute()
                if response.data and len(response.data) > 0:
                    profile = response.data[0]
                    return {
                        "id": profile["email"],
                        "email": profile.get("email", email),
                        "full_name": profile.get("full_name", ""),
                        "role": profile.get("role", "viewer")
                    }
        
        except ImportError:
            logger.warning("Trial manager não disponível, usando comportamento padrão")
        
        # Debug: lista todos os emails na tabela profiles
        try:
            all_profiles = supabase.table("profiles").select("email, role").execute()
            if all_profiles.data:
                logger.info(f"Emails cadastrados no sistema: {[p.get('email') for p in all_profiles.data]}")
            else:
                logger.warning("Tabela profiles está vazia")
        except Exception as debug_error:
            logger.error(f"Erro ao listar perfis para debug: {debug_error}")
        
        # FUNÇÃO DE EMERGÊNCIA: Se for o email específico do admin, tenta criar perfil
        if email == 'bboycrysforever@gmail.com':
            logger.warning("Tentativa de acesso do admin principal - criando perfil de emergência")
            try:
                # Tenta criar perfil admin de emergência
                profile_data = {
                    "email": email,
                    "full_name": "Cristian Ferreira",
                    "role": "admin",
                    "status": "ativo"
                }
                
                logger.info(f"Criando perfil de emergência para {email}")
                response = supabase.table("profiles").insert(profile_data).execute()
                
                if response.data:
                    logger.info(f"Perfil de emergência criado com sucesso para {email}")
                    return {
                        "id": email,
                        "email": email,
                        "full_name": "Cristian Ferreira",
                        "role": "admin"
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
                                "id": email,
                                "email": profile.get("email", email),
                                "full_name": profile.get("full_name", "Cristian Ferreira"),
                                "role": profile.get("role", "admin")
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

def logout_user():
    """Faz logout do usuário e limpa a sessão."""
    try:
        # Limpa dados da sessão
        for key in list(st.session_state.keys()):
            if key.startswith('user_') or key in ['authenticated_user_email', 'role', 'user_id', 'user_info']:
                del st.session_state[key]
        
        # Chama logout do Streamlit
        st.logout()
        
    except Exception as e:
        st.error(f"Erro ao fazer logout: {str(e)}")
        # Força limpeza da sessão
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

def require_login():
    """Middleware que exige autenticação para acessar a página."""
    if not is_user_logged_in():
        from auth.login_page import show_login_page
        show_login_page()
        st.stop()
    
    if not authenticate_user():
        from auth.login_page import show_access_denied_page
        show_access_denied_page()
        st.stop()
    
    # Verifica status do trial após autenticação
    try:
        from services.trial_manager import check_trial_status
        user_email = get_user_email()
        if user_email:
            trial_info = check_trial_status(user_email)
            if trial_info.get('is_trial_expired', False) and trial_info.get('has_trial', False):
                from services.trial_manager import show_trial_expired_page
                show_trial_expired_page()
                st.stop()
    except ImportError:
        pass  # Se não tiver o trial manager, continua normalmente

def show_user_info():
    """Mostra informações do usuário logado na sidebar."""
    user_info = get_user_info()
    if user_info:
        with st.sidebar:
            st.markdown("---")
            st.markdown(f"**Usuário:** {user_info.get('full_name', 'N/A')}")
            st.markdown(f"**E-mail:** {user_info.get('email', 'N/A')}")
            st.markdown(f"**Papel:** {user_info.get('role', 'viewer').title()}")
            
            if st.button("🚪 Logout"):
                logout_user()
