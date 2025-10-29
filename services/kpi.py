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
    return (accidents / hours_worked) * 1_000_000

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
    return ((lost_days + debited_days) / hours_worked) * 1_000_000

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
    """Gera resumo dos KPIs com interpretações conforme NBR 14280"""
    if df.empty:
        return {}
    
    # Calcula totais acumulados para todo o período
    total_accidents = df['accidents_total'].sum()
    total_lost_days = df['lost_days_total'].sum()
    total_hours = df['hours'].sum()
    total_fatalities = df.get('fatalities', pd.Series([0] * len(df))).sum()
    total_debited_days = df.get('debited_days', pd.Series([0] * len(df))).sum()
    
    # Cálculos acumulados para todo o período
    freq_rate = calculate_frequency_rate(total_accidents, total_hours)
    sev_rate = calculate_severity_rate(total_lost_days, total_hours, total_debited_days)
    
    # Interpretações conforme parâmetros de referência
    freq_interpretation = get_frequency_rate_interpretation(freq_rate)
    sev_interpretation = get_severity_rate_interpretation(sev_rate)
    
    # Comparação com período anterior (último período vs penúltimo)
    latest_period = df['period'].max()
    latest_data = df[df['period'] == latest_period].iloc[0]
    
    prev_period_data = df[df['period'] < latest_period]
    if not prev_period_data.empty:
        prev_data = prev_period_data.iloc[-1]
        prev_freq_rate = calculate_frequency_rate(
            prev_data['accidents_total'], 
            prev_data['hours']
        )
        prev_sev_rate = calculate_severity_rate(
            prev_data['lost_days_total'], 
            prev_data['hours'],
            prev_data.get('debited_days', 0)
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
        'total_accidents': total_accidents,
        'total_fatalities': total_fatalities,
        'total_lost_days': total_lost_days,
        'total_debited_days': total_debited_days,
        'total_hours': total_hours,
        'frequency_interpretation': freq_interpretation,
        'severity_interpretation': sev_interpretation
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
            df_sorted['freq_rate'] = (df_sorted['accidents_total'] / df_sorted['hours']) * 1_000_000
            
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
            df_sorted['sev_rate'] = (df_sorted['lost_days_total'] / df_sorted['hours']) * 1_000_000
            
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
            avg_hours = float(recent_data['hours'].mean())
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
