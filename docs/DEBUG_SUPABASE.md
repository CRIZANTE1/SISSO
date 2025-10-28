# 🔧 Debug de Conexão Supabase

Este documento explica como usar o sistema de debug para diagnosticar problemas de conexão com o Supabase.

## 📋 Visão Geral

O sistema de debug foi implementado para ajudar a identificar e resolver problemas de conectividade com o Supabase. Ele inclui:

- Verificação de configuração (variáveis de ambiente vs secrets)
- Testes de conectividade (anônima e service role)
- Teste de acesso a tabelas específicas
- Logs detalhados de debug
- Diagnóstico completo do sistema

## 🚀 Como Usar

### 1. Acessar a Página de Debug

1. Execute a aplicação: `streamlit run app.py`
2. Na navegação superior, clique em **🔧 Debug** > **Debug Supabase**
3. A página de debug será carregada com todas as ferramentas de diagnóstico

### 2. Seções Disponíveis

#### 📋 Verificação de Configuração
- Mostra status das variáveis de ambiente
- Verifica configuração do Streamlit Secrets
- Exibe valores mascarados para segurança

#### 🔍 Status Detalhado
- Atualiza status em tempo real
- Compara configuração entre env vars e secrets
- Identifica qual fonte de configuração está sendo usada

#### 🔌 Teste de Conexão
- **Conexão Anônima**: Testa com SUPABASE_ANON_KEY
- **Service Role**: Testa com SUPABASE_SERVICE_ROLE_KEY
- Mostra resultados detalhados e erros específicos

#### 📊 Teste de Tabelas
- Testa acesso a tabelas específicas
- Verifica permissões de leitura e escrita
- Lista colunas disponíveis
- Identifica problemas de RLS (Row Level Security)

#### 👤 Teste de Autenticação
- Verifica autenticação OIDC
- Testa busca de usuário na base de dados
- Valida criação de perfis automática

#### ℹ️ Informações do Sistema
- Versões de dependências
- Status da sessão atual
- Informações do ambiente

#### 📝 Logs de Debug
- Logs em tempo real
- Histórico de operações
- Exportação de logs para análise

#### 🛠️ Comandos de Diagnóstico
- Instruções para configuração manual
- Comandos de terminal para verificação
- Guias de troubleshooting

#### 📋 Resumo do Debug
- Diagnóstico completo automatizado
- Métricas de status
- Recomendações específicas

## 🔧 Configuração

### Variáveis de Ambiente

```bash
export SUPABASE_URL="sua_url_do_supabase"
export SUPABASE_ANON_KEY="sua_chave_anonima"
export SUPABASE_SERVICE_ROLE_KEY="sua_chave_service_role"
```

### Streamlit Secrets (.streamlit/secrets.toml)

```toml
[supabase]
url = "sua_url_do_supabase"
anon_key = "sua_chave_anonima"
service_role_key = "sua_chave_service_role"
```

## 🐛 Problemas Comuns

### 1. Erro: "SUPABASE_URL e SUPABASE_ANON_KEY devem estar definidas"

**Causa**: Credenciais não configuradas
**Solução**: 
- Configure as variáveis de ambiente
- Ou configure o arquivo `.streamlit/secrets.toml`

### 2. Erro: "Falha ao criar cliente Supabase"

**Causa**: URL ou chave inválida
**Solução**:
- Verifique se a URL está correta
- Verifique se a chave anônima está correta
- Teste no painel do Supabase

### 3. Erro: "Tabela 'profiles' não existe"

**Causa**: Tabela não criada no Supabase
**Solução**:
- Acesse o painel do Supabase
- Crie a tabela `profiles`
- Configure as políticas RLS

### 4. Erro: "Acesso negado" em queries

**Causa**: Políticas RLS muito restritivas
**Solução**:
- Verifique as políticas no Supabase
- Ajuste as permissões conforme necessário
- Use Service Role para operações administrativas

## 📊 Interpretando os Resultados

### ✅ Status OK
- Configuração correta
- Conexão funcionando
- Tabelas acessíveis

### ⚠️ Avisos
- Configuração parcial
- Acesso limitado
- Dependências desatualizadas

### ❌ Erros
- Configuração incorreta
- Conexão falhando
- Permissões insuficientes

## 🔄 Manutenção

### Limpeza de Logs
- Use o botão "🗑️ Limpar Logs" para limpar o histórico
- Logs são mantidos durante a sessão

### Atualização de Status
- Use "🔄 Atualizar" para verificar mudanças em tempo real
- Status é atualizado automaticamente em algumas operações

### Exportação de Logs
- Use "📋 Copiar Logs" para exportar logs
- Útil para compartilhar com suporte técnico

## 🆘 Suporte

Se os problemas persistirem após usar o sistema de debug:

1. Execute o "Diagnóstico Completo"
2. Copie os logs de debug
3. Verifique a documentação do Supabase
4. Entre em contato com o suporte técnico

## 📚 Recursos Adicionais

- [Documentação Supabase](https://supabase.com/docs)
- [Streamlit Secrets](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
- [Row Level Security](https://supabase.com/docs/guides/auth/row-level-security)
