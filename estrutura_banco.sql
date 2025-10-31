-- =============================================
-- Script para Identificar Estrutura do Banco de Dados
-- =============================================
-- 
-- Este script mostra:
-- - Todas as tabelas e suas colunas
-- - Tipos de dados de cada coluna
-- - Constraints (PK, FK, UNIQUE, etc.)
-- - Índices
-- - Views
-- - Políticas RLS
--
-- =============================================

-- =============================================
-- 1. Lista todas as tabelas
-- =============================================
SELECT 
    '=== TABELAS DO BANCO ===' AS info;

SELECT 
    table_name,
    table_type
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_type, table_name;

-- =============================================
-- 2. Estrutura de cada tabela (colunas e tipos)
-- =============================================
SELECT 
    '=== ESTRUTURA DAS TABELAS (COLUNAS E TIPOS) ===' AS info;

-- Lista todas as colunas de todas as tabelas
SELECT
    t.table_name AS tabela,
    c.column_name AS coluna,
    c.data_type AS tipo_dado,
    CASE 
        WHEN c.character_maximum_length IS NOT NULL 
        THEN c.data_type || '(' || c.character_maximum_length || ')'
        WHEN c.numeric_precision IS NOT NULL AND c.numeric_scale IS NOT NULL
        THEN c.data_type || '(' || c.numeric_precision || ',' || c.numeric_scale || ')'
        WHEN c.numeric_precision IS NOT NULL
        THEN c.data_type || '(' || c.numeric_precision || ')'
        ELSE c.data_type
    END AS tipo_completo,
    c.is_nullable AS nullable,
    c.column_default AS default_value,
    c.ordinal_position AS ordem
FROM information_schema.tables t
JOIN information_schema.columns c
    ON t.table_name = c.table_name
    AND t.table_schema = c.table_schema
WHERE t.table_schema = 'public'
    AND t.table_type = 'BASE TABLE'
ORDER BY t.table_name, c.ordinal_position;

-- =============================================
-- 3. Chaves Primárias
-- =============================================
SELECT 
    '=== CHAVES PRIMÁRIAS ===' AS info;

SELECT
    tc.table_name,
    kcu.column_name,
    tc.constraint_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
WHERE tc.constraint_type = 'PRIMARY KEY'
    AND tc.table_schema = 'public'
ORDER BY tc.table_name, kcu.ordinal_position;

-- =============================================
-- 4. Chaves Estrangeiras (Foreign Keys)
-- =============================================
SELECT 
    '=== CHAVES ESTRANGEIRAS ===' AS info;

SELECT
    tc.table_name AS tabela_origem,
    kcu.column_name AS coluna_origem,
    ccu.table_name AS tabela_destino,
    ccu.column_name AS coluna_destino,
    tc.constraint_name AS constraint_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = 'public'
ORDER BY tc.table_name, kcu.ordinal_position;

-- =============================================
-- 5. Constraints UNIQUE
-- =============================================
SELECT 
    '=== CONSTRAINTS UNIQUE ===' AS info;

SELECT
    tc.table_name,
    kcu.column_name,
    tc.constraint_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
WHERE tc.constraint_type = 'UNIQUE'
    AND tc.table_schema = 'public'
ORDER BY tc.table_name, kcu.ordinal_position;

-- =============================================
-- 6. Índices (excluindo PK e Unique)
-- =============================================
SELECT 
    '=== ÍNDICES ===' AS info;

SELECT
    tablename AS tabela,
    indexname AS indice,
    indexdef AS definicao
FROM pg_indexes
WHERE schemaname = 'public'
    AND indexname NOT LIKE '%_pkey'
    AND indexname NOT LIKE '%_key'
ORDER BY tablename, indexname;

-- =============================================
-- 7. Views
-- =============================================
SELECT 
    '=== VIEWS ===' AS info;

SELECT
    table_name AS view_name
FROM information_schema.views
WHERE table_schema = 'public'
ORDER BY table_name;

-- Mostra definição das views
DO $$
DECLARE
    view_name TEXT;
    view_def TEXT;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== DEFINIÇÕES DAS VIEWS ===';
    RAISE NOTICE '';
    
    FOR view_name IN 
        SELECT table_name 
        FROM information_schema.views 
        WHERE table_schema = 'public'
        ORDER BY table_name
    LOOP
        SELECT pg_get_viewdef(('public.' || view_name)::regclass, true) INTO view_def;
        RAISE NOTICE '--- View: % ---', view_name;
        RAISE NOTICE '%', view_def;
        RAISE NOTICE '';
    END LOOP;
END $$;

-- =============================================
-- 8. Políticas RLS (Row Level Security)
-- =============================================
SELECT 
    '=== POLÍTICAS RLS ===' AS info;

SELECT
    schemaname,
    tablename AS tabela,
    policyname AS nome_politica,
    permissive,
    roles,
    cmd AS comando,
    qual AS qualificacao,
    with_check AS with_check
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- =============================================
-- 9. Verifica se RLS está habilitado nas tabelas
-- =============================================
SELECT 
    '=== STATUS RLS POR TABELA ===' AS info;

SELECT
    schemaname,
    tablename AS tabela,
    CASE 
        WHEN rowsecurity THEN 'SIM'
        ELSE 'NÃO'
    END AS rls_habilitado
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- =============================================
-- 10. Resumo: Contagem de registros por tabela
-- =============================================
DO $$
DECLARE
    tbl_name TEXT;
    row_count BIGINT;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== CONTAGEM DE REGISTROS POR TABELA ===';
    RAISE NOTICE '';
    
    FOR tbl_name IN 
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
    LOOP
        EXECUTE format('SELECT COUNT(*) FROM %I', tbl_name) INTO row_count;
        RAISE NOTICE '%-30s : % registros', tbl_name, row_count;
    END LOOP;
    
    RAISE NOTICE '';
END $$;

-- =============================================
-- 11. Estrutura completa em formato JSON (opcional)
-- =============================================
-- Descomente a linha abaixo para gerar um JSON com a estrutura completa
/*
SELECT
    json_agg(
        json_build_object(
            'table', table_name,
            'columns', (
                SELECT json_agg(
                    json_build_object(
                        'name', column_name,
                        'type', data_type,
                        'nullable', is_nullable = 'YES',
                        'default', column_default
                    )
                )
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = t.table_name
            )
        )
    ) AS estrutura_completa
FROM information_schema.tables t
WHERE table_schema = 'public'
AND table_type = 'BASE TABLE';
*/

-- =============================================
-- FIM DO SCRIPT
-- =============================================

