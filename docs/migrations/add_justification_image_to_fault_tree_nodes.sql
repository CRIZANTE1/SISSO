-- Migration: Adicionar campo justification_image_url à tabela fault_tree_nodes
-- Data: 2025-01-29
-- Descrição: Adiciona campo para armazenar URL da imagem associada à justificativa da hipótese

-- Adiciona coluna justification_image_url (nullable)
ALTER TABLE fault_tree_nodes 
ADD COLUMN IF NOT EXISTS justification_image_url TEXT;

-- Comentário na coluna
COMMENT ON COLUMN fault_tree_nodes.justification_image_url IS 'URL da imagem associada à justificativa da hipótese. A imagem será exibida no relatório PDF junto com a justificativa.';

