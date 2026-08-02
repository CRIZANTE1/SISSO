"""
Serviços para gerenciamento de funcionários (employees)
"""
import streamlit as st
from managers.supabase_config import get_supabase_client, get_service_role_client
from typing import List, Dict, Optional
from datetime import date
import pandas as pd

def get_all_employees() -> List[Dict]:
    """Busca funcionários - filtra por usuário logado (exceto admin)"""
    try:
        from auth.auth_utils import get_user_id, is_admin
        
        user_id = get_user_id()
        if not user_id:
            return []
        
        # Usa service_role para contornar RLS e aplicar filtro de segurança no código
        supabase = get_service_role_client()
        if not supabase:
            st.error("Erro de conexão com o banco ao buscar funcionários.")
            return []
        
        # Admin vê todos os funcionários
        if is_admin():
            query = supabase.table("employees").select("*")
        else:
            # Usuário comum vê apenas seus próprios funcionários
            # Aplica filtro explícito por user_id (UUID)
            query = supabase.table("employees").select("*").eq("user_id", user_id)
        
        response = query.order("full_name").execute()
        employees = response.data if response.data else []
        
        # Garante que todos os funcionários retornados têm user_id correto
        # (validação adicional de segurança para usuários não-admin)
        if not is_admin() and employees:
            # Filtra novamente para garantir (segurança em camadas)
            employees = [e for e in employees if e.get('user_id') == user_id]
        
        return employees
    except Exception as e:
        st.error(f"Erro ao buscar funcionários: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return []

def get_employee_by_id(employee_id: str) -> Optional[Dict]:
    """Busca funcionário por ID - verifica se pertence ao usuário logado (exceto admin)"""
    try:
        from auth.auth_utils import get_user_id, is_admin
        
        user_id = get_user_id()
        if not user_id:
            return None
        
        # Usa service_role para contornar RLS e aplicar filtro de segurança no código
        supabase = get_service_role_client()
        
        # Admin pode ver qualquer funcionário
        if is_admin():
            response = supabase.table("employees").select("*").eq("id", employee_id).execute()
        else:
            # Usuário comum só pode ver seus próprios funcionários
            # Aplica filtro explícito por user_id (UUID)
            response = supabase.table("employees").select("*").eq("id", employee_id).eq("user_id", user_id).execute()
        
        if response.data:
            employee = response.data[0]
            # Validação adicional de segurança para usuários não-admin
            if not is_admin() and employee.get('user_id') != user_id:
                return None
            return employee
        return None
    except Exception as e:
        st.error(f"Erro ao buscar funcionário: {str(e)}")
        return None

def create_employee(employee_data: Dict) -> bool:
    """Cria um novo funcionário"""
    try:
        from auth.auth_utils import get_user_id

        # Garante vínculo com o usuário logado
        user_id = employee_data.get("user_id") or get_user_id()
        if not user_id:
            st.error("Não foi possível identificar o usuário logado. Faça login novamente.")
            return False
        employee_data = {**employee_data, "user_id": user_id}

        # Remove chaves vazias que podem quebrar o insert
        clean = {k: v for k, v in employee_data.items() if v is not None and v != ""}

        supabase = get_service_role_client()
        if not supabase:
            st.error("Erro ao conectar com o banco de dados.")
            return False

        result = supabase.table("employees").insert(clean).execute()
        if result.data:
            st.success("✅ Funcionário cadastrado com sucesso!")
            return True
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
        
        # Alinhado com estrutura real: id, full_name, document_id, job_title, department, 
        # admission_date, termination_date, email, user_id, status, created_at, updated_at
        with col1:
            full_name = st.text_input("Nome Completo", value=employee_data.get("full_name", "") if is_update else "")
            document_id = st.text_input("CPF/Documento", value=employee_data.get("document_id", "") if is_update else "")
            email = st.text_input("E-mail", value=employee_data.get("email", "") if is_update else "")
            job_title = st.text_input("Cargo", value=employee_data.get("job_title", "") if is_update else "")
            
        with col2:
            department = st.text_input("Departamento", value=employee_data.get("department", "") if is_update else "")
            default_admission = date.today()
            if is_update and employee_data.get("admission_date"):
                try:
                    default_admission = pd.to_datetime(employee_data.get("admission_date")).date()
                except Exception:
                    default_admission = date.today()
            admission_date = st.date_input("Data de Admissão", value=default_admission)

            has_termination = bool(is_update and employee_data.get("termination_date"))
            include_termination = st.checkbox(
                "Informar data de demissão",
                value=has_termination,
            )
            termination_date = None
            if include_termination:
                default_term = date.today()
                if has_termination:
                    try:
                        default_term = pd.to_datetime(employee_data.get("termination_date")).date()
                    except Exception:
                        default_term = date.today()
                termination_date = st.date_input("Data de Demissão", value=default_term)

            # status é texto com default 'active' - mapeado para checkbox
            status_value = employee_data.get("status", "active") if is_update else "active"
            is_active = st.checkbox("Funcionário Ativo", value=(status_value == "active") if is_update else True)
        
        submitted = st.form_submit_button(button_text, type="primary")
        if submitted:
            # Validação de campos obrigatórios
            errors = []
            if not full_name:
                errors.append("Nome completo é obrigatório.")
            
            if errors:
                for error in errors:
                    st.error(error)
                return None
            
            # Alinhado com estrutura real da tabela employees
            from auth.auth_utils import get_user_id
            user_id = get_user_id()
            if not user_id:
                st.error("Sessão inválida: faça login novamente antes de cadastrar.")
                return None
            
            payload = {
                "full_name": full_name.strip(),
                "document_id": document_id.strip() if document_id else None,
                "email": email.strip().lower() if email else None,
                "job_title": job_title.strip() if job_title else None,
                "department": department.strip() if department else None,
                "admission_date": admission_date.isoformat() if admission_date else None,
                "termination_date": termination_date.isoformat() if termination_date else None,
                "status": "active" if is_active else "inactive",
                "user_id": user_id,
            }
            return payload

def list_employees_table():
    """Exibe tabela de funcionários com opções de edição/remoção"""
    employees = get_all_employees()
    
    if employees:
        st.write("**Funcionários Cadastrados:**")
        employees_df = pd.DataFrame(employees)
        display_cols = ['full_name', 'document_id', 'email', 'job_title', 'department', 'admission_date', 'status']
        available_cols = [col for col in display_cols if col in employees_df.columns]
        st.dataframe(employees_df[available_cols], width='stretch', hide_index=True)
    else:
        st.info("Nenhum funcionário cadastrado.")