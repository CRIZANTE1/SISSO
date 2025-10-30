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
    # Verifica autenticação e trial
    from auth.auth_utils import require_login
    require_login()
    
    st.title("📈 KPIs e Controles Estatísticos")
    # Ajuda da página (popover)
    hl, hr = st.columns([6, 1])
    with hr:
        with st.popover("❓ Ajuda"):
            st.markdown(
                "**Fluxo recomendado**\n\n"
                "1) KPIs Básicos: visão geral e interpretações.\n"
                "2) Controles Estatísticos: limites e padrões.\n"
                "3) Tendências (EWMA) e Previsões.\n"
                "4) Relatórios e Exportação."
            )
    
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
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(["📊 KPIs Básicos", "📈 Controles Estatísticos", "📊 Monitoramento de Tendências", "🔮 Previsões", "📋 Relatórios", "📚 Metodologia", "🔧 Configurações", "📖 Instruções"])
    
    with tab1:
        st.subheader("KPIs Básicos de Segurança")
        
        # Calcula KPIs se não existirem
        if 'freq_rate_per_million' not in df.columns:
            df['freq_rate_per_million'] = (df['accidents_total'] / df['hours']) * 1_000_000
        
        if 'sev_rate_per_million' not in df.columns:
            df['sev_rate_per_million'] = (df['lost_days_total'] / df['hours']) * 1_000_000
        
        # Resumo dos KPIs
        kpi_summary = generate_kpi_summary(df)
        
        # Seção de análises de KPIs
        # Métricas principais com interpretações
        freq_interpretation = kpi_summary.get('frequency_interpretation', {})
        sev_interpretation = kpi_summary.get('severity_interpretation', {})
        
        metrics = [
            {
                "title": "Taxa de Frequência (TF)",
                "value": f"{kpi_summary.get('frequency_rate', 0):.2f}",
                "change": kpi_summary.get('frequency_change'),
                "change_label": "vs período anterior",
                "icon": freq_interpretation.get('icon', '📈'),
                "color": freq_interpretation.get('color', 'normal'),
                "subtitle": freq_interpretation.get('classification', 'N/A')
            },
            {
                "title": "Taxa de Gravidade (TG)",
                "value": f"{kpi_summary.get('severity_rate', 0):.2f}",
                "change": kpi_summary.get('severity_change'),
                "change_label": "vs período anterior",
                "icon": sev_interpretation.get('icon', '⚠️'),
                "color": sev_interpretation.get('color', 'normal'),
                "subtitle": sev_interpretation.get('classification', 'N/A')
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
        
        # ✅ NOVO: Mostrar métricas de conformidade ISO 45001
        iso_metrics = kpi_summary.get('iso_compliance_metrics', {})
        if iso_metrics:
            with st.expander("📊 Conformidade ISO 45001:2018", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    cont_improve = iso_metrics.get('continuous_improvement', {})
                    if cont_improve:
                        is_improving = cont_improve.get('is_improving', False)
                        st.metric(
                            "Melhoria Contínua",
                            "✅ Em Progresso" if is_improving else "⚠️ Necessária",
                            delta="Tendência de KPIs" if is_improving else "Ações requeridas"
                        )
                
                with col2:
                    monitoring = iso_metrics.get('monitoring_compliance', {})
                    if monitoring:
                        quality_score = monitoring.get('data_quality_score', 0)
                        st.metric(
                            "Qualidade dos Dados",
                            f"{quality_score:.0f}%",
                            delta="Conformidade com cláusula 9.1"
                        )
        
        # ✅ NOVO: Mostrar análise de tendências NBR 14280
        trend_analysis = kpi_summary.get('accident_trend_analysis', {})
        if trend_analysis:
            with st.expander("📈 Análise de Tendências - NBR 14280", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    long_trend = trend_analysis.get('long_term_trend', {})
                    if long_trend:
                        change_pct = long_trend.get('change_percentage', 0)
                        direction = long_trend.get('direction', 'stable')
                        st.metric(
                            "Tendência de Longo Prazo",
                            direction.title(),
                            delta=f"{change_pct:+.1f}%"
                        )
                
                with col2:
                    short_trend = trend_analysis.get('short_term_trend', {})
                    if short_trend:
                        change_pct = short_trend.get('change_percentage', 0)
                        direction = short_trend.get('direction', 'stable')
                        st.metric(
                            "Tendência de Curto Prazo",
                            direction.title(),
                            delta=f"{change_pct:+.1f}%"
                        )
        
        # ✅ NOVO: Relatório de conformidade ISO 45001
        with st.expander("📋 Relatório de Conformidade - ISO 45001:2018", expanded=False):
            from services.kpi import generate_iso_45001_compliance_report
            iso_compliance_report = generate_iso_45001_compliance_report(kpi_summary)
            
            for line in iso_compliance_report:
                st.write(line)
        
        # Gráficos de tendência
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = create_trend_chart(
                df,
                "period",
                "freq_rate_per_million",
                "Evolução da Taxa de Frequência"
            )
            st.plotly_chart(fig1, width='stretch')
        
        with col2:
            fig2 = create_trend_chart(
                df,
                "period", 
                "sev_rate_per_million",
                "Evolução da Taxa de Gravidade"
            )
            st.plotly_chart(fig2, width='stretch')
        
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
                st.plotly_chart(fig3, width='stretch')
            
            with col2:
                fig4 = px.bar(
                    site_analysis,
                    x='site_code',
                    y='sev_rate',
                    title='Taxa de Gravidade por Site',
                    labels={'sev_rate': 'Taxa de Gravidade', 'site_code': 'Site'}
                )
                st.plotly_chart(fig4, width='stretch')
    
    with tab2:
        st.subheader("📈 Controles Estatísticos")
        
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
        st.plotly_chart(fig1, width='stretch')
        
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
                    
                    st.dataframe(problem_display, width='stretch', hide_index=True)
                
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
        
        st.plotly_chart(fig1, width='stretch')
        
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
            
            st.dataframe(problem_display, width='stretch', hide_index=True)
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
                    
                    st.plotly_chart(fig, width='stretch')
                
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
            # Horas gravadas em centenas: converter para horas reais
            total_hours = report_df['hours'].sum() * 100
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
                width='stretch',
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
    
    with tab6:
        st.subheader("📚 Metodologia dos KPIs e Controles Estatísticos")
        
        st.markdown("""
        ## 🎯 Objetivo dos KPIs
        
        Os KPIs (Key Performance Indicators) de segurança são métricas quantitativas que permitem:
        - **Medir** o desempenho em segurança
        - **Comparar** períodos e metas
        - **Identificar** tendências e padrões
        - **Tomar decisões** baseadas em dados
        - **Comunicar** resultados de forma clara
        """)
        
        st.markdown("""
        ## 📊 Indicadores Principais
        
        ### 1. Taxa de Frequência (TF)
        - **Fórmula**: `(N° de acidentes × 1.000.000) ÷ hora-homem trabalhada`
        - **Unidade**: Acidentes por 1 milhão de horas trabalhadas
        - **Conceito**: Indica a quantidade de acidentes ocorridos numa empresa em função da exposição ao risco
        - **Interpretação conforme NBR 14280**:
          - **≤ 20**: Muito bom
          - **20,1-40**: Bom
          - **40,1-60**: Ruim
          - **> 60**: Péssimo
        - **Uso**: Mede a "repetição" ou "ocorrência" de acidentes
        
        ### 2. Taxa de Gravidade (TG)
        - **Fórmula**: `((dias perdidos + dias debitados) × 1.000.000) ÷ hora-homem trabalhada`
        - **Unidade**: Dias perdidos por 1 milhão de horas trabalhadas
        - **Conceito**: Mede o "impacto" ou "severidade" dos acidentes em termos de tempo de trabalho perdido
        - **Dias Debitados**: Para casos graves conforme NBR 14280:
          - Morte = 6.000 dias
          - Amputação de mão = 3.000 dias
          - Amputação de pé = 2.400 dias
        - **Interpretação**:
          - **≤ 50**: Excelente
          - **50-100**: Aceitável
          - **100-200**: Elevado
          - **> 200**: Crítico
        - **Uso**: Mede o impacto econômico e social dos acidentes
        
        ### Diferença entre TF e TG
        
        **Taxa de Frequência (TF)**:
        - Mede a **quantidade** de acidentes num dado volume de horas de trabalho
        - Responde: "Quantos acidentes acontecem para cada horário-homem de risco?"
        - Foca na **repetição** ou **ocorrência** de acidentes
        
        **Taxa de Gravidade (TG)**:
        - Mede a **severidade/impacto** desses acidentes em termos de dias de afastamento/débito
        - Responde: "Quão graves foram os acidentes em termos de tempo perdido?"
        - Foca no **impacto** dos acidentes
        
        **Resumo**: TF = quantos acidentes; TG = quão graves eles foram.
        
        ### 3. Total de Acidentes
        - **Definição**: Soma de todos os acidentes no período
        - **Categorias**: Fatais, Com Lesão, Sem Lesão
        - **Uso**: Contagem absoluta de eventos
        
        ### 4. Dias Perdidos
        - **Definição**: Total de dias de trabalho perdidos
        - **Uso**: Medida de impacto econômico e social
        """)
        
        st.markdown("""
        ## 📈 Controles Estatísticos
        
        ### Cartas de Controle de Poisson
        - **Método**: Controle estatístico para eventos raros
        - **Aplicação**: Acidentes são eventos raros e independentes
        - **Limites**:
          - **LSC**: Limite Superior de Controle
          - **LIC**: Limite Inferior de Controle
          - **LM**: Linha Média (média histórica)
        
        ### Interpretação dos Limites
        - **Dentro dos Limites**: Processo sob controle
        - **Fora dos Limites**: Processo fora de controle
        - **Tendências**: Padrões que indicam mudanças no processo
        
        ### Vantagens
        - Detecta mudanças sutis no processo
        - Distingue entre variação comum e especial
        - Permite ação preventiva antes de problemas graves
        """)
        
        st.markdown("""
        ## 📊 Monitoramento de Tendências (EWMA)
        
        ### Exponentially Weighted Moving Average
        - **Método**: Média móvel exponencialmente ponderada
        - **Parâmetro λ (Lambda)**: Controla a sensibilidade (0.1 a 0.3)
        - **Vantagens**:
          - Detecta mudanças graduais
          - Menos sensível a variações aleatórias
          - Ideal para processos com autocorrelação
        
        ### Interpretação
        - **Valor EWMA > LSC**: Tendência de piora
        - **Valor EWMA < LIC**: Tendência de melhoria
        - **Valor EWMA ≈ LM**: Processo estável
        
        ### Parâmetros Recomendados
        - **λ = 0.1**: Alta sensibilidade, detecta mudanças pequenas
        - **λ = 0.2**: Sensibilidade média, equilíbrio
        - **λ = 0.3**: Baixa sensibilidade, detecta mudanças grandes
        """)
        
        st.markdown("""
        ## 🔍 Análise de Padrões
        
        ### Padrões Detectados
        1. **Pontos Fora de Controle**: Valores que excedem os limites
        2. **Tendências Ascendentes**: Sequência de valores crescentes
        3. **Tendências Descendentes**: Sequência de valores decrescentes
        4. **Ciclos**: Padrões repetitivos ao longo do tempo
        
        ### Interpretação dos Padrões
        - **Pontos Fora de Controle**: Investigação imediata necessária
        - **Tendências**: Mudanças sistemáticas no processo
        - **Ciclos**: Sazonalidade ou fatores externos
        
        ### Ações Recomendadas
        - **Investigar**: Causas raiz dos padrões
        - **Implementar**: Medidas corretivas
        - **Monitorar**: Efetividade das ações
        - **Documentar**: Lições aprendidas
        """)
        
        st.markdown("""
        ## 🔮 Previsões
        
        ### Método de Previsão
        - **Análise de Tendência**: Baseada em médias móveis
        - **Período Mínimo**: 3 meses de dados históricos
        - **Base**: Horas trabalhadas
        - **Confiança**: Baseada na estabilidade dos dados
        
        ### Limitações
        - **Eventos Externos**: Não considera fatores imprevistos
        - **Mudanças Estruturais**: Pode não capturar mudanças bruscas
        - **Qualidade dos Dados**: Depende da precisão dos registros
        
        ### Uso Recomendado
        - **Planejamento**: Estabelecer metas e recursos
        - **Alertas**: Identificar riscos futuros
        - **Comunicação**: Informar stakeholders
        - **Decisões**: Base para ações preventivas
        """)
        
        st.markdown("""
        ## 📋 Relatórios
        
        ### Tipos de Relatórios
        1. **Resumo Executivo**: Visão geral para gestores
        2. **Análise Detalhada**: Dados técnicos para especialistas
        3. **Tendências**: Evolução temporal dos indicadores
        4. **Comparações**: Benchmarking e metas
        
        ### Conteúdo dos Relatórios
        - **Indicadores**: Valores atuais e históricos
        - **Gráficos**: Visualizações dos dados
        - **Análises**: Interpretações e insights
        - **Recomendações**: Ações sugeridas
        
        ### Exportação
        - **Formato CSV**: Para análise em outras ferramentas
        - **Período Personalizado**: Filtros de data
        - **Colunas Selecionáveis**: Dados específicos
        """)
        
        st.markdown("""
        ## 🔧 Configurações e Parâmetros
        
        ### Parâmetros de Controle
        - **Nível de Confiança**: 95% (padrão)
        - **Período de Análise**: Configurável
        - **Filtros**: Por usuário, data, localização
        
        ### Calibração
        - **Ajuste de Limites**: Baseado na experiência
        - **Validação**: Comparação com benchmarks
        - **Revisão**: Atualização periódica
        
        ### Manutenção
        - **Qualidade dos Dados**: Verificação regular
        - **Atualização**: Parâmetros e métodos
        - **Treinamento**: Usuários e interpretação
        """)
        
        st.markdown("""
        ## 📚 Referências Técnicas
        
        ### Normas e Padrões
        - **NR-5**: Norma Regulamentadora de SST
        - **ISO 45001**: Sistema de Gestão de SST
        - **ANSI Z16.1**: Métodos de Registro de Acidentes
        - **OHSAS 18001**: Especificação para SST
        
        ### Métodos Estatísticos
        - **Montgomery, D.C.**: Introduction to Statistical Quality Control
        - **Wheeler, D.J.**: Understanding Variation
        - **Shewhart, W.A.**: Economic Control of Quality
        
        ### Software e Ferramentas
        - **Streamlit**: Interface web
        - **Plotly**: Visualizações interativas
        - **Pandas**: Manipulação de dados
        - **NumPy**: Cálculos numéricos
        """)
    
    with tab7:
        st.subheader("🔧 Configurações Avançadas")
        
        st.markdown("""
        ## ⚙️ Parâmetros do Sistema
        
        ### Controles Estatísticos
        """)
        
        # Configurações de controle estatístico
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 Cartas de Controle**")
            confidence_level = st.slider(
                "Nível de Confiança (%)",
                min_value=90,
                max_value=99,
                value=95,
                help="Nível de confiança para os limites de controle"
            )
            
            lambda_value = st.slider(
                "Parâmetro λ (Lambda) para EWMA",
                min_value=0.05,
                max_value=0.5,
                value=0.2,
                step=0.05,
                help="Sensibilidade da detecção de tendências"
            )
        
        with col2:
            st.markdown("**📈 Análise de Tendências**")
            min_periods = st.number_input(
                "Períodos Mínimos para Análise",
                min_value=3,
                max_value=24,
                value=6,
                help="Número mínimo de períodos para análise confiável"
            )
            
            trend_threshold = st.number_input(
                "Limiar de Tendência",
                min_value=0.1,
                max_value=1.0,
                value=0.3,
                step=0.1,
                help="Sensibilidade para detecção de tendências"
            )
        
        st.markdown("""
        ### 🎯 Metas e Limites
        
        """)
        
        # Configurações de metas
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 Taxa de Frequência**")
            freq_excellent = st.number_input(
                "Meta Excelente (Taxa de Frequência)",
                min_value=0.0,
                max_value=10.0,
                value=2.0,
                step=0.5,
                help="Taxa considerada excelente"
            )
            
            freq_acceptable = st.number_input(
                "Limite Aceitável (Taxa de Frequência)",
                min_value=0.0,
                max_value=20.0,
                value=5.0,
                step=0.5,
                help="Taxa considerada aceitável"
            )
        
        with col2:
            st.markdown("**📊 Taxa de Gravidade**")
            sev_excellent = st.number_input(
                "Meta Excelente (Taxa de Gravidade)",
                min_value=0.0,
                max_value=100.0,
                value=20.0,
                step=5.0,
                help="Taxa considerada excelente"
            )
            
            sev_acceptable = st.number_input(
                "Limite Aceitável (Taxa de Gravidade)",
                min_value=0.0,
                max_value=200.0,
                value=50.0,
                step=5.0,
                help="Taxa considerada aceitável"
            )
        
        st.markdown("""
        ### 🔮 Previsões
        
        """)
        
        # Configurações de previsão
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📈 Parâmetros de Previsão**")
            forecast_months = st.number_input(
                "Meses para Previsão",
                min_value=1,
                max_value=12,
                value=1,
                help="Número de meses para prever"
            )
            
            min_data_points = st.number_input(
                "Pontos Mínimos de Dados",
                min_value=3,
                max_value=24,
                value=6,
                help="Mínimo de pontos para previsão confiável"
            )
        
        with col2:
            st.markdown("**🎯 Configurações de Confiança**")
            forecast_confidence = st.slider(
                "Confiança da Previsão (%)",
                min_value=50,
                max_value=95,
                value=70,
                help="Nível de confiança das previsões"
            )
            
            trend_sensitivity = st.slider(
                "Sensibilidade da Tendência",
                min_value=0.1,
                max_value=1.0,
                value=0.5,
                step=0.1,
                help="Sensibilidade para detecção de tendências"
            )
        
        st.markdown("""
        ### 💾 Exportação e Relatórios
        
        """)
        
        # Configurações de exportação
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📄 Formato de Relatórios**")
            include_charts = st.checkbox(
                "Incluir Gráficos",
                value=True,
                help="Incluir gráficos nos relatórios exportados"
            )
            
            include_analysis = st.checkbox(
                "Incluir Análises",
                value=True,
                help="Incluir análises e interpretações"
            )
        
        with col2:
            st.markdown("**📊 Dados para Exportação**")
            export_format = st.selectbox(
                "Formato de Exportação",
                ["CSV", "Excel", "PDF"],
                help="Formato preferido para exportação"
            )
            
            decimal_places = st.number_input(
                "Casas Decimais",
                min_value=0,
                max_value=4,
                value=2,
                help="Número de casas decimais nos números"
            )
        
        # Botão para salvar configurações
        if st.button("💾 Salvar Configurações"):
            st.success("✅ Configurações salvas com sucesso!")
            st.info("ℹ️ As configurações serão aplicadas na próxima análise.")
    
    with tab8:
        # Importa e exibe instruções
        from components.instructions import create_instructions_page, get_kpis_instructions
        
        instructions_data = get_kpis_instructions()
        create_instructions_page(
            title=instructions_data["title"],
            description=instructions_data["description"],
            sections=instructions_data["sections"],
            tips=instructions_data["tips"],
            warnings=instructions_data["warnings"],
            references=instructions_data["references"]
        )

if __name__ == "__main__":
    app({})
