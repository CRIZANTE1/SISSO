-- CORREÇÃO IMEDIATA DE RECURSÃO INFINITA RLS
-- Execute este script no Supabase SQL Editor

-- 1. Remover política problemática que causa recursão
DROP POLICY IF EXISTS "Admins can view all profiles" ON profiles;

-- 2. Verificar se a política foi removida
SELECT policyname, permissive, roles, cmd, qual
FROM pg_policies 
WHERE schemaname = 'public' 
AND tablename = 'profiles'
ORDER BY policyname;
