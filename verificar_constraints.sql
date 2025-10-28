-- Script para verificar constraints e dados
-- Execute este script no SQL Editor do Supabase para verificar se os dados estão corretos

-- 1. Verificar constraint da tabela nonconformities
SELECT 
    conname as constraint_name,
    pg_get_constraintdef(oid) as constraint_definition
FROM pg_constraint 
WHERE conrelid = 'public.nonconformities'::regclass 
AND conname LIKE '%severity%';

-- 2. Verificar valores únicos de severity na tabela nonconformities
SELECT DISTINCT severity, COUNT(*) as count
FROM public.nonconformities 
GROUP BY severity
ORDER BY severity;

-- 3. Verificar valores únicos de potential_severity na tabela near_misses
SELECT DISTINCT potential_severity, COUNT(*) as count
FROM public.near_misses 
GROUP BY potential_severity
ORDER BY potential_severity;

-- 4. Testar inserção de dados com valores corretos
-- (Execute apenas se quiser testar)
/*
INSERT INTO public.nonconformities (
    opened_at,
    standard_ref,
    severity,
    description,
    status,
    created_by
) VALUES 
    ('2024-12-20', 'NR-35', 'leve', 'Teste de constraint', 'aberta', 'bboycrysforever@gmail.com');
*/

-- 5. Verificar se há dados com valores incorretos (deve retornar 0 linhas)
SELECT * FROM public.nonconformities 
WHERE severity NOT IN ('leve','moderada','grave','critica');

-- 6. Contar total de registros por tabela
SELECT 'nonconformities' as tabela, COUNT(*) as total FROM public.nonconformities WHERE created_by = 'bboycrysforever@gmail.com'
UNION ALL
SELECT 'near_misses' as tabela, COUNT(*) as total FROM public.near_misses WHERE created_by = 'bboycrysforever@gmail.com'
UNION ALL
SELECT 'accidents' as tabela, COUNT(*) as total FROM public.accidents WHERE created_by = 'bboycrysforever@gmail.com';
