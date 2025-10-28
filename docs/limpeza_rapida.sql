-- Limpeza rápida de dados fictícios
-- Execute este script no SQL Editor do Supabase

-- Remover todos os dados do usuário de teste
DELETE FROM public.attachments WHERE uploaded_by = 'bboycrysforever@gmail.com';
DELETE FROM public.actions WHERE created_by = 'bboycrysforever@gmail.com';
DELETE FROM public.accidents WHERE created_by = 'bboycrysforever@gmail.com';
DELETE FROM public.near_misses WHERE created_by = 'bboycrysforever@gmail.com';
DELETE FROM public.nonconformities WHERE created_by = 'bboycrysforever@gmail.com';
DELETE FROM public.hours_worked_monthly WHERE created_by = 'bboycrysforever@gmail.com';

-- Verificar limpeza
SELECT 'DADOS REMOVIDOS' as status, 
       'accidents' as tabela, COUNT(*) as total 
FROM public.accidents WHERE created_by = 'bboycrysforever@gmail.com'
UNION ALL
SELECT 'DADOS REMOVIDOS' as status,
       'near_misses' as tabela, COUNT(*) as total 
FROM public.near_misses WHERE created_by = 'bboycrysforever@gmail.com'
UNION ALL
SELECT 'DADOS REMOVIDOS' as status,
       'nonconformities' as tabela, COUNT(*) as total 
FROM public.nonconformities WHERE created_by = 'bboycrysforever@gmail.com'
UNION ALL
SELECT 'DADOS REMOVIDOS' as status,
       'hours_worked_monthly' as tabela, COUNT(*) as total 
FROM public.hours_worked_monthly WHERE created_by = 'bboycrysforever@gmail.com';
