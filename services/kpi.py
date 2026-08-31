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
        from auth.auth_utils import get_user_id, is_admin
        from managers.supabase_config import get_service_role_client
        
        user_id = get_user_id()
        if not user_id:
            return pd.DataFrame()
        
        # Usa service_role para contornar RLS e aplicar filtro de segurança no código
        supabase = get_service_role_client()
        
        query = supabase.table("kpi_monthly").select("*")
        
        # Admin vê todos os dados sem filtro de created_by
        if not is_admin():
            # Usuário comum vê apenas seus próprios KPIs
            query = query.eq("created_by", user_id)
        
        if start_date:
            query = query.gte("period", start_date)
        if end_date:
            query = query.lte("period", end_date)
            
        response = query.order("period").execute()
        
        if response and hasattr(response, 'data'):
            df = pd.DataFrame(response.data) if response.data else pd.DataFrame()
            
            # Validação adicional de segurança para usuários não-admin
            if not is_admin() and not df.empty:
                # Filtra novamente para garantir (segurança em camadas)
                df = df[df['created_by'] == user_id]
            
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao buscar dados de KPI: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
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
    """Gera resumo dos KPIs com interpretações conforme NBR 14280 e ISO 45001"""
    if df.empty:
        return {}
    
    # Calcula totais acumulados para todo o período
    # ✅ VALIDAÇÃO: Garante que horas são numéricas
    df['hours'] = pd.to_numeric(df['hours'], errors='coerce').fillna(0)
    df['accidents_total'] = pd.to_numeric(df['accidents_total'], errors='coerce').fillna(0)
    df['lost_days_total'] = pd.to_numeric(df['lost_days_total'], errors='coerce').fillna(0)
    
    total_accidents = float(df['accidents_total'].sum())
    total_lost_days = float(df['lost_days_total'].sum())
    # ✅ CORRIGIDO: A tabela armazena horas em centenas (1.82 = 182 horas reais)
    # Precisa multiplicar por 100 para converter para horas reais
    total_hours = float(df['hours'].sum())  # Soma dos valores da tabela em centenas (ex: 40.79 centenas)
    total_hours_corrected = total_hours * HOURS_SCALE  # Multiplica por 100: 40.79 × 100 = 4.079 horas reais
    total_fatalities = float(df.get('fatalities', pd.Series([0] * len(df))).sum())
    total_debited_days = float(df.get('debited_days', pd.Series([0] * len(df))).sum())
    
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
    # total_hours na tabela está em centenas (4079 = 4.079 centenas = 407.900 horas reais)
    # A função espera receber em centenas e multiplica por 100 internamente
    # Então passamos total_hours diretamente (já está em centenas)
    freq_rate = calculate_frequency_rate(int(total_accidents), total_hours)
    sev_rate = calculate_severity_rate(int(total_lost_days), total_hours, int(total_debited_days))
    
    # ✅ VALIDAÇÃO: Verifica se o cálculo está correto
    if total_hours_corrected > 0:
        expected_freq = (total_accidents / total_hours_corrected) * 1_000_000
        expected_sev = ((total_lost_days + total_debited_days) / total_hours_corrected) * 1_000_000
        # Se houver diferença significativa, algo está errado
        if abs(freq_rate - expected_freq) > 0.01:
            import warnings
            warnings.warn(f"TF calculada ({freq_rate:.2f}) diferente da esperada ({expected_freq:.2f})")
    
    # ✅ NOVO: Calcula também taxas POR PERÍODO para análise mais precisa
    df_with_rates = df.copy()
    # ✅ CORRIGIDO: Horas na tabela estão em centenas (176.0 = 176 centenas = 17.600 horas reais)
    # A função espera em centenas, então passamos diretamente (já está no formato correto)
    df_with_rates['freq_rate_period'] = df_with_rates.apply(
        lambda row: calculate_frequency_rate(
            row['accidents_total'], 
            row['hours']  # Já está em centenas (176.0), que é o formato esperado pela função
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
            row['hours'],  # Já está em centenas (176.0), que é o formato esperado pela função
            row['period_debited_days']
        ) if row['hours'] > 0 else 0, 
        axis=1
    )
    
    # ✅ CORRIGIDO: Taxa acumulada é sempre a forma correta conforme NBR 14280
    # A "média por período" não faz sentido estatístico quando horas variam entre períodos
    # O padrão da norma é: (Total de acidentes / Total de horas) × 1.000.000
    # 
    # Calculamos taxas por período apenas para análise de tendências, não para exibição principal
    
    # Para múltiplos períodos, usa a TAXA ACUMULADA (padrão da norma)
    # A taxa acumulada já é a forma correta de calcular quando há múltiplos períodos
    avg_freq_rate = float(freq_rate)  # Na verdade é taxa acumulada
    avg_sev_rate = float(sev_rate)    # Na verdade é taxa acumulada
    
    # ✅ SEMPRE usa taxa acumulada para interpretação (padrão NBR 14280)
    freq_interpretation = get_frequency_rate_interpretation(float(freq_rate))
    sev_interpretation = get_severity_rate_interpretation(float(sev_rate))
    
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
    
    # ✅ ISO 45001: Adicionando métricas de desempenho e análise de tendências
    # Conformidade com requisitos ISO 45001:2018
    iso_compliance_metrics = calculate_iso_compliance_metrics(df_with_rates)
    
    # ✅ NBR 14280: Análise de tendências de acidentes
    accident_trend_analysis = analyze_accident_trends(df_with_rates)
    
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
        'calculation_method': 'accumulated' if len(df) > 1 else 'single_period',
        
        # ✅ NOVO: Métricas de conformidade ISO 45001:2018
        'iso_compliance_metrics': iso_compliance_metrics,
        
        # ✅ NOVO: Análise de tendências de acidentes conforme NBR 14280
        'accident_trend_analysis': accident_trend_analysis
    }

def calculate_iso_compliance_metrics(df_with_rates: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcula métricas de conformidade com ISO 45001:2018
    A ISO 45001 exige monitoramento contínuo, investigação de incidentes,
    implementação de ações corretivas e melhoria contínua
    """
    metrics = {}
    
    # Avaliação de melhoria contínua (tendência de melhoria nos KPIs)
    if len(df_with_rates) >= 2:
        recent_freq = df_with_rates['freq_rate_period'].tail(3)
        recent_sev = df_with_rates['sev_rate_period'].tail(3)
        
        # Melhoria contínua - se os KPIs estão em tendência de melhoria
        freq_trend = "improving" if len(recent_freq) >= 2 and recent_freq.iloc[-1] < recent_freq.iloc[-2] else "not_improving"
        sev_trend = "improving" if len(recent_sev) >= 2 and recent_sev.iloc[-1] < recent_sev.iloc[-2] else "not_improving"
        
        metrics['continuous_improvement'] = {
            'frequency_trend': freq_trend,
            'severity_trend': sev_trend,
            'is_improving': freq_trend == "improving" and sev_trend == "improving"
        }
    
    # Monitoramento e medição (conformidade com cláusula 9.1)
    metrics['monitoring_compliance'] = {
        'has_consistent_data': len(df_with_rates) > 0 and df_with_rates['accidents_total'].sum() >= 0,
        'data_quality_score': calculate_data_quality_score(df_with_rates)
    }
    
    # Ações corretivas e preventivas (conformidade com cláusula 10.2)
    # Isso seria implementado com base em dados de ações corretivas registradas
    
    return metrics

def analyze_accident_trends(df_with_rates: pd.DataFrame) -> Dict[str, Any]:
    """
    Análise de tendências de acidentes conforme NBR 14280
    """
    if df_with_rates.empty:
        return {}
    
    trends = {}
    
    # Tendência de longo prazo (últimos 6 meses vs 6 meses anteriores)
    if len(df_with_rates) >= 12:
        recent_6 = df_with_rates.tail(6)['freq_rate_period'].mean()
        prev_6 = df_with_rates.head(6)['freq_rate_period'].mean()
        
        if prev_6 > 0:
            change_pct = ((recent_6 - prev_6) / prev_6) * 100
            trends['long_term_trend'] = {
                'change_percentage': change_pct,
                'direction': 'improving' if change_pct < 0 else 'worsening' if change_pct > 0 else 'stable'
            }
    
    # Tendência de curto prazo (últimos 3 meses)
    if len(df_with_rates) >= 6:
        recent_3 = df_with_rates.tail(3)['freq_rate_period'].mean()
        prev_3 = df_with_rates.iloc[-6:-3]['freq_rate_period'].mean()
        
        if prev_3 > 0:
            change_pct = ((recent_3 - prev_3) / prev_3) * 100
            trends['short_term_trend'] = {
                'change_percentage': change_pct,
                'direction': 'improving' if change_pct < 0 else 'worsening' if change_pct > 0 else 'stable'
            }
    
    # Variação coeficiente de variação (medida de estabilidade)
    if len(df_with_rates) >= 3:
        freq_cv = df_with_rates['freq_rate_period'].std() / df_with_rates['freq_rate_period'].mean() if df_with_rates['freq_rate_period'].mean() > 0 else 0
        trends['stability'] = {
            'coefficient_of_variation': freq_cv,
            'stability_level': 'high' if freq_cv < 0.2 else 'medium' if freq_cv < 0.5 else 'low'
        }
    
    return trends

def calculate_data_quality_score(df: pd.DataFrame) -> float:
    """
    Calcula um escore de qualidade dos dados
    """
    score = 100.0  # Pontuação base
    
    # Verifica completude dos dados
    required_columns = ['accidents_total', 'hours', 'lost_days_total']
    for col in required_columns:
        if col in df.columns:
            completeness = df[col].notna().sum() / len(df) * 100
            score *= (completeness / 100)  # Reduz pontuação proporcionalmente
    
    # Verifica consistência temporal
    if 'period' in df.columns:
        expected_periods = len(df)
        unique_periods = df['period'].nunique()
        consistency = (unique_periods / expected_periods) * 100
        score *= (consistency / 100)
    
    return max(0, min(100, score))  # Limita entre 0 e 100

def calculate_corrective_actions_metrics(df_with_rates: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcula métricas de eficácia de ações corretivas e preventivas
    Conforme requisitos da ISO 45001:2018 cláusula 10.2
    """
    metrics = {}
    
    # Este cálculo seria baseado em dados de ações corretivas do sistema
    # Por enquanto, implementando uma métrica baseada na redução de acidentes após eventos
    if len(df_with_rates) >= 3:
        # Comparando média móvel de acidentes
        recent_accidents = df_with_rates['accidents_total'].tail(3).mean()
        prev_accidents = df_with_rates['accidents_total'].head(3).mean()
        
        if prev_accidents > 0:
            improvement_rate = ((prev_accidents - recent_accidents) / prev_accidents) * 100
            metrics['corrective_effectiveness'] = {
                'improvement_rate': improvement_rate,
                'is_improving': improvement_rate > 0
            }
    
    return metrics

def generate_iso_45001_compliance_report(kpi_summary: Dict[str, Any]) -> List[str]:
    """
    Gera relatório de conformidade com ISO 45001:2018
    """
    report = []
    
    # Avaliação das cláusulas principais da ISO 45001
    freq_rate = kpi_summary.get('frequency_rate', 0)
    sev_rate = kpi_summary.get('severity_rate', 0)
    
    # Cláusula 9.1 - Monitoramento, medição, análise e avaliação
    report.append("📊 **Cláusula 9.1 - Monitoramento e medição:**")
    report.append(f"   - Taxa de Frequência: {freq_rate:.2f} acidentes/milhão de horas")
    report.append(f"   - Taxa de Gravidade: {sev_rate:.2f} dias perdidos/milhão de horas")
    
    # Cláusula 10 - Melhoria
    freq_change = kpi_summary.get('frequency_change', 0)
    sev_change = kpi_summary.get('severity_change', 0)
    
    improvement_status = []
    if freq_change is not None:
        improvement_status.append(f"Taxa de Frequência: {'Melhorando' if freq_change < 0 else 'Piorando' if freq_change > 0 else 'Estável'} ({freq_change:+.1f}%)")
    if sev_change is not None:
        improvement_status.append(f"Taxa de Gravidade: {'Melhorando' if sev_change < 0 else 'Piorando' if sev_change > 0 else 'Estável'} ({sev_change:+.1f}%)")
    
    report.append("🔄 **Cláusula 10 - Melhoria contínua:**")
    for status in improvement_status:
        report.append(f"   - {status}")
    
    # Cláusula 10.2 - Ações corretivas e preventivas
    report.append("🔧 **Cláusula 10.2 - Ações corretivas e preventivas:**")
    report.append("   - Implemente acompanhamento de ações corretivas nos acidentes")
    report.append("   - Verifique encerramento e eficácia das ações tomadas")
    
    return report

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
        from auth.auth_utils import get_user_id, is_admin
        
        # Sempre usa service_role e aplica filtro de segurança no código
        supabase = get_service_role_client()
        if not supabase:
            return pd.DataFrame()
        
        user_id = get_user_id()
        if not user_id:
            return pd.DataFrame()
        
        query = supabase.table("accidents").select("*")
        
        # Admin vê todos os dados, usuário comum vê apenas seus próprios
        if not is_admin():
            query = query.eq("created_by", user_id)
        
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
    
    # is_fatal removido - usar type == 'fatal' em vez disso
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
        
        # is_fatal removido - usar type == 'fatal' em vez disso
        temporal_analysis = accidents_df.groupby('year_month').agg(temporal_agg_dict).rename(columns={'id': 'count'})
    else:
        temporal_analysis = pd.DataFrame()
    
    # Converte para formato mais legível
    def format_analysis(df, analysis_name, group_key=None):
        if df.empty:
            return {}
        
        result = {}
        for idx, row in df.iterrows():
            if pd.isna(idx) or idx == '':
                continue
            
            # Calcula fatalities baseado em type == 'fatal'
            fatalities_count = 0
            if analysis_name == 'by_type':
                # Para análise por tipo, se o índice for 'fatal', todos são fatais
                fatalities_count = int(row['count']) if str(idx) == 'fatal' else 0
            elif group_key is not None and 'type' in accidents_df.columns:
                # Para outras análises, filtra o dataframe original pelo grupo e conta fatais
                if group_key == 'classification':
                    group_data = accidents_df[accidents_df['classification'] == idx]
                elif group_key == 'body_part':
                    group_data = accidents_df[accidents_df['body_part'] == idx]
                elif group_key == 'root_cause':
                    group_data = accidents_df[accidents_df['root_cause'] == idx]
                elif group_key == 'year_month':
                    group_data = accidents_df[accidents_df['year_month'] == idx]
                else:
                    group_data = pd.DataFrame()
                
                if not group_data.empty:
                    fatalities_count = len(group_data[group_data['type'] == 'fatal'])
            
            result[str(idx)] = {
                'count': int(row['count']),
                'lost_days': int(row.get('lost_days', 0)),
                'fatalities': fatalities_count
            }
        return result
    
    # Calcula total de fatais baseado em type == 'fatal'
    total_fatalities = len(accidents_df[accidents_df['type'] == 'fatal']) if 'type' in accidents_df.columns else 0
    
    return {
        'by_type': format_analysis(type_analysis, 'by_type'),
        'by_classification': format_analysis(classification_analysis, 'by_classification', 'classification'),
        'by_body_part': format_analysis(body_part_analysis, 'by_body_part', 'body_part'),
        'by_root_cause': format_analysis(root_cause_analysis, 'by_root_cause', 'root_cause'),
        'temporal': format_analysis(temporal_analysis, 'temporal', 'year_month'),
        'total_accidents': len(accidents_df),
        'total_fatalities': total_fatalities,
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


def save_hours_worked(user_id: str, year: int, month: int, hours: float) -> Dict[str, Any]:
    """Salva ou atualiza horas trabalhadas do usuário para o mês."""
    from managers.supabase_config import get_service_role_client

    if not user_id:
        return {"ok": False, "error": "Usuário não autenticado"}
    if hours is None or float(hours) <= 0:
        return {"ok": False, "error": "Informe um total de horas maior que zero"}
    if month < 1 or month > 12:
        return {"ok": False, "error": "Mês inválido"}

    supabase = get_service_role_client()
    hours_value = float(hours)
    existing = (
        supabase.table("hours_worked_monthly")
        .select("id")
        .eq("created_by", user_id)
        .eq("year", int(year))
        .eq("month", int(month))
        .execute()
    )

    if existing.data:
        supabase.table("hours_worked_monthly").update({"hours": hours_value}).eq(
            "id", existing.data[0]["id"]
        ).execute()
        action = "updated"
    else:
        supabase.table("hours_worked_monthly").insert(
            {
                "year": int(year),
                "month": int(month),
                "hours": hours_value,
                "created_by": user_id,
            }
        ).execute()
        action = "created"

    return {
        "ok": True,
        "action": action,
        "year": int(year),
        "month": int(month),
        "hours": hours_value,
    }


def recalculate_user_kpis(user_id: str) -> Dict[str, Any]:
    """
    Recalcula KPIs mensais do usuário a partir de acidentes + horas trabalhadas.
    Horas em hours_worked_monthly estão em horas reais; kpi_monthly.hours em centenas.
    """
    from collections import defaultdict
    from managers.supabase_config import get_service_role_client

    if not user_id:
        return {"ok": False, "error": "Usuário não autenticado", "kpi_count": 0}

    supabase = get_service_role_client()

    accidents_response = (
        supabase.table("accidents")
        .select("id, occurred_at, created_by, lost_days, type")
        .eq("created_by", user_id)
        .execute()
    )
    hours_response = (
        supabase.table("hours_worked_monthly")
        .select("id, year, month, hours, created_by")
        .eq("created_by", user_id)
        .execute()
    )

    accidents_data = accidents_response.data or []
    hours_data = hours_response.data or []

    if not hours_data:
        return {
            "ok": False,
            "error": "Cadastre horas trabalhadas para calcular KPIs",
            "kpi_count": 0,
            "accidents": len(accidents_data),
            "hours_records": 0,
        }

    accidents_by_period = defaultdict(lambda: {"count": 0, "fatalities": 0, "lost_days": 0})
    for accident in accidents_data:
        if not accident.get("occurred_at"):
            continue
        period = pd.to_datetime(accident["occurred_at"]).strftime("%Y-%m")
        accidents_by_period[period]["count"] += 1
        if accident.get("type") == "fatal":
            accidents_by_period[period]["fatalities"] += 1
        accidents_by_period[period]["lost_days"] += int(accident.get("lost_days") or 0)

    hours_by_period = defaultdict(float)
    for hour_entry in hours_data:
        period = f"{hour_entry['year']}-{str(hour_entry['month']).zfill(2)}"
        hours_by_period[period] += float(hour_entry.get("hours") or 0)

    kpi_count = 0
    periods_with_accidents = 0

    for period, acc_data in accidents_by_period.items():
        if period not in hours_by_period:
            continue
        periods_with_accidents += 1
        hours = hours_by_period[period]
        debited_days = acc_data["fatalities"] * 6000
        hours_in_hundreds = hours / 100
        freq_rate = calculate_frequency_rate(acc_data["count"], hours_in_hundreds)
        sev_rate = calculate_severity_rate(acc_data["lost_days"], hours_in_hundreds, debited_days)

        kpi_data = {
            "period": f"{period}-01",
            "created_by": user_id,
            "accidents_total": acc_data["count"],
            "fatalities": acc_data["fatalities"],
            "lost_days_total": acc_data["lost_days"],
            "hours": hours_in_hundreds,
            "frequency_rate": freq_rate,
            "severity_rate": sev_rate,
            "debited_days": debited_days,
        }

        existing_kpi = (
            supabase.table("kpi_monthly")
            .select("id")
            .eq("period", f"{period}-01")
            .eq("created_by", user_id)
            .execute()
        )
        if existing_kpi.data:
            supabase.table("kpi_monthly").update(kpi_data).eq("period", f"{period}-01").eq(
                "created_by", user_id
            ).execute()
        else:
            supabase.table("kpi_monthly").insert(kpi_data).execute()
        kpi_count += 1

    periods_hours_only = 0
    for period, hours in hours_by_period.items():
        if period in accidents_by_period:
            continue
        periods_hours_only += 1
        existing_kpi = (
            supabase.table("kpi_monthly")
            .select("id")
            .eq("period", f"{period}-01")
            .eq("created_by", user_id)
            .execute()
        )
        kpi_data = {
            "period": f"{period}-01",
            "created_by": user_id,
            "accidents_total": 0,
            "fatalities": 0,
            "lost_days_total": 0,
            "hours": hours / 100,
            "frequency_rate": 0,
            "severity_rate": 0,
            "debited_days": 0,
        }
        if existing_kpi.data:
            supabase.table("kpi_monthly").update(kpi_data).eq("period", f"{period}-01").eq(
                "created_by", user_id
            ).execute()
        else:
            supabase.table("kpi_monthly").insert(kpi_data).execute()
        kpi_count += 1

    return {
        "ok": True,
        "kpi_count": kpi_count,
        "periods_with_accidents": periods_with_accidents,
        "periods_hours_only": periods_hours_only,
        "accidents": len(accidents_data),
        "hours_records": len(hours_data),
        "missing_hours_periods": sorted(set(accidents_by_period.keys()) - set(hours_by_period.keys())),
    }