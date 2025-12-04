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
                    {% if hyp.get('justification_image_b64') %}
                        <div style="margin-top: 10px;">
                            <img src="data:image/jpeg;base64,{{ hyp.get('justification_image_b64') }}" style="max-width: 400px; max-height: 300px; border: 1px solid #ddd; page-break-inside: avoid;" alt="Imagem da justificativa">
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

    <!-- PÁGINA 7: RECOMENDAÇÕES -->
    {% if recommendations %}
    <div class="page-break"></div>
    <div class="section-title">9. RECOMENDAÇÕES</div>
    <p style="margin-bottom: 15px; font-size: 10pt;">Abaixo são apresentadas as recomendações para prevenir ou corrigir as causas básicas e contribuintes identificadas na investigação.</p>
    
    {% if recommendations.get('basic_causes') %}
    <div class="vibra-green" style="margin-top: 15px; margin-bottom: 10px;">9.1. Recomendações para Causas Básicas</div>
    {% for rec in recommendations.get('basic_causes') %}
    <div style="margin-bottom: 20px; page-break-inside: avoid;">
        <div style="font-weight: bold; color: #005f2f; margin-bottom: 5px; font-size: 11pt;">
            {{ loop.index }}. {{ rec.get('label', 'N/A') }}
        </div>
        {% if rec.get('nbr_code') %}
        <div style="margin-bottom: 8px; font-size: 9pt; color: #666;">
            <strong>Código NBR:</strong> {{ rec.get('nbr_code', 'N/A') }} - {{ rec.get('nbr_description', '') }}
        </div>
        {% endif %}
        <div style="padding: 10px; background-color: #f9f9f9; border-left: 4px solid #005f2f; margin-top: 5px;">
            {{ rec.get('recommendation', 'Nenhuma recomendação fornecida.') }}
        </div>
    </div>
    {% endfor %}
    {% endif %}
    
    {% if recommendations.get('contributing_causes') %}
    <div class="vibra-green" style="margin-top: 20px; margin-bottom: 10px;">9.2. Recomendações para Causas Contribuintes</div>
    {% for rec in recommendations.get('contributing_causes') %}
    <div style="margin-bottom: 20px; page-break-inside: avoid;">
        <div style="font-weight: bold; color: #005f2f; margin-bottom: 5px; font-size: 11pt;">
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


def render_fault_tree_html_for_pdf(tree_json: Dict[str, Any]) -> str:
    """
    Renderiza a árvore de falhas em HTML/CSS idêntica à visualização da interface.
    Esta função é uma cópia da render_fault_tree_html de pages/investigation.py
    adaptada para uso no PDF.
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
        
        # Root NUNCA tem numeração
        if node_type == 'root':
            return ""
        
        # Causa básica: marcada manualmente pelo usuário (is_basic_cause = True)
        if is_basic_cause:
            basic_cause_counter += 1
            return f"CB{basic_cause_counter}"
        # Causa contribuinte: marcada manualmente pelo usuário (is_contributing_cause = True)
        elif is_contributing_cause:
            contributing_cause_counter += 1
            return f"CC{contributing_cause_counter}"
        # Hipótese: qualquer hypothesis (pendente ou descartada)
        elif node_type == 'hypothesis':
            hypothesis_counter += 1
            return f"H{hypothesis_counter}"
        # Fact com filhos: trata como hipótese
        elif node_type == 'fact' and has_children:
            hypothesis_counter += 1
            return f"H{hypothesis_counter}"
        # Causa intermediária validada (não root): também pode ter numeração H
        elif status == 'validated' and has_children and node_type != 'root':
            hypothesis_counter += 1
            return f"H{hypothesis_counter}"
        # Status pending ou discarded (mas não root)
        elif status in ['pending', 'discarded'] and node_type != 'root':
            hypothesis_counter += 1
            return f"H{hypothesis_counter}"
        # Sem numeração
        return ""
    
    def get_node_shape(node_type: str, status: str, has_children: bool, is_basic_cause: bool = False, is_contributing_cause: bool = False) -> Dict[str, str]:
        """Retorna a forma e cor do nó baseado no tipo e status"""
        # Causa básica: marcada manualmente pelo usuário (is_basic_cause = True) - Oval verde
        if is_basic_cause:
            return {
                'shape': 'oval',
                'bg_color': '#c8e6c9',
                'border_color': '#4caf50',
                'text_color': '#000000',
                'border_radius': '50px'
            }
        # Causa contribuinte: marcada manualmente pelo usuário (is_contributing_cause = True) - Oval azul
        elif is_contributing_cause:
            return {
                'shape': 'oval',
                'bg_color': '#bbdefb',  # Azul claro
                'border_color': '#2196f3',
                'text_color': '#000000',
                'border_radius': '50px'
            }
        # Root ou causa intermediária validada: Retângulo arredondado amarelo
        elif node_type == 'root' or (status == 'validated' and has_children):
            return {
                'shape': 'rounded-rect',
                'bg_color': '#fff9c4',
                'border_color': '#f9a825',
                'text_color': '#000000',
                'border_radius': '10px'
            }
        # Hipótese descartada: Losango vermelho com X
        elif status == 'discarded':
            return {
                'shape': 'diamond',
                'bg_color': '#ffcdd2',
                'border_color': '#f44336',
                'text_color': '#000000',
                'border_radius': '0px'
            }
        # Hipótese pendente: Losango
        else:
            return {
                'shape': 'diamond',
                'bg_color': '#e0e0e0',
                'border_color': '#757575',
                'text_color': '#000000',
                'border_radius': '0px'
            }
    
    def render_node(node: Dict[str, Any], level: int = 0) -> str:
        """Renderiza um nó recursivamente no formato FTA"""
        status = node.get('status', 'pending')
        node_type = node.get('type', 'hypothesis')
        label = node.get('label', '')
        nbr_code = node.get('nbr_code')
        is_basic_cause = node.get('is_basic_cause', False)  # Campo para marcar manualmente como causa básica
        is_contributing_cause = node.get('is_contributing_cause', False)  # Campo para marcar manualmente como causa contribuinte
        children = node.get('children', [])
        has_children = len(children) > 0
        
        # Obtém número do nó
        node_number = get_node_number(node_type, status, has_children, is_basic_cause, is_contributing_cause)
        
        # Obtém forma e cores
        shape_config = get_node_shape(node_type, status, has_children, is_basic_cause, is_contributing_cause)
        
        # Escapa HTML
        label_escaped = html.escape(label).replace('\n', '<br>')
        
        # Determina forma CSS
        if shape_config['shape'] == 'diamond':
            shape_style = "width: 200px; height: 200px; position: relative;"
            inner_style = f"position: absolute; top: 0; left: 0; width: 100%; height: 100%; clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%); background-color: {shape_config['bg_color']}; border: 2px solid {shape_config['border_color']}; box-shadow: 0 2px 6px rgba(0,0,0,0.15);"
            content_container = "position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 60%; text-align: center; z-index: 2;"
        elif shape_config['shape'] == 'oval':
            shape_style = "border-radius: 50%; width: 200px; min-height: 80px; display: flex; align-items: center; justify-content: center; padding: 15px 20px; position: relative;"
            inner_style = ""
            content_container = "z-index: 2; position: relative;"
        else:
            shape_style = f"border-radius: {shape_config['border_radius']}; width: 240px; min-height: 80px; display: flex; align-items: center; justify-content: center; padding: 15px 20px; position: relative;"
            inner_style = ""
            content_container = "z-index: 2; position: relative;"
        
        # Estilo base do nó
        if shape_config['shape'] == 'diamond':
            node_style = f"{shape_style}"
            node_bg_border = inner_style
        else:
            node_style = f"{shape_style} background-color: {shape_config['bg_color']}; border: 2px solid {shape_config['border_color']}; box-shadow: 0 2px 6px rgba(0,0,0,0.15);"
            node_bg_border = ""
        
        # Número do nó
        number_html = ""
        if node_number:
            number_html = f'<div style="position: absolute; top: -12px; left: -12px; background-color: {shape_config["border_color"]}; color: white; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.75em; box-shadow: 0 2px 4px rgba(0,0,0,0.3); z-index: 10;">{node_number}</div>'
        
        # X para descartado
        discard_x = ""
        if status == 'discarded':
            discard_x = '<div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 3em; color: #d32f2f; font-weight: bold; pointer-events: none; z-index: 5; text-shadow: 1px 1px 3px rgba(255,255,255,0.9);">✕</div>'
        
        # Código NBR
        nbr_html = ""
        if nbr_code:
            nbr_code_escaped = html.escape(str(nbr_code))
            nbr_html = f'<div style="margin-top: 6px; font-size: 0.7em; color: #1976d2; font-weight: 600;">NBR: {nbr_code_escaped}</div>'
        
        # Container do conteúdo
        content_html = f'<div style="{content_container}"><div style="color: {shape_config["text_color"]}; font-weight: 500; font-size: 0.85em; line-height: 1.3; word-wrap: break-word;">{label_escaped}{nbr_html}</div></div>'
        
        # Monta o nó completo
        if shape_config['shape'] == 'diamond':
            node_html_inner = f'<div style="{node_style} margin: 10px;">{number_html}<div style="{node_bg_border}"></div>{discard_x}{content_html}</div>'
        else:
            node_html_inner = f'<div style="{node_style} margin: 10px;">{number_html}{discard_x}{content_html}</div>'
        
        # Renderiza filhos
        children_html = ""
        if children:
            children_items = [render_node(child, level + 1) for child in children]
            children_html = "".join(children_items)
            children_html = f'<div style="position: relative; margin-top: 20px;"><div style="position: absolute; left: 50%; top: 0; width: 2px; height: 20px; background-color: #2196f3; transform: translateX(-50%);"></div><div style="position: absolute; left: 0; right: 0; top: 20px; height: 2px; background-color: #2196f3;"></div><div style="display: flex; flex-wrap: wrap; justify-content: center; align-items: flex-start; gap: 20px; padding-top: 40px;">{children_html}</div></div>'
        
        # Linha conectora ao pai
        connector = ""
        if level > 0:
            connector = '<div style="position: absolute; left: 50%; top: -20px; width: 2px; height: 20px; background-color: #2196f3; transform: translateX(-50%);"></div>'
        
        # HTML completo do nó
        return f'<div style="position: relative; display: inline-flex; flex-direction: column; align-items: center;">{connector}{node_html_inner}{children_html}</div>'
    
    # Renderiza a árvore completa
    tree_html = render_node(tree_json, level=0)
    
    # Legenda
    legend_html = '<div style="position: absolute; top: 10px; right: 10px; background: white; border: 2px solid #333; padding: 12px; border-radius: 6px; font-size: 0.8em; z-index: 1000; box-shadow: 0 2px 8px rgba(0,0,0,0.2); max-width: 220px;"><div style="font-weight: bold; margin-bottom: 10px; border-bottom: 1px solid #ccc; padding-bottom: 6px;">LEGENDA</div><div style="margin-bottom: 6px;"><strong>H:</strong> Hipótese</div><div style="margin-bottom: 6px;"><strong>CB:</strong> Causa Básica</div><div style="margin-bottom: 6px; display: flex; align-items: center; gap: 8px;"><div style="width: 18px; height: 18px; clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%); background: #e0e0e0; border: 2px solid #757575;"></div><span>Hipótese</span></div><div style="margin-bottom: 6px; display: flex; align-items: center; gap: 8px;"><div style="width: 18px; height: 18px; clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%); background: #ffcdd2; border: 2px solid #f44336; position: relative;"><span style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #d32f2f; font-size: 12px;">✕</span></div><span>Descartada</span></div><div style="margin-bottom: 6px; display: flex; align-items: center; gap: 8px;"><div style="width: 18px; height: 18px; background: #fff9c4; border: 2px solid #f9a825; border-radius: 4px;"></div><span>Intermediária</span></div><div style="display: flex; align-items: center; gap: 8px;"><div style="width: 18px; height: 18px; background: #c8e6c9; border: 2px solid #4caf50; border-radius: 50%;"></div><span>Causa Básica</span></div></div>'
    
    # HTML completo
    return f'<div style="position: relative; font-family: Arial, sans-serif; padding: 30px 20px; background: white; min-height: 400px; page-break-inside: avoid; border: 1px solid #e0e0e0; border-radius: 8px;"><div style="text-align: center; margin-bottom: 30px;"><h2 style="margin: 0; color: #333; font-size: 1.5em; font-weight: bold;">ÁRVORE DE FALHAS (FTA)</h2><div style="color: #666; font-size: 0.9em; margin-top: 5px;">{date.today().strftime("%d/%m/%Y")}</div></div>{legend_html}<div style="display: flex; justify-content: center; align-items: flex-start; min-height: 300px; padding: 20px 0;">{tree_html}</div></div>'


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
                'justification': node.get('justification', ''),  # Justificativa para confirmação/descarte
                'justification_image_url': node.get('justification_image_url')  # URL da imagem da justificativa
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
        # Gera HTML da árvore se JSON fornecido (idêntica à visualização)
        fault_tree_html = None
        if fault_tree_json:
            fault_tree_html = render_fault_tree_html_for_pdf(fault_tree_json)
        
        # Extrai hipóteses da árvore
        hypotheses = extract_hypotheses_from_tree(fault_tree_json)
        
        # Converte imagens de justificativa para base64
        for hyp in hypotheses:
            if hyp.get('justification_image_url'):
                img_b64 = convert_image_url_to_base64(hyp.get('justification_image_url'))
                if img_b64:
                    hyp['justification_image_b64'] = img_b64
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
            fault_tree_html=fault_tree_html,
            evidence_images=evidence_images_b64,
            commission=commission,
            current_date=current_date,
            recommendations=recommendations
        )
        
        # Gera PDF
        pdf_bytes = HTML(string=rendered_html).write_pdf(
            stylesheets=[CSS(string=CSS_STYLES)]
        )
        
        return pdf_bytes
        
    except Exception as e:
        raise Exception(f"Erro ao gerar PDF: {str(e)}")

