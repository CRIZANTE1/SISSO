-- Migration: Adicionar campos detalhados do perfil do acidentado à tabela involved_people
-- Data: 2025-01-29
-- Descrição: Adiciona campos para registro completo do perfil do acidentado conforme especificação do relatório Vibra

-- Adiciona campos de dados pessoais
ALTER TABLE involved_people 
ADD COLUMN IF NOT EXISTS birth_date DATE,
ADD COLUMN IF NOT EXISTS rg TEXT,
ADD COLUMN IF NOT EXISTS marital_status TEXT,
ADD COLUMN IF NOT EXISTS birthplace TEXT,
ADD COLUMN IF NOT EXISTS children_count INTEGER;

-- Adiciona campos de lesão e acidente
ALTER TABLE involved_people 
ADD COLUMN IF NOT EXISTS injury_type TEXT,
ADD COLUMN IF NOT EXISTS body_part TEXT,
ADD COLUMN IF NOT EXISTS lost_days INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS cat_number TEXT,
ADD COLUMN IF NOT EXISTS is_fatal BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS employment_type TEXT,
ADD COLUMN IF NOT EXISTS previous_accident_history BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS certifications TEXT;

-- Adiciona constraint CHECK para employment_type
ALTER TABLE involved_people 
DROP CONSTRAINT IF EXISTS involved_people_employment_type_check;

ALTER TABLE involved_people 
ADD CONSTRAINT involved_people_employment_type_check 
CHECK (employment_type IS NULL OR employment_type IN ('Empregado', 'Contratado', 'Terceiros/Comunidade'));

-- Comentários nas colunas
COMMENT ON COLUMN involved_people.birth_date IS 'Data de nascimento do acidentado';
COMMENT ON COLUMN involved_people.rg IS 'RG (Registro Geral) do acidentado';
COMMENT ON COLUMN involved_people.marital_status IS 'Estado civil do acidentado';
COMMENT ON COLUMN involved_people.birthplace IS 'Naturalidade do acidentado';
COMMENT ON COLUMN involved_people.children_count IS 'Número de filhos do acidentado';
COMMENT ON COLUMN involved_people.injury_type IS 'Tipo de lesão sofrida';
COMMENT ON COLUMN involved_people.body_part IS 'Parte do corpo afetada pela lesão';
COMMENT ON COLUMN involved_people.lost_days IS 'Dias perdidos devido à lesão';
COMMENT ON COLUMN involved_people.cat_number IS 'Número da CAT (Comunicação de Acidente de Trabalho)';
COMMENT ON COLUMN involved_people.is_fatal IS 'Indica se o acidente resultou em fatalidade';
COMMENT ON COLUMN involved_people.employment_type IS 'Tipo de vínculo: Empregado, Contratado ou Terceiros/Comunidade';
COMMENT ON COLUMN involved_people.previous_accident_history IS 'Indica se o acidentado tem histórico de acidentes anteriores';
COMMENT ON COLUMN involved_people.certifications IS 'Capacitações e validades do acidentado';
