-- =============================================
-- CORREÇÃO: Política RLS para INSERT na tabela profiles
-- =============================================

-- Problema identificado:
-- A tabela profiles tem RLS habilitado, mas não possui política de INSERT
-- Isso impede a criação de novos perfis de usuário

-- Solução: Adicionar política de INSERT para permitir criação de perfis

-- 1. Política para usuários criarem seus próprios perfis
CREATE POLICY "Users can create their own profile" ON profiles
    FOR INSERT WITH CHECK (auth.jwt() ->> 'email' = email);

-- 2. Política para admins criarem perfis de outros usuários
CREATE POLICY "Admins can create any profile" ON profiles
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE email = auth.jwt() ->> 'email'
            AND role = 'admin'
        )
    );

-- 3. Verificar se RLS está habilitado na tabela
-- (Se não estiver, descomente a linha abaixo)
-- ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- 4. Verificar políticas existentes
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
FROM pg_policies 
WHERE schemaname = 'public' AND tablename = 'profiles'
ORDER BY policyname;

-- 5. Teste da política (opcional)
-- Para testar, execute como usuário autenticado:
-- INSERT INTO profiles (email, full_name, role, status) 
-- VALUES ('teste@exemplo.com', 'Usuário Teste', 'viewer', 'ativo');
