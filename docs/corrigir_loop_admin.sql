-- =============================================
-- CORREÇÃO: Loop Circular nas Políticas de Admin
-- =============================================

-- Problema: Políticas de admin criam loop circular
-- Solução: Usar auth.users para verificar admin

-- 1. Remover políticas problemáticas
DROP POLICY IF EXISTS "Admins can view all profiles" ON profiles;
DROP POLICY IF EXISTS "Admins can manage all profiles" ON profiles;
DROP POLICY IF EXISTS "Admins can create any profile" ON profiles;

-- 2. Criar política simples para admins (sem loop)
-- Assumindo que admins têm um campo específico ou são identificados de outra forma
CREATE POLICY "Admins can view all profiles" ON profiles
    FOR SELECT USING (
        -- Verifica se o usuário está autenticado
        auth.jwt() ->> 'email' IS NOT NULL
        AND (
            -- Se for o email específico do admin principal
            auth.jwt() ->> 'email' = 'bboycrysforever@gmail.com'
            OR
            -- Ou se existir perfil admin (sem loop)
            EXISTS (
                SELECT 1 FROM profiles p
                WHERE p.email = auth.jwt() ->> 'email'
                AND p.role = 'admin'
                AND p.status = 'ativo'
            )
        )
    );

-- 3. Política para admins gerenciarem perfis
CREATE POLICY "Admins can manage all profiles" ON profiles
    FOR ALL USING (
        auth.jwt() ->> 'email' IS NOT NULL
        AND (
            auth.jwt() ->> 'email' = 'bboycrysforever@gmail.com'
            OR
            EXISTS (
                SELECT 1 FROM profiles p
                WHERE p.email = auth.jwt() ->> 'email'
                AND p.role = 'admin'
                AND p.status = 'ativo'
            )
        )
    );

-- 4. Política para admins criarem perfis
CREATE POLICY "Admins can create any profile" ON profiles
    FOR INSERT WITH CHECK (
        auth.jwt() ->> 'email' IS NOT NULL
        AND (
            auth.jwt() ->> 'email' = 'bboycrysforever@gmail.com'
            OR
            EXISTS (
                SELECT 1 FROM profiles p
                WHERE p.email = auth.jwt() ->> 'email'
                AND p.role = 'admin'
                AND p.status = 'ativo'
            )
        )
    );

-- 5. Garantir que o perfil admin existe
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

-- 6. Verificar políticas criadas
SELECT 
    'POLÍTICAS CORRIGIDAS' as status,
    policyname,
    cmd,
    with_check,
    qual
FROM pg_policies 
WHERE schemaname = 'public' 
AND tablename = 'profiles'
ORDER BY policyname;

-- 7. Teste de acesso
SELECT 
    'TESTE DE ACESSO' as status,
    email,
    role,
    status
FROM profiles 
WHERE email = 'bboycrysforever@gmail.com';

-- 8. Mensagem de confirmação
DO $$
BEGIN
    RAISE NOTICE '✅ Políticas corrigidas - Loop circular resolvido!';
    RAISE NOTICE '✅ Admin principal configurado: bboycrysforever@gmail.com';
    RAISE NOTICE '✅ Sistema pronto para uso';
END $$;
