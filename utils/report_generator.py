"""
Gerador de Relatório PDF no Padrão Vibra
Usa HTML/CSS + WeasyPrint para alta fidelidade visual
"""
import base64
from jinja2 import Environment, Template
from weasyprint import HTML, CSS
from datetime import datetime
from typing import Dict, Any, List, Optional
import io

# --- 1. Estilos CSS (Baseado na Identidade Visual Vibra) ---
CSS_STYLES = """
@page {
    size: A4;
    margin: 1.5cm;
    @top-center {
        content: element(header);
    }
    @bottom-center {
        content: "Página " counter(page);
        font-family: Arial, sans-serif;
        font-size: 9pt;
        color: #666;
    }
}

body { 
    font-family: 'Arial', sans-serif; 
    font-size: 10pt; 
    color: #000; 
    line-height: 1.4;
}

.header { 
    position: running(header); 
    width: 100%; 
    border-bottom: 3px solid #005f2f; 
    padding-bottom: 10px; 
    margin-bottom: 20px; 
}

.header-table { 
    width: 100%; 
    border-collapse: collapse;
}

.logo { 
    height: 50px; 
    max-width: 150px;
}

.vibra-green { 
    background-color: #005f2f; 
    color: white; 
    font-weight: bold; 
    padding: 8px; 
    text-align: left;
}

.section-title { 
    font-size: 14pt; 
    font-weight: bold; 
    margin-top: 20px; 
    margin-bottom: 10px; 
    text-transform: uppercase;
    color: #005f2f;
    border-bottom: 2px solid #005f2f;
    padding-bottom: 5px;
}

/* Tabelas estilo Formulário */
.form-table { 
    width: 100%; 
    border-collapse: collapse; 
    margin-bottom: 15px; 
    font-size: 9pt;
}

.form-table td, .form-table th { 
    border: 1px solid #ccc; 
    padding: 6px; 
    vertical-align: top; 
}

.form-table th {
    background-color: #f0f0f0;
    font-weight: bold;
}

.label { 
    font-size: 8pt; 
    color: #555; 
    font-weight: bold; 
    display: block; 
    margin-bottom: 2px;
}

.value { 
    font-size: 10pt; 
    color: #000;
}

.checkbox { 
    font-family: 'DejaVu Sans', sans-serif;
    font-size: 12pt;
}

/* Árvore de Causas */
.tree-image { 
    max-width: 100%; 
    height: auto; 
    margin: 15px 0; 
    border: 1px solid #ddd;
    page-break-inside: avoid;
}

/* Capa */
.cover-title { 
    text-align: center; 
    font-size: 28pt; 
    font-weight: bold; 
    margin-top: 250px;
    color: #005f2f;
}

.cover-subtitle { 
    text-align: center; 
    font-size: 18pt; 
    margin-top: 30px;
    color: #333;
}

.cover-info {
    text-align: center;
    margin-top: 80px;
    font-size: 12pt;
    line-height: 2;
}

/* Evidências */
.evidence-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin: 10px 0;
}

.evidence-img {
    max-width: 200px;
    max-height: 200px;
    border: 1px solid #ddd;
    page-break-inside: avoid;
}

/* Timeline */
.timeline-item {
    border-left: 3px solid #005f2f;
    padding-left: 15px;
    margin: 10px 0;
    page-break-inside: avoid;
}

.timeline-time {
    font-weight: bold;
    color: #005f2f;
}

/* Quebra de página */
.page-break {
    page-break-after: always;
}
"""

# --- 2. Template HTML (Jinja2) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Relatório de Investigação - {{ accident.get('registry_number', 'N/A') }}</title>
</head>
<body>
    <!-- Cabeçalho Repetitivo -->
    <div class="header">
        <table class="header-table">
            <tr>
                <td width="20%" style="vertical-align: middle;">
                    <div style="background-color: #005f2f; color: white; padding: 10px; text-align: center; font-weight: bold; font-size: 16pt;">
                        VIBRA
                    </div>
                </td>
                <td width="60%" style="text-align: center; font-weight: bold; font-size: 14pt; vertical-align: middle;">
                    Relatório de Análise e Investigação de Acidente
                </td>
                <td width="20%" style="text-align: right; font-size: 9pt; vertical-align: middle;">
                    Registro: {{ accident.get('registry_number', 'N/A') }}<br>
                    Data: {{ current_date }}
                </td>
            </tr>
        </table>
    </div>

    <!-- PÁGINA 1: CAPA -->
    <div class="cover-title">RELATÓRIO FINAL</div>
    <div class="cover-subtitle">Investigação de Acidente</div>
    <div class="cover-info">
        <strong>Evento:</strong> {{ accident.get('title', accident.get('description', 'N/A')) }}<br>
        {% if accident.get('site_name') %}
        <strong>Base:</strong> {{ accident.get('site_name', 'N/A') }}<br>
        {% endif %}
        <strong>Local da Base:</strong> {{ accident.get('base_location', 'N/A') }}<br>
        <strong>Data de Ocorrência:</strong> {{ accident.get('occurrence_date', accident.get('occurred_at', 'N/A')) }}<br>
        <strong>Comissão Constituída em:</strong> {{ accident.get('created_at', 'N/A') }}
    </div>

    <div class="page-break"></div>

    <!-- PÁGINA 2: RESUMO GERENCIAL -->
    <div class="section-title">RESUMO GERENCIAL DO RELATÓRIO FINAL</div>
    
    <table class="form-table">
        <tr>
            <td width="25%" class="vibra-green">Data/Hora</td>
            <td width="75%">
                {% if accident.get('occurrence_date') %}
                    {{ accident.occurrence_date }}
                {% elif accident.get('occurred_at') %}
                    {{ accident.occurred_at }}
                {% else %}
                    N/A
                {% endif %}
            </td>
        </tr>
        <tr>
            <td class="vibra-green">Base</td>
            <td>{{ accident.get('site_name', 'N/A') }}</td>
        </tr>
        <tr>
            <td class="vibra-green">Local da Base</td>
            <td>{{ accident.get('base_location', 'N/A') }}</td>
        </tr>
        <tr>
            <td class="vibra-green">Descrição Resumida</td>
            <td>{{ accident.get('description', accident.get('title', 'N/A')) }}</td>
        </tr>
        <tr>
            <td class="vibra-green">Tipo</td>
            <td>{{ accident.get('type', 'N/A') }}</td>
        </tr>
        <tr>
            <td class="vibra-green">Classificação</td>
            <td>{{ accident.get('classification', 'N/A') }}</td>
        </tr>
        {% if evidence_images %}
        <tr>
            <td class="vibra-green">Fotos</td>
            <td style="text-align: center;">
                {% for img in evidence_images[:3] %}
                    <img src="{{ img }}" class="evidence-img" style="margin: 5px;">
                {% endfor %}
            </td>
        </tr>
        {% endif %}
    </table>

    <div class="page-break"></div>

    <!-- PÁGINA 3: INFORMAÇÕES DETALHADAS -->
    <div class="section-title">1. INFORMAÇÕES DO EVENTO</div>
    
    <!-- 1.1 Dados Gerais -->
    <div class="vibra-green" style="margin-top: 10px;">1.1. Dados Gerais</div>
    <table class="form-table">
        <tr>
            <td width="25%"><span class="label">Número do Registro</span><span class="value">{{ accident.get('registry_number', 'N/A') }}</span></td>
            <td width="25%"><span class="label">Base</span><span class="value">{{ accident.get('site_name', 'N/A') }}</span></td>
            <td width="25%"><span class="label">Data de Ocorrência</span><span class="value">
                {% if accident.get('occurrence_date') %}
                    {{ accident.occurrence_date }}
                {% elif accident.get('occurred_at') %}
                    {{ accident.occurred_at }}
                {% else %}
                    N/A
                {% endif %}
            </span></td>
            <td width="25%"><span class="label">Status</span><span class="value">{{ accident.get('status', 'N/A') }}</span></td>
        </tr>
        <tr>
            <td colspan="4">
                <span class="label">Local da Base</span>
                <span class="value">{{ accident.get('base_location', 'N/A') }}</span>
            </td>
        </tr>
        <tr>
            <td colspan="4">
                <span class="label">Descrição Completa</span>
                <span class="value">{{ accident.get('description', accident.get('title', 'N/A')) }}</span>
            </td>
        </tr>
    </table>

    <!-- 1.2 Classificação -->
    <div class="vibra-green" style="margin-top: 10px;">1.2. Classificação</div>
    <table class="form-table">
        <tr>
            <td width="50%">
                <span class="label">Tipo de Impacto</span>
                <span class="checkbox">{{ '☑' if accident.get('class_injury') else '☐' }}</span> Acidente Com Lesão na Força de Trabalho<br>
                <span class="checkbox">{{ '☑' if accident.get('class_community') else '☐' }}</span> Acidente Com Lesão na Comunidade<br>
                <span class="checkbox">{{ '☑' if accident.get('class_environment') else '☐' }}</span> Impacto ao Meio Ambiente<br>
                <span class="checkbox">{{ '☑' if accident.get('class_process_safety') else '☐' }}</span> Segurança de Processo<br>
                <span class="checkbox">{{ '☑' if accident.get('class_asset_damage') else '☐' }}</span> Dano ao Patrimônio<br>
                <span class="checkbox">{{ '☑' if accident.get('class_near_miss') else '☐' }}</span> Quase-Acidente
            </td>
            <td width="50%">
                <span class="label">Gravidade Real/Potencial</span>
                <span class="checkbox">{{ '☑' if accident.get('severity_level') == 'Low' or accident.get('severity_level') == 'Baixa' else '☐' }}</span> Baixa<br>
                <span class="checkbox">{{ '☑' if accident.get('severity_level') == 'Medium' or accident.get('severity_level') == 'Média' else '☐' }}</span> Média<br>
                <span class="checkbox">{{ '☑' if accident.get('severity_level') == 'High' or accident.get('severity_level') == 'Alta' else '☐' }}</span> Alta<br>
                <span class="checkbox">{{ '☑' if accident.get('severity_level') == 'Catastrophic' or accident.get('severity_level') == 'Catastrófica' else '☐' }}</span> Catastrófica
            </td>
        </tr>
        {% if accident.get('estimated_loss_value') %}
        <tr>
            <td colspan="2">
                <span class="label">Valor Estimado de Perdas</span>
                <span class="value">R$ {{ "{:,.2f}".format(accident.estimated_loss_value) }}</span>
            </td>
        </tr>
        {% endif %}
    </table>

    <!-- 1.4 Perfil dos Motoristas -->
    {% if drivers %}
    {% for person in drivers %}
    <div class="vibra-green" style="margin-top: 10px;">1.4. Perfil do Motorista: {{ person.get('name', 'N/A') }}</div>
    <table class="form-table">
        <tr>
            <td width="20%"><span class="label">Nome</span><span class="value">{{ person.get('name', 'N/A') }}</span></td>
            <td width="20%"><span class="label">Idade</span><span class="value">{{ person.get('age', 'N/A') }}</span></td>
            <td width="20%"><span class="label">Função</span><span class="value">{{ person.get('job_title', 'N/A') }}</span></td>
            <td width="20%"><span class="label">Empresa</span><span class="value">{{ person.get('company', 'N/A') }}</span></td>
            <td width="20%"><span class="label">Matrícula/CPF</span><span class="value">{{ person.get('registration_id', 'N/A') }}</span></td>
        </tr>
        {% if person.get('time_in_role') or person.get('aso_date') %}
        <tr>
            <td colspan="2"><span class="label">Tempo na Função</span><span class="value">{{ person.get('time_in_role', 'N/A') }}</span></td>
            <td colspan="3"><span class="label">Data ASO</span><span class="value">{{ person.get('aso_date', 'N/A') }}</span></td>
        </tr>
        {% endif %}
    </table>
    {% endfor %}
    {% endif %}

    <!-- 1.7 Perfil das Vítimas/Lesionados -->
    {% if injured %}
    {% for person in injured %}
    <div class="vibra-green" style="margin-top: 10px;">1.7. Perfil da Vítima/Lesionado: {{ person.get('name', 'N/A') }}</div>
    <table class="form-table">
        <tr>
            <td width="20%"><span class="label">Nome</span><span class="value">{{ person.get('name', 'N/A') }}</span></td>
            <td width="20%"><span class="label">Idade</span><span class="value">{{ person.get('age', 'N/A') }}</span></td>
            <td width="20%"><span class="label">Função</span><span class="value">{{ person.get('job_title', 'N/A') }}</span></td>
            <td width="20%"><span class="label">Empresa</span><span class="value">{{ person.get('company', 'N/A') }}</span></td>
            <td width="20%"><span class="label">Matrícula/CPF</span><span class="value">{{ person.get('registration_id', 'N/A') }}</span></td>
        </tr>
        {% if person.get('time_in_role') or person.get('aso_date') %}
        <tr>
            <td colspan="2"><span class="label">Tempo na Função</span><span class="value">{{ person.get('time_in_role', 'N/A') }}</span></td>
            <td colspan="3"><span class="label">Data ASO</span><span class="value">{{ person.get('aso_date', 'N/A') }}</span></td>
        </tr>
        {% endif %}
    </table>
    {% endfor %}
    {% endif %}

    <!-- 1.8 Testemunhas -->
    {% if witnesses %}
    <div class="vibra-green" style="margin-top: 10px;">1.8. Testemunhas</div>
    <table class="form-table">
        <tr class="vibra-green">
            <th width="30%">Nome</th>
            <th width="30%">Matrícula/CPF</th>
            <th width="40%">Observações</th>
        </tr>
        {% for person in witnesses %}
        <tr>
            <td><span class="value">{{ person.get('name', 'N/A') }}</span></td>
            <td><span class="value">{{ person.get('registration_id', 'N/A') }}</span></td>
            <td><span class="value">{{ person.get('job_title', 'N/A') }}</span></td>
        </tr>
        {% endfor %}
    </table>
    {% endif %}

    <!-- 1.5 Vazamentos / Segurança de Processo -->
    {% if accident.get('class_process_safety') or accident.get('class_environment') %}
    <div class="vibra-green" style="margin-top: 10px;">1.5. Vazamentos / Segurança de Processo</div>
    <table class="form-table">
        <tr>
            <td width="25%"><span class="label">Produto Liberado</span><span class="value">{{ accident.get('product_released', 'N/A') }}</span></td>
            <td width="25%"><span class="label">Volume Liberado</span><span class="value">{{ accident.get('volume_released', 'N/A') }} m³</span></td>
            <td width="25%"><span class="label">Volume Recuperado</span><span class="value">{{ accident.get('volume_recovered', 'N/A') }} m³</span></td>
            <td width="25%"><span class="label">Duração</span><span class="value">{{ accident.get('release_duration_hours', 'N/A') }} horas</span></td>
        </tr>
        <tr>
            <td colspan="2"><span class="label">Equipamento Envolvido</span><span class="value">{{ accident.get('equipment_involved', 'N/A') }}</span></td>
            <td colspan="2"><span class="label">Área Afetada</span><span class="value">{{ accident.get('area_affected', 'N/A') }}</span></td>
        </tr>
    </table>
    {% endif %}

    <!-- 1.6 Cronologia -->
    {% if timeline_events %}
    <div class="vibra-green" style="margin-top: 10px;">1.6. Cronologia de Eventos</div>
    {% for event in timeline_events %}
    <div class="timeline-item">
        <span class="timeline-time">{{ event.get('event_time', 'N/A') }}</span><br>
        <span class="value">{{ event.get('description', 'N/A') }}</span>
    </div>
    {% endfor %}
    {% endif %}

    <div class="page-break"></div>

    <!-- PÁGINA 4: ÁRVORE DE FALHAS -->
    <div class="section-title">5. ANÁLISE DAS CAUSAS (ÁRVORE DE FALHAS)</div>
    
    <p style="margin-bottom: 15px;">Abaixo a representação gráfica da Árvore de Falhas gerada durante a investigação.</p>
    
    <!-- Imagem da árvore gerada pelo Graphviz -->
    <div style="text-align: center;">
        {% if fault_tree_image %}
            <img src="{{ fault_tree_image }}" class="tree-image">
        {% else %}
            <p style="color: #999; font-style: italic;">[Árvore de Falhas não disponível]</p>
        {% endif %}
    </div>

    <!-- Causas e Classificação NBR 14280 -->
    {% if verified_causes %}
    <div class="section-title" style="margin-top: 30px;">5.1. Classificação NBR 14280</div>
    <table class="form-table">
        <tr class="vibra-green">
            <th width="40%">Causa Identificada</th>
            <th width="20%">Código NBR</th>
            <th width="40%">Descrição NBR</th>
        </tr>
        {% for cause in verified_causes %}
        <tr>
            <td>{{ cause.get('label', 'N/A') }}</td>
            <td style="text-align: center; font-weight: bold;">{{ cause.get('nbr_code', 'N/A') }}</td>
            <td>{{ cause.get('nbr_description', 'N/A') }}</td>
        </tr>
        {% endfor %}
    </table>
    {% else %}
    <p style="color: #999; font-style: italic;">Nenhuma causa validada e classificada ainda.</p>
    {% endif %}

    <!-- 5.2 Hipóteses Descritas e Justificadas -->
    {% if hypotheses %}
    <div class="section-title" style="margin-top: 30px;">5.2. Hipóteses Descritas e Justificadas</div>
    <p style="margin-bottom: 15px; font-size: 10pt;">Abaixo são descritas todas as hipóteses levantadas durante a investigação, com suas respectivas justificativas para descarte ou consideração.</p>
    
    {% for hyp in hypotheses %}
    <div style="margin-bottom: 20px; page-break-inside: avoid;">
        <div class="vibra-green" style="margin-top: 10px; margin-bottom: 8px;">
            Hipótese {{ loop.index }}: {{ hyp.get('label', 'N/A') }}
        </div>
        <table class="form-table">
            <tr>
                <td width="20%" style="background-color: #f0f0f0; font-weight: bold;">Status</td>
                <td width="80%">
                    {% if hyp.get('status') == 'discarded' %}
                        <span style="color: #d32f2f; font-weight: bold;">✕ DESCARTADA</span>
                    {% elif hyp.get('status') == 'validated' %}
                        <span style="color: #2e7d32; font-weight: bold;">✓ CONSIDERADA/VALIDADA</span>
                    {% else %}
                        <span style="color: #666; font-weight: bold;">⏳ EM ANÁLISE</span>
                    {% endif %}
                </td>
            </tr>
            <tr>
                <td style="background-color: #f0f0f0; font-weight: bold;">Descrição</td>
                <td>{{ hyp.get('label', 'N/A') }}</td>
            </tr>
            <tr>
                <td style="background-color: #f0f0f0; font-weight: bold;">Justificativa</td>
                <td>
                    {% if hyp.get('justification') %}
                        {{ hyp.get('justification') }}
                    {% elif hyp.get('status') == 'discarded' %}
                        <span style="font-style: italic; color: #666;">Hipótese descartada após análise da evidência disponível.</span>
                    {% elif hyp.get('status') == 'validated' %}
                        <span style="font-style: italic; color: #666;">Hipótese validada com base nas evidências coletadas durante a investigação.</span>
                    {% else %}
                        <span style="font-style: italic; color: #666;">Hipótese em análise, aguardando validação ou descarte.</span>
                    {% endif %}
                </td>
            </tr>
            {% if hyp.get('nbr_code') %}
            <tr>
                <td style="background-color: #f0f0f0; font-weight: bold;">Código NBR</td>
                <td><strong>{{ hyp.get('nbr_code', 'N/A') }}</strong> - {{ hyp.get('nbr_description', '') }}</td>
            </tr>
            {% endif %}
        </table>
    </div>
    {% endfor %}
    {% else %}
    <div class="section-title" style="margin-top: 30px;">5.2. Hipóteses Descritas e Justificadas</div>
    <p style="color: #999; font-style: italic;">Nenhuma hipótese registrada ainda.</p>
    {% endif %}

    <div class="page-break"></div>

    <!-- PÁGINA 5: COMISSÃO -->
    <div class="section-title">7. COMISSÃO DE INVESTIGAÇÃO</div>
    
    {% if commission %}
    <table class="form-table">
        <tr class="vibra-green">
            <th width="30%">Nome</th>
            <th width="30%">Cargo/Função</th>
            <th width="20%">Matrícula/ID</th>
            <th width="20%">Participação</th>
        </tr>
        {% for member in commission %}
        <tr>
            <td>{{ member.get('name', 'N/A') }}</td>
            <td>{{ member.get('job_title', 'N/A') }}</td>
            <td>{{ member.get('registration_id', 'N/A') }}</td>
            <td>{{ member.get('commission_role') or member.get('training_status') or 'Membro da Comissão' }}</td>
        </tr>
        {% endfor %}
    </table>
    {% else %}
    <p style="color: #999; font-style: italic;">Comissão não registrada.</p>
    {% endif %}

    <!-- PÁGINA 6: EVIDÊNCIAS COMPLETAS -->
    {% if evidence_images and evidence_images|length > 3 %}
    <div class="page-break"></div>
    <div class="section-title">8. EVIDÊNCIAS COMPLETAS</div>
    <div class="evidence-grid">
        {% for img in evidence_images %}
            <img src="{{ img }}" class="evidence-img">
        {% endfor %}
    </div>
    {% endif %}

</body>
</html>
"""


def convert_image_url_to_base64(image_url: str) -> Optional[str]:
    """
    Converte URL de imagem para base64 (para embutir no PDF)
    """
    try:
        import requests
        from io import BytesIO
        
        # Se já for base64, retorna direto
        if image_url.startswith('data:image'):
            return image_url
        
        # Se for URL, faz download e converte
        response = requests.get(image_url, timeout=10)
        if response.status_code == 200:
            img_bytes = response.content
            img_b64 = base64.b64encode(img_bytes).decode('utf-8')
            # Detecta tipo de imagem
            if image_url.lower().endswith('.png'):
                return f"data:image/png;base64,{img_b64}"
            elif image_url.lower().endswith('.jpg') or image_url.lower().endswith('.jpeg'):
                return f"data:image/jpeg;base64,{img_b64}"
            else:
                return f"data:image/png;base64,{img_b64}"
        return None
    except Exception as e:
        print(f"Erro ao converter imagem {image_url}: {str(e)}")
        return None


def generate_fault_tree_image(tree_json: Dict[str, Any]) -> Optional[str]:
    """
    Gera imagem da árvore de falhas usando Graphviz e retorna como base64
    """
    try:
        import graphviz
        
        if not tree_json:
            return None
        
        dot = graphviz.Digraph(comment='Fault Tree Analysis')
        dot.attr(rankdir='TB')
        dot.attr('node', shape='box', style='rounded')
        
        # Cores baseadas no status
        color_map = {
            'validated': '#28a745',  # Verde - Confirmado
            'discarded': '#dc3545',  # Vermelho - Descartado
            'pending': '#6c757d'     # Cinza - Em análise
        }
        
        def add_node_recursive(node_json: Dict[str, Any]):
            """Função recursiva para adicionar nós e arestas"""
            node_id = node_json['id']
            label = node_json['label'][:40] + '...' if len(node_json['label']) > 40 else node_json['label']
            status = node_json['status']
            node_type = node_json['type']
            nbr_code = node_json.get('nbr_code')
            
            # Define cor e estilo
            color = color_map.get(status, '#6c757d')
            style = 'filled'
            if status == 'discarded':
                style = 'filled,strikethrough'
            
            # Label com tipo e código NBR
            display_label = f"{label}\n[{node_type}]"
            if nbr_code:
                display_label += f"\nNBR: {nbr_code}"
            
            font_color = 'white' if status != 'pending' else 'black'
            dot.node(node_id, display_label, fillcolor=color, style=style, fontcolor=font_color)
            
            # Processa filhos recursivamente
            for child in node_json.get('children', []):
                dot.edge(node_id, child['id'])
                add_node_recursive(child)
        
        # Inicia recursão a partir do nó raiz
        add_node_recursive(tree_json)
        
        # Gera PNG em bytes
        png_data = dot.pipe(format='png')
        
        # Converte para base64
        tree_b64 = base64.b64encode(png_data).decode('utf-8')
        return f"data:image/png;base64,{tree_b64}"
        
    except Exception as e:
        print(f"Erro ao gerar imagem da árvore: {str(e)}")
        return None


def extract_hypotheses_from_tree(tree_json: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extrai todas as hipóteses da árvore de falhas recursivamente.
    Retorna lista de hipóteses com label, status, nbr_code, nbr_description.
    """
    if not tree_json:
        return []
    
    hypotheses = []
    
    def extract_recursive(node: Dict[str, Any]):
        """Função recursiva para extrair hipóteses"""
        node_type = node.get('type', '')
        status = node.get('status', 'pending')
        
        # Considera como hipótese:
        # 1. Nós do tipo 'hypothesis'
        # 2. Nós com status 'pending', 'discarded' ou 'validated' que não sejam root
        # 3. Nós do tipo 'fact' com filhos (causas intermediárias)
        is_hypothesis = (
            node_type == 'hypothesis' or
            (node_type != 'root' and status in ['pending', 'discarded', 'validated']) or
            (node_type == 'fact' and node.get('children'))
        )
        
        if is_hypothesis and node_type != 'root':
            hyp_data = {
                'label': node.get('label', 'N/A'),
                'status': status,
                'nbr_code': node.get('nbr_code'),
                'nbr_description': node.get('nbr_description', ''),
                'justification': node.get('justification', '')  # Justificativa para confirmação/descarte
            }
            hypotheses.append(hyp_data)
        
        # Processa filhos recursivamente
        for child in node.get('children', []):
            extract_recursive(child)
    
    extract_recursive(tree_json)
    return hypotheses


def generate_pdf_report(
    accident_data: Dict[str, Any],
    people_data: List[Dict[str, Any]],
    timeline_events: List[Dict[str, Any]],
    verified_causes: List[Dict[str, Any]],
    evidence_images: List[str],
    fault_tree_json: Optional[Dict[str, Any]] = None
) -> bytes:
    """
    Gera o PDF preenchendo o template com os dados.
    
    Args:
        accident_data: Dados da tabela 'accidents'
        people_data: Lista da tabela 'involved_people'
        timeline_events: Lista de eventos da timeline
        verified_causes: Lista de nós validados com códigos NBR
        evidence_images: Lista de URLs ou base64 das imagens de evidência
        fault_tree_json: JSON da árvore de falhas (opcional, para gerar imagem)
    
    Returns:
        bytes: PDF gerado
    """
    try:
        # Gera imagem da árvore se JSON fornecido
        fault_tree_image = None
        if fault_tree_json:
            fault_tree_image = generate_fault_tree_image(fault_tree_json)
        
        # Extrai hipóteses da árvore
        hypotheses = extract_hypotheses_from_tree(fault_tree_json)
        
        # Filtra pessoas por tipo
        commission = [p for p in people_data if p.get('person_type') == 'Commission_Member']
        drivers = [p for p in people_data if p.get('person_type') == 'Driver']
        injured = [p for p in people_data if p.get('person_type') == 'Injured']
        witnesses = [p for p in people_data if p.get('person_type') == 'Witness']
        
        # Prepara data atual
        current_date = datetime.now().strftime('%d/%m/%Y')
        
        # Converte URLs de evidências para base64 (para embutir no PDF)
        evidence_images_b64 = []
        for img_url in evidence_images:
            if img_url:
                img_b64 = convert_image_url_to_base64(img_url)
                if img_b64:
                    evidence_images_b64.append(img_b64)
        
        # Renderiza HTML
        template = Template(HTML_TEMPLATE)
        rendered_html = template.render(
            accident=accident_data,
            people=people_data,
            drivers=drivers,
            injured=injured,
            witnesses=witnesses,
            timeline_events=timeline_events,
            verified_causes=verified_causes,
            hypotheses=hypotheses,
            fault_tree_image=fault_tree_image,
            evidence_images=evidence_images_b64,
            commission=commission,
            current_date=current_date
        )
        
        # Gera PDF
        pdf_bytes = HTML(string=rendered_html).write_pdf(
            stylesheets=[CSS(string=CSS_STYLES)]
        )
        
        return pdf_bytes
        
    except Exception as e:
        raise Exception(f"Erro ao gerar PDF: {str(e)}")

