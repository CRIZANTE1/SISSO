-- =============================================
-- CORREÇÃO: Políticas RLS da tabela profiles
-- =============================================

-- Problema: Políticas de SELECT sem restrição adequada
-- Solução: Corrigir políticas para permitir acesso correto

-- 1. Remover políticas problemáticas
DROP POLICY IF EXISTS "Users can view their own profile" ON profiles;
DROP POLICY IF EXISTS "Admins can view all profiles" ON profiles;
DROP POLICY IF EXISTS "Admins can manage all profiles" ON profiles;

-- 2. Criar política correta para usuários visualizarem seus próprios perfis
CREATE POLICY "Users can view their own profile" ON profiles
    FOR SELECT USING (auth.jwt() ->> 'email' = email);

-- 3. Criar política para admins visualizarem todos os perfis
CREATE POLICY "Admins can view all profiles" ON profiles
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE email = auth.jwt() ->> 'email'
            AND role = 'admin'
        )
    );

-- 4. Criar política para admins gerenciarem todos os perfis
CREATE POLICY "Admins can manage all profiles" ON profiles
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE email = auth.jwt() ->> 'email'
            AND role = 'admin'
        )
    );

-- 5. Verificar se RLS está habilitado
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename = 'profiles' 
        AND rowsecurity = true
    ) THEN
        ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
        RAISE NOTICE 'RLS habilitado na tabela profiles';
    ELSE
        RAISE NOTICE 'RLS já está habilitado na tabela profiles';
    END IF;
END $$;

-- 6. Verificar políticas criadas
SELECT 
    policyname as "Política",
    cmd as "Comando",
    with_check as "Condição WITH CHECK",
    qual as "Condição USING"
FROM pg_policies 
WHERE schemaname = 'public' 
AND tablename = 'profiles'
ORDER BY policyname;

-- 7. Teste de acesso (opcional)
-- SELECT * FROM profiles WHERE email = 'bboycrysforever@gmail.com';

-- 8. Mensagem de confirmação
DO $$
BEGIN
    RAISE NOTICE 'Políticas RLS corrigidas com sucesso!';
    RAISE NOTICE 'O sistema deve funcionar normalmente agora.';
END $$;
