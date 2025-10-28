"""
Sistema de Logging Simples para o Sistema SSO
"""
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List

class SimpleLogger:
    """Sistema de logging simples e robusto"""
    
    def __init__(self, name: str = "SSO_System"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Evita duplicação de handlers
        if not self.logger.handlers:
            self._setup_handlers()
        
        # Logs em memória para debug
        self.memory_logs: List[Dict[str, Any]] = []
        self.max_memory_logs = 1000
    
    def _setup_handlers(self):
        """Configura os handlers de logging de forma segura"""
        try:
            # Handler para console
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_format)
            self.logger.addHandler(console_handler)
            
        except Exception as e:
            # Se falhar, não faz nada
            pass
    
    def _add_memory_log(self, level: str, message: str, extra_data: Optional[Dict] = None):
        """Adiciona log à memória para debug"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": level,
                "message": message,
                "extra_data": extra_data or {}
            }
            
            self.memory_logs.append(log_entry)
            
            # Mantém apenas os últimos N logs
            if len(self.memory_logs) > self.max_memory_logs:
                self.memory_logs = self.memory_logs[-self.max_memory_logs:]
        except:
            # Se falhar, não faz nada
            pass
    
    def debug(self, message: str, extra_data: Optional[Dict] = None):
        """Log de debug"""
        try:
            self.logger.debug(message)
            self._add_memory_log("DEBUG", message, extra_data)
        except:
            pass
    
    def info(self, message: str, extra_data: Optional[Dict] = None):
        """Log de informação"""
        try:
            self.logger.info(message)
            self._add_memory_log("INFO", message, extra_data)
        except:
            pass
    
    def warning(self, message: str, extra_data: Optional[Dict] = None):
        """Log de aviso"""
        try:
            self.logger.warning(message)
            self._add_memory_log("WARNING", message, extra_data)
        except:
            pass
    
    def error(self, message: str, extra_data: Optional[Dict] = None):
        """Log de erro"""
        try:
            self.logger.error(message)
            self._add_memory_log("ERROR", message, extra_data)
        except:
            pass
    
    def critical(self, message: str, extra_data: Optional[Dict] = None):
        """Log crítico"""
        try:
            self.logger.critical(message)
            self._add_memory_log("CRITICAL", message, extra_data)
        except:
            pass
    
    def get_memory_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retorna logs da memória"""
        try:
            return self.memory_logs[-limit:] if limit > 0 else self.memory_logs
        except:
            return []
    
    def clear_memory_logs(self):
        """Limpa logs da memória"""
        try:
            self.memory_logs.clear()
            self.info("Logs da memória limpos")
        except:
            pass
    
    def get_system_info(self) -> Dict[str, Any]:
        """Retorna informações do sistema para debug"""
        try:
            import streamlit as st
            
            info = {
                "timestamp": datetime.now().isoformat(),
                "python_version": sys.version,
                "streamlit_version": st.__version__,
                "platform": os.name,
                "working_directory": os.getcwd(),
                "environment_variables": {
                    "SUPABASE_URL": bool(os.environ.get("SUPABASE_URL")),
                    "SUPABASE_ANON_KEY": bool(os.environ.get("SUPABASE_ANON_KEY")),
                    "SUPABASE_SERVICE_ROLE_KEY": bool(os.environ.get("SUPABASE_SERVICE_ROLE_KEY"))
                },
                "session_state": {
                    "authenticated_user_email": bool(st.session_state.get('authenticated_user_email')),
                    "role": st.session_state.get('role', 'N/A'),
                    "user_id": st.session_state.get('user_id', 'N/A')
                }
            }
            
            try:
                import supabase
                info["supabase_version"] = supabase.__version__
            except ImportError:
                info["supabase_version"] = "Não instalado"
            
            return info
        except:
            return {"error": "Não foi possível obter informações do sistema"}

# Instância global do logger (inicializada de forma segura)
_logger_instance = None

def get_logger() -> SimpleLogger:
    """Retorna a instância global do logger"""
    global _logger_instance
    if _logger_instance is None:
        try:
            _logger_instance = SimpleLogger()
        except Exception as e:
            # Fallback: cria logger básico
            print(f"Erro ao criar logger: {e}")
            _logger_instance = SimpleLogger("SSO_Fallback")
    return _logger_instance

# Funções de conveniência
def log_debug(message: str, extra_data: Optional[Dict] = None):
    """Log de debug"""
    get_logger().debug(message, extra_data)

def log_info(message: str, extra_data: Optional[Dict] = None):
    """Log de informação"""
    get_logger().info(message, extra_data)

def log_warning(message: str, extra_data: Optional[Dict] = None):
    """Log de aviso"""
    get_logger().warning(message, extra_data)

def log_error(message: str, extra_data: Optional[Dict] = None):
    """Log de erro"""
    get_logger().error(message, extra_data)

def log_critical(message: str, extra_data: Optional[Dict] = None):
    """Log crítico"""
    get_logger().critical(message, extra_data)
