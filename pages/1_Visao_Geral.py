import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from services.kpi import fetch_kpi_data, generate_kpi_summary, calculate_poisson_control_limits
from components.cards import create_dashboard_summary, create_metric_row, create_trend_chart, create_control_chart
from components.filters import apply_filters_to_df

def app(filters):
    st.title("📊 Visão Geral - SSO")
    
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
    
    # Resumo executivo
    create_dashboard_summary(kpi_summary)
    
    st.markdown("---")
    
    # Gráficos principais
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de distribuição por mês
        fig1 = px.bar(
            df, 
            x="period", 
            y=["accidents_total", "fatalities", "with_injury", "without_injury"],
            barmode="group", 
            title="Distribuição de Acidentes por Mês",
            labels={"value": "Quantidade", "variable": "Tipo"}
        )
        fig1.update_layout(height=400)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Gráfico de taxa de frequência
        if 'freq_rate_per_million' in df.columns:
            fig2 = create_trend_chart(
                df, 
                "period", 
                "freq_rate_per_million",
                "Taxa de Frequência (por 1M de horas)"
            )
        else:
            # Calcula taxa de frequência se não existir
            df['freq_rate'] = (df['accidents_total'] / df['hours']) * 1_000_000
            fig2 = create_trend_chart(
                df, 
                "period", 
                "freq_rate",
                "Taxa de Frequência (por 1M de horas)"
            )
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)
    
    # Gráficos de controle estatístico
    st.subheader("📈 Controles Estatísticos")
    
    # Prepara dados para controle
    control_df = calculate_poisson_control_limits(df)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de controle para acidentes
        fig3 = create_control_chart(
            control_df,
            "period",
            "accidents_total", 
            "ucl",
            "lcl",
            "expected",
            "Controle de Acidentes (Poisson)"
        )
        st.plotly_chart(fig3, use_container_width=True)
    
    with col2:
        # Gráfico de taxa de gravidade
        if 'sev_rate_per_million' in df.columns:
            sev_col = 'sev_rate_per_million'
        else:
            df['sev_rate'] = (df['lost_days_total'] / df['hours']) * 1_000_000
            sev_col = 'sev_rate'
        
        fig4 = create_trend_chart(
            df,
            "period",
            sev_col,
            "Taxa de Gravidade (por 1M de horas)"
        )
        st.plotly_chart(fig4, use_container_width=True)
    
    # Análise por período
    st.subheader("📅 Análise por Período")
    
    if not df.empty:
        period_analysis = df.groupby('period').agg({
            'accidents_total': 'sum',
            'fatalities': 'sum',
            'with_injury': 'sum',
            'without_injury': 'sum',
            'lost_days_total': 'sum',
            'hours': 'sum'
        }).reset_index()
        
        # Calcula taxas por período
        period_analysis['freq_rate'] = (period_analysis['accidents_total'] / period_analysis['hours']) * 1_000_000
        period_analysis['sev_rate'] = (period_analysis['lost_days_total'] / period_analysis['hours']) * 1_000_000
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Taxa de frequência por período
            fig5 = px.bar(
                period_analysis,
                x='period',
                y='freq_rate',
                title='Taxa de Frequência por Período',
                labels={'freq_rate': 'Taxa de Frequência', 'period': 'Período'}
            )
            st.plotly_chart(fig5, use_container_width=True)
        
        with col2:
            # Taxa de gravidade por período
            fig6 = px.bar(
                period_analysis,
                x='period', 
                y='sev_rate',
                title='Taxa de Gravidade por Período',
                labels={'sev_rate': 'Taxa de Gravidade', 'period': 'Período'}
            )
            st.plotly_chart(fig6, use_container_width=True)
    
    # Tabela de dados
    st.subheader("📋 Dados Detalhados")
    
    # Seleciona colunas para exibição
    display_cols = ['period', 'accidents_total', 'fatalities', 
                   'with_injury', 'without_injury', 'lost_days_total', 'hours',
                   'freq_rate_per_million', 'severity_rate_per_million']
    
    available_cols = [col for col in display_cols if col in df.columns]
    
    if available_cols:
        st.dataframe(
            df[available_cols],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Alertas e recomendações
    st.subheader("🚨 Alertas e Recomendações")
    
    # Verifica padrões de controle
    if 'out_of_control' in control_df.columns:
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

if __name__ == "__main__":
    app({})
