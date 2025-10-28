-- Script para inserir dados fictícios para análise
-- Execute este script no SQL Editor do Supabase após cadastrar o usuário

-- 1. Inserir horas trabalhadas mensais para 2024
INSERT INTO public.hours_worked_monthly (
    year,
    month,
    hours,
    created_by
) VALUES 
    (2024, 1, 176, 'bboycrysforever@gmail.com'),
    (2024, 2, 160, 'bboycrysforever@gmail.com'),
    (2024, 3, 184, 'bboycrysforever@gmail.com'),
    (2024, 4, 176, 'bboycrysforever@gmail.com'),
    (2024, 5, 184, 'bboycrysforever@gmail.com'),
    (2024, 6, 168, 'bboycrysforever@gmail.com'),
    (2024, 7, 184, 'bboycrysforever@gmail.com'),
    (2024, 8, 184, 'bboycrysforever@gmail.com'),
    (2024, 9, 176, 'bboycrysforever@gmail.com'),
    (2024, 10, 184, 'bboycrysforever@gmail.com'),
    (2024, 11, 176, 'bboycrysforever@gmail.com'),
    (2024, 12, 168, 'bboycrysforever@gmail.com')
ON CONFLICT (year, month, created_by) DO NOTHING;

-- 2. Inserir acidentes fictícios
INSERT INTO public.accidents (
    occurred_at,
    type,
    classification,
    body_part,
    lost_days,
    description,
    root_cause,
    status,
    created_by
) VALUES 
    -- Acidentes com lesão
    ('2024-01-15', 'lesao', 'Corte profundo', 'Mão esquerda', 5, 'Corte com faca durante preparo de alimentos', 'Falta de EPI - luvas de proteção', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-02-28', 'lesao', 'Entorse', 'Tornozelo direito', 3, 'Queda em piso molhado na cozinha', 'Piso escorregadio sem sinalização', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-03-10', 'lesao', 'Queimadura', 'Braço direito', 2, 'Queimadura com óleo quente', 'Falta de treinamento em segurança', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-04-22', 'lesao', 'Corte superficial', 'Dedo indicador', 1, 'Corte com faca afiada', 'Técnica inadequada de corte', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-05-08', 'lesao', 'Contusão', 'Pé esquerdo', 2, 'Queda de objeto pesado no pé', 'Objeto mal posicionado', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-06-15', 'lesao', 'Corte', 'Mão direita', 4, 'Corte com vidro quebrado', 'Vidro quebrado não removido', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-07-03', 'lesao', 'Entorse', 'Pulso esquerdo', 3, 'Movimento repetitivo excessivo', 'Sobrecarga de trabalho', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-08-20', 'lesao', 'Queimadura', 'Mão esquerda', 1, 'Queimadura com superfície quente', 'Falta de proteção adequada', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-09-12', 'lesao', 'Corte', 'Dedo médio', 2, 'Corte com faca de cozinha', 'Falta de concentração', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-10-05', 'lesao', 'Contusão', 'Joelho direito', 3, 'Queda em escada molhada', 'Escada sem antiderrapante', 'fechado', 'bboycrysforever@gmail.com'),
    
    -- Acidentes sem lesão
    ('2024-01-25', 'sem_lesao', 'Queda', 'N/A', 0, 'Queda sem consequências', 'Piso escorregadio', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-03-18', 'sem_lesao', 'Queda de objeto', 'N/A', 0, 'Queda de prato sem quebrar', 'Mesa instável', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-05-30', 'sem_lesao', 'Derramamento', 'N/A', 0, 'Derramamento de líquido quente', 'Recipiente mal fechado', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-07-25', 'sem_lesao', 'Queda', 'N/A', 0, 'Queda em degrau', 'Degrau mal sinalizado', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-09-28', 'sem_lesao', 'Queda de objeto', 'N/A', 0, 'Queda de utensílio', 'Prateleira instável', 'fechado', 'bboycrysforever@gmail.com'),
    
    -- Acidentes fatais (simulados)
    ('2024-11-10', 'fatal', 'Queda fatal', 'N/A', 0, 'Queda fatal de altura', 'Falta de proteção coletiva', 'fechado', 'bboycrysforever@gmail.com')
ON CONFLICT DO NOTHING;

-- 3. Inserir quase-acidentes fictícios
INSERT INTO public.near_misses (
    occurred_at,
    description,
    potential_severity,
    status,
    created_by
) VALUES 
    ('2024-01-08', 'Quase queda de escada', 'moderada', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-01-20', 'Quase corte com faca', 'leve', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-02-05', 'Quase queimadura com óleo', 'moderada', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-02-18', 'Quase queda de objeto pesado', 'grave', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-03-02', 'Quase escorregão em piso molhado', 'leve', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-03-25', 'Quase corte com vidro', 'moderada', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-04-10', 'Quase queimadura com superfície quente', 'leve', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-04-28', 'Quase queda de altura', 'grave', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-05-15', 'Quase corte com utensílio', 'leve', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-05-30', 'Quase escorregão em degrau', 'moderada', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-06-12', 'Quase queda de prateleira', 'moderada', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-06-28', 'Quase queimadura com vapor', 'leve', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-07-08', 'Quase corte com faca afiada', 'moderada', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-07-22', 'Quase queda em piso escorregadio', 'leve', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-08-05', 'Quase queimadura com óleo quente', 'moderada', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-08-18', 'Quase queda de objeto cortante', 'grave', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-09-05', 'Quase escorregão em líquido', 'leve', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-09-20', 'Quase corte com vidro quebrado', 'moderada', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-10-10', 'Quase queda de altura', 'grave', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-10-25', 'Quase queimadura com superfície quente', 'leve', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-11-05', 'Quase corte com faca', 'moderada', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-11-20', 'Quase queda em escada', 'moderada', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-12-03', 'Quase queimadura com vapor', 'leve', 'fechado', 'bboycrysforever@gmail.com'),
    ('2024-12-15', 'Quase queda de objeto pesado', 'grave', 'fechado', 'bboycrysforever@gmail.com')
ON CONFLICT DO NOTHING;

-- 4. Inserir não conformidades fictícias
INSERT INTO public.nonconformities (
    opened_at,
    standard_ref,
    severity,
    description,
    status,
    created_by
) VALUES 
    ('2024-01-10', 'NR-35', 'moderada', 'Falta de treinamento em trabalho em altura', 'aberta', 'bboycrysforever@gmail.com'),
    ('2024-01-25', 'NR-6', 'leve', 'EPIs não utilizados corretamente', 'fechada', 'bboycrysforever@gmail.com'),
    ('2024-02-05', 'NR-12', 'grave', 'Máquina sem proteção adequada', 'aberta', 'bboycrysforever@gmail.com'),
    ('2024-02-20', 'NR-18', 'moderada', 'Falta de sinalização de segurança', 'fechada', 'bboycrysforever@gmail.com'),
    ('2024-03-08', 'NR-35', 'critica', 'Trabalho em altura sem proteção coletiva', 'aberta', 'bboycrysforever@gmail.com'),
    ('2024-03-22', 'NR-6', 'leve', 'EPIs danificados em uso', 'fechada', 'bboycrysforever@gmail.com'),
    ('2024-04-12', 'NR-12', 'moderada', 'Máquina sem manutenção preventiva', 'aberta', 'bboycrysforever@gmail.com'),
    ('2024-04-28', 'NR-18', 'leve', 'Falta de treinamento em segurança', 'fechada', 'bboycrysforever@gmail.com'),
    ('2024-05-15', 'NR-35', 'grave', 'Escada sem proteção lateral', 'aberta', 'bboycrysforever@gmail.com'),
    ('2024-05-30', 'NR-6', 'moderada', 'Falta de capacete de segurança', 'fechada', 'bboycrysforever@gmail.com'),
    ('2024-06-10', 'NR-12', 'leve', 'Máquina sem manutenção', 'aberta', 'bboycrysforever@gmail.com'),
    ('2024-06-25', 'NR-18', 'moderada', 'Falta de sinalização de emergência', 'fechada', 'bboycrysforever@gmail.com'),
    ('2024-07-08', 'NR-35', 'critica', 'Trabalho em altura sem cinto de segurança', 'aberta', 'bboycrysforever@gmail.com'),
    ('2024-07-22', 'NR-6', 'leve', 'Luvas inadequadas para a atividade', 'fechada', 'bboycrysforever@gmail.com'),
    ('2024-08-05', 'NR-12', 'moderada', 'Máquina sem proteção de emergência', 'aberta', 'bboycrysforever@gmail.com'),
    ('2024-08-20', 'NR-18', 'leve', 'Falta de treinamento em primeiros socorros', 'fechada', 'bboycrysforever@gmail.com'),
    ('2024-09-10', 'NR-35', 'grave', 'Escada sem estabilização', 'aberta', 'bboycrysforever@gmail.com'),
    ('2024-09-25', 'NR-6', 'moderada', 'Falta de óculos de proteção', 'fechada', 'bboycrysforever@gmail.com'),
    ('2024-10-08', 'NR-12', 'leve', 'Máquina sem limpeza adequada', 'aberta', 'bboycrysforever@gmail.com'),
    ('2024-10-22', 'NR-18', 'moderada', 'Falta de sinalização de perigo', 'fechada', 'bboycrysforever@gmail.com'),
    ('2024-11-05', 'NR-35', 'critica', 'Trabalho em altura sem supervisão', 'aberta', 'bboycrysforever@gmail.com'),
    ('2024-11-18', 'NR-6', 'leve', 'Falta de máscara de proteção', 'fechada', 'bboycrysforever@gmail.com'),
    ('2024-12-02', 'NR-12', 'moderada', 'Máquina sem inspeção periódica', 'aberta', 'bboycrysforever@gmail.com'),
    ('2024-12-16', 'NR-18', 'leve', 'Falta de treinamento em emergência', 'fechada', 'bboycrysforever@gmail.com')
ON CONFLICT DO NOTHING;

-- 5. Inserir dados de KPI mensais (calculados automaticamente pelo sistema)
-- Estes dados serão gerados automaticamente pelo sistema baseado nos acidentes e horas
-- Mas podemos inserir alguns dados de exemplo para visualização

-- 6. Verificar dados inseridos
SELECT 'ACIDENTES' as tabela, COUNT(*) as total FROM public.accidents WHERE created_by = 'bboycrysforever@gmail.com'
UNION ALL
SELECT 'QUASE-ACIDENTES' as tabela, COUNT(*) as total FROM public.near_misses WHERE created_by = 'bboycrysforever@gmail.com'
UNION ALL
SELECT 'NÃO CONFORMIDADES' as tabela, COUNT(*) as total FROM public.nonconformities WHERE created_by = 'bboycrysforever@gmail.com'
UNION ALL
SELECT 'HORAS TRABALHADAS' as tabela, COUNT(*) as total FROM public.hours_worked_monthly WHERE created_by = 'bboycrysforever@gmail.com';

-- 7. Resumo dos dados por mês
SELECT 
    EXTRACT(MONTH FROM occurred_at) as mes,
    COUNT(*) as total_acidentes,
    COUNT(CASE WHEN type = 'fatal' THEN 1 END) as fatais,
    COUNT(CASE WHEN type = 'lesao' THEN 1 END) as com_lesao,
    COUNT(CASE WHEN type = 'sem_lesao' THEN 1 END) as sem_lesao
FROM public.accidents 
WHERE created_by = 'bboycrysforever@gmail.com'
GROUP BY EXTRACT(MONTH FROM occurred_at)
ORDER BY mes;
