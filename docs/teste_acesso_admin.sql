-- =============================================
-- TESTE: Acesso do Administrador
-- =============================================

-- Email: bboycrysforever@gmail.com
-- Role: admin

-- 1. Verificar se o perfil existe
SELECT 
    'VERIFICAÇÃO PERFIL' as teste,
    email,
    full_name,
    role,
    status,
    created_at
FROM profiles 
WHERE email = 'bboycrysforever@gmail.com';

-- 2. Se não existir, criar
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

-- 3. Verificar se foi criado/atualizado
SELECT 
    'APÓS CRIAÇÃO' as teste,
    email,
    full_name,
    role,
    status,
    updated_at
FROM profiles 
WHERE email = 'bboycrysforever@gmail.com';

-- 4. Testar acesso com diferentes contextos
-- 4.1. Como usuário autenticado (simular)
SET LOCAL "request.jwt.claims" TO '{"email": "bboycrysforever@gmail.com"}';

SELECT 
    'TESTE COM JWT' as teste,
    email,
    role
FROM profiles 
WHERE email = 'bboycrysforever@gmail.com';

-- 4.2. Reset do contexto
RESET "request.jwt.claims";

-- 5. Verificar políticas ativas
SELECT 
    'POLÍTICAS ATIVAS' as teste,
    policyname,
    cmd,
    permissive,
    roles
FROM pg_policies 
WHERE schemaname = 'public' 
AND tablename = 'profiles'
ORDER BY policyname;

-- 6. Contar total de perfis
SELECT 
    'TOTAL PERFIS' as teste,
    COUNT(*) as total
FROM profiles;

-- 7. Listar todos os perfis (se possível)
SELECT 
    'TODOS PERFIS' as teste,
    email,
    role,
    status
FROM profiles 
ORDER BY created_at DESC;
