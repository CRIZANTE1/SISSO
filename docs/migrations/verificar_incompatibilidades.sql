-- Script de Verificação de Incompatibilidades
-- Data: 2025-01-29
-- Descrição: Verifica se todas as migrations foram aplicadas e se o banco está compatível com o sistema

-- ============================================================================
-- 1. VERIFICAR CAMPOS DA TABELA fault_tree_nodes
-- ============================================================================

SELECT 
    'fault_tree_nodes' AS tabela,
    column_name AS campo,
    data_type AS tipo,
    is_nullable AS nullable,
    CASE 
        WHEN column_name = 'justification' THEN '⚠️ Verificar: Migration add_justification_to_fault_tree_nodes.sql'
        WHEN column_name = 'justification_image_url' THEN '⚠️ Verificar: Migration add_justification_image_to_fault_tree_nodes.sql'
        WHEN column_name = 'recommendation' THEN '⚠️ Verificar: Migration add_recommendation_to_fault_tree_nodes.sql'
        WHEN column_name = 'display_order' THEN '❌ CRÍTICO: Campo essencial para ordenação'
        WHEN column_name = 'is_contributing_cause' THEN '⚠️ Verificar: Migration add_contributing_cause_to_fault_tree_nodes.sql'
        ELSE '✅ OK'
    END AS status
FROM information_schema.columns
WHERE table_name = 'fault_tree_nodes'
  AND column_name IN ('justification', 'justification_image_url', 'recommendation', 'display_order', 'is_contributing_cause')
ORDER BY column_name;

-- Verifica se os campos críticos existem
SELECT 
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'fault_tree_nodes' AND column_name = 'display_order'
        ) THEN '✅ Campo display_order existe'
        ELSE '❌ ERRO: Campo display_order NÃO existe - Executar migration add_display_order_to_fault_tree_nodes.sql'
    END AS verificacao_display_order,
    
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'fault_tree_nodes' AND column_name = 'justification'
        ) THEN '✅ Campo justification existe'
        ELSE '❌ ERRO: Campo justification NÃO existe - Executar migration add_justification_to_fault_tree_nodes.sql'
    END AS verificacao_justification,
    
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'fault_tree_nodes' AND column_name = 'justification_image_url'
        ) THEN '✅ Campo justification_image_url existe'
        ELSE '❌ ERRO: Campo justification_image_url NÃO existe - Executar migration add_justification_image_to_fault_tree_nodes.sql'
    END AS verificacao_justification_image_url,
    
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'fault_tree_nodes' AND column_name = 'recommendation'
        ) THEN '✅ Campo recommendation existe'
        ELSE '❌ ERRO: Campo recommendation NÃO existe - Executar migration add_recommendation_to_fault_tree_nodes.sql'
    END AS verificacao_recommendation,
    
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'fault_tree_nodes' AND column_name = 'is_contributing_cause'
        ) THEN '✅ Campo is_contributing_cause existe'
        ELSE '❌ ERRO: Campo is_contributing_cause NÃO existe - Executar migration add_contributing_cause_to_fault_tree_nodes.sql'
    END AS verificacao_is_contributing_cause;

-- ============================================================================
-- 2. VERIFICAR SE A TABELA commission_actions EXISTE
-- ============================================================================

SELECT 
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'commission_actions'
        ) THEN '✅ Tabela commission_actions existe'
        ELSE '❌ ERRO: Tabela commission_actions NÃO existe - Executar migration create_commission_actions_table.sql'
    END AS verificacao_commission_actions;

-- Se a tabela existe, verifica estrutura
SELECT 
    'commission_actions' AS tabela,
    column_name AS campo,
    data_type AS tipo,
    is_nullable AS nullable,
    column_default AS default_value,
    CASE 
        WHEN column_name = 'id' AND data_type = 'uuid' THEN '✅ OK - Primary Key'
        WHEN column_name = 'accident_id' AND data_type = 'uuid' AND is_nullable = 'NO' THEN '✅ OK - Foreign Key'
        WHEN column_name = 'action_time' AND data_type = 'timestamp with time zone' AND is_nullable = 'NO' THEN '✅ OK'
        WHEN column_name = 'description' AND data_type = 'text' AND is_nullable = 'NO' THEN '✅ OK'
        WHEN column_name IN ('action_type', 'responsible_person') AND is_nullable = 'YES' THEN '✅ OK - Opcional'
        ELSE '⚠️ Verificar'
    END AS status
FROM information_schema.columns
WHERE table_name = 'commission_actions'
ORDER BY ordinal_position;

-- ============================================================================
-- 3. VERIFICAR ÍNDICES
-- ============================================================================

-- Índices em fault_tree_nodes
SELECT 
    indexname AS indice,
    indexdef AS definicao,
    CASE 
        WHEN indexname LIKE '%display_order%' THEN '✅ Índice de ordenação'
        WHEN indexname LIKE '%accident_id%' THEN '✅ Índice de acidente'
        ELSE '⚠️ Verificar necessidade'
    END AS status
FROM pg_indexes
WHERE tablename = 'fault_tree_nodes'
ORDER BY indexname;

-- Índices em commission_actions
SELECT 
    indexname AS indice,
    indexdef AS definicao,
    CASE 
        WHEN indexname LIKE '%accident_id%' THEN '✅ Índice de acidente'
        WHEN indexname LIKE '%action_time%' THEN '✅ Índice de data/hora'
        ELSE '⚠️ Verificar necessidade'
    END AS status
FROM pg_indexes
WHERE tablename = 'commission_actions'
ORDER BY indexname;

-- ============================================================================
-- 4. VERIFICAR FOREIGN KEYS
-- ============================================================================

-- Foreign Keys de fault_tree_nodes
SELECT 
    tc.table_name AS tabela,
    kcu.column_name AS campo,
    ccu.table_name AS tabela_referenciada,
    ccu.column_name AS campo_referenciado,
    CASE 
        WHEN ccu.table_name = 'accidents' THEN '✅ OK'
        WHEN ccu.table_name = 'fault_tree_nodes' AND ccu.column_name = 'id' THEN '✅ OK - Self-reference'
        WHEN ccu.table_name = 'nbr_standards' THEN '✅ OK'
        WHEN ccu.table_name = 'auth.users' THEN '⚠️ ATENÇÃO: FK aponta para auth.users.id, código usa profiles.id'
        ELSE '⚠️ Verificar'
    END AS status
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_name = 'fault_tree_nodes'
ORDER BY tc.table_name, kcu.column_name;

-- Foreign Keys de commission_actions
SELECT 
    tc.table_name AS tabela,
    kcu.column_name AS campo,
    ccu.table_name AS tabela_referenciada,
    ccu.column_name AS campo_referenciado,
    CASE 
        WHEN ccu.table_name = 'accidents' THEN '✅ OK'
        WHEN ccu.table_name = 'auth.users' THEN '⚠️ ATENÇÃO: FK aponta para auth.users.id, código usa profiles.id'
        ELSE '⚠️ Verificar'
    END AS status
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_name = 'commission_actions'
ORDER BY tc.table_name, kcu.column_name;

-- ============================================================================
-- 5. RESUMO GERAL
-- ============================================================================

SELECT 
    'RESUMO GERAL' AS verificacao,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'fault_tree_nodes' AND column_name = 'display_order'
        ) AND EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'fault_tree_nodes' AND column_name = 'justification'
        ) AND EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'fault_tree_nodes' AND column_name = 'justification_image_url'
        ) AND EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'fault_tree_nodes' AND column_name = 'recommendation'
        ) AND EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'commission_actions'
        ) THEN '✅ BANCO COMPATÍVEL: Todas as verificações passaram'
        ELSE '❌ BANCO INCOMPATÍVEL: Execute as migrations faltantes'
    END AS status;
