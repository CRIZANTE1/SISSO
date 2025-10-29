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
    
    # Resumo executivo
    create_dashboard_summary(kpi_summary)
    
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
    
    if not df.empty and 'period' in df.columns:
        kpi_df = df.copy()
        kpi_df['year'] = pd.to_datetime(kpi_df['period']).dt.year
        # Soma anual
        yearly = (
            kpi_df.groupby('year')[['fatalities', 'with_injury', 'hours']]
            .sum()
            .reset_index()
        )
        yearly['recordables'] = yearly['fatalities'] + yearly['with_injury']
        yearly['recordable_rate'] = yearly.apply(
            lambda r: ((r['recordables'] / r['hours']) * 1_000_000) if r['hours'] else 0.0,
            axis=1
        )
        
        # KPIs do ano corrente
        current_year = int(yearly['year'].max()) if not yearly.empty else None
        current_row = yearly[yearly['year'] == current_year].iloc[0] if current_year is not None else None
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Registráveis no Ano", int(current_row['recordables']) if current_row is not None else 0)
        with c2:
            st.metric("Meta Anual", TARGET_RECORDABLES_PER_YEAR)
        with c3:
            status_txt = "Dentro da Meta" if current_row is not None and current_row['recordables'] <= TARGET_RECORDABLES_PER_YEAR else "Acima da Meta"
            if current_row is not None and current_row['recordables'] <= TARGET_RECORDABLES_PER_YEAR:
                st.success(status_txt)
            else:
                st.error(status_txt)
        
        # Gráfico anual com linha da meta
        display_df = yearly.copy()
        display_df['Situação'] = display_df['recordables'] <= TARGET_RECORDABLES_PER_YEAR
        fig_goal = px.bar(
            display_df,
            x='year',
            y='recordables',
            color='Situação',
            color_discrete_map={True: '#28a745', False: '#dc3545'},
            title='Acidentes Registráveis por Ano'
        )
        fig_goal.update_layout(
            height=420,
            xaxis_title='Ano',
            yaxis_title='Registráveis (Fatalidades + Com Lesão)',
            showlegend=True,
            font=dict(size=12)
        )
        # Linha da meta
        fig_goal.add_hline(y=TARGET_RECORDABLES_PER_YEAR, line_dash='dash', line_color='#6c757d', annotation_text='Meta 6', annotation_position='top left')
        st.plotly_chart(fig_goal, use_container_width=True)
        
        # Taxa de registráveis por 1M horas (opcional)
        st.caption("Taxa de registráveis por 1M horas (referência contextual)")
        fig_rate = px.line(
            display_df,
            x='year',
            y='recordable_rate',
            markers=True,
            title='Taxa de Registráveis por 1M de Horas (Anual)'
        )
        fig_rate.update_layout(
            height=360,
            xaxis_title='Ano',
            yaxis_title='Registráveis / 1.000.000 h',
            font=dict(size=12)
        )
        fig_rate.update_traces(line=dict(width=3), marker=dict(size=8))
        st.plotly_chart(fig_rate, use_container_width=True)
    else:
        st.info("🎯 **Meta de Registráveis**\n\nNenhum dado disponível para a análise anual da meta.")
    
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
