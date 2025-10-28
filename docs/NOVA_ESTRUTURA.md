# 🔄 Nova Estrutura do Sistema SSO

## Principais Mudanças

### 1. Simplificação da Arquitetura
- **Removido**: Conceito de sites e contratadas
- **Foco**: Usuário individual como unidade de análise
- **Benefício**: Sistema mais simples e direto

### 2. Nova Estrutura de Dados

#### Tabelas Principais
```sql
-- Perfis de usuário (vinculados ao Auth)
profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id),
  full_name TEXT,
  role TEXT CHECK (role IN ('admin','editor','viewer')),
  created_at TIMESTAMPTZ DEFAULT NOW()
)

-- Horas trabalhadas por usuário/mês
hours_worked_monthly (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  year INT NOT NULL,
  month INT NOT NULL CHECK (month BETWEEN 1 AND 12),
  hours NUMERIC NOT NULL CHECK (hours >= 0),
  created_by UUID REFERENCES auth.users(id),
  UNIQUE (year, month, created_by)
)

-- Acidentes com enum para tipo
accidents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  occurred_at DATE NOT NULL,
  type accident_type NOT NULL, -- ENUM: 'fatal','lesao','sem_lesao'
  classification TEXT,
  body_part TEXT,
  lost_days INT DEFAULT 0,
  description TEXT,
  root_cause TEXT,
  status TEXT DEFAULT 'fechado',
  created_by UUID REFERENCES auth.users(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
)

-- Quase-acidentes simplificados
near_misses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  occurred_at DATE NOT NULL,
  description TEXT,
  potential_severity TEXT,
  status TEXT DEFAULT 'aberto',
  created_by UUID REFERENCES auth.users(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
)

-- Não conformidades
nonconformities (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  opened_at DATE NOT NULL,
  standard_ref TEXT,
  severity TEXT CHECK (severity IN ('leve','moderada','grave','critica')),
  description TEXT,
  status TEXT DEFAULT 'aberta',
  created_by UUID REFERENCES auth.users(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
)

-- Plano de ações 5W2H
actions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  entity_type TEXT CHECK (entity_type IN ('accident','near_miss','nonconformity')),
  entity_id UUID NOT NULL,
  what TEXT NOT NULL,
  who TEXT,
  when_date DATE,
  where_text TEXT,
  why TEXT,
  how TEXT,
  how_much NUMERIC,
  status TEXT DEFAULT 'aberta',
  created_by UUID REFERENCES auth.users(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
)

-- Anexos/evidências
attachments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  bucket TEXT NOT NULL DEFAULT 'evidencias',
  path TEXT NOT NULL,
  entity_type TEXT CHECK (entity_type IN ('accident','near_miss','nonconformity','action')),
  entity_id UUID NOT NULL,
  uploaded_by UUID REFERENCES auth.users(id),
  uploaded_at TIMESTAMPTZ DEFAULT NOW()
)
```

### 3. View de KPIs Atualizada

```sql
CREATE VIEW public.kpi_monthly AS
WITH base AS (
  SELECT created_by, date_trunc('month', occurred_at)::date AS period,
         COUNT(*) FILTER (WHERE type IN ('fatal','lesao','sem_lesao')) AS accidents_total,
         COUNT(*) FILTER (WHERE type = 'fatal') AS fatalities,
         COUNT(*) FILTER (WHERE type = 'lesao') AS with_injury,
         COUNT(*) FILTER (WHERE type = 'sem_lesao') AS without_injury,
         SUM(lost_days) AS lost_days_total
  FROM public.accidents
  GROUP BY created_by, date_trunc('month', occurred_at)
),
hours AS (
  SELECT created_by, make_date(year, month, 1) AS period, hours
  FROM public.hours_worked_monthly
)
SELECT b.created_by,
       b.period,
       COALESCE(b.accidents_total,0) AS accidents_total,
       COALESCE(b.fatalities,0) AS fatalities,
       COALESCE(b.with_injury,0) AS with_injury,
       COALESCE(b.without_injury,0) AS without_injury,
       COALESCE(b.lost_days_total,0) AS lost_days_total,
       COALESCE(h.hours,0) AS hours,
       CASE WHEN COALESCE(h.hours,0) > 0 THEN (COALESCE(b.accidents_total,0) / h.hours) * 1000000 ELSE NULL END AS freq_rate_per_million,
       CASE WHEN COALESCE(h.hours,0) > 0 THEN (COALESCE(b.lost_days_total,0) / h.hours) * 1000000 ELSE NULL END AS severity_rate_per_million
FROM base b
LEFT JOIN hours h ON h.created_by = b.created_by AND h.period = b.period
ORDER BY b.period DESC;
```

### 4. Row Level Security (RLS)

#### Políticas Simplificadas
- **Usuários**: Veem apenas seus próprios dados
- **Admins**: Podem ver todos os dados
- **Isolamento**: Completo por usuário

```sql
-- Exemplo de política RLS
CREATE POLICY "Users can view their own accidents" ON accidents
    FOR SELECT USING (auth.uid() = created_by);

CREATE POLICY "Users can manage their own accidents" ON accidents
    FOR ALL USING (auth.uid() = created_by);
```

### 5. Impacto no Código

#### Serviços Atualizados
- **auth.py**: Busca perfil do usuário na tabela profiles
- **kpi.py**: Filtra por created_by em vez de site_codes
- **uploads.py**: Inclui user_id nos uploads

#### Componentes Atualizados
- **filters.py**: Remove filtros de sites, adiciona filtros de usuários
- **pages/**: Todas as páginas adaptadas para nova estrutura

#### Páginas Atualizadas
- **Visão Geral**: Análise por período em vez de por site
- **Acidentes**: Formulário com novos campos (tipo, classificação, parte do corpo)
- **Quase-Acidentes**: Campos simplificados
- **Não Conformidades**: Campos atualizados
- **Admin**: Foco em usuários em vez de sites/contratadas

### 6. Benefícios da Nova Estrutura

#### Simplicidade
- Menos tabelas para gerenciar
- Lógica mais direta
- Menos complexidade de relacionamentos

#### Performance
- Queries mais simples
- Menos JOINs necessários
- Índices mais eficientes

#### Segurança
- RLS mais simples de implementar
- Isolamento natural por usuário
- Menos superfície de ataque

#### Manutenibilidade
- Código mais limpo
- Menos dependências
- Mais fácil de entender e modificar

### 7. Migração de Dados

#### Se você já tem dados na estrutura antiga:
1. **Backup**: Faça backup dos dados existentes
2. **Mapeamento**: Mapeie sites para usuários
3. **Migração**: Crie script para migrar dados
4. **Validação**: Verifique integridade dos dados

#### Script de migração exemplo:
```sql
-- Migrar acidentes da estrutura antiga para nova
INSERT INTO accidents (occurred_at, type, description, lost_days, root_cause, created_by)
SELECT 
    date as occurred_at,
    CASE 
        WHEN severity = 'fatal' THEN 'fatal'::accident_type
        WHEN severity = 'with_injury' THEN 'lesao'::accident_type
        WHEN severity = 'without_injury' THEN 'sem_lesao'::accident_type
    END as type,
    description,
    lost_days,
    root_cause,
    'user-id-aqui' as created_by
FROM old_accidents_table;
```

### 8. Configuração Inicial

#### 1. Execute o script SQL
```bash
# No SQL Editor do Supabase
# Execute o conteúdo de database_setup.sql
```

#### 2. Configure o Storage
- Crie bucket `evidencias`
- Configure como privado
- Limite de 50MB por arquivo

#### 3. Configure usuários
- Crie perfis na tabela `profiles`
- Configure roles (admin, editor, viewer)
- Teste RLS

#### 4. Importe dados
- Use o formato CSV conforme documentado
- Valide importação

### 9. Testes

#### Teste de RLS
```sql
-- Como usuário específico
SET LOCAL "request.jwt.claims" TO '{"sub": "user-id-aqui"}';
SELECT * FROM accidents; -- Deve retornar apenas dados do usuário
```

#### Teste de KPIs
```sql
-- Verificar view de KPIs
SELECT * FROM kpi_monthly WHERE created_by = 'user-id-aqui';
```

#### Teste de Upload
- Teste upload de evidências
- Verifique permissões
- Valide anexos no Storage

### 10. Monitoramento

#### Logs a verificar
- Queries de RLS
- Uploads de arquivos
- Cálculos de KPIs
- Erros de autenticação

#### Métricas importantes
- Performance das queries
- Uso do Storage
- Taxa de erro de RLS
- Tempo de resposta dos KPIs

## Conclusão

A nova estrutura é mais simples, segura e eficiente. O foco em usuário individual torna o sistema mais direto e fácil de usar, mantendo todas as funcionalidades de análise estatística e controles de segurança.
