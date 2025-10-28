-- Script para limpar dados fictícios inseridos para análise
-- Execute este script no SQL Editor do Supabase para remover os dados de teste

-- ⚠️ ATENÇÃO: Este script irá remover TODOS os dados do usuário 'bboycrysforever@gmail.com'
-- Certifique-se de que este é o usuário correto antes de executar

-- 1. Verificar dados existentes antes da limpeza
SELECT 'ANTES DA LIMPEZA' as status, 
       'accidents' as tabela, COUNT(*) as total 
FROM public.accidents WHERE created_by = 'bboycrysforever@gmail.com'
UNION ALL
SELECT 'ANTES DA LIMPEZA' as status,
       'near_misses' as tabela, COUNT(*) as total 
FROM public.near_misses WHERE created_by = 'bboycrysforever@gmail.com'
UNION ALL
SELECT 'ANTES DA LIMPEZA' as status,
       'nonconformities' as tabela, COUNT(*) as total 
FROM public.nonconformities WHERE created_by = 'bboycrysforever@gmail.com'
UNION ALL
SELECT 'ANTES DA LIMPEZA' as status,
       'hours_worked_monthly' as tabela, COUNT(*) as total 
FROM public.hours_worked_monthly WHERE created_by = 'bboycrysforever@gmail.com';

-- 2. Remover dados fictícios (em ordem de dependência)

-- 2.1. Remover anexos/evidências primeiro (se existirem)
DELETE FROM public.attachments 
WHERE uploaded_by = 'bboycrysforever@gmail.com';

-- 2.2. Remover ações 5W2H (se existirem)
DELETE FROM public.actions 
WHERE created_by = 'bboycrysforever@gmail.com';

-- 2.3. Remover acidentes
DELETE FROM public.accidents 
WHERE created_by = 'bboycrysforever@gmail.com';

-- 2.4. Remover quase-acidentes
DELETE FROM public.near_misses 
WHERE created_by = 'bboycrysforever@gmail.com';

-- 2.5. Remover não conformidades
DELETE FROM public.nonconformities 
WHERE created_by = 'bboycrysforever@gmail.com';

-- 2.6. Remover horas trabalhadas mensais
DELETE FROM public.hours_worked_monthly 
WHERE created_by = 'bboycrysforever@gmail.com';

-- 3. Verificar dados após a limpeza
SELECT 'APÓS A LIMPEZA' as status, 
       'accidents' as tabela, COUNT(*) as total 
FROM public.accidents WHERE created_by = 'bboycrysforever@gmail.com'
UNION ALL
SELECT 'APÓS A LIMPEZA' as status,
       'near_misses' as tabela, COUNT(*) as total 
FROM public.near_misses WHERE created_by = 'bboycrysforever@gmail.com'
UNION ALL
SELECT 'APÓS A LIMPEZA' as status,
       'nonconformities' as tabela, COUNT(*) as total 
FROM public.nonconformities WHERE created_by = 'bboycrysforever@gmail.com'
UNION ALL
SELECT 'APÓS A LIMPEZA' as status,
       'hours_worked_monthly' as tabela, COUNT(*) as total 
FROM public.hours_worked_monthly WHERE created_by = 'bboycrysforever@gmail.com';

-- 4. Verificar se o perfil do usuário ainda existe (não será removido)
SELECT 'PERFIL DO USUÁRIO' as status,
       'profiles' as tabela, COUNT(*) as total
FROM public.profiles WHERE email = 'bboycrysforever@gmail.com';

-- 5. Resumo da limpeza
SELECT 
    'LIMPEZA CONCLUÍDA' as status,
    'Todos os dados fictícios foram removidos' as mensagem,
    'O perfil do usuário foi mantido' as observacao;
