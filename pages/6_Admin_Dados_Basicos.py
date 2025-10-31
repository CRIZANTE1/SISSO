import streamlit as st
import pandas as pd
from services.auth import require_role
from services.uploads import import_hours_csv, import_accidents_csv
from managers.supabase_config import get_supabase_client

def app(filters=None):
    # Verifica autenticação e trial
    from auth.auth_utils import require_login
    require_login()
    
    # Busca filtros do session state se não foram passados como parâmetro
    if filters is None:
        filters = st.session_state.get('filters', {})
    # Verifica se usuário tem permissão de admin
    from auth.auth_utils import check_permission
    check_permission('admin')
    
    st.title("⚙️ Admin - Dados Básicos")
    # Ajuda da página (popover)
    al, ar = st.columns([6, 1])
    with ar:
        with st.popover("❓ Ajuda"):
            st.markdown(
                "**Guia rápido**\n\n"
                "- Gerencie Sites e Usuários.\n"
                "- Importe Horas e Acidentes via CSV.\n"
                "- Recalcule KPIs e veja estatísticas.\n\n"
                "**Dicas**\n\n"
                "- Confira o preview antes de importar.\n"
                "- Usuário existente tem perfil atualizado."
            )
    
    # Tabs para diferentes funcionalidades administrativas
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏢 Sites", 
        "👥 Usuários", 
        "📊 Importar Dados", 
        "📈 Atualizar KPIs"
    ])
    
    with tab1:
        st.subheader("Gerenciar Sites")
        
        # Lista sites existentes
        sites = get_sites()
        
        if sites:
            st.write("**Sites Cadastrados:**")
            sites_df = pd.DataFrame(sites)
            st.dataframe(sites_df, width='stretch', hide_index=True)
        else:
            st.info("Nenhum site cadastrado.")
        
        # Formulário para novo site
        st.subheader("Adicionar Novo Site")
        
        with st.form("new_site_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                site_code = st.text_input("Código do Site", placeholder="Ex: BAERI")
                site_name = st.text_input("Nome do Site", placeholder="Ex: Base Aérea do Rio")
            
            with col2:
                site_type = st.selectbox(
                    "Tipo de Site",
                    options=["Base Aérea", "Aeroporto", "Unidade Operacional", "Outros"]
                )
                is_active = st.checkbox("Site Ativo", value=True)
            
            description = st.text_area("Descrição", height=100)
            
            submitted = st.form_submit_button("💾 Salvar Site", type="primary")
            
            if submitted:
                if not site_code or not site_name:
                    st.error("Código e nome são obrigatórios.")
                else:
                    try:
                        supabase = get_supabase_client()
                        
                        site_data = {
                            "code": site_code.upper(),
                            "name": site_name,
                            "type": site_type,
                            "description": description,
                            "is_active": is_active
                        }
                        
                        result = supabase.table("sites").insert(site_data).execute()
                        
                        if result.data:
                            st.success("✅ Site cadastrado com sucesso!")
                            st.rerun()
                        else:
                            st.error("Erro ao cadastrar site.")
                            
                    except Exception as e:
                        st.error(f"Erro: {str(e)}")
    
    with tab2:
        st.subheader("Gerenciar Usuários")
        
        # Lista usuários existentes
        users = get_users()
        
        if users:
            st.write("**Usuários Cadastrados:**")
            users_df = pd.DataFrame(users)
            st.dataframe(users_df, width='stretch', hide_index=True)
        else:
            st.info("Nenhum usuário cadastrado.")
        
        # Formulário para novo usuário
        st.subheader("Adicionar Novo Usuário")
        
        with st.form("new_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                email = st.text_input("E-mail do Usuário")
                role = st.selectbox(
                    "Papel",
                    options=["viewer", "editor", "admin"],
                    format_func=lambda x: {
                        "viewer": "Visualizador",
                        "editor": "Editor", 
                        "admin": "Administrador"
                    }[x]
                )
            
            with col2:
                # site_ids removido - campo não existe na tabela profiles
                # A tabela profiles não tem relação direta com sites
            
            is_active = st.checkbox("Usuário Ativo", value=True)
            
            submitted = st.form_submit_button("💾 Salvar Usuário", type="primary")
            
            if submitted:
                if not email:
                    st.error("E-mail é obrigatório.")
                else:
                    try:
                        supabase = get_supabase_client()
                        
                        # Verifica se o perfil já existe antes de criar
                        existing_profile = supabase.table("profiles").select("*").eq("email", email).execute()
                        
                        if existing_profile.data:
                            st.warning(f"⚠️ Já existe um perfil para o email {email}. Atualizando perfil existente...")
                            
                            # Atualiza perfil existente
                            profile_data = {
                                "role": role,
                                "status": "ativo" if is_active else "inativo"
                            }
                            
                            result = supabase.table("profiles").update(profile_data).eq("email", email).execute()
                            
                            if result.data:
                                st.success("✅ Perfil atualizado com sucesso!")
                                st.rerun()
                            else:
                                st.error("Erro ao atualizar perfil do usuário.")
                        else:
                            # Cria usuário no Auth
                            auth_response = supabase.auth.admin.create_user({
                                "email": email,
                                "password": "temp_password_123",  # Usuário deve alterar no primeiro login
                                "email_confirm": True
                            })
                            
                            if auth_response.user:
                                # Cria perfil do usuário
                                # Extrai o nome do email para usar como full_name
                                from auth.auth_utils import extract_name_from_email
                                full_name = extract_name_from_email(email)
                                
                                profile_data = {
                                    "email": email,
                                    "full_name": full_name,
                                    "role": role,
                                    "status": "ativo" if is_active else "inativo"
                                }
                                
                                result = supabase.table("profiles").insert(profile_data).execute()
                                
                                if result.data:
                                    st.success("✅ Usuário criado com sucesso!")
                                    st.info("🔑 Senha temporária: temp_password_123 (usuário deve alterar no primeiro login)")
                                    st.rerun()
                                else:
                                    st.error("Erro ao criar perfil do usuário.")
                            else:
                                st.error("Erro ao criar usuário no sistema de autenticação.")
                            
                    except Exception as e:
                        # Se o erro for de chave duplicada, tenta atualizar o perfil existente
                        if "duplicate key value violates unique constraint" in str(e):
                            try:
                                st.warning(f"⚠️ Perfil já existe para {email}. Atualizando perfil existente...")
                                
                                profile_data = {
                                    "role": role,
                                    "status": "ativo" if is_active else "inativo"
                                }
                                
                                result = supabase.table("profiles").update(profile_data).eq("email", email).execute()
                                
                                if result.data:
                                    st.success("✅ Perfil atualizado com sucesso!")
                                    st.rerun()
                                else:
                                    st.error("Erro ao atualizar perfil do usuário.")
                            except Exception as update_error:
                                st.error(f"Erro ao atualizar perfil: {str(update_error)}")
                        else:
                            st.error(f"Erro: {str(e)}")
    
    with tab3:
        st.subheader("Importar Dados")
        
        # Importação de horas trabalhadas
        st.subheader("📊 Importar Horas Trabalhadas")
        
        uploaded_hours = st.file_uploader(
            "Arquivo CSV de Horas Trabalhadas",
            type=['csv'],
            key="hours_upload",
            help="Formato esperado: year, month, hours (site_id removido da tabela)"
        )
        
        if uploaded_hours:
            try:
                hours_df = pd.read_csv(uploaded_hours)
                st.write("**Preview dos dados:**")
                st.dataframe(hours_df.head(), width='stretch')
                
                # Mapeamento de sites
                sites = get_sites()
                site_mapping = {site['code']: site['id'] for site in sites}
                
                if st.button("📥 Importar Horas", key="import_hours"):
                    success = import_hours_csv(hours_df, site_mapping)
                    if success:
                        st.rerun()
                        
            except Exception as e:
                st.error(f"Erro ao processar arquivo: {str(e)}")
        
        # Importação de acidentes
        st.subheader("🚨 Importar Acidentes")
        
        uploaded_accidents = st.file_uploader(
            "Arquivo CSV de Acidentes",
            type=['csv'],
            key="accidents_upload",
            help="Formato esperado: occurred_at (ou date), type (fatal/lesao/sem_lesao), description, classification (opcional), body_part (opcional), lost_days (opcional), root_cause (opcional), status (opcional, default: fechado)"
        )
        
        if uploaded_accidents:
            try:
                accidents_df = pd.read_csv(uploaded_accidents)
                st.write("**Preview dos dados:**")
                st.dataframe(accidents_df.head(), width='stretch')
                
                # Mapeamento de sites
                sites = get_sites()
                site_mapping = {site['code']: site['id'] for site in sites}
                
                if st.button("📥 Importar Acidentes", key="import_accidents"):
                    success = import_accidents_csv(accidents_df, site_mapping)
                    if success:
                        st.rerun()
                        
            except Exception as e:
                st.error(f"Erro ao processar arquivo: {str(e)}")
    
    with tab4:
        st.subheader("Atualizar KPIs")
        
        st.info("💡 Os KPIs são calculados automaticamente baseados nos dados de acidentes e horas trabalhadas.")
        
        if st.button("🔄 Recalcular KPIs", type="primary"):
            with st.spinner("Recalculando KPIs..."):
                try:
                    from services.kpi import calculate_frequency_rate, calculate_severity_rate
                    from managers.supabase_config import get_service_role_client
                    import datetime
                    
                    supabase = get_service_role_client()
                    
                    # Busca todos os dados de acidentes e horas trabalhadas
                    accidents_response = supabase.table("accidents").select(
                        "id, occurred_at, created_by, lost_days, type"
                    ).execute()
                    
                    hours_response = supabase.table("hours_worked_monthly").select(
                        "id, year, month, hours, created_by"
                    ).execute()
                    
                    accidents_data = accidents_response.data if accidents_response and hasattr(accidents_response, 'data') else []
                    hours_data = hours_response.data if hours_response and hasattr(hours_response, 'data') else []
                    
                    # Agrupa acidentes por mês/criador
                    from collections import defaultdict
                    import pandas as pd
                    
                    accidents_by_period = defaultdict(lambda: {'count': 0, 'fatalities': 0, 'lost_days': 0})
                    
                    for accident in accidents_data:
                        period = pd.to_datetime(accident['occurred_at']).strftime('%Y-%m')
                        accidents_by_period[period]['count'] += 1
                        # is_fatal removido - usa type para identificar fatais
                        if accident.get('type') == 'fatal':
                            accidents_by_period[period]['fatalities'] += 1
                        accidents_by_period[period]['lost_days'] += int(accident.get('lost_days', 0))
                    
                    # Agrupa horas por mês/criador
                    hours_by_period = defaultdict(lambda: 0)
                    
                    for hour_entry in hours_data:
                        period = f"{hour_entry['year']}-{str(hour_entry['month']).zfill(2)}"
                        hours_by_period[period] += float(hour_entry.get('hours', 0))
                    
                    # Limpa tabela de KPIs existentes (opcional - pode ser substituído por atualização incremental)
                    # supabase.table("kpi_monthly").delete().neq("id", 0).execute()
                    
                    # Calcula KPIs mensais
                    kpi_updates = []
                    for period, acc_data in accidents_by_period.items():
                        if period in hours_by_period:
                            hours = hours_by_period[period]
                            
                            # Calcular dias debitados para acidentes fatais (NBR 14280)
                            debited_days = acc_data['fatalities'] * 6000  # 6.000 dias por morte
                            
                            # Calcula taxas
                            freq_rate = calculate_frequency_rate(acc_data['count'], hours)
                            sev_rate = calculate_severity_rate(acc_data['lost_days'], hours, debited_days)
                            
                            # Verifica se já existe KPI para este período
                            existing_kpi = supabase.table("kpi_monthly").select("id").eq("period", f"{period}-01").execute()
                            
                            kpi_data = {
                                "period": f"{period}-01",
                                "accidents_total": acc_data['count'],
                                "fatalities": acc_data['fatalities'],
                                "lost_days_total": acc_data['lost_days'],
                                "hours": hours / 100,  # Armazena como centenas (176 representa 17.600 horas)
                                "frequency_rate": freq_rate,
                                "severity_rate": sev_rate,
                                "debited_days": debited_days
                            }
                            
                            if existing_kpi.data:
                                # Atualiza existente
                                supabase.table("kpi_monthly").update(kpi_data).eq("period", f"{period}-01").execute()
                            else:
                                # Insere novo
                                supabase.table("kpi_monthly").insert(kpi_data).execute()
                    
                    st.success(f"✅ KPIs recalculados com sucesso para {len(accidents_by_period)} períodos!")
                    
                except Exception as e:
                    st.error(f"Erro ao recalcular KPIs: {str(e)}")
        
        # Estatísticas do sistema
        st.subheader("📊 Estatísticas do Sistema")
        
        try:
            supabase = get_supabase_client()
            
            # Conta registros em cada tabela
            stats = {}
            
            tables = ['sites', 'accidents', 'near_misses', 'nonconformities', 'hours_worked_monthly']
            
            for table in tables:
                try:
                    result = supabase.table(table).select("id", count="exact").execute()
                    stats[table] = result.count
                except:
                    stats[table] = 0
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Sites", stats.get('sites', 0))
                # contractors removido - tabela não existe
            
            with col2:
                st.metric("Acidentes", stats.get('accidents', 0))
                st.metric("Quase-Acidentes", stats.get('near_misses', 0))
            
            with col3:
                st.metric("Não Conformidades", stats.get('nonconformities', 0))
                st.metric("Registros de Horas", stats.get('hours_worked_monthly', 0))
                
        except Exception as e:
            st.error(f"Erro ao carregar estatísticas: {str(e)}")

def get_sites():
    """Busca sites disponíveis"""
    try:
        supabase = get_supabase_client()
        response = supabase.table("sites").select("*").execute()
        return response.data
    except:
        return []

# get_contractors removido - tabela contractors não existe no banco

def get_users():
    """Busca usuários disponíveis"""
    try:
        supabase = get_supabase_client()
        response = supabase.table("profiles").select("*").execute()
        return response.data
    except:
        return []

if __name__ == "__main__":
    app({})
