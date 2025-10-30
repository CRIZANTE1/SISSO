import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
from managers.supabase_config import get_supabase_client
import streamlit as st

# Import scipy opcionalmente
try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("⚠️ SciPy não está disponível. Algumas funcionalidades estatísticas podem estar limitadas.")

# Escala das horas: dados cadastrados em centenas (ex: 176 representa 17.600 horas)
HOURS_SCALE = 100

def fetch_kpi_data(user_email: Optional[str] = None,
                   start_date: Optional[str] = None, 
                   end_date: Optional[str] = None) -> pd.DataFrame:
    """Busca dados de KPI do Supabase"""
    try:
        supabase = get_supabase_client()
        query = supabase.table("kpi_monthly").select("*")
        
        if user_email:
            query = query.eq("created_by", user_email)
        if start_date:
            query = query.gte("period", start_date)
        if end_date:
            query = query.lte("period", end_date)
            
        data = query.order("period").execute().data
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Erro ao buscar dados de KPI: {str(e)}")
        return pd.DataFrame()

def calculate_frequency_rate(accidents: int, hours_worked: float) -> float:
    """
    Calcula Taxa de Frequência (TF) conforme NBR 14280
    
    Fórmula: (N° de acidentes x 1.000.000) / hora-homem trabalhada
    
    A TF indica a quantidade de acidentes ocorridos numa empresa em função 
    da exposição ao risco (horas-homem de exposição ao risco).
    
    Parâmetros de referência:
    - TF até 20 = muito bom
    - 20,1-40 = bom  
    - 40,1-60 = ruim
    - acima de 60 = péssima
    """
    if hours_worked is None or hours_worked == 0:
        return 0.0
    return (accidents / (hours_worked * HOURS_SCALE)) * 1_000_000

def calculate_severity_rate(lost_days: int, hours_worked: float, debited_days: int = 0) -> float:
    """
    Calcula Taxa de Gravidade (TG) conforme NBR 14280
    
    Fórmula: ((dias perdidos + dias debitados) x 1.000.000) / hora-homem trabalhada
    
    A TG mede o impacto ou severidade dos acidentes em termos de tempo de trabalho 
    perdido (ou que será perdido) por cada milhão de horas-homem de exposição ao risco.
    
    Args:
        lost_days: Dias que o trabalhador ficou afastado por conta do acidente
        hours_worked: Total de horas-homem trabalhadas
        debited_days: Dias debitados para casos graves (incapacidade permanente, morte)
                      Ex: morte = 6000 dias, amputação de mão = 3000 dias
    """
    if hours_worked is None or hours_worked == 0:
        return 0.0
    return ((lost_days + debited_days) / (hours_worked * HOURS_SCALE)) * 1_000_000

def get_frequency_rate_interpretation(tf_value: float) -> dict:
    """
    Retorna interpretação da Taxa de Frequência conforme parâmetros de referência
    """
    if tf_value <= 20:
        return {
            "classification": "Muito Bom",
            "color": "success",
            "icon": "✅",
            "description": "Excelente desempenho em prevenção de acidentes"
        }
    elif tf_value <= 40:
        return {
            "classification": "Bom", 
            "color": "info",
            "icon": "📊",
            "description": "Bom desempenho, manter práticas atuais"
        }
    elif tf_value <= 60:
        return {
            "classification": "Ruim",
            "color": "warning", 
            "icon": "⚠️",
            "description": "Desempenho ruim, revisar procedimentos de segurança"
        }
    else:
        return {
            "classification": "Péssimo",
            "color": "danger",
            "icon": "🚨", 
            "description": "Desempenho crítico, ação imediata necessária"
        }

def get_severity_rate_interpretation(tg_value: float) -> dict:
    """
    Retorna interpretação da Taxa de Gravidade
    """
    if tg_value <= 50:
        return {
            "classification": "Excelente",
            "color": "success",
            "icon": "✅",
            "description": "Baixo impacto dos acidentes"
        }
    elif tg_value <= 100:
        return {
            "classification": "Aceitável",
            "color": "info", 
            "icon": "📊",
            "description": "Impacto moderado, monitorar"
        }
    elif tg_value <= 200:
        return {
            "classification": "Elevado",
            "color": "warning",
            "icon": "⚠️",
            "description": "Alto impacto, revisar medidas preventivas"
        }
    else:
        return {
            "classification": "Crítico",
            "color": "danger",
            "icon": "🚨",
            "description": "Impacto crítico, investigação imediata necessária"
        }

def calculate_poisson_control_limits(df: pd.DataFrame, 
                                   accidents_col: str = 'accidents_total',
                                   hours_col: str = 'hours') -> pd.DataFrame:
    """Calcula limites de controle Poisson para eventos raros"""
    df = df.copy()
    
    # Taxa média de acidentes por hora
    total_accidents = df[accidents_col].sum()
    total_hours = df[hours_col].sum()
    total_hours_corrected = total_hours * HOURS_SCALE
    mean_rate = total_accidents / total_hours_corrected if total_hours_corrected > 0 else 0
    
    # Valor esperado para cada período
    df['expected'] = (df[hours_col] * HOURS_SCALE) * mean_rate
    
    # Limites de controle (3-sigma)
    df['ucl'] = df['expected'] + 3 * np.sqrt(df['expected'])
    df['lcl'] = np.maximum(0, df['expected'] - 3 * np.sqrt(df['expected']))
    
    # Identificar pontos fora de controle
    df['out_of_control'] = (df[accidents_col] > df['ucl']) | (df[accidents_col] < df['lcl'])
    
    return df

def calculate_ewma(df: pd.DataFrame, 
                  value_col: str, 
                  lambda_param: float = 0.2) -> pd.DataFrame:
    """Calcula EWMA (Exponentially Weighted Moving Average)"""
    df = df.copy()
    df = df.sort_values('period')
    
    # Inicializa com a média dos primeiros valores
    initial_mean = df[value_col].head(12).mean() if len(df) >= 12 else df[value_col].mean()
    
    ewma_values = []
    ewma = initial_mean
    
    for value in df[value_col]:
        ewma = lambda_param * value + (1 - lambda_param) * ewma
        ewma_values.append(ewma)
    
    df['ewma'] = ewma_values
    
    # Limites de controle para EWMA
    variance = df[value_col].var()
    sigma_ewma = np.sqrt((lambda_param / (2 - lambda_param)) * variance)
    
    df['ewma_ucl'] = initial_mean + 3 * sigma_ewma
    df['ewma_lcl'] = initial_mean - 3 * sigma_ewma
    
    return df

def detect_control_chart_patterns(df: pd.DataFrame, 
                                value_col: str, 
                                ucl_col: str, 
                                lcl_col: str) -> Dict[str, List[int]]:
    """Detecta padrões de controle estatístico"""
    patterns = {
        'out_of_control': [],
        'trend_up': [],
        'trend_down': [],
        'runs_above_center': [],
        'runs_below_center': []
    }
    
    values = df[value_col].values
    ucl_values = df[ucl_col].values
    lcl_values = df[lcl_col].values
    center_line = values.mean()
    
    for i in range(len(values)):
        # Pontos fora de controle
        if values[i] > ucl_values[i] or values[i] < lcl_values[i]:
            patterns['out_of_control'].append(i)
        
        # Tendência ascendente (8 pontos consecutivos)
        if i >= 7:
            if all(values[j] > values[j-1] for j in range(i-7, i+1)):
                patterns['trend_up'].append(i)
        
        # Tendência descendente (8 pontos consecutivos)
        if i >= 7:
            if all(values[j] < values[j-1] for j in range(i-7, i+1)):
                patterns['trend_down'].append(i)
    
    return patterns

def generate_kpi_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Gera resumo dos KPIs com interpretações conforme NBR 14280"""
    if df.empty:
        return {}
    
    # Calcula totais acumulados para todo o período
    total_accidents = df['accidents_total'].sum()
    total_lost_days = df['lost_days_total'].sum()
    total_hours = df['hours'].sum()
    total_hours_corrected = total_hours * HOURS_SCALE
    total_fatalities = df.get('fatalities', pd.Series([0] * len(df))).sum()
    total_debited_days = df.get('debited_days', pd.Series([0] * len(df))).sum()
    
    # Calcula automaticamente os dias debitados para acidentes fatais conforme NBR 14280
    # Morte = 6.000 dias debitados
    automatic_debited_days = total_fatalities * 6000
    total_debited_days = total_debited_days + automatic_debited_days
    
    # ✅ VALIDAÇÃO: Verifica se há horas válidas
    if total_hours_corrected <= 0:
        st.warning("⚠️ Total de horas trabalhadas é zero ou inválido. Verifique os dados cadastrados.")
        return {
            'frequency_rate': 0,
            'severity_rate': 0,
            'total_accidents': total_accidents,
            'total_fatalities': total_fatalities,
            'total_lost_days': total_lost_days,
            'total_hours': 0,
            'error': 'Horas inválidas'
        }
    
    # ✅ Cálculos ACUMULADOS para todo o período (correto para visão geral)
    freq_rate = calculate_frequency_rate(total_accidents, total_hours)
    sev_rate = calculate_severity_rate(total_lost_days, total_hours, total_debited_days)
    
    # ✅ NOVO: Calcula também taxas POR PERÍODO para análise mais precisa
    df_with_rates = df.copy()
    df_with_rates['freq_rate_period'] = df_with_rates.apply(
        lambda row: calculate_frequency_rate(
            row['accidents_total'], 
            row['hours']
        ) if row['hours'] > 0 else 0, 
        axis=1
    )
    
    # Calcula dias debitados por período (fatalidades * 6000)
    df_with_rates['period_debited_days'] = (
        df_with_rates.get('debited_days', 0) + 
        (df_with_rates.get('fatalities', 0) * 6000)
    )
    
    df_with_rates['sev_rate_period'] = df_with_rates.apply(
        lambda row: calculate_severity_rate(
            row['lost_days_total'], 
            row['hours'],
            row['period_debited_days']
        ) if row['hours'] > 0 else 0, 
        axis=1
    )
    
    # Taxa média por período (mais representativa para períodos múltiplos)
    avg_freq_rate = df_with_rates['freq_rate_period'].mean()
    avg_sev_rate = df_with_rates['sev_rate_period'].mean()
    
    # Interpretações conforme parâmetros de referência
    freq_interpretation = get_frequency_rate_interpretation(freq_rate)
    sev_interpretation = get_severity_rate_interpretation(sev_rate)
    
    # ✅ MELHORADO: Comparação com média dos últimos 3 períodos (mais estável)
    freq_change = None
    sev_change = None
    
    if len(df_with_rates) >= 4:
        # Ordena por período
        df_sorted = df_with_rates.sort_values('period')
        
        # Último período
        latest_freq = df_sorted['freq_rate_period'].iloc[-1]
        latest_sev = df_sorted['sev_rate_period'].iloc[-1]
        
        # Média dos 3 períodos anteriores
        prev_3_freq = df_sorted['freq_rate_period'].iloc[-4:-1].mean()
        prev_3_sev = df_sorted['sev_rate_period'].iloc[-4:-1].mean()
        
        # Calcula variação percentual
        if prev_3_freq > 0:
            freq_change = ((latest_freq - prev_3_freq) / prev_3_freq * 100)
        
        if prev_3_sev > 0:
            sev_change = ((latest_sev - prev_3_sev) / prev_3_sev * 100)
    
    elif len(df_with_rates) >= 2:
        # Se tiver apenas 2-3 períodos, compara com o anterior
        df_sorted = df_with_rates.sort_values('period')
        
        latest_freq = df_sorted['freq_rate_period'].iloc[-1]
        latest_sev = df_sorted['sev_rate_period'].iloc[-1]
        
        prev_freq = df_sorted['freq_rate_period'].iloc[-2]
        prev_sev = df_sorted['sev_rate_period'].iloc[-2]
        
        if prev_freq > 0:
            freq_change = ((latest_freq - prev_freq) / prev_freq * 100)
        
        if prev_sev > 0:
            sev_change = ((latest_sev - prev_sev) / prev_sev * 100)
    
    return {
        'latest_period': df['period'].max(),
        
        # Taxas acumuladas (total do período)
        'frequency_rate': freq_rate,
        'severity_rate': sev_rate,
        
        # ✅ NOVO: Taxas médias por período
        'avg_frequency_rate': avg_freq_rate,
        'avg_severity_rate': avg_sev_rate,
        
        # Variações
        'frequency_change': freq_change,
        'severity_change': sev_change,
        
        # Totalizadores
        'total_accidents': int(total_accidents),
        'total_fatalities': int(total_fatalities),
        'total_lost_days': int(total_lost_days),
        'total_debited_days': int(total_debited_days),
        'automatic_debited_days': int(automatic_debited_days),
        'total_hours': float(total_hours_corrected),
        
        # Interpretações
        'frequency_interpretation': freq_interpretation,
        'severity_interpretation': sev_interpretation,
        
        # ✅ NOVO: Metadados para transparência
        'periods_count': len(df),
        'calculation_method': 'accumulated' if len(df) > 1 else 'single_period'
    }

def calculate_forecast(df: pd.DataFrame, months_ahead: int = 1) -> Dict[str, Any]:
    """Calcula previsões para os próximos meses baseadas em tendências históricas"""
    if df.empty or len(df) < 3:
        return {}
    
    try:
        # Ordena por período
        df_sorted = df.sort_values('period').copy()
        
        # Calcula médias móveis dos últimos 3 meses
        recent_data = df_sorted.tail(3)
        
        # Previsões baseadas em médias móveis simples
        forecasts = {}
        
        # Taxa de Frequência - usa média móvel dos últimos 3 meses
        if 'hours' in df_sorted.columns and 'accidents_total' in df_sorted.columns:
            df_sorted['freq_rate'] = (df_sorted['accidents_total'] / (df_sorted['hours'] * HOURS_SCALE)) * 1_000_000
            
            # Calcula tendência simples comparando últimos 3 meses
            recent_freq = df_sorted['freq_rate'].tail(3).values
            if len(recent_freq) >= 2:
                # Tendência baseada na diferença entre último e penúltimo
                trend = recent_freq[-1] - recent_freq[-2] if len(recent_freq) >= 2 else 0
                
                # Previsão: último valor + tendência
                predicted_freq = recent_freq[-1] + trend
                predicted_freq = max(0, predicted_freq)  # Não pode ser negativo
                
                forecasts['frequency_rate'] = {
                    'predicted': predicted_freq,
                    'trend': 'increasing' if trend > 0 else 'decreasing' if trend < 0 else 'stable',
                    'confidence': 0.7  # Confiança fixa para simplicidade
                }
        
        # Taxa de Gravidade - usa média móvel dos últimos 3 meses
        if 'hours' in df_sorted.columns and 'lost_days_total' in df_sorted.columns:
            df_sorted['sev_rate'] = (df_sorted['lost_days_total'] / (df_sorted['hours'] * HOURS_SCALE)) * 1_000_000
            
            recent_sev = df_sorted['sev_rate'].tail(3).values
            if len(recent_sev) >= 2:
                trend = recent_sev[-1] - recent_sev[-2] if len(recent_sev) >= 2 else 0
                
                predicted_sev = recent_sev[-1] + trend
                predicted_sev = max(0, predicted_sev)  # Não pode ser negativo
                
                forecasts['severity_rate'] = {
                    'predicted': predicted_sev,
                    'trend': 'increasing' if trend > 0 else 'decreasing' if trend < 0 else 'stable',
                    'confidence': 0.7
                }
        
        # Total de Acidentes - usa média móvel dos últimos 3 meses
        if 'accidents_total' in df_sorted.columns:
            recent_acc = df_sorted['accidents_total'].tail(3).values
            if len(recent_acc) >= 2:
                trend = recent_acc[-1] - recent_acc[-2] if len(recent_acc) >= 2 else 0
                
                predicted_acc = recent_acc[-1] + trend
                predicted_acc = max(0, round(predicted_acc))  # Arredonda e não pode ser negativo
                
                forecasts['total_accidents'] = {
                    'predicted': predicted_acc,
                    'trend': 'increasing' if trend > 0 else 'decreasing' if trend < 0 else 'stable',
                    'confidence': 0.7
                }
        
        # Dias Perdidos - usa média móvel dos últimos 3 meses
        if 'lost_days_total' in df_sorted.columns:
            recent_days = df_sorted['lost_days_total'].tail(3).values
            if len(recent_days) >= 2:
                trend = recent_days[-1] - recent_days[-2] if len(recent_days) >= 2 else 0
                
                predicted_days = recent_days[-1] + trend
                predicted_days = max(0, round(predicted_days))  # Arredonda e não pode ser negativo
                
                forecasts['lost_days'] = {
                    'predicted': predicted_days,
                    'trend': 'increasing' if trend > 0 else 'decreasing' if trend < 0 else 'stable',
                    'confidence': 0.7
                }
        
        # Horas trabalhadas (assume valor médio dos últimos 3 meses)
        if 'hours' in df_sorted.columns:
            avg_hours = float(recent_data['hours'].mean()) * HOURS_SCALE
            forecasts['hours'] = {
                'predicted': round(avg_hours),
                'trend': 'stable',
                'confidence': 0.8
            }
        
        return forecasts
        
    except Exception as e:
        # Em caso de erro, retorna dicionário vazio
        return {}

def generate_forecast_recommendations(forecasts: Dict[str, Any]) -> List[str]:
    """Gera recomendações baseadas nas previsões"""
    recommendations = []
    
    # Análise da taxa de frequência
    if 'frequency_rate' in forecasts:
        freq_data = forecasts['frequency_rate']
        if freq_data['trend'] == 'increasing' and freq_data['predicted'] > 5:
            recommendations.append("🚨 **CRÍTICO:** Taxa de frequência prevista em alta - implementar medidas preventivas urgentes")
        elif freq_data['trend'] == 'increasing':
            recommendations.append("⚠️ **ATENÇÃO:** Taxa de frequência em tendência de alta - revisar procedimentos")
        elif freq_data['trend'] == 'decreasing':
            recommendations.append("✅ **POSITIVO:** Taxa de frequência em tendência de melhoria - manter práticas atuais")
    
    # Análise da taxa de gravidade
    if 'severity_rate' in forecasts:
        sev_data = forecasts['severity_rate']
        if sev_data['trend'] == 'increasing' and sev_data['predicted'] > 50:
            recommendations.append("🚨 **CRÍTICO:** Taxa de gravidade prevista em alta - investigar causas raiz")
        elif sev_data['trend'] == 'increasing':
            recommendations.append("⚠️ **ATENÇÃO:** Taxa de gravidade em tendência de alta - implementar medidas preventivas")
        elif sev_data['trend'] == 'decreasing':
            recommendations.append("✅ **POSITIVO:** Taxa de gravidade em tendência de melhoria - documentar boas práticas")
    
    # Análise do total de acidentes
    if 'total_accidents' in forecasts:
        acc_data = forecasts['total_accidents']
        if acc_data['predicted'] > 2:
            recommendations.append("⚠️ **MONITORAR:** Previsão de acidentes elevada - intensificar treinamentos")
        elif acc_data['predicted'] == 0:
            recommendations.append("🎯 **META:** Previsão de zero acidentes - manter excelente desempenho")
    
    return recommendations

def fetch_detailed_accidents(user_email: str, start_date=None, end_date=None) -> pd.DataFrame:
    """
    Busca dados detalhados de acidentes do usuário atual
    """
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        
        # Busca dados de acidentes - o RLS já controla o acesso baseado no created_by
        query = supabase.table("accidents").select("*").eq("created_by", user_email)
        
        if start_date:
            query = query.gte("occurred_at", start_date.isoformat())
        if end_date:
            query = query.lte("occurred_at", end_date.isoformat())
            
        response = query.order("occurred_at", desc=True).execute()
        
        if response and hasattr(response, 'data') and response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"Erro ao buscar dados de acidentes: {str(e)}")
        return pd.DataFrame()

def analyze_accidents_by_category(accidents_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analisa acidentes por categoria (lesão/fatalidade) e calcula frequência
    """
    if accidents_df.empty:
        return {}
    
    # Converte data para datetime se necessário
    if 'occurred_at' in accidents_df.columns:
        accidents_df['occurred_at'] = pd.to_datetime(accidents_df['occurred_at'])
        accidents_df['year_month'] = accidents_df['occurred_at'].dt.to_period('M')
    
    # Análise por tipo de acidente
    agg_dict = {
        'id': 'count',
        'lost_days': 'sum'
    }
    
    # Adiciona is_fatal apenas se a coluna existir
    if 'is_fatal' in accidents_df.columns:
        agg_dict['is_fatal'] = 'sum'
    
    type_analysis = accidents_df.groupby('type').agg(agg_dict).rename(columns={'id': 'count'})
    
    # Análise por classificação
    classification_analysis = accidents_df.groupby('classification').agg({
        'id': 'count',
        'lost_days': 'sum'
    }).rename(columns={'id': 'count'})
    
    # Análise por parte do corpo
    body_part_analysis = accidents_df.groupby('body_part').agg({
        'id': 'count',
        'lost_days': 'sum'
    }).rename(columns={'id': 'count'})
    
    # Análise por causa raiz
    root_cause_analysis = accidents_df.groupby('root_cause').agg({
        'id': 'count',
        'lost_days': 'sum'
    }).rename(columns={'id': 'count'})
    
    # Análise temporal (últimos 12 meses)
    if 'year_month' in accidents_df.columns:
        temporal_agg_dict = {
            'id': 'count',
            'lost_days': 'sum'
        }
        
        # Adiciona is_fatal apenas se a coluna existir
        if 'is_fatal' in accidents_df.columns:
            temporal_agg_dict['is_fatal'] = 'sum'
            
        temporal_analysis = accidents_df.groupby('year_month').agg(temporal_agg_dict).rename(columns={'id': 'count'})
    else:
        temporal_analysis = pd.DataFrame()
    
    # Converte para formato mais legível
    def format_analysis(df, name):
        if df.empty:
            return {}
        
        result = {}
        for idx, row in df.iterrows():
            if pd.isna(idx) or idx == '':
                continue
            result[str(idx)] = {
                'count': int(row['count']),
                'lost_days': int(row.get('lost_days', 0)),
                'fatalities': int(row.get('is_fatal', 0)) if 'is_fatal' in row else 0
            }
        return result
    
    return {
        'by_type': format_analysis(type_analysis, 'Tipo'),
        'by_classification': format_analysis(classification_analysis, 'Classificação'),
        'by_body_part': format_analysis(body_part_analysis, 'Parte do Corpo'),
        'by_root_cause': format_analysis(root_cause_analysis, 'Causa Raiz'),
        'temporal': format_analysis(temporal_analysis, 'Temporal'),
        'total_accidents': len(accidents_df),
        'total_fatalities': int(accidents_df['is_fatal'].sum()) if 'is_fatal' in accidents_df.columns else 0,
        'total_lost_days': int(accidents_df['lost_days'].sum()) if 'lost_days' in accidents_df.columns else 0,
        'frequency_by_period': calculate_accident_frequency_by_period(accidents_df)
    }

def calculate_accident_frequency_by_period(accidents_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcula a frequência de acidentes por período (mensal)
    """
    if accidents_df.empty or 'occurred_at' not in accidents_df.columns:
        return {}
    
    # Converte data para datetime
    accidents_df['occurred_at'] = pd.to_datetime(accidents_df['occurred_at'])
    accidents_df['year_month'] = accidents_df['occurred_at'].dt.to_period('M')
    
    # Agrupa por período e tipo
    period_analysis = accidents_df.groupby(['year_month', 'type']).size().unstack(fill_value=0)
    
    # Calcula frequência relativa
    period_totals = period_analysis.sum(axis=1)
    period_frequency = {}
    
    for period in period_analysis.index:
        period_str = str(period)
        period_frequency[period_str] = {
            'total': int(period_totals[period]),
            'fatal': int(period_analysis.loc[period, 'fatal']) if 'fatal' in period_analysis.columns else 0,
            'lesao': int(period_analysis.loc[period, 'lesao']) if 'lesao' in period_analysis.columns else 0,
            'sem_lesao': int(period_analysis.loc[period, 'sem_lesao']) if 'sem_lesao' in period_analysis.columns else 0
        }
    
    return period_frequency