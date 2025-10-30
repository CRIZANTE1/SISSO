import streamlit as st
import pandas as pd
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from managers.supabase_config import get_supabase_client

def get_users() -> List[Dict[str, Any]]:
    """Busca lista de usuários disponíveis"""
    try:
        supabase = get_supabase_client()
        response = supabase.table("profiles").select("email, full_name, role").order("full_name").execute()
        return response.data
    except Exception as e:
        st.error(f"Erro ao buscar usuários: {str(e)}")
        return []

def user_filter(allow_multiple: bool = True, 
                default_all: bool = True,
                key_prefix: str = "") -> List[str]:
    """Filtro de usuários"""
    users = get_users()
    
    if not users:
        return []
    
    user_options = {f"{user['full_name'] or 'Usuário'} ({user['role']})": user['email'] for user in users}
    
    if allow_multiple:
        if default_all:
            default_selection = list(user_options.keys())
        else:
            default_selection = []
        
        selected_users = st.multiselect(
            "👥 Usuários",
            options=list(user_options.keys()),
            default=default_selection,
            key=f"{key_prefix}_users",
            help="Selecione um ou mais usuários para filtrar os registros pelo campo 'created_by'."
        )
        
        return [user_options[user] for user in selected_users]
    else:
        selected_user = st.selectbox(
            "👥 Usuário",
            options=["Todos"] + list(user_options.keys()),
            key=f"{key_prefix}_user",
            help="Selecione um usuário específico ou 'Todos' para incluir todos os criadores."
        )
        
        if selected_user == "Todos":
            return [user_options[user] for user in user_options.keys()]
        else:
            return [user_options[selected_user]]

def date_range_filter(key_prefix: str = "") -> tuple[Optional[date], Optional[date]]:
    """Filtro de período opcional (só aplica se ativado pelo usuário)."""
    enable_dates = st.checkbox(
        "Filtrar por data",
        value=False,
        key=f"{key_prefix}_date_enabled",
        help="Ative para restringir os resultados a um intervalo de datas."
    )
    
    if not enable_dates:
        return None, None
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "📅 Data Inicial",
            key=f"{key_prefix}_start_date",
            help="Data mínima considerada no filtro."
        )
    
    with col2:
        end_date = st.date_input(
            "📅 Data Final",
            key=f"{key_prefix}_end_date",
            help="Data máxima considerada no filtro."
        )
    
    return start_date, end_date

def severity_filter(key_prefix: str = "") -> List[str]:
    """Filtro de severidade/tipo para ACCIDENTES (registráveis e não registráveis)
    Mapeado para a nova estrutura: fatal, lesao, sem_lesao
    """
    severity_options = {
        "Fatal": "fatal",
        "Com Lesão": "lesao", 
        "Sem Lesão": "sem_lesao",
    }
    
    selected_severities = st.multiselect(
        "⚠️ Severidade",
        options=list(severity_options.keys()),
        default=list(severity_options.keys()),
        key=f"{key_prefix}_severity",
        help="Define quais severidades de acidente serão incluídas na análise."
    )
    
    return [severity_options[sev] for sev in selected_severities]

def event_type_filter(key_prefix: str = "") -> List[str]:
    """Filtro de tipo de evento"""
    event_types = [
        "Acidente Fatal",
        "Acidente com Lesão",
        "Acidente sem Lesão", 
        "Quase-Acidente",
        "Não Conformidade"
    ]
    
    selected_types = st.multiselect(
        "📋 Tipo de Evento",
        options=event_types,
        default=event_types,
        key=f"{key_prefix}_event_type",
        help="Filtra os registros pelos tipos selecionados."
    )
    
    return selected_types

def root_cause_filter(key_prefix: str = "") -> List[str]:
    """Filtro de causa raiz"""
    root_causes = [
        "Fator Humano",
        "Fator Material", 
        "Fator Ambiental",
        "Fator Organizacional",
        "Fator Técnico",
        "Outros"
    ]
    
    selected_causes = st.multiselect(
        "🔍 Causa Raiz",
        options=root_causes,
        default=root_causes,
        key=f"{key_prefix}_root_cause",
        help="Mostra somente registros com as causas selecionadas."
    )
    
    return selected_causes

def period_filter(key_prefix: str = "") -> str:
    """Filtro de período (últimos N meses)"""
    period_options = {
        "Últimos 3 meses": 3,
        "Últimos 6 meses": 6,
        "Últimos 12 meses": 12,
        "Últimos 24 meses": 24,
        "Todos os períodos": 0
    }
    
    selected_period = st.selectbox(
        "📊 Período",
        options=list(period_options.keys()),
        key=f"{key_prefix}_period",
        help="Aplica um recorte relativo no tempo (em meses). Use 'Todos os períodos' para não limitar."
    )
    
    return period_options[selected_period]

def create_filter_sidebar() -> Dict[str, Any]:
    """Cria sidebar com todos os filtros"""
    with st.sidebar:
        st.header("🔍 Filtros")
        # Ajuda dos filtros via popover
        cols_help = st.columns([1, 1])
        with cols_help[0]:
            with st.popover("❓ Ajuda"):
                st.markdown(
                    "**Como os filtros funcionam**\n\n"
                    "- Os filtros aplicam-se às páginas de análise, registros e métricas.\n"
                    "- '📊 Período' limita pelos últimos N meses com base no dado mais recente.\n"
                    "- 'Filtrar por data' substitui o período com um intervalo específico.\n"
                    "- '👥 Usuários' filtra por quem criou o registro (created_by).\n"
                    "- Nem todas as páginas usam todos os filtros (ex.: causa raiz).\n\n"
                    "**Dicas**\n\n"
                    "- Se não retornar dados, experimente reduzir os filtros.\n"
                    "- Verifique se as colunas existem na sua base (ex.: root_cause)."
                )
        with st.expander("Como usar os filtros", expanded=False):
            st.markdown(
                "- Use os filtros para refinar a análise em todas as páginas.\n"
                "- O período relativo (📊 Período) limita por meses a partir do dado mais recente.\n"
                "- O intervalo de datas (📅) substitui o período quando ativado.\n"
                "- Os filtros aplicam-se aos gráficos, tabelas e métricas."
            )
        with st.popover("❓ Dúvidas sobre filtros"):
            st.markdown(
                "- Se nada aparece, reduza os filtros.\n"
                "- 'Usuários' filtra por quem criou o registro.\n"
                "- Nem todas as páginas usam todos os filtros (ex.: causa raiz só onde existe)."
            )
        
        # Usuários
        selected_users = user_filter()
        
        # Período
        months_back = period_filter()
        
        # Data específica
        start_date, end_date = date_range_filter()
        
        # Severidade
        selected_severities = severity_filter()
        
        # Tipo de evento
        selected_event_types = event_type_filter()
        
        # Causa raiz
        selected_root_causes = root_cause_filter()
        
        return {
            "users": selected_users,
            "months_back": months_back,
            "start_date": start_date,
            "end_date": end_date,
            "severities": selected_severities,
            "event_types": selected_event_types,
            "root_causes": selected_root_causes
        }

def apply_filters_to_df(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    """Aplica filtros a um DataFrame"""
    filtered_df = df.copy()
    
    # Normaliza colunas de datas quando existirem
    if "occurred_at" in filtered_df.columns:
        filtered_df["occurred_at"] = pd.to_datetime(filtered_df["occurred_at"], errors="coerce").dt.date
    if "opened_at" in filtered_df.columns:
        filtered_df["opened_at"] = pd.to_datetime(filtered_df["opened_at"], errors="coerce").dt.date
    
    # Filtro por usuários
    if filters.get("users") and "created_by" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["created_by"].isin(filters["users"])]
    
    # Filtro por período (últimos N meses)
    if filters.get("months_back", 0) > 0:
        if "period" in filtered_df.columns:
            # Assume que period está no formato YYYY-MM-DD
            latest_period = pd.to_datetime(filtered_df["period"]).max()
            cutoff_date = latest_period - pd.DateOffset(months=filters["months_back"])
            filtered_df = filtered_df[pd.to_datetime(filtered_df["period"]) >= cutoff_date]
    
    # Filtro por data
    if filters.get("start_date") and "occurred_at" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["occurred_at"] >= filters["start_date"]]
    
    if filters.get("end_date") and "occurred_at" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["occurred_at"] <= filters["end_date"]]
    
    # Filtro por data para não conformidades
    if filters.get("start_date") and "opened_at" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["opened_at"] >= filters["start_date"]]
    
    if filters.get("end_date") and "opened_at" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["opened_at"] <= filters["end_date"]]
    
    # Filtro por tipo de acidente
    if filters.get("severities") and "type" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["type"].isin(filters["severities"])]
    
    # Filtro por severidade de não conformidade
    if filters.get("severities") and "severity" in filtered_df.columns:
        # Só aplica se houver interseção de valores possíveis
        allowed = set(filters["severities"]) & set(filtered_df["severity"].dropna().unique())
        if allowed:
            filtered_df = filtered_df[filtered_df["severity"].isin(allowed)]
    
    # Filtro por causa raiz
    if filters.get("root_causes") and "root_cause" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["root_cause"].isin(filters["root_causes"])]
    
    return filtered_df
