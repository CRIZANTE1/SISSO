# 🛡️ Sistema de Monitoramento SSO

Sistema completo de monitoramento de Segurança e Saúde Ocupacional (SSO) com análise de acidentes, quase-acidentes, não conformidades e cálculo de KPIs com controles estatísticos.

## 🚀 Funcionalidades

### 📊 Análise de Dados & Investigação
- **Acidentes**: Registro e análise de acidentes fatais, com e sem lesão
- **Quase-Acidentes**: Monitoramento de eventos de quase-acidente por severidade potencial
- **Não Conformidades**: Controle de N/C com referência normativa (NR-12, NR-20, ISO 45001, etc.)
- **Investigação Formal (FTA)**: Análise de Causa Raiz com Árvore de Falhas (Fault Tree Analysis) e emissão de laudo pericial (PDF e Word) para Acidentes e Não Conformidades
- **Ações 5W2H**: Plano de ações para correção e mitigação de desvios
- **Evidências**: Upload e gerenciamento de fotos, PDFs e documentos periciais

### 📈 KPIs e Controles Estatísticos
- **Taxa de Frequência**: (nº acidentes / horas trabalhadas) × 1.000.000
- **Taxa de Gravidade**: (dias perdidos / horas trabalhadas) × 1.000.000
- **Controles Poisson**: Limites de controle para eventos raros
- **Método M**: Monitoramento com EWMA (Exponentially Weighted Moving Average)
- **Alertas Automáticos**: Detecção de padrões e tendências

### 🔐 Governança e Segurança
- **Autenticação OIDC**: Login via Google OAuth (sem armazenamento de senhas)
- **Autorização RBAC**: Controle de acesso baseado em papéis (Admin, Editor, Viewer)
- **Isolamento Multi-Tenant**: Segregação de dados por usuário individual
- **RLS**: Row Level Security no PostgreSQL/Supabase
- **Sessões Seguras**: Dados do usuário na st.session_state
- **Auditoria**: Logs completos de alterações

## 🛠️ Stack Tecnológica

- **Frontend**: Streamlit + Plotly + Altair
- **Backend**: Supabase (PostgreSQL + Auth + Storage)
- **Análise**: Pandas + NumPy + SciPy
- **Visualização**: Plotly + Streamlit Charts
- **Deploy**: Streamlit Cloud ou servidor próprio

## 📋 Pré-requisitos

- Python 3.8+
- Conta no Supabase
- Google Cloud Console (para OAuth opcional)

## ⚙️ Instalação

### 1. Clone o repositório
```bash
git clone <repository-url>
cd sso-monitor
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Configure o Supabase

1. Crie um projeto no [Supabase](https://supabase.com)
2. Execute o script `database_setup.sql` no SQL Editor do Supabase
3. (Opcional) Execute `rls_policies.sql` para aplicar apenas as políticas RLS
4. (Opcional) Execute `verificar_rls.sql` para verificar se as políticas estão funcionando

**🔄 Scripts de Reset (se necessário):**
- `drop_tables.sql` - Remove apenas as tabelas
- `reset_database.sql` - Remove tudo e limpa completamente
- `recreate_database.sql` - Remove e recria tudo em um script

### 4. Configure o Storage:
   - Crie um bucket chamado `evidencias`
   - Configure como privado
   - Limite de 50MB por arquivo
   - Tipos permitidos: image/*, application/pdf, application/msword

### 5. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
SUPABASE_URL=sua_url_do_supabase
SUPABASE_ANON_KEY=sua_chave_anonima_do_supabase
```

### 6. Configure OIDC Google (Obrigatório)

1. **No Streamlit Cloud**:
   - Vá em Settings > Authentication
   - Ative "Enable authentication"
   - Selecione "Google" como provider
   - Configure Client ID e Client Secret do Google

2. **No Google Cloud Console**:
   - Crie credenciais OAuth 2.0
   - Adicione a URL de callback: `https://seu-app.streamlit.app/_stcore/oauth/callback`
   - Configure domínios autorizados

3. **Configuração Local** (desenvolvimento):
   - Configure as variáveis de ambiente ou use `.streamlit/secrets.toml`
   - O sistema criará perfis automaticamente para novos usuários

### 7. Execute o sistema
```bash
streamlit run app.py
```

## 📊 Estrutura do Banco de Dados

### Tabelas Principais
- `profiles`: Perfis de usuário (vinculados ao Auth)
- `hours_worked_monthly`: Horas trabalhadas por mês por usuário
- `accidents`: Acidentes de trabalho (fatal, lesão, sem lesão)
- `near_misses`: Quase-acidentes com severidade potencial
- `nonconformities`: Não conformidades com referência normativa
- `actions`: Plano de ações 5W2H para correção
- `attachments`: Evidências e anexos dos registros

### Views e Funções
- `kpi_monthly`: View com KPIs calculados automaticamente por usuário
- Extensões: `uuid-ossp` e `pgcrypto` para UUIDs e criptografia
- RLS: Row Level Security configurado para isolamento por usuário

## 🔧 Uso do Sistema

### 1. Primeiro Acesso
1. Acesse o sistema
2. Faça login com Google ou crie uma conta
3. Um administrador deve configurar seu perfil e sites de acesso

### 2. Configuração Inicial (Admin)
1. Acesse "Admin - Dados Básicos"
2. Configure usuários e permissões
3. Importe dados históricos (CSV)
4. Cada usuário gerencia seus próprios dados

### 3. Registro de Eventos
- **Acidentes**: Data, tipo (fatal/lesão/sem lesão), classificação, parte do corpo, dias perdidos
- **Quase-Acidentes**: Data, severidade potencial, descrição, status
- **N/C**: Data de abertura, norma de referência, gravidade, status
- **Ações 5W2H**: O que, quem, quando, onde, por que, como, quanto custa

### 4. Análise e Relatórios
- **Visão Geral**: Dashboard executivo com métricas principais
- **KPIs**: Taxas de frequência e gravidade com controles estatísticos
- **Controles**: Gráficos de controle Poisson e EWMA
- **Exportação**: Relatórios em CSV

## 📈 Métricas e Controles

### Taxa de Frequência (TF)
```
TF = (nº de acidentes / horas trabalhadas) × 1.000.000
```

### Taxa de Gravidade (TG)
```
TG = (dias perdidos / horas trabalhadas) × 1.000.000
```

### Controles Estatísticos
- **Limites Poisson**: UCL = μ + 3√μ, LCL = max(0, μ - 3√μ)
- **EWMA**: Suavização exponencial com λ = 0.2-0.3
- **Alertas**: Pontos fora de controle, tendências, padrões

## 🔐 Segurança e Permissões

### Papéis de Usuário
- **Viewer**: Apenas visualização de dados
- **Editor**: Criação e edição de registros
- **Admin**: Acesso total + configurações

### Row Level Security (RLS)
- Políticas baseadas em papel do usuário
- Escopo por sites de acesso
- Auditoria completa de alterações

## 📱 Interface do Usuário

### Páginas Principais
1. **Visão Geral**: Dashboard executivo
2. **Acidentes**: Gestão de acidentes
3. **Quase-Acidentes**: Monitoramento preventivo
4. **Não Conformidades**: Controle normativo
5. **KPIs e Controles**: Análise estatística
6. **Admin**: Configurações do sistema

### Recursos de UX
- Filtros dinâmicos na sidebar
- Gráficos interativos (Plotly)
- Upload de evidências
- Exportação de dados
- Alertas em tempo real

## 🚀 Deploy

### Streamlit Cloud
1. Conecte o repositório ao Streamlit Cloud
2. Configure as variáveis de ambiente
3. Deploy automático

### Servidor Próprio
```bash
# Instale dependências
pip install -r requirements.txt

# Configure nginx (opcional)
# Configure SSL (recomendado)

# Execute
streamlit run app.py --server.port 8501
```

## 🔧 Manutenção

### Atualização de KPIs
```sql
-- Execute no Supabase SQL Editor
SELECT refresh_kpi_monthly();
```

### Backup
- Backup automático do Supabase
- Exportação de dados via interface
- Backup de evidências no Storage

### Monitoramento
- Logs do Supabase
- Métricas de performance
- Alertas de sistema

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os logs do sistema
2. Consulte a documentação do Supabase
3. Abra uma issue no repositório

## 📄 Licença

Este projeto está sob licença MIT. Veja o arquivo LICENSE para detalhes.

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor:
1. Faça um fork do projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Abra um Pull Request

---

**Desenvolvido com ❤️ para a segurança e saúde ocupacional**
