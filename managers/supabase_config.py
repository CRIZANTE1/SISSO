"""
Configuração do Supabase para o Sistema SSO
"""
import os
from supabase import create_client, Client
from typing import Optional

def get_supabase_client() -> Optional[Client]:
    """Cria e retorna cliente Supabase configurado"""
    try:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_ANON_KEY")
        
        if not url or not key:
            # Tenta buscar do secrets do Streamlit
            try:
                import streamlit as st
                url = st.secrets.get("supabase", {}).get("url")
                key = st.secrets.get("supabase", {}).get("anon_key")
            except:
                pass
        
        if not url or not key:
            raise ValueError("SUPABASE_URL e SUPABASE_ANON_KEY devem estar definidas")
        
        return create_client(url, key)
        
    except Exception as e:
        print(f"Erro ao configurar Supabase: {e}")
        return None

def get_service_role_client() -> Optional[Client]:
    """Cria cliente Supabase com service role key (apenas para operações admin)"""
    try:
        url = os.environ.get("SUPABASE_URL")
        service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        
        if not url or not service_key:
            # Tenta buscar do secrets do Streamlit
            try:
                import streamlit as st
                url = st.secrets.get("supabase", {}).get("url")
                service_key = st.secrets.get("supabase", {}).get("service_role_key")
            except:
                pass
        
        if not url or not service_key:
            raise ValueError("SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY devem estar definidas")
        
        return create_client(url, service_key)
        
    except Exception as e:
        print(f"Erro ao configurar Supabase Service Role: {e}")
        return None

def test_connection() -> bool:
    """Testa conexão com Supabase"""
    try:
        client = get_supabase_client()
        if not client:
            return False
        
        # Testa uma query simples
        response = client.table("profiles").select("id").limit(1).execute()
        return True
        
    except Exception as e:
        print(f"Erro ao testar conexão: {e}")
        return False
