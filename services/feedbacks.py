"""
Serviços para gerenciamento de feedbacks de erros e sugestões
"""
import streamlit as st
from managers.supabase_config import get_supabase_client, get_service_role_client
from auth.auth_utils import get_user_id, is_admin, get_user_email
from typing import List, Dict, Optional
import pandas as pd

def get_user_feedbacks() -> List[Dict]:
    """Busca todos os feedbacks do usuário logado"""
    try:
        supabase = get_supabase_client()
        user_id = get_user_id()
        
        if not user_id:
            return []
        
        response = supabase.table("feedbacks")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .execute()
            
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Erro ao buscar feedbacks: {str(e)}")
        return []

def get_all_feedbacks(include_resolved: bool = False) -> List[Dict]:
    """Busca todos os feedbacks (apenas para admins)"""
    try:
        if not is_admin():
            return []
        
        # Admin usa service_role para ver todos os feedbacks
        supabase = get_service_role_client()
        query = supabase.table("feedbacks").select("*")
        
        if not include_resolved:
            query = query.neq("status", "resolvido")
        
        response = query.order("created_at", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Erro ao buscar feedbacks: {str(e)}")
        return []

def create_feedback(feedback_data: Dict) -> bool:
    """Cria um novo feedback"""
    try:
        supabase = get_supabase_client()
        user_id = get_user_id()
        
        if not user_id:
            st.error("Usuário não autenticado")
            return False
        
        # Adiciona user_id se não estiver presente
        if "user_id" not in feedback_data:
            feedback_data["user_id"] = user_id
        
        # Adiciona created_by se não estiver presente
        if "created_by" not in feedback_data:
            feedback_data["created_by"] = user_id
        
        result = supabase.table("feedbacks").insert(feedback_data).execute()
        
        if result.data:
            st.success("✅ Feedback registrado com sucesso! Obrigado pela sua contribuição.")
            return True
        else:
            st.error("Erro ao criar feedback")
            return False
    except Exception as e:
        st.error(f"Erro ao criar feedback: {str(e)}")
        return False

def update_feedback_status(feedback_id: str, new_status: str, admin_notes: Optional[str] = None) -> bool:
    """Atualiza o status de um feedback (apenas admins ou o próprio usuário se estiver aberto)"""
    try:
        supabase = get_supabase_client()
        user_id = get_user_id()
        
        if not user_id:
            st.error("Usuário não autenticado")
            return False
        
        update_data = {"status": new_status}
        
        # Se for admin e tiver notas, adiciona
        if is_admin() and admin_notes:
            update_data["admin_notes"] = admin_notes
        
        # Se status mudou para resolvido, o trigger atualiza resolved_at automaticamente
        if new_status == "resolvido":
            update_data["resolved_at"] = "now()"
        
        result = supabase.table("feedbacks")\
            .update(update_data)\
            .eq("id", feedback_id)\
            .execute()
        
        if result.data:
            return True
        else:
            st.error("Erro ao atualizar feedback")
            return False
    except Exception as e:
        st.error(f"Erro ao atualizar feedback: {str(e)}")
        return False

def delete_feedback(feedback_id: str) -> bool:
    """Remove um feedback (apenas se for do usuário e estiver aberto)"""
    try:
        supabase = get_supabase_client()
        user_id = get_user_id()
        
        if not user_id:
            st.error("Usuário não autenticado")
            return False
        
        # Busca o feedback primeiro para verificar se é do usuário
        feedback = supabase.table("feedbacks")\
            .select("user_id, status")\
            .eq("id", feedback_id)\
            .execute()
        
        if not feedback.data:
            st.error("Feedback não encontrado")
            return False
        
        feedback_data = feedback.data[0]
        
        # Só pode deletar se for do usuário e estiver aberto (ou se for admin)
        if not is_admin() and (feedback_data.get("user_id") != user_id or feedback_data.get("status") != "aberto"):
            st.error("Você só pode remover feedbacks próprios que estejam com status 'aberto'")
            return False
        
        result = supabase.table("feedbacks")\
            .delete()\
            .eq("id", feedback_id)\
            .execute()
        
        if result.data:
            st.success("Feedback removido com sucesso!")
            return True
        else:
            st.error("Erro ao remover feedback")
            return False
    except Exception as e:
        st.error(f"Erro ao remover feedback: {str(e)}")
        return False

def get_feedback_statistics() -> Dict:
    """Retorna estatísticas dos feedbacks (apenas para admins)"""
    try:
        if not is_admin():
            return {}
        
        # Admin usa service_role para ver todas as estatísticas
        supabase = get_service_role_client()
        
        # Total de feedbacks
        total = supabase.table("feedbacks").select("id", count="exact").execute()
        
        # Por tipo
        tipos = supabase.table("feedbacks").select("type").execute()
        
        # Por status
        status = supabase.table("feedbacks").select("status").execute()
        
        # Por prioridade
        prioridades = supabase.table("feedbacks").select("priority").execute()
        
        stats = {
            "total": total.count if hasattr(total, 'count') else 0,
            "por_tipo": {},
            "por_status": {},
            "por_prioridade": {}
        }
        
        if tipos.data:
            for tipo in tipos.data:
                tipo_val = tipo.get('type', 'outro')
                stats["por_tipo"][tipo_val] = stats["por_tipo"].get(tipo_val, 0) + 1
        
        if status.data:
            for stat in status.data:
                stat_val = stat.get('status', 'aberto')
                stats["por_status"][stat_val] = stats["por_status"].get(stat_val, 0) + 1
        
        if prioridades.data:
            for prioridade in prioridades.data:
                prior_val = prioridade.get('priority', 'media')
                stats["por_prioridade"][prior_val] = stats["por_prioridade"].get(prior_val, 0) + 1
        
        return stats
    except Exception as e:
        st.error(f"Erro ao buscar estatísticas: {str(e)}")
        return {}

