-- Migration: Criar tabela commission_actions
-- Data: 2025-01-29
-- Descrição: Tabela para armazenar ações executadas pela comissão durante a investigação

-- Cria tabela commission_actions
CREATE TABLE IF NOT EXISTS commission_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    accident_id UUID NOT NULL REFERENCES accidents(id) ON DELETE CASCADE,
    action_time TIMESTAMPTZ NOT NULL,
    description TEXT NOT NULL,
    action_type TEXT,
    responsible_person TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    created_by UUID REFERENCES auth.users(id)
);

-- Comentários nas colunas
COMMENT ON TABLE commission_actions IS 'Ações executadas pela comissão durante a investigação do acidente';
COMMENT ON COLUMN commission_actions.action_time IS 'Data e hora em que a ação foi executada';
COMMENT ON COLUMN commission_actions.description IS 'Descrição detalhada da ação executada';
COMMENT ON COLUMN commission_actions.action_type IS 'Tipo de ação (ex: entrevista, inspeção, análise, reunião, etc.)';
COMMENT ON COLUMN commission_actions.responsible_person IS 'Nome da pessoa responsável pela ação';

-- Índice para melhor performance
CREATE INDEX IF NOT EXISTS idx_commission_actions_accident_id ON commission_actions(accident_id);
CREATE INDEX IF NOT EXISTS idx_commission_actions_action_time ON commission_actions(action_time);

-- Habilita RLS
ALTER TABLE commission_actions ENABLE ROW LEVEL SECURITY;

-- Política RLS básica (ajustar conforme necessário)
CREATE POLICY "Users can view commission actions for their accidents"
    ON commission_actions FOR SELECT
    USING (true);

CREATE POLICY "Users can insert commission actions for their accidents"
    ON commission_actions FOR INSERT
    WITH CHECK (true);

CREATE POLICY "Users can update commission actions for their accidents"
    ON commission_actions FOR UPDATE
    USING (true);

CREATE POLICY "Users can delete commission actions for their accidents"
    ON commission_actions FOR DELETE
    USING (true);

