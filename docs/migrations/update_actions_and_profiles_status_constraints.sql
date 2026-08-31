-- Migration: Atualizar constraints de status em profiles e actions
-- Data: 2026-08-31
-- Descrição: 
--   1. Permite o status 'pendente' na tabela profiles para fluxo de auto-cadastro e aprovação.
--   2. Permite os status 'em_andamento' e 'fechada' na tabela actions (5W2H) para compatibilidade com o frontend.
--   3. Garante existência da tabela attachments para evidências de acidentes e não conformidades.

-- ============================================================================
-- 1. ATUALIZAÇÃO DE CONSTRAINT DE STATUS EM PROFILES
-- ============================================================================
ALTER TABLE public.profiles 
  DROP CONSTRAINT IF EXISTS profiles_status_check;

ALTER TABLE public.profiles 
  ADD CONSTRAINT profiles_status_check 
  CHECK (status IN ('ativo', 'inativo', 'suspenso', 'pendente'));

COMMENT ON CONSTRAINT profiles_status_check ON public.profiles IS 
  'Status do usuário: ativo, inativo, suspenso ou pendente de aprovação por administrador';

-- ============================================================================
-- 2. ATUALIZAÇÃO DE CONSTRAINT DE STATUS EM ACTIONS (5W2H)
-- ============================================================================
ALTER TABLE public.actions 
  DROP CONSTRAINT IF EXISTS actions_status_check;

ALTER TABLE public.actions 
  ADD CONSTRAINT actions_status_check 
  CHECK (status IN ('aberta', 'em_andamento', 'em_execucao', 'fechada', 'concluida', 'cancelada'));

COMMENT ON CONSTRAINT actions_status_check ON public.actions IS 
  'Status da ação 5W2H: aberta, em_andamento, em_execucao, fechada, concluida, cancelada';

-- ============================================================================
-- 3. GARANTIR TABELA ATTACHMENTS (EVIDÊNCIAS E ANEXOS)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bucket TEXT NOT NULL DEFAULT 'evidencias',
    path TEXT NOT NULL,
    entity_type TEXT CHECK (entity_type IN ('accident', 'near_miss', 'nonconformity', 'action')),
    entity_id UUID NOT NULL,
    uploaded_by TEXT,
    uploaded_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.attachments ENABLE ROW LEVEL SECURITY;

DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE tablename = 'attachments' AND policyname = 'Allow all access to attachments'
  ) THEN
    CREATE POLICY "Allow all access to attachments" 
    ON public.attachments 
    FOR ALL 
    USING (true) 
    WITH CHECK (true);
  END IF;
END $$;
