-- =============================================
-- CORREÇÃO RÁPIDA DE RECURSÃO INFINITA RLS
-- =============================================

-- PROBLEMA: Política RLS causa recursão infinita na tabela profiles
-- SOLUÇÃO: Remover política problemática e criar versão corrigida

-- =============================================
-- 1. REMOVER POLÍTICA PROBLEMÁTICA
-- =============================================

DROP POLICY IF EXISTS "Admins can view all profiles" ON profiles;

-- =============================================
-- 2. CRIAR POLÍTICAS BÁSICAS (SEM RECURSÃO)
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
-- 3. VERIFICAR CONFIGURAÇÃO
-- =============================================

-- Verificar políticas ativas
SELECT policyname, permissive, roles, cmd, qual
FROM pg_policies 
WHERE schemaname = 'public' 
AND tablename = 'profiles'
ORDER BY policyname;

-- =============================================
-- 4. TESTE BÁSICO
-- =============================================

-- Teste: Usuário deve conseguir ver seu próprio perfil
-- SET LOCAL "request.jwt.claims" TO '{"email": "teste@empresa.com"}';
-- SELECT * FROM profiles WHERE id = 'teste@empresa.com';

-- =============================================
-- NOTA IMPORTANTE
-- =============================================

-- Esta correção remove temporariamente o acesso de admin a todos os perfis
-- Para restaurar funcionalidade de admin, use uma das soluções do arquivo
-- corrigir_rls_recursao.sql (tabela admin_users ou função de segurança)
