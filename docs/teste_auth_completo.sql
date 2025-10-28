-- =============================================
-- TESTE COMPLETO: Verificar autenticação e criação de perfis
-- =============================================

-- 1. Verificar se a tabela profiles existe e tem RLS habilitado
SELECT 
    schemaname, 
    tablename, 
    rowsecurity as "RLS Habilitado"
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename = 'profiles';

-- 2. Verificar políticas RLS existentes
SELECT 
    policyname as "Política",
    cmd as "Comando",
    with_check as "Condição WITH CHECK"
FROM pg_policies 
WHERE schemaname = 'public' 
AND tablename = 'profiles'
ORDER BY policyname;

-- 3. Verificar estrutura da tabela
SELECT 
    column_name as "Coluna",
    data_type as "Tipo",
    is_nullable as "Permite NULL"
FROM information_schema.columns 
WHERE table_schema = 'public' 
AND table_name = 'profiles'
ORDER BY ordinal_position;

-- 4. Contar perfis existentes
SELECT COUNT(*) as "Total de perfis" FROM profiles;

-- 5. Listar perfis existentes (se houver)
SELECT email, full_name, role, status, created_at 
FROM profiles 
ORDER BY created_at DESC 
LIMIT 10;

-- 6. Verificar se há usuários no auth.users
SELECT COUNT(*) as "Usuários no auth.users" FROM auth.users;

-- 7. Teste de inserção usando Service Role (simular criação de perfil)
-- Descomente para testar:
/*
INSERT INTO profiles (email, full_name, role, status) 
VALUES ('teste@exemplo.com', 'Usuário Teste', 'viewer', 'ativo')
RETURNING *;
*/

-- 8. Verificar se a inserção funcionou
-- SELECT * FROM profiles WHERE email = 'teste@exemplo.com';
