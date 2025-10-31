-- =============================================
-- Script para Verificar Dados para Cálculo de KPIs
-- =============================================
-- 
-- Este script verifica se há dados suficientes para calcular KPIs
--
-- =============================================

-- 1. Verifica se há acidentes
SELECT 
    'ACCIDENTES' AS tipo_dado,
    COUNT(*) AS total_registros,
    COUNT(DISTINCT created_by) AS usuarios_diferentes,
    MIN(occurred_at) AS data_mais_antiga,
    MAX(occurred_at) AS data_mais_recente
FROM public.accidents;

-- 2. Verifica se há horas trabalhadas
SELECT 
    'HORAS_TRABALHADAS' AS tipo_dado,
    COUNT(*) AS total_registros,
    COUNT(DISTINCT created_by) AS usuarios_diferentes,
    MIN(year || '-' || LPAD(month::text, 2, '0') || '-01') AS periodo_mais_antigo,
    MAX(year || '-' || LPAD(month::text, 2, '0') || '-01') AS periodo_mais_recente,
    SUM(hours) AS total_horas
FROM public.hours_worked_monthly;

-- 3. Verifica se há KPIs calculados
SELECT 
    'KPIS_CALCULADOS' AS tipo_dado,
    COUNT(*) AS total_registros,
    COUNT(DISTINCT created_by) AS usuarios_diferentes,
    MIN(period) AS periodo_mais_antigo,
    MAX(period) AS periodo_mais_recente
FROM public.kpi_monthly;

-- 4. Verifica períodos que têm acidentes mas não têm horas
SELECT 
    'PERIODOS_SEM_HORAS' AS tipo_dado,
    DATE_TRUNC('month', occurred_at) AS periodo,
    COUNT(*) AS acidentes,
    created_by
FROM public.accidents
WHERE DATE_TRUNC('month', occurred_at) NOT IN (
    SELECT DATE(year || '-' || LPAD(month::text, 2, '0') || '-01')
    FROM public.hours_worked_monthly
    WHERE created_by = accidents.created_by
)
GROUP BY DATE_TRUNC('month', occurred_at), created_by
ORDER BY periodo DESC
LIMIT 10;

-- 5. Verifica períodos que têm horas mas não têm acidentes
SELECT 
    'PERIODOS_SEM_ACIDENTES' AS tipo_dado,
    DATE(year || '-' || LPAD(month::text, 2, '0') || '-01') AS periodo,
    SUM(hours) AS horas,
    created_by
FROM public.hours_worked_monthly
WHERE DATE(year || '-' || LPAD(month::text, 2, '0') || '-01') NOT IN (
    SELECT DATE_TRUNC('month', occurred_at)
    FROM public.accidents
    WHERE created_by = hours_worked_monthly.created_by
)
GROUP BY DATE(year || '-' || LPAD(month::text, 2, '0') || '-01'), created_by
ORDER BY periodo DESC
LIMIT 10;

