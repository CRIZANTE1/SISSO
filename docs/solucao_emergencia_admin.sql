-- =============================================
-- SOLUÇÃO DE EMERGÊNCIA: Acesso do Admin
-- =============================================

-- Execute este script no SQL Editor do Supabase para resolver o problema

-- 1. DESABILITAR RLS temporariamente
ALTER TABLE profiles DISABLE ROW LEVEL SECURITY;

-- 2. Criar/atualizar perfil do admin
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
    'PERFIL CRIADO' as status,
    email,
    full_name,
    role,
    status,
    created_at
FROM profiles 
WHERE email = 'bboycrysforever@gmail.com';

-- 4. REABILITAR RLS
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- 5. Criar políticas corretas
-- 5.1. Remover políticas antigas
DROP POLICY IF EXISTS "Users can view their own profile" ON profiles;
DROP POLICY IF EXISTS "Admins can view all profiles" ON profiles;
DROP POLICY IF EXISTS "Admins can manage all profiles" ON profiles;

-- 5.2. Criar políticas corretas
CREATE POLICY "Users can view their own profile" ON profiles
    FOR SELECT USING (auth.jwt() ->> 'email' = email);

CREATE POLICY "Admins can view all profiles" ON profiles
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE email = auth.jwt() ->> 'email'
            AND role = 'admin'
        )
    );

CREATE POLICY "Admins can manage all profiles" ON profiles
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE email = auth.jwt() ->> 'email'
            AND role = 'admin'
        )
    );

-- 6. Verificar políticas
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

-- 7. Teste final
SELECT 
    'TESTE FINAL' as status,
    email,
    role,
    status
FROM profiles 
WHERE email = 'bboycrysforever@gmail.com';

-- 8. Mensagem de sucesso
DO $$
BEGIN
    RAISE NOTICE '✅ SOLUÇÃO APLICADA COM SUCESSO!';
    RAISE NOTICE '✅ Perfil do admin criado/atualizado';
    RAISE NOTICE '✅ Políticas RLS corrigidas';
    RAISE NOTICE '✅ Sistema pronto para uso';
    RAISE NOTICE '🔑 Tente fazer login novamente';
END $$;
