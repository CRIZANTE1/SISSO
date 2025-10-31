-- =============================================
-- Script para Criar Tabela kpi_monthly
-- =============================================
-- 
-- Esta tabela armazena KPIs mensais calculados
-- baseados em acidentes e horas trabalhadas
--
-- =============================================

-- Remove view se existir
DROP VIEW IF EXISTS public.kpi_monthly CASCADE;

-- Cria a tabela kpi_monthly
CREATE TABLE IF NOT EXISTS public.kpi_monthly (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    period DATE NOT NULL,
    created_by UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    accidents_total INTEGER DEFAULT 0,
    fatalities INTEGER DEFAULT 0,
    lost_days_total INTEGER DEFAULT 0,
    hours NUMERIC DEFAULT 0,
    frequency_rate NUMERIC DEFAULT 0,
    severity_rate NUMERIC DEFAULT 0,
    debited_days INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(period, created_by)
);

-- Cria índice para melhor performance
CREATE INDEX IF NOT EXISTS idx_kpi_monthly_period ON public.kpi_monthly(period);
CREATE INDEX IF NOT EXISTS idx_kpi_monthly_created_by ON public.kpi_monthly(created_by);
CREATE INDEX IF NOT EXISTS idx_kpi_monthly_period_user ON public.kpi_monthly(period, created_by);

-- Habilita RLS na tabela
ALTER TABLE public.kpi_monthly ENABLE ROW LEVEL SECURITY;

-- Políticas RLS para kpi_monthly
CREATE POLICY "Users can view their own kpi"
    ON public.kpi_monthly
    FOR SELECT
    USING (
        created_by::uuid = (SELECT id::uuid FROM public.profiles WHERE email = (auth.jwt() ->> 'email') LIMIT 1)
        OR EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE email = (auth.jwt() ->> 'email')
            AND role = 'admin'
        )
    );

CREATE POLICY "Users can insert their own kpi"
    ON public.kpi_monthly
    FOR INSERT
    WITH CHECK (
        created_by::uuid = (SELECT id::uuid FROM public.profiles WHERE email = (auth.jwt() ->> 'email') LIMIT 1)
        OR EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE email = (auth.jwt() ->> 'email')
            AND role = 'admin'
        )
    );

CREATE POLICY "Users can update their own kpi"
    ON public.kpi_monthly
    FOR UPDATE
    USING (
        created_by::uuid = (SELECT id::uuid FROM public.profiles WHERE email = (auth.jwt() ->> 'email') LIMIT 1)
        OR EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE email = (auth.jwt() ->> 'email')
            AND role = 'admin'
        )
    )
    WITH CHECK (
        created_by::uuid = (SELECT id::uuid FROM public.profiles WHERE email = (auth.jwt() ->> 'email') LIMIT 1)
        OR EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE email = (auth.jwt() ->> 'email')
            AND role = 'admin'
        )
    );

CREATE POLICY "Users can delete their own kpi"
    ON public.kpi_monthly
    FOR DELETE
    USING (
        created_by::uuid = (SELECT id::uuid FROM public.profiles WHERE email = (auth.jwt() ->> 'email') LIMIT 1)
        OR EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE email = (auth.jwt() ->> 'email')
            AND role = 'admin'
        )
    );

