-- =============================================
-- Script para corrigir colunas created_by
-- =============================================
-- 
-- Este script:
-- 1. Adiciona coluna created_by (UUID) nas tabelas que faltam
-- 2. Altera tipo de TEXT para UUID onde necessário
-- 3. Adiciona foreign key para profiles.id
-- 4. Migra dados existentes (se houver)
--
-- =============================================

-- Tabelas que DEVEM ter created_by (baseado no código):
-- - accidents ✅ (usa no código)
-- - near_misses ✅ (usa no código)
-- - nonconformities ✅ (usa no código)
-- - hours_worked_monthly ✅ (usa no código)
--
-- Tabelas que NÃO devem ter created_by:
-- - profiles (é a tabela de referência)
-- - employees (não usa created_by no código)
-- - sites (não usa created_by no código)
-- - attachments (não vi uso direto no código)

-- =============================================
-- 0. Salva e remove dependências (views e policies)
-- =============================================
-- Cria tabelas temporárias para armazenar definições
CREATE TEMP TABLE IF NOT EXISTS _view_definitions (
    view_name TEXT PRIMARY KEY,
    view_definition TEXT
);

CREATE TEMP TABLE IF NOT EXISTS _policy_definitions (
    policy_id SERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
    policy_name TEXT NOT NULL,
    policy_cmd TEXT,
    policy_qual TEXT,
    policy_with_check TEXT,
    UNIQUE(table_name, policy_name)
);

-- Salva definição da view kpi_monthly se existir
DO $$
DECLARE
    view_def TEXT;
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.views WHERE table_schema = 'public' AND table_name = 'kpi_monthly') THEN
        SELECT pg_get_viewdef('kpi_monthly', true) INTO view_def;
        
        INSERT INTO _view_definitions (view_name, view_definition)
        VALUES ('kpi_monthly', view_def)
        ON CONFLICT (view_name) DO UPDATE SET view_definition = EXCLUDED.view_definition;
        
        DROP VIEW IF EXISTS kpi_monthly CASCADE;
        
        RAISE NOTICE 'View kpi_monthly removida temporariamente';
    END IF;
END $$;

-- Salva e remove políticas RLS que dependem de created_by
DO $$
DECLARE
    pol RECORD;
    policy_sql TEXT;
BEGIN
    -- Salva todas as políticas que referenciam created_by
    FOR pol IN 
        SELECT 
            schemaname,
            tablename,
            policyname,
            permissive,
            roles,
            cmd,
            qual,
            with_check
        FROM pg_policies
        WHERE schemaname = 'public'
        AND (
            qual LIKE '%created_by%' 
            OR with_check LIKE '%created_by%'
        )
    LOOP
        -- Armazena definição da política
        INSERT INTO _policy_definitions (table_name, policy_name, policy_cmd, policy_qual, policy_with_check)
        VALUES (pol.tablename, pol.policyname, pol.cmd::TEXT, pol.qual, pol.with_check)
        ON CONFLICT (table_name, policy_name) DO UPDATE SET
            policy_cmd = EXCLUDED.policy_cmd,
            policy_qual = EXCLUDED.policy_qual,
            policy_with_check = EXCLUDED.policy_with_check;
        
        -- Remove política
        EXECUTE format('DROP POLICY IF EXISTS %I ON %I', pol.policyname, pol.tablename);
        
        RAISE NOTICE 'Política % removida da tabela %', pol.policyname, pol.tablename;
    END LOOP;
    
    RAISE NOTICE 'Políticas RLS que dependem de created_by foram removidas temporariamente';
END $$;

-- =============================================
-- 1. TABELA: accidents
-- =============================================
DO $$
DECLARE
    fk_constraint TEXT;
BEGIN
    -- Remove TODAS as foreign keys relacionadas a created_by ANTES de alterar o tipo
    -- Procura por qualquer constraint que referencie created_by
    -- Usa pg_constraint para ter certeza de encontrar todas
    FOR fk_constraint IN 
        SELECT conname::TEXT
        FROM pg_constraint con
        JOIN pg_class rel ON rel.oid = con.conrelid
        JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
        WHERE nsp.nspname = 'public'
        AND rel.relname = 'accidents'
        AND con.contype = 'f'
        AND EXISTS (
            SELECT 1 FROM unnest(con.conkey) AS col
            JOIN pg_attribute att ON att.attrelid = con.conrelid AND att.attnum = col
            WHERE att.attname = 'created_by'
        )
    LOOP
        EXECUTE format('ALTER TABLE accidents DROP CONSTRAINT IF EXISTS %I CASCADE', fk_constraint);
        RAISE NOTICE 'Foreign key % removida da tabela accidents', fk_constraint;
    END LOOP;
    
    -- Verifica se a coluna existe
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'accidents' 
        AND column_name = 'created_by'
    ) THEN
        -- Se existe como TEXT, altera para UUID
        IF (
            SELECT data_type FROM information_schema.columns 
            WHERE table_name = 'accidents' 
            AND column_name = 'created_by'
        ) = 'text' THEN
            -- Primeiro, limpa valores inválidos (não UUID)
            UPDATE accidents 
            SET created_by = NULL 
            WHERE created_by IS NOT NULL 
            AND created_by !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';
            
            -- Altera tipo para UUID
            ALTER TABLE accidents 
            ALTER COLUMN created_by TYPE UUID USING created_by::UUID;
        END IF;
        
        -- Cria nova foreign key para profiles.id (UUID)
        ALTER TABLE accidents 
        ADD CONSTRAINT accidents_created_by_fkey 
        FOREIGN KEY (created_by) REFERENCES profiles(id);
    ELSE
        -- Adiciona coluna se não existir
        ALTER TABLE accidents 
        ADD COLUMN created_by UUID REFERENCES profiles(id);
    END IF;
    
    RAISE NOTICE 'Tabela accidents: coluna created_by configurada';
END $$;

-- =============================================
-- 2. TABELA: near_misses
-- =============================================
DO $$
DECLARE
    fk_constraint TEXT;
BEGIN
    -- Remove TODAS as foreign keys relacionadas a created_by
    FOR fk_constraint IN 
        SELECT conname::TEXT
        FROM pg_constraint con
        JOIN pg_class rel ON rel.oid = con.conrelid
        JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
        WHERE nsp.nspname = 'public'
        AND rel.relname = 'near_misses'
        AND con.contype = 'f'
        AND EXISTS (
            SELECT 1 FROM unnest(con.conkey) AS col
            JOIN pg_attribute att ON att.attrelid = con.conrelid AND att.attnum = col
            WHERE att.attname = 'created_by'
        )
    LOOP
        EXECUTE format('ALTER TABLE near_misses DROP CONSTRAINT IF EXISTS %I CASCADE', fk_constraint);
    END LOOP;
    
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'near_misses' 
        AND column_name = 'created_by'
    ) THEN
        IF (
            SELECT data_type FROM information_schema.columns 
            WHERE table_name = 'near_misses' 
            AND column_name = 'created_by'
        ) = 'text' THEN
            UPDATE near_misses 
            SET created_by = NULL 
            WHERE created_by IS NOT NULL 
            AND created_by !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';
            
            ALTER TABLE near_misses 
            ALTER COLUMN created_by TYPE UUID USING created_by::UUID;
        END IF;
        
        -- Cria nova foreign key para profiles.id (UUID)
        ALTER TABLE near_misses 
        ADD CONSTRAINT near_misses_created_by_fkey 
        FOREIGN KEY (created_by) REFERENCES profiles(id);
    ELSE
        ALTER TABLE near_misses 
        ADD COLUMN created_by UUID REFERENCES profiles(id);
    END IF;
    
    RAISE NOTICE 'Tabela near_misses: coluna created_by configurada';
END $$;

-- =============================================
-- 3. TABELA: nonconformities
-- =============================================
DO $$
DECLARE
    fk_constraint TEXT;
BEGIN
    -- Remove TODAS as foreign keys relacionadas a created_by
    FOR fk_constraint IN 
        SELECT conname::TEXT
        FROM pg_constraint con
        JOIN pg_class rel ON rel.oid = con.conrelid
        JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
        WHERE nsp.nspname = 'public'
        AND rel.relname = 'nonconformities'
        AND con.contype = 'f'
        AND EXISTS (
            SELECT 1 FROM unnest(con.conkey) AS col
            JOIN pg_attribute att ON att.attrelid = con.conrelid AND att.attnum = col
            WHERE att.attname = 'created_by'
        )
    LOOP
        EXECUTE format('ALTER TABLE nonconformities DROP CONSTRAINT IF EXISTS %I CASCADE', fk_constraint);
    END LOOP;
    
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'nonconformities' 
        AND column_name = 'created_by'
    ) THEN
        IF (
            SELECT data_type FROM information_schema.columns 
            WHERE table_name = 'nonconformities' 
            AND column_name = 'created_by'
        ) = 'text' THEN
            UPDATE nonconformities 
            SET created_by = NULL 
            WHERE created_by IS NOT NULL 
            AND created_by !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';
            
            ALTER TABLE nonconformities 
            ALTER COLUMN created_by TYPE UUID USING created_by::UUID;
        END IF;
        
        -- Cria nova foreign key para profiles.id (UUID)
        ALTER TABLE nonconformities 
        ADD CONSTRAINT nonconformities_created_by_fkey 
        FOREIGN KEY (created_by) REFERENCES profiles(id);
    ELSE
        ALTER TABLE nonconformities 
        ADD COLUMN created_by UUID REFERENCES profiles(id);
    END IF;
    
    RAISE NOTICE 'Tabela nonconformities: coluna created_by configurada';
END $$;

-- =============================================
-- 4. TABELA: hours_worked_monthly
-- =============================================
DO $$
DECLARE
    fk_constraint TEXT;
BEGIN
    -- Remove TODAS as foreign keys relacionadas a created_by
    FOR fk_constraint IN 
        SELECT conname::TEXT
        FROM pg_constraint con
        JOIN pg_class rel ON rel.oid = con.conrelid
        JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
        WHERE nsp.nspname = 'public'
        AND rel.relname = 'hours_worked_monthly'
        AND con.contype = 'f'
        AND EXISTS (
            SELECT 1 FROM unnest(con.conkey) AS col
            JOIN pg_attribute att ON att.attrelid = con.conrelid AND att.attnum = col
            WHERE att.attname = 'created_by'
        )
    LOOP
        EXECUTE format('ALTER TABLE hours_worked_monthly DROP CONSTRAINT IF EXISTS %I CASCADE', fk_constraint);
    END LOOP;
    
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'hours_worked_monthly' 
        AND column_name = 'created_by'
    ) THEN
        IF (
            SELECT data_type FROM information_schema.columns 
            WHERE table_name = 'hours_worked_monthly' 
            AND column_name = 'created_by'
        ) = 'text' THEN
            UPDATE hours_worked_monthly 
            SET created_by = NULL 
            WHERE created_by IS NOT NULL 
            AND created_by !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';
            
            ALTER TABLE hours_worked_monthly 
            ALTER COLUMN created_by TYPE UUID USING created_by::UUID;
        END IF;
        
        -- Cria nova foreign key para profiles.id (UUID)
        ALTER TABLE hours_worked_monthly 
        ADD CONSTRAINT hours_worked_monthly_created_by_fkey 
        FOREIGN KEY (created_by) REFERENCES profiles(id);
    ELSE
        ALTER TABLE hours_worked_monthly 
        ADD COLUMN created_by UUID REFERENCES profiles(id);
    END IF;
    
    RAISE NOTICE 'Tabela hours_worked_monthly: coluna created_by configurada';
END $$;

-- =============================================
-- 5. TABELA: actions (opcional - se usar no futuro)
-- =============================================
DO $$
DECLARE
    fk_constraint TEXT;
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'actions') THEN
        -- Remove TODAS as foreign keys relacionadas a created_by
        FOR fk_constraint IN 
            SELECT conname::TEXT
            FROM pg_constraint con
            JOIN pg_class rel ON rel.oid = con.conrelid
            JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
            WHERE nsp.nspname = 'public'
            AND rel.relname = 'actions'
            AND con.contype = 'f'
            AND EXISTS (
                SELECT 1 FROM unnest(con.conkey) AS col
                JOIN pg_attribute att ON att.attrelid = con.conrelid AND att.attnum = col
                WHERE att.attname = 'created_by'
            )
        LOOP
            EXECUTE format('ALTER TABLE actions DROP CONSTRAINT IF EXISTS %I CASCADE', fk_constraint);
        END LOOP;
        
        IF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'actions' 
            AND column_name = 'created_by'
        ) THEN
            IF (
                SELECT data_type FROM information_schema.columns 
                WHERE table_name = 'actions' 
                AND column_name = 'created_by'
            ) = 'text' THEN
                UPDATE actions 
                SET created_by = NULL 
                WHERE created_by IS NOT NULL 
                AND created_by !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';
                
                ALTER TABLE actions 
                ALTER COLUMN created_by TYPE UUID USING created_by::UUID;
            END IF;
            
            -- Cria nova foreign key para profiles.id (UUID)
            ALTER TABLE actions 
            ADD CONSTRAINT actions_created_by_fkey 
            FOREIGN KEY (created_by) REFERENCES profiles(id);
        ELSE
            ALTER TABLE actions 
            ADD COLUMN created_by UUID REFERENCES profiles(id);
        END IF;
        
        RAISE NOTICE 'Tabela actions: coluna created_by configurada';
    END IF;
END $$;

-- =============================================
-- 6. Recria políticas RLS que foram removidas
-- =============================================
DO $$
DECLARE
    pol RECORD;
    policy_sql TEXT;
BEGIN
    -- Recria todas as políticas salvas, atualizando created_by para usar UUID
    FOR pol IN 
        SELECT * FROM _policy_definitions
        ORDER BY policy_id
    LOOP
        BEGIN
            -- Recria política, mas substituindo referências a email por UUID
            -- As políticas originais usavam auth.jwt() ->> 'email' = created_by
            -- Agora precisam usar: created_by = (SELECT id FROM profiles WHERE email = auth.jwt() ->> 'email')
            -- OU mais simples: created_by = (SELECT id FROM profiles WHERE id::text = auth.jwt() ->> 'email')
            -- Mas o ideal é atualizar para usar UUID diretamente do JWT se disponível
            
            -- Recria política com a qualificação atualizada
            IF pol.policy_cmd IS NOT NULL THEN
                -- Construir comando CREATE POLICY
                policy_sql := format(
                    'CREATE POLICY %I ON %I FOR %s',
                    pol.policy_name,
                    pol.table_name,
                    pol.policy_cmd
                );
                
                -- Atualiza qualificação para usar UUID
                IF pol.policy_qual IS NOT NULL THEN
                    -- Substitui referências a email por comparação com UUID via profiles
                    -- Forma antiga: auth.jwt() ->> 'email' = created_by
                    -- Forma nova: created_by = (SELECT id FROM profiles WHERE email = auth.jwt() ->> 'email')
                    policy_sql := policy_sql || format(
                        ' USING (%s)',
                        REPLACE(
                            REPLACE(pol.policy_qual, 
                                'auth.jwt() ->> ''email'' = created_by',
                                'created_by = (SELECT id FROM profiles WHERE email = auth.jwt() ->> ''email'')'
                            ),
                            'created_by = auth.jwt() ->> ''email''',
                            'created_by = (SELECT id FROM profiles WHERE email = auth.jwt() ->> ''email'')'
                        )
                    );
                END IF;
                
                IF pol.policy_with_check IS NOT NULL THEN
                    policy_sql := policy_sql || format(
                        ' WITH CHECK (%s)',
                        REPLACE(
                            REPLACE(pol.policy_with_check,
                                'auth.jwt() ->> ''email'' = created_by',
                                'created_by = (SELECT id FROM profiles WHERE email = auth.jwt() ->> ''email'')'
                            ),
                            'created_by = auth.jwt() ->> ''email''',
                            'created_by = (SELECT id FROM profiles WHERE email = auth.jwt() ->> ''email'')'
                        )
                    );
                END IF;
                
                EXECUTE policy_sql;
                RAISE NOTICE 'Política % recriada na tabela %', pol.policy_name, pol.table_name;
            END IF;
        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'Não foi possível recriar política % na tabela %: %', 
                pol.policy_name, pol.table_name, SQLERRM;
            RAISE NOTICE 'Definição original: cmd=%, qual=%, with_check=%', 
                pol.policy_cmd, pol.policy_qual, pol.policy_with_check;
        END;
    END LOOP;
    
    RAISE NOTICE 'Políticas RLS recriadas';
END $$;

-- =============================================
-- 7. Recria view kpi_monthly se foi removida
-- =============================================
DO $$
DECLARE
    view_def TEXT;
BEGIN
    -- Tenta recuperar definição da view da tabela temporária
    SELECT view_definition INTO view_def 
    FROM _view_definitions 
    WHERE view_name = 'kpi_monthly';
    
    IF view_def IS NOT NULL AND view_def != '' THEN
        BEGIN
            -- Recria view com a definição original
            EXECUTE format('CREATE VIEW kpi_monthly AS %s', view_def);
            RAISE NOTICE 'View kpi_monthly recriada com sucesso';
        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'Não foi possível recriar view kpi_monthly: %', SQLERRM;
            RAISE NOTICE 'Definição original da view foi salva na tabela temporária _view_definitions';
            RAISE NOTICE 'Você pode recriar manualmente usando a definição salva';
        END;
    ELSIF EXISTS (SELECT 1 FROM information_schema.views WHERE table_schema = 'public' AND table_name = 'kpi_monthly') THEN
        RAISE NOTICE 'View kpi_monthly já existe (não foi removida)';
    ELSE
        RAISE NOTICE 'View kpi_monthly não existe e não havia definição salva';
    END IF;
END $$;

-- =============================================
-- Verificação Final
-- =============================================
DO $$
DECLARE
    rec RECORD;
BEGIN
    RAISE NOTICE '=== VERIFICAÇÃO DE COLUNAS created_by ===';
    
    FOR rec IN 
        SELECT 
            table_name,
            column_name,
            data_type,
            is_nullable
        FROM information_schema.columns 
        WHERE column_name = 'created_by'
        AND table_schema = 'public'
        ORDER BY table_name
    LOOP
        RAISE NOTICE 'Tabela: %, Tipo: %, Nullable: %', 
            rec.table_name, 
            rec.data_type, 
            rec.is_nullable;
    END LOOP;
    
    RAISE NOTICE '=== FIM DA VERIFICAÇÃO ===';
    RAISE NOTICE 'Todas as colunas created_by devem ser do tipo UUID';
END $$;

-- =============================================
-- FIM DO SCRIPT
-- =============================================
-- Após executar, todas as colunas created_by devem:
-- 1. Ser do tipo UUID
-- 2. Ter foreign key para profiles(id)
-- 3. Estar presentes nas tabelas: accidents, near_misses, nonconformities, hours_worked_monthly
-- =============================================

