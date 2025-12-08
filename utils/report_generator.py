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

# --- 1. Estilos CSS ---
CSS_STYLES = """
@page {
    size: A4;
    margin: 3cm 1.5cm 1.5cm 1.5cm;  /* Aumenta margem superior para 3cm */
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

@page fault-tree-page {
    size: A4 landscape;
    margin: 1cm;
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
    margin: 0;
    padding: 0;
}

.content-wrapper {
    margin-top: 0;
    padding-top: 0;
}

.header { 
    position: running(header); 
    width: 100%; 
    border-bottom: 3px solid #d3d3d3; 
    padding-bottom: 10px; 
    margin-bottom: 20px; 
}

.header-table { 
    width: 100%; 
    border-collapse: collapse;
}

.vibra-green { 
    background-color: #d3d3d3; 
    color: #333; 
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
    color: #666;
    border-bottom: 2px solid #d3d3d3;
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

/* Estilos para árvore de falhas HTML/CSS */
.fault-tree-container {
    position: relative;
    font-family: Arial, sans-serif;
    padding: 20px;
    background: white;
    min-height: 300px;
    page-break-inside: avoid;
    margin: 15px 0;
}

.fault-tree-title {
    text-align: center;
    margin-bottom: 20px;
    color: #333;
    font-size: 12pt;
    font-weight: bold;
}

.fault-tree-legend {
    position: absolute;
    top: 10px;
    right: 10px;
    background: white;
    border: 2px solid #333;
    padding: 8px;
    border-radius: 4px;
    font-size: 7pt;
    z-index: 1000;
    max-width: 180px;
}

.fault-tree-node {
    position: relative;
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    margin: 5px;
}

.fault-tree-node-diamond {
    width: 180px;
    height: 180px;
    position: relative;
}

.fault-tree-node-oval {
    border-radius: 50%;
    width: 180px;
    min-height: 70px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 12px 18px;
}

.fault-tree-node-rect {
    border-radius: 8px;
    width: 200px;
    min-height: 70px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 12px 18px;
}

.fault-tree-connector {
    position: absolute;
    left: 50%;
    top: -15px;
    width: 2px;
    height: 15px;
    background-color: #2196f3;
    transform: translateX(-50%);
}

.fault-tree-children {
    position: relative;
    margin-top: 15px;
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    align-items: flex-start;
    gap: 15px;
    padding-top: 30px;
}

.fault-tree-node-number {
    position: absolute;
    top: -10px;
    left: -10px;
    background-color: #f9a825;
    color: white;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 8pt;
    z-index: 10;
}

.fault-tree-discard-x {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 2.5em;
    color: #d32f2f;
    font-weight: bold;
    z-index: 5;
}

/* Capa */
.cover-title { 
    text-align: center; 
    font-size: 28pt; 
    font-weight: bold; 
    margin-top: 250px;
    color: #666;
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
    border-left: 3px solid #d3d3d3;
    padding-left: 15px;
    margin: 10px 0;
    page-break-inside: avoid;
}

.timeline-time {
    font-weight: bold;
    color: #666;
}

/* Quebra de página */
.page-break {
    page-break-after: always;
}

/* Página da árvore em paisagem */
.fault-tree-landscape {
    page: fault-tree-page;
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
                <td width="70%" style="text-align: center; font-weight: bold; font-size: 14pt; vertical-align: middle;">
                    Relatório de Análise e Investigação de Acidente
                </td>
                <td width="30%" style="text-align: right; font-size: 9pt; vertical-align: middle;">
                    Registro: {{ accident.get('registry_number', 'N/A') }}<br>
                    Data: {{ current_date }}
                </td>
            </tr>
        </table>
    </div>

    <div class="content-wrapper">
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

    <!-- PÁGINA 2: METODOLOGIA -->
    <div class="section-title">2. METODOLOGIA DE INVESTIGAÇÃO</div>
    
    <div style="text-align: justify; line-height: 1.6; margin-bottom: 15px;">
        <p style="margin-bottom: 12px;">
            A investigação deste acidente foi conduzida utilizando a metodologia de <strong>Análise de Árvore de Falhas (FTA - Fault Tree Analysis)</strong>, 
            uma técnica sistemática e estruturada para identificar e analisar as causas raiz de eventos indesejados. Esta metodologia permite uma 
            representação gráfica hierárquica das relações causais, facilitando a compreensão dos fatores que contribuíram para a ocorrência do acidente.
        </p>
        
        <p style="margin-bottom: 12px;">
            A FTA é amplamente reconhecida na indústria como uma ferramenta eficaz para investigação de acidentes, conforme estabelecido pela 
            <strong>NBR 14280:2019 - Cadastro de acidente do trabalho - Procedimento e classificação</strong> <sup>1</sup>, que estabelece os critérios 
            para classificação e registro de acidentes do trabalho no Brasil. A norma define parâmetros para classificação de acidentes com e sem 
            afastamento, além de estabelecer critérios para cálculo de indicadores de segurança.
        </p>
        
        <p style="margin-bottom: 12px;">
            A metodologia segue os princípios estabelecidos pela <strong>ISO 31010:2019 - Risk management - Risk assessment techniques</strong> <sup>2</sup>, 
            que apresenta a Análise de Árvore de Falhas como uma técnica recomendada para análise de riscos e investigação de eventos. A norma internacional 
            destaca a capacidade da FTA em identificar combinações de falhas que podem levar a eventos indesejados, permitindo uma análise probabilística 
            e qualitativa dos fatores contribuintes.
        </p>
        
        <p style="margin-bottom: 12px;">
            Durante a investigação, foram aplicados os princípios da <strong>Análise de Causa Raiz (RCA - Root Cause Analysis)</strong>, conforme metodologia 
            descrita por <strong>ABS Consulting (2005)</strong> <sup>3</sup> em "Root Cause Analysis Handbook: A Guide to Effective Incident Investigation". 
            Esta abordagem sistemática permite identificar não apenas as causas imediatas, mas também as causas contribuintes e as causas raiz, garantindo 
            que as ações corretivas sejam direcionadas aos fatores fundamentais que permitiram a ocorrência do evento.
        </p>
        
        <p style="margin-bottom: 12px;">
            A construção da árvore de falhas seguiu a estrutura hierárquica proposta por <strong>Vesely et al. (1981)</strong> <sup>4</sup> em "Fault Tree Handbook", 
            onde o evento topo (acidente) é decomposto em eventos intermediários e eventos básicos, utilizando portas lógicas (AND, OR) para representar 
            as relações causais. Esta estrutura permite uma análise sistemática de todas as hipóteses causais, facilitando a validação ou descarte de 
            cada hipótese através de evidências coletadas durante a investigação.
        </p>
        
        <p style="margin-bottom: 12px;">
            A classificação das causas seguiu os critérios estabelecidos pela <strong>NBR 14280:2019</strong> <sup>1</sup>, que diferencia entre causas 
            imediatas, causas contribuintes e causas básicas. As causas básicas são aquelas que, se corrigidas, podem prevenir a recorrência do acidente, 
            enquanto as causas imediatas são os fatores que diretamente levaram à ocorrência do evento.
        </p>
        
        <p style="margin-bottom: 12px;">
            A coleta de evidências foi realizada seguindo os princípios de preservação e documentação estabelecidos por <strong>OSHA (Occupational Safety 
            and Health Administration)</strong> <sup>5</sup> em suas diretrizes para investigação de acidentes. Todas as evidências foram documentadas, 
            incluindo fotografias, depoimentos, documentos técnicos e registros operacionais, garantindo a rastreabilidade e a confiabilidade das 
            informações utilizadas na análise.
        </p>
        
        <p style="margin-bottom: 12px;">
            A validação das hipóteses causais foi realizada através da análise crítica das evidências coletadas, seguindo o método científico de 
            formulação e teste de hipóteses. Cada hipótese foi avaliada quanto à sua plausibilidade, consistência com as evidências e capacidade de 
            explicar a sequência de eventos que levou ao acidente, conforme metodologia descrita por <strong>Reason (1997)</strong> <sup>6</sup> em 
            "Managing the Risks of Organizational Accidents".
        </p>
    </div>
    
    <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid #ddd;">
        <div class="vibra-green" style="margin-bottom: 10px;">REFERÊNCIAS BIBLIOGRÁFICAS</div>
        <div style="font-size: 9pt; line-height: 1.8; text-align: left;">
            <p style="margin-bottom: 8px;">
                <sup>1</sup> ABNT - Associação Brasileira de Normas Técnicas. <strong>NBR 14280:2019</strong> - Cadastro de acidente do trabalho - 
                Procedimento e classificação. Rio de Janeiro: ABNT, 2019.
            </p>
            <p style="margin-bottom: 8px;">
                <sup>2</sup> ISO - International Organization for Standardization. <strong>ISO 31010:2019</strong> - Risk management - Risk assessment 
                techniques. Geneva: ISO, 2019.
            </p>
            <p style="margin-bottom: 8px;">
                <sup>3</sup> ABS Consulting. <strong>Root Cause Analysis Handbook: A Guide to Effective Incident Investigation</strong>. 3rd ed. 
                Knoxville: ABS Group, 2005.
            </p>
            <p style="margin-bottom: 8px;">
                <sup>4</sup> VESELY, W. E.; GOLDBERG, F. F.; ROBERTS, N. H.; HAASL, D. F. <strong>Fault Tree Handbook</strong>. Washington, DC: 
                U.S. Nuclear Regulatory Commission, 1981. (NUREG-0492)
            </p>
            <p style="margin-bottom: 8px;">
                <sup>5</sup> OSHA - Occupational Safety and Health Administration. <strong>Incident Investigation</strong>. In: OSHA 2254-09R 2015 - 
                Training Requirements in OSHA Standards and Training Guidelines. Washington, DC: U.S. Department of Labor, 2015.
            </p>
            <p style="margin-bottom: 8px;">
                <sup>6</sup> REASON, J. <strong>Managing the Risks of Organizational Accidents</strong>. Aldershot: Ashgate Publishing, 1997.
            </p>
        </div>
    </div>

    <div class="page-break"></div>

    <!-- PÁGINA 3: RESUMO GERENCIAL -->
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
            <td>
                {% set class_injury_val = accident.get('class_injury') %}
                {% set class_community_val = accident.get('class_community') %}
                {% set class_environment_val = accident.get('class_environment') %}
                {% set class_process_safety_val = accident.get('class_process_safety') %}
                {% set class_asset_damage_val = accident.get('class_asset_damage') %}
                {% set class_near_miss_val = accident.get('class_near_miss') %}
                {% set class_str = '' %}
                {% if class_injury_val == True or (class_injury_val is not none and (class_injury_val|string|lower) in ['true', '1', 'yes']) %}
                    {% set class_str = class_str + 'Com Lesão' %}
                {% endif %}
                {% if class_community_val == True or (class_community_val is not none and (class_community_val|string|lower) in ['true', '1', 'yes']) %}
                    {% if class_str %}{% set class_str = class_str + ', ' %}{% endif %}
                    {% set class_str = class_str + 'Impacto na Comunidade' %}
                {% endif %}
                {% if class_environment_val == True or (class_environment_val is not none and (class_environment_val|string|lower) in ['true', '1', 'yes']) %}
                    {% if class_str %}{% set class_str = class_str + ', ' %}{% endif %}
                    {% set class_str = class_str + 'Meio Ambiente' %}
                {% endif %}
                {% if class_process_safety_val == True or (class_process_safety_val is not none and (class_process_safety_val|string|lower) in ['true', '1', 'yes']) %}
                    {% if class_str %}{% set class_str = class_str + ', ' %}{% endif %}
                    {% set class_str = class_str + 'Segurança de Processo' %}
                {% endif %}
                {% if class_asset_damage_val == True or (class_asset_damage_val is not none and (class_asset_damage_val|string|lower) in ['true', '1', 'yes']) %}
                    {% if class_str %}{% set class_str = class_str + ', ' %}{% endif %}
                    {% set class_str = class_str + 'Dano ao Patrimônio' %}
                {% endif %}
                {% if class_near_miss_val == True or (class_near_miss_val is not none and (class_near_miss_val|string|lower) in ['true', '1', 'yes']) %}
                    {% if class_str %}{% set class_str = class_str + ', ' %}{% endif %}
                    {% set class_str = class_str + 'Quase-Acidente' %}
                {% endif %}
                {% if class_str %}
                    {{ class_str }}
                {% else %}
                    {{ accident.get('classification', 'N/A') }}
                {% endif %}
            </td>
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

    <!-- PÁGINA 4: INFORMAÇÕES DETALHADAS -->
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
                {% set class_injury_val = accident.get('class_injury') %}
                {% set class_community_val = accident.get('class_community') %}
                {% set class_environment_val = accident.get('class_environment') %}
                {% set class_process_safety_val = accident.get('class_process_safety') %}
                {% set class_asset_damage_val = accident.get('class_asset_damage') %}
                {% set class_near_miss_val = accident.get('class_near_miss') %}
                <span class="checkbox">{{ '☑' if (class_injury_val == True or (class_injury_val is not none and (class_injury_val|string|lower) in ['true', '1', 'yes'])) else '☐' }}</span> Acidente Com Lesão na Força de Trabalho<br>
                <span class="checkbox">{{ '☑' if (class_community_val == True or (class_community_val is not none and (class_community_val|string|lower) in ['true', '1', 'yes'])) else '☐' }}</span> Acidente Com Lesão na Comunidade<br>
                <span class="checkbox">{{ '☑' if (class_environment_val == True or (class_environment_val is not none and (class_environment_val|string|lower) in ['true', '1', 'yes'])) else '☐' }}</span> Impacto ao Meio Ambiente<br>
                <span class="checkbox">{{ '☑' if (class_process_safety_val == True or (class_process_safety_val is not none and (class_process_safety_val|string|lower) in ['true', '1', 'yes'])) else '☐' }}</span> Segurança de Processo<br>
                <span class="checkbox">{{ '☑' if (class_asset_damage_val == True or (class_asset_damage_val is not none and (class_asset_damage_val|string|lower) in ['true', '1', 'yes'])) else '☐' }}</span> Dano ao Patrimônio<br>
                <span class="checkbox">{{ '☑' if (class_near_miss_val == True or (class_near_miss_val is not none and (class_near_miss_val|string|lower) in ['true', '1', 'yes'])) else '☐' }}</span> Quase-Acidente
            </td>
            <td width="50%">
                <span class="label">Gravidade Real/Potencial</span>
                <span class="checkbox">{{ '☑' if accident.get('severity_level') == 'Very Low' or accident.get('severity_level') == 'Muito Baixa' else '☐' }}</span> Muito Baixa<br>
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

    <!-- 1.6 Cronologia de Eventos -->
    {% if timeline_events %}
    <div class="vibra-green" style="margin-top: 10px;">1.6. Cronologia de Eventos</div>
    {% for event in timeline_events %}
    <div class="timeline-item">
        <span class="timeline-time">{{ event.get('event_time', 'N/A') }}</span><br>
        <span class="value">{{ event.get('description', 'N/A') }}</span>
    </div>
    {% endfor %}
    {% endif %}

    <!-- 1.7 Cronologia de Ações da Comissão -->
    {% if commission_actions %}
    <div class="vibra-green" style="margin-top: 15px;">1.7. Cronologia de Ações da Comissão</div>
    <p style="margin-bottom: 10px; font-size: 9pt; color: #666;">Abaixo são apresentadas as ações executadas pela comissão durante a investigação.</p>
    {% for action in commission_actions %}
    <div class="timeline-item" style="border-left-color: #2196f3;">
        <span class="timeline-time" style="color: #2196f3;">{{ action.get('action_time', 'N/A') }}</span>
        {% if action.get('action_type') %}
        <span style="display: inline-block; background-color: #2196f3; color: white; padding: 2px 8px; border-radius: 3px; font-size: 8pt; margin-left: 8px; font-weight: bold;">{{ action.get('action_type') }}</span>
        {% endif %}
        {% if action.get('responsible_person') %}
        <span style="font-size: 9pt; color: #666; margin-left: 8px;"> Responsável: {{ action.get('responsible_person') }}</span>
        {% endif %}
        <br>
        <span class="value">{{ action.get('description', 'N/A') }}</span>
    </div>
    {% endfor %}
    {% endif %}

    <div class="page-break"></div>

    <!-- PÁGINA 5: ÁRVORE DE FALHAS -->
    <div class="section-title">5. ANÁLISE DAS CAUSAS (ÁRVORE DE FALHAS)</div>
    
    <p style="margin-bottom: 15px;">Abaixo a representação gráfica da Árvore de Falhas gerada durante a investigação.</p>
    
    <!-- Árvore renderizada em HTML/CSS (idêntica à visualização) -->
    {% if fault_tree_html %}
        {{ fault_tree_html|safe }}
    {% else %}
        <p style="color: #999; font-style: italic;">[Árvore de Falhas não disponível]</p>
    {% endif %}

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
    {% endif %}

    <!-- 5.2 Hipóteses Descritas e Justificadas -->
    {% if hypotheses %}
    <div class="section-title" style="margin-top: 30px;">5.2. Hipóteses Descritas e Justificadas</div>
    <p style="margin-bottom: 15px; font-size: 10pt;">Abaixo são descritas todas as hipóteses levantadas durante a investigação, com suas respectivas justificativas para descarte ou consideração.</p>
    
    {% for hyp in hypotheses %}
    <div style="margin-bottom: 20px; page-break-inside: avoid;">
        <div class="vibra-green" style="margin-top: 10px; margin-bottom: 8px;">
            {% if hyp.get('node_number') %}
                Hipótese {{ hyp.get('node_number') }}: {{ hyp.get('label', 'N/A') }}
            {% else %}
                Hipótese {{ loop.index }}: {{ hyp.get('label', 'N/A') }}
            {% endif %}
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
                    {% if hyp.get('justification_image_b64') %}
                        <div style="margin-top: 10px;">
                            <img src="{{ hyp.get('justification_image_b64') }}" style="max-width: 400px; max-height: 300px; border: 1px solid #ddd; page-break-inside: avoid;" alt="Imagem da justificativa">
                        </div>
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

    <!-- PÁGINA 6: COMISSÃO -->
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

    <!-- PÁGINA 7: EVIDÊNCIAS COMPLETAS -->
    {% if evidence_images and evidence_images|length > 3 %}
    <div class="page-break"></div>
    <div class="section-title">8. EVIDÊNCIAS COMPLETAS</div>
    <div class="evidence-grid">
        {% for img in evidence_images %}
            <img src="{{ img }}" class="evidence-img">
        {% endfor %}
    </div>
    {% endif %}

    <!-- PÁGINA 8: RECOMENDAÇÕES -->
    {% if recommendations %}
    <div class="page-break"></div>
    <div class="section-title">9. RECOMENDAÇÕES</div>
    <p style="margin-bottom: 15px; font-size: 10pt;">Abaixo são apresentadas as recomendações para prevenir ou corrigir as causas básicas e contribuintes identificadas na investigação.</p>
    
    {% if recommendations.get('basic_causes') %}
    <div class="vibra-green" style="margin-top: 15px; margin-bottom: 10px;">9.1. Recomendações para Causas Básicas</div>
    {% for rec in recommendations.get('basic_causes') %}
    <div style="margin-bottom: 20px; page-break-inside: avoid;">
        <div style="font-weight: bold; color: #666; margin-bottom: 5px; font-size: 11pt;">
            {{ loop.index }}. {{ rec.get('label', 'N/A') }}
        </div>
        {% if rec.get('nbr_code') %}
        <div style="margin-bottom: 8px; font-size: 9pt; color: #666;">
            <strong>Código NBR:</strong> {{ rec.get('nbr_code', 'N/A') }} - {{ rec.get('nbr_description', '') }}
        </div>
        {% endif %}
        <div style="padding: 10px; background-color: #f9f9f9; border-left: 4px solid #d3d3d3; margin-top: 5px;">
            {{ rec.get('recommendation', 'Nenhuma recomendação fornecida.') }}
        </div>
    </div>
    {% endfor %}
    {% endif %}
    
    {% if recommendations.get('contributing_causes') %}
    <div class="vibra-green" style="margin-top: 20px; margin-bottom: 10px;">9.2. Recomendações para Causas Contribuintes</div>
    {% for rec in recommendations.get('contributing_causes') %}
    <div style="margin-bottom: 20px; page-break-inside: avoid;">
        <div style="font-weight: bold; color: #666; margin-bottom: 5px; font-size: 11pt;">
            {{ loop.index }}. {{ rec.get('label', 'N/A') }}
        </div>
        {% if rec.get('nbr_code') %}
        <div style="margin-bottom: 8px; font-size: 9pt; color: #666;">
            <strong>Código NBR:</strong> {{ rec.get('nbr_code', 'N/A') }} - {{ rec.get('nbr_description', '') }}
        </div>
        {% endif %}
        <div style="padding: 10px; background-color: #f9f9f9; border-left: 4px solid #2196f3; margin-top: 5px;">
            {{ rec.get('recommendation', 'Nenhuma recomendação fornecida.') }}
        </div>
    </div>
    {% endfor %}
    {% endif %}
    
    {% if not recommendations.get('basic_causes') and not recommendations.get('contributing_causes') %}
    <p style="color: #999; font-style: italic;">Nenhuma recomendação registrada ainda.</p>
    {% endif %}
    {% endif %}
    </div>

</body>
</html>
"""


def convert_image_url_to_base64(image_url: str, image_cache: Optional[Dict[str, str]] = None) -> Optional[str]:
    """
    Converte URL de imagem para base64 (para embutir no PDF)
    Suporta URLs do Supabase Storage e outras URLs públicas
    Usa PIL para validar e processar imagens corretamente
    Tenta URL decodificada e original para resolver problemas de encoding
    """
    try:
        import requests
        from io import BytesIO
        from PIL import Image
        from urllib.parse import unquote
        
        # Se já for base64, retorna direto
        if image_url.startswith('data:image'):
            return image_url
        
        if not image_url or not isinstance(image_url, str):
            print(f"[CONVERT_IMAGE] URL inválida: {image_url}")
            return None
        
        # Remove espaços em branco no início/fim
        image_url = image_url.strip()
        
        # Verifica se a imagem está no cache primeiro
        if image_cache and image_url in image_cache:
            cached_image = image_cache[image_url]
            print(f"[CONVERT_IMAGE] ✓ Imagem encontrada no cache")
            return cached_image
        
        print(f"[CONVERT_IMAGE] URL original: {image_url}")
        
        # Para URLs do Supabase que já vêm com %20, vamos tentar DECODIFICAR
        # pois o servidor pode esperar os caracteres reais
        try:
            # Decodifica a URL (transforma %20 em espaço, etc.)
            decoded_url = unquote(image_url)
            print(f"[CONVERT_IMAGE] URL decodificada: {decoded_url}")
            
            # Se a URL decodificada for diferente, tenta primeiro a decodificada
            urls_to_try = [decoded_url, image_url] if decoded_url != image_url else [image_url]
        except Exception as e:
            print(f"[CONVERT_IMAGE] Erro ao decodificar URL: {str(e)}")
            urls_to_try = [image_url]
        
        # Tenta fazer download da imagem (tenta URLs decodificada e original)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        last_error = None
        for attempt, url_to_use in enumerate(urls_to_try, 1):
            try:
                print(f"[CONVERT_IMAGE] Tentativa {attempt}/{len(urls_to_try)}: Baixando de {url_to_use[:120]}...")
                response = requests.get(url_to_use, timeout=30, headers=headers, stream=True, verify=True)
            
                if response.status_code == 200:
                    img_bytes = response.content
                    
                    # Verifica se realmente é uma imagem
                    if len(img_bytes) == 0:
                        print(f"[CONVERT_IMAGE] Imagem vazia na tentativa {attempt}")
                        continue
                    
                    print(f"[CONVERT_IMAGE] ✓ Imagem baixada na tentativa {attempt}: {len(img_bytes)} bytes")
                    
                    # Tenta abrir com PIL para validar e converter se necessário
                    try:
                        img = Image.open(BytesIO(img_bytes))
                        print(f"[CONVERT_IMAGE] Imagem carregada: {img.format} {img.size} {img.mode}")
                        
                        # Converte para RGB se necessário (remove canal alpha)
                        if img.mode in ('RGBA', 'LA', 'P'):
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            if img.mode == 'P':
                                img = img.convert('RGBA')
                            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                            img = background
                            print(f"[CONVERT_IMAGE] Convertido para RGB")
                        elif img.mode != 'RGB':
                            img = img.convert('RGB')
                            print(f"[CONVERT_IMAGE] Convertido de {img.mode} para RGB")
                        
                        # Redimensiona se muito grande (otimização para PDF)
                        max_size = 1920
                        if img.width > max_size or img.height > max_size:
                            original_size = img.size
                            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                            print(f"[CONVERT_IMAGE] Imagem redimensionada de {original_size} para {img.size}")
                        
                        # Salva como JPEG com qualidade otimizada
                        output = BytesIO()
                        img.save(output, format='JPEG', quality=85, optimize=True)
                        img_bytes = output.getvalue()
                        print(f"[CONVERT_IMAGE] Imagem processada: {len(img_bytes)} bytes")
                        
                    except Exception as e:
                        print(f"[CONVERT_IMAGE] Erro ao processar com PIL: {str(e)}")
                        print(f"[CONVERT_IMAGE] Continuando com bytes originais")
                    
                    img_b64 = base64.b64encode(img_bytes).decode('utf-8')
                    result = f"data:image/jpeg;base64,{img_b64}"
                    print(f"[CONVERT_IMAGE] ✓ Conversão bem-sucedida: {len(result)} caracteres")
                    return result
                    
                else:
                    error_msg = f"Erro HTTP {response.status_code} na tentativa {attempt}"
                    print(f"[CONVERT_IMAGE] {error_msg}")
                    try:
                        error_body = response.text
                        print(f"[CONVERT_IMAGE] Response body: {error_body}")
                    except:
                        pass
                    last_error = error_msg
                    
            except requests.exceptions.Timeout:
                error_msg = f"Timeout na tentativa {attempt}"
                print(f"[CONVERT_IMAGE] {error_msg}")
                last_error = error_msg
            except requests.exceptions.RequestException as e:
                error_msg = f"Erro de requisição na tentativa {attempt}: {str(e)}"
                print(f"[CONVERT_IMAGE] {error_msg}")
                last_error = error_msg
        
        print(f"[CONVERT_IMAGE] ✗ Todas as tentativas falharam. Último erro: {last_error}")
        return None
        
    except Exception as e:
        print(f"[CONVERT_IMAGE] Erro inesperado ao converter imagem {image_url}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def render_fault_tree_html_for_pdf(tree_json: Dict[str, Any]) -> str:
    """
    Renderiza a árvore de falhas em HTML/CSS usando tabelas para compatibilidade com WeasyPrint.
    Otimizado para caber em A4 paisagem.
    """
    if not tree_json:
        return ""
    
    import html
    from datetime import date
    
    # Contadores para numeração automática
    hypothesis_counter = 0
    basic_cause_counter = 0
    contributing_cause_counter = 0
    
    def get_node_number(node_type: str, status: str, has_children: bool, is_basic_cause: bool = False, is_contributing_cause: bool = False) -> str:
        """Retorna o número do nó (H1, H2, CB1, CB2, CC1, CC2, etc.)"""
        nonlocal hypothesis_counter, basic_cause_counter, contributing_cause_counter
        
        if node_type == 'root':
            return ""
        
        if is_basic_cause:
            basic_cause_counter += 1
            return f"CB{basic_cause_counter}"
        elif is_contributing_cause:
            contributing_cause_counter += 1
            return f"CC{contributing_cause_counter}"
        elif node_type == 'hypothesis':
            hypothesis_counter += 1
            return f"H{hypothesis_counter}"
        elif node_type == 'fact' and has_children:
            hypothesis_counter += 1
            return f"H{hypothesis_counter}"
        elif status == 'validated' and has_children and node_type != 'root':
            hypothesis_counter += 1
            return f"H{hypothesis_counter}"
        elif status in ['pending', 'discarded'] and node_type != 'root':
            hypothesis_counter += 1
            return f"H{hypothesis_counter}"
        return ""
    
    def get_node_shape(node_type: str, status: str, has_children: bool, is_basic_cause: bool = False, is_contributing_cause: bool = False) -> Dict[str, str]:
        """Retorna a forma e cor do nó baseado no tipo e status"""
        if is_basic_cause:
            return {
                'shape': 'oval',
                'bg_color': '#c8e6c9',
                'border_color': '#4caf50',
                'text_color': '#000000'
            }
        elif is_contributing_cause:
            return {
                'shape': 'oval',
                'bg_color': '#bbdefb',
                'border_color': '#2196f3',
                'text_color': '#000000'
            }
        elif node_type == 'root':
            return {
                'shape': 'rounded-rect',
                'bg_color': '#ffcdd2',
                'border_color': '#f44336',
                'text_color': '#000000'
            }
        elif status == 'validated' and has_children:
            return {
                'shape': 'rounded-rect',
                'bg_color': '#fff9c4',
                'border_color': '#f9a825',
                'text_color': '#000000'
            }
        elif status == 'discarded':
            return {
                'shape': 'diamond',
                'bg_color': '#ffcdd2',
                'border_color': '#f44336',
                'text_color': '#000000'
            }
        else:
            return {
                'shape': 'diamond',
                'bg_color': '#e0e0e0',
                'border_color': '#757575',
                'text_color': '#000000'
            }
    
    def render_node(node: Dict[str, Any], level: int = 0) -> str:
        """Renderiza um nó usando tabelas para melhor compatibilidade"""
        status = node.get('status', 'pending')
        node_type = node.get('type', 'hypothesis')
        label = node.get('label', '')
        nbr_code = node.get('nbr_code')
        is_basic_cause = node.get('is_basic_cause', False)
        is_contributing_cause = node.get('is_contributing_cause', False)
        children = node.get('children', [])
        has_children = len(children) > 0
        
        node_number = get_node_number(node_type, status, has_children, is_basic_cause, is_contributing_cause)
        shape_config = get_node_shape(node_type, status, has_children, is_basic_cause, is_contributing_cause)
        
        # Trunca label se muito longo (max 50 caracteres)
        label_display = label[:50] + '...' if len(label) > 50 else label
        label_escaped = html.escape(label_display).replace('\n', '<br>')
        
        # Renderiza conteúdo do nó com tamanhos MUITO reduzidos para A4 paisagem
        if shape_config['shape'] == 'diamond':
            # Losango usando SVG - MUITO REDUZIDO
            node_content = f'''
            <div style="position: relative; width: 60px; height: 60px; margin: 0 auto;">
                <svg width="60" height="60" style="position: absolute; top: 0; left: 0;">
                    <polygon points="30,2 58,30 30,58 2,30" 
                             fill="{shape_config['bg_color']}" 
                             stroke="{shape_config['border_color']}" 
                             stroke-width="1"/>
                </svg>
                <div style="position: absolute; top: 50%; left: 50%; width: 50px; margin-left: -25px; margin-top: -12px; text-align: center; font-size: 5pt; line-height: 1.0; color: {shape_config['text_color']};">
                    {label_escaped}
                </div>
                {f'<div style="position: absolute; top: 50%; left: 50%; margin-left: -8px; margin-top: -8px; font-size: 16px; color: #d32f2f; font-weight: bold;">✕</div>' if status == 'discarded' else ''}
                {f'<div style="position: absolute; top: -2px; left: -2px; background-color: {shape_config["border_color"]}; color: white; width: 14px; height: 14px; border-radius: 50%; text-align: center; line-height: 14px; font-weight: bold; font-size: 6pt;">{node_number}</div>' if node_number else ''}
            </div>
            '''
        elif shape_config['shape'] == 'oval':
            # Oval - MUITO REDUZIDO
            node_content = f'''
            <div style="position: relative; width: 70px; min-height: 35px; margin: 0 auto; background-color: {shape_config['bg_color']}; border: 1px solid {shape_config['border_color']}; border-radius: 25px; padding: 4px 8px;">
                <div style="text-align: center; font-size: 5pt; line-height: 1.0; color: {shape_config['text_color']};">
                    {label_escaped}
                    {f'<div style="margin-top: 1px; font-size: 4.5pt; color: #1976d2; font-weight: 600;">NBR: {html.escape(str(nbr_code))}</div>' if nbr_code else ''}
                </div>
                {f'<div style="position: absolute; top: -2px; left: -2px; background-color: {shape_config["border_color"]}; color: white; width: 14px; height: 14px; border-radius: 50%; text-align: center; line-height: 14px; font-weight: bold; font-size: 6pt;">{node_number}</div>' if node_number else ''}
            </div>
            '''
        else:
            # Retângulo arredondado - MUITO REDUZIDO
            node_content = f'''
            <div style="position: relative; width: 80px; min-height: 35px; margin: 0 auto; background-color: {shape_config['bg_color']}; border: 1px solid {shape_config['border_color']}; border-radius: 5px; padding: 4px 8px;">
                <div style="text-align: center; font-size: 5pt; line-height: 1.0; color: {shape_config['text_color']};">
                    {label_escaped}
                    {f'<div style="margin-top: 1px; font-size: 4.5pt; color: #1976d2; font-weight: 600;">NBR: {html.escape(str(nbr_code))}</div>' if nbr_code else ''}
                </div>
                {f'<div style="position: absolute; top: -2px; left: -2px; background-color: {shape_config["border_color"]}; color: white; width: 14px; height: 14px; border-radius: 50%; text-align: center; line-height: 14px; font-weight: bold; font-size: 6pt;">{node_number}</div>' if node_number else ''}
            </div>
            '''
        
        # Se tem filhos, usa tabela para organizar
        if children:
            children_cells = []
            for child in children:
                children_cells.append(f'<td style="vertical-align: top; padding: 0 3px;">{render_node(child, level + 1)}</td>')
            
            children_row = f'<tr>{"".join(children_cells)}</tr>'
            
            # Linha vertical conectora - MUITO REDUZIDA
            connector_line = f'<div style="width: 1px; height: 8px; background-color: #2196f3; margin: 0 auto;"></div>'
            
            # Linha horizontal (se múltiplos filhos) - MUITO REDUZIDA
            horizontal_line = ''
            if len(children) > 1:
                horizontal_line = f'<div style="height: 1px; background-color: #2196f3; margin: 0 auto; width: 95%;"></div>'
            
            return f'''
            <table style="border-collapse: collapse; margin: 0 auto;">
                <tr>
                    <td colspan="{len(children)}" style="text-align: center; padding-bottom: 2px;">
                        {node_content}
                        {connector_line}
                        {horizontal_line}
                    </td>
                </tr>
                {children_row}
            </table>
            '''
        else:
            # Nó folha - sem filhos
            if level > 0:
                connector_line = f'<div style="width: 1px; height: 8px; background-color: #2196f3; margin: 0 auto; margin-bottom: 2px;"></div>'
                return f'{connector_line}{node_content}'
            return node_content
    
    # Renderiza a árvore completa
    tree_html = render_node(tree_json, level=0)
    
    # Legenda corrigida para A4 paisagem (igual ao sistema)
    legend_html = '''
    <div style="position: absolute; top: 5px; right: 5px; background: white; border: 1.5px solid #333; padding: 5px; border-radius: 3px; font-size: 5.5pt; width: 120px;">
        <div style="font-weight: bold; margin-bottom: 3px; border-bottom: 1px solid #ccc; padding-bottom: 2px; font-size: 6pt;">LEGENDA</div>
        <div style="margin-bottom: 2px;"><strong>H:</strong> Hipótese</div>
        <div style="margin-bottom: 2px;"><strong>CB:</strong> Causa Básica</div>
        <div style="margin-bottom: 2px;"><strong>CC:</strong> Causa Contribuinte</div>
        <div style="margin-top: 3px; margin-bottom: 2px;">
            <span style="display: inline-block; width: 10px; height: 10px; background: #ffcdd2; border: 1px solid #f44336; border-radius: 2px; vertical-align: middle;"></span>
            <span style="margin-left: 3px;">Evento Topo</span>
        </div>
        <div style="margin-bottom: 2px;">
            <svg width="10" height="10" style="display: inline-block; vertical-align: middle; margin-right: 3px;">
                <polygon points="5,1 9,5 5,9 1,5" fill="#e0e0e0" stroke="#757575" stroke-width="1"/>
            </svg>
            <span style="margin-left: 3px;">Hipótese</span>
        </div>
        <div style="margin-bottom: 2px;">
            <svg width="10" height="10" style="display: inline-block; vertical-align: middle; margin-right: 3px;">
                <polygon points="5,1 9,5 5,9 1,5" fill="#ffcdd2" stroke="#f44336" stroke-width="1"/>
                <text x="5" y="7" text-anchor="middle" font-size="8" fill="#d32f2f" font-weight="bold">✕</text>
            </svg>
            <span style="margin-left: 3px;">Descartada</span>
        </div>
        <div style="margin-bottom: 2px;">
            <span style="display: inline-block; width: 10px; height: 10px; background: #fff9c4; border: 1px solid #f9a825; border-radius: 2px; vertical-align: middle;"></span>
            <span style="margin-left: 3px;">Intermediária</span>
        </div>
        <div style="margin-bottom: 2px;">
            <span style="display: inline-block; width: 10px; height: 10px; background: #c8e6c9; border: 1px solid #4caf50; border-radius: 50%; vertical-align: middle;"></span>
            <span style="margin-left: 3px;">Causa Básica</span>
        </div>
        <div>
            <span style="display: inline-block; width: 10px; height: 10px; background: #bbdefb; border: 1px solid #2196f3; border-radius: 50%; vertical-align: middle;"></span>
            <span style="margin-left: 3px;">Causa Contribuinte</span>
        </div>
    </div>
    '''
    
    # HTML completo otimizado para A4 paisagem (árvore centralizada)
    return f'''
    <div class="fault-tree-landscape" style="position: relative; padding: 5px; padding-top: 6cm; background: white; min-height: 190mm; page-break-inside: avoid; border: 1px solid #e0e0e0;">
        {legend_html}
        <div style="overflow: hidden;">
            {tree_html}
        </div>
    </div>
    '''


def extract_hypotheses_from_tree(tree_json: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extrai todas as hipóteses da árvore de falhas recursivamente.
    Retorna lista de hipóteses com label, status, nbr_code, nbr_description.
    Inclui o número da hipótese (H1, H2, etc.) para corresponder à numeração da árvore.
    """
    if not tree_json:
        return []
    
    hypotheses = []
    
    # Contadores para numeração automática (mesma lógica da renderização da árvore)
    hypothesis_counter = 0
    basic_cause_counter = 0
    contributing_cause_counter = 0
    
    def get_node_number(node_type: str, status: str, has_children: bool, is_basic_cause: bool = False, is_contributing_cause: bool = False) -> str:
        """Retorna o número do nó (H1, H2, CB1, CB2, CC1, CC2, etc.) - mesma lógica da árvore"""
        nonlocal hypothesis_counter, basic_cause_counter, contributing_cause_counter
        
        if node_type == 'root':
            return ""
        
        if is_basic_cause:
            basic_cause_counter += 1
            return f"CB{basic_cause_counter}"
        elif is_contributing_cause:
            contributing_cause_counter += 1
            return f"CC{contributing_cause_counter}"
        elif node_type == 'hypothesis':
            hypothesis_counter += 1
            return f"H{hypothesis_counter}"
        elif node_type == 'fact' and has_children:
            hypothesis_counter += 1
            return f"H{hypothesis_counter}"
        elif status == 'validated' and has_children and node_type != 'root':
            hypothesis_counter += 1
            return f"H{hypothesis_counter}"
        elif status in ['pending', 'discarded'] and node_type != 'root':
            hypothesis_counter += 1
            return f"H{hypothesis_counter}"
        return ""
    
    def extract_recursive(node: Dict[str, Any]):
        """Função recursiva para extrair hipóteses"""
        nonlocal hypothesis_counter, basic_cause_counter, contributing_cause_counter
        
        node_type = node.get('type', '')
        status = node.get('status', 'pending')
        children = node.get('children', [])
        has_children = len(children) > 0
        is_basic_cause = node.get('is_basic_cause', False)
        is_contributing_cause = node.get('is_contributing_cause', False)
        
        # Considera como hipótese:
        # 1. Nós do tipo 'hypothesis'
        # 2. Nós com status 'pending', 'discarded' ou 'validated' que não sejam root
        # 3. Nós do tipo 'fact' com filhos (causas intermediárias)
        is_hypothesis = (
            node_type == 'hypothesis' or
            (node_type != 'root' and status in ['pending', 'discarded', 'validated']) or
            (node_type == 'fact' and has_children)
        )
        
        if is_hypothesis and node_type != 'root':
            justification = node.get('justification', '')
            
            # Calcula o número da hipótese (mesma lógica da árvore)
            # IMPORTANTE: Sempre calcula o número, mesmo que não vá adicionar à lista,
            # para manter a numeração correta na árvore
            node_number = get_node_number(node_type, status, has_children, is_basic_cause, is_contributing_cause)
            
            # Exclui hipóteses do tipo 'fact' sem justificativa (null ou vazio)
            if node_type == 'fact' and not justification:
                # Não adiciona à lista de hipóteses, mas o contador já foi incrementado acima
                pass
            else:
                hyp_data = {
                    'label': node.get('label', 'N/A'),
                    'status': status,
                    'nbr_code': node.get('nbr_code'),
                    'nbr_description': node.get('nbr_description', ''),
                    'justification': justification,  # Justificativa para confirmação/descarte
                    'justification_image_url': node.get('justification_image_url'),  # URL da imagem da justificativa
                    'node_number': node_number  # Número da hipótese (H1, H2, etc.) para corresponder à árvore
                }
                hypotheses.append(hyp_data)
        
        # Processa filhos recursivamente
        for child in node.get('children', []):
            extract_recursive(child)
    
    extract_recursive(tree_json)
    return hypotheses


def extract_recommendations_from_tree(tree_json: Optional[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extrai recomendações de causas básicas e contribuintes da árvore de falhas.
    Retorna dicionário com 'basic_causes' e 'contributing_causes'.
    """
    if not tree_json:
        return {'basic_causes': [], 'contributing_causes': []}
    
    basic_causes = []
    contributing_causes = []
    
    def extract_recursive(node: Dict[str, Any]):
        """Função recursiva para extrair recomendações"""
        is_basic = node.get('is_basic_cause', False)
        is_contributing = node.get('is_contributing_cause', False)
        status = node.get('status', 'pending')
        recommendation = node.get('recommendation')
        
        # Só inclui se for causa básica ou contribuinte validada e tiver recomendação
        if status == 'validated' and recommendation:
            rec_data = {
                'label': node.get('label', 'N/A'),
                'nbr_code': node.get('nbr_code'),
                'nbr_description': node.get('nbr_description', ''),
                'recommendation': recommendation
            }
            
            if is_basic:
                basic_causes.append(rec_data)
            elif is_contributing:
                contributing_causes.append(rec_data)
        
        # Processa filhos recursivamente
        for child in node.get('children', []):
            extract_recursive(child)
    
    extract_recursive(tree_json)
    return {
        'basic_causes': basic_causes,
        'contributing_causes': contributing_causes
    }


def generate_pdf_report(
    accident_data: Dict[str, Any],
    people_data: List[Dict[str, Any]],
    timeline_events: List[Dict[str, Any]],
    verified_causes: List[Dict[str, Any]],
    evidence_images: List[str],
    fault_tree_json: Optional[Dict[str, Any]] = None,
    commission_actions: Optional[List[Dict[str, Any]]] = None,
    image_cache: Optional[Dict[str, str]] = None
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
        commission_actions: Lista de ações executadas pela comissão (opcional)
        image_cache: Dicionário com cache de imagens pré-carregadas (opcional)
    
    Returns:
        bytes: PDF gerado
    """
    try:
        print(f"[PDF_GENERATION] Iniciando geração do PDF")
        print(f"[PDF_GENERATION] Total de imagens de evidência recebidas: {len(evidence_images)}")
        
        # Gera HTML da árvore se JSON fornecido (idêntica à visualização)
        fault_tree_html = None
        if fault_tree_json:
            fault_tree_html = render_fault_tree_html_for_pdf(fault_tree_json)
        
        # Extrai hipóteses da árvore
        hypotheses = extract_hypotheses_from_tree(fault_tree_json)
        print(f"[PDF_GENERATION] Total de hipóteses extraídas: {len(hypotheses)}")
        
        # Converte imagens de justificativa para base64
        for i, hyp in enumerate(hypotheses):
            justification_image_url = hyp.get('justification_image_url')
            if justification_image_url and isinstance(justification_image_url, str) and justification_image_url.strip():
                try:
                    print(f"[PDF_GENERATION] [{i+1}/{len(hypotheses)}] Processando imagem de justificativa: {justification_image_url[:100]}...")
                    img_b64 = convert_image_url_to_base64(justification_image_url.strip(), image_cache)
                    if img_b64:
                        hyp['justification_image_b64'] = img_b64
                        print(f"[PDF_GENERATION] ✓ Imagem {i+1} convertida com sucesso")
                    else:
                        hyp['justification_image_b64'] = None
                        print(f"[PDF_GENERATION] ✗ Falha ao converter imagem {i+1}")
                except Exception as e:
                    hyp['justification_image_b64'] = None
                    print(f"[PDF_GENERATION] ✗ Exceção ao processar imagem {i+1}: {str(e)}")
            else:
                hyp['justification_image_b64'] = None
        
        # Extrai recomendações de causas básicas e contribuintes
        recommendations = extract_recommendations_from_tree(fault_tree_json)
        
        # Filtra pessoas por tipo
        commission = [p for p in people_data if p.get('person_type') == 'Commission_Member']
        drivers = [p for p in people_data if p.get('person_type') == 'Driver']
        injured = [p for p in people_data if p.get('person_type') == 'Injured']
        witnesses = [p for p in people_data if p.get('person_type') == 'Witness']
        
        # Prepara data atual
        current_date = datetime.now().strftime('%d/%m/%Y')
        
        # Converte URLs de evidências para base64 (para embutir no PDF)
        print(f"[PDF_GENERATION] Convertendo imagens de evidência...")
        evidence_images_b64 = []
        for i, img_url in enumerate(evidence_images):
            if img_url:
                print(f"[PDF_GENERATION] [{i+1}/{len(evidence_images)}] Convertendo: {img_url[:100]}...")
                img_b64 = convert_image_url_to_base64(img_url, image_cache)
                if img_b64:
                    evidence_images_b64.append(img_b64)
                    print(f"[PDF_GENERATION] ✓ Evidência {i+1} convertida")
                else:
                    print(f"[PDF_GENERATION] ✗ Falha ao converter evidência {i+1}")
        
        print(f"[PDF_GENERATION] Total de imagens convertidas: {len(evidence_images_b64)}/{len(evidence_images)}")
        
        # Prepara ações da comissão (ordena por data/hora)
        commission_actions_sorted = []
        if commission_actions:
            commission_actions_sorted = sorted(commission_actions, key=lambda x: x.get('action_time', ''))
        
        # Renderiza HTML
        print(f"[PDF_GENERATION] Renderizando template HTML...")
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
            fault_tree_html=fault_tree_html,
            evidence_images=evidence_images_b64,
            commission=commission,
            current_date=current_date,
            recommendations=recommendations,
            commission_actions=commission_actions_sorted
        )
        
        print(f"[PDF_GENERATION] Gerando PDF com WeasyPrint...")
        # Gera PDF
        pdf_bytes = HTML(string=rendered_html).write_pdf(
            stylesheets=[CSS(string=CSS_STYLES)]
        )
        
        if pdf_bytes:
            print(f"[PDF_GENERATION] ✓ PDF gerado com sucesso: {len(pdf_bytes)} bytes")
            return pdf_bytes
        else:
            raise Exception("Falha ao gerar PDF: retorno vazio do WeasyPrint")
        
    except Exception as e:
        print(f"[PDF_GENERATION] ✗ Erro ao gerar PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        raise Exception(f"Erro ao gerar PDF: {str(e)}")

