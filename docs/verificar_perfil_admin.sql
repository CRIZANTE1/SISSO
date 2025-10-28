-- =============================================
-- VERIFICAÇÃO E CORREÇÃO: Perfil do Administrador
-- =============================================

-- Email do usuário: bboycrysforever@gmail.com
-- Problema: Usuário cadastrado como admin mas sistema não encontra

-- 1. Verificar se o perfil existe
SELECT 
    'VERIFICAÇÃO INICIAL' as status,
    email,
    full_name,
    role,
    status,
    created_at
FROM profiles 
WHERE email = 'bboycrysforever@gmail.com';

-- 2. Verificar se há perfis com email similar (case sensitivity)
SELECT 
    'BUSCA SIMILAR' as status,
    email,
    full_name,
    role,
    status
FROM profiles 
WHERE LOWER(email) = LOWER('bboycrysforever@gmail.com');

-- 3. Listar todos os perfis para debug
SELECT 
    'TODOS OS PERFIS' as status,
    email,
    role,
    status
FROM profiles 
ORDER BY created_at DESC;

-- 4. Verificar estrutura da tabela profiles
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'profiles' 
ORDER BY ordinal_position;

-- 5. Se o perfil não existir, criar um novo
-- Descomente as linhas abaixo se necessário:

/*
INSERT INTO profiles (
    email,
    full_name,
    role,
    status,
    created_at,
    updated_at
) VALUES (
    'bboycrysforever@gmail.com',
    'Cristian Ferreira',
    'admin',
    'ativo',
    NOW(),
    NOW()
) ON CONFLICT (email) DO UPDATE SET
    full_name = EXCLUDED.full_name,
    role = EXCLUDED.role,
    status = EXCLUDED.status,
    updated_at = NOW();
*/

-- 6. Verificar se a inserção funcionou
-- SELECT * FROM profiles WHERE email = 'bboycrysforever@gmail.com';

-- 7. Verificar políticas RLS
SELECT 
    policyname,
    cmd,
    with_check
FROM pg_policies 
WHERE schemaname = 'public' 
AND tablename = 'profiles'
ORDER BY policyname;

-- 8. Teste de acesso (opcional)
-- SELECT * FROM profiles WHERE email = 'bboycrysforever@gmail.com';
