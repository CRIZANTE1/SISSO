import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from services.uploads import upload_evidence, get_attachments
from components.cards import create_metric_row, create_bar_chart, create_pie_chart
from components.filters import apply_filters_to_df
from managers.supabase_config import get_supabase_client

def fetch_near_misses(site_codes=None, start_date=None, end_date=None):
    """Busca dados de quase-acidentes"""
    try:
        supabase = get_supabase_client()
        query = supabase.table("near_misses").select("*")
        
        if site_codes:
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
        st.error(f"Erro ao buscar quase-acidentes: {str(e)}")
        return pd.DataFrame()

def app(filters):
    st.title("⚠️ Quase-Acidentes")
    
    # Tabs para diferentes visualizações
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Análise", "📋 Registros", "📎 Evidências", "➕ Novo Quase-Acidente"])
    
    with tab1:
        st.subheader("Análise de Quase-Acidentes")
        
        # Busca dados
        with st.spinner("Carregando dados de quase-acidentes..."):
            df = fetch_near_misses(
                site_codes=filters.get("sites"),
                start_date=filters.get("start_date"),
                end_date=filters.get("end_date")
            )
        
        if df.empty:
            st.warning("Nenhum quase-acidente encontrado com os filtros aplicados.")
        else:
            # Aplica filtros adicionais
            df = apply_filters_to_df(df, filters)
            
            # Métricas principais
            total_near_misses = len(df)
            high_risk = len(df[df['risk_level'] == 'high']) if 'risk_level' in df.columns else 0
            medium_risk = len(df[df['risk_level'] == 'medium']) if 'risk_level' in df.columns else 0
            low_risk = len(df[df['risk_level'] == 'low']) if 'risk_level' in df.columns else 0
            
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
                # Distribuição por nível de risco
                if 'risk_level' in df.columns:
                    risk_counts = df['risk_level'].value_counts()
                    fig1 = create_pie_chart(
                        pd.DataFrame({
                            'risk_level': risk_counts.index,
                            'count': risk_counts.values
                        }),
                        'risk_level',
                        'count',
                        'Distribuição por Nível de Risco'
                    )
                    st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                # Quase-acidentes por mês
                if 'date' in df.columns:
                    df['month'] = pd.to_datetime(df['date']).dt.to_period('M')
                    monthly_counts = df.groupby('month').size().reset_index(name='count')
                    monthly_counts['month'] = monthly_counts['month'].astype(str)
                    
                    fig2 = create_bar_chart(
                        monthly_counts,
                        'month',
                        'count',
                        'Quase-Acidentes por Mês'
                    )
                    st.plotly_chart(fig2, use_container_width=True)
            
            # Análise por categoria
            if 'category' in df.columns:
                st.subheader("Análise por Categoria")
                category_counts = df['category'].value_counts()
                
                fig3 = create_bar_chart(
                    pd.DataFrame({
                        'category': category_counts.index,
                        'count': category_counts.values
                    }),
                    'category',
                    'count',
                    'Quase-Acidentes por Categoria'
                )
                st.plotly_chart(fig3, use_container_width=True)
            
            # Análise por causa raiz
            if 'root_cause' in df.columns:
                st.subheader("Análise por Causa Raiz")
                root_cause_counts = df['root_cause'].value_counts()
                
                fig4 = create_bar_chart(
                    pd.DataFrame({
                        'root_cause': root_cause_counts.index,
                        'count': root_cause_counts.values
                    }),
                    'root_cause',
                    'count',
                    'Quase-Acidentes por Causa Raiz'
                )
                st.plotly_chart(fig4, use_container_width=True)
    
    with tab2:
        st.subheader("Registros de Quase-Acidentes")
        
        if not df.empty:
            # Filtros adicionais para a tabela
            col1, col2, col3 = st.columns(3)
            
            with col1:
                risk_filter = st.selectbox(
                    "Filtrar por Nível de Risco",
                    options=["Todos"] + list(df['risk_level'].unique()) if 'risk_level' in df.columns else ["Todos"],
                    key="near_miss_risk_filter"
                )
            
            with col2:
                category_filter = st.selectbox(
                    "Filtrar por Categoria",
                    options=["Todas"] + list(df['category'].unique()) if 'category' in df.columns else ["Todas"],
                    key="near_miss_category_filter"
                )
            
            with col3:
                search_term = st.text_input("Buscar na descrição", key="near_miss_search")
            
            # Aplica filtros
            filtered_df = df.copy()
            
            if risk_filter != "Todos" and 'risk_level' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['risk_level'] == risk_filter]
            
            if category_filter != "Todas" and 'category' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['category'] == category_filter]
            
            if search_term and 'description' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['description'].str.contains(search_term, case=False, na=False)]
            
            # Exibe tabela
            display_cols = ['date', 'risk_level', 'category', 'description', 'root_cause', 'preventive_actions']
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
            st.info("Nenhum quase-acidente encontrado.")
    
    with tab3:
        st.subheader("Evidências dos Quase-Acidentes")
        
        if not df.empty:
            # Seleciona quase-acidente para ver evidências
            near_miss_options = {}
            for idx, row in df.iterrows():
                near_miss_id = row.get('id', idx)
                description = row.get('description', f'Quase-acidente {near_miss_id}')[:50]
                date_str = row.get('date', 'Data não informada')
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
                risk_level = st.selectbox(
                    "Nível de Risco",
                    options=["low", "medium", "high"],
                    format_func=lambda x: {
                        "low": "Baixo",
                        "medium": "Médio", 
                        "high": "Alto"
                    }[x]
                )
                category = st.selectbox(
                    "Categoria",
                    options=["Queda", "Choque", "Corte", "Queimadura", "Outros"]
                )
            
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
                if not site_id:
                    st.error("Selecione um site.")
                elif not description.strip():
                    st.error("Descrição é obrigatória.")
                else:
                    try:
                        supabase = get_supabase_client()
                        
                        # Insere quase-acidente
                        near_miss_data = {
                            "site_id": site_id,
                            "date": date_input.isoformat(),
                            "risk_level": risk_level,
                            "category": category,
                            "description": description,
                            "root_cause": root_cause,
                            "preventive_actions": preventive_actions
                        }
                        
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
