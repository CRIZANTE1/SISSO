import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from services.kpi import (
    fetch_kpi_data, 
    calculate_frequency_rate, 
    calculate_severity_rate,
    calculate_poisson_control_limits,
    calculate_ewma,
    detect_control_chart_patterns,
    generate_kpi_summary
)
from components.cards import create_control_chart, create_trend_chart, create_metric_row
from components.filters import apply_filters_to_df

def app(filters=None):
    st.title("📈 KPIs e Controles Estatísticos")
    
    # Busca filtros do session state se não foram passados como parâmetro
    if filters is None:
        filters = st.session_state.get('filters', {})
    
    # Busca dados
    with st.spinner("Carregando dados de KPIs..."):
        from auth.auth_utils import get_user_email
        user_email = get_user_email()
        
        df = fetch_kpi_data(
            user_email=user_email,
            start_date=filters.get("start_date"),
            end_date=filters.get("end_date")
        )
    
    if df.empty:
        st.warning("Nenhum dado de KPI encontrado com os filtros aplicados.")
        return
    
    # Aplica filtros adicionais
    df = apply_filters_to_df(df, filters)
    
    # Tabs para diferentes análises
    tab1, tab2, tab3, tab4 = st.tabs(["📊 KPIs Básicos", "📈 Controles Estatísticos", "🔍 Método M", "📋 Relatórios"])
    
    with tab1:
        st.subheader("KPIs Básicos de Segurança")
        
        # Calcula KPIs se não existirem
        if 'freq_rate_per_million' not in df.columns:
            df['freq_rate_per_million'] = (df['accidents_total'] / df['hours']) * 1_000_000
        
        if 'sev_rate_per_million' not in df.columns:
            df['sev_rate_per_million'] = (df['lost_days_total'] / df['hours']) * 1_000_000
        
        # Resumo dos KPIs
        kpi_summary = generate_kpi_summary(df)
        
        # Métricas principais
        metrics = [
            {
                "title": "Taxa de Frequência",
                "value": f"{kpi_summary.get('frequency_rate', 0):.2f}",
                "change": kpi_summary.get('frequency_change'),
                "change_label": "vs período anterior",
                "icon": "📈",
                "color": "danger" if kpi_summary.get('frequency_change', 0) > 0 else "success"
            },
            {
                "title": "Taxa de Gravidade",
                "value": f"{kpi_summary.get('severity_rate', 0):.2f}",
                "change": kpi_summary.get('severity_change'),
                "change_label": "vs período anterior",
                "icon": "⚠️",
                "color": "danger" if kpi_summary.get('severity_change', 0) > 0 else "success"
            },
            {
                "title": "Total de Acidentes",
                "value": kpi_summary.get('total_accidents', 0),
                "icon": "🚨",
                "color": "normal"
            },
            {
                "title": "Dias Perdidos",
                "value": kpi_summary.get('total_lost_days', 0),
                "icon": "📅",
                "color": "warning"
            }
        ]
        
        create_metric_row(metrics)
        
        # Gráficos de tendência
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = create_trend_chart(
                df,
                "period",
                "freq_rate_per_million",
                "Evolução da Taxa de Frequência"
            )
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            fig2 = create_trend_chart(
                df,
                "period", 
                "sev_rate_per_million",
                "Evolução da Taxa de Gravidade"
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        # Análise por site
        if 'site_code' in df.columns:
            st.subheader("KPIs por Site")
            
            site_analysis = df.groupby('site_code').agg({
                'accidents_total': 'sum',
                'lost_days_total': 'sum',
                'hours': 'sum'
            }).reset_index()
            
            site_analysis['freq_rate'] = (site_analysis['accidents_total'] / site_analysis['hours']) * 1_000_000
            site_analysis['sev_rate'] = (site_analysis['lost_days_total'] / site_analysis['hours']) * 1_000_000
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig3 = px.bar(
                    site_analysis,
                    x='site_code',
                    y='freq_rate',
                    title='Taxa de Frequência por Site',
                    labels={'freq_rate': 'Taxa de Frequência', 'site_code': 'Site'}
                )
                st.plotly_chart(fig3, use_container_width=True)
            
            with col2:
                fig4 = px.bar(
                    site_analysis,
                    x='site_code',
                    y='sev_rate',
                    title='Taxa de Gravidade por Site',
                    labels={'sev_rate': 'Taxa de Gravidade', 'site_code': 'Site'}
                )
                st.plotly_chart(fig4, use_container_width=True)
    
    with tab2:
        st.subheader("Controles Estatísticos")
        
        # Calcula limites de controle Poisson
        control_df = calculate_poisson_control_limits(df)
        
        # Gráfico de controle para acidentes
        fig1 = create_control_chart(
            control_df,
            "period",
            "accidents_total",
            "ucl",
            "lcl", 
            "expected",
            "Controle de Acidentes (Limites Poisson)"
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        # Análise de padrões
        patterns = detect_control_chart_patterns(
            control_df,
            "accidents_total",
            "ucl",
            "lcl"
        )
        
        # Alertas baseados em padrões
        st.subheader("🚨 Análise de Padrões")
        
        if patterns['out_of_control']:
            st.warning(f"⚠️ **{len(patterns['out_of_control'])} pontos fora de controle** detectados!")
        
        if patterns['trend_up']:
            st.error(f"🚨 **Tendência ascendente crítica** detectada em {len(patterns['trend_up'])} pontos!")
        
        if patterns['trend_down']:
            st.success(f"✅ **Tendência descendente positiva** detectada em {len(patterns['trend_down'])} pontos!")
        
        # Tabela de pontos fora de controle
        if patterns['out_of_control']:
            st.subheader("Pontos Fora de Controle")
            out_of_control_data = control_df.iloc[patterns['out_of_control']][
                ['period', 'accidents_total', 'expected', 'ucl', 'lcl']
            ]
            st.dataframe(out_of_control_data, use_container_width=True)
    
    with tab3:
        st.subheader("Método M - Monitoramento de Indicadores")
        
        # Parâmetros do EWMA
        col1, col2 = st.columns(2)
        
        with col1:
            lambda_param = st.slider(
                "Parâmetro λ (Lambda) para EWMA",
                min_value=0.1,
                max_value=0.5,
                value=0.2,
                step=0.05,
                help="Valores menores suavizam mais a série temporal"
            )
        
        with col2:
            metric_choice = st.selectbox(
                "Métrica para Análise EWMA",
                options=["accidents_total", "freq_rate_per_million", "sev_rate_per_million"],
                format_func=lambda x: {
                    "accidents_total": "Total de Acidentes",
                    "freq_rate_per_million": "Taxa de Frequência",
                    "sev_rate_per_million": "Taxa de Gravidade"
                }[x]
            )
        
        # Calcula EWMA
        ewma_df = calculate_ewma(df, metric_choice, lambda_param)
        
        # Gráfico EWMA
        fig1 = go.Figure()
        
        # Valores observados
        fig1.add_trace(go.Scatter(
            x=ewma_df['period'],
            y=ewma_df[metric_choice],
            mode='lines+markers',
            name='Valores Observados',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=6)
        ))
        
        # EWMA
        fig1.add_trace(go.Scatter(
            x=ewma_df['period'],
            y=ewma_df['ewma'],
            mode='lines',
            name='EWMA',
            line=dict(color='red', width=3)
        ))
        
        # Limites de controle EWMA
        fig1.add_trace(go.Scatter(
            x=ewma_df['period'],
            y=ewma_df['ewma_ucl'],
            mode='lines',
            name='UCL EWMA',
            line=dict(color='red', width=2, dash='dash')
        ))
        
        fig1.add_trace(go.Scatter(
            x=ewma_df['period'],
            y=ewma_df['ewma_lcl'],
            mode='lines',
            name='LCL EWMA',
            line=dict(color='red', width=2, dash='dash')
        ))
        
        fig1.update_layout(
            title=f'Análise EWMA - {metric_choice}',
            xaxis_title='Período',
            yaxis_title=metric_choice,
            hovermode='x unified',
            template='plotly_white'
        )
        
        st.plotly_chart(fig1, use_container_width=True)
        
        # Análise de sinais EWMA
        st.subheader("Análise de Sinais EWMA")
        
        # Identifica pontos fora dos limites EWMA
        ewma_out_of_control = (ewma_df[metric_choice] > ewma_df['ewma_ucl']) | (ewma_df[metric_choice] < ewma_df['ewma_lcl'])
        
        if ewma_out_of_control.any():
            st.warning(f"⚠️ **{ewma_out_of_control.sum()} pontos** fora dos limites de controle EWMA!")
            
            # Mostra pontos problemáticos
            problem_points = ewma_df[ewma_out_of_control][['period', metric_choice, 'ewma', 'ewma_ucl', 'ewma_lcl']]
            st.dataframe(problem_points, use_container_width=True)
        else:
            st.success("✅ Todos os pontos estão dentro dos limites de controle EWMA!")
        
        # Estatísticas do EWMA
        st.subheader("Estatísticas do EWMA")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Valor Inicial EWMA", f"{ewma_df['ewma'].iloc[0]:.2f}")
        
        with col2:
            st.metric("Valor Final EWMA", f"{ewma_df['ewma'].iloc[-1]:.2f}")
        
        with col3:
            st.metric("Variação EWMA", f"{ewma_df['ewma'].iloc[-1] - ewma_df['ewma'].iloc[0]:.2f}")
    
    with tab4:
        st.subheader("Relatórios de KPIs")
        
        # Seleção de período para relatório
        col1, col2 = st.columns(2)
        
        with col1:
            report_start = st.date_input("Data Inicial do Relatório", value=df['period'].min())
        
        with col2:
            report_end = st.date_input("Data Final do Relatório", value=df['period'].max())
        
        # Filtra dados para o relatório
        report_df = df[(df['period'] >= str(report_start)) & (df['period'] <= str(report_end))]
        
        if not report_df.empty:
            # Resumo executivo
            st.subheader("📊 Resumo Executivo")
            
            total_accidents = report_df['accidents_total'].sum()
            total_hours = report_df['hours'].sum()
            total_lost_days = report_df['lost_days_total'].sum()
            
            overall_freq_rate = (total_accidents / total_hours) * 1_000_000 if total_hours > 0 else 0
            overall_sev_rate = (total_lost_days / total_hours) * 1_000_000 if total_hours > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Taxa de Frequência Geral", f"{overall_freq_rate:.2f}")
            
            with col2:
                st.metric("Taxa de Gravidade Geral", f"{overall_sev_rate:.2f}")
            
            with col3:
                st.metric("Total de Acidentes", total_accidents)
            
            with col4:
                st.metric("Total de Horas", f"{total_hours:,.0f}")
            
            # Tabela detalhada por período
            st.subheader("📋 Dados Detalhados por Período")
            
            display_cols = ['period', 'site_code', 'accidents_total', 'fatalities', 
                           'with_injury', 'without_injury', 'lost_days_total', 'hours',
                           'freq_rate_per_million', 'sev_rate_per_million']
            
            available_cols = [col for col in display_cols if col in report_df.columns]
            
            st.dataframe(
                report_df[available_cols],
                use_container_width=True,
                hide_index=True
            )
            
            # Botão para exportar
            if st.button("📥 Exportar Relatório CSV"):
                csv = report_df[available_cols].to_csv(index=False)
                st.download_button(
                    "💾 Baixar CSV",
                    csv,
                    f"relatorio_kpi_{report_start}_{report_end}.csv",
                    "text/csv"
                )
        else:
            st.info("Nenhum dado encontrado para o período selecionado.")

if __name__ == "__main__":
    app({})
