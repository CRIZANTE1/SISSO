-- =============================================
-- Diagnóstico do Cálculo de KPIs
-- =============================================

-- 1. Verifica dados na tabela kpi_monthly
SELECT 
    COUNT(*) as total_periodos,
    SUM(accidents_total) as total_acidentes_calculado,
    SUM(lost_days_total) as total_dias_perdidos_calculado,
    SUM(fatalities) as total_fatais_calculado,
    SUM(debited_days) as total_debitados_calculado,
    SUM(hours) as total_horas_em_centenas,
    SUM(hours) * 100 as total_horas_reais,
    -- Taxa acumulada correta
    -- ✅ CORRIGIDO: hours na tabela está em centenas (176.0 = 17.600 horas reais)
    (SUM(accidents_total)::numeric / (SUM(hours) * 100)) * 1000000 as tf_correta,
    ((SUM(lost_days_total) + SUM(debited_days))::numeric / (SUM(hours) * 100)) * 1000000 as tg_correta,
    -- Média das taxas (ERRADA quando horas variam)
    AVG(frequency_rate) as tf_media_simples_errada,
    AVG(severity_rate) as tg_media_simples_errada
FROM public.kpi_monthly
WHERE created_by = 'd88fd010-c11f-4e0a-9491-7a13f5577e8f';

-- 2. Lista taxas por período
SELECT 
    period,
    accidents_total,
    lost_days_total,
    fatalities,
    debited_days,
    hours,
    hours * 100 as horas_reais,
    frequency_rate as tf_periodo,
    severity_rate as tg_periodo,
    -- Taxa correta para este período
    -- ✅ CORRIGIDO: hours na tabela está em centenas (176.0 = 176 centenas = 17.600 horas reais)
    -- Precisa multiplicar por 100 para converter para horas reais
    CASE 
        WHEN hours > 0 THEN (accidents_total::numeric / (hours * 100)) * 1000000
        ELSE 0
    END as tf_periodo_correta,
    CASE 
        WHEN hours > 0 THEN ((lost_days_total + debited_days)::numeric / (hours * 100)) * 1000000
        ELSE 0
    END as tg_periodo_correta
FROM public.kpi_monthly
WHERE created_by = 'd88fd010-c11f-4e0a-9491-7a13f5577e8f'
ORDER BY period;

-- 3. Compara taxas calculadas vs corretas
SELECT 
    period,
    frequency_rate as tf_calculada_tabela,
    CASE 
        WHEN hours > 0 THEN (accidents_total::numeric / (hours * 100)) * 1000000
        ELSE 0
    END as tf_correta,
    ABS(frequency_rate - CASE 
        WHEN hours > 0 THEN (accidents_total::numeric / (hours * 100)) * 1000000
        ELSE 0
    END) as diferenca_tf,
    severity_rate as tg_calculada_tabela,
    CASE 
        WHEN hours > 0 THEN ((lost_days_total + debited_days)::numeric / (hours * 100)) * 1000000
        ELSE 0
    END as tg_correta,
    ABS(severity_rate - CASE 
        WHEN hours > 0 THEN ((lost_days_total + debited_days)::numeric / (hours * 100)) * 1000000
        ELSE 0
    END) as diferenca_tg
FROM public.kpi_monthly
WHERE created_by = 'd88fd010-c11f-4e0a-9491-7a13f5577e8f'
ORDER BY period;

