# 💳 Sistema de Planos e Trial

## Visão Geral

O sistema implementa um controle de planos e trial de 14 dias para novos usuários. Administradores e usuários com planos ilimitados não têm restrições.

## 🎯 Planos Disponíveis

1. **trial**: Período de avaliação de 14 dias (padrão para novos usuários)
2. **basic**: Plano básico
3. **premium**: Plano premium
4. **dev_ilimitado**: Plano de desenvolvedor com acesso ilimitado
5. **enterprise**: Plano empresarial com acesso ilimitado

## 🔓 Acesso Ilimitado

Usuários com **acesso ilimitado** não têm restrições de trial:
- ✅ Administradores (`role = 'admin'`)
- ✅ Plano `dev_ilimitado`
- ✅ Plano `enterprise`

## 🗄️ Estrutura do Banco

### Campo `plan` na tabela `profiles`

```sql
plan TEXT DEFAULT 'trial' 
CHECK (plan IN ('trial', 'basic', 'premium', 'dev_ilimitado', 'enterprise'))
```

## 🔧 Funções Disponíveis

### `check_trial_status(email)`

Verifica o status de trial do usuário. Retorna:
- `unlimited_access`: True se for admin ou plano ilimitado
- `has_trial`: True se ainda está em trial
- `is_trial_expired`: True se o trial expirou
- `plan`: Plano atual do usuário
- `role`: Papel do usuário

### `update_user_plan(email, plan)`

Atualiza o plano do usuário. Planos válidos:
- `'trial'`
- `'basic'`
- `'premium'`
- `'dev_ilimitado'`
- `'enterprise'`

## 📋 Como Atualizar o Plano de um Usuário

### Via SQL (Supabase)

```sql
-- Atualizar para plano dev_ilimitado
UPDATE profiles 
SET plan = 'dev_ilimitado', updated_at = NOW()
WHERE email = 'seu-email@exemplo.com';

-- Atualizar para admin (role) + dev_ilimitado (plan)
UPDATE profiles 
SET role = 'admin', plan = 'dev_ilimitado', updated_at = NOW()
WHERE email = 'seu-email@exemplo.com';
```

### Via Python (Streamlit)

```python
from services.trial_manager import update_user_plan

# Atualizar plano
update_user_plan('seu-email@exemplo.com', 'dev_ilimitado')
```

## 🚫 Bloqueios e Restrições

### Usuários com Trial Expirado

- ❌ Não podem acessar o sistema
- ❌ Veem mensagem "TRIAL EXPIRADO"
- ✅ Dados são preservados

### Usuários com Acesso Ilimitado

- ✅ Acesso total ao sistema
- ✅ Sem restrições de tempo
- ✅ Não veem mensagens de trial

## 🔍 Verificação de Status

O sistema verifica automaticamente:

1. **Ao fazer login**: Verifica trial e bloqueia se expirado
2. **Em cada página**: Mostra notificações se necessário
3. **Para admins/ilimitados**: Pula todas as verificações

## 📝 Exemplo de Uso

### Configurar Admin com Plano Ilimitado

```sql
-- No Supabase SQL Editor
UPDATE profiles 
SET 
    role = 'admin',
    plan = 'dev_ilimitado',
    status = 'ativo',
    updated_at = NOW()
WHERE email = 'seu-email@exemplo.com';
```

### Verificar Status Atual

```python
from services.trial_manager import check_trial_status

trial_info = check_trial_status('seu-email@exemplo.com')
print(f"Plano: {trial_info.get('plan')}")
print(f"Acesso Ilimitado: {trial_info.get('unlimited_access')}")
print(f"Trial Expirado: {trial_info.get('is_trial_expired')}")
```

## ⚠️ Importante

- **Admins** têm acesso ilimitado automaticamente (não precisa plano)
- **Plano `dev_ilimitado`** também dá acesso ilimitado
- **Plano `enterprise`** também dá acesso ilimitado
- Usuários com `status = 'ativo'` e trial válido têm acesso normal
- Trial expira 14 dias após `created_at`

---

**Sistema de planos implementado com suporte a acesso ilimitado para admins e desenvolvedores** ✅

