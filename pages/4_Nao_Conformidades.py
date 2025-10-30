import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from services.uploads import upload_evidence, get_attachments
from components.cards import create_metric_row, create_bar_chart, create_pie_chart
from components.filters import apply_filters_to_df
from managers.supabase_config import get_supabase_client

def fetch_nonconformities(site_codes=None, start_date=None, end_date=None):
    """Busca dados de não conformidades"""
    try:
        supabase = get_supabase_client()
        query = supabase.table("nonconformities").select("*")
        
        if site_codes:
            sites_response = supabase.table("sites").select("id, code").in_("code", site_codes).execute()
            site_ids = [site['id'] for site in sites_response.data]
            query = query.in_("site_id", site_ids)
        
        if start_date:
            query = query.gte("occurred_at", start_date.isoformat())
        if end_date:
            query = query.lte("occurred_at", end_date.isoformat())
            
        data = query.order("occurred_at", desc=True).execute().data
        df = pd.DataFrame(data)

        # Normalizações para UI
        if not df.empty:
            # Renomeia standard_ref -> norm_reference (se existir)
            if 'standard_ref' in df.columns and 'norm_reference' not in df.columns:
                df['norm_reference'] = df['standard_ref']
            # Mapeia status pt-br -> status normalizado (open/in_progress/closed)
            if 'status' in df.columns:
                status_map = {
                    'aberta': 'open',
                    'tratando': 'in_progress',
                    'encerrada': 'closed',
                    'open': 'open',
                    'in_progress': 'in_progress',
                    'closed': 'closed'
                }
                df['status'] = df['status'].astype(str).str.lower().map(status_map).fillna(df['status'])
            # Mapeia severidade pt-br -> low/medium/high/critical
            if 'severity' in df.columns:
                sev_map = {
                    'leve': 'low',
                    'moderada': 'medium',
                    'grave': 'high',
                    'critica': 'critical',
                    'crítica': 'critical',
                    'low': 'low',
                    'medium': 'medium',
                    'high': 'high',
                    'critical': 'critical'
                }
                df['severity'] = df['severity'].astype(str).str.lower().map(sev_map).fillna(df['severity'])
        
        return df
    except Exception as e:
        st.error(f"Erro ao buscar não conformidades: {str(e)}")
        return pd.DataFrame()

def app(filters=None):
    # Busca filtros do session state se não foram passados como parâmetro
    if filters is None:
        filters = st.session_state.get('filters', {})
    st.title("📋 Não Conformidades")
    
    # Tabs para diferentes visualizações
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Análise", "📋 Registros", "📎 Evidências", "➕ Nova Não Conformidade"])
    
    with tab1:
        st.subheader("Análise de Não Conformidades")
        
        # Busca dados
        with st.spinner("Carregando dados de não conformidades..."):
            df = fetch_nonconformities(
                site_codes=filters.get("sites"),
                start_date=filters.get("start_date"),
                end_date=filters.get("end_date")
            )
        
        if df.empty:
            st.warning("Nenhuma não conformidade encontrada com os filtros aplicados.")
        else:
            # Aplica filtros adicionais
            df = apply_filters_to_df(df, filters)
            
            # Métricas principais
            total_nc = len(df)
            open_nc = len(df[df['status'] == 'open']) if 'status' in df.columns else 0
            closed_nc = len(df[df['status'] == 'closed']) if 'status' in df.columns else 0
            overdue_nc = len(df[df['status'] == 'overdue']) if 'status' in df.columns else 0
            
            # Calcula dias médios de resolução
            if 'status' in df.columns and 'resolution_date' in df.columns:
                closed_df = df[df['status'] == 'closed']
                if not closed_df.empty and 'occurred_at' in closed_df.columns:
                    closed_df['resolution_days'] = (pd.to_datetime(closed_df['resolution_date']) - pd.to_datetime(closed_df['occurred_at'])).dt.days
                    avg_resolution_days = closed_df['resolution_days'].mean()
                else:
                    avg_resolution_days = 0
            else:
                avg_resolution_days = 0
            
            metrics = [
                {
                    "title": "Total de N/C",
                    "value": total_nc,
                    "icon": "📋",
                    "color": "warning" if total_nc > 0 else "success"
                },
                {
                    "title": "Abertas",
                    "value": open_nc,
                    "icon": "🔴",
                    "color": "danger" if open_nc > 0 else "success"
                },
                {
                    "title": "Fechadas",
                    "value": closed_nc,
                    "icon": "✅",
                    "color": "success"
                },
                {
                    "title": "Dias Médios Resolução",
                    "value": f"{avg_resolution_days:.1f}",
                    "icon": "⏱️",
                    "color": "info"
                }
            ]
            
            create_metric_row(metrics)
            
            # Gráficos
            col1, col2 = st.columns(2)
            
            with col1:
                # Distribuição por status
                if 'status' in df.columns:
                    status_counts = df['status'].value_counts()
                    fig1 = create_pie_chart(
                        pd.DataFrame({
                            'status': status_counts.index,
                            'count': status_counts.values
                        }),
                        'status',
                        'count',
                        'Distribuição por Status'
                    )
                    st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                # N/C por mês
                if 'occurred_at' in df.columns:
                    df['month'] = pd.to_datetime(df['occurred_at']).dt.to_period('M')
                    monthly_counts = df.groupby('month').size().reset_index(name='count')
                    monthly_counts['month'] = monthly_counts['month'].astype(str)
                    
                    fig2 = create_bar_chart(
                        monthly_counts,
                        'month',
                        'count',
                        'Não Conformidades por Mês'
                    )
                    st.plotly_chart(fig2, use_container_width=True)
            
            # Análise por norma
            if 'norm_reference' in df.columns:
                st.subheader("Análise por Norma")
                norm_counts = df['norm_reference'].value_counts()
                
                fig3 = create_bar_chart(
                    pd.DataFrame({
                        'norm_reference': norm_counts.index,
                        'count': norm_counts.values
                    }),
                    'norm_reference',
                    'count',
                    'Não Conformidades por Norma'
                )
                st.plotly_chart(fig3, use_container_width=True)
            
            # Análise por gravidade
            if 'severity' in df.columns:
                st.subheader("Análise por Gravidade")
                severity_counts = df['severity'].value_counts()
                
                fig4 = create_bar_chart(
                    pd.DataFrame({
                        'severity': severity_counts.index,
                        'count': severity_counts.values
                    }),
                    'severity',
                    'count',
                    'Não Conformidades por Gravidade'
                )
                st.plotly_chart(fig4, use_container_width=True)
    
    with tab2:
        st.subheader("Registros de Não Conformidades")
        
        if not df.empty:
            # Filtros adicionais para a tabela
            col1, col2, col3 = st.columns(3)
            
            with col1:
                status_filter = st.selectbox(
                    "Filtrar por Status",
                    options=["Todos"] + list(df['status'].unique()) if 'status' in df.columns else ["Todos"],
                    key="nc_status_filter"
                )
            
            with col2:
                norm_filter = st.selectbox(
                    "Filtrar por Norma",
                    options=["Todas"] + list(df['norm_reference'].unique()) if 'norm_reference' in df.columns else ["Todas"],
                    key="nc_norm_filter"
                )
            
            with col3:
                search_term = st.text_input("Buscar na descrição", key="nc_search")
            
            # Aplica filtros
            filtered_df = df.copy()
            
            if status_filter != "Todos" and 'status' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['status'] == status_filter]
            
            if norm_filter != "Todas" and 'norm_reference' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['norm_reference'] == norm_filter]
            
            if search_term and 'description' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['description'].str.contains(search_term, case=False, na=False)]
            
            # Exibe tabela
            display_cols = ['occurred_at', 'norm_reference', 'severity', 'status', 'description', 'corrective_actions']
            available_cols = [col for col in display_cols if col in filtered_df.columns]
            
            if available_cols:
                st.dataframe(
                    filtered_df[available_cols],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma não conformidade encontrada.")
    
    with tab3:
        st.subheader("Evidências das Não Conformidades")
        
        if not df.empty:
            # Seleciona não conformidade para ver evidências
            nc_options = {}
            for idx, row in df.iterrows():
                nc_id = row.get('id', idx)
                description = row.get('description', f'N/C {nc_id}')[:50]
                date_str = row.get('occurred_at', 'Data não informada')
                nc_options[f"{date_str} - {description}..."] = nc_id
            
            selected_nc = st.selectbox(
                "Selecionar Não Conformidade",
                options=list(nc_options.keys()),
                key="evidence_nc_selector"
            )
            
            if selected_nc:
                nc_id = nc_options[selected_nc]
                
                # Busca evidências
                attachments = get_attachments("nonconformity", str(nc_id))
                
                if attachments:
                    st.write(f"**Evidências para a não conformidade selecionada:**")
                    
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
                    st.info("Nenhuma evidência encontrada para esta não conformidade.")
        else:
            st.info("Nenhuma não conformidade encontrada para exibir evidências.")
    
    with tab4:
        st.subheader("Registrar Nova Não Conformidade")
        
        with st.form("new_nonconformity_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                date_input = st.date_input("Data da N/C", value=date.today())
                norm_reference = st.selectbox(
                    "Norma de Referência",
                    options=["NR-12", "NR-18", "NR-35", "ISO 45001", "OHSAS 18001", "Outras"]
                )
                severity = st.selectbox(
                    "Gravidade",
                    options=["leve", "moderada", "grave", "critica"],
                    format_func=lambda x: {
                        "leve": "Baixa",
                        "moderada": "Média", 
                        "grave": "Alta",
                        "critica": "Crítica"
                    }[x]
                )
            
            with col2:
                # Busca sites disponíveis
                sites = get_sites()
                site_options = {f"{site['code']} - {site['name']}": site['id'] for site in sites}
                selected_site = st.selectbox("Site", options=list(site_options.keys()))
                site_id = site_options[selected_site] if selected_site else None
                
                status = st.selectbox(
                    "Status",
                    options=["aberta", "tratando", "encerrada"],
                    format_func=lambda x: {
                        "aberta": "Aberta",
                        "tratando": "Em Tratamento", 
                        "encerrada": "Encerrada"
                    }[x]
                )

            # Seleção opcional do acidentado (quando aplicável)
            employees = get_employees()
            emp_options = {"— (Sem funcionário) —": None}
            emp_options.update({f"{e.get('full_name','Sem Nome')} ({e.get('department','-')})": e['id'] for e in employees})
            selected_emp = st.selectbox("Funcionário (opcional)", options=list(emp_options.keys()))
            employee_id = emp_options[selected_emp]
            
            description = st.text_area("Descrição da Não Conformidade", height=100)
            corrective_actions = st.text_area("Ações Corretivas", height=100)
            
            # Data de resolução se encerrada
            if status == "encerrada":
                resolution_date = st.date_input("Data de Resolução", value=date.today())
            else:
                resolution_date = None
            
            # Upload de evidências
            uploaded_files = st.file_uploader(
                "Evidências (Fotos, PDFs, etc.)",
                accept_multiple_files=True,
                type=['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx']
            )
            
            submitted = st.form_submit_button("💾 Salvar Não Conformidade", type="primary")
            
            if submitted:
                if not site_id:
                    st.error("Selecione um site.")
                elif not description.strip():
                    st.error("Descrição é obrigatória.")
                else:
                    try:
                        supabase = get_supabase_client()
                        
                        # Insere não conformidade nos campos reais
                        nc_data = {
                            "site_id": site_id,
                            "opened_at": date_input.isoformat(),
                            "occurred_at": date_input.isoformat(),
                            "standard_ref": norm_reference,
                            "severity": severity,
                            "status": status,
                            "description": description,
                            "corrective_actions": corrective_actions
                        }
                        if employee_id:
                            nc_data["employee_id"] = employee_id
                        
                        if resolution_date:
                            nc_data["resolution_date"] = resolution_date.isoformat()
                        
                        result = supabase.table("nonconformities").insert(nc_data).execute()
                        
                        if result.data:
                            nc_id = result.data[0]['id']
                            st.success("✅ Não conformidade registrada com sucesso!")
                            
                            # Upload de evidências
                            if uploaded_files:
                                for uploaded_file in uploaded_files:
                                    file_bytes = uploaded_file.read()
                                    upload_evidence(
                                        file_bytes,
                                        uploaded_file.name,
                                        "nonconformity",
                                        str(nc_id),
                                        f"Evidência da N/C de {date_input}"
                                    )
                                st.success(f"✅ {len(uploaded_files)} evidência(s) enviada(s)!")
                            
                            st.rerun()
                        else:
                            st.error("Erro ao salvar não conformidade.")
                            
                    except Exception as e:
                        st.error(f"Erro: {str(e)}")

def get_sites():
    """Busca sites disponíveis"""
    try:
        supabase = get_supabase_client()
        response = supabase.table("sites").select("id, code, name").execute()
        return response.data
    except:
        return []

def get_employees():
    """Busca funcionários (employees)"""
    try:
        supabase = get_supabase_client()
        response = supabase.table("employees").select("id, full_name, department").order("full_name").execute()
        return response.data
    except:
        return []

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

if __name__ == "__main__":
    app({})
