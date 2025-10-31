import streamlit as st
from auth.auth_utils import require_login, get_user_info
from managers.supabase_config import get_service_role_client
import pandas as pd
from datetime import date
from services.employees import get_all_employees, create_employee, employee_form, list_employees_table


def load_profile(email: str) -> dict:
    supabase = get_service_role_client()
    if not supabase:
        st.error("Erro de conexão com o banco de dados.")
        return {}
    resp = supabase.table("profiles").select("email, full_name, company_name, employees_count, contact_email, status").eq("email", email).limit(1).execute()
    if resp and hasattr(resp, 'data') and resp.data:
        return resp.data[0]
    return {"email": email}


def save_profile(data: dict) -> bool:
    supabase = get_service_role_client()
    if not supabase:
        st.error("Erro de conexão com o banco de dados.")
        return False
    # upsert por email
    result = supabase.table("profiles").upsert(data, on_conflict="email").execute()
    return bool(result and hasattr(result, 'data'))


def fetch_user_accidents(user_email: str, user_name: str) -> pd.DataFrame:
    try:
        supabase = get_service_role_client()
        if not supabase:
            return pd.DataFrame()
        # Campos de investigação removidos - não existem na tabela accidents
        # Filtra apenas por status aberto e criador
        query = supabase.table("accidents").select("id, occurred_at, description, status, created_by")
        # Mostra apenas acidentes abertos do usuário
        response = query.eq("status", "aberto").order("occurred_at", desc=True).execute()
        if response and hasattr(response, 'data') and response.data:
            df = pd.DataFrame(response.data)
            return df
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def update_investigation(accident_id: int, completed: bool, inv_date: date | None, responsible: str | None, notes: str | None) -> bool:
    supabase = get_service_role_client()
    if not supabase:
        return False
    # Campos de investigação removidos - apenas atualiza status
    payload = {
        "status": "fechado" if completed else "aberto",
    }
    res = supabase.table("accidents").update(payload).eq("id", accident_id).execute()
    return bool(res and hasattr(res, 'data'))


def app():
    require_login()
    
    # Verifica e mostra informações do trial
    try:
        from services.trial_manager import show_trial_notification
        show_trial_notification()
    except ImportError:
        pass  # Se não tiver o trial manager, continua normalmente
    
    user = get_user_info() or {}
    user_email = user.get("email", "")
    user_name = user.get("full_name", "")

    st.title("👤 Perfil do Usuário")
    # Ajuda da página (popover)
    pl, pr = st.columns([6, 1])
    with pr:
        with st.popover("❓ Ajuda"):
            st.markdown(
                "**Guia rápido**\n\n"
                "- Atualize dados de perfil e contatos.\n"
                "- Gerencie funcionários vinculados.\n"
                "- Atualize investigações sob sua responsabilidade.\n\n"
                "**Dicas**\n\n"
                "- E-mail de contato é obrigatório para salvar.\n\n"
                "**📝 Feedback**\n"
                "- Encontrou um erro ou tem uma sugestão? Acesse **Feedbacks** no menu para reportar!"
            )

    # Perfil
    st.subheader("Dados de Perfil")
    profile = load_profile(user_email)

    col1, col2 = st.columns(2)
    with col1:
        full_name = st.text_input("Nome completo", value=profile.get("full_name", user_name or ""))
        company_name = st.text_input("Empresa", value=profile.get("company_name", ""), placeholder="Ex: Minha Empresa LTDA")
        contact_email = st.text_input("E-mail de contato", value=profile.get("contact_email", profile.get("email", user_email)))
    with col2:
        employees_count = st.number_input("Número de funcionários", min_value=0, step=1, value=int(profile.get("employees_count") or 0))
        status = st.selectbox("Status", options=["ativo", "inativo"], index=0 if profile.get("status", "ativo") == "ativo" else 1)

    if st.button("💾 Salvar Perfil", type="primary", key="btn_save_profile"):
        if not contact_email:
            st.error("E-mail de contato é obrigatório.")
        else:
            data = {
                "email": user_email,
                "full_name": full_name.strip(),
                "company_name": company_name.strip() or None,
                "employees_count": int(employees_count),
                "contact_email": contact_email.strip().lower(),
                "status": status,
            }
            if save_profile(data):
                st.success("Perfil salvo com sucesso!")
            else:
                st.error("Falha ao salvar perfil.")

    st.markdown("---")

    # Gerenciamento de Funcionários
    st.subheader("👷 Gerenciar Funcionários")
    list_employees_table()
    
    st.subheader("Adicionar Novo Funcionário")
    employee_data = employee_form()
    if employee_data:
        create_employee(employee_data)
        st.rerun()

    st.markdown("---")

    # Atualização de Investigação de Acidentes
    st.subheader("🔍 Atualizar Investigação de Acidentes")
    df_acc = fetch_user_accidents(user_email, user_name)

    if df_acc.empty:
        st.info("Nenhum acidente disponível para atualizar.")
        return

    # Seleciona acidente
    options = {}
    for _, row in df_acc.iterrows():
        label = f"{row.get('occurred_at', '')} - {str(row.get('description', 'Sem descrição'))[:60]} (#{row.get('id')})"
        options[label] = row.get('id')

    selected = st.selectbox("Selecione um acidente", options=list(options.keys()))

    if selected:
        accident_id = options[selected]
        sel_row = df_acc[df_acc['id'] == accident_id].iloc[0]

        with st.form("investigation_form"):
            # Campos de investigação removidos - apenas status
            completed = st.checkbox("Marcar como Fechado", value=sel_row.get('status') == 'fechado')
            # inv_date, responsible, notes removidos - campos não existem na tabela

            submitted = st.form_submit_button("💾 Atualizar Investigação", type="primary")
            if submitted:
                ok = update_investigation(accident_id, completed, None, None, None)
                if ok:
                    st.success("Investigação atualizada!")
                    st.rerun()
                else:
                    st.error("Falha ao atualizar investigação.")


if __name__ == "__main__":
    app()
