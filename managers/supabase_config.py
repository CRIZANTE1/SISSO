"""
Configuração do Supabase para o Sistema SSO
"""
import os
from supabase import create_client, Client
from typing import Optional
from utils.logger import get_logger

# Inicializa logger
logger = get_logger()

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
                logger.info("Usando credenciais do Streamlit secrets")
            except Exception as secrets_error:
                logger.warning(f"Erro ao acessar secrets: {secrets_error}")
        
        if not url or not key:
            error_msg = "SUPABASE_URL e SUPABASE_ANON_KEY devem estar definidas"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Cliente Supabase anônimo criado com sucesso")
        return create_client(url, key)
        
    except Exception as e:
        logger.error(f"Erro ao configurar Supabase: {e}")
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
                logger.info("Usando credenciais do Streamlit secrets para Service Role")
            except Exception as secrets_error:
                logger.warning(f"Erro ao acessar secrets para Service Role: {secrets_error}")
        
        if not url or not service_key:
            error_msg = "SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY devem estar definidas"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Cliente Supabase Service Role criado com sucesso")
        return create_client(url, service_key)
        
    except Exception as e:
        logger.error(f"Erro ao configurar Supabase Service Role: {e}")
        return None

def test_connection() -> bool:
    """Testa conexão com Supabase"""
    try:
        logger.info("Testando conexão com Supabase")
        client = get_supabase_client()
        if not client:
            logger.error("Cliente Supabase não pôde ser criado")
            return False
        
        # Testa uma query simples
        response = client.table("profiles").select("id").limit(1).execute()
        logger.info("Teste de conexão com Supabase bem-sucedido")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao testar conexão: {e}")
        return False
