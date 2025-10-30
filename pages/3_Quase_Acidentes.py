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
    """Busca dados de quase-acidentes"""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        query = supabase.table("near_misses").select("*")
        
        if start_date:
            query = query.gte("occurred_at", start_date.isoformat())
        if end_date:
            query = query.lte("occurred_at", end_date.isoformat())
            
        data = query.order("occurred_at", desc=True).execute().data
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Erro ao buscar quase-acidentes: {str(e)}")
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
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Análise", "📋 Registros", "📎 Evidências", "➕ Novo Quase-Acidente"])
    
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
                    "- Sem resultados? Amplie o período ou limpe filtros."
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
                "- Sem resultados? Amplie o período ou limpe filtros."
            )
        
        # Busca dados
        with st.spinner("Carregando dados de quase-acidentes..."):
            df = fetch_near_misses(
                start_date=filters.get("start_date"),
                end_date=filters.get("end_date")
            )
        
        if df.empty:
            st.warning("Nenhum quase-acidente encontrado com os filtros aplicados.")
        else:
            # Aplica filtros adicionais
            df = apply_filters_to_df(df, filters)
            
            # Normaliza severidade potencial para 3 níveis: low/medium/high
            if 'potential_severity' in df.columns:
                sev_map = {
                    'leve': 'low',
                    'low': 'low',
                    'moderada': 'medium',
                    'medium': 'medium',
                    'grave': 'high',
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
                    options=["low", "medium", "high"],
                    format_func=lambda x: {
                        "low": "Baixo",
                        "medium": "Médio", 
                        "high": "Alto"
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
            
            # Seleção opcional de funcionário (acidentado potencial)
            employees = get_employees()
            emp_options = {"— (Sem funcionário) —": None}
            emp_options.update({f"{e.get('full_name','Sem Nome')} ({e.get('department','-')})": e['id'] for e in employees})
            selected_emp = st.selectbox("Funcionário (opcional)", options=list(emp_options.keys()))
            employee_id = emp_options[selected_emp]
            
            description = st.text_area("Descrição do Quase-Acidente", height=100)
            preventive_actions = st.text_area("Ações Preventivas", height=100)
            
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
                        from managers.supabase_config import get_service_role_client
                        supabase = get_service_role_client()
                        
                        # Insere quase-acidente
                        near_miss_data = {
                            "occurred_at": date_input.isoformat(),
                            "potential_severity": potential_severity,
                            "description": description,
                            "status": status
                        }
                        if employee_id:
                            near_miss_data["employee_id"] = employee_id
                        
                        result = supabase.table("near_misses").insert(near_miss_data).execute()
                        
                        if result.data:
                            near_miss_id = result.data[0]['id']
                            st.success("✅ Quase-acidente registrado com sucesso!")
                            
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
    """Busca funcionários (employees)"""
    try:
        supabase = get_supabase_client()
        response = supabase.table("employees").select("id, full_name, department").order("full_name").execute()
        return response.data
    except:
        return []

if __name__ == "__main__":
    app({})
