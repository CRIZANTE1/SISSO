-- =============================================
-- CORREÇÃO RÁPIDA: Adicionar política de INSERT para profiles
-- =============================================

-- Execute este script no SQL Editor do Supabase para corrigir o erro de RLS

-- 1. Verificar se RLS está habilitado (se não estiver, habilitar)
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

-- 2. Remover políticas existentes de INSERT (se houver) para evitar conflitos
DROP POLICY IF EXISTS "Users can create their own profile" ON profiles;
DROP POLICY IF EXISTS "Admins can create any profile" ON profiles;

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

-- 5. Verificar se as políticas foram criadas corretamente
SELECT 
    policyname as "Política",
    cmd as "Comando",
    with_check as "Condição"
FROM pg_policies 
WHERE schemaname = 'public' 
AND tablename = 'profiles'
AND cmd = 'INSERT'
ORDER BY policyname;

-- 6. Teste (opcional) - descomente para testar
-- INSERT INTO profiles (email, full_name, role, status) 
-- VALUES ('teste@exemplo.com', 'Usuário Teste', 'viewer', 'ativo');

RAISE NOTICE 'Correção aplicada com sucesso! As páginas devem carregar normalmente agora.';
