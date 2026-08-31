import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from services.uploads import upload_evidence, get_attachments, download_attachment, delete_attachment
from components.cards import create_metric_row, create_bar_chart, create_pie_chart
from components.filters import apply_filters_to_df
from managers.supabase_config import get_supabase_client

def fetch_nonconformities(start_date=None, end_date=None):
    """Busca dados de não conformidades - filtra por usuário logado"""
    try:
        from managers.supabase_config import get_service_role_client
        from auth.auth_utils import get_user_id, is_admin, get_user_email
        user_id = get_user_id()
        user_email = get_user_email()
        
        if not user_id:
            return pd.DataFrame()
        
        # Usa service_role para contornar RLS e aplicar filtro de segurança no código
        supabase = get_service_role_client()
        
        query = supabase.table("nonconformities").select("*")
        
        # Filtra por usuário logado, exceto se for admin
        # Admin vê todos os dados sem filtro de created_by
        if not is_admin():
            # Usuário comum vê apenas suas próprias não conformidades
            query = query.eq("created_by", user_id)
        # Admin vê todas as não conformidades - não aplica filtro de created_by
        
        if start_date:
            query = query.gte("occurred_at", start_date.isoformat())
        if end_date:
            query = query.lte("occurred_at", end_date.isoformat())
        
        response = query.order("occurred_at", desc=True).execute()
        
        if response and hasattr(response, 'data'):
            df = pd.DataFrame(response.data) if response.data else pd.DataFrame()
            
            # Validação adicional de segurança para usuários não-admin
            if not is_admin() and not df.empty:
                # Filtra novamente para garantir (segurança em camadas)
                df = df[df['created_by'] == user_id]
        else:
            df = pd.DataFrame()

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
        
        # Aplica filtro de data após carregar os dados
        if start_date and 'occurred_at' in df.columns:
            df = df.copy()  # Evita SettingWithCopyWarning
            df['occurred_at'] = pd.to_datetime(df['occurred_at'], errors='coerce').dt.date
            df = df[df['occurred_at'] >= start_date]
        
        if end_date and 'occurred_at' in df.columns:
            df = df.copy()  # Evita SettingWithCopyWarning
            df['occurred_at'] = pd.to_datetime(df['occurred_at'], errors='coerce').dt.date
            df = df[df['occurred_at'] <= end_date]
        
        return df
    except Exception as e:
        st.error(f"Erro ao buscar não conformidades: {str(e)}")
        return pd.DataFrame()

def app(filters=None):
    # Verifica autenticação e trial
    from auth.auth_utils import require_login
    require_login()
    
    # Busca filtros do session state se não foram passados como parâmetro
    st.title("📋 Não Conformidades")
    
    # Tabs para diferentes visualizações
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Análise", "📋 Registros", "📎 Evidências", "➕ Nova Não Conformidade", "✅ Ações Corretivas"])
    
    with tab1:
        st.subheader("Análise de Não Conformidades")
        # Ajuda via popover
        c1, c2 = st.columns([6, 1])
        with c2:
            with st.popover("❓ Ajuda"):
                st.markdown(
                    "**Guia rápido**\n\n"
                    "1) Ajuste filtros (datas/período) na sidebar.\n"
                    "2) Revise métricas: abertas/encerradas e tempo médio.\n"
                    "3) Explore status, mês, norma e gravidade.\n\n"
                    "**Dicas**\n\n"
                    "- Sem 'opened_at', usamos 'occurred_at' nos gráficos.\n"
                    "- Campos podem variar (ex.: site_id).\n\n"
                    "**Definições**\n\n"
                    "- 'opened_at': data em que a N/C foi aberta/registrada no sistema.\n"
                    "- 'occurred_at': data em que a N/C (ou fato gerador) aconteceu em campo.\n\n"
                    "**📝 Feedback**\n"
                    "- Encontrou um erro? Acesse **Conta → Feedbacks** para reportar!"
                )
        with st.expander("Guia rápido de análise", expanded=False):
            st.markdown(
                "1. Ajuste o período na sidebar e confirme se há dados.\n"
                "2. Use as métricas para panorama (abertas, fechadas, tempo médio).\n"
                "3. Explore gráficos por status, mês, norma e gravidade.\n"
                "4. Vá em 'Registros' para filtrar por norma e buscar texto."
            )
        with st.popover("❓ Dicas"):
            st.markdown(
                "- Alguns campos podem variar entre ambientes (ex.: site).\n"
                "- Se não houver 'opened_at', os gráficos usam 'occurred_at' como fallback.\n\n"
                "**📝 Encontrou um erro ou tem uma sugestão?**\n"
                "- Acesse **Conta → Feedbacks** no menu para reportar ou sugerir melhorias!"
            )
        
        # Busca dados usando a função que respeita isolamento por usuário
        with st.spinner("Carregando dados de não conformidades..."):
            df = fetch_nonconformities(
                start_date=filters.get("start_date") if filters else None,
                end_date=filters.get("end_date") if filters else None
            )
        
        if df.empty:
            # Verifica se é problema de autenticação ou realmente não há dados
            from auth.auth_utils import get_user_id, get_user_email
            user_id = get_user_id()
            user_email = get_user_email()
            
            if not user_id:
                st.error("❌ **Erro**: Usuário não autenticado. Faça login novamente.")
            else:
                st.warning("Nenhuma não conformidade encontrada.")
        else:
            # Mostra informações sobre os dados encontrados
            st.success(f"📊 **{len(df)} não conformidade(s) encontrada(s)**")
            
            # Mostra informações de debug para verificar os dados reais
            if 'status' in df.columns:
                status_counts = df['status'].value_counts()
                st.write(f"**Status encontrados:** {dict(status_counts)}")
            
            if 'opened_at' in df.columns:
                df['opened_at'] = pd.to_datetime(df['opened_at'], errors='coerce')
                months_count = df['opened_at'].dt.to_period('M').value_counts()
                st.write(f"**Meses com registros:** {len(months_count)} diferentes")
            
            # Não aplicamos mais nenhum filtro adicional que possa excluir os dados
            # pois o objetivo é mostrar os dados existentes independentemente dos filtros do sistema
            pass  # df já está carregado com os dados
            
            # Métricas principais - considerando os status em português originais
            total_nc = len(df)
            
            if 'status' in df.columns:
                # Conta status em português que estão nos dados
                open_nc = len(df[df['status'].isin(['aberta', 'open'])])
                closed_nc = len(df[df['status'].isin(['encerrada', 'closed'])])
                in_progress_nc = len(df[df['status'].isin(['tratando', 'in_progress'])])
                overdue_nc = len(df[df['status'] == 'overdue'])
            else:
                open_nc = closed_nc = in_progress_nc = overdue_nc = 0
            
            # Calcula dias médios de resolução
            if 'status' in df.columns and 'resolution_date' in df.columns:
                # Filtra registros fechados considerando ambos os formatos
                closed_df = df[df['status'].isin(['encerrada', 'closed'])]
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
                    st.plotly_chart(fig1, width='stretch')
            
            with col2:
                # N/C por mês - usando opened_at em vez de occurred_at para análise temporal
                # porque no INSERT fornecido, occurred_at tem todos o mesmo valor ('2025-10-28')
                if 'opened_at' in df.columns:
                    df_temp = df.copy()
                    df_temp['opened_at'] = pd.to_datetime(df_temp['opened_at'])
                    df_temp['month'] = df_temp['opened_at'].dt.to_period('M')
                    monthly_counts = df_temp.groupby('month').size().reset_index(name='count')
                    monthly_counts['month'] = monthly_counts['month'].astype(str)
                    
                    fig2 = create_bar_chart(
                        monthly_counts,
                        'month',
                        'count',
                        'Não Conformidades por Mês (abertura)'
                    )
                    st.plotly_chart(fig2, width='stretch')
                elif 'occurred_at' in df.columns:
                    # Fallback para occurred_at se opened_at não estiver disponível
                    df_temp = df.copy()
                    df_temp['occurred_at'] = pd.to_datetime(df_temp['occurred_at'])
                    df_temp['month'] = df_temp['occurred_at'].dt.to_period('M')
                    monthly_counts = df_temp.groupby('month').size().reset_index(name='count')
                    monthly_counts['month'] = monthly_counts['month'].astype(str)
                    
                    fig2 = create_bar_chart(
                        monthly_counts,
                        'month',
                        'count',
                        'Não Conformidades por Mês (ocorrência)'
                    )
                    st.plotly_chart(fig2, width='stretch')
            
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
                st.plotly_chart(fig3, width='stretch')
            
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
                st.plotly_chart(fig4, width='stretch')
    
    with tab2:
        st.subheader("Registros de Não Conformidades")
        
        if not df.empty:
            # Filtros locais para a tabela (não afetam o dataframe principal)
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
            
            # Aplica filtros locais
            filtered_df = df.copy()
            
            if status_filter != "Todos" and 'status' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['status'] == status_filter]
            
            if norm_filter != "Todas" and 'norm_reference' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['norm_reference'] == norm_filter]
            
            if search_term and 'description' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['description'].str.contains(search_term, case=False, na=False)]
            
            # Exibe tabela
            display_cols = ['occurred_at', 'norm_reference', 'severity', 'status', 'description']
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
                try:
                    attachments = get_attachments("nonconformity", str(nc_id))
                except:
                    attachments = []
                
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
                                try:
                                    file_data = download_attachment(attachment['bucket'], attachment['path'])
                                    if file_data:
                                        st.download_button(
                                            "💾 Baixar Arquivo",
                                            file_data,
                                            attachment['filename'],
                                            key=f"download_btn_{attachment['id']}"
                                        )
                                except:
                                    st.error("Erro ao baixar arquivo")
                        
                        with col3:
                            if st.button("🗑️ Remover", key=f"remove_{attachment['id']}"):
                                try:
                                    if delete_attachment(attachment['id']):
                                        st.success("Evidência removida!")
                                        st.rerun()
                                except:
                                    st.error("Erro ao remover evidência")
                else:
                    st.info("Nenhuma evidência encontrada para esta não conformidade.")
        else:
            st.info("Nenhuma não conformidade encontrada para exibir evidências.")
    
    with tab4:
        st.subheader("Registrar Nova Não Conformidade")
        
        # Instruções de cadastro
        with st.expander("📖 Como Cadastrar uma Não Conformidade", expanded=True):
            st.markdown("""
            **Siga estes passos para registrar uma nova não conformidade:**
            
            1. **Data de Ocorrência**: Selecione a data em que a não conformidade foi identificada ou ocorreu
            
            2. **Norma de Referência**: Informe qual norma, procedimento ou padrão foi violado ou não atendido
               - Exemplos: NR-12, ISO 9001, Procedimento de Segurança, etc.
            
            3. **Gravidade**: Avalie a gravidade da não conformidade:
               - **Grave**: Risco significativo, requer ação imediata
               - **Moderada**: Risco médio, requer atenção
               - **Leve**: Risco baixo, pode ser tratada normalmente
            
            4. **Descrição**: Descreva detalhadamente:
               - O que foi identificado como não conformidade
               - Contexto e situação
               - Impacto potencial
               - Local onde foi identificado
            
            5. **Status**: Defina o status atual:
               - **Aberta**: Não conformidade identificada, aguardando tratamento
               - **Encerrada**: Não conformidade já foi tratada e resolvida
            
            6. **Evidências**: (Opcional) Anexe fotos, documentos, relatórios ou outros arquivos que comprovem ou documentem a não conformidade
            
            **💡 Importante**: 
            - Não conformidades são situações que não atendem aos requisitos estabelecidos
            - Podem estar relacionadas a normas, procedimentos, padrões de qualidade ou segurança
            - O registro adequado permite rastreabilidade e melhoria contínua
            
            **📋 Campos Obrigatórios**: Data de Ocorrência, Norma de Referência, Gravidade e Descrição
            """)
        
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
                # site_id, employee_id, resolution_date removidos - não existem na tabela nonconformities
                
                status = st.selectbox(
                    "Status",
                    options=["aberta", "encerrada"],
                    format_func=lambda x: {
                        "aberta": "Aberta",
                        "encerrada": "Encerrada"
                    }[x]
                )

            description = st.text_area("Descrição da Não Conformidade", height=100)
            # corrective_actions removido - campo não existe na tabela nonconformities
            
            # Upload de evidências
            uploaded_files = st.file_uploader(
                "Evidências (Fotos, PDFs, etc.)",
                accept_multiple_files=True,
                type=['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx']
            )
            
            submitted = st.form_submit_button("💾 Salvar Não Conformidade", type="primary")
            
            if submitted:
                if not description.strip():
                    st.error("Descrição é obrigatória.")
                else:
                    try:
                        from managers.supabase_config import get_service_role_client
                        from auth.auth_utils import get_user_id
                        # Usa service_role para contornar RLS ao inserir não conformidade
                        supabase = get_service_role_client()
                        
                        user_id = get_user_id()
                        if not user_id:
                            st.error("Usuário não autenticado.")
                            return
                        
                        # Insere não conformidade nos campos que existem na tabela
                        nc_data = {
                            "opened_at": date_input.isoformat(),
                            "occurred_at": date_input.isoformat(),
                            "standard_ref": norm_reference,
                            "severity": severity,
                            "status": status,
                            "description": description,
                            "created_by": user_id
                        }
                        
                        result = supabase.table("nonconformities").insert(nc_data).execute()
                        
                        if result.data:
                            nc_id = result.data[0]['id']
                            st.success("✅ Não conformidade registrada com sucesso!")
                            
                            # Registra log da ação
                            try:
                                from services.user_logs import log_action
                                log_action(
                                    action_type="create",
                                    entity_type="nonconformity",
                                    description=f"Não conformidade criada: {description[:100]}...",
                                    entity_id=nc_id,
                                    metadata={"severity": severity, "status": status}
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
                                        "nonconformity",
                                        str(nc_id),
                                        description=f"Evidência da N/C de {date_input}"
                                    )
                                st.success(f"✅ {len(uploaded_files)} evidência(s) enviada(s)!")
                            
                            st.rerun()
                        else:
                            st.error("Erro ao salvar não conformidade.")
                            
                    except Exception as e:
                        st.error(f"Erro: {str(e)}")
    
    with tab5:
        st.subheader("✅ Ações Corretivas")
        st.info("📋 Registre e gerencie ações corretivas relacionadas às não conformidades usando a metodologia 5W2H")
        
        # Busca todas as não conformidades para seleção
        if df.empty:
            st.warning("Nenhuma não conformidade encontrada. Registre não conformidades primeiro para criar ações corretivas.")
        else:
            # Seleção de não conformidade
            nc_options = {f"ID: {row['id'][:8]}... - {row.get('description', 'Sem descrição')[:50]}": row['id'] 
                              for _, row in df.iterrows()}
            
            selected_nc_id = st.selectbox(
                "Selecione a Não Conformidade",
                options=list(nc_options.keys()),
                help="Selecione a não conformidade para ver ou criar ações corretivas"
            )
            
            if selected_nc_id:
                nc_id = nc_options[selected_nc_id]
                
                # Busca ações existentes
                from services.actions import get_actions_by_entity, create_action, update_action_status, delete_action, action_form
                
                actions = get_actions_by_entity("nonconformity", nc_id)
                
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
                    st.info("Nenhuma ação corretiva registrada para esta não conformidade.")
                
                # Formulário para nova ação
                st.markdown("---")
                st.markdown("### ➕ Nova Ação Corretiva")
                
                new_action = action_form("nonconformity", nc_id)
                if new_action:
                    if create_action(new_action):
                        st.success("✅ Ação corretiva registrada com sucesso!")
                        st.rerun()

def get_sites():
    """Busca sites disponíveis"""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            return []
        response = supabase.table("sites").select("id, code, name").execute()
        return response.data if response.data else []
    except:
        return []

def get_employees():
    """Busca funcionários (employees) - filtra por usuário logado"""
    try:
        from services.employees import get_all_employees
        employees = get_all_employees()
        # Retorna apenas os campos necessários para compatibilidade
        return [{"id": e.get("id"), "full_name": e.get("full_name"), "department": e.get("department")} for e in employees]
    except:
        return []

def download_attachment(bucket, path):
    """Download de anexo"""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            return None
        response = supabase.storage.from_(bucket).download(path)
        return response
    except:
        return None

def delete_attachment(attachment_id):
    """Remove anexo"""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            return False
        supabase.table("attachments").delete().eq("id", attachment_id).execute()
        return True
    except:
        return False

if __name__ == "__main__":
    app({})
