"""
Serviços para gerenciamento de ações corretivas (actions)
"""
import streamlit as st
from managers.supabase_config import get_supabase_client, get_service_role_client
from auth.auth_utils import get_user_id, is_admin
from typing import List, Dict, Optional
import pandas as pd

def get_actions_by_entity(entity_type: str, entity_id: str) -> List[Dict]:
    """Busca todas as ações relacionadas a uma entidade (accident, near_miss, nonconformity)"""
    try:
        if is_admin():
            supabase = get_service_role_client()
        else:
            supabase = get_supabase_client()
            
        response = supabase.table("actions")\
            .select("*")\
            .eq("entity_type", entity_type)\
            .eq("entity_id", entity_id)\
            .order("when_date", desc=True)\
            .execute()
            
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Erro ao buscar ações: {str(e)}")
        return []

def create_action(action_data: Dict) -> bool:
    """Cria uma nova ação corretiva"""
    try:
        supabase = get_supabase_client()
        user_id = get_user_id()
        
        if not user_id:
            st.error("Usuário não autenticado")
            return False
        
        # Adiciona created_by se não estiver presente
        if "created_by" not in action_data:
            action_data["created_by"] = user_id
        
        result = supabase.table("actions").insert(action_data).execute()
        
        if result.data:
            # Registra log da ação
            try:
                from services.user_logs import log_action
                log_action(
                    action_type="create",
                    entity_type="action",
                    description=f"Ação corretiva criada: {action_data.get('what', '')[:100]}...",
                    entity_id=result.data[0].get('id'),
                    metadata={"entity_type": action_data.get('entity_type'), "status": action_data.get('status')}
                )
            except:
                pass  # Não interrompe o fluxo se houver erro no log
            
            return True
        else:
            st.error("Erro ao criar ação corretiva")
            return False
    except Exception as e:
        st.error(f"Erro ao criar ação: {str(e)}")
        return False

def update_action_status(action_id: str, new_status: str) -> bool:
    """Atualiza o status de uma ação"""
    try:
        supabase = get_supabase_client()
        result = supabase.table("actions")\
            .update({"status": new_status})\
            .eq("id", action_id)\
            .execute()
        
        if result.data:
            return True
        else:
            st.error("Erro ao atualizar ação")
            return False
    except Exception as e:
        st.error(f"Erro ao atualizar ação: {str(e)}")
        return False

def delete_action(action_id: str) -> bool:
    """Remove uma ação"""
    try:
        supabase = get_supabase_client()
        result = supabase.table("actions")\
            .delete()\
            .eq("id", action_id)\
            .execute()
        
        if result.data:
            return True
        else:
            st.error("Erro ao remover ação")
            return False
    except Exception as e:
        st.error(f"Erro ao remover ação: {str(e)}")
        return False

def action_form(entity_type: str, entity_id: str, action_data: Optional[Dict] = None) -> Optional[Dict]:
    """Formulário para criar/editar ação corretiva usando metodologia 5W2H"""
    is_update = action_data is not None
    title = "Editar Ação Corretiva" if is_update else "Nova Ação Corretiva (5W2H)"
    
    with st.form(f"action_form_{entity_type}_{entity_id}"):
        st.markdown(f"### {title}")
        
        if not is_update:
            st.info("📋 Preencha os campos seguindo a metodologia 5W2H (What, Who, When, Where, Why, How, How Much)")
        
        # 5W2H - Campos da metodologia
        what = st.text_area(
            "**O QUE** será feito? (Descrição da ação)",
            value=action_data.get("what", "") if is_update else "",
            height=100,
            help="Descreva claramente a ação a ser implementada"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            who = st.text_input(
                "**QUEM** é responsável?",
                value=action_data.get("who", "") if is_update else "",
                help="Nome da pessoa ou equipe responsável"
            )
            
            when_date = st.date_input(
                "**QUANDO** será executada?",
                value=pd.to_datetime(action_data.get("when_date")).date() if is_update and action_data.get("when_date") else None,
                help="Data prevista para execução"
            )
            
        with col2:
            where_text = st.text_input(
                "**ONDE** será executada?",
                value=action_data.get("where_text", "") if is_update else "",
                help="Local/área onde a ação será implementada"
            )
            
            how_much = st.number_input(
                "**QUANTO** custa? (R$)",
                min_value=0.0,
                value=float(action_data.get("how_much", 0)) if is_update and action_data.get("how_much") else 0.0,
                step=0.01,
                help="Custo estimado da ação"
            )
        
        why = st.text_area(
            "**POR QUE** é necessária? (Justificativa)",
            value=action_data.get("why", "") if is_update else "",
            height=80,
            help="Justificativa da necessidade da ação"
        )
        
        how = st.text_area(
            "**COMO** será executada? (Método/Procedimento)",
            value=action_data.get("how", "") if is_update else "",
            height=80,
            help="Descrição do método ou procedimento a ser seguido"
        )
        
        status = st.selectbox(
            "Status",
            options=["aberta", "em_andamento", "fechada"],
            index=["aberta", "em_andamento", "fechada"].index(action_data.get("status", "aberta")) if is_update else 0,
            format_func=lambda x: {
                "aberta": "Aberta",
                "em_andamento": "Em Andamento",
                "fechada": "Fechada"
            }[x]
        )
        
        submitted = st.form_submit_button(
            "💾 Salvar Ação Corretiva" if not is_update else "💾 Atualizar Ação",
            type="primary"
        )
        
        if submitted:
            if not what.strip():
                st.error("O campo 'O QUE será feito?' é obrigatório.")
                return None
            
            if not who.strip():
                st.error("O campo 'QUEM é responsável?' é obrigatório.")
                return None
            
            action_dict = {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "what": what.strip(),
                "who": who.strip(),
                "when_date": when_date.isoformat() if when_date else None,
                "where_text": where_text.strip() if where_text else None,
                "why": why.strip() if why else None,
                "how": how.strip() if how else None,
                "how_much": float(how_much) if how_much else None,
                "status": status
            }
            
            return action_dict
        return None
    
    return None

