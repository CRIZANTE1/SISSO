-- Script para limpar dados de um usuário específico
-- Substitua 'bboycrysforever@gmail.com' pelo email do usuário desejado

-- ⚠️ ATENÇÃO: Este script irá remover TODOS os dados do usuário especificado
-- Certifique-se de que o email está correto antes de executar

-- 1. Definir o email do usuário a ser limpo
-- (Altere aqui o email se necessário)
\set user_email 'bboycrysforever@gmail.com'

-- 2. Verificar dados existentes antes da limpeza
SELECT 'ANTES DA LIMPEZA' as status, 
       'accidents' as tabela, COUNT(*) as total 
FROM public.accidents WHERE created_by = :'user_email'
UNION ALL
SELECT 'ANTES DA LIMPEZA' as status,
       'near_misses' as tabela, COUNT(*) as total 
FROM public.near_misses WHERE created_by = :'user_email'
UNION ALL
SELECT 'ANTES DA LIMPEZA' as status,
       'nonconformities' as tabela, COUNT(*) as total 
FROM public.nonconformities WHERE created_by = :'user_email'
UNION ALL
SELECT 'ANTES DA LIMPEZA' as status,
       'hours_worked_monthly' as tabela, COUNT(*) as total 
FROM public.hours_worked_monthly WHERE created_by = :'user_email';

-- 3. Remover dados do usuário (em ordem de dependência)

-- 3.1. Remover anexos/evidências primeiro
DELETE FROM public.attachments 
WHERE uploaded_by = :'user_email';

-- 3.2. Remover ações 5W2H
DELETE FROM public.actions 
WHERE created_by = :'user_email';

-- 3.3. Remover acidentes
DELETE FROM public.accidents 
WHERE created_by = :'user_email';

-- 3.4. Remover quase-acidentes
DELETE FROM public.near_misses 
WHERE created_by = :'user_email';

-- 3.5. Remover não conformidades
DELETE FROM public.nonconformities 
WHERE created_by = :'user_email';

-- 3.6. Remover horas trabalhadas mensais
DELETE FROM public.hours_worked_monthly 
WHERE created_by = :'user_email';

-- 4. Verificar dados após a limpeza
SELECT 'APÓS A LIMPEZA' as status, 
       'accidents' as tabela, COUNT(*) as total 
FROM public.accidents WHERE created_by = :'user_email'
UNION ALL
SELECT 'APÓS A LIMPEZA' as status,
       'near_misses' as tabela, COUNT(*) as total 
FROM public.near_misses WHERE created_by = :'user_email'
UNION ALL
SELECT 'APÓS A LIMPEZA' as status,
       'nonconformities' as tabela, COUNT(*) as total 
FROM public.nonconformities WHERE created_by = :'user_email'
UNION ALL
SELECT 'APÓS A LIMPEZA' as status,
       'hours_worked_monthly' as tabela, COUNT(*) as total 
FROM public.hours_worked_monthly WHERE created_by = :'user_email';

-- 5. Verificar se o perfil do usuário ainda existe
SELECT 'PERFIL DO USUÁRIO' as status,
       'profiles' as tabela, COUNT(*) as total
FROM public.profiles WHERE email = :'user_email';

-- 6. Resumo da limpeza
SELECT 
    'LIMPEZA CONCLUÍDA' as status,
    'Todos os dados do usuário foram removidos' as mensagem,
    'O perfil do usuário foi mantido' as observacao;
