"""
Gerador de Relatório Word (DOCX) no Padrão Vibra
Usa python-docx para criar documento editável
"""
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from datetime import datetime
from typing import Dict, Any, List, Optional
import io

def generate_word_report(
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
    Gera relatório em formato Word (.docx) com os mesmos dados do PDF.
    
    Args:
        accident_data: Dados da tabela 'accidents'
        people_data: Lista da tabela 'involved_people'
        timeline_events: Lista de eventos da timeline
        verified_causes: Lista de nós validados com códigos NBR
        evidence_images: Lista de URLs ou base64 das imagens de evidência
        fault_tree_json: JSON da árvore de falhas (opcional)
        commission_actions: Lista de ações executadas pela comissão (opcional)
        image_cache: Dicionário com cache de imagens pré-carregadas (opcional)
    
    Returns:
        bytes: Documento Word gerado
    """
    try:
        print(f"[WORD_GENERATION] Iniciando geração do Word")
        
        # Cria documento
        doc = Document()
        
        # Configuração de estilo padrão
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Arial'
        font.size = Pt(10)
        
        # ========== CAPA ==========
        title = doc.add_heading('RELATÓRIO FINAL', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        subtitle = doc.add_heading('Investigação de Acidente', level=1)
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Espaço
        doc.add_paragraph()
        
        # Informações do acidente
        event_title = accident_data.get('title') or accident_data.get('description', 'N/A')
        doc.add_paragraph(f"Evento: {event_title}")
        
        if accident_data.get('site_name'):
            doc.add_paragraph(f"Base: {accident_data.get('site_name', 'N/A')}")
        
        doc.add_paragraph(f"Local da Base: {accident_data.get('base_location', 'N/A')}")
        
        occurrence_date = accident_data.get('occurrence_date') or accident_data.get('occurred_at', 'N/A')
        doc.add_paragraph(f"Data de Ocorrência: {occurrence_date}")
        
        if accident_data.get('created_at'):
            doc.add_paragraph(f"Comissão Constituída em: {accident_data.get('created_at', 'N/A')}")
        
        # Quebra de página
        doc.add_page_break()
        
        # ========== METODOLOGIA ==========
        doc.add_heading('2. METODOLOGIA DE INVESTIGAÇÃO', level=1)
        
        methodology_text = [
            "A investigação deste acidente foi conduzida utilizando a metodologia de Análise de Árvore de Falhas (FTA - Fault Tree Analysis), uma técnica sistemática e estruturada para identificar e analisar as causas raiz de eventos indesejados. Esta metodologia permite uma representação gráfica hierárquica das relações causais, facilitando a compreensão dos fatores que contribuíram para a ocorrência do acidente.",
            "A FTA é amplamente reconhecida na indústria como uma ferramenta eficaz para investigação de acidentes, conforme estabelecido pela NBR 14280:2019 - Cadastro de acidente do trabalho - Procedimento e classificação¹, que estabelece os critérios para classificação e registro de acidentes do trabalho no Brasil. A norma define parâmetros para classificação de acidentes com e sem afastamento, além de estabelecer critérios para cálculo de indicadores de segurança.",
            "A metodologia segue os princípios estabelecidos pela ISO 31010:2019 - Risk management - Risk assessment techniques², que apresenta a Análise de Árvore de Falhas como uma técnica recomendada para análise de riscos e investigação de eventos. A norma internacional destaca a capacidade da FTA em identificar combinações de falhas que podem levar a eventos indesejados, permitindo uma análise probabilística e qualitativa dos fatores contribuintes.",
            "Durante a investigação, foram aplicados os princípios da Análise de Causa Raiz (RCA - Root Cause Analysis), conforme metodologia descrita por ABS Consulting (2005)³ em \"Root Cause Analysis Handbook: A Guide to Effective Incident Investigation\". Esta abordagem sistemática permite identificar não apenas as causas imediatas, mas também as causas contribuintes e as causas raiz, garantindo que as ações corretivas sejam direcionadas aos fatores fundamentais que permitiram a ocorrência do evento.",
            "A construção da árvore de falhas seguiu a estrutura hierárquica proposta por Vesely et al. (1981)⁴ em \"Fault Tree Handbook\", onde o evento topo (acidente) é decomposto em eventos intermediários e eventos básicos, utilizando portas lógicas (AND, OR) para representar as relações causais. Esta estrutura permite uma análise sistemática de todas as hipóteses causais, facilitando a validação ou descarte de cada hipótese através de evidências coletadas durante a investigação.",
            "A classificação das causas seguiu os critérios estabelecidos pela NBR 14280:2019¹, que diferencia entre causas imediatas, causas contribuintes e causas básicas. As causas básicas são aquelas que, se corrigidas, podem prevenir a recorrência do acidente, enquanto as causas imediatas são os fatores que diretamente levaram à ocorrência do evento.",
            "A coleta de evidências foi realizada seguindo os princípios de preservação e documentação estabelecidos por OSHA (Occupational Safety and Health Administration)⁵ em suas diretrizes para investigação de acidentes. Todas as evidências foram documentadas, incluindo fotografias, depoimentos, documentos técnicos e registros operacionais, garantindo a rastreabilidade e a confiabilidade das informações utilizadas na análise.",
            "A validação das hipóteses causais foi realizada através da análise crítica das evidências coletadas, seguindo o método científico de formulação e teste de hipóteses. Cada hipótese foi avaliada quanto à sua plausibilidade, consistência com as evidências e capacidade de explicar a sequência de eventos que levou ao acidente, conforme metodologia descrita por Reason (1997)⁶ em \"Managing the Risks of Organizational Accidents\"."
        ]
        
        for text in methodology_text:
            p = doc.add_paragraph(text)
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        
        # Referências bibliográficas
        doc.add_paragraph()
        doc.add_heading('REFERÊNCIAS BIBLIOGRÁFICAS', level=2)
        
        references = [
            "¹ ABNT - Associação Brasileira de Normas Técnicas. NBR 14280:2019 - Cadastro de acidente do trabalho - Procedimento e classificação. Rio de Janeiro: ABNT, 2019.",
            "² ISO - International Organization for Standardization. ISO 31010:2019 - Risk management - Risk assessment techniques. Geneva: ISO, 2019.",
            "³ ABS Consulting. Root Cause Analysis Handbook: A Guide to Effective Incident Investigation. 3rd ed. Knoxville: ABS Group, 2005.",
            "⁴ VESELY, W. E.; GOLDBERG, F. F.; ROBERTS, N. H.; HAASL, D. F. Fault Tree Handbook. Washington, DC: U.S. Nuclear Regulatory Commission, 1981. (NUREG-0492)",
            "⁵ OSHA - Occupational Safety and Health Administration. Incident Investigation. In: OSHA 2254-09R 2015 - Training Requirements in OSHA Standards and Training Guidelines. Washington, DC: U.S. Department of Labor, 2015.",
            "⁶ REASON, J. Managing the Risks of Organizational Accidents. Aldershot: Ashgate Publishing, 1997."
        ]
        
        for ref in references:
            p = doc.add_paragraph(ref, style='List Bullet')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_page_break()
        
        # ========== RESUMO GERENCIAL ==========
        doc.add_heading('RESUMO GERENCIAL DO RELATÓRIO FINAL', level=1)
        
        # Tabela de resumo
        table = doc.add_table(rows=1, cols=2)
        table.style = 'Light Grid Accent 1'
        
        # Cabeçalho
        header_cells = table.rows[0].cells
        header_cells[0].text = 'Campo'
        header_cells[1].text = 'Valor'
        
        # Dados
        summary_data = [
            ('Data/Hora', occurrence_date),
            ('Base', accident_data.get('site_name', 'N/A')),
            ('Local da Base', accident_data.get('base_location', 'N/A')),
            ('Descrição Resumida', accident_data.get('description', accident_data.get('title', 'N/A'))),
            ('Tipo', accident_data.get('type', 'N/A')),
        ]
        
        # Classificação
        class_parts = []
        if accident_data.get('class_injury'):
            class_parts.append('Com Lesão')
        if accident_data.get('class_community'):
            class_parts.append('Impacto na Comunidade')
        if accident_data.get('class_environment'):
            class_parts.append('Meio Ambiente')
        if accident_data.get('class_process_safety'):
            class_parts.append('Segurança de Processo')
        if accident_data.get('class_asset_damage'):
            class_parts.append('Dano ao Patrimônio')
        if accident_data.get('class_near_miss'):
            class_parts.append('Quase-Acidente')
        
        classification = ', '.join(class_parts) if class_parts else accident_data.get('classification', 'N/A')
        summary_data.append(('Classificação', classification))
        
        for label, value in summary_data:
            row = table.add_row()
            row.cells[0].text = label
            row.cells[1].text = str(value)
        
        doc.add_page_break()
        
        # ========== INFORMAÇÕES DETALHADAS ==========
        doc.add_heading('3. INFORMAÇÕES DETALHADAS DO ACIDENTE', level=1)
        
        # Dados gerais
        doc.add_heading('3.1. Dados Gerais', level=2)
        
        general_table = doc.add_table(rows=1, cols=2)
        general_table.style = 'Light Grid Accent 1'
        
        general_data = [
            ('Número do Registro', accident_data.get('registry_number', 'N/A')),
            ('Local', accident_data.get('base_location', 'N/A')),
            ('Data/Hora', occurrence_date),
            ('Status', accident_data.get('status', 'N/A')),
        ]
        
        for label, value in general_data:
            row = general_table.add_row()
            row.cells[0].text = label
            row.cells[1].text = str(value)
        
        # Pessoas envolvidas
        drivers = [p for p in people_data if p.get('person_type') == 'Driver']
        injured = [p for p in people_data if p.get('person_type') == 'Injured']
        witnesses = [p for p in people_data if p.get('person_type') == 'Witness']
        
        if drivers or injured or witnesses:
            doc.add_heading('3.2. Pessoas Envolvidas', level=2)
            
            if injured:
                doc.add_heading('Vítimas', level=3)
                injured_table = doc.add_table(rows=1, cols=5)
                injured_table.style = 'Light Grid Accent 1'
                header = injured_table.rows[0].cells
                header[0].text = 'Nome'
                header[1].text = 'Idade'
                header[2].text = 'Cargo'
                header[3].text = 'Empresa'
                header[4].text = 'Tipo de Lesão'
                
                for person in injured:
                    row = injured_table.add_row()
                    row.cells[0].text = person.get('name', 'N/A')
                    row.cells[1].text = str(person.get('age', 'N/A')) if person.get('age') else 'N/A'
                    row.cells[2].text = person.get('job_title', 'N/A')
                    row.cells[3].text = person.get('company', 'N/A')
                    row.cells[4].text = person.get('injury_type', 'N/A')
            
            if drivers:
                doc.add_heading('Condutores', level=3)
                drivers_table = doc.add_table(rows=1, cols=4)
                drivers_table.style = 'Light Grid Accent 1'
                header = drivers_table.rows[0].cells
                header[0].text = 'Nome'
                header[1].text = 'Idade'
                header[2].text = 'Cargo'
                header[3].text = 'Empresa'
                
                for person in drivers:
                    row = drivers_table.add_row()
                    row.cells[0].text = person.get('name', 'N/A')
                    row.cells[1].text = str(person.get('age', 'N/A')) if person.get('age') else 'N/A'
                    row.cells[2].text = person.get('job_title', 'N/A')
                    row.cells[3].text = person.get('company', 'N/A')
            
            if witnesses:
                doc.add_heading('Testemunhas', level=3)
                witnesses_table = doc.add_table(rows=1, cols=4)
                witnesses_table.style = 'Light Grid Accent 1'
                header = witnesses_table.rows[0].cells
                header[0].text = 'Nome'
                header[1].text = 'Idade'
                header[2].text = 'Cargo'
                header[3].text = 'Empresa'
                
                for person in witnesses:
                    row = witnesses_table.add_row()
                    row.cells[0].text = person.get('name', 'N/A')
                    row.cells[1].text = str(person.get('age', 'N/A')) if person.get('age') else 'N/A'
                    row.cells[2].text = person.get('job_title', 'N/A')
                    row.cells[3].text = person.get('company', 'N/A')
        
        # Timeline
        if timeline_events:
            doc.add_heading('3.3. Linha do Tempo', level=2)
            for event in timeline_events:
                event_time = event.get('event_time', 'N/A')
                event_description = event.get('description', 'N/A')
                doc.add_paragraph(f"{event_time}: {event_description}", style='List Bullet')
        
        doc.add_page_break()
        
        # ========== HIPÓTESES ==========
        if fault_tree_json:
            from utils.report_generator import extract_hypotheses_from_tree
            hypotheses = extract_hypotheses_from_tree(fault_tree_json)
            
            if hypotheses:
                doc.add_heading('5. HIPÓTESES DESCRITAS E JUSTIFICADAS', level=1)
                
                for i, hyp in enumerate(hypotheses, 1):
                    node_num = hyp.get('node_number', f'H{i}')
                    hyp_label = hyp.get('label', 'N/A')
                    doc.add_heading(f'Hipótese {node_num}: {hyp_label}', level=2)
                    
                    # Status
                    p = doc.add_paragraph()
                    p.add_run('Status: ').bold = True
                    status = hyp.get('status', 'pending')
                    if status == 'validated':
                        p.add_run('✓ CONSIDERADA/VALIDADA').bold = True
                    elif status == 'discarded':
                        p.add_run('✕ DESCARTADA').bold = True
                    else:
                        p.add_run('⏳ EM ANÁLISE').bold = True
                    
                    # Descrição
                    doc.add_paragraph(f"Descrição: {hyp_label}")
                    
                    # Justificativa
                    justification = hyp.get('justification', '')
                    if justification:
                        doc.add_paragraph('Justificativa:')
                        doc.add_paragraph(justification)
                    elif status == 'discarded':
                        doc.add_paragraph('Hipótese descartada após análise da evidência disponível.', style='Intense Quote')
                    elif status == 'validated':
                        doc.add_paragraph('Hipótese validada com base nas evidências coletadas durante a investigação.', style='Intense Quote')
                    else:
                        doc.add_paragraph('Hipótese em análise, aguardando validação ou descarte.', style='Intense Quote')
                    
                    # Código NBR
                    if hyp.get('nbr_code'):
                        doc.add_paragraph(f"Código NBR: {hyp.get('nbr_code')} - {hyp.get('nbr_description', '')}")
                    
                    doc.add_paragraph()
        
        doc.add_page_break()
        
        # ========== RECOMENDAÇÕES ==========
        if fault_tree_json:
            from utils.report_generator import extract_recommendations_from_tree
            recommendations = extract_recommendations_from_tree(fault_tree_json)
            
            if recommendations.get('basic_causes') or recommendations.get('contributing_causes'):
                doc.add_heading('9. RECOMENDAÇÕES', level=1)
                doc.add_paragraph('Abaixo são apresentadas as recomendações para prevenir ou corrigir as causas básicas e contribuintes identificadas na investigação.')
                
                if recommendations.get('basic_causes'):
                    doc.add_heading('9.1. Recomendações para Causas Básicas', level=2)
                    
                    for i, rec in enumerate(recommendations.get('basic_causes', []), 1):
                        doc.add_heading(f"{i}. {rec.get('label', 'N/A')}", level=3)
                        
                        if rec.get('nbr_code'):
                            doc.add_paragraph(f"Código NBR: {rec.get('nbr_code')} - {rec.get('nbr_description', '')}")
                        
                        recommendation_text = rec.get('recommendation', 'Nenhuma recomendação fornecida.')
                        p = doc.add_paragraph(recommendation_text)
                        p.paragraph_format.left_indent = Inches(0.5)
                        p.paragraph_format.space_before = Pt(6)
                        p.paragraph_format.space_after = Pt(6)
                
                if recommendations.get('contributing_causes'):
                    doc.add_heading('9.2. Recomendações para Causas Contribuintes', level=2)
                    
                    for i, rec in enumerate(recommendations.get('contributing_causes', []), 1):
                        doc.add_heading(f"{i}. {rec.get('label', 'N/A')}", level=3)
                        
                        if rec.get('nbr_code'):
                            doc.add_paragraph(f"Código NBR: {rec.get('nbr_code')} - {rec.get('nbr_description', '')}")
                        
                        recommendation_text = rec.get('recommendation', 'Nenhuma recomendação fornecida.')
                        p = doc.add_paragraph(recommendation_text)
                        p.paragraph_format.left_indent = Inches(0.5)
                        p.paragraph_format.space_before = Pt(6)
                        p.paragraph_format.space_after = Pt(6)
        
        # ========== COMISSÃO ==========
        commission = [p for p in people_data if p.get('person_type') == 'Commission_Member']
        if commission:
            doc.add_page_break()
            doc.add_heading('7. COMISSÃO DE INVESTIGAÇÃO', level=1)
            
            commission_table = doc.add_table(rows=1, cols=4)
            commission_table.style = 'Light Grid Accent 1'
            header = commission_table.rows[0].cells
            header[0].text = 'Nome'
            header[1].text = 'Cargo/Função'
            header[2].text = 'Matrícula/ID'
            header[3].text = 'Participação'
            
            for member in commission:
                row = commission_table.add_row()
                row.cells[0].text = member.get('name', 'N/A')
                row.cells[1].text = member.get('job_title', 'N/A')
                row.cells[2].text = member.get('registration_id', 'N/A')
                row.cells[3].text = member.get('commission_role') or member.get('training_status') or 'Membro da Comissão'
        
        # Salva em bytes
        doc_bytes = io.BytesIO()
        doc.save(doc_bytes)
        doc_bytes.seek(0)
        
        print(f"[WORD_GENERATION] ✓ Word gerado com sucesso: {len(doc_bytes.getvalue())} bytes")
        return doc_bytes.getvalue()
        
    except Exception as e:
        print(f"[WORD_GENERATION] ✗ Erro ao gerar Word: {str(e)}")
        import traceback
        traceback.print_exc()
        raise Exception(f"Erro ao gerar Word: {str(e)}")
