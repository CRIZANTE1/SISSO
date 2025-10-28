"""
Sistema de Logging Integrado para o Sistema SSO
"""
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

class SSOLogger:
    """Sistema de logging centralizado para o Sistema SSO"""
    
    def __init__(self, name: str = "SSO_System"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Evita duplicação de handlers
        if not self.logger.handlers:
            self._setup_handlers()
        
        # Logs em memória para debug
        self.memory_logs: List[Dict[str, Any]] = []
        self.max_memory_logs = 1000
    
    def _setup_handlers(self):
        """Configura os handlers de logging"""
        
        # Handler para console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        
        # Handler para arquivo
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(
            log_dir / f"sso_system_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        
        # Adiciona handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def _add_memory_log(self, level: str, message: str, extra_data: Optional[Dict] = None):
        """Adiciona log à memória para debug"""
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
    
    def debug(self, message: str, extra_data: Optional[Dict] = None):
        """Log de debug"""
        self.logger.debug(message)
        self._add_memory_log("DEBUG", message, extra_data)
    
    def info(self, message: str, extra_data: Optional[Dict] = None):
        """Log de informação"""
        self.logger.info(message)
        self._add_memory_log("INFO", message, extra_data)
    
    def warning(self, message: str, extra_data: Optional[Dict] = None):
        """Log de aviso"""
        self.logger.warning(message)
        self._add_memory_log("WARNING", message, extra_data)
    
    def error(self, message: str, extra_data: Optional[Dict] = None):
        """Log de erro"""
        self.logger.error(message)
        self._add_memory_log("ERROR", message, extra_data)
    
    def critical(self, message: str, extra_data: Optional[Dict] = None):
        """Log crítico"""
        self.logger.critical(message)
        self._add_memory_log("CRITICAL", message, extra_data)
    
    def get_memory_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retorna logs da memória"""
        return self.memory_logs[-limit:] if limit > 0 else self.memory_logs
    
    def clear_memory_logs(self):
        """Limpa logs da memória"""
        self.memory_logs.clear()
        self.info("Logs da memória limpos")
    
    def get_system_info(self) -> Dict[str, Any]:
        """Retorna informações do sistema para debug"""
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

# Instância global do logger
logger = SSOLogger()

def get_logger() -> SSOLogger:
    """Retorna a instância global do logger"""
    return logger

# Funções de conveniência
def log_debug(message: str, extra_data: Optional[Dict] = None):
    """Log de debug"""
    logger.debug(message, extra_data)

def log_info(message: str, extra_data: Optional[Dict] = None):
    """Log de informação"""
    logger.info(message, extra_data)

def log_warning(message: str, extra_data: Optional[Dict] = None):
    """Log de aviso"""
    logger.warning(message, extra_data)

def log_error(message: str, extra_data: Optional[Dict] = None):
    """Log de erro"""
    logger.error(message, extra_data)

def log_critical(message: str, extra_data: Optional[Dict] = None):
    """Log crítico"""
    logger.critical(message, extra_data)
