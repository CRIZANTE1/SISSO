-- =============================================
-- DIAGNÓSTICO: Estado atual das políticas RLS da tabela profiles
-- =============================================

-- 1. Verificar se RLS está habilitado na tabela profiles
SELECT 
    schemaname, 
    tablename, 
    rowsecurity as "RLS Habilitado"
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename = 'profiles';

-- 2. Listar todas as políticas existentes para a tabela profiles
SELECT 
    policyname as "Nome da Política",
    permissive as "Permissiva",
    roles as "Roles",
    cmd as "Comando",
    qual as "Condição WHERE",
    with_check as "Condição WITH CHECK"
FROM pg_policies 
WHERE schemaname = 'public' 
AND tablename = 'profiles'
ORDER BY policyname;

-- 3. Verificar se existem políticas de INSERT
SELECT 
    COUNT(*) as "Políticas de INSERT"
FROM pg_policies 
WHERE schemaname = 'public' 
AND tablename = 'profiles'
AND cmd = 'INSERT';

-- 4. Verificar estrutura da tabela profiles
SELECT 
    column_name as "Coluna",
    data_type as "Tipo",
    is_nullable as "Permite NULL",
    column_default as "Valor Padrão"
FROM information_schema.columns 
WHERE table_schema = 'public' 
AND table_name = 'profiles'
ORDER BY ordinal_position;

-- 5. Verificar se a tabela profiles existe
SELECT 
    EXISTS (
        SELECT 1 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'profiles'
    ) as "Tabela profiles existe";

-- 6. Contar registros na tabela profiles (se RLS permitir)
SELECT COUNT(*) as "Total de perfis" FROM profiles;

-- 7. Verificar se há usuários autenticados no sistema
SELECT 
    COUNT(*) as "Usuários autenticados"
FROM auth.users 
WHERE created_at > NOW() - INTERVAL '1 day';
