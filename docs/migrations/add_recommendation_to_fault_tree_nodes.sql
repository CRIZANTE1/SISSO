-- Migration: Adicionar campo recommendation à tabela fault_tree_nodes
-- Data: 2025-01-29
-- Descrição: Adiciona campo para armazenar recomendações para cada causa básica ou contribuinte

-- Adiciona coluna recommendation (nullable)
ALTER TABLE fault_tree_nodes 
ADD COLUMN IF NOT EXISTS recommendation TEXT;

-- Comentário na coluna
COMMENT ON COLUMN fault_tree_nodes.recommendation IS 'Recomendações para prevenir ou corrigir a causa básica ou contribuinte. Será exibida no relatório PDF ao final.';

