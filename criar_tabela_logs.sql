-- =============================================
-- Script para Criar Tabela de Logs de Ações
-- =============================================
-- 
-- Esta tabela armazena logs temporários de ações dos usuários no sistema
-- Logs podem ser limpos periodicamente conforme política de retenção
--
-- =============================================

-- Cria a tabela user_logs se não existir
CREATE TABLE IF NOT EXISTS public.user_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    action_type TEXT NOT NULL CHECK (action_type IN (
        'create', 'update', 'delete', 'view', 'export', 'import', 
        'login', 'logout', 'upload', 'download', 'other'
    )),
    entity_type TEXT NOT NULL,  -- Ex: 'accident', 'near_miss', 'nonconformity', 'action', 'feedback', etc.
    entity_id UUID,  -- ID da entidade relacionada (pode ser NULL para ações gerais)
    description TEXT NOT NULL,  -- Descrição da ação realizada
    ip_address TEXT,  -- Endereço IP do usuário (opcional)
    user_agent TEXT,  -- User agent do navegador (opcional)
    metadata JSONB,  -- Dados adicionais em formato JSON (opcional)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,  -- Data de expiração do log (para logs temporários)
    created_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL
);

-- Cria índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_user_logs_user_id ON public.user_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_user_logs_action_type ON public.user_logs(action_type);
CREATE INDEX IF NOT EXISTS idx_user_logs_entity_type ON public.user_logs(entity_type);
CREATE INDEX IF NOT EXISTS idx_user_logs_entity_id ON public.user_logs(entity_id);
CREATE INDEX IF NOT EXISTS idx_user_logs_created_at ON public.user_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_logs_expires_at ON public.user_logs(expires_at) WHERE expires_at IS NOT NULL;

-- Índice composto para consultas frequentes
CREATE INDEX IF NOT EXISTS idx_user_logs_user_created ON public.user_logs(user_id, created_at DESC);

-- Habilita RLS (Row Level Security)
ALTER TABLE public.user_logs ENABLE ROW LEVEL SECURITY;

-- Política RLS: Usuários podem ver apenas seus próprios logs
CREATE POLICY "Users can view their own logs"
    ON public.user_logs
    FOR SELECT
    USING (
        user_id = (SELECT id FROM profiles WHERE email = auth.jwt() ->> 'email')
        OR created_by = (SELECT id FROM profiles WHERE email = auth.jwt() ->> 'email')
    );

-- Política RLS: Sistema pode inserir logs (para registrar ações)
CREATE POLICY "System can insert logs"
    ON public.user_logs
    FOR INSERT
    WITH CHECK (
        user_id = (SELECT id FROM profiles WHERE email = auth.jwt() ->> 'email')
        OR created_by = (SELECT id FROM profiles WHERE email = auth.jwt() ->> 'email')
    );

-- Política RLS: Admins podem ver todos os logs
CREATE POLICY "Admins can view all logs"
    ON public.user_logs
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE email = auth.jwt() ->> 'email'
            AND role = 'admin'
        )
    );

-- Política RLS: Admins podem deletar logs (para limpeza)
CREATE POLICY "Admins can delete logs"
    ON public.user_logs
    FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE email = auth.jwt() ->> 'email'
            AND role = 'admin'
        )
    );

-- Função para limpar logs expirados automaticamente
CREATE OR REPLACE FUNCTION cleanup_expired_logs()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Remove logs que já expiraram (expires_at < NOW())
    DELETE FROM public.user_logs
    WHERE expires_at IS NOT NULL 
    AND expires_at < NOW();
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Função para definir expiração automática (opcional - 90 dias por padrão)
CREATE OR REPLACE FUNCTION set_log_expiration_default()
RETURNS TRIGGER AS $$
BEGIN
    -- Se expires_at não foi definido, define como 90 dias a partir de agora
    IF NEW.expires_at IS NULL THEN
        NEW.expires_at = NOW() + INTERVAL '90 days';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para definir expiração padrão (opcional - pode ser desabilitado se não quiser expiração automática)
-- Descomente se quiser expiração automática de 90 dias:
-- CREATE TRIGGER trigger_set_log_expiration
--     BEFORE INSERT ON public.user_logs
--     FOR EACH ROW
--     EXECUTE FUNCTION set_log_expiration_default();

-- Comentários na tabela e colunas
COMMENT ON TABLE public.user_logs IS 'Armazena logs temporários de ações dos usuários no sistema';
COMMENT ON COLUMN public.user_logs.action_type IS 'Tipo de ação: create, update, delete, view, export, import, login, logout, upload, download, other';
COMMENT ON COLUMN public.user_logs.entity_type IS 'Tipo de entidade afetada: accident, near_miss, nonconformity, action, feedback, profile, etc.';
COMMENT ON COLUMN public.user_logs.entity_id IS 'ID da entidade relacionada à ação (NULL para ações gerais)';
COMMENT ON COLUMN public.user_logs.description IS 'Descrição detalhada da ação realizada';
COMMENT ON COLUMN public.user_logs.metadata IS 'Dados adicionais em formato JSON (ex: campos alterados, valores antigos/novos)';
COMMENT ON COLUMN public.user_logs.expires_at IS 'Data de expiração do log. Logs expirados podem ser removidos automaticamente';
COMMENT ON COLUMN public.user_logs.ip_address IS 'Endereço IP do usuário quando a ação foi realizada';
COMMENT ON COLUMN public.user_logs.user_agent IS 'User agent do navegador quando a ação foi realizada';

-- Cria uma view para logs recentes (últimos 30 dias)
CREATE OR REPLACE VIEW public.recent_user_logs AS
SELECT 
    ul.id,
    ul.user_id,
    p.email AS user_email,
    p.full_name AS user_name,
    ul.action_type,
    ul.entity_type,
    ul.entity_id,
    ul.description,
    ul.ip_address,
    ul.user_agent,
    ul.metadata,
    ul.created_at,
    ul.expires_at
FROM public.user_logs ul
LEFT JOIN public.profiles p ON p.id = ul.user_id
WHERE ul.created_at >= NOW() - INTERVAL '30 days'
ORDER BY ul.created_at DESC;

-- Comentário na view
COMMENT ON VIEW public.recent_user_logs IS 'View com logs recentes dos últimos 30 dias, incluindo informações do usuário';

