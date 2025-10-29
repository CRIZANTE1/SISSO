import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from services.kpi import fetch_kpi_data, generate_kpi_summary
from components.filters import apply_filters_to_df

def app(filters=None):
    st.title("📊 Dashboard Executivo - SSO")
    
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
    
    # === RESUMO EXECUTIVO ===
    st.subheader("📈 Resumo Executivo")
    
    # Métricas principais em destaque
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Taxa de Frequência",
            f"{kpi_summary.get('frequency_rate', 0):.0f}",
            delta=f"{kpi_summary.get('frequency_change', 0):+.1f}%" if kpi_summary.get('frequency_change') else None,
            help="Acidentes por 1 milhão de horas trabalhadas"
        )
    
    with col2:
        st.metric(
            "Taxa de Gravidade", 
            f"{kpi_summary.get('severity_rate', 0):.0f}",
            delta=f"{kpi_summary.get('severity_change', 0):+.1f}%" if kpi_summary.get('severity_change') else None,
            help="Dias perdidos por 1 milhão de horas trabalhadas"
        )
    
    with col3:
        st.metric(
            "Total de Acidentes",
            kpi_summary.get('total_accidents', 0),
            help="Total de acidentes no período"
        )
    
    with col4:
        st.metric(
            "Dias Perdidos",
            kpi_summary.get('total_lost_days', 0),
            help="Total de dias perdidos no período"
        )
    
    # Status geral
    st.markdown("---")
    
    # === STATUS DE SEGURANÇA ===
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🎯 Status de Segurança")
        
        # Calcula status baseado nos indicadores
        freq_rate = kpi_summary.get('frequency_rate', 0)
        sev_rate = kpi_summary.get('severity_rate', 0)
        fatalities = kpi_summary.get('total_fatalities', 0)
        
        # Status geral
        if fatalities > 0:
            st.error("🚨 **CRÍTICO** - Acidentes fatais registrados")
        elif freq_rate > 10 or sev_rate > 100:
            st.warning("⚠️ **ATENÇÃO** - Indicadores elevados")
        elif freq_rate > 5 or sev_rate > 50:
            st.info("📊 **MONITORAR** - Indicadores dentro do aceitável")
        else:
            st.success("✅ **EXCELENTE** - Indicadores dentro da meta")
    
    with col2:
        st.subheader("📊 Base de Cálculo")
        st.metric("Horas Trabalhadas", f"{kpi_summary.get('total_hours', 0):,.0f}")
        st.metric("Período", f"{len(df)} meses")
    
    st.markdown("---")
    
    # === VISUALIZAÇÃO SIMPLIFICADA ===
    st.subheader("📊 Evolução dos Indicadores")
    
    if not df.empty and 'period' in df.columns and 'hours' in df.columns:
        # Calcula indicadores mensais
        df['freq_rate'] = (df['accidents_total'] / df['hours']) * 1_000_000
        df['sev_rate'] = (df['lost_days_total'] / df['hours']) * 1_000_000
        
        # Gráfico único com ambos os indicadores
        fig = go.Figure()
        
        # Taxa de Frequência
        fig.add_trace(go.Scatter(
            x=df['period'],
            y=df['freq_rate'],
            mode='lines+markers',
            name='Taxa de Frequência',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8)
        ))
        
        # Taxa de Gravidade
        fig.add_trace(go.Scatter(
            x=df['period'],
            y=df['sev_rate'],
            mode='lines+markers',
            name='Taxa de Gravidade',
            line=dict(color='#ff7f0e', width=3),
            marker=dict(size=8),
            yaxis='y2'
        ))
        
        # Layout do gráfico
        fig.update_layout(
            title="Evolução das Taxas de Segurança",
            xaxis_title="Período",
            yaxis=dict(title="Taxa de Frequência", side="left"),
            yaxis2=dict(title="Taxa de Gravidade", side="right", overlaying="y"),
            height=400,
            template="plotly_white",
            font=dict(size=12)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # === RESUMO MENSAL SIMPLIFICADO ===
    st.subheader("📅 Resumo Mensal")
    
    if not df.empty:
        # Tabela simplificada
        period_summary = df.groupby('period').agg({
            'accidents_total': 'sum',
            'fatalities': 'sum',
            'with_injury': 'sum',
            'lost_days_total': 'sum',
            'hours': 'sum'
        }).reset_index()
        
        # Calcula taxas
        period_summary['freq_rate'] = (period_summary['accidents_total'] / period_summary['hours'] * 1_000_000).round(0)
        period_summary['sev_rate'] = (period_summary['lost_days_total'] / period_summary['hours'] * 1_000_000).round(0)
        
        # Renomeia colunas
        period_summary.columns = [
            'Período', 'Acidentes', 'Fatais', 'Com Lesão', 
            'Dias Perdidos', 'Horas', 'Taxa Freq.', 'Taxa Grav.'
        ]
        
        # Formata números
        for col in ['Acidentes', 'Fatais', 'Com Lesão', 'Dias Perdidos', 'Taxa Freq.', 'Taxa Grav.']:
            period_summary[col] = period_summary[col].astype(int)
        
        period_summary['Horas'] = period_summary['Horas'].round(0).astype(int)
        
        st.dataframe(
            period_summary,
            use_container_width=True,
            hide_index=True
        )
    
    # === ALERTAS SIMPLIFICADOS ===
    st.subheader("🚨 Alertas")
    
    # Alertas baseados nos indicadores
    alerts = []
    
    if kpi_summary.get('total_fatalities', 0) > 0:
        alerts.append("🚨 **CRÍTICO:** Acidentes fatais registrados")
    
    if kpi_summary.get('frequency_rate', 0) > 10:
        alerts.append("⚠️ **ATENÇÃO:** Taxa de frequência muito elevada")
    elif kpi_summary.get('frequency_rate', 0) > 5:
        alerts.append("📊 **MONITORAR:** Taxa de frequência elevada")
    
    if kpi_summary.get('severity_rate', 0) > 100:
        alerts.append("⚠️ **ATENÇÃO:** Taxa de gravidade muito elevada")
    elif kpi_summary.get('severity_rate', 0) > 50:
        alerts.append("📊 **MONITORAR:** Taxa de gravidade elevada")
    
    if alerts:
        for alert in alerts:
            st.markdown(alert)
    else:
        st.success("✅ Nenhum alerta crítico identificado")

if __name__ == "__main__":
    app({})
