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
# Imports da NBR 14280 removidos

def calculate_work_days_until_accident(accident_date, employee_identifier=None):
    """
    Calcula quantos dias o funcionário trabalhou até o acidente acontecer.
    Aceita identificador de usuário (e-mail ou UUID). Tenta obter data de admissão
    e somatório de horas trabalhadas até o mês do acidente. Converte horas em dias (8h/dia).
    """
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()

        admission_date = None
        user_email = None
        user_id = None

        # Resolve identificador do funcionário: pode ser e-mail (contém '@') ou UUID
        if employee_identifier:
            if isinstance(employee_identifier, str) and '@' in employee_identifier:
                user_email = employee_identifier
            else:
                user_id = employee_identifier

        # Busca perfil para obter email e uma possível data de admissão
        profile_response = None
        if user_email:
            profile_response = supabase.table("profiles").select("id, email, created_at, admission_date").eq("email", user_email).limit(1).execute()
        elif user_id:
            profile_response = supabase.table("profiles").select("id, email, created_at, admission_date").eq("id", user_id).limit(1).execute()

        if profile_response and hasattr(profile_response, 'data') and profile_response.data:
            profile = profile_response.data[0]
            user_id = profile.get('id', user_id)
            user_email = profile.get('email', user_email)

            # Preferir campo admission_date se existir; senão usar created_at
            if profile.get('admission_date'):
                admission_date = pd.to_datetime(profile['admission_date']).date()
            elif profile.get('created_at'):
                admission_date = pd.to_datetime(profile['created_at']).date()

        # Calcula dias corridos entre admissão e acidente (se conhecido)
        days_since_admission = None
        if admission_date is not None:
            days_since_admission = (accident_date - admission_date).days
            if days_since_admission < 0:
                days_since_admission = 0

        # Busca horas trabalhadas mensais para calcular dias úteis
        total_hours = 0.0
        hours_response = None
        # Tenta por e-mail
        if user_email:
            hours_response = supabase.table("hours_worked_monthly").select("year, month, hours, created_by, user_id").eq("created_by", user_email).execute()
        # Se não achou por e-mail, tenta por user_id em created_by
        if (not hours_response or not getattr(hours_response, 'data', None)) and user_id:
            hours_response = supabase.table("hours_worked_monthly").select("year, month, hours, created_by, user_id").eq("created_by", user_id).execute()
        # Se a tabela tiver coluna user_id, tenta também por ela
        if (not hours_response or not getattr(hours_response, 'data', None)) and user_id:
            try:
                hours_response = supabase.table("hours_worked_monthly").select("year, month, hours, user_id").eq("user_id", user_id).execute()
            except Exception:
                pass

        if hours_response and hasattr(hours_response, 'data') and hours_response.data:
            # Soma horas até o mês do acidente (inclusive)
            for row in hours_response.data:
                if 'year' in row and 'month' in row:
                    try:
                        month_date = pd.to_datetime(f"{row['year']}-{int(row['month']):02d}-01").date()
                        if month_date <= accident_date:
                            total_hours += float(row.get('hours', 0) or 0)
                    except Exception:
                        continue

        # Converte horas para dias úteis (8h/dia). Aplicar escala *100 conforme convenção dos dados.
        if total_hours > 0:
            work_days = (total_hours * 100.0) / 8.0
            return min(work_days, days_since_admission) if days_since_admission is not None else work_days

        # Fallback: se não há horas, mas conhecemos admissão, use dias corridos
        if days_since_admission is not None:
            return days_since_admission

        # Fallback adicional: se não há perfil e existe histórico de acidentes do mesmo criador,
        # usar dias desde o primeiro registro desse criador como aproximação.
        if employee_identifier:
            try:
                # Determina filtro mais provável
                identifier_field = "created_by"
                identifier_value = employee_identifier
                # Busca acidentes mais antigos do mesmo criador
                first_acc = supabase.table("accidents").select("occurred_at").eq(identifier_field, identifier_value).order("occurred_at").limit(1).execute()
                if first_acc and hasattr(first_acc, 'data') and first_acc.data:
                    first_date = pd.to_datetime(first_acc.data[0]['occurred_at']).date()
                    approx_days = (accident_date - first_date).days
                    return max(0, approx_days)
            except Exception:
                pass

        # Último fallback: sem perfil e sem horas, retorne 0
        return 0

    except Exception as e:
        st.error(f"Erro ao calcular dias trabalhados: {str(e)}")
        return 0

def get_work_days_analysis(df):
    """
    Analisa os dias trabalhados até acidentes e retorna estatísticas.
    """
    if df.empty or 'occurred_at' not in df.columns:
        return {}, df
    
    try:
        # Cria uma cópia para não modificar o DataFrame original
        df_work = df.copy()
        
        # Converte data para datetime
        df_work['occurred_at'] = pd.to_datetime(df_work['occurred_at'])
        df_work['accident_date'] = df_work['occurred_at'].dt.date
        
        # Calcula dias trabalhados para cada acidente
        work_days_list = []
        for idx, row in df_work.iterrows():
            work_days = calculate_work_days_until_accident(
                row['accident_date'], 
                row.get('created_by')
            )
            # Garante que não há valores negativos
            work_days = max(0, work_days)
            work_days_list.append(work_days)
        
        df_work['work_days_until_accident'] = work_days_list
        
        # Filtra apenas valores válidos (maiores que 0)
        valid_work_days = df_work[df_work['work_days_until_accident'] > 0]['work_days_until_accident']
        
        # Estatísticas
        analysis = {
            'total_accidents': len(df_work),
            'avg_work_days': valid_work_days.mean() if len(valid_work_days) > 0 else 0,
            'median_work_days': valid_work_days.median() if len(valid_work_days) > 0 else 0,
            'min_work_days': valid_work_days.min() if len(valid_work_days) > 0 else 0,
            'max_work_days': valid_work_days.max() if len(valid_work_days) > 0 else 0,
            'accidents_first_week': len(df_work[df_work['work_days_until_accident'] <= 7]),
            'accidents_first_month': len(df_work[df_work['work_days_until_accident'] <= 30]),
            'accidents_first_year': len(df_work[df_work['work_days_until_accident'] <= 365])
        }
        
        return analysis, df_work
        
    except Exception as e:
        st.error(f"Erro na análise de dias trabalhados: {str(e)}")
        return {}, df

def fetch_accidents(start_date=None, end_date=None):
    """Busca dados de acidentes"""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        query = supabase.table("accidents").select("*")
        
        if start_date:
            query = query.gte("occurred_at", start_date.isoformat())
        if end_date:
            query = query.lte("occurred_at", end_date.isoformat())
            
        response = query.order("occurred_at", desc=True).execute()
        if response and hasattr(response, 'data') and response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao buscar acidentes: {str(e)}")
        return pd.DataFrame()

def app(filters=None):
    st.title("🚨 Acidentes")
    
    # Busca filtros do session state se não foram passados como parâmetro
    if filters is None:
        filters = st.session_state.get('filters', {})
    
    # Tabs para diferentes visualizações
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Análise", "📋 Registros", "📎 Evidências", "➕ Novo Acidente", "📚 Instruções"])
    
    # Busca dados uma única vez no início
    with st.spinner("Carregando dados de acidentes..."):
        df = fetch_accidents(
            start_date=filters.get("start_date"),
            end_date=filters.get("end_date")
        )
    
    if df.empty:
        st.warning("Nenhum acidente encontrado com os filtros aplicados.")
        work_days_analysis = {}
        df_with_work_days = df
    else:
        # Aplica filtros adicionais
        df = apply_filters_to_df(df, filters)
        
        # Análise de dias trabalhados até acidente
        work_days_analysis, df_with_work_days = get_work_days_analysis(df)
    
    with tab1:
        st.subheader("Análise de Acidentes")
        
        if not df.empty:
            
            # Métricas principais
            total_accidents = len(df)
            fatal_accidents = len(df[df['type'] == 'fatal'])
            with_injury = len(df[df['type'] == 'lesao'])
            without_injury = len(df[df['type'] == 'sem_lesao'])
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
            
            # Análise de Dias Trabalhados até Acidente
            if work_days_analysis and work_days_analysis.get('total_accidents', 0) > 0:
                st.subheader("📅 Análise de Dias Trabalhados até Acidente")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    avg_days = work_days_analysis.get('avg_work_days', 0)
                    if avg_days > 0:
                        st.metric(
                            "Média de Dias",
                            f"{avg_days:.0f}",
                            help="Média de dias trabalhados até o acidente"
                        )
                    else:
                        st.metric(
                            "Média de Dias",
                            "N/A",
                            help="Dados insuficientes para calcular média"
                        )
                
                with col2:
                    st.metric(
                        "Primeira Semana",
                        f"{work_days_analysis.get('accidents_first_week', 0)}",
                        help="Acidentes nos primeiros 7 dias de trabalho"
                    )
                
                with col3:
                    st.metric(
                        "Primeiro Mês",
                        f"{work_days_analysis.get('accidents_first_month', 0)}",
                        help="Acidentes nos primeiros 30 dias de trabalho"
                    )
                
                with col4:
                    st.metric(
                        "Primeiro Ano",
                        f"{work_days_analysis.get('accidents_first_year', 0)}",
                        help="Acidentes nos primeiros 365 dias de trabalho"
                    )
                
                # Informação adicional sobre dados
                if work_days_analysis.get('avg_work_days', 0) == 0:
                    st.info("ℹ️ **Nota**: Para análise precisa de dias trabalhados, é necessário ter dados de funcionários e horas trabalhadas cadastrados no sistema.")
                
                # Gráfico de distribuição de dias trabalhados
                if 'work_days_until_accident' in df_with_work_days.columns:
                    st.subheader("📊 Distribuição de Dias Trabalhados até Acidente")
                    
                    # Filtra apenas valores válidos para o gráfico
                    valid_data = df_with_work_days[df_with_work_days['work_days_until_accident'] > 0].copy()
                    
                    if len(valid_data) > 0:
                        # Cria faixas de dias
                        valid_data['work_days_range'] = pd.cut(
                            valid_data['work_days_until_accident'],
                            bins=[0, 7, 30, 90, 365, float('inf')],
                            labels=['0-7 dias', '8-30 dias', '31-90 dias', '91-365 dias', 'Mais de 1 ano'],
                            include_lowest=True
                        )
                        
                        range_counts = valid_data['work_days_range'].value_counts()
                        
                        fig_work_days = px.bar(
                            x=range_counts.index,
                            y=range_counts.values,
                            title="Acidentes por Faixa de Dias Trabalhados",
                            color=range_counts.values,
                            color_continuous_scale="Oranges"
                        )
                        fig_work_days.update_layout(
                            xaxis_title="Faixa de Dias Trabalhados",
                            yaxis_title="Número de Acidentes",
                            showlegend=False,
                            height=400
                        )
                        st.plotly_chart(fig_work_days, use_container_width=True)
                    else:
                        st.info("📊 **Distribuição de Dias Trabalhados**\n\nNão há dados suficientes para gerar o gráfico de distribuição.")
            
            # Gráficos
            col1, col2 = st.columns(2)
            
            with col1:
                # Distribuição por tipo - Simplificada
                if 'type' in df.columns:
                    type_counts = df['type'].value_counts()
                    type_names = {'fatal': 'Fatal', 'lesao': 'Com Lesão', 'sem_lesao': 'Sem Lesão'}
                    
                    fig1 = px.pie(
                        values=type_counts.values,
                        names=[type_names.get(t, t) for t in type_counts.index],
                        title="Distribuição por Tipo de Acidente",
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig1.update_layout(
                        height=400,
                        font=dict(size=12)
                    )
                    st.plotly_chart(fig1, use_container_width=True)
                else:
                    st.info("📊 **Distribuição por Tipo**\n\nNenhum dado de tipo disponível.")
            
            with col2:
                # Acidentes por mês - Simplificada
                if 'occurred_at' in df.columns:
                    df_temp = df.copy()
                    df_temp['month'] = pd.to_datetime(df_temp['occurred_at']).dt.to_period('M')
                    monthly_counts = df_temp.groupby('month').size().reset_index(name='count')
                    monthly_counts['month'] = monthly_counts['month'].astype(str)
                    
                    fig2 = px.bar(
                        monthly_counts,
                        x='month',
                        y='count',
                        title="Acidentes por Mês",
                        color='count',
                        color_continuous_scale="Reds"
                    )
                    fig2.update_layout(
                        height=400,
                        xaxis_title="Mês",
                        yaxis_title="Número de Acidentes",
                        showlegend=False,
                        font=dict(size=12)
                    )
                    fig2.update_traces(marker_line_width=0)
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("📅 **Acidentes por Mês**\n\nNenhum dado de data disponível.")
            
            # Análise por causa raiz - Simplificada
            if 'root_cause' in df.columns and not df['root_cause'].isna().all():
                st.subheader("📋 Análise por Causa Raiz")
                root_cause_counts = df['root_cause'].value_counts()
                
                fig3 = px.bar(
                    x=root_cause_counts.values,
                    y=root_cause_counts.index,
                    orientation='h',
                    title="Acidentes por Causa Raiz",
                    color=root_cause_counts.values,
                    color_continuous_scale="Blues"
                )
                fig3.update_layout(
                    height=400,
                    xaxis_title="Número de Acidentes",
                    yaxis_title="Causa Raiz",
                    showlegend=False,
                    font=dict(size=12)
                )
                fig3.update_traces(marker_line_width=0)
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("📋 **Análise por Causa Raiz**\n\nNenhum dado de causa raiz disponível.")
    
            # Análise por Classificação (NBR 14280)
            if 'classification' in df.columns and not df['classification'].isna().all():
                st.subheader("📚 Análise por Classificação (NBR 14280)")
                class_counts = df['classification'].value_counts()

                fig_class = px.pie(
                    values=class_counts.values,
                    names=class_counts.index,
                    title="Distribuição por Classificação",
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                fig_class.update_layout(height=380, font=dict(size=12))
                st.plotly_chart(fig_class, use_container_width=True)
            else:
                st.info("📚 **Classificação (NBR 14280)**\n\nNenhum dado de classificação disponível.")

            # Análise por Parte do Corpo Afetada (NBR 14280)
            if 'body_part' in df.columns and not df['body_part'].isna().all():
                st.subheader("🧍 Análise por Parte do Corpo Afetada (NBR 14280)")
                body_counts = df['body_part'].value_counts().sort_values(ascending=True)

                fig_body = px.bar(
                    x=body_counts.values,
                    y=body_counts.index,
                    orientation='h',
                    title="Acidentes por Parte do Corpo",
                    color=body_counts.values,
                    color_continuous_scale="Tealgrn"
                )
                fig_body.update_layout(
                    height=420,
                    xaxis_title="Número de Acidentes",
                    yaxis_title="Parte do Corpo",
                    showlegend=False,
                    font=dict(size=12)
                )
                fig_body.update_traces(marker_line_width=0)
                st.plotly_chart(fig_body, use_container_width=True)
            else:
                st.info("🧍 **Parte do Corpo Afetada (NBR 14280)**\n\nNenhum dado disponível.")

    with tab2:
        st.subheader("Registros de Acidentes")
        
        if not df.empty:
            # Filtros adicionais para a tabela
            col1, col2, col3 = st.columns(3)
            
            with col1:
                type_filter = st.selectbox(
                    "Filtrar por Tipo",
                    options=["Todos"] + list(df['type'].unique()) if 'type' in df.columns else ["Todos"],
                    key="accident_type_filter"
                )
            
            with col2:
                status_filter = st.selectbox(
                    "Filtrar por Status",
                    options=["Todos"] + list(df['status'].unique()) if 'status' in df.columns else ["Todos"],
                    key="accident_status_filter"
                )
            
            with col3:
                search_term = st.text_input("Buscar na descrição", key="accident_search")
            
            # Aplica filtros
            filtered_df = df.copy()
            
            if type_filter != "Todos" and 'type' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['type'] == type_filter]
            
            if status_filter != "Todos" and 'status' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['status'] == status_filter]
            
            if search_term and 'description' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['description'].astype(str).str.contains(search_term, case=False, na=False)]
            
            # Exibe tabela de acidentes
            display_cols = ['occurred_at', 'type', 'description', 'lost_days', 'root_cause', 'status']
            available_cols = [col for col in display_cols if col in filtered_df.columns]
            
            # Adiciona coluna de dias trabalhados se disponível
            if 'work_days_until_accident' in filtered_df.columns:
                available_cols.append('work_days_until_accident')
            
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
                date_str = row.get('occurred_at', 'Data não informada')
                accident_options[f"{date_str} - {description}..."] = accident_id
            
            selected_accident = st.selectbox(
                "Selecionar Acidente",
                options=list(accident_options.keys()),
                key="evidence_accident_selector"
            )
            
            if selected_accident:
                accident_id = accident_options[selected_accident]
                
                # Busca evidências
                try:
                    attachments = get_attachments("accident", str(accident_id))
                except:
                    attachments = []
                
                if attachments:
                    st.write(f"**Evidências para o acidente selecionado:**")
                    
                    for attachment in attachments:
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.write(f"📎 {attachment['filename']}")
                            if attachment.get('description'):
                                st.caption(attachment['description'])
                        
                        with col2:
                            if st.button("📥 Download", key=f"download_{attachment.get('id', 'unknown')}"):
                                try:
                                    file_data = download_attachment(attachment.get('bucket', ''), attachment.get('path', ''))
                                    if file_data:
                                        st.download_button(
                                            "💾 Baixar Arquivo",
                                            file_data,
                                            attachment.get('filename', 'arquivo'),
                                            key=f"download_btn_{attachment.get('id', 'unknown')}"
                                        )
                                except:
                                    st.error("Erro ao baixar arquivo")
                        
                        with col3:
                            if st.button("🗑️ Remover", key=f"remove_{attachment.get('id', 'unknown')}"):
                                try:
                                    if delete_attachment(attachment.get('id', '')):
                                        st.success("Evidência removida!")
                                        st.rerun()
                                except:
                                    st.error("Erro ao remover evidência")
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
                accident_type = st.selectbox(
                    "Tipo",
                    options=["fatal", "lesao", "sem_lesao"],
                    format_func=lambda x: {
                        "fatal": "Fatal",
                        "lesao": "Com Lesão", 
                        "sem_lesao": "Sem Lesão"
                    }[x]
                )
                lost_days = st.number_input("Dias Perdidos", min_value=0, value=0)
                is_fatal = st.checkbox("Acidente Fatal", value=False, help="Marque se o acidente resultou em morte")
            
            with col2:
                classification_options = [
                    "Típico",
                    "Trajeto",
                    "Doença do Trabalho",
                    "Outro"
                ]
                classification_sel = st.selectbox("Classificação", options=classification_options)
                classification = (
                    st.text_input("Classificação (Outro)") if classification_sel == "Outro" else classification_sel
                )

                body_part_options = [
                    "Cabeça",
                    "Olhos",
                    "Face",
                    "Pescoço",
                    "Membros Superiores",
                    "Mãos",
                    "Membros Inferiores",
                    "Pés",
                    "Tronco",
                    "Abdome",
                    "Coluna Vertebral",
                    "Múltiplas Partes",
                    "Outras"
                ]
                body_part_sel = st.selectbox("Parte do Corpo Afetada", options=body_part_options)
                body_part = (
                    st.text_input("Parte do Corpo (Outra)") if body_part_sel == "Outras" else body_part_sel
                )
                root_cause = st.selectbox(
                    "Causa Raiz",
                    options=["Fator Humano", "Fator Material", "Fator Ambiental", 
                            "Fator Organizacional", "Fator Técnico", "Outros"]
                )
                
                # Campos adicionais
                cat_number = st.text_input("Número da CAT", placeholder="Ex: 2024001234")
                communication_date = st.date_input("Data de Comunicação", value=date.today())
            
            # Campos de investigação
            st.subheader("🔍 Investigação do Acidente")
            col3, col4 = st.columns(2)
            
            with col3:
                investigation_completed = st.checkbox("Investigação Concluída", value=False)
                investigation_date = st.date_input("Data de Conclusão da Investigação", value=date.today()) if investigation_completed else None
            
            with col4:
                investigation_responsible = st.text_input("Responsável pela Investigação") if investigation_completed else None
                investigation_notes = st.text_area("Observações da Investigação", height=80) if investigation_completed else None
            
            description = st.text_area("Descrição do Acidente", height=100)
            corrective_actions = st.text_area("Ações Corretivas", height=100)

            # Status padronizado
            status = st.selectbox(
                "Status",
                options=["aberto", "em_investigacao", "fechado"],
                format_func=lambda x: {
                    "aberto": "Aberto",
                    "em_investigacao": "Em investigação",
                    "fechado": "Fechado"
                }[x]
            )
            
            # Upload de evidências
            uploaded_files = st.file_uploader(
                "Evidências (Fotos, PDFs, etc.)",
                accept_multiple_files=True,
                type=['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx']
            )
            
            submitted = st.form_submit_button("💾 Salvar Acidente", type="primary")
            
            if submitted:
                if not description.strip():
                    st.error("Descrição é obrigatória.")
                else:
                    try:
                        from managers.supabase_config import get_service_role_client
                        supabase = get_service_role_client()
                        
                        # Insere acidente
                        accident_data = {
                            "occurred_at": date_input.isoformat(),
                            "type": accident_type,
                            "classification": classification,
                            "body_part": body_part,
                            "description": description,
                            "lost_days": lost_days,
                            "root_cause": root_cause,
                            "status": status,
                            "is_fatal": is_fatal,
                            "cat_number": cat_number if cat_number else None,
                            "communication_date": communication_date.isoformat() if communication_date else None,
                            "investigation_completed": investigation_completed,
                            "investigation_date": investigation_date.isoformat() if investigation_date else None,
                            "investigation_responsible": investigation_responsible if investigation_responsible else None,
                            "investigation_notes": investigation_notes if investigation_notes else None
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
    
    with tab5:
        # Importa e exibe instruções
        from components.instructions import create_instructions_page, get_accidents_instructions
        
        instructions_data = get_accidents_instructions()
        create_instructions_page(
            title=instructions_data["title"],
            description=instructions_data["description"],
            sections=instructions_data["sections"],
            tips=instructions_data["tips"],
            warnings=instructions_data["warnings"],
            references=instructions_data["references"]
        )


def download_attachment(bucket, path):
    """Download de anexo"""
    try:
        supabase = get_supabase_client()
        if supabase:
            response = supabase.storage.from_(bucket).download(path)
            return response
        return None
    except:
        return None

def delete_attachment(attachment_id):
    """Remove anexo"""
    try:
        supabase = get_supabase_client()
        if supabase:
            supabase.table("attachments").delete().eq("id", attachment_id).execute()
            return True
        return False
    except:
        return False

if __name__ == "__main__":
    app({})
