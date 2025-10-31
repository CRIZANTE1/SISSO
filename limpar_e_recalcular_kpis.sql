-- =============================================
-- Script para Limpar KPIs Antigos e Recalcular
-- =============================================
-- 
-- Este script limpa os KPIs antigos calculados incorretamente
-- Depois disso, você deve recalcular usando o botão "Recalcular KPIs"
-- na página Admin → Dados Básicos
--
-- =============================================

-- Limpa todos os KPIs do usuário (ou remove o WHERE para limpar todos)
DELETE FROM public.kpi_monthly 
WHERE created_by = 'd88fd010-c11f-4e0a-9491-7a13f5577e8f';

-- Verifica se a limpeza foi feita
SELECT 
    COUNT(*) as kpis_restantes,
    CASE 
        WHEN COUNT(*) = 0 THEN '✅ Tabela limpa com sucesso!'
        ELSE '⚠️ Ainda há KPIs na tabela'
    END as status
FROM public.kpi_monthly
WHERE created_by = 'd88fd010-c11f-4e0a-9491-7a13f5577e8f';

-- Verifica se há horas trabalhadas para calcular
SELECT 
    COUNT(*) as total_periodos_com_horas,
    SUM(hours) as total_horas_reais,
    MIN(year || '-' || LPAD(month::text, 2, '0') || '-01') as periodo_mais_antigo,
    MAX(year || '-' || LPAD(month::text, 2, '0') || '-01') as periodo_mais_recente
FROM public.hours_worked_monthly
WHERE created_by = 'd88fd010-c11f-4e0a-9491-7a13f5577e8f';

-- Verifica se há acidentes para calcular
SELECT 
    COUNT(*) as total_acidentes,
    SUM(CASE WHEN type != 'sem_lesao' THEN 1 ELSE 0 END) as acidentes_com_lesao,
    SUM(lost_days) as total_dias_perdidos,
    SUM(CASE WHEN type = 'fatal' THEN 1 ELSE 0 END) as total_fatais,
    MIN(occurred_at) as acidente_mais_antigo,
    MAX(occurred_at) as acidente_mais_recente
FROM public.accidents
WHERE created_by = 'd88fd010-c11f-4e0a-9491-7a13f5577e8f';

