-- Migration: Adicionar campos detalhados de Segurança de Processo
-- Data: 2025-01-29
-- Descrição: Adiciona campos para incêndio, explosão, transportadora, perdas detalhadas e observações de segurança de processo

-- ========== CAMPOS DE INCÊNDIO ==========
ALTER TABLE accidents 
ADD COLUMN IF NOT EXISTS has_fire BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS fire_area TEXT,
ADD COLUMN IF NOT EXISTS fire_duration_hours NUMERIC,
ADD COLUMN IF NOT EXISTS fire_observation TEXT;

-- ========== CAMPOS DE EXPLOSÃO ==========
ALTER TABLE accidents 
ADD COLUMN IF NOT EXISTS has_explosion BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS explosion_type TEXT,
ADD COLUMN IF NOT EXISTS explosion_area TEXT,
ADD COLUMN IF NOT EXISTS explosion_duration_hours NUMERIC,
ADD COLUMN IF NOT EXISTS explosion_observation TEXT;

-- ========== CAMPOS DA TRANSPORTADORA ==========
ALTER TABLE accidents 
ADD COLUMN IF NOT EXISTS transporter_name TEXT,
ADD COLUMN IF NOT EXISTS transporter_cnpj TEXT,
ADD COLUMN IF NOT EXISTS transporter_contract_number TEXT,
ADD COLUMN IF NOT EXISTS transporter_contract_start DATE,
ADD COLUMN IF NOT EXISTS transporter_contract_end DATE;

-- ========== OBSERVAÇÃO DE SEGURANÇA DE PROCESSO ==========
ALTER TABLE accidents 
ADD COLUMN IF NOT EXISTS process_safety_observation TEXT;

-- ========== CAMPOS DETALHADOS DE PERDAS ==========
ALTER TABLE accidents 
ADD COLUMN IF NOT EXISTS loss_product NUMERIC DEFAULT 0,
ADD COLUMN IF NOT EXISTS loss_material NUMERIC DEFAULT 0,
ADD COLUMN IF NOT EXISTS loss_vacuum_truck NUMERIC DEFAULT 0,
ADD COLUMN IF NOT EXISTS loss_indirect_contractor NUMERIC DEFAULT 0,
ADD COLUMN IF NOT EXISTS loss_overtime_hours NUMERIC DEFAULT 0,
ADD COLUMN IF NOT EXISTS loss_civil_works NUMERIC DEFAULT 0,
ADD COLUMN IF NOT EXISTS loss_waste_containers NUMERIC DEFAULT 0,
ADD COLUMN IF NOT EXISTS loss_mechanical_works NUMERIC DEFAULT 0,
ADD COLUMN IF NOT EXISTS loss_mobilization NUMERIC DEFAULT 0,
ADD COLUMN IF NOT EXISTS loss_total NUMERIC DEFAULT 0;

-- ========== CAMPOS ADICIONAIS DO CONDUTOR (tabela involved_people) ==========
ALTER TABLE involved_people 
ADD COLUMN IF NOT EXISTS time_in_company TEXT,
ADD COLUMN IF NOT EXISTS time_driving_vehicle_type TEXT,
ADD COLUMN IF NOT EXISTS time_license TEXT,
ADD COLUMN IF NOT EXISTS driver_observation TEXT;

-- Comentários nas colunas de incêndio
COMMENT ON COLUMN accidents.has_fire IS 'Indica se ocorreu incêndio';
COMMENT ON COLUMN accidents.fire_area IS 'Área afetada pelo incêndio';
COMMENT ON COLUMN accidents.fire_duration_hours IS 'Duração do incêndio em horas';
COMMENT ON COLUMN accidents.fire_observation IS 'Observações sobre o incêndio';

-- Comentários nas colunas de explosão
COMMENT ON COLUMN accidents.has_explosion IS 'Indica se ocorreu explosão';
COMMENT ON COLUMN accidents.explosion_type IS 'Tipo de explosão';
COMMENT ON COLUMN accidents.explosion_area IS 'Área afetada pela explosão';
COMMENT ON COLUMN accidents.explosion_duration_hours IS 'Duração/efeito da explosão em horas';
COMMENT ON COLUMN accidents.explosion_observation IS 'Observações sobre a explosão';

-- Comentários nas colunas da transportadora
COMMENT ON COLUMN accidents.transporter_name IS 'Nome da transportadora';
COMMENT ON COLUMN accidents.transporter_cnpj IS 'CNPJ da transportadora';
COMMENT ON COLUMN accidents.transporter_contract_number IS 'Número do contrato com a transportadora';
COMMENT ON COLUMN accidents.transporter_contract_start IS 'Data de início do contrato';
COMMENT ON COLUMN accidents.transporter_contract_end IS 'Data de fim do contrato';

-- Comentários nas colunas de perdas
COMMENT ON COLUMN accidents.loss_product IS 'Valor da perda do produto';
COMMENT ON COLUMN accidents.loss_material IS 'Valor da perda material';
COMMENT ON COLUMN accidents.loss_vacuum_truck IS 'Valor do caminhão vácuo';
COMMENT ON COLUMN accidents.loss_indirect_contractor IS 'Efetivo Indireto - empreiteira';
COMMENT ON COLUMN accidents.loss_overtime_hours IS 'Custos de horas extras pessoal';
COMMENT ON COLUMN accidents.loss_civil_works IS 'Obras civis - empreiteira';
COMMENT ON COLUMN accidents.loss_waste_containers IS 'Caçambas de resíduos';
COMMENT ON COLUMN accidents.loss_mechanical_works IS 'Obras mecânicas - empreiteira';
COMMENT ON COLUMN accidents.loss_mobilization IS 'Mobilização - empreiteira';
COMMENT ON COLUMN accidents.loss_total IS 'Valor total calculado das perdas';

-- Comentários nas colunas do condutor
COMMENT ON COLUMN involved_people.time_in_company IS 'Tempo na empresa';
COMMENT ON COLUMN involved_people.time_driving_vehicle_type IS 'Tempo dirigindo o tipo de veículo';
COMMENT ON COLUMN involved_people.time_license IS 'Tempo de habilitação';
COMMENT ON COLUMN involved_people.driver_observation IS 'Observações sobre o condutor';
