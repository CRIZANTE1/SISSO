-- =============================================
-- CRIAÇÃO DE EMERGÊNCIA: Perfil Administrador
-- =============================================

-- Execute este script se o usuário admin não conseguir acessar

-- 1. Remover perfil existente (se houver)
DELETE FROM profiles WHERE email = 'bboycrysforever@gmail.com';

-- 2. Criar perfil admin
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
);

-- 3. Verificar se foi criado
SELECT 
    'PERFIL CRIADO' as status,
    email,
    full_name,
    role,
    status,
    created_at
FROM profiles 
WHERE email = 'bboycrysforever@gmail.com';

-- 4. Verificar se RLS está configurado corretamente
SELECT 
    'VERIFICAÇÃO RLS' as status,
    policyname,
    cmd,
    with_check
FROM pg_policies 
WHERE schemaname = 'public' 
AND tablename = 'profiles'
ORDER BY policyname;

-- 5. Teste de acesso
SELECT 
    'TESTE DE ACESSO' as status,
    COUNT(*) as total_perfis
FROM profiles;
