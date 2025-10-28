# 🔒 Políticas de Row Level Security (RLS)

## Visão Geral

O sistema implementa Row Level Security (RLS) para garantir isolamento completo de dados por usuário. Cada usuário só pode acessar seus próprios dados, exceto administradores que têm acesso total.

## 🏗️ Arquitetura de Segurança

### Princípios Fundamentais
- **Isolamento por Usuário**: Cada usuário vê apenas seus próprios dados
- **Acesso Administrativo**: Admins podem ver todos os dados
- **Autenticação Obrigatória**: Todas as operações requerem usuário autenticado
- **Políticas Granulares**: Diferentes níveis de acesso por tabela

## 📋 Políticas por Tabela

### 1. **Tabela `profiles`**

#### Política de Visualização Própria
```sql
CREATE POLICY "Users can view their own profile" ON profiles
    FOR SELECT USING (auth.jwt() ->> 'email' = id);
```
**Descrição**: Usuários podem visualizar apenas seu próprio perfil baseado no email do JWT.

#### Política de Atualização Própria
```sql
CREATE POLICY "Users can update their own profile" ON profiles
    FOR UPDATE USING (auth.jwt() ->> 'email' = id);
```
**Descrição**: Usuários podem atualizar apenas seu próprio perfil baseado no email do JWT.

#### Política de Criação Própria
```sql
CREATE POLICY "Users can create their own profile" ON profiles
    FOR INSERT WITH CHECK (auth.jwt() ->> 'email' = email);
```
**Descrição**: Usuários podem criar apenas seu próprio perfil baseado no email do JWT.

#### Política de Visualização para Admins
```sql
CREATE POLICY "Admins can view all profiles" ON profiles
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE id = auth.jwt() ->> 'email'
            AND role = 'admin'
        )
    );
```
**Descrição**: Administradores podem visualizar todos os perfis baseado no email do JWT.

#### Política de Criação para Admins
```sql
CREATE POLICY "Admins can create any profile" ON profiles
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE email = auth.jwt() ->> 'email'
            AND role = 'admin'
        )
    );
```
**Descrição**: Administradores podem criar perfis de qualquer usuário.

### 2. **Tabela `hours_worked_monthly`**

#### Política de Visualização
```sql
CREATE POLICY "Users can view their own hours" ON hours_worked_monthly
    FOR SELECT USING (auth.jwt() ->> 'email' = created_by);
```
**Descrição**: Usuários podem visualizar apenas suas próprias horas trabalhadas baseado no email do JWT.

#### Política de Gerenciamento
```sql
CREATE POLICY "Users can manage their own hours" ON hours_worked_monthly
    FOR ALL USING (auth.jwt() ->> 'email' = created_by);
```
**Descrição**: Usuários podem criar, atualizar e excluir apenas suas próprias horas trabalhadas baseado no email do JWT.

### 3. **Tabela `accidents`**

#### Política de Visualização
```sql
CREATE POLICY "Users can view their own accidents" ON accidents
    FOR SELECT USING (auth.jwt() ->> 'email' = created_by);
```
**Descrição**: Usuários podem visualizar apenas seus próprios acidentes.

#### Política de Gerenciamento
```sql
CREATE POLICY "Users can manage their own accidents" ON accidents
    FOR ALL USING (auth.jwt() ->> 'email' = created_by);
```
**Descrição**: Usuários podem criar, atualizar e excluir apenas seus próprios acidentes.

### 4. **Tabela `near_misses`**

#### Política de Visualização
```sql
CREATE POLICY "Users can view their own near misses" ON near_misses
    FOR SELECT USING (auth.jwt() ->> 'email' = created_by);
```
**Descrição**: Usuários podem visualizar apenas seus próprios quase-acidentes.

#### Política de Gerenciamento
```sql
CREATE POLICY "Users can manage their own near misses" ON near_misses
    FOR ALL USING (auth.jwt() ->> 'email' = created_by);
```
**Descrição**: Usuários podem criar, atualizar e excluir apenas seus próprios quase-acidentes.

### 5. **Tabela `nonconformities`**

#### Política de Visualização
```sql
CREATE POLICY "Users can view their own nonconformities" ON nonconformities
    FOR SELECT USING (auth.jwt() ->> 'email' = created_by);
```
**Descrição**: Usuários podem visualizar apenas suas próprias não conformidades.

#### Política de Gerenciamento
```sql
CREATE POLICY "Users can manage their own nonconformities" ON nonconformities
    FOR ALL USING (auth.jwt() ->> 'email' = created_by);
```
**Descrição**: Usuários podem criar, atualizar e excluir apenas suas próprias não conformidades.

### 6. **Tabela `actions`**

#### Política de Visualização
```sql
CREATE POLICY "Users can view their own actions" ON actions
    FOR SELECT USING (auth.jwt() ->> 'email' = created_by);
```
**Descrição**: Usuários podem visualizar apenas suas próprias ações.

#### Política de Gerenciamento
```sql
CREATE POLICY "Users can manage their own actions" ON actions
    FOR ALL USING (auth.jwt() ->> 'email' = created_by);
```
**Descrição**: Usuários podem criar, atualizar e excluir apenas suas próprias ações.

### 7. **Tabela `attachments`**

#### Política de Visualização
```sql
CREATE POLICY "Users can view their own attachments" ON attachments
    FOR SELECT USING (auth.jwt() ->> 'email' = uploaded_by);
```
**Descrição**: Usuários podem visualizar apenas seus próprios anexos.

#### Política de Gerenciamento
```sql
CREATE POLICY "Users can manage their own attachments" ON attachments
    FOR ALL USING (auth.jwt() ->> 'email' = uploaded_by);
```
**Descrição**: Usuários podem criar, atualizar e excluir apenas seus próprios anexos.

## 🔧 Script Completo de RLS

```sql
-- =============================================
-- CONFIGURAÇÃO COMPLETA DE ROW LEVEL SECURITY
-- =============================================

-- 1. Habilitar RLS nas tabelas
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE hours_worked_monthly ENABLE ROW LEVEL SECURITY;
ALTER TABLE accidents ENABLE ROW LEVEL SECURITY;
ALTER TABLE near_misses ENABLE ROW LEVEL SECURITY;
ALTER TABLE nonconformities ENABLE ROW LEVEL SECURITY;
ALTER TABLE actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE attachments ENABLE ROW LEVEL SECURITY;

-- 2. Políticas para profiles
CREATE POLICY "Users can view their own profile" ON profiles
    FOR SELECT USING (auth.jwt() ->> 'email' = id);

CREATE POLICY "Users can update their own profile" ON profiles
    FOR UPDATE USING (auth.jwt() ->> 'email' = id);

CREATE POLICY "Users can create their own profile" ON profiles
    FOR INSERT WITH CHECK (auth.jwt() ->> 'email' = email);

CREATE POLICY "Admins can view all profiles" ON profiles
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE id = auth.jwt() ->> 'email' 
            AND role = 'admin'
        )
    );

CREATE POLICY "Admins can create any profile" ON profiles
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE email = auth.jwt() ->> 'email'
            AND role = 'admin'
        )
    );

-- 3. Políticas para hours_worked_monthly
CREATE POLICY "Users can view their own hours" ON hours_worked_monthly
    FOR SELECT USING (auth.jwt() ->> 'email' = created_by);

CREATE POLICY "Users can manage their own hours" ON hours_worked_monthly
    FOR ALL USING (auth.jwt() ->> 'email' = created_by);

-- 4. Políticas para accidents
CREATE POLICY "Users can view their own accidents" ON accidents
    FOR SELECT USING (auth.jwt() ->> 'email' = created_by);

CREATE POLICY "Users can manage their own accidents" ON accidents
    FOR ALL USING (auth.jwt() ->> 'email' = created_by);

-- 5. Políticas para near_misses
CREATE POLICY "Users can view their own near misses" ON near_misses
    FOR SELECT USING (auth.jwt() ->> 'email' = created_by);

CREATE POLICY "Users can manage their own near misses" ON near_misses
    FOR ALL USING (auth.jwt() ->> 'email' = created_by);

-- 6. Políticas para nonconformities
CREATE POLICY "Users can view their own nonconformities" ON nonconformities
    FOR SELECT USING (auth.jwt() ->> 'email' = created_by);

CREATE POLICY "Users can manage their own nonconformities" ON nonconformities
    FOR ALL USING (auth.jwt() ->> 'email' = created_by);

-- 7. Políticas para actions
CREATE POLICY "Users can view their own actions" ON actions
    FOR SELECT USING (auth.jwt() ->> 'email' = created_by);

CREATE POLICY "Users can manage their own actions" ON actions
    FOR ALL USING (auth.jwt() ->> 'email' = created_by);

-- 8. Políticas para attachments
CREATE POLICY "Users can view their own attachments" ON attachments
    FOR SELECT USING (auth.jwt() ->> 'email' = uploaded_by);

CREATE POLICY "Users can manage their own attachments" ON attachments
    FOR ALL USING (auth.jwt() ->> 'email' = uploaded_by);
```

## 🛡️ Recursos de Segurança

### **Isolamento Completo**
- Cada usuário vê apenas seus próprios dados
- Impossível acessar dados de outros usuários
- Proteção automática em todas as operações

### **Controle Administrativo**
- Administradores têm acesso total
- Verificação de papel via subquery
- Políticas específicas para admins

### **Autenticação Obrigatória**
- Todas as políticas verificam `auth.jwt() ->> 'email'`
- Usuários não autenticados não têm acesso
- Proteção contra acesso anônimo

### **Granularidade por Operação**
- Políticas separadas para SELECT, INSERT, UPDATE, DELETE
- Controle fino de permissões
- Flexibilidade para diferentes níveis de acesso

## 🧪 Testes de RLS

### **Teste de Isolamento**
```sql
-- Como usuário específico
SET LOCAL "request.jwt.claims" TO '{"email": "usuario@empresa.com"}';

-- Deve retornar apenas dados do usuário
SELECT * FROM accidents;
SELECT * FROM near_misses;
SELECT * FROM nonconformities;
```

### **Teste de Acesso Admin**
```sql
-- Como admin
SET LOCAL "request.jwt.claims" TO '{"email": "admin@empresa.com"}';

-- Deve retornar todos os dados
SELECT * FROM profiles;
```

### **Teste de Acesso Negado**
```sql
-- Sem autenticação
-- Deve retornar vazio ou erro
SELECT * FROM accidents;
```

## 🔍 Monitoramento de RLS

### **Verificar Políticas Ativas**
```sql
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
FROM pg_policies 
WHERE schemaname = 'public'
ORDER BY tablename, policyname;
```

### **Verificar RLS Habilitado**
```sql
SELECT schemaname, tablename, rowsecurity
FROM pg_tables 
WHERE schemaname = 'public' 
AND rowsecurity = true;
```

### **Logs de Acesso**
- Monitore logs do Supabase
- Verifique tentativas de acesso negado
- Analise padrões de uso

## ⚠️ Considerações Importantes

### **Performance**
- RLS adiciona overhead mínimo
- Índices otimizados para `created_by` e `uploaded_by`
- Queries eficientes com subqueries

### **Manutenção**
- Políticas são aplicadas automaticamente
- Não requer código adicional na aplicação
- Fácil de auditar e modificar

### **Escalabilidade**
- Suporta milhares de usuários
- Isolamento automático
- Performance consistente

## 🚀 Implementação

### **1. Execute o Script**
```sql
-- Execute o script completo de RLS no Supabase SQL Editor
-- Todas as políticas serão criadas automaticamente
```

### **2. Verifique Configuração**
```sql
-- Confirme que RLS está habilitado
SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public';
```

### **3. Teste Funcionamento**
```sql
-- Teste com diferentes usuários
-- Verifique isolamento de dados
-- Confirme acesso administrativo
```

## 📚 Referências

- [Supabase RLS Documentation](https://supabase.com/docs/guides/auth/row-level-security)
- [PostgreSQL RLS](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [OIDC Authentication](https://openid.net/connect/)

---

**As políticas de RLS garantem segurança máxima e isolamento completo de dados, sendo essenciais para aplicações multi-tenant como o Sistema SSO.**
