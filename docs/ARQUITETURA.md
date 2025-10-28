# 🏗️ Arquitetura do Sistema SSO

## Visão Geral

O Sistema de Monitoramento SSO é uma aplicação web construída com Streamlit e Supabase, projetada para análise estatística de dados de segurança e saúde ocupacional.

## Diagrama de Arquitetura

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Usuário       │    │   Streamlit App  │    │   Supabase      │
│   (Browser)     │◄──►│   (Frontend)     │◄──►│   (Backend)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                │                        ├── PostgreSQL
                                │                        ├── Auth
                                │                        ├── Storage
                                │                        └── Edge Functions
                                │
                                ▼
                       ┌──────────────────┐
                       │   Análise de     │
                       │   Dados          │
                       │   (Pandas/       │
                       │   NumPy/SciPy)   │
                       └──────────────────┘
```

## Componentes Principais

### 1. Frontend (Streamlit)
- **Framework**: Streamlit 1.39.0
- **Visualização**: Plotly, Altair
- **UI Components**: Streamlit nativo + AgGrid
- **Autenticação**: Supabase Auth integration

### 2. Backend (Supabase)
- **Banco de Dados**: PostgreSQL 15+
- **Autenticação**: Supabase Auth (JWT)
- **Storage**: Supabase Storage (evidências)
- **API**: REST + RPC functions
- **Segurança**: Row Level Security (RLS)

### 3. Análise de Dados
- **Processamento**: Pandas, NumPy
- **Estatística**: SciPy
- **Visualização**: Plotly, Streamlit Charts
- **Controles**: Implementação customizada

## Estrutura de Dados

### Modelo Relacional

```sql
sites (1) ──┐
            ├── hours_worked_monthly (N)
            ├── accidents (N)
            ├── near_misses (N)
            └── nonconformities (N)

contractors (1) ──┐
                  ├── accidents (N)
                  ├── near_misses (N)
                  └── nonconformities (N)

profiles (1) ──┐
               └── auth.users (1)

attachments (N) ──┐
                  ├── accidents (1)
                  ├── near_misses (1)
                  └── nonconformities (1)
```

### View Materializada

```sql
kpi_monthly AS
SELECT 
    site_id,
    period,
    hours,
    accidents_total,
    fatalities,
    with_injury,
    without_injury,
    lost_days_total,
    freq_rate_per_million,
    sev_rate_per_million
FROM hours_worked_monthly h
JOIN sites s ON h.site_id = s.id
LEFT JOIN aggregated_accidents acc ON ...
```

## Fluxo de Dados

### 1. Autenticação
```
Usuário → Streamlit → Supabase Auth → JWT Token → RLS Policies
```

### 2. CRUD Operations
```
Streamlit → Supabase Client → PostgreSQL → RLS Check → Data
```

### 3. Upload de Evidências
```
Streamlit → Supabase Storage → Bucket 'evidencias' → Database Reference
```

### 4. Cálculo de KPIs
```
Raw Data → Pandas Processing → Statistical Functions → Plotly Charts
```

## Segurança

### Row Level Security (RLS)

```sql
-- Exemplo de política RLS
CREATE POLICY "Accidents are viewable by authenticated users" 
ON accidents FOR SELECT 
USING (auth.role() = 'authenticated');
```

### Autenticação e Autorização

1. **Autenticação**: Supabase Auth (JWT)
2. **Autorização**: Baseada em papéis (role-based)
3. **Escopo**: Por sites de acesso (site_ids)
4. **Auditoria**: Logs automáticos de alterações

### Papéis de Usuário

- **Viewer**: Apenas leitura
- **Editor**: Criação e edição
- **Admin**: Acesso total + configurações

## Controles Estatísticos

### Método M (Monitoramento de Indicadores)

#### 1. Limites de Controle Poisson
```python
mean_rate = total_accidents / total_hours
expected = hours * mean_rate
ucl = expected + 3 * sqrt(expected)
lcl = max(0, expected - 3 * sqrt(expected))
```

#### 2. EWMA (Exponentially Weighted Moving Average)
```python
ewma[t] = λ * value[t] + (1 - λ) * ewma[t-1]
sigma_ewma = sqrt((λ / (2 - λ)) * variance)
ucl_ewma = center_line + 3 * sigma_ewma
```

#### 3. Detecção de Padrões
- Pontos fora de controle
- Tendências (8 pontos consecutivos)
- Runs (sequências acima/abaixo da média)

## Performance

### Otimizações Implementadas

1. **Índices de Banco**:
   - `idx_accidents_site_date`
   - `idx_kpi_monthly_period`
   - `idx_attachments_entity`

2. **View Materializada**:
   - KPIs pré-calculados
   - Refresh automático via trigger

3. **Paginação**:
   - Limite de registros por página
   - Lazy loading de dados

4. **Cache**:
   - Session state do Streamlit
   - Dados em memória durante sessão

### Métricas de Performance

- **Tempo de carregamento**: < 2s para dashboards
- **Upload de arquivos**: < 5s para arquivos < 10MB
- **Cálculos estatísticos**: < 1s para datasets < 10k registros

## Escalabilidade

### Horizontal Scaling
- **Streamlit**: Múltiplas instâncias com load balancer
- **Supabase**: Escalabilidade automática
- **Storage**: CDN global

### Vertical Scaling
- **Processamento**: Otimização de queries
- **Memória**: Paginação e streaming
- **CPU**: Cálculos assíncronos

## Monitoramento

### Logs
- **Application**: Streamlit logs
- **Database**: PostgreSQL logs
- **Auth**: Supabase Auth logs
- **Storage**: Upload/download logs

### Métricas
- **Performance**: Tempo de resposta
- **Usage**: Usuários ativos, queries
- **Errors**: Taxa de erro, exceções
- **Storage**: Uso de espaço, bandwidth

## Backup e Recuperação

### Backup Automático
- **Database**: Supabase backup automático
- **Storage**: Replicação automática
- **Code**: Git repository

### Backup Manual
- **Export de dados**: CSV/Excel via interface
- **Database dump**: Via Supabase CLI
- **Storage backup**: Download de arquivos

## Deploy

### Desenvolvimento
```bash
streamlit run app.py --server.port 8501
```

### Produção
```bash
# Streamlit Cloud
# Configurar variáveis de ambiente
# Deploy automático via Git

# Servidor próprio
gunicorn app:app --bind 0.0.0.0:8501
```

### CI/CD
- **Git**: Versionamento
- **Streamlit Cloud**: Deploy automático
- **Supabase**: Migrations automáticas

## Manutenção

### Atualizações
- **Dependências**: `pip install -r requirements.txt`
- **Database**: Migrations via SQL
- **Code**: Git pull + restart

### Troubleshooting
- **Logs**: Verificar logs do sistema
- **Database**: Verificar queries e índices
- **Auth**: Verificar tokens e permissões
- **Storage**: Verificar bucket e políticas

## Roadmap

### Próximas Funcionalidades
- [ ] Notificações em tempo real
- [ ] API REST para integração
- [ ] Mobile app (React Native)
- [ ] Machine Learning para predição
- [ ] Integração com sistemas externos

### Melhorias Técnicas
- [ ] Cache Redis
- [ ] Background jobs (Celery)
- [ ] Microserviços
- [ ] Kubernetes deployment
- [ ] Observabilidade (Prometheus/Grafana)
