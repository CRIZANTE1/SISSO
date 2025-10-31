-- =============================================
-- Script para Criar Tabela de Feedbacks
-- =============================================
-- 
-- Esta tabela armazena feedbacks de erros e sugestões dos usuários
--
-- =============================================

-- Cria a tabela feedbacks se não existir
CREATE TABLE IF NOT EXISTS public.feedbacks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('erro', 'sugestao', 'melhoria', 'outro')),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT DEFAULT 'aberto' CHECK (status IN ('aberto', 'em_analise', 'resolvido', 'rejeitado')),
    priority TEXT DEFAULT 'media' CHECK (priority IN ('baixa', 'media', 'alta')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    admin_notes TEXT,
    created_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL
);

-- Cria índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_feedbacks_user_id ON public.feedbacks(user_id);
CREATE INDEX IF NOT EXISTS idx_feedbacks_type ON public.feedbacks(type);
CREATE INDEX IF NOT EXISTS idx_feedbacks_status ON public.feedbacks(status);
CREATE INDEX IF NOT EXISTS idx_feedbacks_created_at ON public.feedbacks(created_at DESC);

-- Habilita RLS (Row Level Security)
ALTER TABLE public.feedbacks ENABLE ROW LEVEL SECURITY;

-- Política RLS: Usuários podem ver apenas seus próprios feedbacks
CREATE POLICY "Users can view their own feedbacks"
    ON public.feedbacks
    FOR SELECT
    USING (
        user_id = (SELECT id FROM profiles WHERE email = auth.jwt() ->> 'email')
        OR created_by = (SELECT id FROM profiles WHERE email = auth.jwt() ->> 'email')
    );

-- Política RLS: Usuários podem criar seus próprios feedbacks
CREATE POLICY "Users can insert their own feedbacks"
    ON public.feedbacks
    FOR INSERT
    WITH CHECK (
        user_id = (SELECT id FROM profiles WHERE email = auth.jwt() ->> 'email')
    );

-- Política RLS: Usuários podem atualizar seus próprios feedbacks (apenas se estiver aberto)
CREATE POLICY "Users can update their own open feedbacks"
    ON public.feedbacks
    FOR UPDATE
    USING (
        user_id = (SELECT id FROM profiles WHERE email = auth.jwt() ->> 'email')
        AND status = 'aberto'
    );

-- Política RLS: Admins podem ver todos os feedbacks
CREATE POLICY "Admins can view all feedbacks"
    ON public.feedbacks
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE email = auth.jwt() ->> 'email'
            AND role = 'admin'
        )
    );

-- Política RLS: Admins podem atualizar todos os feedbacks
CREATE POLICY "Admins can update all feedbacks"
    ON public.feedbacks
    FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE email = auth.jwt() ->> 'email'
            AND role = 'admin'
        )
    );

-- Política RLS: Admins podem deletar todos os feedbacks
CREATE POLICY "Admins can delete all feedbacks"
    ON public.feedbacks
    FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE email = auth.jwt() ->> 'email'
            AND role = 'admin'
        )
    );

-- Comentários na tabela e colunas
COMMENT ON TABLE public.feedbacks IS 'Armazena feedbacks de erros, sugestões e melhorias dos usuários';
COMMENT ON COLUMN public.feedbacks.type IS 'Tipo de feedback: erro, sugestao, melhoria, outro';
COMMENT ON COLUMN public.feedbacks.status IS 'Status do feedback: aberto, em_analise, resolvido, rejeitado';
COMMENT ON COLUMN public.feedbacks.priority IS 'Prioridade: baixa, media, alta';
COMMENT ON COLUMN public.feedbacks.admin_notes IS 'Notas do administrador sobre o feedback';

-- Trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_feedbacks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_feedbacks_updated_at
    BEFORE UPDATE ON public.feedbacks
    FOR EACH ROW
    EXECUTE FUNCTION update_feedbacks_updated_at();

-- Trigger para atualizar resolved_at quando status muda para resolvido
CREATE OR REPLACE FUNCTION update_feedbacks_resolved_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'resolvido' AND OLD.status != 'resolvido' THEN
        NEW.resolved_at = NOW();
    ELSIF NEW.status != 'resolvido' THEN
        NEW.resolved_at = NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_feedbacks_resolved_at
    BEFORE UPDATE ON public.feedbacks
    FOR EACH ROW
    EXECUTE FUNCTION update_feedbacks_resolved_at();

