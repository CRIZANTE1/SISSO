-- =============================================
-- Script para Verificar Formato das Horas
-- =============================================
-- 
-- Este script ajuda a entender como as horas estão sendo armazenadas
--
-- =============================================

-- 1. Verifica horas trabalhadas ORIGINAIS (tabela hours_worked_monthly)
SELECT 
    'hours_worked_monthly' as tabela,
    year,
    month,
    hours as horas_na_tabela,
    hours as horas_interpretacao_1,  -- Se forem horas reais diretas
    hours * 100 as horas_interpretacao_2,  -- Se forem em centenas
    DATE(year || '-' || LPAD(month::text, 2, '0') || '-01') as periodo
FROM public.hours_worked_monthly
WHERE created_by = 'd88fd010-c11f-4e0a-9491-7a13f5577e8f'
ORDER BY year, month;

-- 2. Verifica horas nos KPIs calculados (tabela kpi_monthly)
SELECT 
    'kpi_monthly' as tabela,
    period,
    hours as horas_na_tabela,
    hours * 100 as horas_interpretacao_1,  -- Multiplicando por 100 uma vez
    hours * 100 * 100 as horas_interpretacao_2,  -- Multiplicando por 100 duas vezes
    accidents_total,
    frequency_rate,
    CASE 
        WHEN hours > 0 THEN (accidents_total::numeric / (hours * 100)) * 1000000
        ELSE 0
    END as tf_com_interpretacao_1,
    CASE 
        WHEN hours > 0 THEN (accidents_total::numeric / (hours * 100 * 100)) * 1000000
        ELSE 0
    END as tf_com_interpretacao_2
FROM public.kpi_monthly
WHERE created_by = 'd88fd010-c11f-4e0a-9491-7a13f5577e8f'
AND accidents_total > 0
ORDER BY period;

-- 3. Compara acidentes com horas do mesmo período
SELECT 
    DATE_TRUNC('month', a.occurred_at) as periodo,
    COUNT(*) as acidentes,
    h.hours as horas_na_tabela_original,
    h.hours * 100 as horas_se_em_centenas,
    h.hours as horas_se_reais,
    -- Calcula TF com ambas interpretações
    CASE 
        WHEN h.hours > 0 THEN (COUNT(*)::numeric / (h.hours * 100)) * 1000000
        ELSE 0
    END as tf_se_horas_em_centenas,
    CASE 
        WHEN h.hours > 0 THEN (COUNT(*)::numeric / h.hours) * 1000000
        ELSE 0
    END as tf_se_horas_reais
FROM public.accidents a
LEFT JOIN public.hours_worked_monthly h ON 
    DATE_TRUNC('month', a.occurred_at) = DATE(h.year || '-' || LPAD(h.month::text, 2, '0') || '-01')
    AND a.created_by = h.created_by
WHERE a.created_by = 'd88fd010-c11f-4e0a-9491-7a13f5577e8f'
    AND h.created_by = 'd88fd010-c11f-4e0a-9491-7a13f5577e8f'
GROUP BY DATE_TRUNC('month', a.occurred_at), h.hours
ORDER BY periodo;

