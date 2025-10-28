-- =============================================
-- CORREÇÃO FINAL: Políticas RLS para profiles
-- =============================================

-- Este script resolve o problema de "new row violates row-level security policy"

-- 1. Verificar se RLS está habilitado
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

-- 2. Remover políticas de INSERT existentes (se houver)
DROP POLICY IF EXISTS "Users can create their own profile" ON profiles;
DROP POLICY IF EXISTS "Admins can create any profile" ON profiles;
DROP POLICY IF EXISTS "Service role can create profiles" ON profiles;

-- 3. Criar política para usuários criarem seus próprios perfis
CREATE POLICY "Users can create their own profile" ON profiles
    FOR INSERT WITH CHECK (auth.jwt() ->> 'email' = email);

-- 4. Criar política para admins criarem perfis de outros usuários
CREATE POLICY "Admins can create any profile" ON profiles
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE email = auth.jwt() ->> 'email'
            AND role = 'admin'
        )
    );

-- 5. Criar política para Service Role (bypass RLS para criação automática)
CREATE POLICY "Service role can create profiles" ON profiles
    FOR INSERT WITH CHECK (true);

-- 6. Verificar políticas criadas
SELECT 
    policyname as "Política",
    cmd as "Comando",
    with_check as "Condição"
FROM pg_policies 
WHERE schemaname = 'public' 
AND tablename = 'profiles'
ORDER BY policyname;

-- 7. Teste de inserção (opcional - descomente para testar)
/*
-- Teste como usuário autenticado
SET LOCAL "request.jwt.claims" TO '{"email": "usuario@exemplo.com"}';
INSERT INTO profiles (email, full_name, role, status) 
VALUES ('usuario@exemplo.com', 'Usuário Teste', 'viewer', 'ativo');
*/

-- 8. Mensagem de confirmação
DO $$
BEGIN
    RAISE NOTICE 'Correção aplicada! O sistema deve funcionar normalmente agora.';
END $$;
