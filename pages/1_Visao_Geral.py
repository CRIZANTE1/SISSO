import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from services.kpi import (
    fetch_kpi_data, 
    generate_kpi_summary,
    calculate_poisson_control_limits,
    calculate_ewma,
    detect_control_chart_patterns,
    fetch_detailed_accidents,
    analyze_accidents_by_category
)
from components.filters import apply_filters_to_df

def app(filters=None):
    # Verifica autenticação e trial
    from auth.auth_utils import require_login
    require_login()
    
    st.title("📊 Dashboard Executivo - SSO")
    # Ajuda da página (popover)
    c1, c2 = st.columns([6, 1])
    with c2:
        with st.popover("❓ Ajuda"):
            st.markdown(
                "**Como usar a Visão Geral**\n\n"
                "- Ajuste filtros na barra lateral.\n"
                "- Leia os cartões de status e indicadores principais.\n"
                "- Use as abas para metodologia e instruções detalhadas.\n\n"
                "**📝 Feedback**\n"
                "- Encontrou um erro ou tem uma sugestão? Acesse **Conta → Feedbacks** para reportar!"
            )
    
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
        
        # Busca dados detalhados de acidentes
        accidents_df = fetch_detailed_accidents(
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
    
    # Cria abas para diferentes seções
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📚 Metodologia", "📚 Instruções"])
    
    with tab1:
        # === RESUMO SIMPLES E CLARO ===
        st.subheader("📊 Resumo da Segurança no Trabalho")
        
        # ✅ NOVO: Aviso quando há dados acumulados
        if kpi_summary.get('periods_count', 0) > 1:
            st.info(f"📊 **Dados acumulados de {kpi_summary['periods_count']} períodos** | "
                    f"Total de {kpi_summary.get('total_hours', 0):,.0f} horas trabalhadas")
        
        # Status geral em destaque
        freq_rate = kpi_summary.get('frequency_rate', 0)
        sev_rate = kpi_summary.get('severity_rate', 0)
        total_accidents = kpi_summary.get('total_accidents', 0)
        fatalities = kpi_summary.get('total_fatalities', 0)
        
        # ✅ CORRIGIDO: Sempre usa TAXA ACUMULADA (padrão NBR 14280)
        # A taxa acumulada é calculada como: (Total acidentes / Total horas) × 1.000.000
        # Esta é a forma correta de calcular para múltiplos períodos conforme a norma
        display_freq_rate = freq_rate
        display_sev_rate = sev_rate
        if kpi_summary.get('periods_count', 0) > 1:
            rate_label = f"Taxa Acumulada ({kpi_summary['periods_count']} períodos)"
        else:
            rate_label = "Taxa do Período"
        
        # Determina status geral
        if fatalities > 0:
            status_color = "🔴"
            status_text = "CRÍTICO"
            status_description = "Há acidentes fatais registrados"
        elif freq_rate > 40 or sev_rate > 100:
            status_color = "🟠"
            status_text = "ATENÇÃO"
            status_description = "Indicadores elevados, revisão necessária"
        elif freq_rate > 20 or sev_rate > 50:
            status_color = "🟡"
            status_text = "MONITORAR"
            status_description = "Indicadores dentro do aceitável"
        else:
            status_color = "🟢"
            status_text = "EXCELENTE"
            status_description = "Indicadores em situação ideal"
        
        # Card de status principal
        st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
            <h2 style="color: #1f4e79; margin: 0;">{status_color} Status Geral: {status_text}</h2>
            <p style="font-size: 16px; margin: 10px 0 0 0; color: #666;">{status_description}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Métricas principais simplificadas
        st.subheader("📈 Indicadores Principais")
        
        # ✅ Mostra informação sobre o cálculo
        if kpi_summary.get('periods_count', 0) > 1:
            st.caption(f"**{rate_label}** - Conforme NBR 14280: (Total de acidentes ÷ Total de horas) × 1.000.000")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            freq_data = kpi_summary.get('frequency_interpretation', {})
            freq_value = display_freq_rate  # ✅ Usa valor correto
            freq_class = freq_data.get('classification', 'N/A')
            
            # Ícone baseado na classificação
            if freq_class == 'Muito Bom':
                freq_icon = "🟢"
            elif freq_class == 'Bom':
                freq_icon = "🟡"
            elif freq_class == 'Ruim':
                freq_icon = "🟠"
            else:
                freq_icon = "🔴"
            
            # ✅ CORRIGIDO: Só mostra delta se houver comparação válida
            freq_change = kpi_summary.get('frequency_change')
            freq_delta = f"{freq_change:+.1f}%" if freq_change is not None else None
            
            st.metric(
                f"{freq_icon} Acidentes por Milhão de Horas",
                f"{freq_value:.0f}",
                delta=freq_delta,
                help=f"Quantos acidentes acontecem a cada 1 milhão de horas trabalhadas\nClassificação: {freq_class}\n{rate_label}"
            )
        
        with col2:
            sev_data = kpi_summary.get('severity_interpretation', {})
            sev_value = display_sev_rate  # ✅ Usa valor correto
            sev_class = sev_data.get('classification', 'N/A')
            
            # Ícone baseado na classificação
            if sev_class == 'Excelente':
                sev_icon = "🟢"
            elif sev_class == 'Aceitável':
                sev_icon = "🟡"
            elif sev_class == 'Elevado':
                sev_icon = "🟠"
            else:
                sev_icon = "🔴"
            
            # ✅ CORRIGIDO: Só mostra delta se houver comparação válida
            sev_change = kpi_summary.get('severity_change')
            sev_delta = f"{sev_change:+.1f}%" if sev_change is not None else None
            
            st.metric(
                f"{sev_icon} Dias Perdidos por Milhão de Horas",
                f"{sev_value:.0f}",
                delta=sev_delta,
                help=f"Quantos dias de trabalho são perdidos a cada 1 milhão de horas trabalhadas\nClassificação: {sev_class}\n{rate_label}"
            )
        
        with col3:
            total_acc = kpi_summary.get('total_accidents', 0)
            fatalities = kpi_summary.get('total_fatalities', 0)
            
            # Ícone baseado no número de acidentes
            if total_acc == 0:
                acc_icon = "🟢"
            elif total_acc <= 2:
                acc_icon = "🟡"
            elif total_acc <= 5:
                acc_icon = "🟠"
            else:
                acc_icon = "🔴"
            
            st.metric(
                f"{acc_icon} Total de Acidentes",
                f"{total_acc}",
                help=f"Quantos acidentes aconteceram no período\nFatais: {fatalities}"
            )
        
        with col4:
            lost_days = kpi_summary.get('total_lost_days', 0)
            automatic_debited = kpi_summary.get('automatic_debited_days', 0)
            total_impact = lost_days + automatic_debited
            
            # Ícone baseado no impacto total (dias perdidos + debitados)
            if total_impact == 0:
                days_icon = "🟢"
            elif total_impact <= 100:
                days_icon = "🟡"
            elif total_impact <= 1000:
                days_icon = "🟠"
            else:
                days_icon = "🔴"
            
            st.metric(
                f"{days_icon} Dias de Trabalho Perdidos",
                f"{lost_days}",
                delta=f"+{automatic_debited} debitados" if automatic_debited > 0 else None,
                help=f"Dias perdidos reais: {lost_days}\nDias debitados (fatais): {automatic_debited}\nTotal de impacto: {total_impact}"
            )
        
        # Resumo em linguagem simples
        st.markdown("---")
        st.subheader("💡 O que isso significa?")
        
        # Explicação simples baseada nos dados
        if fatalities > 0:
            st.error("🚨 **SITUAÇÃO CRÍTICA**: Houve acidentes fatais. Ação imediata é necessária para investigar e prevenir novos casos.")
        elif total_accidents == 0:
            st.success("🎉 **EXCELENTE**: Nenhum acidente registrado no período! Continue mantendo os padrões de segurança.")
        elif total_accidents <= 2:
            st.info("✅ **BOM**: Poucos acidentes registrados. Continue monitorando e mantendo as práticas de segurança.")
        else:
            st.warning("⚠️ **ATENÇÃO**: Número de acidentes acima do ideal. É necessário revisar os procedimentos de segurança.")
        
        # Dicas práticas baseadas nos dados
        st.markdown("**📋 Próximos Passos Recomendados:**")
        if fatalities > 0:
            st.markdown("- 🔍 Investigar imediatamente as causas dos acidentes fatais")
            st.markdown("- 🚨 Implementar medidas emergenciais de segurança")
            st.markdown("- 📞 Comunicar às autoridades competentes")
        elif freq_rate > 40:
            st.markdown("- 📚 Revisar e atualizar treinamentos de segurança")
            st.markdown("- 🔧 Melhorar equipamentos de proteção individual")
            st.markdown("- 👥 Intensificar supervisão no trabalho")
        elif freq_rate > 20:
            st.markdown("- 📊 Monitorar indicadores mensalmente")
            st.markdown("- 🎯 Focar em prevenção de acidentes")
            st.markdown("- ✅ Manter práticas atuais de segurança")
        else:
            st.markdown("- 🏆 Documentar boas práticas que estão funcionando")
            st.markdown("- 📈 Manter os padrões atuais de excelência")
            st.markdown("- 🔄 Compartilhar experiências com outras equipes")
        
        st.markdown("---")
        
        # === DETALHES DOS ACIDENTES ===
        if not accidents_df.empty:
            st.subheader("🔍 Detalhes dos Acidentes")
            
            # Analisa acidentes por categoria
            accident_analysis = analyze_accidents_by_category(accidents_df)
            
            if accident_analysis:
                # Resumo simples dos acidentes
                st.markdown("**📊 Resumo por Tipo de Acidente**")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if accident_analysis.get('by_type'):
                        for accident_type, data in accident_analysis['by_type'].items():
                            type_name = {
                                'fatal': 'Fatal',
                                'lesao': 'Com Lesão',
                                'sem_lesao': 'Sem Lesão'
                            }.get(accident_type, accident_type)
                            
                            # Cor baseada no tipo
                            if accident_type == 'fatal':
                                color = "🔴"
                            elif accident_type == 'lesao':
                                color = "🟠"
                            else:
                                color = "🟡"
                            
                            st.metric(
                                f"{color} {type_name}",
                                f"{data['count']} acidentes",
                                help=f"Dias perdidos: {data['lost_days']} | Fatais: {data['fatalities']}"
                            )
                    else:
                        st.info("Nenhum acidente registrado")
                
                with col2:
                    st.markdown("**🎯 Principais Causas**")
                    if accident_analysis.get('by_root_cause'):
                        # Mostra apenas as 2 mais comuns
                        sorted_causes = sorted(
                            accident_analysis['by_root_cause'].items(),
                            key=lambda x: x[1]['count'],
                            reverse=True
                        )[:2]
                        
                        for cause, data in sorted_causes:
                            if cause and cause.strip():
                                st.metric(
                                    f"🔍 {cause}",
                                    f"{data['count']} acidentes",
                                    help=f"Dias perdidos: {data['lost_days']}"
                                )
                    else:
                        st.info("Nenhuma causa registrada")
                
                with col3:
                    st.markdown("**📅 Estatísticas Gerais**")
                    total_acc = accident_analysis.get('total_accidents', 0)
                    fatalities = accident_analysis.get('total_fatalities', 0)
                    lost_days = accident_analysis.get('total_lost_days', 0)
                    
                    st.metric("Total de Acidentes", f"{total_acc}")
                    st.metric("Acidentes Fatais", f"{fatalities}")
                    st.metric("Dias Perdidos", f"{lost_days}")
                
                # Gráfico simples de distribuição
                if accident_analysis.get('by_type'):
                    st.markdown("**📈 Distribuição Visual dos Acidentes**")
                    
                    type_data = accident_analysis['by_type']
                    type_names = []
                    type_counts = []
                    type_colors = []
                    
                    for accident_type, data in type_data.items():
                        type_name = {
                            'fatal': 'Fatal',
                            'lesao': 'Com Lesão',
                            'sem_lesao': 'Sem Lesão'
                        }.get(accident_type, accident_type)
                        
                        type_names.append(type_name)
                        type_counts.append(data['count'])
                        
                        # Cores baseadas no tipo
                        if accident_type == 'fatal':
                            type_colors.append('#FF0000')  # Vermelho
                        elif accident_type == 'lesao':
                            type_colors.append('#FFA500')  # Laranja
                        else:
                            type_colors.append('#FFD700')  # Amarelo
                    
                    # Cria gráfico de pizza simples
                    fig = go.Figure(data=[go.Pie(
                        labels=type_names,
                        values=type_counts,
                        marker_colors=type_colors,
                        textinfo='label+value',
                        textfont_size=14
                    )])
                    
                    fig.update_layout(
                        title="Tipos de Acidentes",
                        height=350,
                        showlegend=True,
                        font=dict(size=12)
                    )
                    
                    st.plotly_chart(fig, width='stretch')
        
        st.markdown("---")
        
        # === INFORMAÇÕES ADICIONAIS ===
        st.subheader("📊 Informações de Base")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Horas Trabalhadas",
                f"{kpi_summary.get('total_hours', 0):,.0f}",
                help="Total de horas trabalhadas no período"
            )
        
        with col2:
            st.metric(
                "Período Analisado",
                f"{len(df)} meses",
                help="Quantidade de meses com dados"
            )
        
        with col3:
            if kpi_summary.get('total_hours', 0) > 0:
                avg_hours_month = kpi_summary.get('total_hours', 0) / len(df) if len(df) > 0 else 0
                st.metric(
                    "Média Mensal",
                    f"{avg_hours_month:,.0f} horas",
                    help="Média de horas trabalhadas por mês"
                )
            else:
                st.metric("Média Mensal", "0 horas")
        
        st.markdown("---")
        
        # === GRÁFICO SIMPLES ===
        if not df.empty and 'period' in df.columns and 'hours' in df.columns:
            st.subheader("📈 Evolução dos Acidentes")
            
            # Gráfico simples de acidentes por mês
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df['period'],
                y=df['accidents_total'],
                mode='lines+markers',
                name='Total de Acidentes',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8)
            ))
            
            fig.update_layout(
                title="Acidentes por Mês",
                xaxis_title="Período",
                yaxis_title="Número de Acidentes",
                height=350,
                template="plotly_white",
                font=dict(size=12)
            )
            
            st.plotly_chart(fig, width='stretch')
    
        # === TABELA MENSAL SIMPLES ===
        if not df.empty:
            st.subheader("📅 Dados por Mês")
            
            # Tabela simplificada
            period_summary = df.groupby('period').agg({
                'accidents_total': 'sum',
                'fatalities': 'sum',
                'lost_days_total': 'sum',
                'hours': 'sum'
            }).reset_index()
            
            # Renomeia colunas para linguagem simples
            period_summary.columns = [
                'Mês', 'Acidentes', 'Fatais', 'Dias Perdidos', 'Horas Trabalhadas'
            ]
            
            # Formata números
            for col in ['Acidentes', 'Fatais', 'Dias Perdidos']:
                period_summary[col] = period_summary[col].astype(int)
            
            period_summary['Horas Trabalhadas'] = period_summary['Horas Trabalhadas'].round(0).astype(int)
            
            st.dataframe(
                period_summary,
                width='stretch',
                hide_index=True
            )
        
        # === RESUMO FINAL ===
        st.subheader("📋 Resumo Final")
        
        # Resumo simples baseado nos dados
        if fatalities > 0:
            st.error("🚨 **ATENÇÃO CRÍTICA**: Há acidentes fatais registrados. Ação imediata necessária.")
        elif total_accidents == 0:
            st.success("🎉 **PARABÉNS**: Nenhum acidente registrado! Continue assim!")
        elif total_accidents <= 2:
            st.info("✅ **BOM**: Poucos acidentes. Continue monitorando a segurança.")
        else:
            st.warning("⚠️ **CUIDADO**: Número de acidentes acima do ideal. Revisar procedimentos.")
        
        # Informação adicional com taxas corretas
        if kpi_summary.get('total_hours', 0) > 0:
            automatic_debited = kpi_summary.get('automatic_debited_days', 0)
            periods_count = kpi_summary.get('periods_count', 1)
            
            info_text = f"""
            📊 **Base de cálculo**: 
            - {kpi_summary.get('total_hours', 0):,.0f} horas trabalhadas em {periods_count} período(s)
            - Taxa de Frequência Acumulada: {freq_rate:.1f} acidentes/milhão de horas
            - Taxa de Gravidade Acumulada: {sev_rate:.1f} dias perdidos/milhão de horas
            """
            
            if periods_count > 1:
                info_text += f"""
            - Taxa de Frequência Média: {kpi_summary.get('avg_frequency_rate', 0):.1f} acidentes/milhão de horas
            - Taxa de Gravidade Média: {kpi_summary.get('avg_severity_rate', 0):.1f} dias perdidos/milhão de horas
                """
            
            if automatic_debited > 0:
                info_text += f"""
            
            ⚠️ **Dias Debitados Automáticos**: {automatic_debited:,} dias adicionados automaticamente para acidentes fatais conforme NBR 14280 (6.000 dias por fatalidade)
                """
            
            st.info(info_text)
    
    with tab2:
        st.subheader("📚 Metodologia do Dashboard Executivo")
        
        st.markdown("""
        ## 🎯 Objetivo do Dashboard
        
        O Dashboard Executivo foi projetado para fornecer uma **visão consolidada e estratégica** dos indicadores de segurança, 
        permitindo tomada de decisão rápida e eficaz para gestores e executivos.
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
        - **Cálculo**: Baseado em dados acumulados do período selecionado
        
        ### 2. Taxa de Gravidade (TG)
        - **Fórmula**: `((dias perdidos + dias debitados) × 1.000.000) ÷ hora-homem trabalhada`
        - **Unidade**: Dias perdidos por 1 milhão de horas trabalhadas
        - **Conceito**: Mede o impacto ou severidade dos acidentes em termos de tempo de trabalho perdido
        - **Dias Debitados**: Para casos graves conforme NBR 14280:
          - Morte = 6.000 dias
          - Amputação de mão = 3.000 dias
          - Amputação de pé = 2.400 dias
        - **Interpretação**:
          - **≤ 50**: Excelente
          - **50-100**: Aceitável
          - **100-200**: Elevado
          - **> 200**: Crítico
        - **Cálculo**: Baseado em dados acumulados do período selecionado
        
        ### 3. Total de Acidentes
        - **Definição**: Soma de todos os acidentes registrados no período
        - **Categorias**: Fatais, Com Lesão, Sem Lesão
        - **Cálculo**: Acumulado do período selecionado
        
        ### 4. Dias Perdidos
        - **Definição**: Total de dias de trabalho perdidos devido a acidentes
        - **Cálculo**: Soma de todos os dias perdidos no período
        - **Importância**: Indicador de impacto econômico dos acidentes
        """)
        
        st.markdown("""
        ## 🎨 Sistema de Status Visual
        
        ### Status de Segurança
        - **🚨 CRÍTICO**: Acidentes fatais registrados
        - **⚠️ ATENÇÃO**: Indicadores elevados (freq > 10 ou grav > 100)
        - **📊 MONITORAR**: Indicadores dentro do aceitável (freq > 5 ou grav > 50)
        - **✅ EXCELENTE**: Indicadores dentro da meta
        
        ### Cores e Ícones
        - **🔴 Vermelho**: Situação crítica, ação imediata necessária
        - **🟡 Amarelo**: Atenção, monitoramento intensivo
        - **🟢 Verde**: Situação normal, manter práticas
        - **📈📉**: Tendências ascendentes/descendentes
        """)
        
        st.markdown("""
        ## 📈 Análise de Tendências
        
        ### Gráfico de Evolução
        - **Dados Históricos**: Valores observados em cada período
        - **Tendência Suavizada**: Linha que mostra direção geral
        - **Interpretação**:
          - **Linha Ascendente**: Piora no desempenho
          - **Linha Descendente**: Melhoria no desempenho
          - **Linha Estável**: Manutenção do status quo
        
        ### Variações Percentuais
        - **Cálculo**: `((Valor Atual - Valor Anterior) ÷ Valor Anterior) × 100`
        - **Interpretação**:
          - **Positivo (+)**: Aumento (ruim para acidentes)
          - **Negativo (-)**: Diminuição (bom para acidentes)
        """)
        
        st.markdown("""
        ## 📋 Resumo Mensal
        
        ### Tabela de Dados
        - **Período**: Mês/ano dos dados
        - **Acidentes**: Total por período
        - **Fatais/Com Lesão/Sem Lesão**: Classificação dos acidentes
        - **Dias Perdidos**: Impacto econômico
        - **Horas**: Base de cálculo
        - **Taxa Freq./Grav.**: Indicadores calculados
        
        ### Formatação
        - **Números Inteiros**: Para contagens (acidentes, dias)
        - **Decimais**: Para taxas (frequência, gravidade)
        - **Cores**: Destaque para valores críticos
        """)
        
        st.markdown("""
        ## 🚨 Sistema de Alertas
        
        ### Critérios de Alerta
        1. **Acidentes Fatais**: Sempre crítico
        2. **Taxa de Frequência > 10**: Atenção
        3. **Taxa de Frequência > 5**: Monitorar
        4. **Taxa de Gravidade > 100**: Atenção
        5. **Taxa de Gravidade > 50**: Monitorar
        
        ### Ações Recomendadas
        - **CRÍTICO**: Investigação imediata, plano de ação emergencial
        - **ATENÇÃO**: Revisão de procedimentos, medidas preventivas
        - **MONITORAR**: Acompanhamento regular, melhorias pontuais
        - **EXCELENTE**: Manter práticas, documentar sucessos
        """)
        
        st.markdown("""
        ## 🔧 Limitações e Considerações
        
        ### Dados Necessários
        - **Mínimo**: 1 mês de dados para cálculos básicos
        - **Recomendado**: 3+ meses para análise de tendências
        - **Ideal**: 12+ meses para análise sazonal
        
        ### Qualidade dos Dados
        - **Horas Trabalhadas**: Deve ser registrada corretamente
        - **Classificação de Acidentes**: Seguir critérios padronizados
        - **Dias Perdidos**: Contabilizar apenas dias efetivamente perdidos
        
        ### Interpretação
        - **Contexto**: Considerar sazonalidade e eventos especiais
        - **Comparação**: Usar períodos similares para análise
        - **Tendências**: Focar em padrões de longo prazo
        """)
        
        st.markdown("""
        ## 📚 Referências Técnicas
        
        - **NR-5**: Norma Regulamentadora de Segurança e Saúde no Trabalho
        - **ISO 45001**: Sistema de Gestão de Segurança e Saúde Ocupacional
        - **OHSAS 18001**: Especificação para Sistemas de Gestão de SST
        - **ANSI Z16.1**: Métodos de Registro e Medição de Acidentes
        """)
        
        # ✅ NOVO: Explicação detalhada da base de cálculo e exemplos
        st.markdown("""
        ## 🧮 Metodologia de Cálculo Aplicada
        
        ### Base de Cálculo
        O sistema utiliza duas abordagens para cálculo das taxas:
        
        **1. Taxa Acumulada (Período Total)**
        - **Uso**: Visão consolidada de todo o período filtrado
        - **Cálculo**: `(Total de acidentes / Total de horas) × 1.000.000`
        - **Quando usar**: Relatórios anuais, comparações de longo prazo
        
        **2. Taxa Média por Período**
        - **Uso**: Análise de desempenho médio mensal
        - **Cálculo**: Média das taxas calculadas para cada mês
        - **Quando usar**: Identificar tendências, comparar meses específicos
        
        ### Exemplo Prático
        
        **Cenário**: 3 meses de dados
        
        | Mês | Acidentes | Horas | Taxa Individual |
        |-----|-----------|-------|-----------------|
        | Jan | 2 | 10.000 | 200 |
        | Fev | 0 | 10.000 | 0 |
        | Mar | 1 | 10.000 | 100 |
        
        **Taxa Acumulada**: (3 / 30.000) × 1.000.000 = **100**
        **Taxa Média**: (200 + 0 + 100) / 3 = **100**
        
        Neste caso, os valores coincidem. Porém, com horas variáveis:
        
        | Mês | Acidentes | Horas | Taxa Individual |
        |-----|-----------|-------|-----------------|
        | Jan | 2 | 5.000 | 400 |
        | Fev | 0 | 15.000 | 0 |
        | Mar | 1 | 10.000 | 100 |
        
        **Taxa Acumulada**: (3 / 30.000) × 1.000.000 = **100**
        **Taxa Média**: (400 + 0 + 100) / 3 = **166,7**
        
        A taxa média é mais alta porque janeiro teve muitos acidentes com poucas horas.
        
        ### Qual Taxa Usar?
        
        - **Taxa Acumulada**: Melhor para relatórios oficiais e comparações totais
        - **Taxa Média**: Melhor para identificar meses problemáticos e tendências
        
        **Neste sistema**: Exibimos a **taxa acumulada** por padrão, mas calculamos ambas para análises internas.
        """)
    
    with tab3:
        # Importa e exibe instruções
        from components.instructions import create_instructions_page, get_general_instructions
        
        instructions_data = get_general_instructions()
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
