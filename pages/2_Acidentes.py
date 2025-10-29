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
            
        data = query.order("occurred_at", desc=True).execute().data
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Erro ao buscar acidentes: {str(e)}")
        return pd.DataFrame()

def app(filters=None):
    st.title("🚨 Acidentes")
    
    # Busca filtros do session state se não foram passados como parâmetro
    if filters is None:
        filters = st.session_state.get('filters', {})
    
    # Tabs para diferentes visualizações
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Análise", "📋 Registros", "📎 Evidências", "➕ Novo Acidente"])
    
    with tab1:
        st.subheader("Análise de Acidentes")
        
        # Busca dados
        with st.spinner("Carregando dados de acidentes..."):
            df = fetch_accidents(
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
                    df['month'] = pd.to_datetime(df['occurred_at']).dt.to_period('M')
                    monthly_counts = df.groupby('month').size().reset_index(name='count')
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
                filtered_df = filtered_df[filtered_df['description'].str.contains(search_term, case=False, na=False)]
            
            # Exibe tabela
            display_cols = ['occurred_at', 'type', 'description', 'lost_days', 'root_cause', 'status']
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
            
            with col2:
                classification = st.text_input("Classificação")
                body_part = st.text_input("Parte do Corpo Afetada")
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
                            "status": "fechado"
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

    with tab2:
        st.subheader("📚 Metodologia de Análise de Acidentes")
        
        st.markdown("""
        ## 🎯 Objetivo da Análise
        
        A análise de acidentes tem como objetivo:
        - **Identificar** padrões e tendências nos acidentes
        - **Investigar** causas raiz dos eventos
        - **Prevenir** ocorrências futuras
        - **Melhorar** continuamente a segurança
        - **Comunicar** lições aprendidas
        """)
        
        st.markdown("""
        ## 📊 Classificação de Acidentes
        
        ### Por Gravidade
        1. **Fatais**: Acidentes que resultam em morte
        2. **Com Lesão**: Acidentes que resultam em lesões físicas
        3. **Sem Lesão**: Acidentes que não resultam em lesões físicas
        
        ### Por Tipo
        - **Quedas**: Quedas de altura, escorregões, tropeços
        - **Cortes**: Cortes por ferramentas, objetos cortantes
        - **Queimaduras**: Queimaduras térmicas, químicas, elétricas
        - **Impactos**: Colisões, golpes, esmagamentos
        - **Outros**: Outros tipos de acidentes não classificados
        
        ### Por Localização
        - **Área de Produção**: Locais onde ocorrem atividades produtivas
        - **Escritórios**: Áreas administrativas
        - **Área Externa**: Pátios, estacionamentos, áreas externas
        - **Outros**: Outras localizações específicas
        """)
        
        st.markdown("""
        ## 📈 Métricas de Análise
        
        ### Métricas Quantitativas
        1. **Total de Acidentes**: Contagem absoluta de eventos
        2. **Taxa de Frequência**: Acidentes por 1M horas trabalhadas
        3. **Taxa de Gravidade**: Dias perdidos por 1M horas trabalhadas
        4. **Distribuição por Tipo**: Percentual de cada categoria
        5. **Distribuição por Local**: Percentual por localização
        
        ### Métricas Temporais
        1. **Evolução Mensal**: Tendência ao longo do tempo
        2. **Sazonalidade**: Padrões por estação do ano
        3. **Dias da Semana**: Análise por dia da semana
        4. **Horários**: Análise por período do dia
        
        ### Métricas de Impacto
        1. **Dias Perdidos**: Impacto econômico
        2. **Custos Diretos**: Gastos com tratamento
        3. **Custos Indiretos**: Perda de produtividade
        4. **Impacto Social**: Efeitos na equipe
        """)
        
        st.markdown("""
        ## 🔍 Análise de Causas
        
        ### Método 5 Porquês
        1. **Por que** o acidente aconteceu?
        2. **Por que** essa causa ocorreu?
        3. **Por que** essa condição existia?
        4. **Por que** não foi detectada?
        5. **Por que** não foi prevenida?
        
        ### Árvore de Causas
        - **Causa Imediata**: Ação ou condição que causou o acidente
        - **Causa Contributiva**: Fatores que contribuíram
        - **Causa Raiz**: Fator fundamental que permitiu o evento
        
        ### Fatores Humanos
        - **Comportamento**: Ações inseguras
        - **Conhecimento**: Falta de treinamento
        - **Atitude**: Negligência ou pressa
        - **Fadiga**: Cansaço físico ou mental
        
        ### Fatores Ambientais
        - **Condições de Trabalho**: Iluminação, temperatura, ruído
        - **Equipamentos**: Falhas, manutenção inadequada
        - **Procedimentos**: Instruções inadequadas ou ausentes
        - **Organização**: Pressão por produtividade
        """)
        
        st.markdown("""
        ## 📊 Visualizações e Gráficos
        
        ### Gráficos de Barras
        - **Comparação**: Entre diferentes categorias
        - **Evolução**: Ao longo do tempo
        - **Ranking**: Ordenação por frequência
        
        ### Gráficos de Pizza
        - **Distribuição**: Percentual de cada categoria
        - **Proporção**: Relação entre diferentes tipos
        - **Composição**: Estrutura dos acidentes
        
        ### Gráficos de Linha
        - **Tendências**: Evolução temporal
        - **Sazonalidade**: Padrões repetitivos
        - **Comparação**: Entre diferentes períodos
        
        ### Mapas de Calor
        - **Localização**: Concentração por área
        - **Temporal**: Padrões por horário
        - **Gravidade**: Intensidade dos eventos
        """)
        
        st.markdown("""
        ## 🚨 Sistema de Alertas
        
        ### Critérios de Alerta
        1. **Acidentes Fatais**: Sempre crítico
        2. **Aumento de 50%**: Em relação ao período anterior
        3. **Padrões Anômalos**: Sequências incomuns
        4. **Concentração**: Muitos acidentes em uma área
        
        ### Níveis de Alerta
        - **🔴 CRÍTICO**: Ação imediata necessária
        - **🟡 ATENÇÃO**: Monitoramento intensivo
        - **🟢 NORMAL**: Situação controlada
        
        ### Ações Recomendadas
        - **Investigar**: Causas raiz imediatamente
        - **Implementar**: Medidas corretivas
        - **Comunicar**: Informar stakeholders
        - **Monitorar**: Acompanhar efetividade
        """)
        
        st.markdown("""
        ## 📋 Relatórios e Documentação
        
        ### Relatório de Acidente
        1. **Dados Básicos**: Data, hora, local, envolvidos
        2. **Descrição**: Narrativa do evento
        3. **Causas**: Análise de causas raiz
        4. **Ações**: Medidas tomadas e recomendadas
        5. **Anexos**: Fotos, documentos, evidências
        
        ### Relatório de Análise
        1. **Resumo Executivo**: Visão geral para gestores
        2. **Análise Detalhada**: Dados técnicos
        3. **Tendências**: Padrões identificados
        4. **Recomendações**: Ações sugeridas
        5. **Acompanhamento**: Status das ações
        
        ### Documentação de Evidências
        - **Fotografias**: Registro visual do local
        - **Vídeos**: Gravações do evento
        - **Documentos**: Relatórios, laudos
        - **Depoimentos**: Testemunhas e envolvidos
        """)
        
        st.markdown("""
        ## 🔧 Ferramentas e Recursos
        
        ### Upload de Evidências
        - **Formatos Suportados**: JPG, PNG, PDF, DOC, XLS
        - **Tamanho Máximo**: 10MB por arquivo
        - **Segurança**: Criptografia e controle de acesso
        - **Organização**: Categorização automática
        
        ### Filtros e Busca
        - **Por Período**: Data de ocorrência
        - **Por Tipo**: Classificação do acidente
        - **Por Local**: Área de ocorrência
        - **Por Gravidade**: Nível de impacto
        
        ### Exportação de Dados
        - **Formato CSV**: Para análise externa
        - **Relatórios PDF**: Para apresentações
        - **Dashboards**: Para monitoramento
        - **Alertas**: Para notificações
        """)
        
        st.markdown("""
        ## 📚 Referências e Normas
        
        ### Normas Regulamentadoras
        - **NR-5**: Comissão Interna de Prevenção de Acidentes
        - **NR-7**: Programa de Controle Médico de Saúde Ocupacional
        - **NR-18**: Condições e Meio Ambiente de Trabalho
        - **NR-35**: Trabalho em Altura
        
        ### Padrões Internacionais
        - **ISO 45001**: Sistema de Gestão de SST
        - **OHSAS 18001**: Especificação para SST
        - **ANSI Z16.1**: Métodos de Registro de Acidentes
        - **OSHA**: Occupational Safety and Health Administration
        
        ### Metodologias de Análise
        - **Análise de Árvore de Falhas**: FTA
        - **Análise de Modos de Falha**: FMEA
        - **Análise de Riscos**: HAZOP
        - **Investigação de Acidentes**: Método TapRooT
        """)

if __name__ == "__main__":
    app({})
