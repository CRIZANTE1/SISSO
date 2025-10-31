-- =============================================
-- Script para inserir dados fictícios
-- Relacionados ao profile: d88fd010-c11f-4e0a-9491-7a13f5577e8f
-- =============================================
-- 
-- Este script cria:
-- - Tabela sites (se não existir)
-- - Sites fictícios
-- - Funcionários fictícios
-- - Horas trabalhadas mensais
-- - Acidentes
-- - Quase-acidentes
-- - Não conformidades
--
-- =============================================

-- =============================================
-- 0. Cria tabela sites (se não existir)
-- =============================================
CREATE TABLE IF NOT EXISTS sites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    type TEXT,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Cria índice único no code se não existir
CREATE UNIQUE INDEX IF NOT EXISTS sites_code_unique ON sites(code);

-- UUID do profile
DO $$
DECLARE
    profile_uuid UUID := 'd88fd010-c11f-4e0a-9491-7a13f5577e8f';
    site_1_id UUID;
    site_2_id UUID;
    site_3_id UUID;
    site_4_id UUID;
    emp_1_id UUID;
    emp_2_id UUID;
    emp_3_id UUID;
    emp_4_id UUID;
    emp_5_id UUID;
    acc_1_id UUID;
    acc_2_id UUID;
    acc_3_id UUID;
    acc_4_id UUID;
    nm_1_id UUID;
    nm_2_id UUID;
    nm_3_id UUID;
    nm_4_id UUID;
    nc_1_id UUID;
    nc_2_id UUID;
    nc_3_id UUID;
    nc_4_id UUID;
BEGIN
    -- =============================================
    -- 1. Cria Sites fictícios (se não existirem)
    -- =============================================
    RAISE NOTICE '=== Criando Sites ===';
    
    -- Site 1
    INSERT INTO sites (code, name, type, description, is_active)
    VALUES ('BAERI', 'Base Aérea do Rio de Janeiro', 'Base Aérea', 'Base Aérea principal do Rio de Janeiro', true)
    ON CONFLICT (code) DO NOTHING
    RETURNING id INTO site_1_id;
    
    IF site_1_id IS NULL THEN
        SELECT id INTO site_1_id FROM sites WHERE code = 'BAERI';
    END IF;
    
    -- Site 2
    INSERT INTO sites (code, name, type, description, is_active)
    VALUES ('BASP', 'Base Aérea de São Paulo', 'Base Aérea', 'Base Aérea de São Paulo', true)
    ON CONFLICT (code) DO NOTHING
    RETURNING id INTO site_2_id;
    
    IF site_2_id IS NULL THEN
        SELECT id INTO site_2_id FROM sites WHERE code = 'BASP';
    END IF;
    
    -- Site 3
    INSERT INTO sites (code, name, type, description, is_active)
    VALUES ('BACO', 'Base Aérea de Contagem', 'Base Aérea', 'Base Aérea de Contagem - Minas Gerais', true)
    ON CONFLICT (code) DO NOTHING
    RETURNING id INTO site_3_id;
    
    IF site_3_id IS NULL THEN
        SELECT id INTO site_3_id FROM sites WHERE code = 'BACO';
    END IF;
    
    -- Site 4
    INSERT INTO sites (code, name, type, description, is_active)
    VALUES ('ABR', 'Aeroporto de Brasília', 'Aeroporto', 'Aeroporto Internacional de Brasília', true)
    ON CONFLICT (code) DO NOTHING
    RETURNING id INTO site_4_id;
    
    IF site_4_id IS NULL THEN
        SELECT id INTO site_4_id FROM sites WHERE code = 'ABR';
    END IF;
    
    RAISE NOTICE 'Sites criados: BAERI (%), BASP (%), BACO (%), ABR (%)', site_1_id, site_2_id, site_3_id, site_4_id;
    
    -- =============================================
    -- 2. Cria Funcionários fictícios
    -- =============================================
    RAISE NOTICE '=== Criando Funcionários ===';
    
    -- Funcionário 1
    SELECT id INTO emp_1_id FROM employees WHERE email = 'joao.silva@empresa.com' LIMIT 1;
    
    IF emp_1_id IS NULL THEN
        INSERT INTO employees (full_name, email, department, admission_date, user_id)
        VALUES (
            'João Silva',
            'joao.silva@empresa.com',
            'Operações',
            '2024-01-15',
            profile_uuid
        )
        RETURNING id INTO emp_1_id;
    END IF;
    
    -- Funcionário 2
    SELECT id INTO emp_2_id FROM employees WHERE email = 'maria.santos@empresa.com' LIMIT 1;
    
    IF emp_2_id IS NULL THEN
        INSERT INTO employees (full_name, email, department, admission_date, user_id)
        VALUES (
            'Maria Santos',
            'maria.santos@empresa.com',
            'Manutenção',
            '2023-06-20',
            profile_uuid
        )
        RETURNING id INTO emp_2_id;
    END IF;
    
    -- Funcionário 3
    SELECT id INTO emp_3_id FROM employees WHERE email = 'pedro.oliveira@empresa.com' LIMIT 1;
    
    IF emp_3_id IS NULL THEN
        INSERT INTO employees (full_name, email, department, admission_date, user_id)
        VALUES (
            'Pedro Oliveira',
            'pedro.oliveira@empresa.com',
            'Segurança',
            '2024-03-10',
            profile_uuid
        )
        RETURNING id INTO emp_3_id;
    END IF;
    
    -- Funcionário 4
    SELECT id INTO emp_4_id FROM employees WHERE email = 'ana.costa@empresa.com' LIMIT 1;
    
    IF emp_4_id IS NULL THEN
        INSERT INTO employees (full_name, email, department, admission_date, user_id)
        VALUES (
            'Ana Costa',
            'ana.costa@empresa.com',
            'Operações',
            '2022-05-12',
            profile_uuid
        )
        RETURNING id INTO emp_4_id;
    END IF;
    
    -- Funcionário 5
    SELECT id INTO emp_5_id FROM employees WHERE email = 'carlos.mendes@empresa.com' LIMIT 1;
    
    IF emp_5_id IS NULL THEN
        INSERT INTO employees (full_name, email, department, admission_date, user_id)
        VALUES (
            'Carlos Mendes',
            'carlos.mendes@empresa.com',
            'Manutenção',
            '2023-09-01',
            profile_uuid
        )
        RETURNING id INTO emp_5_id;
    END IF;
    
    RAISE NOTICE 'Funcionários criados: %, %, %, %, %', emp_1_id, emp_2_id, emp_3_id, emp_4_id, emp_5_id;
    
    -- =============================================
    -- 3. Insere Horas Trabalhadas Mensais
    -- =============================================
    RAISE NOTICE '=== Criando Horas Trabalhadas ===';
    
    -- Verifica se a tabela tem coluna employee_id ou site_id
    -- Insere horas trabalhadas por funcionário (últimos 12 meses)
    -- Usando year, month, hours, created_by e employee_id (se existir)
    
    -- Horas trabalhadas mensais - Últimos 12 meses (gerais, sem referência a funcionário ou site específico)
    INSERT INTO hours_worked_monthly (year, month, hours, created_by)
    VALUES
        -- 2024
        (2024, 11, 176.0, profile_uuid),
        (2024, 10, 180.0, profile_uuid),
        (2024, 9, 175.0, profile_uuid),
        (2024, 8, 178.0, profile_uuid),
        (2024, 7, 182.0, profile_uuid),
        (2024, 6, 176.0, profile_uuid),
        (2024, 5, 179.0, profile_uuid),
        (2024, 4, 177.0, profile_uuid),
        (2024, 3, 181.0, profile_uuid),
        (2024, 2, 174.0, profile_uuid),
        (2024, 1, 178.0, profile_uuid),
        -- 2023
        (2023, 12, 175.0, profile_uuid),
        (2023, 11, 173.0, profile_uuid),
        (2023, 10, 171.0, profile_uuid),
        (2023, 9, 174.0, profile_uuid),
        (2023, 8, 177.0, profile_uuid),
        (2023, 7, 175.0, profile_uuid),
        (2023, 6, 178.0, profile_uuid),
        (2023, 5, 176.0, profile_uuid),
        (2023, 4, 179.0, profile_uuid),
        (2023, 3, 174.0, profile_uuid),
        (2023, 2, 172.0, profile_uuid),
        (2023, 1, 175.0, profile_uuid);
    
    RAISE NOTICE 'Horas trabalhadas inseridas';
    
    -- =============================================
    -- 4. Insere Acidentes
    -- =============================================
    RAISE NOTICE '=== Criando Acidentes ===';
    
    INSERT INTO accidents (
        occurred_at, type, classification, body_part, description,
        lost_days, root_cause, status, created_by, employee_id
    )
    VALUES (
        '2024-10-15',
        'lesao',
        'leve',
        'Mão',
        'Corte no dedo durante manutenção de equipamento. Funcionário não estava usando luvas adequadas.',
        3,
        'Ausência de EPI adequado e falta de treinamento específico',
        'fechado',
        profile_uuid,
        emp_1_id
    )
    RETURNING id INTO acc_1_id;
    
    INSERT INTO accidents (
        occurred_at, type, classification, body_part, description,
        lost_days, root_cause, status, created_by, employee_id
    )
    VALUES (
        '2024-09-20',
        'lesao',
        'moderado',
        'Pé',
        'Queda de altura de aproximadamente 2 metros. Fratura do tornozelo direito.',
        45,
        'Plataforma de trabalho inadequada e falta de sistema de proteção contra quedas',
        'fechado',
        profile_uuid,
        emp_2_id
    )
    RETURNING id INTO acc_2_id;
    
    INSERT INTO accidents (
        occurred_at, type, classification, body_part, description,
        lost_days, root_cause, status, created_by, employee_id
    )
    VALUES (
        '2024-08-12',
        'sem_lesao',
        'leve',
        NULL,
        'Contato com produto químico. Funcionário lavou imediatamente e não houve lesão, apenas irritação temporária na pele.',
        0,
        'Falta de sinalização adequada no local de armazenamento de produtos químicos',
        'fechado',
        profile_uuid,
        emp_3_id
    )
    RETURNING id INTO acc_3_id;
    
    INSERT INTO accidents (
        occurred_at, type, classification, body_part, description,
        lost_days, root_cause, status, created_by, employee_id
    )
    VALUES (
        '2024-07-05',
        'lesao',
        'grave',
        'Costas',
        'Queda durante operação de carga. Lesão na coluna. Funcionário em tratamento intensivo.',
        120,
        'Equipamento de carga inadequado e falta de procedimento seguro de operação',
        'fechado',
        profile_uuid,
        emp_4_id
    )
    RETURNING id INTO acc_4_id;
    
    RAISE NOTICE 'Acidentes criados: %, %, %, %', acc_1_id, acc_2_id, acc_3_id, acc_4_id;
    
    -- =============================================
    -- 5. Insere Quase-Acidentes
    -- =============================================
    RAISE NOTICE '=== Criando Quase-Acidentes ===';
    
    INSERT INTO near_misses (
        occurred_at, potential_severity, description, status, created_by
    )
    VALUES (
        '2024-11-10',
        'alta',
        'Ferramenta pesada caiu de altura de 5 metros, caindo a 1 metro de distância de funcionário. Por pouco não houve acidente grave.',
        'fechado',
        profile_uuid
    )
    RETURNING id INTO nm_1_id;
    
    INSERT INTO near_misses (
        occurred_at, potential_severity, description, status, created_by
    )
    VALUES (
        '2024-10-05',
        'media',
        'Vazamento de gás detectado em área próxima a fonte de ignição. Sistema de detecção alertou a tempo.',
        'fechado',
        profile_uuid
    )
    RETURNING id INTO nm_2_id;
    
    INSERT INTO near_misses (
        occurred_at, potential_severity, description, status, created_by
    )
    VALUES (
        '2024-09-18',
        'alta',
        'Funcionário quase atingido por peça que se soltou de equipamento em movimento. Por pouco não resultou em acidente grave.',
        'fechado',
        profile_uuid
    )
    RETURNING id INTO nm_3_id;
    
    INSERT INTO near_misses (
        occurred_at, potential_severity, description, status, created_by
    )
    VALUES (
        '2024-11-15',
        'baixa',
        'Escada escorregou durante manutenção, mas funcionário conseguiu se segurar. Nenhum ferimento.',
        'aberto',
        profile_uuid
    )
    RETURNING id INTO nm_4_id;
    
    RAISE NOTICE 'Quase-acidentes criados: %, %, %, %', nm_1_id, nm_2_id, nm_3_id, nm_4_id;
    
    -- =============================================
    -- 6. Insere Não Conformidades
    -- =============================================
    RAISE NOTICE '=== Criando Não Conformidades ===';
    
    INSERT INTO nonconformities (
        opened_at, occurred_at, standard_ref, severity, status,
        description, created_by
    )
    VALUES (
        '2024-11-01',
        '2024-10-28',
        'NR-12',
        'grave',
        'aberta',
        'Equipamento sem proteção adequada conforme NR-12. Máquina operando sem guarda de proteção.',
        profile_uuid
    )
    RETURNING id INTO nc_1_id;
    
    INSERT INTO nonconformities (
        opened_at, occurred_at, standard_ref, severity, status,
        description, created_by
    )
    VALUES (
        '2024-09-15',
        '2024-09-10',
        'ISO 45001',
        'moderada',
        'encerrada',
        'Documentação de procedimentos de segurança desatualizada. Procedimento não refletia prática atual.',
        profile_uuid
    )
    RETURNING id INTO nc_2_id;
    
    INSERT INTO nonconformities (
        opened_at, occurred_at, standard_ref, severity, status,
        description, created_by
    )
    VALUES (
        '2024-10-20',
        '2024-10-18',
        'NR-35',
        'grave',
        'aberta',
        'Trabalho em altura realizado sem sistema de proteção adequado. Falta de linha de vida e guarda-corpo.',
        profile_uuid
    )
    RETURNING id INTO nc_3_id;
    
    INSERT INTO nonconformities (
        opened_at, occurred_at, standard_ref, severity, status,
        description, created_by
    )
    VALUES (
        '2024-08-05',
        '2024-08-01',
        'NR-10',
        'leve',
        'encerrada',
        'Falta de sinalização de área elétrica restrita. Sinalização foi instalada após identificação.',
        profile_uuid
    )
    RETURNING id INTO nc_4_id;
    
    RAISE NOTICE 'Não conformidades criadas: %, %, %, %', nc_1_id, nc_2_id, nc_3_id, nc_4_id;
    
    -- =============================================
    -- 7. Insere Ações (se tabela existir)
    -- =============================================
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'actions') THEN
        RAISE NOTICE '=== Criando Ações ===';
        
        INSERT INTO actions (
            entity_type, entity_id, what, who, when_date, where_text, why, how, how_much, status, created_by
        )
        VALUES (
            'nonconformity',
            nc_1_id,
            'Instalar sistema de proteção contra quedas',
            'Equipe de Manutenção',
            '2024-12-01',
            'Plataformas de trabalho - Setor B',
            'Prevenir acidentes por queda',
            'Instalação de guarda-corpos e linhas de vida',
            15000.00,
            'aberta',
            profile_uuid
        );
        
        INSERT INTO actions (
            entity_type, entity_id, what, who, when_date, where_text, why, how, how_much, status, created_by
        )
        VALUES (
            'accident',
            acc_1_id,
            'Treinamento de uso de EPI',
            'Equipe de Segurança',
            '2024-11-20',
            'Sala de treinamentos',
            'Prevenir acidentes por falta de uso adequado de EPI',
            'Curso de 4 horas sobre seleção e uso correto de EPI',
            2000.00,
            'aberta',
            profile_uuid
        );
        
        INSERT INTO actions (
            entity_type, entity_id, what, who, when_date, where_text, why, how, how_much, status, created_by
        )
        VALUES (
            'nonconformity',
            nc_3_id,
            'Instalação de sistema de detecção de gás',
            'Equipe de Manutenção',
            '2024-12-15',
            'Área de produção',
            'Prevenir acidentes relacionados a vazamento de gases',
            'Instalação de sensores de gás e sistema de alarme',
            35000.00,
            'aberta',
            profile_uuid
        );
        
        INSERT INTO actions (
            entity_type, entity_id, what, who, when_date, where_text, why, how, how_much, status, created_by
        )
        VALUES (
            'accident',
            acc_4_id,
            'Substituição de equipamentos de carga',
            'Equipe de Manutenção',
            '2024-11-30',
            'Setor de Logística',
            'Prevenir acidentes por falha de equipamento',
            'Substituição de equipamentos antigos por modelos modernos e seguros',
            85000.00,
            'aberta',
            profile_uuid
        );
        
        RAISE NOTICE 'Ações criadas';
    END IF;
    
    RAISE NOTICE '=== Dados fictícios criados com sucesso! ===';
    RAISE NOTICE 'Profile UUID: %', profile_uuid;
    
END $$;

-- =============================================
-- Verificação: Conta registros criados
-- =============================================
DO $$
DECLARE
    profile_uuid UUID := 'd88fd010-c11f-4e0a-9491-7a13f5577e8f';
BEGIN
    RAISE NOTICE '=== VERIFICAÇÃO DE DADOS CRIADOS ===';
    
    RAISE NOTICE 'Sites: %', (SELECT COUNT(*) FROM sites);
    RAISE NOTICE 'Funcionários: %', (SELECT COUNT(*) FROM employees WHERE user_id = profile_uuid);
    RAISE NOTICE 'Horas trabalhadas: %', (SELECT COUNT(*) FROM hours_worked_monthly WHERE created_by = profile_uuid);
    RAISE NOTICE 'Acidentes: %', (SELECT COUNT(*) FROM accidents WHERE created_by = profile_uuid);
    RAISE NOTICE 'Quase-acidentes: %', (SELECT COUNT(*) FROM near_misses WHERE created_by = profile_uuid);
    RAISE NOTICE 'Não conformidades: %', (SELECT COUNT(*) FROM nonconformities WHERE created_by = profile_uuid);
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'actions') THEN
        RAISE NOTICE 'Ações: %', (SELECT COUNT(*) FROM actions WHERE created_by = profile_uuid);
    END IF;
    
    RAISE NOTICE '=== FIM DA VERIFICAÇÃO ===';
END $$;

-- =============================================
-- FIM DO SCRIPT
-- =============================================
-- Todos os dados foram criados relacionados ao profile:
-- d88fd010-c11f-4e0a-9491-7a13f5577e8f
-- =============================================

