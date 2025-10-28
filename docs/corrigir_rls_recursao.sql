-- =============================================
-- CORREÇÃO DE RECURSÃO INFINITA EM RLS
-- =============================================

-- PROBLEMA IDENTIFICADO:
-- A política "Admins can view all profiles" causa recursão infinita
-- porque faz uma consulta na própria tabela profiles para verificar
-- se o usuário é admin, mas para fazer essa consulta, precisa aplicar
-- as políticas RLS, que por sua vez fazem a mesma consulta.

-- SOLUÇÃO:
-- 1. Remover a política problemática
-- 2. Criar uma política mais simples que não cause recursão
-- 3. Usar uma abordagem diferente para verificar admin

-- =============================================
-- 1. REMOVER POLÍTICAS PROBLEMÁTICAS
-- =============================================

-- Remove a política que causa recursão
DROP POLICY IF EXISTS "Admins can view all profiles" ON profiles;

-- =============================================
-- 2. CRIAR POLÍTICAS CORRIGIDAS
-- =============================================

-- Política para usuários verem seu próprio perfil
CREATE POLICY "Users can view their own profile" ON profiles
    FOR SELECT USING (auth.jwt() ->> 'email' = id);

-- Política para usuários atualizarem seu próprio perfil
CREATE POLICY "Users can update their own profile" ON profiles
    FOR UPDATE USING (auth.jwt() ->> 'email' = id);

-- Política para usuários inserirem seu próprio perfil
CREATE POLICY "Users can insert their own profile" ON profiles
    FOR INSERT WITH CHECK (auth.jwt() ->> 'email' = id);

-- =============================================
-- 3. SOLUÇÃO ALTERNATIVA PARA ADMINS
-- =============================================

-- Opção 1: Usar uma tabela separada para roles de admin
-- (Recomendado para evitar recursão)

-- Criar tabela de administradores (se não existir)
CREATE TABLE IF NOT EXISTS admin_users (
    email TEXT PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by TEXT
);

-- Inserir usuários admin (substitua pelos emails reais)
-- INSERT INTO admin_users (email) VALUES ('admin@empresa.com');

-- Política para admins verem todos os perfis
CREATE POLICY "Admins can view all profiles" ON profiles
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM admin_users 
            WHERE email = auth.jwt() ->> 'email'
        )
    );

-- Política para admins gerenciarem todos os perfis
CREATE POLICY "Admins can manage all profiles" ON profiles
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM admin_users 
            WHERE email = auth.jwt() ->> 'email'
        )
    );

-- =============================================
-- 4. VERIFICAR CONFIGURAÇÃO
-- =============================================

-- Verificar se RLS está habilitado
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename = 'profiles';

-- Verificar políticas ativas
SELECT policyname, permissive, roles, cmd, qual
FROM pg_policies 
WHERE schemaname = 'public' 
AND tablename = 'profiles'
ORDER BY policyname;

-- =============================================
-- 5. TESTE DE FUNCIONAMENTO
-- =============================================

-- Teste 1: Usuário comum deve ver apenas seu perfil
-- SET LOCAL "request.jwt.claims" TO '{"email": "usuario@empresa.com"}';
-- SELECT * FROM profiles; -- Deve retornar apenas 1 registro

-- Teste 2: Admin deve ver todos os perfis
-- SET LOCAL "request.jwt.claims" TO '{"email": "admin@empresa.com"}';
-- SELECT * FROM profiles; -- Deve retornar todos os registros

-- =============================================
-- 6. ALTERNATIVA: USAR FUNÇÃO DE SEGURANÇA
-- =============================================

-- Se preferir manter a verificação na tabela profiles,
-- pode usar uma função de segurança que evita recursão:

CREATE OR REPLACE FUNCTION is_admin_user(user_email TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    -- Verifica se o usuário é admin sem aplicar RLS
    RETURN EXISTS (
        SELECT 1 FROM profiles 
        WHERE id = user_email 
        AND role = 'admin'
        -- Usa SECURITY DEFINER para contornar RLS
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Política usando a função
-- CREATE POLICY "Admins can view all profiles via function" ON profiles
--     FOR SELECT USING (is_admin_user(auth.jwt() ->> 'email'));

-- =============================================
-- NOTAS IMPORTANTES
-- =============================================

-- 1. A solução com tabela admin_users é mais segura e eficiente
-- 2. Evita recursão infinita completamente
-- 3. Facilita gerenciamento de administradores
-- 4. Melhor performance que funções

-- 5. Para implementar:
--    - Execute este script no Supabase SQL Editor
--    - Insira os emails dos administradores na tabela admin_users
--    - Teste o funcionamento com diferentes usuários

-- 6. Para reverter (se necessário):
--    DROP TABLE IF EXISTS admin_users CASCADE;
--    -- E recriar as políticas originais
