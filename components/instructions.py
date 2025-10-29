import streamlit as st
from typing import Dict, List, Optional

def create_instructions_page(
    title: str,
    description: str,
    sections: List[Dict[str, any]],
    tips: Optional[List[str]] = None,
    warnings: Optional[List[str]] = None,
    references: Optional[List[str]] = None
):
    """
    Cria uma página de instruções padronizada para qualquer módulo do sistema.
    
    Args:
        title: Título da página de instruções
        description: Descrição geral do módulo
        sections: Lista de seções com título, conteúdo e tipo
        tips: Lista de dicas importantes
        warnings: Lista de avisos importantes
        references: Lista de referências e normas
    """
    
    st.title(f"📚 {title}")
    
    # Descrição geral
    st.markdown(f"## 🎯 Objetivo")
    st.markdown(description)
    
    # Seções principais
    for section in sections:
        section_type = section.get('type', 'info')
        section_title = section.get('title', '')
        section_content = section.get('content', '')
        section_icon = section.get('icon', '📋')
        
        if section_type == 'info':
            st.markdown(f"### {section_icon} {section_title}")
            st.markdown(section_content)
        
        elif section_type == 'steps':
            st.markdown(f"### {section_icon} {section_title}")
            steps = section.get('steps', [])
            for i, step in enumerate(steps, 1):
                st.markdown(f"**{i}.** {step}")
        
        elif section_type == 'metrics':
            st.markdown(f"### {section_icon} {section_title}")
            st.markdown(section_content)
            
            # Cria colunas para métricas
            metrics = section.get('metrics', [])
            if metrics:
                cols = st.columns(len(metrics))
                for i, metric in enumerate(metrics):
                    with cols[i]:
                        st.metric(
                            metric.get('title', ''),
                            metric.get('value', ''),
                            metric.get('delta', ''),
                            help=metric.get('help', '')
                        )
        
        elif section_type == 'chart':
            st.markdown(f"### {section_icon} {section_title}")
            st.markdown(section_content)
            
            # Aqui você pode adicionar lógica para diferentes tipos de gráficos
            chart_type = section.get('chart_type', 'bar')
            if chart_type == 'example':
                st.info("📊 **Exemplo de Gráfico**\n\nAqui seria exibido um exemplo do tipo de visualização utilizada neste módulo.")
        
        elif section_type == 'table':
            st.markdown(f"### {section_icon} {section_title}")
            st.markdown(section_content)
            
            # Exemplo de tabela
            table_data = section.get('table_data', [])
            if table_data:
                import pandas as pd
                df = pd.DataFrame(table_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Dicas importantes
    if tips:
        st.markdown("## 💡 Dicas Importantes")
        for tip in tips:
            st.info(f"💡 {tip}")
    
    # Avisos importantes
    if warnings:
        st.markdown("## ⚠️ Avisos Importantes")
        for warning in warnings:
            st.warning(f"⚠️ {warning}")
    
    # Referências
    if references:
        st.markdown("## 📚 Referências e Normas")
        for ref in references:
            st.markdown(f"- {ref}")

def get_accidents_instructions():
    """Retorna as instruções específicas para o módulo de Acidentes"""
    
    return {
        "title": "Instruções - Módulo de Acidentes",
        "description": """
        O módulo de Acidentes permite registrar, analisar e gerenciar acidentes de trabalho conforme 
        as normas regulamentadoras brasileiras. Este módulo é essencial para a gestão de segurança 
        e saúde ocupacional, fornecendo insights valiosos para prevenção de acidentes futuros.
        """,
        "sections": [
            {
                "type": "info",
                "title": "Funcionalidades Principais",
                "icon": "🔧",
                "content": """
                - **Registro de Acidentes**: Cadastro completo com classificação NBR 14280
                - **Análise de Dias Trabalhados**: Cálculo de dias trabalhados até o acidente
                - **Classificação por Gravidade**: Leve, Moderado, Grave e Fatal
                - **Gestão de Evidências**: Upload e organização de documentos
                - **Relatórios e Estatísticas**: Dashboards e análises detalhadas
                - **Conformidade Legal**: Atendimento às normas regulamentadoras
                """
            },
            {
                "type": "steps",
                "title": "Como Registrar um Acidente",
                "icon": "📝",
                "steps": [
                    "Acesse a aba 'Novo Acidente'",
                    "Preencha os dados básicos (data, tipo, descrição)",
                    "Informe os dias perdidos e se é fatal",
                    "Adicione a classificação NBR 14280",
                    "Preencha os dados de investigação",
                    "Faça upload das evidências",
                    "Clique em 'Salvar Acidente'"
                ]
            },
            {
                "type": "metrics",
                "title": "Métricas de Análise",
                "icon": "📊",
                "content": "O sistema calcula automaticamente as seguintes métricas:",
                "metrics": [
                    {
                        "title": "Taxa de Frequência",
                        "value": "Acidentes/1M horas",
                        "help": "Indica quantos acidentes ocorrem por milhão de horas trabalhadas"
                    },
                    {
                        "title": "Taxa de Gravidade", 
                        "value": "Dias perdidos/1M horas",
                        "help": "Indica quantos dias são perdidos por milhão de horas trabalhadas"
                    },
                    {
                        "title": "Dias Trabalhados",
                        "value": "Média de dias",
                        "help": "Média de dias trabalhados até o acidente acontecer"
                    }
                ]
            },
            {
                "type": "info",
                "title": "Classificação NBR 14280",
                "icon": "📋",
                "content": """
                **Leve**: 1-15 dias perdidos  
                **Moderado**: 16-30 dias perdidos  
                **Grave**: 31+ dias perdidos  
                **Fatal**: Acidentes que resultam em morte
                
                A classificação é feita automaticamente pelo sistema baseada nos dias perdidos.
                """
            },
            {
                "type": "chart",
                "title": "Visualizações Disponíveis",
                "icon": "📈",
                "content": "O módulo oferece diversos tipos de visualizações:",
                "chart_type": "example"
            },
            {
                "type": "table",
                "title": "Campos Obrigatórios",
                "icon": "📋",
                "content": "Para registrar um acidente, os seguintes campos são obrigatórios:",
                "table_data": [
                    {"Campo": "Data do Acidente", "Obrigatório": "Sim", "Tipo": "Data"},
                    {"Campo": "Tipo", "Obrigatório": "Sim", "Tipo": "Seleção"},
                    {"Campo": "Descrição", "Obrigatório": "Sim", "Tipo": "Texto"},
                    {"Campo": "Dias Perdidos", "Obrigatório": "Sim", "Tipo": "Número"},
                    {"Campo": "Causa Raiz", "Obrigatório": "Sim", "Tipo": "Seleção"}
                ]
            }
        ],
        "tips": [
            "Sempre preencha a descrição de forma detalhada para facilitar a investigação",
            "Faça upload de evidências (fotos, documentos) sempre que possível",
            "Classifique corretamente a causa raiz para melhor análise preventiva",
            "Mantenha os dados de investigação sempre atualizados"
        ],
        "warnings": [
            "Acidentes fatais devem ser comunicados imediatamente às autoridades competentes",
            "A CAT (Comunicação de Acidente de Trabalho) deve ser emitida em até 24 horas",
            "Dados incorretos podem comprometer a análise e prevenção de acidentes"
        ],
        "references": [
            "NR-5: Comissão Interna de Prevenção de Acidentes",
            "NR-7: Programa de Controle Médico de Saúde Ocupacional", 
            "NBR 14280: Cadastro de Acidente do Trabalho",
            "ISO 45001: Sistema de Gestão de SST"
        ]
    }

def get_kpis_instructions():
    """Retorna as instruções específicas para o módulo de KPIs"""
    
    return {
        "title": "Instruções - Módulo de KPIs e Controles",
        "description": """
        O módulo de KPIs e Controles Estatísticos fornece indicadores de desempenho em segurança 
        e saúde ocupacional, permitindo monitoramento contínuo e tomada de decisão baseada em dados.
        """,
        "sections": [
            {
                "type": "info",
                "title": "Indicadores Principais",
                "icon": "📊",
                "content": """
                - **Taxa de Frequência**: Acidentes por 1 milhão de horas trabalhadas
                - **Taxa de Gravidade**: Dias perdidos por 1 milhão de horas trabalhadas
                - **Controles Estatísticos**: Gráficos de controle para monitoramento
                - **Previsões**: Projeções baseadas em tendências históricas
                - **Benchmarking**: Comparação com metas e padrões
                """
            },
            {
                "type": "steps",
                "title": "Como Interpretar os KPIs",
                "icon": "🔍",
                "steps": [
                    "Verifique se os dados estão atualizados",
                    "Compare com metas estabelecidas",
                    "Analise tendências ao longo do tempo",
                    "Identifique padrões anômalos",
                    "Tome ações corretivas quando necessário"
                ]
            },
            {
                "type": "metrics",
                "title": "Metas Recomendadas",
                "icon": "🎯",
                "content": "Valores de referência para os indicadores:",
                "metrics": [
                    {
                        "title": "Taxa de Frequência",
                        "value": "< 5",
                        "help": "Excelente: menos de 5 acidentes por 1M horas"
                    },
                    {
                        "title": "Taxa de Gravidade",
                        "value": "< 50", 
                        "help": "Excelente: menos de 50 dias perdidos por 1M horas"
                    }
                ]
            }
        ],
        "tips": [
            "Monitore os indicadores mensalmente para identificar tendências",
            "Configure alertas para valores que excedam os limites aceitáveis",
            "Use os controles estatísticos para detectar padrões anômalos"
        ],
        "warnings": [
            "Valores muito baixos podem indicar subnotificação de acidentes",
            "Picos súbitos nos indicadores requerem investigação imediata"
        ],
        "references": [
            "NR-4: Serviços Especializados em Engenharia de Segurança",
            "ISO 45001: Sistema de Gestão de SST",
            "ANSI Z16.1: Métodos de Registro de Acidentes"
        ]
    }

def get_general_instructions():
    """Retorna as instruções gerais do sistema"""
    
    return {
        "title": "Instruções Gerais do Sistema",
        "description": """
        O Sistema de Gestão de Segurança e Saúde Ocupacional (SSO) é uma ferramenta completa 
        para gestão de indicadores de segurança, permitindo registro, análise e monitoramento 
        de acidentes, quase-acidentes e não conformidades.
        """,
        "sections": [
            {
                "type": "info",
                "title": "Módulos Disponíveis",
                "icon": "🏗️",
                "content": """
                - **Visão Geral**: Dashboard executivo com indicadores principais
                - **Acidentes**: Registro e análise de acidentes de trabalho
                - **Quase Acidentes**: Gestão de eventos que quase causaram acidentes
                - **Não Conformidades**: Controle de desvios e não conformidades
                - **KPIs e Controles**: Indicadores estatísticos e controles
                - **Admin Dados Básicos**: Gestão de usuários e configurações
                - **Logs Sistema**: Auditoria e logs do sistema
                """
            },
            {
                "type": "steps",
                "title": "Primeiros Passos",
                "icon": "🚀",
                "steps": [
                    "Configure seus dados básicos no módulo Admin",
                    "Registre as horas trabalhadas mensais",
                    "Comece registrando acidentes e eventos",
                    "Configure metas e limites nos KPIs",
                    "Monitore regularmente os indicadores"
                ]
            }
        ],
        "tips": [
            "Use os filtros para analisar períodos específicos",
            "Exporte relatórios regularmente para backup",
            "Mantenha os dados sempre atualizados"
        ],
        "warnings": [
            "Faça backup regular dos dados importantes",
            "Mantenha as senhas seguras e atualizadas"
        ],
        "references": [
            "Manual do Usuário do Sistema SSO",
            "Normas Regulamentadoras do MTE",
            "ISO 45001: Sistema de Gestão de SST"
        ]
    }
