from managers.supabase_config import get_supabase_client

def get_client():
    """Cria e retorna cliente Supabase configurado"""
    client = get_supabase_client()
    if not client:
        raise ValueError("Erro ao configurar cliente Supabase. Verifique as variáveis de ambiente.")
    return client
