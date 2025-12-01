-- Migration: Adicionar campo justification à tabela fault_tree_nodes
-- Data: 2025-01-29
-- Descrição: Adiciona campo para armazenar justificativas ao confirmar ou descartar hipóteses

-- Adiciona coluna justification (nullable, pode ser preenchida posteriormente)
ALTER TABLE fault_tree_nodes 
ADD COLUMN IF NOT EXISTS justification TEXT;

-- Comentário na coluna
COMMENT ON COLUMN fault_tree_nodes.justification IS 'Justificativa para confirmação ou descarte da hipótese. Usado no relatório PDF.';

-- Índice opcional para buscas (se necessário)
-- CREATE INDEX IF NOT EXISTS idx_fault_tree_nodes_justification 
-- ON fault_tree_nodes(justification) 
-- WHERE justification IS NOT NULL;

