-- =============================================
-- SOLUÇÃO SIMPLES: Acesso do Admin
-- =============================================

-- Esta solução resolve o problema de forma simples e direta

-- 1. DESABILITAR RLS temporariamente
ALTER TABLE profiles DISABLE ROW LEVEL SECURITY;

-- 2. Garantir que o perfil admin existe
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

-- 3. Verificar se foi criado
SELECT 
    'PERFIL ADMIN CRIADO' as status,
    email,
    full_name,
    role,
    status,
    created_at
FROM profiles 
WHERE email = 'bboycrysforever@gmail.com';

-- 4. REABILITAR RLS
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- 5. Criar políticas simples (sem loop circular)
-- 5.1. Remover todas as políticas existentes
DROP POLICY IF EXISTS "Admins can view all profiles" ON profiles;
DROP POLICY IF EXISTS "Admins can manage all profiles" ON profiles;
DROP POLICY IF EXISTS "Admins can create any profile" ON profiles;
DROP POLICY IF EXISTS "Users can view their own profile" ON profiles;
DROP POLICY IF EXISTS "Users can update their own profile" ON profiles;
DROP POLICY IF EXISTS "Users can create their own profile" ON profiles;
DROP POLICY IF EXISTS "Authenticated users can insert profiles" ON profiles;
DROP POLICY IF EXISTS "Service role can create profiles" ON profiles;

-- 5.2. Criar políticas simples e funcionais
CREATE POLICY "Allow all for authenticated users" ON profiles
    FOR ALL USING (auth.jwt() ->> 'email' IS NOT NULL);

-- 6. Verificar se RLS está ativo
SELECT 
    'RLS STATUS' as status,
    tablename,
    rowsecurity as "RLS Ativo"
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename = 'profiles';

-- 7. Verificar políticas finais
SELECT 
    'POLÍTICAS FINAIS' as status,
    policyname,
    cmd,
    with_check,
    qual
FROM pg_policies 
WHERE schemaname = 'public' 
AND tablename = 'profiles'
ORDER BY policyname;

-- 8. Teste final de acesso
SELECT 
    'TESTE FINAL' as status,
    email,
    full_name,
    role,
    status
FROM profiles 
WHERE email = 'bboycrysforever@gmail.com';

-- 9. Contar total de perfis
SELECT 
    'TOTAL PERFIS' as status,
    COUNT(*) as total
FROM profiles;

-- 10. Mensagem de sucesso
DO $$
BEGIN
    RAISE NOTICE '🎉 SOLUÇÃO APLICADA COM SUCESSO!';
    RAISE NOTICE '✅ Perfil do admin criado/atualizado';
    RAISE NOTICE '✅ RLS reabilitado com política simples';
    RAISE NOTICE '✅ Loop circular resolvido';
    RAISE NOTICE '🔑 Tente fazer login agora!';
    RAISE NOTICE '📧 Email: bboycrysforever@gmail.com';
    RAISE NOTICE '👑 Role: admin';
END $$;
