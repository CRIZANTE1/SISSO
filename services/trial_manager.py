"""
Serviço para gerenciamento de trial de 14 dias para novos usuários
"""
import streamlit as st
from managers.supabase_config import get_service_role_client
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import pytz

def check_trial_status(email: str) -> Dict[str, Any]:
    """
    Verifica o status de trial do usuário
    Retorna informações sobre trial, expiração e acesso
    """
    try:
        supabase = get_service_role_client()
        if not supabase:
            return {
                "has_trial": False,
                "is_trial_expired": True,
                "trial_expires_at": None,
                "error": "Erro de conexão com o banco de dados"
            }
        
        # Busca o perfil do usuário
        response = supabase.table("profiles").select("*").eq("email", email).execute()
        
        if not response.data:
            # Usuário não existe, vamos criar com trial
            return create_new_trial_user(email)
        
        profile = response.data[0]
        
        # Verifica se o usuário é novo comparando created_at com a data atual
        # se foi criado há menos de 14 dias, ainda está em trial
        created_at_str = profile.get("created_at")
        status = profile.get("status", "inativo")  # 'ativo' ou 'inativo'
        role = profile.get("role", "viewer")
        
        # Converte created_at para datetime
        if created_at_str:
            if isinstance(created_at_str, str):
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            else:
                created_at = created_at_str
            
            # Calcula a data de expiração do trial (14 dias após criação)
            trial_expires_at = created_at + timedelta(days=14)
            
            # Verifica se o trial expirou
            now = datetime.now(pytz.UTC)
            is_trial_expired = trial_expires_at < now
            has_trial = not is_trial_expired  # Tem trial se ainda não expirou
            
            # Considera ativo se o status for 'ativo' e o trial não tiver expirado
            is_active = (status == 'ativo' or status == 'Ativo' or status == 'Ativo') and not is_trial_expired
            
            return {
                "has_trial": has_trial,
                "is_trial_expired": is_trial_expired,
                "trial_expires_at": trial_expires_at,
                "is_active": is_active,
                "role": role
            }
        else:
            # Usuário existe mas sem data de criação
            # Considera ativo se o status for 'ativo'
            is_active = status in ['ativo', 'Ativo']
            return {
                "has_trial": False,  # Não sabemos, assume que não está em trial
                "is_trial_expired": True,  # Assumimos que expirou pois não tem data de criação
                "trial_expires_at": None,
                "is_active": is_active,
                "role": role
            }
    
    except Exception as e:
        st.error(f"Erro ao verificar status de trial: {str(e)}")
        return {
            "has_trial": False,
            "is_trial_expired": True,
            "trial_expires_at": None,
            "error": str(e)
        }

def create_new_trial_user(email: str) -> Dict[str, Any]:
    """
    Cria um novo usuário com trial de 14 dias
    """
    try:
        supabase = get_service_role_client()
        if not supabase:
            return {
                "has_trial": False,
                "is_trial_expired": True,
                "trial_expires_at": None,
                "error": "Erro de conexão com o banco de dados"
            }
        
        # Cria perfil com trial (14 dias a partir de agora)
        now = datetime.now(pytz.UTC)
        
        # Extrai o nome do email para usar como full_name
        from auth.auth_utils import extract_name_from_email
        full_name = extract_name_from_email(email)
        
        profile_data = {
            "email": email.lower().strip(),
            "full_name": full_name,
            "role": "viewer",  # Inicialmente viewer
            "status": "ativo",  # Mantém compatibilidade com o campo existente
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
            # Não inclui campos que não existem na tabela (como is_active)
        }
        
        response = supabase.table("profiles").insert(profile_data).execute()
        
        if response.data:
            # Calcula data de expiração do trial para retornar
            trial_expires_at = now + timedelta(days=14)
            return {
                "has_trial": True,
                "is_trial_expired": False,
                "trial_expires_at": trial_expires_at,
                "is_active": True,
                "role": "viewer",
                "new_user": True
            }
        else:
            st.error("Erro ao criar perfil de trial")
            return {
                "has_trial": False,
                "is_trial_expired": True,
                "trial_expires_at": None,
                "error": "Erro ao criar perfil"
            }
    
    except Exception as e:
        st.error(f"Erro ao criar usuário de trial: {str(e)}")
        return {
            "has_trial": False,
            "is_trial_expired": True,
            "trial_expires_at": None,
            "error": str(e)
        }

def show_trial_notification():
    """
    Mostra notificação de trial expirado ou informações sobre o trial
    """
    user_email = get_user_email_from_session()
    if not user_email:
        return
    
    trial_info = check_trial_status(user_email)
    
    if trial_info.get("error"):
        st.error("Erro ao verificar status do trial")
        return
    
    if trial_info.get("is_trial_expired"):
        # Mostra tela de trial expirado
        show_trial_expired_page()
    elif trial_info.get("has_trial"):
        # Mostra informações sobre o trial
        days_left = calculate_days_until_expiry(trial_info.get("trial_expires_at"))
        if days_left <= 3:  # Avisa 3 dias antes do fim
            st.warning(f"⚠️ Seu período de trial expira em {days_left} dia(s). Entre em contato com ssbbaaccidentinvestigation@gmail.com para continuar usando o sistema.")
        elif days_left <= 0:
            show_trial_expired_page()

def calculate_days_until_expiry(trial_expires_at) -> int:
    """
    Calcula quantos dias faltam para o trial expirar
    """
    if not trial_expires_at:
        return -1
    
    if isinstance(trial_expires_at, str):
        trial_expires_at = datetime.fromisoformat(trial_expires_at.replace('Z', '+00:00'))
    
    now = datetime.now(pytz.UTC)
    diff = trial_expires_at - now
    return max(0, diff.days)

def get_user_email_from_session() -> Optional[str]:
    """
    Pega o email do usuário da sessão
    """
    try:
        # Tenta pegar do sistema de autenticação existente
        from auth.auth_utils import get_user_email
        return get_user_email()
    except:
        return None

def show_trial_expired_page():
    """
    Mostra a tela de trial expirado com informações de contato
    """
    st.markdown("""
    <div style="text-align: center; padding: 50px; background: #f8f9fa; border-radius: 10px; margin: 20px 0;">
        <h2 style="color: #dc3545;">_TRIAL EXPIRADO_</h2>
        <p style="font-size: 18px; color: #666;">
            Seu período de avaliação de 14 dias terminou.
        </p>
        <p style="font-size: 16px; color: #666; margin: 20px 0;">
            Para continuar usando o sistema, entre em contato conosco:
        </p>
        <div style="background: white; padding: 20px; border-radius: 8px; display: inline-block; margin: 20px 0;">
            <h3 style="color: #007bff;">📧 E-mail de Contato:</h3>
            <p style="font-size: 20px; color: #28a745; font-weight: bold;">
                ssbbaaccidentinvestigation@gmail.com
            </p>
        </div>
        <p style="font-size: 14px; color: #888; margin-top: 30px;">
            <i>Preservamos seus dados e histórico para quando retornar ao sistema.</i>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Botão para tentar fazer logout
    if st.button("🚪 Fazer Logout"):
        try:
            from auth.auth_utils import logout_user
            logout_user()
        except:
            # Se não tiver a função de logout, limpa a sessão
            for key in list(st.session_state.keys()):
                if key.startswith('user_') or key in ['authenticated_user_email', 'role', 'user_id', 'user_info']:
                    del st.session_state[key]
            st.rerun()

def extend_trial(email: str, additional_days: int = 14) -> bool:
    """
    Estende o trial do usuário (somente para admin)
    Esta função redefine o período de trial calculando uma nova data de início
    para que o usuário tenha mais additional_days a partir de agora
    """
    try:
        supabase = get_service_role_client()
        if not supabase:
            return False
        
        now = datetime.now(pytz.UTC)
        
        # Calcula o novo created_at ajustado para que expire em additional_days
        # Isso é feito subtraindo (14 - additional_days) dias para que 14 dias depois expire no tempo certo
        # Por exemplo: se queremos extender por 21 dias, o created_at deve ser ajustado para 7 dias atrás
        # Isso fará com que o cálculo de 14 dias a partir dessa data resulte em 21 dias totais a partir de now
        adjusted_created_at = now - timedelta(days=max(0, 14 - additional_days))
        
        # Atualiza o perfil com novo created_at e updated_at
        update_response = supabase.table("profiles").update({
            "created_at": adjusted_created_at.isoformat(),
            "updated_at": now.isoformat()
        }).eq("email", email).execute()
        
        return bool(update_response.data)
    
    except Exception as e:
        st.error(f"Erro ao estender trial: {str(e)}")
        return False