"""
Configurações do Sistema SSO
"""
import os
from typing import Dict, Any

# Configurações do Supabase
SUPABASE_CONFIG = {
    "url": os.environ.get("SUPABASE_URL", ""),
    "anon_key": os.environ.get("SUPABASE_ANON_KEY", ""),
}

# Configurações do sistema
SYSTEM_CONFIG = {
    "app_title": "Sistema SSO - Monitoramento",
    "app_icon": "🛡️",
    "page_layout": "wide",
    "initial_sidebar_state": "expanded"
}

# Configurações de KPIs
KPI_CONFIG = {
    "frequency_rate_multiplier": 1_000_000,  # Multiplicador para taxa de frequência
    "severity_rate_multiplier": 1_000_000,  # Multiplicador para taxa de gravidade
    "ewma_lambda_default": 0.2,  # Parâmetro lambda padrão para EWMA
    "control_limits_sigma": 3,  # Número de sigmas para limites de controle
}

# Configurações de upload
UPLOAD_CONFIG = {
    "max_file_size_mb": 50,
    "allowed_extensions": ['.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx'],
    "storage_bucket": "evidencias"
}

# Configurações de autenticação
AUTH_CONFIG = {
    "session_timeout_hours": 24,
    "enable_oidc": True,
    "oidc_provider": "google",
    "auto_create_profiles": True,
    "default_role": "viewer"
}

# Configurações de relatórios
REPORT_CONFIG = {
    "default_period_months": 12,
    "max_records_per_page": 100,
    "export_formats": ["csv", "excel"]
}

def get_config(section: str) -> Dict[str, Any]:
    """Retorna configurações de uma seção específica"""
    configs = {
        "supabase": SUPABASE_CONFIG,
        "system": SYSTEM_CONFIG,
        "kpi": KPI_CONFIG,
        "upload": UPLOAD_CONFIG,
        "auth": AUTH_CONFIG,
        "report": REPORT_CONFIG
    }
    return configs.get(section, {})

def validate_config() -> bool:
    """Valida se as configurações essenciais estão presentes"""
    required_vars = ["SUPABASE_URL", "SUPABASE_ANON_KEY"]
    
    for var in required_vars:
        if not os.environ.get(var):
            return False
    
    return True
