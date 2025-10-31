import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from services.uploads import upload_evidence, get_attachments
from components.cards import create_metric_row, create_bar_chart, create_pie_chart
from components.filters import apply_filters_to_df
from managers.supabase_config import get_supabase_client

def fetch_near_misses(start_date=None, end_date=None):
    """Busca dados de quase-acidentes - filtra por usuário logado"""
    try:
        from managers.supabase_config import get_supabase_client, get_service_role_client
        from auth.auth_utils import get_user_id, is_admin, get_user_email
        user_id = get_user_id()
        user_email = get_user_email()
        
        if not user_id:
            return pd.DataFrame()
        
        # Admin usa service_role para contornar RLS e ver todos os dados
        if is_admin():
            supabase = get_service_role_client()
        else:
            supabase = get_supabase_client()
        
        query = supabase.table("near_misses").select("*")
        
        # Filtra por usuário logado, exceto se for admin
        # Admin vê todos os dados sem filtro de created_by
        if not is_admin():
            # Usuário comum vê apenas seus próprios quase-acidentes
            query = query.eq("created_by", user_id)
        # Admin vê todos os quase-acidentes - não aplica filtro de created_by
        
        if start_date:
            query = query.gte("occurred_at", start_date.isoformat())
        if end_date:
            query = query.lte("occurred_at", end_date.isoformat())
            
        response = query.order("occurred_at", desc=True).execute()
        
        if response and hasattr(response, 'data'):
            df = pd.DataFrame(response.data) if response.data else pd.DataFrame()
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao buscar quase-acidentes: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return pd.DataFrame()

def app(filters=None):
    # Verifica autenticação e trial
    from auth.auth_utils import require_login
    require_login()
    
    st.title("⚠️ Quase-Acidentes")
    
    # Busca filtros do session state se não foram passados como parâmetro
    if filters is None:
        filters = st.session_state.get('filters', {})
    
    # Tabs para diferentes visualizações
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Análise", "📋 Registros", "📎 Evidências", "➕ Novo Quase-Acidente", "✅ Ações Corretivas"])
    
    with tab1:
        st.subheader("Análise de Quase-Acidentes")
        # Ajuda via popover
        c1, c2 = st.columns([6, 1])
        with c2:
            with st.popover("❓ Ajuda"):
                st.markdown(
                    "**Guia rápido**\n\n"
                    "1) Ajuste filtros (datas/usuários) na sidebar.\n"
                    "2) Veja métricas por risco (alto/médio/baixo).\n"
                    "3) Explore gráficos por severidade e mês.\n\n"
                    "**Dicas**\n\n"
                    "- Severidade potencial é normalizada em Baixo/Médio/Alto.\n"
                    "- Sem resultados? Amplie o período ou limpe filtros.\n\n"
                    "**📝 Feedback**\n"
                    "- Encontrou um erro? Acesse **Conta → Feedbacks** para reportar!"
                )
        with st.expander("Guia rápido de análise", expanded=False):
            st.markdown(
                "1. Ajuste os filtros (lado esquerdo) para recortar o período e usuários.\n"
                "2. Verifique as métricas por risco (alto/médio/baixo).\n"
                "3. Explore os gráficos por severidade e mês para tendências.\n"
                "4. Use 'Registros' para buscar descrições específicas."
            )
        with st.popover("❓ Dicas"):
            st.markdown(
                "- A severidade potencial é normalizada em Baixo/Médio/Alto.\n"
                "- Sem resultados? Amplie o período ou limpe filtros.\n\n"
                "**📝 Encontrou um erro ou tem uma sugestão?**\n"
                "- Acesse **Conta → Feedbacks** no menu para reportar ou sugerir melhorias!"
            )
        
        # Busca dados
        with st.spinner("Carregando dados de quase-acidentes..."):
            df = fetch_near_misses(
                start_date=filters.get("start_date"),
                end_date=filters.get("end_date")
            )
        
        if df.empty:
            # Verifica se é problema de autenticação ou realmente não há dados
            from auth.auth_utils import get_user_id, get_user_email
            user_id = get_user_id()
            user_email = get_user_email()
            
            if not user_id:
                st.error("❌ **Erro**: Usuário não autenticado. Faça login novamente.")
            else:
                st.warning("Nenhum quase-acidente encontrado com os filtros aplicados.")
        else:
            # Aplica filtros adicionais
            df = apply_filters_to_df(df, filters)
            
            # Normaliza severidade potencial para 3 níveis: low/medium/high
            if 'potential_severity' in df.columns:
                sev_map = {
                    'baixa': 'low',
                    'media': 'medium',
                    'alta': 'high',
                    'low': 'low',
                    'medium': 'medium',
                    'high': 'high'
                }
                df['_severity_norm'] = (
                    df['potential_severity']
                    .astype(str)
                    .str.lower()
                    .map(sev_map)
                    .fillna(df['potential_severity'].astype(str).str.lower())
                )
            else:
                df['_severity_norm'] = []

            # Métricas principais
            total_near_misses = len(df)
            high_risk = len(df[df['_severity_norm'] == 'high']) if '_severity_norm' in df.columns else 0
            medium_risk = len(df[df['_severity_norm'] == 'medium']) if '_severity_norm' in df.columns else 0
            low_risk = len(df[df['_severity_norm'] == 'low']) if '_severity_norm' in df.columns else 0
            
            metrics = [
                {
                    "title": "Total de Quase-Acidentes",
                    "value": total_near_misses,
                    "icon": "⚠️",
                    "color": "warning" if total_near_misses > 0 else "success"
                },
                {
                    "title": "Alto Risco",
                    "value": high_risk,
                    "icon": "🔴",
                    "color": "danger" if high_risk > 0 else "success"
                },
                {
                    "title": "Médio Risco",
                    "value": medium_risk,
                    "icon": "🟡",
                    "color": "warning"
                },
                {
                    "title": "Baixo Risco",
                    "value": low_risk,
                    "icon": "🟢",
                    "color": "success"
                }
            ]
            
            create_metric_row(metrics)
            
            # Gráficos
            col1, col2 = st.columns(2)
            
            with col1:
                # Distribuição por severidade potencial - Simplificada
                if '_severity_norm' in df.columns and not df['_severity_norm'].empty:
                    severity_counts = df['_severity_norm'].value_counts()
                    severity_names = {'low': 'Baixo', 'medium': 'Médio', 'high': 'Alto'}
                    
                    fig1 = px.pie(
                        values=severity_counts.values,
                        names=[severity_names.get(s, s) for s in severity_counts.index],
                        title="Distribuição por Severidade Potencial",
                        color_discrete_sequence=['#28a745', '#ffc107', '#dc3545']  # Verde, Amarelo, Vermelho
                    )
                    fig1.update_layout(
                        height=400,
                        font=dict(size=12)
                    )
                    st.plotly_chart(fig1, width='stretch')
                else:
                    st.info("📊 **Distribuição por Severidade**\n\nNenhum dado de severidade disponível.")
            
            with col2:
                # Quase-acidentes por mês - Simplificada
                if 'occurred_at' in df.columns:
                    df['month'] = pd.to_datetime(df['occurred_at']).dt.to_period('M')
                    monthly_counts = df.groupby('month').size().reset_index(name='count')
                    monthly_counts['month'] = monthly_counts['month'].astype(str)
                    
                    fig2 = px.bar(
                        monthly_counts,
                        x='month',
                        y='count',
                        title="Quase-Acidentes por Mês",
                        color='count',
                        color_continuous_scale="Oranges"
                    )
                    fig2.update_layout(
                        height=400,
                        xaxis_title="Mês",
                        yaxis_title="Número de Quase-Acidentes",
                        showlegend=False,
                        font=dict(size=12)
                    )
                    fig2.update_traces(marker_line_width=0)
                    st.plotly_chart(fig2, width='stretch')
                else:
                    st.info("📅 **Quase-Acidentes por Mês**\n\nNenhum dado de data disponível.")
            
            # Análise por status - Simplificada
            if 'status' in df.columns and not df['status'].isna().all():
                st.subheader("📊 Análise por Status")
                status_counts = df['status'].value_counts()
                status_names = {'aberto': 'Aberto', 'fechado': 'Fechado'}
                
                fig3 = px.bar(
                    x=status_counts.index,
                    y=status_counts.values,
                    title="Quase-Acidentes por Status",
                    color=status_counts.values,
                    color_continuous_scale="Greens"
                )
                fig3.update_layout(
                    height=400,
                    xaxis_title="Status",
                    yaxis_title="Número de Quase-Acidentes",
                    showlegend=False,
                    font=dict(size=12)
                )
                fig3.update_traces(marker_line_width=0)
                st.plotly_chart(fig3, width='stretch')
            else:
                st.info("📊 **Análise por Status**\n\nNenhum dado de status disponível.")
    
    with tab2:
        st.subheader("Registros de Quase-Acidentes")
        
        if not df.empty:
            # Filtros adicionais para a tabela
            col1, col2, col3 = st.columns(3)
            
            with col1:
                severity_filter = st.selectbox(
                    "Filtrar por Severidade Potencial",
                    options=["Todas"] + list(df['potential_severity'].unique()) if 'potential_severity' in df.columns else ["Todas"],
                    key="near_miss_severity_filter"
                )
            
            with col2:
                status_filter = st.selectbox(
                    "Filtrar por Status",
                    options=["Todos"] + list(df['status'].unique()) if 'status' in df.columns else ["Todos"],
                    key="near_miss_status_filter"
                )
            
            with col3:
                search_term = st.text_input("Buscar na descrição", key="near_miss_search")
            
            # Aplica filtros
            filtered_df = df.copy()
            
            if severity_filter != "Todas" and 'potential_severity' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['potential_severity'] == severity_filter]
            
            if status_filter != "Todos" and 'status' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['status'] == status_filter]
            
            if search_term and 'description' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['description'].str.contains(search_term, case=False, na=False)]
            
            # Exibe tabela
            display_cols = ['occurred_at', 'potential_severity', 'description', 'status']
            available_cols = [col for col in display_cols if col in filtered_df.columns]
            
            if available_cols:
                st.dataframe(
                    filtered_df[available_cols],
                    width='stretch',
                    hide_index=True
                )
            else:
                st.dataframe(filtered_df, width='stretch', hide_index=True)
        else:
            st.info("Nenhum quase-acidente encontrado.")
    
    with tab3:
        st.subheader("Evidências dos Quase-Acidentes")
        
        if not df.empty:
            # Seleciona quase-acidente para ver evidências
            near_miss_options = {}
            for idx, row in df.iterrows():
                near_miss_id = row.get('id', idx)
                description = row.get('description', f'Quase-acidente {near_miss_id}')[:50]
                date_str = row.get('occurred_at', 'Data não informada')
                near_miss_options[f"{date_str} - {description}..."] = near_miss_id
            
            selected_near_miss = st.selectbox(
                "Selecionar Quase-Acidente",
                options=list(near_miss_options.keys()),
                key="evidence_near_miss_selector"
            )
            
            if selected_near_miss:
                near_miss_id = near_miss_options[selected_near_miss]
                
                # Busca evidências
                attachments = get_attachments("near_miss", str(near_miss_id))
                
                if attachments:
                    st.write(f"**Evidências para o quase-acidente selecionado:**")
                    
                    for attachment in attachments:
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.write(f"📎 {attachment['filename']}")
                            if attachment.get('description'):
                                st.caption(attachment['description'])
                        
                        with col2:
                            if st.button("📥 Download", key=f"download_{attachment['id']}"):
                                file_data = download_attachment(attachment['bucket'], attachment['path'])
                                if file_data:
                                    st.download_button(
                                        "💾 Baixar Arquivo",
                                        file_data,
                                        attachment['filename'],
                                        key=f"download_btn_{attachment['id']}"
                                    )
                        
                        with col3:
                            if st.button("🗑️ Remover", key=f"remove_{attachment['id']}"):
                                if delete_attachment(attachment['id']):
                                    st.success("Evidência removida!")
                                    st.rerun()
                else:
                    st.info("Nenhuma evidência encontrada para este quase-acidente.")
        else:
            st.info("Nenhum quase-acidente encontrado para exibir evidências.")
    
    with tab4:
        st.subheader("Registrar Novo Quase-Acidente")
        
        with st.form("new_near_miss_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                date_input = st.date_input("Data do Quase-Acidente", value=date.today())
                potential_severity = st.selectbox(
                    "Severidade Potencial",
                    options=["baixa", "media", "alta"],
                    format_func=lambda x: {
                        "baixa": "Baixa",
                        "media": "Média", 
                        "alta": "Alta"
                    }[x]
                )
            
            with col2:
                status = st.selectbox(
                    "Status",
                    options=["aberto", "fechado"],
                    format_func=lambda x: {
                        "aberto": "Aberto",
                        "fechado": "Fechado"
                    }[x]
                )
            
            # employee_id removido - campo não existe na tabela near_misses
            
            description = st.text_area("Descrição do Quase-Acidente", height=100)
            # preventive_actions removido - campo não existe na tabela near_misses
            
            # Upload de evidências
            uploaded_files = st.file_uploader(
                "Evidências (Fotos, PDFs, etc.)",
                accept_multiple_files=True,
                type=['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx']
            )
            
            submitted = st.form_submit_button("💾 Salvar Quase-Acidente", type="primary")
            
            if submitted:
                if not description.strip():
                    st.error("Descrição é obrigatória.")
                else:
                    try:
                        from managers.supabase_config import get_supabase_client
                        from auth.auth_utils import get_user_id
                        supabase = get_supabase_client()
                        
                        user_id = get_user_id()
                        if not user_id:
                            st.error("Usuário não autenticado.")
                            return
                        
                        # Insere quase-acidente
                        near_miss_data = {
                            "occurred_at": date_input.isoformat(),
                            "potential_severity": potential_severity,
                            "description": description,
                            "status": status,
                            "created_by": user_id
                        }
                        # employee_id removido - campo não existe na tabela near_misses
                        
                        result = supabase.table("near_misses").insert(near_miss_data).execute()
                        
                        if result.data:
                            near_miss_id = result.data[0]['id']
                            st.success("✅ Quase-acidente registrado com sucesso!")
                            
                            # Registra log da ação
                            try:
                                from services.user_logs import log_action
                                log_action(
                                    action_type="create",
                                    entity_type="near_miss",
                                    description=f"Quase-acidente criado: {description[:100]}...",
                                    entity_id=near_miss_id,
                                    metadata={"potential_severity": potential_severity, "status": status}
                                )
                            except:
                                pass  # Não interrompe o fluxo se houver erro no log
                            
                            # Upload de evidências
                            if uploaded_files:
                                for uploaded_file in uploaded_files:
                                    file_bytes = uploaded_file.read()
                                    upload_evidence(
                                        file_bytes,
                                        uploaded_file.name,
                                        "near_miss",
                                        str(near_miss_id),
                                        f"Evidência do quase-acidente de {date_input}"
                                    )
                                st.success(f"✅ {len(uploaded_files)} evidência(s) enviada(s)!")
                            
                            st.rerun()
                        else:
                            st.error("Erro ao salvar quase-acidente.")
                            
                    except Exception as e:
                        st.error(f"Erro: {str(e)}")
    
    with tab5:
        st.subheader("✅ Ações Corretivas")
        st.info("📋 Registre e gerencie ações corretivas relacionadas aos quase-acidentes usando a metodologia 5W2H")
        
        # Busca todos os quase-acidentes para seleção
        if df.empty:
            st.warning("Nenhum quase-acidente encontrado. Registre quase-acidentes primeiro para criar ações corretivas.")
        else:
            # Seleção de quase-acidente
            near_miss_options = {f"ID: {row['id'][:8]}... - {row.get('description', 'Sem descrição')[:50]}": row['id'] 
                              for _, row in df.iterrows()}
            
            selected_nm_id = st.selectbox(
                "Selecione o Quase-Acidente",
                options=list(near_miss_options.keys()),
                help="Selecione o quase-acidente para ver ou criar ações corretivas"
            )
            
            if selected_nm_id:
                near_miss_id = near_miss_options[selected_nm_id]
                
                # Busca ações existentes
                from services.actions import get_actions_by_entity, create_action, update_action_status, delete_action, action_form
                
                actions = get_actions_by_entity("near_miss", near_miss_id)
                
                # Mostra ações existentes
                if actions:
                    st.markdown("### Ações Corretivas Existentes")
                    for action in actions:
                        with st.expander(f"🔹 {action.get('what', 'Sem descrição')[:60]}... - Status: {action.get('status', 'N/A')}"):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown(f"**O QUE:** {action.get('what', '-')}")
                                st.markdown(f"**QUEM:** {action.get('who', '-')}")
                                st.markdown(f"**QUANDO:** {action.get('when_date', '-')}")
                                st.markdown(f"**ONDE:** {action.get('where_text', '-')}")
                                st.markdown(f"**POR QUÊ:** {action.get('why', '-')}")
                                st.markdown(f"**COMO:** {action.get('how', '-')}")
                                if action.get('how_much'):
                                    st.markdown(f"**QUANTO:** R$ {action.get('how_much', 0):,.2f}")
                            
                            with col2:
                                # Atualizar status
                                new_status = st.selectbox(
                                    "Alterar Status",
                                    options=["aberta", "em_andamento", "fechada"],
                                    index=["aberta", "em_andamento", "fechada"].index(action.get("status", "aberta")),
                                    key=f"status_{action.get('id')}"
                                )
                                
                                if new_status != action.get("status"):
                                    if st.button("Atualizar", key=f"update_{action.get('id')}"):
                                        if update_action_status(action.get('id'), new_status):
                                            st.success("Status atualizado!")
                                            st.rerun()
                                
                                if st.button("🗑️ Remover", key=f"delete_{action.get('id')}"):
                                    if delete_action(action.get('id')):
                                        st.success("Ação removida!")
                                        st.rerun()
                else:
                    st.info("Nenhuma ação corretiva registrada para este quase-acidente.")
                
                # Formulário para nova ação
                st.markdown("---")
                st.markdown("### ➕ Nova Ação Corretiva")
                
                new_action = action_form("near_miss", near_miss_id)
                if new_action:
                    if create_action(new_action):
                        st.success("✅ Ação corretiva registrada com sucesso!")
                        st.rerun()

def download_attachment(bucket, path):
    """Download de anexo"""
    try:
        supabase = get_supabase_client()
        response = supabase.storage.from_(bucket).download(path)
        return response
    except:
        return None

def delete_attachment(attachment_id):
    """Remove anexo"""
    try:
        supabase = get_supabase_client()
        supabase.table("attachments").delete().eq("id", attachment_id).execute()
        return True
    except:
        return False

def get_employees():
    """Busca funcionários (employees) - filtra por usuário logado"""
    try:
        from services.employees import get_all_employees
        employees = get_all_employees()
        # Retorna apenas os campos necessários para compatibilidade
        return [{"id": e.get("id"), "full_name": e.get("full_name"), "department": e.get("department")} for e in employees]
    except:
        return []

if __name__ == "__main__":
    app({})
