"""
Serviços para gerenciamento de funcionários (employees)
"""
import streamlit as st
from managers.supabase_config import get_supabase_client, get_service_role_client
from typing import List, Dict, Optional
import pandas as pd

def get_all_employees() -> List[Dict]:
    """Busca todos os funcionários"""
    try:
        supabase = get_supabase_client()
        response = supabase.table("employees").select("*").order("full_name").execute()
        return response.data
    except Exception as e:
        st.error(f"Erro ao buscar funcionários: {str(e)}")
        return []

def get_employee_by_id(employee_id: str) -> Optional[Dict]:
    """Busca funcionário por ID"""
    try:
        supabase = get_supabase_client()
        response = supabase.table("employees").select("*").eq("id", employee_id).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Erro ao buscar funcionário: {str(e)}")
        return None

def create_employee(employee_data: Dict) -> bool:
    """Cria um novo funcionário"""
    try:
        supabase = get_service_role_client()
        result = supabase.table("employees").insert(employee_data).execute()
        if result.data:
            st.success("✅ Funcionário cadastrado com sucesso!")
            return True
        else:
            st.error("Erro ao cadastrar funcionário.")
            return False
    except Exception as e:
        st.error(f"Erro ao criar funcionário: {str(e)}")
        return False

def update_employee(employee_id: str, employee_data: Dict) -> bool:
    """Atualiza um funcionário existente"""
    try:
        supabase = get_service_role_client()
        result = supabase.table("employees").update(employee_data).eq("id", employee_id).execute()
        if result.data:
            st.success("✅ Funcionário atualizado com sucesso!")
            return True
        else:
            st.error("Erro ao atualizar funcionário.")
            return False
    except Exception as e:
        st.error(f"Erro ao atualizar funcionário: {str(e)}")
        return False

def delete_employee(employee_id: str) -> bool:
    """Remove um funcionário"""
    try:
        supabase = get_service_role_client()
        result = supabase.table("employees").delete().eq("id", employee_id).execute()
        if result.data:
            st.success("✅ Funcionário removido com sucesso!")
            return True
        else:
            st.error("Erro ao remover funcionário.")
            return False
    except Exception as e:
        st.error(f"Erro ao remover funcionário: {str(e)}")
        return False

def employee_form(employee_data: Optional[Dict] = None) -> Optional[Dict]:
    """Formulário para criar/atualizar funcionário"""
    is_update = employee_data is not None
    title = "Atualizar Funcionário" if is_update else "Adicionar Novo Funcionário"
    button_text = "💾 Atualizar Funcionário" if is_update else "💾 Salvar Funcionário"
    
    with st.form(f"employee_form_{'update' if is_update else 'create'}"):
        col1, col2 = st.columns(2)
        
        with col1:
            full_name = st.text_input("Nome Completo", value=employee_data.get("full_name", "") if is_update else "")
            cpf = st.text_input("CPF", value=employee_data.get("cpf", "") if is_update else "")
            email = st.text_input("E-mail", value=employee_data.get("email", "") if is_update else "")
            phone = st.text_input("Telefone", value=employee_data.get("phone", "") if is_update else "")
            employee_id_input = st.text_input("ID do Funcionário", value=employee_data.get("employee_id", "") if is_update else "")
            
        with col2:
            department = st.text_input("Departamento", value=employee_data.get("department", "") if is_update else "")
            position = st.text_input("Cargo", value=employee_data.get("position", "") if is_update else "")
            admission_date = st.date_input("Data de Admissão", value=pd.to_datetime(employee_data.get("admission_date")).date() if is_update and employee_data.get("admission_date") else None)
            is_active = st.checkbox("Funcionário Ativo", value=employee_data.get("is_active", True) if is_update else True)
            site_id = st.text_input("ID do Site", value=employee_data.get("site_id", "") if is_update else "")
        
        submitted = st.form_submit_button(button_text, type="primary")
        if submitted:
            # Validação de campos obrigatórios
            errors = []
            if not full_name:
                errors.append("Nome completo é obrigatório.")
            if not cpf:
                errors.append("CPF é obrigatório.")
            if not email:
                errors.append("E-mail é obrigatório.")
            
            if errors:
                for error in errors:
                    st.error(error)
                return None
            
            employee_data = {
                "full_name": full_name,
                "cpf": cpf,
                "email": email,
                "phone": phone,
                "employee_id": employee_id_input,
                "department": department,
                "position": position,
                "admission_date": admission_date.isoformat() if admission_date else None,
                "is_active": is_active,
                "site_id": site_id
            }
            return employee_data

def list_employees_table():
    """Exibe tabela de funcionários com opções de edição/remoção"""
    employees = get_all_employees()
    
    if employees:
        st.write("**Funcionários Cadastrados:**")
        employees_df = pd.DataFrame(employees)
        display_cols = ['full_name', 'cpf', 'email', 'department', 'position', 'admission_date', 'is_active']
        available_cols = [col for col in display_cols if col in employees_df.columns]
        st.dataframe(employees_df[available_cols], use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum funcionário cadastrado.")