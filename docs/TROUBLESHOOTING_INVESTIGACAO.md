# 🔧 Troubleshooting - Investigação de Acidentes

## Problema: Acidente não aparece na lista de investigação

### Possíveis Causas

1. **Filtro de Usuário**: O acidente foi criado por outro usuário e você não é admin
2. **Campo `title` vazio**: Acidente criado sem título
3. **Problema de RLS (Row Level Security)**: Políticas do Supabase bloqueando acesso
4. **Cache do Streamlit**: Dados não atualizados

### Soluções Implementadas

#### 1. Normalização de Título
- Se `title` for `None` ou vazio, usa `description`
- Se ambos forem vazios, usa "Acidente sem título"

#### 2. Botão de Refresh
- Botão "🔄 Atualizar Lista de Acidentes" na sidebar
- Força atualização da lista

#### 3. Tratamento de Erros
- Melhor tratamento de exceções
- Logs de debug quando necessário

### Como Verificar

1. **Verifique se você é admin:**
   ```python
   from auth.auth_utils import is_admin
   is_admin()  # Deve retornar True se for admin
   ```

2. **Verifique o `created_by` do acidente:**
   - O acidente deve ter `created_by` igual ao seu `user_id`
   - Ou você deve ser admin para ver todos

3. **Verifique no banco de dados:**
   ```sql
   SELECT id, title, description, created_by, status
   FROM accidents
   ORDER BY created_at DESC
   LIMIT 5;
   ```

4. **Clique no botão "🔄 Atualizar Lista de Acidentes"**

### Debug Manual

Se o problema persistir, adicione este código temporário na página:

```python
# Debug temporário
if st.checkbox("🔍 Modo Debug"):
    from auth.auth_utils import get_user_id, is_admin
    user_id = get_user_id()
    st.write(f"User ID: {user_id}")
    st.write(f"É Admin: {is_admin()}")
    
    from managers.supabase_config import get_supabase_client
    supabase = get_supabase_client()
    
    # Busca todos os acidentes (sem filtro)
    all_accidents = supabase.table("accidents").select("*").limit(10).execute()
    st.write(f"Total de acidentes no banco: {len(all_accidents.data) if all_accidents.data else 0}")
    st.json(all_accidents.data[:3] if all_accidents.data else [])
    
    # Busca acidentes do usuário atual
    if user_id:
        user_accidents = supabase.table("accidents").select("*").eq("created_by", user_id).execute()
        st.write(f"Acidentes do usuário atual: {len(user_accidents.data) if user_accidents.data else 0}")
        st.json(user_accidents.data if user_accidents.data else [])
```

### Correções Aplicadas

1. ✅ Normalização de `title` quando `None`
2. ✅ Tratamento de datas (`occurrence_date` e `occurred_at`)
3. ✅ Botão de refresh na sidebar
4. ✅ Melhor formatação de labels no selectbox
5. ✅ Tratamento de erros melhorado

### Próximos Passos

Se o problema persistir:

1. Verifique as políticas RLS no Supabase
2. Verifique se o `user_id` está correto
3. Verifique se você tem permissão de admin
4. Tente criar um novo acidente e verificar se aparece

---

**Última atualização:** Correções aplicadas para normalização de títulos e tratamento de erros.

