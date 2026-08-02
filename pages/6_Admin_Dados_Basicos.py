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
                "- Usuário existente tem perfil atualizado.\n\n"
                "**📝 Feedback**\n"
                "- Encontrou um erro ou tem uma sugestão? Acesse **Conta → Feedbacks** para reportar!"
            )
    
    # Tabs para diferentes funcionalidades administrativas
    tab1, tab2, tab3, tab4 = st.tabs([
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
                        from managers.supabase_config import get_service_role_client
                        supabase = get_service_role_client()
                        if not supabase:
                            st.error("Erro ao conectar com o banco de dados")
                        else:
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

        # Solicitações pendentes de aprovação
        pending_users = [u for u in (get_users() or []) if (u.get("status") or "").lower() == "pendente"]
        if pending_users:
            st.markdown("### ⏳ Solicitações Pendentes")
            st.caption("Usuários que solicitaram acesso e aguardam aprovação.")
            for pending in pending_users:
                p_email = pending.get("email", "")
                p_name = pending.get("full_name") or "—"
                p_id = pending.get("id")
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 1, 1])
                    with c1:
                        st.markdown(f"**{p_name}**")
                        st.caption(p_email)
                    with c2:
                        if st.button("✅ Aprovar", key=f"approve_{p_id}", width='stretch'):
                            if _update_user_status(p_email, "ativo"):
                                st.success(f"Usuário {p_email} aprovado.")
                                st.rerun()
                    with c3:
                        if st.button("❌ Rejeitar", key=f"reject_{p_id}", width='stretch'):
                            if _update_user_status(p_email, "inativo"):
                                st.warning(f"Solicitação de {p_email} rejeitada.")
                                st.rerun()
            st.markdown("---")
        
        # Lista usuários existentes com edição inline de role e status
        users = get_users()

        if users:
            st.write("**Usuários Cadastrados:**")
            st.caption("Edite o **Papel** ou **Status** diretamente na tabela e clique em 'Salvar Alterações'.")

            # Preparar dataframe para exibição e edição
            users_df = pd.DataFrame(users)
            display_cols = ['full_name', 'email', 'role', 'status', 'plan', 'created_at']
            display_df = users_df[display_cols].copy()

            # Guarda snapshot original para detectar mudanças
            # Recria o original sempre que o data_editor for resetado ou na primeira carga
            if 'original_users_df' not in st.session_state or st.session_state.get('_reset_user_editor'):
                st.session_state.original_users_df = display_df.copy()
                st.session_state._reset_user_editor = False

            edited_df = st.data_editor(
                display_df,
                column_config={
                    "full_name": st.column_config.TextColumn("Nome", disabled=True),
                    "email": st.column_config.TextColumn("Email", disabled=True),
                    "role": st.column_config.SelectboxColumn(
                        "Papel",
                        options=["admin", "editor", "viewer"],
                        format_func=lambda x: {
                            "admin": "Administrador",
                            "editor": "Editor",
                            "viewer": "Visualizador"
                        }.get(x, x),
                        required=True,
                    ),
                    "status": st.column_config.SelectboxColumn(
                        "Status",
                        options=["ativo", "inativo", "pendente", "suspenso"],
                        required=True,
                    ),
                    "plan": st.column_config.TextColumn("Plano", disabled=True),
                    "created_at": st.column_config.DatetimeColumn("Criado em", disabled=True),
                },
                hide_index=True,
                use_container_width=True,
                key="user_editor",
                num_rows="fixed",
            )

            col_save, col_undo = st.columns([1, 4])
            with col_save:
                if st.button("💾 Salvar Alterações", type="primary", key="save_user_changes"):
                    changes_made = 0
                    current_user_email = (st.session_state.get('user_email', '') or '').lower().strip()

                    for idx, row in edited_df.iterrows():
                        if idx >= len(st.session_state.original_users_df):
                            continue
                        original_row = st.session_state.original_users_df.iloc[idx]
                        email = row['email']

                        role_changed = row['role'] != original_row['role']
                        status_changed = row['status'] != original_row['status']

                        if role_changed or status_changed:
                            # Proteção: admin não pode remover o próprio papel
                            if email.lower().strip() == current_user_email and row['role'] != 'admin':
                                st.error(f"⚠️ Você não pode remover seu próprio papel de administrador!")
                                continue

                            update_data = {}
                            if role_changed:
                                update_data['role'] = row['role']
                            if status_changed:
                                update_data['status'] = row['status']

                            try:
                                from managers.supabase_config import get_service_role_client
                                supabase = get_service_role_client()
                                if supabase:
                                    result = (
                                        supabase.table("profiles")
                                        .update(update_data)
                                        .eq("email", email.lower().strip())
                                        .execute()
                                    )
                                    if result.data:
                                        changes_made += 1
                            except Exception as e:
                                st.error(f"Erro ao atualizar {email}: {str(e)}")

                    if changes_made > 0:
                        st.success(f"✅ {changes_made} usuário(s) atualizado(s) com sucesso!")
                        # Atualiza snapshot e recarrega
                        st.session_state.original_users_df = edited_df.copy()
                        st.rerun()
                    else:
                        st.info("Nenhuma alteração detectada.")

            with col_undo:
                if st.button("🔄 Desfazer Alterações", key="undo_user_changes"):
                    # Remove o estado do widget para resetar ao valor original do banco
                    if 'user_editor' in st.session_state:
                        del st.session_state['user_editor']
                    st.session_state._reset_user_editor = True
                    st.rerun()
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
                password = st.text_input(
                    "Senha (opcional)",
                    type="password",
                    help="Se informada, cria login por e-mail no Supabase Auth. Sem senha, o usuário entra só via Google.",
                )
            
            is_active = st.checkbox("Usuário Ativo", value=True)
            
            submitted = st.form_submit_button("💾 Salvar Usuário", type="primary")
            
            if submitted:
                if not email:
                    st.error("E-mail é obrigatório.")
                elif password and len(password) < 6:
                    st.error("A senha deve ter pelo menos 6 caracteres.")
                else:
                    try:
                        from managers.supabase_config import get_service_role_client
                        from auth.auth_utils import extract_name_from_email
                        supabase = get_service_role_client()
                        if not supabase:
                            st.error("Erro ao conectar com o banco de dados")
                        else:
                            email_norm = email.lower().strip()
                            full_name = extract_name_from_email(email_norm)
                            status_val = "ativo" if is_active else "inativo"

                            # Conta Auth (e-mail/senha) — só se senha foi informada
                            if password:
                                try:
                                    supabase.auth.admin.create_user({
                                        "email": email_norm,
                                        "password": password,
                                        "email_confirm": True,
                                        "user_metadata": {"full_name": full_name},
                                    })
                                except Exception as auth_err:
                                    err_text = str(auth_err).lower()
                                    if "already" in err_text or "registered" in err_text or "exists" in err_text:
                                        st.warning(
                                            "Usuário já existe no Auth. Atualizando apenas o perfil."
                                        )
                                    else:
                                        raise

                            existing_profile = (
                                supabase.table("profiles")
                                .select("*")
                                .eq("email", email_norm)
                                .execute()
                            )

                            if existing_profile.data:
                                st.warning(
                                    f"⚠️ Já existe um perfil para o email {email_norm}. Atualizando..."
                                )
                                result = (
                                    supabase.table("profiles")
                                    .update({"role": role, "status": status_val, "full_name": full_name})
                                    .eq("email", email_norm)
                                    .execute()
                                )
                                if result.data:
                                    st.success("✅ Perfil atualizado com sucesso!")
                                    if password:
                                        st.info("Login por e-mail/senha disponível com a senha informada.")
                                    st.rerun()
                                else:
                                    st.error("Erro ao atualizar perfil do usuário.")
                            else:
                                profile_data = {
                                    "email": email_norm,
                                    "full_name": full_name,
                                    "role": role,
                                    "status": status_val,
                                }
                                result = supabase.table("profiles").insert(profile_data).execute()

                                if result.data:
                                    st.success("✅ Usuário criado com sucesso!")
                                    if password:
                                        st.info(
                                            "O usuário pode entrar com e-mail/senha ou com Google "
                                            "(se o e-mail for o mesmo)."
                                        )
                                    else:
                                        st.info(
                                            "Sem senha: o usuário acessa apenas via Google "
                                            "com este e-mail."
                                        )
                                    st.rerun()
                                else:
                                    st.error("Erro ao criar perfil do usuário.")
                            
                    except Exception as e:
                        # Se o erro for de chave duplicada, tenta atualizar o perfil existente
                        if "duplicate key value violates unique constraint" in str(e):
                            try:
                                from managers.supabase_config import get_service_role_client
                                supabase = get_service_role_client()
                                if supabase:
                                    email_norm = email.lower().strip()
                                    st.warning(f"⚠️ Perfil já existe para {email_norm}. Atualizando perfil existente...")
                                    
                                    profile_data = {
                                        "role": role,
                                        "status": "ativo" if is_active else "inativo"
                                    }
                                    
                                    result = supabase.table("profiles").update(profile_data).eq("email", email_norm).execute()
                                
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
        
        st.info("💡 **Importante**: Os KPIs precisam ser calculados manualmente através do botão abaixo.\n\n"
                "📋 **Requisitos para calcular KPIs:**\n"
                "1. Ter acidentes cadastrados na tabela `accidents`\n"
                "2. Ter horas trabalhadas cadastradas na tabela `hours_worked_monthly`\n"
                "3. Os dados devem estar no mesmo período (mês/ano) e vinculados ao mesmo usuário\n\n"
                "**Como funciona:** O sistema agrupa acidentes e horas por período (mês) e usuário, "
                "calcula as taxas de frequência e gravidade, e salva na tabela `kpi_monthly`.")
        
        # Verifica se há dados antes de permitir recalcular
        try:
            from managers.supabase_config import get_service_role_client
            supabase = get_service_role_client()
            
            accidents_count = supabase.table("accidents").select("id", count="exact").execute().count or 0
            hours_count = supabase.table("hours_worked_monthly").select("id", count="exact").execute().count or 0
            kpis_count = supabase.table("kpi_monthly").select("id", count="exact").execute().count or 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Acidentes Cadastrados", accidents_count)
            with col2:
                st.metric("Registros de Horas", hours_count)
            with col3:
                st.metric("KPIs Calculados", kpis_count)
            
            if accidents_count == 0 and hours_count == 0:
                st.warning("⚠️ **Nenhum dado encontrado**: Cadastre acidentes e/ou horas trabalhadas primeiro!")
            elif accidents_count == 0:
                st.warning("⚠️ **Sem acidentes**: Cadastre acidentes para calcular KPIs!")
            elif hours_count == 0:
                st.warning("⚠️ **Sem horas trabalhadas**: Cadastre horas trabalhadas para calcular KPIs!")
            elif kpis_count == 0:
                st.info("ℹ️ **KPIs não calculados**: Clique no botão abaixo para calcular os KPIs baseados nos dados existentes.")
            else:
                st.success(f"✅ **KPIs já calculados**: Existem {kpis_count} registros de KPI calculados.")
        except Exception as e:
            st.error(f"Erro ao verificar dados: {str(e)}")
        
        if st.button("🔄 Recalcular KPIs", type="primary", key="btn_recalculate_kpis"):
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
                    # pd já está importado no topo do arquivo
                    
                    accidents_by_period_user = defaultdict(lambda: {'count': 0, 'fatalities': 0, 'lost_days': 0})
                    
                    for accident in accidents_data:
                        period = pd.to_datetime(accident['occurred_at']).strftime('%Y-%m')
                        user_id = accident.get('created_by')
                        if user_id:
                            key = f"{period}_{user_id}"
                            accidents_by_period_user[key]['count'] += 1
                            # is_fatal removido - usa type para identificar fatais
                            if accident.get('type') == 'fatal':
                                accidents_by_period_user[key]['fatalities'] += 1
                            accidents_by_period_user[key]['lost_days'] += int(accident.get('lost_days', 0))
                    
                    # Agrupa horas por mês/criador
                    hours_by_period_user = defaultdict(lambda: 0)
                    
                    for hour_entry in hours_data:
                        period = f"{hour_entry['year']}-{str(hour_entry['month']).zfill(2)}"
                        user_id = hour_entry.get('created_by')
                        if user_id:
                            key = f"{period}_{user_id}"
                            hours_by_period_user[key] += float(hour_entry.get('hours', 0))
                    
                    # Limpa tabela de KPIs existentes (opcional - pode ser substituído por atualização incremental)
                    # supabase.table("kpi_monthly").delete().neq("id", 0).execute()
                    
                    # Calcula KPIs mensais por usuário
                    kpi_updates = []
                    for key, acc_data in accidents_by_period_user.items():
                        if key in hours_by_period_user:
                            period, user_id = key.split('_', 1)
                            hours = hours_by_period_user[key]
                            
                            # Calcular dias debitados para acidentes fatais (NBR 14280)
                            debited_days = acc_data['fatalities'] * 6000  # 6.000 dias por morte
                            
                            # ✅ CORRIGIDO: hours vem da tabela hours_worked_monthly em HORAS REAIS (182.0 = 182 horas reais)
                            # A função espera receber em centenas e multiplica por 100 internamente
                            # Então dividimos por 100 para converter para centenas antes de calcular
                            hours_in_hundreds = hours / 100  # Converte 182.0 horas reais para 1.82 centenas
                            freq_rate = calculate_frequency_rate(acc_data['count'], hours_in_hundreds)
                            sev_rate = calculate_severity_rate(acc_data['lost_days'], hours_in_hundreds, debited_days)
                            
                            # Verifica se já existe KPI para este período e usuário
                            existing_kpi = supabase.table("kpi_monthly").select("id").eq("period", f"{period}-01").eq("created_by", user_id).execute()
                            
                            kpi_data = {
                                "period": f"{period}-01",
                                "created_by": user_id,  # UUID do usuário
                                "accidents_total": acc_data['count'],
                                "fatalities": acc_data['fatalities'],
                                "lost_days_total": acc_data['lost_days'],
                                "hours": hours_in_hundreds,  # ✅ Armazena em centenas (182.0 → 1.82 na tabela)
                                "frequency_rate": freq_rate,
                                "severity_rate": sev_rate,
                                "debited_days": debited_days
                            }
                            
                            if existing_kpi.data:
                                # Atualiza existente
                                supabase.table("kpi_monthly").update(kpi_data).eq("period", f"{period}-01").eq("created_by", user_id).execute()
                            else:
                                # Insere novo
                                supabase.table("kpi_monthly").insert(kpi_data).execute()
                    
                    # Processa horas sem acidentes (cria KPIs com zero acidentes)
                    for key, hours in hours_by_period_user.items():
                        if key not in accidents_by_period_user:
                            period, user_id = key.split('_', 1)
                            
                            # Verifica se já existe KPI para este período e usuário
                            existing_kpi = supabase.table("kpi_monthly").select("id").eq("period", f"{period}-01").eq("created_by", user_id).execute()
                            
                            if not existing_kpi.data:
                                kpi_data = {
                                    "period": f"{period}-01",
                                    "created_by": user_id,
                                    "accidents_total": 0,
                                    "fatalities": 0,
                                    "lost_days_total": 0,
                                    "hours": hours / 100,  # ✅ Converte horas reais para centenas (182.0 → 1.82 na tabela)
                                    "frequency_rate": 0,
                                    "severity_rate": 0,
                                    "debited_days": 0
                                }
                                supabase.table("kpi_monthly").insert(kpi_data).execute()
                    
                    total_kpis = len(accidents_by_period_user) + len([k for k in hours_by_period_user.keys() if k not in accidents_by_period_user])
                    st.success(f"✅ KPIs recalculados com sucesso!\n\n"
                              f"📊 **Resumo:**\n"
                              f"- Períodos com acidentes processados: {len(accidents_by_period_user)}\n"
                              f"- Períodos com horas (sem acidentes) processados: {len([k for k in hours_by_period_user.keys() if k not in accidents_by_period_user])}\n"
                              f"- **Total de KPIs calculados/atualizados: {total_kpis}**\n\n"
                              f"💡 **Dica**: Atualize os KPIs sempre que cadastrar novos acidentes ou horas trabalhadas.")
                    
                except Exception as e:
                    st.error(f"Erro ao recalcular KPIs: {str(e)}")
        
        # Estatísticas do sistema
        st.subheader("📊 Estatísticas do Sistema")
        
        try:
            from managers.supabase_config import get_service_role_client
            supabase = get_service_role_client()
            if not supabase:
                st.error("Erro ao conectar com o banco de dados")
            else:
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
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            return []
        response = supabase.table("sites").select("*").execute()
        return response.data if response.data else []
    except:
        return []

# get_contractors removido - tabela contractors não existe no banco

def get_users():
    """Busca usuários disponíveis"""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            return []
        response = supabase.table("profiles").select("*").execute()
        return response.data
    except:
        return []


def _update_user_status(email: str, status: str) -> bool:
    """Atualiza o status de um perfil (aprovar/rejeitar solicitação)."""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            st.error("Erro ao conectar com o banco de dados")
            return False
        result = (
            supabase.table("profiles")
            .update({"status": status})
            .eq("email", email.lower().strip())
            .execute()
        )
        return bool(result.data)
    except Exception as e:
        st.error(f"Erro ao atualizar status: {str(e)}")
        return False

if __name__ == "__main__":
    app({})
