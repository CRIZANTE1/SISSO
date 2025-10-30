import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, Any, List, Optional

def create_kpi_card(title: str, 
                   value: Any, 
                   change: Optional[float] = None,
                   change_label: str = "vs período anterior",
                   icon: str = "📊",
                   color: str = "normal",
                   subtitle: Optional[str] = None) -> None:
    """Cria card de KPI com valor e variação"""
    
    # Define cores baseadas no tipo
    color_map = {
        "normal": "#1f77b4",
        "success": "#28a745", 
        "warning": "#ffc107",
        "danger": "#dc3545",
        "info": "#17a2b8"
    }
    
    card_color = color_map.get(color, color_map["normal"])
    
    # Formata valor
    if isinstance(value, (int, float)):
        if value >= 1_000_000:
            formatted_value = f"{value:,.1f}M"
        elif value >= 1_000:
            formatted_value = f"{value:,.1f}K"
        else:
            formatted_value = f"{value:,.2f}"
    else:
        formatted_value = str(value)
    
    # Formata mudança
    change_text = ""
    change_color = ""
    if change is not None:
        if change > 0:
            change_text = f"+{change:.1f}%"
            change_color = "#dc3545"  # Vermelho para aumento
        elif change < 0:
            change_text = f"{change:.1f}%"
            change_color = "#28a745"  # Verde para diminuição
        else:
            change_text = "0.0%"
            change_color = "#6c757d"  # Cinza para sem mudança
    
    # Layout do card
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown(f"<div style='text-align: center; font-size: 2em;'>{icon}</div>", 
                   unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"**{title}**")
        st.markdown(f"<div style='font-size: 1.5em; font-weight: bold; color: {card_color};'>{formatted_value}</div>", 
                   unsafe_allow_html=True)
        
        if subtitle:
            st.markdown(f"<div style='font-size: 0.8em; color: {card_color}; font-style: italic;'>{subtitle}</div>", 
                       unsafe_allow_html=True)
        
        if change_text:
            st.markdown(f"<div style='font-size: 0.9em; color: {change_color};'>{change_text} {change_label}</div>", 
                       unsafe_allow_html=True)

def create_metric_row(metrics: List[Dict[str, Any]]) -> None:
    """Cria linha de métricas lado a lado"""
    cols = st.columns(len(metrics))
    
    for i, metric in enumerate(metrics):
        with cols[i]:
            create_kpi_card(
                title=metric.get("title", ""),
                value=metric.get("value", 0),
                change=metric.get("change"),
                change_label=metric.get("change_label", "vs anterior"),
                icon=metric.get("icon", "📊"),
                color=metric.get("color", "normal"),
                subtitle=metric.get("subtitle")
            )

def create_trend_chart(df: pd.DataFrame, 
                      x_col: str, 
                      y_col: str,
                      title: str,
                      color: str = "#1f77b4") -> go.Figure:
    """Cria gráfico de tendência"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[y_col],
        mode='lines+markers',
        name=y_col,
        line=dict(color=color, width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title=x_col,
        yaxis_title=y_col,
        hovermode='x unified',
        template='plotly_white'
    )
    
    return fig

def create_control_chart(df: pd.DataFrame,
                        x_col: str,
                        value_col: str,
                        ucl_col: str,
                        lcl_col: str,
                        center_line_col: str,
                        title: str) -> go.Figure:
    """Cria gráfico de controle estatístico"""
    fig = go.Figure()
    
    # Linha de valores observados
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[value_col],
        mode='lines+markers',
        name='Valores Observados',
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=6)
    ))
    
    # Limite superior de controle
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[ucl_col],
        mode='lines',
        name='UCL',
        line=dict(color='red', width=2, dash='dash'),
        showlegend=True
    ))
    
    # Limite inferior de controle
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[lcl_col],
        mode='lines',
        name='LCL',
        line=dict(color='red', width=2, dash='dash'),
        showlegend=True
    ))
    
    # Linha central
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[center_line_col],
        mode='lines',
        name='Linha Central',
        line=dict(color='green', width=2, dash='dot'),
        showlegend=True
    ))
    
    # Destacar pontos fora de controle
    if 'out_of_control' in df.columns:
        out_of_control = df[df['out_of_control']]
        if not out_of_control.empty:
            fig.add_trace(go.Scatter(
                x=out_of_control[x_col],
                y=out_of_control[value_col],
                mode='markers',
                name='Fora de Controle',
                marker=dict(color='red', size=10, symbol='x'),
                showlegend=True
            ))
    
    fig.update_layout(
        title=title,
        xaxis_title=x_col,
        yaxis_title=value_col,
        hovermode='x unified',
        template='plotly_white'
    )
    
    return fig

def create_bar_chart(df: pd.DataFrame,
                    x_col: str,
                    y_col: str,
                    title: str,
                    color: str = "#1f77b4") -> go.Figure:
    """Cria gráfico de barras"""
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df[x_col],
        y=df[y_col],
        name=y_col,
        marker_color=color
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title=x_col,
        yaxis_title=y_col,
        template='plotly_white'
    )
    
    return fig

def create_pie_chart(df: pd.DataFrame,
                    names_col: str,
                    values_col: str,
                    title: str) -> go.Figure:
    """Cria gráfico de pizza"""
    fig = go.Figure(data=[go.Pie(
        labels=df[names_col],
        values=df[values_col],
        hole=0.3
    )])
    
    fig.update_layout(
        title=title,
        template='plotly_white'
    )
    
    return fig

def create_heatmap(df: pd.DataFrame,
                  x_col: str,
                  y_col: str,
                  values_col: str,
                  title: str) -> go.Figure:
    """Cria mapa de calor"""
    fig = go.Figure(data=go.Heatmap(
        x=df[x_col],
        y=df[y_col],
        z=df[values_col],
        colorscale='Reds'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title=x_col,
        yaxis_title=y_col,
        template='plotly_white'
    )
    
    return fig

def create_dashboard_summary(kpi_data: Dict[str, Any]) -> None:
    """Cria resumo do dashboard"""
    st.header("📊 Resumo Executivo")
    
    # Métricas principais
    metrics = [
        {
            "title": "Taxa de Frequência",
            "value": f"{kpi_data.get('frequency_rate', 0):.2f}",
            "change": kpi_data.get('frequency_change'),
            "change_label": "vs mês anterior",
            "icon": "📈",
            # Cor neutra quando não há base de comparação
            "color": ("info" if kpi_data.get('frequency_change') is None else ("danger" if kpi_data.get('frequency_change', 0) > 0 else "success"))
        },
        {
            "title": "Taxa de Gravidade", 
            "value": f"{kpi_data.get('severity_rate', 0):.2f}",
            "change": kpi_data.get('severity_change'),
            "change_label": "vs mês anterior",
            "icon": "⚠️",
            "color": ("info" if kpi_data.get('severity_change') is None else ("danger" if kpi_data.get('severity_change', 0) > 0 else "success"))
        },
        {
            "title": "Total de Acidentes",
            "value": kpi_data.get('total_accidents', 0),
            "icon": "🚨",
            "color": "normal"
        },
        {
            "title": "Dias Perdidos",
            "value": kpi_data.get('total_lost_days', 0),
            "icon": "📅",
            "color": "warning"
        }
    ]
    
    create_metric_row(metrics)
    
    # Alertas
    if kpi_data.get('frequency_change', 0) > 10:
        st.warning("⚠️ **Alerta:** Taxa de frequência aumentou significativamente!")
    
    if kpi_data.get('severity_change', 0) > 10:
        st.warning("⚠️ **Alerta:** Taxa de gravidade aumentou significativamente!")
    
    if kpi_data.get('total_fatalities', 0) > 0:
        st.error("🚨 **CRÍTICO:** Há acidentes fatais registrados!")

def create_data_table(df: pd.DataFrame, 
                     title: str = "Dados",
                     page_size: int = 20) -> None:
    """Cria tabela de dados com paginação"""
    st.subheader(title)
    
    if df.empty:
        st.info("Nenhum dado encontrado com os filtros aplicados.")
        return
    
    # Paginação
    total_pages = (len(df) - 1) // page_size + 1
    page = st.selectbox("Página", range(1, total_pages + 1), key=f"page_{title}")
    
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    st.dataframe(
        df.iloc[start_idx:end_idx],
        width='stretch',
        hide_index=True
    )
    
    st.caption(f"Mostrando {start_idx + 1}-{min(end_idx, len(df))} de {len(df)} registros")
