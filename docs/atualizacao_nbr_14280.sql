-- =============================================
-- ATUALIZAÇÃO DO BANCO DE DADOS PARA NBR 14280
-- Sistema de Gestão de Segurança e Saúde Ocupacional (SSO)
-- =============================================

-- 1. Criar enum para classificação de severidade conforme NBR 14280
CREATE TYPE accident_severity_nbr AS ENUM (
    'leve',      -- 1-15 dias perdidos
    'moderado',  -- 16-30 dias perdidos  
    'grave',     -- 31+ dias perdidos
    'fatal'      -- Morte
);

-- 2. Adicionar coluna de classificação NBR 14280 na tabela accidents
ALTER TABLE accidents 
ADD COLUMN severity_nbr accident_severity_nbr;

-- 3. Adicionar coluna para indicar se é acidente fatal
ALTER TABLE accidents 
ADD COLUMN is_fatal BOOLEAN DEFAULT FALSE;

-- 4. Adicionar coluna para número da CAT (Comunicação de Acidente de Trabalho)
ALTER TABLE accidents 
ADD COLUMN cat_number TEXT;

-- 5. Adicionar coluna para data de comunicação do acidente
ALTER TABLE accidents 
ADD COLUMN communication_date DATE;

-- 6. Adicionar coluna para indicar se investigação foi concluída
ALTER TABLE accidents 
ADD COLUMN investigation_completed BOOLEAN DEFAULT FALSE;

-- 7. Adicionar coluna para data de conclusão da investigação
ALTER TABLE accidents 
ADD COLUMN investigation_date DATE;

-- 8. Adicionar coluna para responsável pela investigação
ALTER TABLE accidents 
ADD COLUMN investigation_responsible TEXT;

-- 9. Adicionar coluna para observações da investigação
ALTER TABLE accidents 
ADD COLUMN investigation_notes TEXT;

-- 10. Criar função para classificar automaticamente a severidade
CREATE OR REPLACE FUNCTION classify_accident_severity_nbr()
RETURNS TRIGGER AS $$
BEGIN
    -- Se é acidente fatal, classifica como fatal
    IF NEW.is_fatal = TRUE OR NEW.type = 'fatal' THEN
        NEW.severity_nbr := 'fatal';
        NEW.is_fatal := TRUE;
    -- Se tem dias perdidos, classifica conforme NBR 14280
    ELSIF NEW.lost_days > 0 THEN
        IF NEW.lost_days BETWEEN 1 AND 15 THEN
            NEW.severity_nbr := 'leve';
        ELSIF NEW.lost_days BETWEEN 16 AND 30 THEN
            NEW.severity_nbr := 'moderado';
        ELSIF NEW.lost_days >= 31 THEN
            NEW.severity_nbr := 'grave';
        END IF;
    -- Se não tem dias perdidos e não é fatal, não classifica
    ELSE
        NEW.severity_nbr := NULL;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 11. Criar trigger para classificação automática
DROP TRIGGER IF EXISTS trigger_classify_accident_severity ON accidents;
CREATE TRIGGER trigger_classify_accident_severity
    BEFORE INSERT OR UPDATE ON accidents
    FOR EACH ROW
    EXECUTE FUNCTION classify_accident_severity_nbr();

-- 12. Atualizar registros existentes com classificação
UPDATE accidents 
SET 
    is_fatal = (type = 'fatal'),
    severity_nbr = CASE 
        WHEN type = 'fatal' THEN 'fatal'::accident_severity_nbr
        WHEN lost_days BETWEEN 1 AND 15 THEN 'leve'::accident_severity_nbr
        WHEN lost_days BETWEEN 16 AND 30 THEN 'moderado'::accident_severity_nbr
        WHEN lost_days >= 31 THEN 'grave'::accident_severity_nbr
        ELSE NULL
    END
WHERE severity_nbr IS NULL;

-- 13. Criar view para relatórios NBR 14280
CREATE OR REPLACE VIEW accidents_nbr_14280 AS
SELECT 
    a.id,
    a.occurred_at,
    a.type,
    a.classification,
    a.body_part,
    a.lost_days,
    a.description,
    a.root_cause,
    a.status,
    a.is_fatal,
    a.severity_nbr,
    a.cat_number,
    a.communication_date,
    a.investigation_completed,
    a.investigation_date,
    a.investigation_responsible,
    a.investigation_notes,
    a.created_by,
    a.created_at,
    -- Classificação legível
    CASE a.severity_nbr
        WHEN 'leve' THEN 'Leve (1-15 dias)'
        WHEN 'moderado' THEN 'Moderado (16-30 dias)'
        WHEN 'grave' THEN 'Grave (31+ dias)'
        WHEN 'fatal' THEN 'Fatal (Morte)'
        ELSE 'Não classificado'
    END as severity_description,
    -- Ícones para interface
    CASE a.severity_nbr
        WHEN 'leve' THEN '🟢'
        WHEN 'moderado' THEN '🟡'
        WHEN 'grave' THEN '🟠'
        WHEN 'fatal' THEN '🔴'
        ELSE '⚪'
    END as severity_icon,
    -- Cores para interface
    CASE a.severity_nbr
        WHEN 'leve' THEN '#28a745'
        WHEN 'moderado' THEN '#ffc107'
        WHEN 'grave' THEN '#fd7e14'
        WHEN 'fatal' THEN '#dc3545'
        ELSE '#6c757d'
    END as severity_color
FROM accidents a;

-- 14. Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_accidents_severity_nbr ON accidents(severity_nbr);
CREATE INDEX IF NOT EXISTS idx_accidents_is_fatal ON accidents(is_fatal);
CREATE INDEX IF NOT EXISTS idx_accidents_cat_number ON accidents(cat_number);
CREATE INDEX IF NOT EXISTS idx_accidents_investigation ON accidents(investigation_completed);

-- 15. Atualizar view kpi_monthly para incluir classificação NBR 14280
CREATE OR REPLACE VIEW kpi_monthly_nbr_14280 AS
WITH base AS (
    SELECT 
        created_by, 
        date_trunc('month', occurred_at)::date AS period,
        COUNT(*) FILTER (WHERE type IN ('fatal','lesao','sem_lesao')) AS accidents_total,
        COUNT(*) FILTER (WHERE type = 'fatal' OR is_fatal = TRUE) AS fatalities,
        COUNT(*) FILTER (WHERE type = 'lesao' AND is_fatal = FALSE) AS with_injury,
        COUNT(*) FILTER (WHERE type = 'sem_lesao') AS without_injury,
        SUM(lost_days) AS lost_days_total,
        -- Classificações NBR 14280
        COUNT(*) FILTER (WHERE severity_nbr = 'leve') AS accidents_leve,
        COUNT(*) FILTER (WHERE severity_nbr = 'moderado') AS accidents_moderado,
        COUNT(*) FILTER (WHERE severity_nbr = 'grave') AS accidents_grave,
        COUNT(*) FILTER (WHERE severity_nbr = 'fatal') AS accidents_fatal,
        -- Dias perdidos por classificação
        SUM(lost_days) FILTER (WHERE severity_nbr = 'leve') AS lost_days_leve,
        SUM(lost_days) FILTER (WHERE severity_nbr = 'moderado') AS lost_days_moderado,
        SUM(lost_days) FILTER (WHERE severity_nbr = 'grave') AS lost_days_grave
    FROM accidents
    GROUP BY created_by, date_trunc('month', occurred_at)
),
hours AS (
    SELECT 
        created_by, 
        make_date(year, month, 1) AS period, 
        hours
    FROM hours_worked_monthly
)
SELECT 
    b.created_by,
    b.period,
    COALESCE(h.hours, 0) AS hours,
    b.accidents_total,
    b.fatalities,
    b.with_injury,
    b.without_injury,
    b.lost_days_total,
    -- Classificações NBR 14280
    b.accidents_leve,
    b.accidents_moderado,
    b.accidents_grave,
    b.accidents_fatal,
    b.lost_days_leve,
    b.lost_days_moderado,
    b.lost_days_grave,
    -- KPIs tradicionais
    CASE 
        WHEN h.hours > 0 THEN (b.accidents_total / h.hours) * 1000000 
        ELSE 0 
    END AS freq_rate_per_million,
    CASE 
        WHEN h.hours > 0 THEN (b.lost_days_total / h.hours) * 1000000 
        ELSE 0 
    END AS sev_rate_per_million,
    -- KPIs por classificação NBR 14280
    CASE 
        WHEN h.hours > 0 THEN (b.accidents_leve / h.hours) * 1000000 
        ELSE 0 
    END AS freq_rate_leve,
    CASE 
        WHEN h.hours > 0 THEN (b.accidents_moderado / h.hours) * 1000000 
        ELSE 0 
    END AS freq_rate_moderado,
    CASE 
        WHEN h.hours > 0 THEN (b.accidents_grave / h.hours) * 1000000 
        ELSE 0 
    END AS freq_rate_grave,
    CASE 
        WHEN h.hours > 0 THEN (b.accidents_fatal / h.hours) * 1000000 
        ELSE 0 
    END AS freq_rate_fatal
FROM base b
LEFT JOIN hours h ON b.created_by = h.created_by AND b.period = h.period
ORDER BY b.created_by, b.period;

-- 16. Comentários para documentação
COMMENT ON TYPE accident_severity_nbr IS 'Classificação de severidade conforme NBR 14280:2001';
COMMENT ON COLUMN accidents.severity_nbr IS 'Classificação de severidade conforme NBR 14280 (leve, moderado, grave, fatal)';
COMMENT ON COLUMN accidents.is_fatal IS 'Indica se o acidente resultou em morte';
COMMENT ON COLUMN accidents.cat_number IS 'Número da Comunicação de Acidente de Trabalho (CAT)';
COMMENT ON COLUMN accidents.communication_date IS 'Data de comunicação do acidente aos órgãos competentes';
COMMENT ON COLUMN accidents.investigation_completed IS 'Indica se a investigação do acidente foi concluída';
COMMENT ON COLUMN accidents.investigation_date IS 'Data de conclusão da investigação';
COMMENT ON COLUMN accidents.investigation_responsible IS 'Responsável pela investigação do acidente';
COMMENT ON COLUMN accidents.investigation_notes IS 'Observações da investigação do acidente';

-- 17. Política RLS para nova view
CREATE POLICY "Users can view their own accidents NBR 14280" ON accidents_nbr_14280
    FOR SELECT USING (auth.jwt() ->> 'email' = created_by);

-- 18. Verificar se a atualização foi aplicada corretamente
SELECT 
    'Atualização NBR 14280 aplicada com sucesso!' as status,
    COUNT(*) as total_accidents,
    COUNT(*) FILTER (WHERE severity_nbr IS NOT NULL) as classified_accidents,
    COUNT(*) FILTER (WHERE is_fatal = TRUE) as fatal_accidents
FROM accidents;
