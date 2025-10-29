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
    generate_kpi_summary,
    calculate_forecast,
    generate_forecast_recommendations
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
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 KPIs Básicos", "📈 Controles Estatísticos", "📊 Monitoramento de Tendências", "🔮 Previsões", "📋 Relatórios"])
    
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
        try:
            patterns = detect_control_chart_patterns(
                control_df,
                "accidents_total",
                "ucl",
                "lcl"
            )
            
            # Alertas baseados em padrões
            st.subheader("🚨 Análise de Padrões")
            
            # Explicação da análise
            st.info("""
            **📊 O que é a Análise de Padrões?**
            
            Esta ferramenta detecta automaticamente padrões estatísticos nos dados de acidentes:
            
            - 🔴 **Pontos Fora de Controle**: Valores que excedem os limites estatísticos
            - 📈 **Tendência Ascendente**: 8 pontos consecutivos em alta (crítico)
            - 📉 **Tendência Descendente**: 8 pontos consecutivos em baixa (positivo)
            """)
            
            # Resumo dos padrões detectados
            col1, col2, col3 = st.columns(3)
            
            with col1:
                out_of_control_count = len(patterns['out_of_control'])
                if out_of_control_count > 0:
                    st.error(f"🔴 **{out_of_control_count} pontos fora de controle**")
                else:
                    st.success("✅ **Todos os pontos dentro dos limites**")
            
            with col2:
                trend_up_count = len(patterns['trend_up'])
                if trend_up_count > 0:
                    st.error(f"📈 **{trend_up_count} tendências ascendentes críticas**")
                else:
                    st.success("✅ **Nenhuma tendência ascendente crítica**")
            
            with col3:
                trend_down_count = len(patterns['trend_down'])
                if trend_down_count > 0:
                    st.success(f"📉 **{trend_down_count} tendências descendentes positivas**")
                else:
                    st.info("📊 **Nenhuma tendência descendente detectada**")
            
            # Detalhes dos padrões detectados
            if patterns['out_of_control'] or patterns['trend_up'] or patterns['trend_down']:
                st.subheader("📋 Detalhes dos Padrões Detectados")
                
                # Pontos fora de controle
                if patterns['out_of_control']:
                    st.warning(f"⚠️ **{len(patterns['out_of_control'])} Pontos Fora de Controle**")
                    
                    out_of_control_data = control_df.iloc[patterns['out_of_control']].copy()
                    out_of_control_data['Status'] = out_of_control_data.apply(
                        lambda row: "🔴 Acima do Limite" if row['accidents_total'] > row['ucl'] else "🟢 Abaixo do Limite",
                        axis=1
                    )
                    
                    display_cols = ['period', 'accidents_total', 'expected', 'ucl', 'lcl', 'Status']
                    problem_display = out_of_control_data[display_cols].copy()
                    problem_display.columns = ['Período', 'Acidentes', 'Esperado', 'Limite Superior', 'Limite Inferior', 'Status']
                    
                    st.dataframe(problem_display, use_container_width=True, hide_index=True)
                
                # Tendências ascendentes
                if patterns['trend_up']:
                    st.error(f"🚨 **{len(patterns['trend_up'])} Tendências Ascendentes Críticas**")
                    st.markdown("**Períodos com tendência ascendente:**")
                    trend_periods = [control_df.iloc[i]['period'] for i in patterns['trend_up']]
                    for period in trend_periods:
                        st.markdown(f"- {period}")
                
                # Tendências descendentes
                if patterns['trend_down']:
                    st.success(f"✅ **{len(patterns['trend_down'])} Tendências Descendentes Positivas**")
                    st.markdown("**Períodos com tendência descendente:**")
                    trend_periods = [control_df.iloc[i]['period'] for i in patterns['trend_down']]
                    for period in trend_periods:
                        st.markdown(f"- {period}")
            
            else:
                st.success("🎉 **Excelente!** Nenhum padrão problemático detectado nos dados.")
                st.info("📊 Os indicadores estão dentro dos limites estatísticos normais.")
            
            # Recomendações baseadas nos padrões
            st.subheader("💡 Recomendações")
            
            if patterns['out_of_control']:
                st.warning("""
                **🔴 Ação Imediata Necessária:**
                - Investigar causas dos pontos fora de controle
                - Revisar procedimentos de segurança
                - Implementar medidas corretivas urgentes
                """)
            
            if patterns['trend_up']:
                st.error("""
                **🚨 Tendência Crítica Detectada:**
                - Análise de causa raiz obrigatória
                - Revisão completa dos processos
                - Implementação de plano de ação emergencial
                """)
            
            if patterns['trend_down']:
                st.success("""
                **✅ Tendência Positiva:**
                - Manter práticas atuais
                - Documentar boas práticas
                - Compartilhar lições aprendidas
                """)
            
            if not any([patterns['out_of_control'], patterns['trend_up'], patterns['trend_down']]):
                st.info("""
                **📊 Situação Estável:**
                - Continuar monitoramento regular
                - Manter padrões atuais
                - Focar em melhorias contínuas
                """)
                
        except Exception as e:
            st.error(f"❌ **Erro na análise de padrões:** {str(e)}")
            st.info("Verifique se os dados estão no formato correto e tente novamente.")
    
    with tab3:
        st.subheader("📊 Monitoramento Avançado de Tendências")
        
        # Explicação do método
        st.info("""
        **📈 O que é o Monitoramento de Tendências?**
        
        Esta ferramenta utiliza a técnica **EWMA (Média Móvel Ponderada Exponencialmente)** para detectar 
        mudanças sutis nos indicadores de segurança ao longo do tempo. É especialmente útil para:
        
        - 🔍 **Detectar tendências** antes que se tornem problemas críticos
        - 📊 **Suavizar variações** aleatórias nos dados
        - ⚠️ **Alertar precocemente** sobre mudanças no desempenho
        - 📈 **Identificar melhorias** ou deterioração gradual
        """)
        
        # Configurações
        st.subheader("⚙️ Configurações da Análise")
        
        col1, col2 = st.columns(2)
        
        with col1:
            metric_choice = st.selectbox(
                "📊 Indicador para Monitoramento",
                options=["accidents_total", "freq_rate_per_million", "sev_rate_per_million"],
                format_func=lambda x: {
                    "accidents_total": "Total de Acidentes",
                    "freq_rate_per_million": "Taxa de Frequência",
                    "sev_rate_per_million": "Taxa de Gravidade"
                }[x],
                help="Selecione qual indicador você deseja monitorar"
            )
        
        with col2:
            lambda_param = st.slider(
                "🎛️ Sensibilidade da Detecção",
                min_value=0.1,
                max_value=0.5,
                value=0.2,
                step=0.05,
                help="Valores menores = mais suave (detecta mudanças graduais)\nValores maiores = mais sensível (detecta mudanças rápidas)"
            )
        
        # Calcula EWMA
        ewma_df = calculate_ewma(df, metric_choice, lambda_param)
        
        # Gráfico de monitoramento
        st.subheader("📈 Gráfico de Monitoramento")
        
        fig1 = go.Figure()
        
        # Valores observados (dados reais)
        fig1.add_trace(go.Scatter(
            x=ewma_df['period'],
            y=ewma_df[metric_choice],
            mode='lines+markers',
            name='📊 Dados Reais',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=6),
            opacity=0.7
        ))
        
        # Linha de tendência (EWMA)
        fig1.add_trace(go.Scatter(
            x=ewma_df['period'],
            y=ewma_df['ewma'],
            mode='lines',
            name='📈 Tendência Suavizada',
            line=dict(color='#ff6b35', width=4)
        ))
        
        # Limite superior de controle
        fig1.add_trace(go.Scatter(
            x=ewma_df['period'],
            y=ewma_df['ewma_ucl'],
            mode='lines',
            name='⚠️ Limite Superior',
            line=dict(color='#dc3545', width=2, dash='dash'),
            opacity=0.8
        ))
        
        # Limite inferior de controle
        fig1.add_trace(go.Scatter(
            x=ewma_df['period'],
            y=ewma_df['ewma_lcl'],
            mode='lines',
            name='✅ Limite Inferior',
            line=dict(color='#28a745', width=2, dash='dash'),
            opacity=0.8
        ))
        
        # Área entre os limites
        fig1.add_trace(go.Scatter(
            x=ewma_df['period'],
            y=ewma_df['ewma_ucl'],
            fill=None,
            mode='lines',
            line_color='rgba(0,0,0,0)',
            showlegend=False,
            hoverinfo="skip"
        ))
        
        fig1.add_trace(go.Scatter(
            x=ewma_df['period'],
            y=ewma_df['ewma_lcl'],
            fill='tonexty',
            mode='lines',
            line_color='rgba(0,0,0,0)',
            name='Zona de Controle',
            fillcolor='rgba(0,255,0,0.1)',
            hoverinfo="skip"
        ))
        
        # Título e labels mais claros
        metric_name = {
            "accidents_total": "Total de Acidentes",
            "freq_rate_per_million": "Taxa de Frequência",
            "sev_rate_per_million": "Taxa de Gravidade"
        }[metric_choice]
        
        fig1.update_layout(
            title=f'📊 Monitoramento de Tendências - {metric_name}',
            xaxis_title='Período',
            yaxis_title=metric_name,
            hovermode='x unified',
            template='plotly_white',
            height=500,
            font=dict(size=12)
        )
        
        st.plotly_chart(fig1, use_container_width=True)
        
        # Interpretação do gráfico
        st.subheader("🔍 Como Interpretar o Gráfico")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **📊 Dados Reais (azul)**
            - Valores observados em cada período
            - Podem ter variações aleatórias
            
            **📈 Tendência Suavizada (laranja)**
            - Mostra a direção geral do indicador
            - Ignora variações temporárias
            - Linha ascendente = piora, descendente = melhora
            """)
        
        with col2:
            st.markdown("""
            **⚠️ Limites de Controle**
            - Linha vermelha tracejada = limite superior
            - Linha verde tracejada = limite inferior
            - Zona verde = desempenho normal
            - Fora da zona = atenção necessária
            """)
        
        # Análise de alertas
        st.subheader("🚨 Análise de Alertas")
        
        # Identifica pontos fora dos limites
        ewma_out_of_control = (ewma_df[metric_choice] > ewma_df['ewma_ucl']) | (ewma_df[metric_choice] < ewma_df['ewma_lcl'])
        
        if ewma_out_of_control.any():
            st.warning(f"⚠️ **{ewma_out_of_control.sum()} períodos** com indicadores fora da zona de controle!")
            
            # Mostra pontos problemáticos de forma mais clara
            problem_points = ewma_df[ewma_out_of_control].copy()
            problem_points['Status'] = problem_points.apply(
                lambda row: "🔴 Acima do Limite" if row[metric_choice] > row['ewma_ucl'] else "🟢 Abaixo do Limite", 
                axis=1
            )
            
            # Cria DataFrame com colunas renomeadas
            problem_display = pd.DataFrame({
                'Período': problem_points['period'],
                'Valor Real': problem_points[metric_choice],
                'Tendência': problem_points['ewma'],
                'Limite Superior': problem_points['ewma_ucl'],
                'Limite Inferior': problem_points['ewma_lcl'],
                'Status': problem_points['Status']
            })
            
            st.dataframe(problem_display, use_container_width=True, hide_index=True)
        else:
            st.success("✅ **Excelente!** Todos os períodos estão dentro da zona de controle normal.")
        
        # Resumo da análise
        st.subheader("📊 Resumo da Análise")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "🎯 Valor Inicial", 
                f"{ewma_df['ewma'].iloc[0]:.1f}",
                help="Valor da tendência no primeiro período"
            )
        
        with col2:
            st.metric(
                "📈 Valor Atual", 
                f"{ewma_df['ewma'].iloc[-1]:.1f}",
                help="Valor atual da tendência"
            )
        
        with col3:
            variation = ewma_df['ewma'].iloc[-1] - ewma_df['ewma'].iloc[0]
            st.metric(
                "📊 Variação Total", 
                f"{variation:+.1f}",
                delta="Melhoria" if variation < 0 else "Deterioração" if variation > 0 else "Estável",
                help="Mudança total na tendência"
            )
        
        # Recomendações baseadas na análise
        st.subheader("💡 Recomendações")
        
        if variation > 0:
            st.warning("📈 **Tendência de Deterioração Detectada**\n\n- Revisar procedimentos de segurança\n- Investigar causas raiz\n- Implementar ações corretivas")
        elif variation < -0.1:
            st.success("📉 **Tendência de Melhoria Detectada**\n\n- Manter práticas atuais\n- Documentar boas práticas\n- Compartilhar lições aprendidas")
        else:
            st.info("📊 **Tendência Estável**\n\n- Continuar monitoramento\n- Manter padrões atuais\n- Focar em melhorias contínuas")
    
    with tab4:
        st.subheader("🔮 Previsões para o Próximo Mês")
        
        # Explicação da funcionalidade
        st.info("""
        **🔮 Como Funcionam as Previsões?**
        
        Esta ferramenta utiliza análise de tendências históricas para prever os indicadores do próximo mês:
        
        - 📈 **Análise Linear**: Identifica tendências nos dados históricos
        - 🎯 **Previsão Inteligente**: Considera padrões e sazonalidade
        - ⚠️ **Alertas Preventivos**: Avisa sobre riscos futuros
        - 💡 **Recomendações**: Sugere ações baseadas nas previsões
        """)
        
        # Calcula previsões
        if not df.empty and len(df) >= 3:
            forecasts = calculate_forecast(df)
            
            if forecasts:
                # Resumo das previsões
                st.subheader("📊 Previsões do Próximo Mês")
                
                col1, col2, col3, col4 = st.columns(4)
                
                # Taxa de Frequência
                if 'frequency_rate' in forecasts:
                    freq_data = forecasts['frequency_rate']
                    with col1:
                        trend_icon = "📈" if freq_data['trend'] == 'increasing' else "📉" if freq_data['trend'] == 'decreasing' else "➡️"
                        confidence_pct = int(freq_data['confidence'] * 100)
                        st.metric(
                            "Taxa de Frequência Prevista",
                            f"{freq_data['predicted']:.0f}",
                            help=f"Tendência: {freq_data['trend']}\nConfiança: {confidence_pct}%"
                        )
                        st.caption(f"{trend_icon} {freq_data['trend'].title()}")
                
                # Taxa de Gravidade
                if 'severity_rate' in forecasts:
                    sev_data = forecasts['severity_rate']
                    with col2:
                        trend_icon = "📈" if sev_data['trend'] == 'increasing' else "📉" if sev_data['trend'] == 'decreasing' else "➡️"
                        confidence_pct = int(sev_data['confidence'] * 100)
                        st.metric(
                            "Taxa de Gravidade Prevista",
                            f"{sev_data['predicted']:.0f}",
                            help=f"Tendência: {sev_data['trend']}\nConfiança: {confidence_pct}%"
                        )
                        st.caption(f"{trend_icon} {sev_data['trend'].title()}")
                
                # Total de Acidentes
                if 'total_accidents' in forecasts:
                    acc_data = forecasts['total_accidents']
                    with col3:
                        trend_icon = "📈" if acc_data['trend'] == 'increasing' else "📉" if acc_data['trend'] == 'decreasing' else "➡️"
                        confidence_pct = int(acc_data['confidence'] * 100)
                        st.metric(
                            "Acidentes Previstos",
                            f"{acc_data['predicted']:.0f}",
                            help=f"Tendência: {acc_data['trend']}\nConfiança: {confidence_pct}%"
                        )
                        st.caption(f"{trend_icon} {acc_data['trend'].title()}")
                
                # Dias Perdidos
                if 'lost_days' in forecasts:
                    days_data = forecasts['lost_days']
                    with col4:
                        trend_icon = "📈" if days_data['trend'] == 'increasing' else "📉" if days_data['trend'] == 'decreasing' else "➡️"
                        confidence_pct = int(days_data['confidence'] * 100)
                        st.metric(
                            "Dias Perdidos Previstos",
                            f"{days_data['predicted']:.0f}",
                            help=f"Tendência: {days_data['trend']}\nConfiança: {confidence_pct}%"
                        )
                        st.caption(f"{trend_icon} {days_data['trend'].title()}")
                
                # Gráfico de previsão
                st.subheader("📈 Gráfico de Previsão")
                
                # Prepara dados para o gráfico
                df_with_forecast = df.copy()
                df_with_forecast['freq_rate'] = (df_with_forecast['accidents_total'] / df_with_forecast['hours']) * 1_000_000
                df_with_forecast['sev_rate'] = (df_with_forecast['lost_days_total'] / df_with_forecast['hours']) * 1_000_000
                
                # Adiciona ponto de previsão
                if 'frequency_rate' in forecasts and 'severity_rate' in forecasts:
                    # Calcula próximo período
                    last_period = pd.to_datetime(df_with_forecast['period'].max())
                    next_period = last_period + pd.DateOffset(months=1)
                    
                    # Cria DataFrame com previsão
                    forecast_row = pd.DataFrame({
                        'period': [next_period.strftime('%Y-%m-%d')],
                        'freq_rate': [forecasts['frequency_rate']['predicted']],
                        'sev_rate': [forecasts['severity_rate']['predicted']],
                        'accidents_total': [forecasts.get('total_accidents', {}).get('predicted', 0)],
                        'lost_days_total': [forecasts.get('lost_days', {}).get('predicted', 0)],
                        'is_forecast': [True]
                    })
                    
                    df_with_forecast['is_forecast'] = False
                    df_combined = pd.concat([df_with_forecast, forecast_row], ignore_index=True)
                    
                    # Gráfico de previsão
                    fig = go.Figure()
                    
                    # Dados históricos
                    historical_data = df_combined[df_combined['is_forecast'] == False]
                    fig.add_trace(go.Scatter(
                        x=historical_data['period'],
                        y=historical_data['freq_rate'],
                        mode='lines+markers',
                        name='📊 Taxa de Frequência (Histórico)',
                        line=dict(color='#1f77b4', width=3),
                        marker=dict(size=6)
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=historical_data['period'],
                        y=historical_data['sev_rate'],
                        mode='lines+markers',
                        name='📊 Taxa de Gravidade (Histórico)',
                        line=dict(color='#ff7f0e', width=3),
                        marker=dict(size=6),
                        yaxis='y2'
                    ))
                    
                    # Previsões
                    forecast_data = df_combined[df_combined['is_forecast'] == True]
                    if not forecast_data.empty:
                        fig.add_trace(go.Scatter(
                            x=forecast_data['period'],
                            y=forecast_data['freq_rate'],
                            mode='markers',
                            name='🔮 Taxa de Frequência (Previsão)',
                            marker=dict(color='#1f77b4', size=12, symbol='diamond'),
                            showlegend=True
                        ))
                        
                        fig.add_trace(go.Scatter(
                            x=forecast_data['period'],
                            y=forecast_data['sev_rate'],
                            mode='markers',
                            name='🔮 Taxa de Gravidade (Previsão)',
                            marker=dict(color='#ff7f0e', size=12, symbol='diamond'),
                            yaxis='y2',
                            showlegend=True
                        ))
                    
                    # Layout do gráfico
                    fig.update_layout(
                        title="📈 Previsões vs Histórico",
                        xaxis_title="Período",
                        yaxis=dict(title="Taxa de Frequência", side="left"),
                        yaxis2=dict(title="Taxa de Gravidade", side="right", overlaying="y"),
                        height=500,
                        template="plotly_white",
                        font=dict(size=12)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # Recomendações baseadas nas previsões
                st.subheader("💡 Recomendações Baseadas nas Previsões")
                
                recommendations = generate_forecast_recommendations(forecasts)
                
                if recommendations:
                    for i, rec in enumerate(recommendations, 1):
                        st.markdown(f"{i}. {rec}")
                else:
                    st.info("📊 **Situação Estável:** As previsões indicam continuidade do desempenho atual.")
                
                # Detalhes técnicos
                with st.expander("🔧 Detalhes Técnicos da Previsão"):
                    st.markdown("""
                    **Método Utilizado:**
                    - Análise de regressão linear simples
                    - Baseado nos últimos 3+ meses de dados
                    - Considera tendências e sazonalidade básica
                    
                    **Limitações:**
                    - Previsões são estimativas baseadas em padrões históricos
                    - Não considera eventos externos imprevistos
                    - Confiança diminui com maior variabilidade dos dados
                    
                    **Interpretação:**
                    - **Confiança Alta (80%+)**: Padrão histórico estável
                    - **Confiança Média (50-80%)**: Alguma variabilidade nos dados
                    - **Confiança Baixa (<50%)**: Dados muito variáveis para previsão confiável
                    """)
            
            else:
                st.warning("⚠️ **Dados Insuficientes:** São necessários pelo menos 3 meses de dados para gerar previsões confiáveis.")
        
        else:
            st.warning("⚠️ **Dados Insuficientes:** São necessários pelo menos 3 meses de dados para gerar previsões.")
    
    with tab5:
        st.subheader("Relatórios de KPIs")
        
        # Seleção de período para relatório
        col1, col2 = st.columns(2)
        
        with col1:
            min_date = pd.to_datetime(df['period'].min()).date()
            report_start = st.date_input("Data Inicial do Relatório", value=min_date)
        
        with col2:
            max_date = pd.to_datetime(df['period'].max()).date()
            report_end = st.date_input("Data Final do Relatório", value=max_date)
        
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
                try:
                    # Cria DataFrame para exportação
                    export_data = pd.DataFrame()
                    for col in available_cols:
                        if col in report_df.columns:
                            export_data[col] = report_df[col]
                    
                    csv_data = export_data.to_csv(index=False)
                    st.download_button(
                        "💾 Baixar CSV",
                        csv_data,
                        f"relatorio_kpi_{report_start}_{report_end}.csv",
                        "text/csv"
                    )
                except Exception as e:
                    st.error(f"Erro ao exportar CSV: {str(e)}")
        else:
            st.info("Nenhum dado encontrado para o período selecionado.")

if __name__ == "__main__":
    app({})
