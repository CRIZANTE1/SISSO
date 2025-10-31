"""
Serviços para registro de logs de ações dos usuários
"""
import streamlit as st
from managers.supabase_config import get_supabase_client, get_service_role_client
from auth.auth_utils import get_user_id, is_admin
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

def log_action(
    action_type: str,
    entity_type: str,
    description: str,
    entity_id: Optional[str] = None,
    metadata: Optional[Dict] = None,
    expires_days: int = 90
) -> bool:
    """
    Registra uma ação do usuário no log
    
    Args:
        action_type: Tipo de ação (create, update, delete, view, export, import, login, logout, upload, download, other)
        entity_type: Tipo de entidade (accident, near_miss, nonconformity, action, feedback, profile, etc.)
        description: Descrição detalhada da ação
        entity_id: ID da entidade relacionada (opcional)
        metadata: Dados adicionais em formato dict (opcional)
        expires_days: Dias até o log expirar (padrão: 90 dias)
    
    Returns:
        True se o log foi registrado com sucesso, False caso contrário
    """
    try:
        supabase = get_supabase_client()
        user_id = get_user_id()
        
        if not user_id:
            # Se não houver usuário logado, não registra log
            return False
        
        # Tenta obter informações adicionais do request (se disponível)
        ip_address = None
        user_agent = None
        
        try:
            # Streamlit não expõe diretamente, mas podemos tentar obter de headers se disponível
            pass
        except:
            pass
        
        # Calcula data de expiração
        expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()
        
        log_data = {
            "user_id": user_id,
            "action_type": action_type,
            "entity_type": entity_type,
            "description": description,
            "created_by": user_id,
            "expires_at": expires_at
        }
        
        if entity_id:
            log_data["entity_id"] = entity_id
        
        if metadata:
            log_data["metadata"] = json.dumps(metadata)
        
        if ip_address:
            log_data["ip_address"] = ip_address
        
        if user_agent:
            log_data["user_agent"] = user_agent
        
        result = supabase.table("user_logs").insert(log_data).execute()
        
        return bool(result.data)
    except Exception as e:
        # Não interrompe o fluxo se houver erro no log
        # Apenas registra silenciosamente para não afetar a experiência do usuário
        try:
            import logging
            logging.error(f"Erro ao registrar log de ação: {str(e)}")
        except:
            pass
        return False

def get_user_logs(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    action_type: Optional[str] = None,
    entity_type: Optional[str] = None,
    limit: int = 100
) -> List[Dict]:
    """
    Busca logs do usuário logado
    
    Args:
        start_date: Data inicial (opcional)
        end_date: Data final (opcional)
        action_type: Filtrar por tipo de ação (opcional)
        entity_type: Filtrar por tipo de entidade (opcional)
        limit: Limite de registros (padrão: 100)
    
    Returns:
        Lista de logs
    """
    try:
        supabase = get_supabase_client()
        user_id = get_user_id()
        
        if not user_id:
            return []
        
        query = supabase.table("user_logs").select("*")
        
        # RLS já filtra para mostrar apenas logs do usuário logado
        # Mas podemos adicionar filtro adicional para garantir
        
        if start_date:
            query = query.gte("created_at", start_date.isoformat())
        
        if end_date:
            query = query.lte("created_at", end_date.isoformat())
        
        if action_type:
            query = query.eq("action_type", action_type)
        
        if entity_type:
            query = query.eq("entity_type", entity_type)
        
        response = query\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        if response.data:
            # Processa metadata JSON se existir
            for log in response.data:
                if log.get('metadata') and isinstance(log['metadata'], str):
                    try:
                        log['metadata'] = json.loads(log['metadata'])
                    except:
                        pass
        
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Erro ao buscar logs: {str(e)}")
        return []

def get_all_logs(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    action_type: Optional[str] = None,
    entity_type: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 500
) -> List[Dict]:
    """
    Busca todos os logs (apenas para admins)
    
    Args:
        start_date: Data inicial (opcional)
        end_date: Data final (opcional)
        action_type: Filtrar por tipo de ação (opcional)
        entity_type: Filtrar por tipo de entidade (opcional)
        user_id: Filtrar por usuário (opcional)
        limit: Limite de registros (padrão: 500)
    
    Returns:
        Lista de logs
    """
    try:
        if not is_admin():
            return []
        
        # Admin usa service_role para ver todos os logs
        supabase = get_service_role_client()
        query = supabase.table("user_logs").select("*")
        
        if start_date:
            query = query.gte("created_at", start_date.isoformat())
        
        if end_date:
            query = query.lte("created_at", end_date.isoformat())
        
        if action_type:
            query = query.eq("action_type", action_type)
        
        if entity_type:
            query = query.eq("entity_type", entity_type)
        
        if user_id:
            query = query.eq("user_id", user_id)
        
        response = query\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        if response.data:
            # Processa metadata JSON se existir
            for log in response.data:
                if log.get('metadata') and isinstance(log['metadata'], str):
                    try:
                        log['metadata'] = json.loads(log['metadata'])
                    except:
                        pass
        
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Erro ao buscar logs: {str(e)}")
        return []

def cleanup_expired_logs() -> int:
    """
    Limpa logs expirados (apenas para admins)
    
    Returns:
        Número de logs removidos
    """
    try:
        if not is_admin():
            return 0
        
        supabase = get_service_role_client()
        
        # Remove logs expirados
        result = supabase.rpc("cleanup_expired_logs").execute()
        
        # Se a função RPC não estiver disponível, faz manualmente
        if not result:
            result = supabase.table("user_logs")\
                .delete()\
                .lt("expires_at", datetime.now().isoformat())\
                .execute()
            
            return len(result.data) if result.data else 0
        
        return result.data if isinstance(result.data, int) else 0
    except Exception as e:
        st.error(f"Erro ao limpar logs expirados: {str(e)}")
        return 0

def get_log_statistics() -> Dict:
    """
    Retorna estatísticas dos logs (apenas para admins)
    
    Returns:
        Dicionário com estatísticas
    """
    try:
        if not is_admin():
            return {}
        
        supabase = get_service_role_client()
        
        # Total de logs
        total = supabase.table("user_logs").select("id", count="exact").execute()
        
        # Por tipo de ação
        actions = supabase.table("user_logs").select("action_type").execute()
        
        # Por tipo de entidade
        entities = supabase.table("user_logs").select("entity_type").execute()
        
        stats = {
            "total": total.count if hasattr(total, 'count') else 0,
            "por_action_type": {},
            "por_entity_type": {}
        }
        
        if actions.data:
            for action in actions.data:
                action_val = action.get('action_type', 'other')
                stats["por_action_type"][action_val] = stats["por_action_type"].get(action_val, 0) + 1
        
        if entities.data:
            for entity in entities.data:
                entity_val = entity.get('entity_type', 'other')
                stats["por_entity_type"][entity_val] = stats["por_entity_type"].get(entity_val, 0) + 1
        
        return stats
    except Exception as e:
        st.error(f"Erro ao buscar estatísticas: {str(e)}")
        return {}

