"""
Classificação de Acidentes conforme NBR 14280:2001
Sistema de Gestão de Segurança e Saúde Ocupacional (SSO)
"""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass

class AccidentSeverity(Enum):
    """
    Classificação de gravidade dos acidentes conforme NBR 14280:2001
    
    A NBR 14280 estabelece critérios para classificação de acidentes de trabalho
    baseados na natureza das lesões e no tempo de afastamento.
    """
    LEVE = "leve"
    MODERADO = "moderado"
    GRAVE = "grave"
    FATAL = "fatal"

class AccidentType(Enum):
    """
    Tipos de acidentes conforme NBR 14280:2001
    """
    FATAL = "fatal"
    COM_LESAO = "com_lesao"
    SEM_LESAO = "sem_lesao"

@dataclass
class SeverityCriteria:
    """
    Critérios para classificação de severidade conforme NBR 14280
    """
    name: str
    description: str
    lost_days_min: Optional[int]
    lost_days_max: Optional[int]
    injury_type: str
    color: str
    icon: str

# Definições dos critérios conforme NBR 14280
SEVERITY_CRITERIA: Dict[AccidentSeverity, SeverityCriteria] = {
    AccidentSeverity.LEVE: SeverityCriteria(
        name="Leve",
        description="Acidente que resulta em lesão temporária com afastamento de até 15 dias",
        lost_days_min=1,
        lost_days_max=15,
        injury_type="Lesão temporária",
        color="#28a745",  # Verde
        icon="🟢"
    ),
    AccidentSeverity.MODERADO: SeverityCriteria(
        name="Moderado", 
        description="Acidente que resulta em lesão temporária com afastamento de 16 a 30 dias",
        lost_days_min=16,
        lost_days_max=30,
        injury_type="Lesão temporária",
        color="#ffc107",  # Amarelo
        icon="🟡"
    ),
    AccidentSeverity.GRAVE: SeverityCriteria(
        name="Grave",
        description="Acidente que resulta em lesão temporária com afastamento superior a 30 dias ou lesão permanente",
        lost_days_min=31,
        lost_days_max=None,  # Sem limite superior
        injury_type="Lesão temporária prolongada ou permanente",
        color="#fd7e14",  # Laranja
        icon="🟠"
    ),
    AccidentSeverity.FATAL: SeverityCriteria(
        name="Fatal",
        description="Acidente que resulta em morte do trabalhador",
        lost_days_min=None,
        lost_days_max=None,
        injury_type="Morte",
        color="#dc3545",  # Vermelho
        icon="🔴"
    )
}

def classify_accident_severity(lost_days: int, is_fatal: bool = False) -> Optional[AccidentSeverity]:
    """
    Classifica a severidade do acidente baseado nos critérios da NBR 14280
    
    Args:
        lost_days: Número de dias perdidos
        is_fatal: Se o acidente resultou em morte
        
    Returns:
        Optional[AccidentSeverity]: Classificação da severidade ou None se não aplicável
    """
    if is_fatal:
        return AccidentSeverity.FATAL
    
    if lost_days == 0:
        # Acidente sem lesão - não se aplica classificação de severidade
        return None
    
    if 1 <= lost_days <= 15:
        return AccidentSeverity.LEVE
    elif 16 <= lost_days <= 30:
        return AccidentSeverity.MODERADO
    elif lost_days >= 31:
        return AccidentSeverity.GRAVE
    else:
        # Caso inválido
        return None

def get_severity_description(severity: AccidentSeverity) -> str:
    """
    Retorna a descrição completa da severidade
    
    Args:
        severity: Classificação de severidade
        
    Returns:
        str: Descrição da severidade
    """
    if severity not in SEVERITY_CRITERIA:
        return "Classificação não definida"
    
    criteria = SEVERITY_CRITERIA[severity]
    return f"{criteria.icon} {criteria.name}: {criteria.description}"

def get_severity_color(severity: AccidentSeverity) -> str:
    """
    Retorna a cor associada à severidade
    
    Args:
        severity: Classificação de severidade
        
    Returns:
        str: Código da cor em hexadecimal
    """
    if severity not in SEVERITY_CRITERIA:
        return "#6c757d"  # Cinza padrão
    
    return SEVERITY_CRITERIA[severity].color

def get_severity_icon(severity: AccidentSeverity) -> str:
    """
    Retorna o ícone associado à severidade
    
    Args:
        severity: Classificação de severidade
        
    Returns:
        str: Emoji do ícone
    """
    if severity not in SEVERITY_CRITERIA:
        return "❓"
    
    return SEVERITY_CRITERIA[severity].icon

def get_all_severities() -> List[Dict]:
    """
    Retorna lista de todas as severidades com suas informações
    
    Returns:
        List[Dict]: Lista com informações de cada severidade
    """
    severities = []
    for severity, criteria in SEVERITY_CRITERIA.items():
        severities.append({
            'value': severity.value,
            'name': criteria.name,
            'description': criteria.description,
            'lost_days_min': criteria.lost_days_min,
            'lost_days_max': criteria.lost_days_max,
            'injury_type': criteria.injury_type,
            'color': criteria.color,
            'icon': criteria.icon
        })
    
    return severities

def validate_accident_data(accident_type: str, lost_days: int, is_fatal: bool = False) -> Dict:
    """
    Valida os dados do acidente e retorna classificação e alertas
    
    Args:
        accident_type: Tipo do acidente (fatal, com_lesao, sem_lesao)
        lost_days: Número de dias perdidos
        is_fatal: Se o acidente resultou em morte
        
    Returns:
        Dict: Dados validados e classificação
    """
    validation_result = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'severity': None,
        'recommendations': []
    }
    
    # Validação de consistência
    if is_fatal and accident_type != 'fatal':
        validation_result['warnings'].append(
            "Inconsistência: Acidente marcado como fatal mas tipo não é 'fatal'"
        )
    
    if accident_type == 'fatal' and not is_fatal:
        validation_result['warnings'].append(
            "Inconsistência: Tipo 'fatal' mas não marcado como fatal"
        )
    
    if accident_type == 'sem_lesao' and lost_days > 0:
        validation_result['errors'].append(
            "Inconsistência: Acidente sem lesão não pode ter dias perdidos"
        )
    
    if accident_type == 'com_lesao' and lost_days == 0:
        validation_result['warnings'].append(
            "Atenção: Acidente com lesão sem dias perdidos - verificar classificação"
        )
    
    # Classificação de severidade
    if accident_type in ['fatal', 'com_lesao']:
        severity = classify_accident_severity(lost_days, is_fatal)
        validation_result['severity'] = severity
        
        if severity:
            criteria = SEVERITY_CRITERIA[severity]
            validation_result['recommendations'].append(
                f"Classificação NBR 14280: {criteria.name}"
            )
    
    # Recomendações específicas
    if lost_days > 0:
        if lost_days > 30:
            validation_result['recommendations'].append(
                "Acidente grave - requer investigação detalhada conforme NBR 14280"
            )
        elif lost_days > 15:
            validation_result['recommendations'].append(
                "Acidente moderado - monitorar evolução do tratamento"
            )
    
    if is_fatal:
        validation_result['recommendations'].append(
            "Acidente fatal - notificar imediatamente órgãos competentes"
        )
    
    validation_result['is_valid'] = len(validation_result['errors']) == 0
    
    return validation_result

# Constantes para uso em formulários e interfaces
SEVERITY_OPTIONS = [
    {
        'value': severity.value,
        'label': f"{criteria.icon} {criteria.name}",
        'description': criteria.description
    }
    for severity, criteria in SEVERITY_CRITERIA.items()
]

# Mapeamento para compatibilidade com sistema existente
LEGACY_TYPE_MAPPING = {
    'fatal': AccidentType.FATAL,
    'lesao': AccidentType.COM_LESAO,
    'sem_lesao': AccidentType.SEM_LESAO
}

def convert_legacy_type(legacy_type: str) -> AccidentType:
    """
    Converte tipo legado para novo enum
    
    Args:
        legacy_type: Tipo no formato antigo
        
    Returns:
        AccidentType: Tipo no novo formato
    """
    return LEGACY_TYPE_MAPPING.get(legacy_type, AccidentType.SEM_LESAO)
