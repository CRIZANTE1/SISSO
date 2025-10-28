"""
Utilitários de Debug para Conexão Supabase
"""
import streamlit as st
import os
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List
from managers.supabase_config import get_supabase_client, get_service_role_client

class SupabaseDebugger:
    """Classe para debug e diagnóstico da conexão Supabase"""
    
    def __init__(self):
        self.logs: List[str] = []
        self.add_log("Debugger inicializado")
    
    def add_log(self, message: str):
        """Adiciona uma entrada de log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        print(log_entry)  # Também imprime no console
    
    def get_configuration_status(self) -> Dict[str, Any]:
        """Retorna o status da configuração"""
        status = {
            "env_vars": {
                "SUPABASE_URL": bool(os.environ.get("SUPABASE_URL")),
                "SUPABASE_ANON_KEY": bool(os.environ.get("SUPABASE_ANON_KEY")),
                "SUPABASE_SERVICE_ROLE_KEY": bool(os.environ.get("SUPABASE_SERVICE_ROLE_KEY"))
            },
            "secrets": {
                "url": False,
                "anon_key": False,
                "service_role_key": False
            },
            "values": {
                "env_url": os.environ.get("SUPABASE_URL", ""),
                "env_anon_key": os.environ.get("SUPABASE_ANON_KEY", ""),
                "env_service_key": os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
            }
        }
        
        try:
            secrets = st.secrets.get("supabase", {})
            status["secrets"]["url"] = bool(secrets.get("url"))
            status["secrets"]["anon_key"] = bool(secrets.get("anon_key"))
            status["secrets"]["service_role_key"] = bool(secrets.get("service_role_key"))
            status["values"]["secrets_url"] = secrets.get("url", "")
            status["values"]["secrets_anon_key"] = secrets.get("anon_key", "")
            status["values"]["secrets_service_key"] = secrets.get("service_role_key", "")
        except Exception as e:
            self.add_log(f"Erro ao acessar secrets: {str(e)}")
        
        return status
    
    def test_connection(self, use_service_role: bool = False) -> Dict[str, Any]:
        """Testa a conexão com Supabase"""
        self.add_log(f"Testando conexão {'Service Role' if use_service_role else 'Anônima'}")
        
        result = {
            "success": False,
            "error": None,
            "client_created": False,
            "query_success": False,
            "query_data": None,
            "query_error": None
        }
        
        try:
            # Cria cliente
            if use_service_role:
                client = get_service_role_client()
            else:
                client = get_supabase_client()
            
            if not client:
                result["error"] = "Falha ao criar cliente Supabase"
                self.add_log(f"❌ {result['error']}")
                return result
            
            result["client_created"] = True
            self.add_log("✅ Cliente Supabase criado com sucesso")
            
            # Testa query simples
            try:
                response = client.table("profiles").select("id").limit(1).execute()
                result["query_success"] = True
                result["query_data"] = response.data
                self.add_log(f"✅ Query executada com sucesso - {len(response.data)} registros")
                
            except Exception as query_error:
                result["query_error"] = str(query_error)
                self.add_log(f"❌ Erro na query: {str(query_error)}")
                
        except Exception as e:
            result["error"] = str(e)
            self.add_log(f"❌ Erro geral: {str(e)}")
        
        result["success"] = result["client_created"] and result["query_success"]
        return result
    
    def test_table_access(self, table_name: str) -> Dict[str, Any]:
        """Testa acesso a uma tabela específica"""
        self.add_log(f"Testando acesso à tabela: {table_name}")
        
        result = {
            "table_exists": False,
            "can_read": False,
            "can_write": False,
            "columns": [],
            "error": None
        }
        
        try:
            client = get_supabase_client()
            if not client:
                result["error"] = "Cliente Supabase não disponível"
                return result
            
            # Testa leitura
            try:
                response = client.table(table_name).select("*").limit(1).execute()
                result["can_read"] = True
                result["table_exists"] = True
                
                if response.data:
                    result["columns"] = list(response.data[0].keys())
                
                self.add_log(f"✅ Acesso de leitura à tabela {table_name} OK")
                
            except Exception as read_error:
                result["error"] = f"Erro de leitura: {str(read_error)}"
                self.add_log(f"❌ Erro de leitura na tabela {table_name}: {str(read_error)}")
            
            # Testa escrita (apenas se leitura funcionou)
            if result["can_read"]:
                try:
                    # Tenta inserir um registro de teste (que será deletado)
                    test_data = {"email": f"test_{datetime.now().timestamp()}@debug.com"}
                    insert_response = client.table(table_name).insert(test_data).execute()
                    
                    if insert_response.data:
                        # Deleta o registro de teste
                        test_id = insert_response.data[0].get("id")
                        if test_id:
                            client.table(table_name).delete().eq("id", test_id).execute()
                        
                        result["can_write"] = True
                        self.add_log(f"✅ Acesso de escrita à tabela {table_name} OK")
                    else:
                        self.add_log(f"⚠️ Inserção na tabela {table_name} não retornou dados")
                        
                except Exception as write_error:
                    self.add_log(f"⚠️ Erro de escrita na tabela {table_name}: {str(write_error)}")
        
        except Exception as e:
            result["error"] = str(e)
            self.add_log(f"❌ Erro geral ao testar tabela {table_name}: {str(e)}")
        
        return result
    
    def get_system_info(self) -> Dict[str, Any]:
        """Retorna informações do sistema"""
        info = {
            "python_version": os.sys.version,
            "streamlit_version": st.__version__,
            "supabase_version": None,
            "platform": os.name,
            "working_directory": os.getcwd(),
            "environment_variables": {
                "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
                "PATH": os.environ.get("PATH", "")[:100] + "..." if len(os.environ.get("PATH", "")) > 100 else os.environ.get("PATH", "")
            }
        }
        
        try:
            import supabase
            info["supabase_version"] = supabase.__version__
        except ImportError:
            info["supabase_version"] = "Não instalado"
        
        return info
    
    def get_logs(self, limit: int = 20) -> List[str]:
        """Retorna os logs de debug"""
        return self.logs[-limit:] if limit > 0 else self.logs
    
    def clear_logs(self):
        """Limpa os logs"""
        self.logs.clear()
        self.add_log("Logs limpos")

# Instância global do debugger
debugger = SupabaseDebugger()

def get_debugger() -> SupabaseDebugger:
    """Retorna a instância global do debugger"""
    return debugger
