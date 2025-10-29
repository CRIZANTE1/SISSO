import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
from managers.supabase_config import get_supabase_client

# Import scipy opcionalmente
try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("⚠️ SciPy não está disponível. Algumas funcionalidades estatísticas podem estar limitadas.")

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
    """Calcula taxa de frequência (acidentes por 1M de horas)"""
    if hours_worked is None or hours_worked == 0:
        return 0.0
    return (accidents / hours_worked) * 1_000_000

def calculate_severity_rate(lost_days: int, hours_worked: float) -> float:
    """Calcula taxa de gravidade (dias perdidos por 1M de horas)"""
    if hours_worked is None or hours_worked == 0:
        return 0.0
    return (lost_days / hours_worked) * 1_000_000

def calculate_poisson_control_limits(df: pd.DataFrame, 
                                   accidents_col: str = 'accidents_total',
                                   hours_col: str = 'hours') -> pd.DataFrame:
    """Calcula limites de controle Poisson para eventos raros"""
    df = df.copy()
    
    # Taxa média de acidentes por hora
    total_accidents = df[accidents_col].sum()
    total_hours = df[hours_col].sum()
    mean_rate = total_accidents / total_hours if total_hours > 0 else 0
    
    # Valor esperado para cada período
    df['expected'] = df[hours_col] * mean_rate
    
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
    """Gera resumo dos KPIs"""
    if df.empty:
        return {}
    
    latest_period = df['period'].max()
    latest_data = df[df['period'] == latest_period].iloc[0]
    
    # Cálculos para o período mais recente
    freq_rate = calculate_frequency_rate(
        latest_data['accidents_total'], 
        latest_data['hours']
    )
    
    sev_rate = calculate_severity_rate(
        latest_data['lost_days_total'], 
        latest_data['hours']
    )
    
    # Comparação com período anterior
    prev_period_data = df[df['period'] < latest_period]
    if not prev_period_data.empty:
        prev_data = prev_period_data.iloc[-1]
        prev_freq_rate = calculate_frequency_rate(
            prev_data['accidents_total'], 
            prev_data['hours']
        )
        prev_sev_rate = calculate_severity_rate(
            prev_data['lost_days_total'], 
            prev_data['hours']
        )
        
        # Evita variações artificiais quando o período anterior é zero ou inexistente
        freq_change = ((freq_rate - prev_freq_rate) / prev_freq_rate * 100) if prev_freq_rate and prev_freq_rate > 0 else None
        sev_change = ((sev_rate - prev_sev_rate) / prev_sev_rate * 100) if prev_sev_rate and prev_sev_rate > 0 else None
    else:
        freq_change = None
        sev_change = None
    
    return {
        'latest_period': latest_period,
        'frequency_rate': freq_rate,
        'severity_rate': sev_rate,
        'frequency_change': freq_change,
        'severity_change': sev_change,
        'total_accidents': latest_data['accidents_total'],
        'total_fatalities': latest_data.get('fatalities', 0),
        'total_lost_days': latest_data['lost_days_total'],
        'total_hours': latest_data['hours']
    }
