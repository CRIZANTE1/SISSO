import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from services.kpi import fetch_kpi_data
from services.uploads import upload_evidence, get_attachments
from components.cards import create_metric_row, create_bar_chart, create_pie_chart
from components.filters import apply_filters_to_df
from managers.supabase_config import get_supabase_client

def fetch_accidents(site_codes=None, start_date=None, end_date=None):
    """Busca dados de acidentes"""
    try:
        supabase = get_supabase_client()
        query = supabase.table("accidents").select("*")
        
        if site_codes:
            # Busca site_ids baseado nos códigos
            sites_response = supabase.table("sites").select("id, code").in_("code", site_codes).execute()
            site_ids = [site['id'] for site in sites_response.data]
            query = query.in_("site_id", site_ids)
        
        if start_date:
            query = query.gte("date", start_date.isoformat())
        if end_date:
            query = query.lte("date", end_date.isoformat())
            
        data = query.order("date", desc=True).execute().data
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Erro ao buscar acidentes: {str(e)}")
        return pd.DataFrame()

def app(filters):
    st.title("🚨 Acidentes")
    
    # Tabs para diferentes visualizações
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Análise", "📋 Registros", "📎 Evidências", "➕ Novo Acidente"])
    
    with tab1:
        st.subheader("Análise de Acidentes")
        
        # Busca dados
        with st.spinner("Carregando dados de acidentes..."):
            df = fetch_accidents(
                site_codes=filters.get("sites"),
                start_date=filters.get("start_date"),
                end_date=filters.get("end_date")
            )
        
        if df.empty:
            st.warning("Nenhum acidente encontrado com os filtros aplicados.")
        else:
            # Aplica filtros adicionais
            df = apply_filters_to_df(df, filters)
            
            # Métricas principais
            total_accidents = len(df)
            fatal_accidents = len(df[df['severity'] == 'fatal'])
            with_injury = len(df[df['severity'] == 'with_injury'])
            without_injury = len(df[df['severity'] == 'without_injury'])
            total_lost_days = df['lost_days'].sum() if 'lost_days' in df.columns else 0
            
            metrics = [
                {
                    "title": "Total de Acidentes",
                    "value": total_accidents,
                    "icon": "🚨",
                    "color": "danger" if total_accidents > 0 else "success"
                },
                {
                    "title": "Acidentes Fatais",
                    "value": fatal_accidents,
                    "icon": "💀",
                    "color": "danger" if fatal_accidents > 0 else "success"
                },
                {
                    "title": "Com Lesão",
                    "value": with_injury,
                    "icon": "🏥",
                    "color": "warning"
                },
                {
                    "title": "Dias Perdidos",
                    "value": total_lost_days,
                    "icon": "📅",
                    "color": "info"
                }
            ]
            
            create_metric_row(metrics)
            
            # Gráficos
            col1, col2 = st.columns(2)
            
            with col1:
                # Distribuição por severidade
                if 'severity' in df.columns:
                    severity_counts = df['severity'].value_counts()
                    fig1 = create_pie_chart(
                        pd.DataFrame({
                            'severity': severity_counts.index,
                            'count': severity_counts.values
                        }),
                        'severity',
                        'count',
                        'Distribuição por Severidade'
                    )
                    st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                # Acidentes por mês
                if 'date' in df.columns:
                    df['month'] = pd.to_datetime(df['date']).dt.to_period('M')
                    monthly_counts = df.groupby('month').size().reset_index(name='count')
                    monthly_counts['month'] = monthly_counts['month'].astype(str)
                    
                    fig2 = create_bar_chart(
                        monthly_counts,
                        'month',
                        'count',
                        'Acidentes por Mês'
                    )
                    st.plotly_chart(fig2, use_container_width=True)
            
            # Análise por causa raiz
            if 'root_cause' in df.columns:
                st.subheader("Análise por Causa Raiz")
                root_cause_counts = df['root_cause'].value_counts()
                
                fig3 = create_bar_chart(
                    pd.DataFrame({
                        'root_cause': root_cause_counts.index,
                        'count': root_cause_counts.values
                    }),
                    'root_cause',
                    'count',
                    'Acidentes por Causa Raiz'
                )
                st.plotly_chart(fig3, use_container_width=True)
    
    with tab2:
        st.subheader("Registros de Acidentes")
        
        if not df.empty:
            # Filtros adicionais para a tabela
            col1, col2, col3 = st.columns(3)
            
            with col1:
                severity_filter = st.selectbox(
                    "Filtrar por Severidade",
                    options=["Todas"] + list(df['severity'].unique()) if 'severity' in df.columns else ["Todas"],
                    key="accident_severity_filter"
                )
            
            with col2:
                site_filter = st.selectbox(
                    "Filtrar por Site",
                    options=["Todos"] + list(df['site_id'].unique()) if 'site_id' in df.columns else ["Todos"],
                    key="accident_site_filter"
                )
            
            with col3:
                search_term = st.text_input("Buscar na descrição", key="accident_search")
            
            # Aplica filtros
            filtered_df = df.copy()
            
            if severity_filter != "Todas" and 'severity' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['severity'] == severity_filter]
            
            if site_filter != "Todos" and 'site_id' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['site_id'] == site_filter]
            
            if search_term and 'description' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['description'].str.contains(search_term, case=False, na=False)]
            
            # Exibe tabela
            display_cols = ['date', 'severity', 'description', 'lost_days', 'root_cause']
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
            st.info("Nenhum acidente encontrado.")
    
    with tab3:
        st.subheader("Evidências dos Acidentes")
        
        if not df.empty:
            # Seleciona acidente para ver evidências
            accident_options = {}
            for idx, row in df.iterrows():
                accident_id = row.get('id', idx)
                description = row.get('description', f'Acidente {accident_id}')[:50]
                date_str = row.get('date', 'Data não informada')
                accident_options[f"{date_str} - {description}..."] = accident_id
            
            selected_accident = st.selectbox(
                "Selecionar Acidente",
                options=list(accident_options.keys()),
                key="evidence_accident_selector"
            )
            
            if selected_accident:
                accident_id = accident_options[selected_accident]
                
                # Busca evidências
                attachments = get_attachments("accident", str(accident_id))
                
                if attachments:
                    st.write(f"**Evidências para o acidente selecionado:**")
                    
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
                    st.info("Nenhuma evidência encontrada para este acidente.")
        else:
            st.info("Nenhum acidente encontrado para exibir evidências.")
    
    with tab4:
        st.subheader("Registrar Novo Acidente")
        
        with st.form("new_accident_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                date_input = st.date_input("Data do Acidente", value=date.today())
                severity = st.selectbox(
                    "Severidade",
                    options=["fatal", "with_injury", "without_injury"],
                    format_func=lambda x: {
                        "fatal": "Fatal",
                        "with_injury": "Com Lesão", 
                        "without_injury": "Sem Lesão"
                    }[x]
                )
                lost_days = st.number_input("Dias Perdidos", min_value=0, value=0)
            
            with col2:
                # Busca sites disponíveis
                sites = get_sites()
                site_options = {f"{site['code']} - {site['name']}": site['id'] for site in sites}
                selected_site = st.selectbox("Site", options=list(site_options.keys()))
                site_id = site_options[selected_site] if selected_site else None
                
                root_cause = st.selectbox(
                    "Causa Raiz",
                    options=["Fator Humano", "Fator Material", "Fator Ambiental", 
                            "Fator Organizacional", "Fator Técnico", "Outros"]
                )
            
            description = st.text_area("Descrição do Acidente", height=100)
            corrective_actions = st.text_area("Ações Corretivas", height=100)
            
            # Upload de evidências
            uploaded_files = st.file_uploader(
                "Evidências (Fotos, PDFs, etc.)",
                accept_multiple_files=True,
                type=['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx']
            )
            
            submitted = st.form_submit_button("💾 Salvar Acidente", type="primary")
            
            if submitted:
                if not site_id:
                    st.error("Selecione um site.")
                elif not description.strip():
                    st.error("Descrição é obrigatória.")
                else:
                    try:
                        supabase = get_supabase_client()
                        
                        # Insere acidente
                        accident_data = {
                            "site_id": site_id,
                            "date": date_input.isoformat(),
                            "severity": severity,
                            "description": description,
                            "lost_days": lost_days,
                            "root_cause": root_cause,
                            "corrective_actions": corrective_actions
                        }
                        
                        result = supabase.table("accidents").insert(accident_data).execute()
                        
                        if result.data:
                            accident_id = result.data[0]['id']
                            st.success("✅ Acidente registrado com sucesso!")
                            
                            # Upload de evidências
                            if uploaded_files:
                                for uploaded_file in uploaded_files:
                                    file_bytes = uploaded_file.read()
                                    upload_evidence(
                                        file_bytes,
                                        uploaded_file.name,
                                        "accident",
                                        str(accident_id),
                                        f"Evidência do acidente de {date_input}"
                                    )
                                st.success(f"✅ {len(uploaded_files)} evidência(s) enviada(s)!")
                            
                            st.rerun()
                        else:
                            st.error("Erro ao salvar acidente.")
                            
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
