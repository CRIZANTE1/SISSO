import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from services.kpi import fetch_kpi_data, generate_kpi_summary, calculate_poisson_control_limits
from components.cards import create_dashboard_summary, create_metric_row, create_trend_chart, create_control_chart
from components.filters import apply_filters_to_df

def app(filters=None):
    st.title("📊 Visão Geral - SSO")
    
    # Busca filtros do session state se não foram passados como parâmetro
    if filters is None:
        filters = st.session_state.get('filters', {})
    
    # Busca dados do usuário atual
    from auth.auth_utils import get_user_email
    user_email = get_user_email()
    
    # Busca dados
    with st.spinner("Carregando dados..."):
        df = fetch_kpi_data(
            user_email=user_email,
            start_date=filters.get("start_date"),
            end_date=filters.get("end_date")
        )
    
    if df.empty:
        st.warning("Nenhum dado encontrado com os filtros aplicados.")
        return
    
    # Aplica filtros adicionais
    df = apply_filters_to_df(df, filters)
    
    # Gera resumo dos KPIs
    kpi_summary = generate_kpi_summary(df)
    
    # Estatísticas do Sistema
    st.subheader("📊 Estatísticas do Sistema")
    
    # Busca dados de todas as tabelas
    system_stats = get_system_statistics()
    
    # Exibe estatísticas em cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Sites", system_stats.get('sites', 0))
        st.metric("Contratadas", system_stats.get('contractors', 0))
    
    with col2:
        st.metric("Acidentes", system_stats.get('accidents', 0))
        st.metric("Quase-Acidentes", system_stats.get('near_misses', 0))
    
    with col3:
        st.metric("Não Conformidades", system_stats.get('nonconformities', 0))
        st.metric("Registros de Horas", system_stats.get('hours_records', 0))
    
    st.markdown("---")
    
    # KPIs Principais - Simplificados e Corrigidos
    st.subheader("📈 Indicadores de Segurança")
    
    if not df.empty and 'hours' in df.columns:
        # Calcula KPIs do período mais recente
        latest_data = df.iloc[-1] if len(df) > 0 else None
        
        if latest_data is not None:
            # Taxa de Frequência (acidentes por 1M horas)
            total_accidents = latest_data.get('accidents_total', 0)
            total_hours = latest_data.get('hours', 0)
            freq_rate = (total_accidents / total_hours * 1_000_000) if total_hours > 0 else 0
            
            # Taxa de Gravidade (dias perdidos por 1M horas)
            total_lost_days = latest_data.get('lost_days_total', 0)
            sev_rate = (total_lost_days / total_hours * 1_000_000) if total_hours > 0 else 0
            
            # Comparação com período anterior (se houver)
            if len(df) > 1:
                prev_data = df.iloc[-2]
                prev_freq_rate = (prev_data.get('accidents_total', 0) / prev_data.get('hours', 1) * 1_000_000) if prev_data.get('hours', 0) > 0 else 0
                prev_sev_rate = (prev_data.get('lost_days_total', 0) / prev_data.get('hours', 1) * 1_000_000) if prev_data.get('hours', 0) > 0 else 0
                
                freq_change = ((freq_rate - prev_freq_rate) / prev_freq_rate * 100) if prev_freq_rate > 0 else None
                sev_change = ((sev_rate - prev_sev_rate) / prev_sev_rate * 100) if prev_sev_rate > 0 else None
            else:
                freq_change = None
                sev_change = None
            
            # Exibe métricas
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if freq_change is not None:
                    st.metric(
                        "Taxa de Frequência", 
                        f"{freq_rate:.2f}",
                        delta=f"{freq_change:+.1f}%" if freq_change is not None else None
                    )
                else:
                    st.metric("Taxa de Frequência", f"{freq_rate:.2f}")
            
            with col2:
                if sev_change is not None:
                    st.metric(
                        "Taxa de Gravidade", 
                        f"{sev_rate:.2f}",
                        delta=f"{sev_change:+.1f}%" if sev_change is not None else None
                    )
                else:
                    st.metric("Taxa de Gravidade", f"{sev_rate:.2f}")
            
            with col3:
                st.metric("Total de Acidentes", int(total_accidents))
            
            with col4:
                st.metric("Dias Perdidos", int(total_lost_days))
            
            # Informações contextuais
            st.caption(f"📊 Baseado em {total_hours:,.0f} horas trabalhadas no período")
            
            if freq_rate > 5.0:
                st.warning("⚠️ Taxa de frequência elevada - revisar procedimentos de segurança")
            if sev_rate > 50.0:
                st.warning("⚠️ Taxa de gravidade elevada - implementar medidas preventivas")
            if total_lost_days == 0 and total_accidents > 0:
                st.info("ℹ️ Acidentes sem dias perdidos registrados")
        else:
            st.info("📊 Nenhum dado disponível para calcular indicadores")
    else:
        st.info("📊 Dados insuficientes para calcular indicadores de segurança")
    
    st.markdown("---")
    
    # Gráficos principais
    st.subheader("📊 Análise de Acidentes")
    
    if not df.empty and 'period' in df.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de distribuição por mês - Simplificado
            fig1 = px.bar(
                df, 
                x="period", 
                y="accidents_total",
                title="Total de Acidentes por Mês",
                color="accidents_total",
                color_continuous_scale="Reds"
            )
            fig1.update_layout(
                height=400,
                xaxis_title="Período",
                yaxis_title="Número de Acidentes",
                showlegend=False,
                font=dict(size=12)
            )
            fig1.update_traces(marker_line_width=0)
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # Gráfico de tipos de acidente
            accident_types = df[['fatalities', 'with_injury', 'without_injury']].sum()
            accident_types = accident_types[accident_types > 0]  # Remove zeros
            
            if not accident_types.empty:
                fig2 = px.pie(
                    values=accident_types.values,
                    names=['Fatais', 'Com Lesão', 'Sem Lesão'],
                    title="Distribuição por Tipo de Acidente",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig2.update_layout(
                    height=400,
                    font=dict(size=12)
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("📊 **Distribuição por Tipo**\n\nNenhum acidente registrado para exibir a distribuição.")
    else:
        st.info("📊 **Análise de Acidentes**\n\nNenhum dado de acidentes disponível para exibir os gráficos.")
    
    # Análise de Tendências
    st.subheader("📈 Análise de Tendências")
    
    if not df.empty and 'period' in df.columns and 'hours' in df.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            # Taxa de Frequência - Simplificada
            df['freq_rate'] = (df['accidents_total'] / df['hours']) * 1_000_000
            fig3 = px.line(
                df,
                x="period",
                y="freq_rate",
                title="Taxa de Frequência (por 1M horas)",
                markers=True
            )
            fig3.update_layout(
                height=400,
                xaxis_title="Período",
                yaxis_title="Taxa de Frequência",
                font=dict(size=12)
            )
            fig3.update_traces(line=dict(width=3), marker=dict(size=8))
            st.plotly_chart(fig3, use_container_width=True)
        
        with col2:
            # Taxa de Gravidade - Simplificada
            df['sev_rate'] = (df['lost_days_total'] / df['hours']) * 1_000_000
            fig4 = px.line(
                df,
                x="period",
                y="sev_rate",
                title="Taxa de Gravidade (por 1M horas)",
                markers=True,
                color_discrete_sequence=['orange']
            )
            fig4.update_layout(
                height=400,
                xaxis_title="Período",
                yaxis_title="Taxa de Gravidade",
                font=dict(size=12)
            )
            fig4.update_traces(line=dict(width=3), marker=dict(size=8))
            st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("📈 **Análise de Tendências**\n\nNenhum dado suficiente disponível para exibir as tendências.")
    
    # Meta de Acidentes Registráveis (Fatalidades + Com Lesão)
    st.subheader("🎯 Meta de Acidentes Registráveis (≤ 6 por ano)")
    TARGET_RECORDABLES_PER_YEAR = 6
    TARGET_RECORDABLES_PER_MONTH = 0.5  # 6/12 meses
    
    if not df.empty and 'period' in df.columns:
        kpi_df = df.copy()
        kpi_df['period'] = pd.to_datetime(kpi_df['period'])
        kpi_df['year'] = kpi_df['period'].dt.year
        kpi_df['month'] = kpi_df['period'].dt.month
        kpi_df['month_name'] = kpi_df['period'].dt.strftime('%Y-%m')
        
        # Soma mensal
        monthly = (
            kpi_df.groupby(['year', 'month', 'month_name'])[['fatalities', 'with_injury', 'hours']]
            .sum()
            .reset_index()
        )
        monthly['recordables'] = monthly['fatalities'] + monthly['with_injury']
        monthly['recordable_rate'] = monthly.apply(
            lambda r: ((r['recordables'] / r['hours']) * 1_000_000) if r['hours'] else 0.0,
            axis=1
        )
        
        # Acumulado anual para cada mês
        monthly['yearly_cumulative'] = monthly.groupby('year')['recordables'].cumsum()
        monthly['yearly_target'] = TARGET_RECORDABLES_PER_YEAR
        monthly['monthly_target'] = TARGET_RECORDABLES_PER_MONTH
        
        # KPIs do mês atual
        latest_month = monthly.iloc[-1] if not monthly.empty else None
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Registráveis no Mês", int(latest_month['recordables']) if latest_month is not None else 0)
        with c2:
            st.metric("Acumulado no Ano", int(latest_month['yearly_cumulative']) if latest_month is not None else 0)
        with c3:
            st.metric("Meta Anual", TARGET_RECORDABLES_PER_YEAR)
        with c4:
            if latest_month is not None:
                status_txt = "Dentro da Meta" if latest_month['yearly_cumulative'] <= TARGET_RECORDABLES_PER_YEAR else "Acima da Meta"
                if latest_month['yearly_cumulative'] <= TARGET_RECORDABLES_PER_YEAR:
                    st.success(status_txt)
                else:
                    st.error(status_txt)
            else:
                st.info("Sem dados")
        
        # Gráfico mensal - Fatalidades + Com Lesão
        display_df = monthly.copy()
        
        # Cria colunas separadas para cada tipo
        display_df['Fatalidades'] = display_df['fatalities']
        display_df['Com Lesão'] = display_df['with_injury']
        
        # Gráfico de barras empilhadas
        fig_goal = px.bar(
            display_df,
            x='month_name',
            y=['Fatalidades', 'Com Lesão'],
            title='Acidentes Registráveis por Mês (Fatalidades + Com Lesão)',
            color_discrete_map={'Fatalidades': '#dc3545', 'Com Lesão': '#ffc107'},
            text_auto=True
        )
        fig_goal.update_layout(
            height=420,
            xaxis_title='Mês',
            yaxis_title='Número de Acidentes',
            barmode='stack',
            font=dict(size=12)
        )
        fig_goal.update_traces(
            textposition='inside',
            textfont=dict(size=10, color='white')
        )
        
        # Linha da meta mensal
        fig_goal.add_hline(
            y=TARGET_RECORDABLES_PER_MONTH, 
            line_dash='dash', 
            line_color='#6c757d', 
            annotation_text='Meta: 0.5/mês', 
            annotation_position='top right'
        )
        st.plotly_chart(fig_goal, use_container_width=True)
        
        # Resumo simples dos dados
        col1, col2, col3 = st.columns(3)
        with col1:
            total_fatalities = display_df['Fatalidades'].sum()
            st.metric("Total Fatalidades", total_fatalities, delta=None)
        with col2:
            total_injuries = display_df['Com Lesão'].sum()
            st.metric("Total Com Lesão", total_injuries, delta=None)
        with col3:
            total_recordables = total_fatalities + total_injuries
            st.metric("Total Registráveis", total_recordables, delta=None)
        
        st.markdown("---")
        
        # Gráfico de acumulado anual vs meta - Simplificado
        fig_cumulative = px.line(
            display_df,
            x='month_name',
            y='yearly_cumulative',
            markers=True,
            title='Acumulado Anual de Acidentes Registráveis',
            color_discrete_sequence=['#007bff']
        )
        fig_cumulative.update_layout(
            height=400,
            xaxis_title='Mês',
            yaxis_title='Total Acumulado no Ano',
            font=dict(size=12)
        )
        fig_cumulative.update_traces(line=dict(width=4), marker=dict(size=10))
        
        # Adiciona linha da meta anual
        fig_cumulative.add_hline(
            y=TARGET_RECORDABLES_PER_YEAR, 
            line_dash='dash', 
            line_color='#dc3545', 
            annotation_text='Meta: 6 por ano', 
            annotation_position='top right'
        )
        
        # Adiciona área de alerta (acima de 4 acidentes)
        fig_cumulative.add_hrect(
            y0=4, y1=TARGET_RECORDABLES_PER_YEAR,
            fillcolor="rgba(255, 193, 7, 0.2)",
            annotation_text="Zona de Atenção",
            annotation_position="top left"
        )
        
        st.plotly_chart(fig_cumulative, use_container_width=True)
        
        # Taxa de registráveis por 1M horas (mensal) - Simplificado
        if display_df['recordable_rate'].sum() > 0:  # Só mostra se houver dados
            st.caption("📊 Taxa de registráveis por 1M de horas trabalhadas")
            fig_rate = px.line(
                display_df,
                x='month_name',
                y='recordable_rate',
                markers=True,
                title='Taxa de Acidentes Registráveis (por 1M horas)',
                color_discrete_sequence=['#17a2b8']
            )
            fig_rate.update_layout(
                height=360,
                xaxis_title='Mês',
                yaxis_title='Taxa por 1M horas',
                font=dict(size=12)
            )
            fig_rate.update_traces(line=dict(width=3), marker=dict(size=8))
            st.plotly_chart(fig_rate, use_container_width=True)
        else:
            st.info("📊 **Taxa de Registráveis**\n\nNenhuma taxa calculável (sem horas trabalhadas registradas).")
    else:
        st.info("🎯 **Meta de Registráveis**\n\nNenhum dado disponível para a análise mensal da meta.")
    
    # Resumo por Período
    st.subheader("📅 Resumo por Período")
    
    if not df.empty:
        # Tabela simplificada
        period_summary = df.groupby('period').agg({
            'accidents_total': 'sum',
            'fatalities': 'sum',
            'with_injury': 'sum',
            'without_injury': 'sum',
            'lost_days_total': 'sum',
            'hours': 'sum'
        }).reset_index()
        
        # Renomeia colunas para português
        period_summary.columns = [
            'Período', 'Total Acidentes', 'Fatais', 'Com Lesão', 
            'Sem Lesão', 'Dias Perdidos', 'Horas Trabalhadas'
        ]
        
        # Formata números
        for col in ['Total Acidentes', 'Fatais', 'Com Lesão', 'Sem Lesão', 'Dias Perdidos']:
            period_summary[col] = period_summary[col].astype(int)
        
        period_summary['Horas Trabalhadas'] = period_summary['Horas Trabalhadas'].round(0).astype(int)
        
        st.dataframe(
            period_summary,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Nenhum dado disponível para resumo por período.")
    
    # Alertas e recomendações
    st.subheader("🚨 Alertas e Recomendações")
    
    # (Re)calcula dataframe de controle caso disponível
    control_df = pd.DataFrame()
    if not df.empty and 'accidents_total' in df.columns and 'hours' in df.columns:
        control_df = calculate_poisson_control_limits(df)
    
    # Verifica padrões de controle
    if not control_df.empty and 'out_of_control' in control_df.columns:
        out_of_control_count = control_df['out_of_control'].sum()
        if out_of_control_count > 0:
            st.warning(f"⚠️ **{out_of_control_count}** pontos fora de controle estatístico detectados!")
        
        # Verifica tendências
        if len(control_df) >= 8:
            recent_trend = control_df['accidents_total'].tail(8)
            if all(recent_trend.iloc[i] > recent_trend.iloc[i-1] for i in range(1, len(recent_trend))):
                st.error("🚨 **Tendência ascendente crítica:** 8 pontos consecutivos em alta!")
            elif all(recent_trend.iloc[i] < recent_trend.iloc[i-1] for i in range(1, len(recent_trend))):
                st.success("✅ **Tendência descendente positiva:** 8 pontos consecutivos em baixa!")
    
    # Recomendações baseadas nos dados
    if kpi_summary.get('frequency_rate', 0) > 5.0:
        st.info("💡 **Recomendação:** Taxa de frequência elevada. Revisar procedimentos de segurança.")
    
    if kpi_summary.get('severity_rate', 0) > 50.0:
        st.info("💡 **Recomendação:** Taxa de gravidade elevada. Implementar medidas preventivas.")
    
    if kpi_summary.get('total_fatalities', 0) > 0:
        st.error("🚨 **CRÍTICO:** Investigação imediata necessária para acidentes fatais!")

def get_system_statistics():
    """Busca estatísticas gerais do sistema"""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        
        if not supabase:
            return {}
        
        stats = {}
        
        # Conta registros em cada tabela
        try:
            # Sites (se existir)
            sites_response = supabase.table("sites").select("id", count="exact").execute()
            stats['sites'] = sites_response.count or 0
        except:
            stats['sites'] = 0
        
        try:
            # Contratadas (se existir)
            contractors_response = supabase.table("contractors").select("id", count="exact").execute()
            stats['contractors'] = contractors_response.count or 0
        except:
            stats['contractors'] = 0
        
        try:
            # Acidentes
            accidents_response = supabase.table("accidents").select("id", count="exact").execute()
            stats['accidents'] = accidents_response.count or 0
        except:
            stats['accidents'] = 0
        
        try:
            # Quase-acidentes
            near_misses_response = supabase.table("near_misses").select("id", count="exact").execute()
            stats['near_misses'] = near_misses_response.count or 0
        except:
            stats['near_misses'] = 0
        
        try:
            # Não conformidades
            nonconformities_response = supabase.table("nonconformities").select("id", count="exact").execute()
            stats['nonconformities'] = nonconformities_response.count or 0
        except:
            stats['nonconformities'] = 0
        
        try:
            # Registros de horas
            hours_response = supabase.table("hours_worked_monthly").select("id", count="exact").execute()
            stats['hours_records'] = hours_response.count or 0
        except:
            stats['hours_records'] = 0
        
        return stats
        
    except Exception as e:
        st.error(f"Erro ao buscar estatísticas do sistema: {str(e)}")
        return {}

if __name__ == "__main__":
    app({})
