-- Migration: Adicionar campo is_contributing_cause à tabela fault_tree_nodes
-- Data: 2025-01-29
-- Descrição: Adiciona campo para marcar causas contribuintes nas hipóteses validadas

-- Adiciona coluna is_contributing_cause (nullable, default FALSE)
ALTER TABLE fault_tree_nodes 
ADD COLUMN IF NOT EXISTS is_contributing_cause BOOLEAN DEFAULT FALSE;

-- Comentário na coluna
COMMENT ON COLUMN fault_tree_nodes.is_contributing_cause IS 'Indica se o nó é uma causa contribuinte (marcado manualmente pelo usuário). Causas contribuintes são fatores que contribuem para o acidente mas não são causas básicas.';

