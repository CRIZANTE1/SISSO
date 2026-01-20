-- Migration: Adicionar campo display_order à tabela fault_tree_nodes
-- Data: 2025-01-29
-- Descrição: Adiciona campo para controlar a ordem de exibição dos nós na árvore de falhas
-- CRÍTICO: Este campo é essencial para o funcionamento do sistema de investigação

-- Adiciona coluna display_order (nullable, será preenchido pelo sistema)
ALTER TABLE fault_tree_nodes 
ADD COLUMN IF NOT EXISTS display_order INTEGER;

-- Comentário na coluna
COMMENT ON COLUMN fault_tree_nodes.display_order IS 'Ordem de exibição dos nós na árvore de falhas. Usado para ordenar nós filhos do mesmo parent. O sistema calcula automaticamente ao adicionar novos nós.';

-- Índice para melhor performance em queries de ordenação
CREATE INDEX IF NOT EXISTS idx_fault_tree_nodes_display_order 
ON fault_tree_nodes(accident_id, parent_id, display_order);

-- Atualiza nós existentes: define display_order baseado em created_at
-- Para nós do mesmo parent_id, ordena por created_at e define display_order sequencial
UPDATE fault_tree_nodes AS ftn1
SET display_order = (
    SELECT COUNT(*) + 1
    FROM fault_tree_nodes AS ftn2
    WHERE ftn2.accident_id = ftn1.accident_id
      AND COALESCE(ftn2.parent_id::text, '') = COALESCE(ftn1.parent_id::text, '')
      AND ftn2.created_at < ftn1.created_at
      AND ftn2.id != ftn1.id
)
WHERE display_order IS NULL;

-- Se ainda houver NULLs (para nós com mesmo created_at), define baseado em id
UPDATE fault_tree_nodes
SET display_order = 1
WHERE display_order IS NULL;
