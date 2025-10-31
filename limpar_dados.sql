-- =============================================
-- Script para limpar todos os dados do banco
-- EXCETO a tabela profiles
-- =============================================
-- 
-- ATENÇÃO: Este script irá deletar TODOS os dados
-- das tabelas abaixo, mantendo apenas a tabela profiles.
-- Execute com cuidado!
--
-- =============================================

-- Desabilita temporariamente as verificações de foreign key
SET session_replication_role = 'replica';

-- Limpa tabelas na ordem correta (filhas primeiro, pais depois)
-- Ordem baseada em dependências de foreign keys
-- Usa DO para ignorar erros se a tabela não existir

-- 1. Tabelas de anexos/evidências (dependem de outras tabelas)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'attachments') THEN
        DELETE FROM attachments;
    END IF;
END $$;

-- 2. Tabelas de ações (podem depender de não conformidades)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'actions') THEN
        DELETE FROM actions;
    END IF;
END $$;

-- 3. Tabelas principais de registros
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'accidents') THEN
        DELETE FROM accidents;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'near_misses') THEN
        DELETE FROM near_misses;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'nonconformities') THEN
        DELETE FROM nonconformities;
    END IF;
END $$;

-- 4. Tabelas de dados mensais
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'hours_worked_monthly') THEN
        DELETE FROM hours_worked_monthly;
    END IF;
END $$;

-- 5. Tabelas de KPIs (se for tabela, não view)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'kpi_monthly' AND table_type = 'BASE TABLE') THEN
        DELETE FROM kpi_monthly;
    END IF;
END $$;

-- 6. Tabelas de funcionários
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'employees') THEN
        DELETE FROM employees;
    END IF;
END $$;

-- 6. Tabelas de referência
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'sites') THEN
        DELETE FROM sites;
    END IF;
END $$;

-- 7. Tabelas administrativas (se existirem)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'admin_users') THEN
        DELETE FROM admin_users;
    END IF;
END $$;

-- Reabilita as verificações de foreign key
SET session_replication_role = 'origin';

-- =============================================
-- Verificação: Conta registros restantes
-- =============================================
-- Verifica apenas tabelas que existem usando DO block
DO $$
DECLARE
    tbl_name TEXT;
    row_count BIGINT;
BEGIN
    RAISE NOTICE '=== VERIFICAÇÃO DE REGISTROS APÓS LIMPEZA ===';
    
    -- Verifica profiles separadamente (não deve estar vazia)
    BEGIN
        EXECUTE 'SELECT COUNT(*) FROM profiles' INTO row_count;
        RAISE NOTICE 'Tabela profiles: % registros', row_count;
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Tabela profiles não encontrada';
    END;
    
    -- Verifica todas as outras tabelas
    FOR tbl_name IN 
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name != 'profiles'
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
    LOOP
        BEGIN
            EXECUTE format('SELECT COUNT(*) FROM %I', tbl_name) INTO row_count;
            RAISE NOTICE 'Tabela %: % registros', tbl_name, row_count;
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'Erro ao contar registros da tabela %', tbl_name;
        END;
    END LOOP;
    
    RAISE NOTICE '=== FIM DA VERIFICAÇÃO ===';
    RAISE NOTICE 'Todas as tabelas (exceto profiles) devem ter 0 registros';
END $$;

-- =============================================
-- FIM DO SCRIPT
-- =============================================
-- Após executar, todas as tabelas (exceto profiles)
-- devem mostrar 0 registros na verificação acima.
-- =============================================

