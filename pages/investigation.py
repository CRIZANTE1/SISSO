"""
Página de Investigação de Acidentes - Versão Wizard/Guided
Experiência intuitiva passo a passo baseada em FTA e NBR 14280
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date, time, timezone
from typing import Optional, Dict, Any, List
import requests
import os
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
from services.investigation import (
    create_accident,
    get_accidents,
    get_accident,
    update_accident,
    upload_evidence_image,
    get_evidence,
    add_timeline_event,
    get_timeline,
    update_timeline_event,
    delete_timeline_event,
    add_commission_action,
    get_commission_actions,
    update_commission_action,
    delete_commission_action,
    get_root_node,
    create_root_node,
    add_fault_tree_node,
    get_tree_nodes,
    update_node_status,
    update_node_label,
    link_nbr_standard_to_node,
    get_nbr_standards,
    get_validated_nodes,
    update_accident_status,
    build_fault_tree_json,
    get_involved_people,
    upsert_involved_people,
    get_sites,
    update_node_is_basic_cause,
    update_node_is_contributing_cause,
    upload_justification_image,
    update_node_justification_image,
    update_node_recommendation,
    delete_fault_tree_node
)
from auth.auth_utils import require_login

# Verifica disponibilidade do graphviz
try:
    import graphviz
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False


def render_progress_bar(current_step: int, total_steps: int = 4):
    """Renderiza barra de progresso visual"""
    steps = [
        ("1. Fatos & Fotos", "📸"),
        ("2. Linha do Tempo", "📅"),
        ("3. Árvore de Porquês", "🌳"),
        ("4. Classificação Oficial", "📋")
    ]
    
    # Cria colunas para cada passo
    cols = st.columns(total_steps)
    
    for i, (step_name, icon) in enumerate(steps):
        with cols[i]:
            if i < current_step:
                # Passo completado
                st.markdown(f"""
                <div style="text-align: center; padding: 10px; background-color: #d4edda; 
                            border-radius: 5px; border: 2px solid #28a745;">
                    <div style="font-size: 1.5em;">{icon}</div>
                    <div style="color: #155724; font-weight: bold;">{step_name}</div>
                    <div style="color: #155724; font-size: 0.8em;">✓ Concluído</div>
                </div>
                """, unsafe_allow_html=True)
            elif i == current_step:
                # Passo atual
                st.markdown(f"""
                <div style="text-align: center; padding: 10px; background-color: #fff3cd; 
                            border-radius: 5px; border: 2px solid #ffc107;">
                    <div style="font-size: 1.5em;">{icon}</div>
                    <div style="color: #856404; font-weight: bold;">{step_name}</div>
                    <div style="color: #856404; font-size: 0.8em;">→ Em andamento</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Passo futuro
                st.markdown(f"""
                <div style="text-align: center; padding: 10px; background-color: #f8f9fa; 
                            border-radius: 5px; border: 2px solid #dee2e6;">
                    <div style="font-size: 1.5em; opacity: 0.5;">{icon}</div>
                    <div style="color: #6c757d; font-weight: bold;">{step_name}</div>
                    <div style="color: #6c757d; font-size: 0.8em;">Aguardando</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Barra de progresso linear
    progress = (current_step + 1) / total_steps
    st.progress(progress)


def render_fault_tree_html(tree_json: Dict[str, Any]) -> str:
    """Renderiza a árvore de falhas no padrão FTA (Fault Tree Analysis) - idêntico ao diagrama"""
    if not tree_json:
        return ""
    
    import html
    
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
                'bg_color': '#c8e6c9',  # Verde claro
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
        # Root: Retângulo arredondado vermelho
        elif node_type == 'root':
            return {
                'shape': 'rounded-rect',
                'bg_color': '#ffcdd2',  # Vermelho claro
                'border_color': '#f44336',
                'text_color': '#000000',
                'border_radius': '10px'
            }
        # Causa intermediária validada: Retângulo arredondado amarelo
        elif status == 'validated' and has_children:
            return {
                'shape': 'rounded-rect',
                'bg_color': '#fff9c4',  # Amarelo claro
                'border_color': '#f9a825',
                'text_color': '#000000',
                'border_radius': '10px'
            }
        # Hipótese descartada: Losango vermelho com X
        elif status == 'discarded':
            return {
                'shape': 'diamond',
                'bg_color': '#ffcdd2',  # Vermelho claro
                'border_color': '#f44336',
                'text_color': '#000000',
                'border_radius': '0px'
            }
        # Hipótese pendente: Losango
        else:
            return {
                'shape': 'diamond',
                'bg_color': '#e0e0e0',  # Cinza claro
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
        
        # Determina forma CSS (tamanhos otimizados para A4 paisagem)
        if shape_config['shape'] == 'diamond':
            # Losango: usa div externa para dimensões e interna para conteúdo
            shape_style = "width: 140px; height: 140px; position: relative;"
            inner_style = f"position: absolute; top: 0; left: 0; width: 100%; height: 100%; clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%); background-color: {shape_config['bg_color']}; border: 2px solid {shape_config['border_color']}; box-shadow: 0 2px 6px rgba(0,0,0,0.15);"
            content_container = "position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 70%; text-align: center; z-index: 2;"
        elif shape_config['shape'] == 'oval':
            shape_style = "border-radius: 50%; width: 130px; min-height: 50px; display: flex; align-items: center; justify-content: center; padding: 8px 12px; position: relative;"
            inner_style = ""
            content_container = "z-index: 2; position: relative;"
        else:
            shape_style = f"border-radius: {shape_config['border_radius']}; width: 160px; min-height: 50px; display: flex; align-items: center; justify-content: center; padding: 8px 12px; position: relative;"
            inner_style = ""
            content_container = "z-index: 2; position: relative;"
        
        # Estilo base do nó (wrapper)
        if shape_config['shape'] == 'diamond':
            node_style = f"{shape_style}"
            node_bg_border = inner_style
        else:
            node_style = f"{shape_style} background-color: {shape_config['bg_color']}; border: 2px solid {shape_config['border_color']}; box-shadow: 0 2px 6px rgba(0,0,0,0.15);"
            node_bg_border = ""
        
        # Número do nó
        number_html = ""
        if node_number:
            number_html = f'<div style="position: absolute; top: -8px; left: -8px; background-color: {shape_config["border_color"]}; color: white; width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.65em; box-shadow: 0 2px 4px rgba(0,0,0,0.3); z-index: 10;">{node_number}</div>'
        
        # X para descartado
        discard_x = ""
        if status == 'discarded':
            discard_x = '<div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 2em; color: #d32f2f; font-weight: bold; pointer-events: none; z-index: 5; text-shadow: 1px 1px 3px rgba(255,255,255,0.9);">✕</div>'
        
        # Código NBR
        nbr_html = ""
        if nbr_code:
            nbr_code_escaped = html.escape(str(nbr_code))
            nbr_html = f'<div style="margin-top: 3px; font-size: 0.6em; color: #1976d2; font-weight: 600;">NBR: {nbr_code_escaped}</div>'
        
        # Container do conteúdo do nó
        content_html = f'<div style="{content_container}"><div style="color: {shape_config["text_color"]}; font-weight: 500; font-size: 0.7em; line-height: 1.15; word-wrap: break-word;">{label_escaped}{nbr_html}</div></div>'
        
        # Monta o nó completo
        if shape_config['shape'] == 'diamond':
            node_html_inner = f'<div style="{node_style} margin: 6px;">{number_html}<div style="{node_bg_border}"></div>{discard_x}{content_html}</div>'
        else:
            node_html_inner = f'<div style="{node_style} margin: 6px;">{number_html}{discard_x}{content_html}</div>'
        
        # Renderiza filhos
        children_html = ""
        if children:
            children_items = [render_node(child, level + 1) for child in children]
            children_html = "".join(children_items)
            
            # Container dos filhos com linhas conectivas (otimizado para A4 paisagem)
            children_html = f'<div style="position: relative; margin-top: 12px;"><div style="position: absolute; left: 50%; top: 0; width: 2px; height: 12px; background-color: #2196f3; transform: translateX(-50%);"></div><div style="position: absolute; left: 0; right: 0; top: 12px; height: 2px; background-color: #2196f3;"></div><div style="display: flex; flex-wrap: wrap; justify-content: center; align-items: flex-start; gap: 12px; padding-top: 25px;">{children_html}</div></div>'
        
        # Linha conectora ao pai
        connector = ""
        if level > 0:
            connector = '<div style="position: absolute; left: 50%; top: -12px; width: 2px; height: 12px; background-color: #2196f3; transform: translateX(-50%);"></div>'
        
        # HTML completo do nó
        return f'<div style="position: relative; display: inline-flex; flex-direction: column; align-items: center;">{connector}{node_html_inner}{children_html}</div>'
    
    # Renderiza a árvore completa
    tree_html = render_node(tree_json, level=0)
    
    # Legenda (otimizada para A4 paisagem)
    legend_html = '<div style="position: absolute; top: 8px; right: 8px; background: white; border: 2px solid #333; padding: 8px; border-radius: 4px; font-size: 0.7em; z-index: 1000; box-shadow: 0 2px 6px rgba(0,0,0,0.2); max-width: 180px;"><div style="font-weight: bold; margin-bottom: 6px; border-bottom: 1px solid #ccc; padding-bottom: 4px; font-size: 0.9em;">LEGENDA</div><div style="margin-bottom: 4px;"><strong>H:</strong> Hipótese</div><div style="margin-bottom: 4px;"><strong>CB:</strong> Causa Básica</div><div style="margin-bottom: 4px;"><strong>CC:</strong> Causa Contribuinte</div><div style="margin-bottom: 4px; display: flex; align-items: center; gap: 6px;"><div style="width: 14px; height: 14px; background: #ffcdd2; border: 2px solid #f44336; border-radius: 3px;"></div><span>Evento Topo</span></div><div style="margin-bottom: 4px; display: flex; align-items: center; gap: 6px;"><div style="width: 14px; height: 14px; clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%); background: #e0e0e0; border: 2px solid #757575;"></div><span>Hipótese</span></div><div style="margin-bottom: 4px; display: flex; align-items: center; gap: 6px;"><div style="width: 14px; height: 14px; clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%); background: #ffcdd2; border: 2px solid #f44336; position: relative;"><span style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #d32f2f; font-size: 10px;">✕</span></div><span>Descartada</span></div><div style="margin-bottom: 4px; display: flex; align-items: center; gap: 6px;"><div style="width: 14px; height: 14px; background: #fff9c4; border: 2px solid #f9a825; border-radius: 3px;"></div><span>Intermediária</span></div><div style="margin-bottom: 4px; display: flex; align-items: center; gap: 6px;"><div style="width: 14px; height: 14px; background: #c8e6c9; border: 2px solid #4caf50; border-radius: 50%;"></div><span>Causa Básica</span></div><div style="display: flex; align-items: center; gap: 6px;"><div style="width: 14px; height: 14px; background: #bbdefb; border: 2px solid #2196f3; border-radius: 50%;"></div><span>Causa Contribuinte</span></div></div>'
    
    # HTML completo (otimizado para A4 paisagem)
    from datetime import date
    return f'<div style="position: relative; font-family: Arial, sans-serif; padding: 15px 10px; background: white; min-height: 250px; overflow-x: auto; border: 1px solid #e0e0e0; border-radius: 8px;"><div style="text-align: center; margin-bottom: 15px;"><h2 style="margin: 0; color: #333; font-size: 1.2em; font-weight: bold;">ÁRVORE DE FALHAS (FTA)</h2><div style="color: #666; font-size: 0.8em; margin-top: 3px;">{date.today().strftime("%d/%m/%Y")}</div></div>{legend_html}<div style="display: flex; justify-content: center; align-items: flex-start; min-height: 180px; padding: 10px 0;">{tree_html}</div></div>'


def render_fault_tree_graph_from_json(tree_json: Dict[str, Any]):
    """Renderiza a árvore de falhas usando graphviz a partir do JSON hierárquico"""
    if not GRAPHVIZ_AVAILABLE:
        return None
    if not tree_json:
        return None
    
    import graphviz
    dot = graphviz.Digraph(comment='Fault Tree Analysis')
    dot.attr(rankdir='TB')
    dot.attr('node', shape='box', style='rounded')
    
    # Cores baseadas no status (semáforo)
    color_map = {
        'validated': '#28a745',  # Verde - Confirmado
        'discarded': '#dc3545',  # Vermelho - Descartado
        'pending': '#6c757d'     # Cinza - Em análise
    }
    
    def add_node_recursive(node_json: Dict[str, Any]):
        """Função recursiva para adicionar nós e arestas ao gráfico"""
        node_id = node_json['id']
        label = node_json['label'][:50] + '...' if len(node_json['label']) > 50 else node_json['label']
        status = node_json['status']
        node_type = node_json['type']
        nbr_code = node_json.get('nbr_code')
        
        # Define cor e estilo baseado no status
        color = color_map.get(status, '#6c757d')
        style = 'filled'
        if status == 'discarded':
            style = 'filled,strikethrough'
        
        # Label com tipo e código NBR (se existir)
        display_label = f"{label}\n[{node_type}]"
        if nbr_code:
            display_label += f"\nNBR: {nbr_code}"
        if status == 'discarded':
            display_label = f"~~{label}~~\n[{node_type}] - DESCARTADO"
        
        # Adiciona nó ao gráfico
        font_color = 'white' if status != 'pending' else 'black'
        dot.node(node_id, display_label, fillcolor=color, style=style, fontcolor=font_color)
        
        # Processa filhos recursivamente
        for child in node_json.get('children', []):
            # Adiciona aresta do pai para o filho
            dot.edge(node_id, child['id'])
            # Processa o filho recursivamente
            add_node_recursive(child)
    
    # Inicia recursão a partir do nó raiz
    add_node_recursive(tree_json)
    
    return dot


def main():
    require_login()
    
    st.title("🔍 Investigação Formal (FTA)")
    st.markdown("**Assistente de Análise de Causa Raiz por Árvore de Falhas (FTA) - Acidentes e Não Conformidades**")
    
    # ========== SIDEBAR - CONTEXT MANAGER ==========
    with st.sidebar:
        st.header("📋 Gerenciamento de Investigação")
        
        # Seleção de evento/não conformidade para investigação
        st.subheader("Selecionar Evento para Investigação")
        
        # Botão de refresh para forçar atualização
        if st.button("🔄 Atualizar Lista de Investigações", help="Clique se a investigação não aparecer"):
            st.session_state['current_accident'] = None
            st.rerun()
            
        tipo_filtro = st.radio(
            "Filtrar por Tipo:",
            options=["Todas", "🚨 Acidentes", "📋 Não Conformidades"],
            horizontal=True,
            key="inv_type_filter"
        )
        
        investigations = get_accidents()
        
        if investigations:
            # Cria opções com informações do evento / não conformidade
            investigation_options = {}
            for inv in investigations:
                is_nc = (
                    inv.get('classification') == 'Não Conformidade' or 
                    str(inv.get('registry_number', '')).startswith('NC-') or
                    str(inv.get('title', '')).startswith('N/C')
                )
                
                if tipo_filtro == "🚨 Acidentes" and is_nc:
                    continue
                if tipo_filtro == "📋 Não Conformidades" and not is_nc:
                    continue
                
                # Formata a label com informações relevantes
                prefix = "📋 [N/C]" if is_nc else "🚨 [Acidente]"
                
                # Pega título ou descrição
                title_text = inv.get('title', 'Sem título')
                if not title_text or title_text == 'Sem título':
                    title_text = inv.get('description', 'Sem título')
                
                # Limita tamanho do título
                if len(title_text) > 30:
                    title_text = title_text[:30] + "..."
                
                # Formata data
                acc_date = ""
                if inv.get('occurrence_date'):
                    try:
                        acc_date = pd.to_datetime(inv['occurrence_date']).strftime('%d/%m/%Y')
                    except:
                        try:
                            acc_date = str(inv['occurrence_date'])[:10]
                        except:
                            acc_date = ""
                elif inv.get('occurred_at'):
                    try:
                        acc_date = pd.to_datetime(inv['occurred_at']).strftime('%d/%m/%Y')
                    except:
                        try:
                            acc_date = str(inv['occurred_at'])[:10]
                        except:
                            acc_date = ""
                
                # Cria label
                if acc_date:
                    label = f"{prefix} {title_text} | {acc_date}"
                else:
                    label = f"{prefix} {title_text}"
                
                investigation_options[label] = inv['id']
            
            investigation_options["-- Selecione uma investigação --"] = None
            
            options_keys = list(investigation_options.keys())
            options_values = list(investigation_options.values())
            
            current_id = st.session_state.get('current_accident')
            default_idx = 0
            if current_id and current_id in options_values:
                default_idx = options_values.index(current_id)
            elif "-- Selecione uma investigação --" in options_keys:
                default_idx = options_keys.index("-- Selecione uma investigação --")
            
            selected_label = st.selectbox(
                "Investigação Ativa:",
                options=options_keys,
                key="investigation_selector",
                index=default_idx,
                help="Selecione um Acidente ou Não Conformidade para iniciar/continuar a investigação FTA"
            )
            
            # Obtém o ID da investigação selecionada
            selected_id = investigation_options.get(selected_label)
            
            # Valida que selected_id é um UUID válido
            if selected_id:
                selected_id = str(selected_id).strip()
                if len(selected_id) < 10:
                    st.error(f"❌ ID de investigação inválido: {selected_id}")
                    selected_id = None
            
            if selected_id and selected_id != st.session_state.get('current_accident'):
                st.session_state['current_accident'] = selected_id
                st.session_state['current_step'] = 0  # Reset step ao mudar investigação
                st.rerun()
            elif selected_id is None and selected_label == "-- Selecione uma investigação --":
                st.session_state['current_accident'] = None
                st.session_state['current_step'] = 0
        else:
            st.warning("⚠️ Nenhuma investigação encontrada.")
            st.info("""
            **Como iniciar uma investigação:**
            1. Crie um Acidente na página **"Acidentes"** ou uma Não Conformidade na página **"Não Conformidades"**
            2. Clique no botão **"🔍 Iniciar Investigação Formal (FTA)"**
            3. Acompanhe a árvore de falhas e gere o laudo pericial
            """)
            st.session_state['current_accident'] = None
            st.session_state['current_step'] = 0
        
        st.divider()
        st.markdown("""
        **📋 Fluxo de Investigação:**
        1. **Registrar Evento** → "Acidentes" ou "Não Conformidades"
        2. **Selecionar Registro** → Barra lateral
        3. **Preencher Investigação** → Passos 1-4 (Fatos, Timeline, FTA, Laudo)
        """)
    
    # ========== VERIFICAÇÃO DE ACCIDENT_ID ==========
    # IMPORTANTE: Sempre usa ID (UUID), NUNCA nome/título
    accident_id = st.session_state.get('current_accident')
    
    # Valida que accident_id é um UUID válido (não é nome/título)
    if accident_id:
        accident_id = str(accident_id).strip()
        # UUID tem 36 caracteres, mas aceita qualquer string com pelo menos 10 chars
        if len(accident_id) < 10:
            st.error(f"❌ ID de acidente inválido: {accident_id}")
            st.session_state['current_accident'] = None
            accident_id = None
    
    if not accident_id:
        st.info("👆 **Por favor, selecione um acidente na barra lateral para iniciar a investigação.**")
        st.markdown("""
        ### Como usar:
        1. **Crie um acidente** na página **"Acidentes"** (menu superior)
        2. **Volte para esta página** e selecione o acidente criado na barra lateral
        3. Após selecionar, siga o assistente passo a passo para preencher a investigação
        """)
        st.markdown("---")
        st.markdown("**💡 Dica:** O acidente deve ser criado primeiro na página 'Acidentes' antes de iniciar a investigação aqui.**")
        return
    
    # ========== CARREGA DADOS DA INVESTIGAÇÃO (BUSCA POR ID) ==========
    # IMPORTANTE: get_accident() busca EXCLUSIVAMENTE por ID (UUID), nunca por nome/título
    investigation = get_accident(accident_id)
    if not investigation:
        st.error(f"❌ Acidente não encontrado com ID: {accident_id[:8]}...")
        st.info("💡 Tente selecionar o acidente novamente na barra lateral.")
        st.session_state['current_accident'] = None
        st.rerun()
        return
    
    # ========== INICIALIZA STEP SE NÃO EXISTIR ==========
    if 'current_step' not in st.session_state:
        st.session_state['current_step'] = 0
    
    # ========== BARRA DE PROGRESSO ==========
    st.divider()
    render_progress_bar(st.session_state['current_step'])
    st.divider()
    
    # ========== HEADER DA INVESTIGAÇÃO ==========
    is_nc = (
        investigation.get('classification') == 'Não Conformidade' or 
        str(investigation.get('registry_number', '')).startswith('NC-') or
        str(investigation.get('title', '')).startswith('N/C')
    )
    
    col_status, col_info = st.columns([1, 3])
    
    with col_status:
        # Normaliza status para exibição
        acc_status = investigation.get('status', 'Open')
        if acc_status.lower() in ['aberto', 'open']:
            status_color = "🟢"
            status_text = "Aberto"
        else:
            status_color = "🔴"
            status_text = "Fechado"
        st.markdown(f"**Status:** {status_color} {status_text}")
        if is_nc:
            st.caption("📋 **Tipo:** Não Conformidade")
        else:
            st.caption(f"🚨 **Tipo:** {investigation.get('type', 'Acidente')}")
    
    with col_info:
        if is_nc:
            st.markdown(f"### 📋 Investigação de Não Conformidade: {investigation.get('title', 'N/A')}")
            st.caption(f"**Registro:** `{investigation.get('registry_number', 'N/A')}` | **Metodologia:** Árvore de Falhas (FTA) / NBR 14280 / ISO 45001")
        else:
            st.markdown(f"### 🚨 Investigação de Acidente: {investigation.get('title', 'N/A')}")
            st.caption(f"**Registro:** `{investigation.get('registry_number', 'N/A')}` | **Metodologia:** Árvore de Falhas (FTA) / NBR 14280")
        if investigation.get('description'):
            st.caption(f"{investigation['description']}")
    
    st.divider()
    
    # ========== PASSO 1: FATOS & FOTOS ==========
    if st.session_state['current_step'] == 0:
        st.header("📸 Passo 1: Contexto e Evidências")
        st.markdown("**O que aconteceu?** Preencha todos os dados do acidente conforme o relatório oficial.")
        
        # Carrega dados existentes
        involved_drivers = get_involved_people(accident_id, 'Driver')
        involved_injured = get_involved_people(accident_id, 'Injured')
        involved_commission = get_involved_people(accident_id, 'Commission_Member')
        involved_witnesses = get_involved_people(accident_id, 'Witness')
        
        # ========== CAMPOS DE CONTROLE FORA DO FORM (para atualização imediata) ==========
        st.divider()
        st.markdown("### 👥 Configuração de Pessoas Envolvidas")
        
        # Inicializa session_state para todos os contadores
        num_drivers_key = f"num_drivers_{accident_id}"
        num_injured_key = f"num_injured_{accident_id}"
        num_witnesses_key = f"num_witnesses_{accident_id}"
        num_commission_key = f"num_commission_{accident_id}"
        
        if num_drivers_key not in st.session_state:
            st.session_state[num_drivers_key] = len(involved_drivers)
        if num_injured_key not in st.session_state:
            st.session_state[num_injured_key] = len(involved_injured)
        if num_witnesses_key not in st.session_state:
            st.session_state[num_witnesses_key] = len(involved_witnesses)
        if num_commission_key not in st.session_state:
            st.session_state[num_commission_key] = len(involved_commission) if involved_commission else 0
        
        # Campos de número FORA DO FORM para atualização imediata
        col_drv, col_inj, col_wit = st.columns(3)
        with col_drv:
            num_drivers = st.number_input(
                "🚗 Quantidade de motoristas:", 
                min_value=0, 
                max_value=10, 
                value=st.session_state[num_drivers_key], 
                key=f"num_drivers_input_{accident_id}",
                help="Digite o número de motoristas"
            )
            if num_drivers != st.session_state[num_drivers_key]:
                st.session_state[num_drivers_key] = num_drivers
                st.rerun()
        
        with col_inj:
            num_injured = st.number_input(
                "🏥 Quantidade de vítimas:", 
                min_value=0, 
                max_value=10, 
                value=st.session_state[num_injured_key], 
                key=f"num_injured_input_{accident_id}",
                help="Digite 1 para ver campos detalhados do perfil do acidentado"
            )
            if num_injured != st.session_state[num_injured_key]:
                st.session_state[num_injured_key] = num_injured
                st.rerun()
            # Mensagem informativa
            if num_injured == 1:
                st.success("✅ Campos detalhados aparecerão no formulário")
        
        with col_wit:
            num_witnesses = st.number_input(
                "👁️ Quantidade de testemunhas:", 
                min_value=0, 
                max_value=10, 
                value=st.session_state[num_witnesses_key], 
                key=f"num_witnesses_input_{accident_id}",
                help="Digite o número de testemunhas"
            )
            if num_witnesses != st.session_state[num_witnesses_key]:
                st.session_state[num_witnesses_key] = num_witnesses
                st.rerun()
        
        # Campo de quantidade de membros da comissão FORA do form
        with st.expander("👔 Configurar Comissão de Investigação", expanded=True):
            num_commission = st.number_input(
                "Quantidade de membros:", 
                min_value=0, 
                max_value=10, 
                value=st.session_state[num_commission_key], 
                key=f"num_commission_input_{accident_id}",
                help="Defina quantos membros da comissão você deseja cadastrar. Os campos aparecerão no formulário abaixo."
            )
            if num_commission != st.session_state[num_commission_key]:
                st.session_state[num_commission_key] = num_commission
                st.rerun()
        
        st.divider()
        
        # Formulário completo com seções
        with st.form("accident_context_form", clear_on_submit=False):
            # ========== SEÇÃO 1: DADOS GERAIS ==========
            with st.expander("📋 Seção 1: Dados Gerais", expanded=True):
                col_reg, col_date = st.columns(2)
                with col_reg:
                    registry_number = st.text_input(
                        "Número do Registro:",
                        value=investigation.get('registry_number', ''),
                        placeholder="Ex: XX/2024",
                        help="Número de registro do acidente conforme protocolo interno"
                    )
                
                with col_date:
                    if investigation.get('occurrence_date'):
                        # Converte do banco (pode estar em UTC ou sem timezone)
                        occ_dt = pd.to_datetime(investigation.get('occurrence_date'))
                        # Remove timezone se existir para manter o horário original
                        if occ_dt.tz is not None:
                            occ_dt = occ_dt.tz_localize(None)
                        occ_date = occ_dt.date()
                        occ_time = occ_dt.time()
                    else:
                        occ_date = date.today()
                        occ_time = time(12, 0)
                    
                    occurrence_date_input = st.date_input(
                        "Data da Ocorrência:",
                        value=occ_date,
                        help="Data do acidente"
                    )
                    occurrence_time_input = st.time_input(
                        "Hora da Ocorrência:",
                        value=occ_time,
                        help="Hora do acidente"
                    )
                    # Combina data e hora (sem timezone - mantém horário como inserido pelo usuário)
                    occurrence_datetime = datetime.combine(occurrence_date_input, occurrence_time_input)
                
                # Campo: Local da Base (input manual)
                base_location = st.text_input(
                    "Local da Base:",
                    value=investigation.get('base_location', ''),
                    placeholder="Ex: Hangar 3, Pista 2, Área de Manutenção",
                    help="Digite o local específico dentro da base onde ocorreu o acidente"
                )
                
                # Campo: Base (selectbox da tabela sites)
                sites_list = get_sites()
                site_options = [""] + [f"{site['name']} ({site['code']})" for site in sites_list]
                site_ids = [None] + [site['id'] for site in sites_list]
                
                # Encontra o site_id atual do acidente (se existir)
                current_site_id = investigation.get('site_id')
                current_site_index = 0
                if current_site_id:
                    try:
                        current_site_index = site_ids.index(current_site_id) if current_site_id in site_ids else 0
                    except:
                        current_site_index = 0
                
                # Garante que o index está dentro dos limites
                current_site_index = max(0, min(current_site_index, len(site_options) - 1))
                selected_site_label = st.selectbox(
                    "Base:",
                    options=site_options,
                    index=current_site_index,
                    help="Selecione a base da tabela de sites cadastrados",
                    disabled=False
                )
                
                # Obtém o site_id correspondente à seleção
                selected_site_id = None
                if selected_site_label and selected_site_label != "":
                    selected_index = site_options.index(selected_site_label)
                    if selected_index > 0:  # Não é a opção vazia
                        selected_site_id = site_ids[selected_index]
                
                title = st.text_input(
                    "Título do Acidente:",
                    value=investigation.get('title', ''),
                    help="Título descritivo do acidente"
                )
                
                # Campo: Tipo do Acidente
                current_type = investigation.get('type', 'sem_lesao')
                type_options = ["fatal", "lesao", "sem_lesao"]
                type_labels = {
                    "fatal": "Fatal",
                    "lesao": "Com Lesão",
                    "sem_lesao": "Sem Lesão"
                }
                current_type_index = type_options.index(current_type) if current_type in type_options else 2
                # Garante que o index está dentro dos limites
                current_type_index = max(0, min(current_type_index, len(type_options) - 1))
                accident_type = st.selectbox(
                    "Tipo do Acidente:",
                    options=type_options,
                    index=current_type_index,
                    format_func=lambda x: type_labels.get(x, x),
                    help="Tipo do acidente: Fatal, Com Lesão ou Sem Lesão",
                    disabled=False
                )
                
                description = st.text_area(
                    "Descrição Detalhada:",
                    value=investigation.get('description', ''),
                    height=100,
                    help="Descrição completa do que aconteceu"
                )
            
            # ========== SEÇÃO 2: CLASSIFICAÇÃO E GRAVIDADE ==========
            with st.expander("🏷️ Seção 2: Classificação e Gravidade", expanded=True):
                st.markdown("**Selecione todas as classificações aplicáveis:**")
                
                col_class1, col_class2 = st.columns(2)
                with col_class1:
                    # Garante que o valor seja sempre booleano (não None)
                    class_injury_val = investigation.get('class_injury')
                    class_injury = st.checkbox(
                        "Com Lesão",
                        value=bool(class_injury_val) if class_injury_val is not None else False,
                        help="Acidente com lesão física",
                        key="class_injury_checkbox"
                    )
                    class_environment_val = investigation.get('class_environment')
                    class_environment = st.checkbox(
                        "Meio Ambiente",
                        value=bool(class_environment_val) if class_environment_val is not None else False,
                        help="Impacto ambiental",
                        key="class_environment_checkbox"
                    )
                    class_process_safety_val = investigation.get('class_process_safety')
                    class_process_safety = st.checkbox(
                        "Segurança de Processo",
                        value=bool(class_process_safety_val) if class_process_safety_val is not None else False,
                        help="Relacionado à segurança de processo",
                        key="class_process_safety_checkbox"
                    )
                
                with col_class2:
                    class_asset_damage_val = investigation.get('class_asset_damage')
                    class_asset_damage = st.checkbox(
                        "Dano ao Patrimônio",
                        value=bool(class_asset_damage_val) if class_asset_damage_val is not None else False,
                        help="Danos materiais/patrimoniais",
                        key="class_asset_damage_checkbox"
                    )
                    class_community_val = investigation.get('class_community')
                    class_community = st.checkbox(
                        "Impacto na Comunidade",
                        value=bool(class_community_val) if class_community_val is not None else False,
                        help="Impacto na comunidade local",
                        key="class_community_checkbox"
                    )
                    class_near_miss_val = investigation.get('class_near_miss')
                    class_near_miss = st.checkbox(
                        "Quase-Acidente",
                        value=bool(class_near_miss_val) if class_near_miss_val is not None else False,
                        help="Evento de quase-acidente",
                        key="class_near_miss_checkbox"
                    )
                
                # Mapeamento entre português (interface) e inglês (banco)
                severity_options_pt = ["", "Muito Baixa", "Baixa", "Média", "Alta", "Catastrófica"]
                severity_options_en = ["", "Very Low", "Low", "Medium", "High", "Catastrophic"]
                
                # Converte valor do banco (inglês) para índice em português
                current_severity_en = investigation.get('severity_level', '') or ''
                current_index = 0
                if current_severity_en and current_severity_en in severity_options_en:
                    current_index = severity_options_en.index(current_severity_en)
                
                # Garante que o index está dentro dos limites
                current_index = max(0, min(current_index, len(severity_options_pt) - 1))
                severity_level_pt = st.selectbox(
                    "Nível de Gravidade:",
                    options=severity_options_pt,
                    index=current_index,
                    help="Gravidade do acidente: Muito Baixa, Baixa, Média, Alta ou Catastrófica",
                    disabled=False
                )
                
                # Converte seleção em português para inglês (para salvar no banco)
                if severity_level_pt and severity_level_pt in severity_options_pt:
                    severity_level = severity_options_en[severity_options_pt.index(severity_level_pt)]
                else:
                    severity_level = ""
                
                estimated_loss_val = investigation.get('estimated_loss_value')
                estimated_loss_value = st.number_input(
                    "Valor Estimado de Perdas (R$):",
                    value=float(estimated_loss_val) if estimated_loss_val is not None else 0.0,
                    min_value=0.0,
                    step=1000.0,
                    help="Valor estimado das perdas em reais"
                )
            
            # ========== SEÇÃO 3: DETALHES DO VAZAMENTO/PROCESSO ==========
            show_process_details = class_environment or class_process_safety
            
            if show_process_details:
                # Variáveis para armazenar valores (inicializadas antes)
                process_safety_observation = None
                has_fire = False
                fire_area = None
                fire_duration_hours = 0.0
                fire_observation = None
                has_explosion = False
                explosion_type = None
                explosion_area = None
                explosion_duration_hours = 0.0
                explosion_observation = None
                transporter_name = None
                transporter_cnpj = None
                transporter_contract_number = None
                transporter_contract_start = None
                transporter_contract_end = None
                loss_product = 0.0
                loss_material = 0.0
                loss_vacuum_truck = 0.0
                loss_indirect_contractor = 0.0
                loss_overtime_hours = 0.0
                loss_civil_works = 0.0
                loss_waste_containers = 0.0
                loss_mechanical_works = 0.0
                loss_mobilization = 0.0
                loss_total = 0.0
                
                if class_process_safety:
                    # Seção expandida para Segurança de Processo
                    with st.expander("🔬 Seção 3: Acidentes de Segurança de Processo", expanded=True):
                        st.info("💡 Esta seção contém campos específicos para acidentes de segurança de processo")
                        
                        # Subseção 1: VAZAMENTO
                        st.markdown("### 🔵 Vazamento")
                        product_released = st.text_input(
                            "Produto liberado:",
                            value=investigation.get('product_released', ''),
                            placeholder="Ex: Gasolina, Etanol, Diesel...",
                            key="process_product_released"
                        )
                        
                        col_vol1, col_vol2 = st.columns(2)
                        with col_vol1:
                            vol_released_val = investigation.get('volume_released')
                            volume_released = st.number_input(
                                "Volume vazado (m³):",
                                value=float(vol_released_val) if vol_released_val is not None else 0.0,
                                min_value=0.0,
                                step=0.1,
                                key="process_volume_released"
                            )
                        
                        with col_vol2:
                            vol_recovered_val = investigation.get('volume_recovered')
                            volume_recovered = st.number_input(
                                "Volume Recuperado (m³):",
                                value=float(vol_recovered_val) if vol_recovered_val is not None else 0.0,
                                min_value=0.0,
                                step=0.1,
                                key="process_volume_recovered"
                            )
                        
                        release_duration_val = investigation.get('release_duration_hours')
                        release_duration_hours = st.number_input(
                            "Duração vazamento (horas):",
                            value=float(release_duration_val) if release_duration_val is not None else 0.0,
                            min_value=0.0,
                            step=0.1,
                            key="process_release_duration"
                        )
                        
                        equipment_involved = st.text_area(
                            "Equipamento onde ocorreu a perda de contenção:",
                            value=investigation.get('equipment_involved', ''),
                            height=80,
                            key="process_equipment_involved"
                        )
                        
                        process_safety_observation = st.text_area(
                            "Observação:",
                            value=investigation.get('process_safety_observation', ''),
                            height=100,
                            key="process_safety_observation"
                        )
                        
                        st.divider()
                        
                        # Subseção 2: INCÊNDIO
                        st.markdown("### 🔥 Incêndio")
                        has_fire = st.checkbox(
                            "Ocorreu incêndio",
                            value=bool(investigation.get('has_fire', False)),
                            key="process_has_fire"
                        )
                        
                        if has_fire:
                            fire_area = st.text_input(
                                "Área afetada pelo incêndio:",
                                value=investigation.get('fire_area', ''),
                                key="process_fire_area"
                            )
                            
                            fire_duration_val = investigation.get('fire_duration_hours')
                            fire_duration_hours = st.number_input(
                                "Duração do incêndio (horas):",
                                value=float(fire_duration_val) if fire_duration_val is not None else 0.0,
                                min_value=0.0,
                                step=0.1,
                                key="process_fire_duration"
                            )
                            
                            fire_observation = st.text_area(
                                "Observações sobre o incêndio:",
                                value=investigation.get('fire_observation', ''),
                                height=80,
                                key="process_fire_observation"
                            )
                        
                        st.divider()
                        
                        # Subseção 3: EXPLOSÃO
                        st.markdown("### 💥 Explosão")
                        has_explosion = st.checkbox(
                            "Ocorreu explosão",
                            value=bool(investigation.get('has_explosion', False)),
                            key="process_has_explosion"
                        )
                        
                        if has_explosion:
                            col_exp1, col_exp2 = st.columns(2)
                            with col_exp1:
                                explosion_type = st.text_input(
                                    "Tipo de explosão:",
                                    value=investigation.get('explosion_type', ''),
                                    key="process_explosion_type"
                                )
                            
                            with col_exp2:
                                explosion_area = st.text_input(
                                    "Área afetada pela explosão:",
                                    value=investigation.get('explosion_area', ''),
                                    key="process_explosion_area"
                                )
                            
                            explosion_duration_val = investigation.get('explosion_duration_hours')
                            explosion_duration_hours = st.number_input(
                                "Duração/efeito da explosão (horas):",
                                value=float(explosion_duration_val) if explosion_duration_val is not None else 0.0,
                                min_value=0.0,
                                step=0.1,
                                key="process_explosion_duration"
                            )
                            
                            explosion_observation = st.text_area(
                                "Observações sobre a explosão:",
                                value=investigation.get('explosion_observation', ''),
                                height=80,
                                key="process_explosion_observation"
                            )
                        
                        st.divider()
                        
                        # Subseção 4: INFORMAÇÕES DO CONDUTOR
                        st.markdown("### 🚗 Informações do Condutor envolvido no acidente (Transporte ou Frota Leve)")
                        st.info("💡 Preencha os dados do condutor abaixo. Se não se aplica, deixe em branco.")
                        
                        # Usa os motoristas já cadastrados
                        if len(involved_drivers) > 0:
                            for i, driver in enumerate(involved_drivers):
                                with st.expander(f"Condutor {i+1}: {driver.get('name', 'N/A')}", expanded=(i == 0)):
                                    col_d1, col_d2, col_d3 = st.columns(3)
                                    with col_d1:
                                        marital_options = ["", "Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)", "União Estável"]
                                        current_driver_marital = driver.get('marital_status', '')
                                        try:
                                            driver_marital_index = marital_options.index(current_driver_marital) if current_driver_marital in marital_options else 0
                                        except (ValueError, AttributeError):
                                            driver_marital_index = 0
                                        driver_marital_index = max(0, min(driver_marital_index, len(marital_options) - 1))
                                        driver_marital = st.selectbox(
                                            "Estado Civil:",
                                            options=marital_options,
                                            index=driver_marital_index,
                                            key=f"driver_marital_{i}",
                                            disabled=False
                                        )
                                    
                                    with col_d2:
                                        driver_children = st.number_input(
                                            "Número de Filhos:",
                                            min_value=0,
                                            max_value=20,
                                            value=int(driver.get('children_count', 0)) if driver.get('children_count') else 0,
                                            key=f"driver_children_{i}"
                                        )
                                    
                                    with col_d3:
                                        driver_time_company = st.text_input(
                                            "Tempo Empresa:",
                                            value=driver.get('time_in_company', ''),
                                            placeholder="Ex: 5 anos",
                                            key=f"driver_time_company_{i}"
                                        )
                                    
                                    col_d4, col_d5, col_d6 = st.columns(3)
                                    with col_d4:
                                        driver_time_role = st.text_input(
                                            "Tempo Função:",
                                            value=driver.get('time_in_role', ''),
                                            placeholder="Ex: 3 anos",
                                            key=f"driver_time_role_{i}"
                                        )
                                    
                                    with col_d5:
                                        driver_time_vehicle = st.text_input(
                                            "Tempo Dirigindo o Tipo de Veículo:",
                                            value=driver.get('time_driving_vehicle_type', ''),
                                            placeholder="Ex: 2 anos",
                                            key=f"driver_time_vehicle_{i}"
                                        )
                                    
                                    with col_d6:
                                        driver_time_license = st.text_input(
                                            "Tempo Habilitação:",
                                            value=driver.get('time_license', ''),
                                            placeholder="Ex: 10 anos",
                                            key=f"driver_time_license_{i}"
                                        )
                                    
                                    driver_observation = st.text_area(
                                        "Observação:",
                                        value=driver.get('driver_observation', ''),
                                        height=60,
                                        key=f"driver_observation_{i}"
                                    )
                        else:
                            st.info("ℹ️ Nenhum condutor cadastrado. Adicione na Seção 4: Pessoas Envolvidas.")
                        
                        st.divider()
                        
                        # Subseção 5: INFORMAÇÕES DA TRANSPORTADORA
                        st.markdown("### 🚛 Acidentes no Transporte – Informações Transportadora")
                        transporter_not_applicable = st.checkbox(
                            "Não aplicável",
                            value=not bool(investigation.get('transporter_name')),
                            key="transporter_not_applicable"
                        )
                        
                        if not transporter_not_applicable:
                            transporter_name = st.text_input(
                                "Transportadora:",
                                value=investigation.get('transporter_name', ''),
                                key="transporter_name"
                            )
                            
                            col_t1, col_t2 = st.columns(2)
                            with col_t1:
                                transporter_cnpj = st.text_input(
                                    "CNPJ:",
                                    value=investigation.get('transporter_cnpj', ''),
                                    placeholder="00.000.000/0000-00",
                                    key="transporter_cnpj"
                                )
                            
                            with col_t2:
                                transporter_contract_number = st.text_input(
                                    "Nº do Contrato:",
                                    value=investigation.get('transporter_contract_number', ''),
                                    key="transporter_contract_number"
                                )
                            
                            col_t3, col_t4 = st.columns(2)
                            with col_t3:
                                transporter_start_val = investigation.get('transporter_contract_start')
                                if transporter_start_val:
                                    try:
                                        transporter_start_val = pd.to_datetime(transporter_start_val).date()
                                    except:
                                        transporter_start_val = None
                                transporter_contract_start = st.date_input(
                                    "Início:",
                                    value=transporter_start_val,
                                    key="transporter_contract_start"
                                )
                            
                            with col_t4:
                                transporter_end_val = investigation.get('transporter_contract_end')
                                if transporter_end_val:
                                    try:
                                        transporter_end_val = pd.to_datetime(transporter_end_val).date()
                                    except:
                                        transporter_end_val = None
                                transporter_contract_end = st.date_input(
                                    "Final:",
                                    value=transporter_end_val,
                                    key="transporter_contract_end"
                                )
                        
                        st.divider()
                        
                        # Subseção 6: VALOR ESTIMADO DAS PERDAS
                        st.markdown("### 💰 Valor Estimado das Perdas")
                        st.info("💡 Preencha os valores das perdas. O valor total será calculado automaticamente.")
                        
                        col_l1, col_l2, col_l3 = st.columns(3)
                        with col_l1:
                            loss_product = st.number_input(
                                "Perda do Produto (R$):",
                                value=float(investigation.get('loss_product', 0) or 0),
                                min_value=0.0,
                                step=1000.0,
                                key="loss_product"
                            )
                            loss_material = st.number_input(
                                "Perda Material (R$):",
                                value=float(investigation.get('loss_material', 0) or 0),
                                min_value=0.0,
                                step=1000.0,
                                key="loss_material"
                            )
                            loss_vacuum_truck = st.number_input(
                                "Caminhão vácuo (R$):",
                                value=float(investigation.get('loss_vacuum_truck', 0) or 0),
                                min_value=0.0,
                                step=1000.0,
                                key="loss_vacuum_truck"
                            )
                        
                        with col_l2:
                            loss_indirect_contractor = st.number_input(
                                "Efetivo Indireto - empreiteira (R$):",
                                value=float(investigation.get('loss_indirect_contractor', 0) or 0),
                                min_value=0.0,
                                step=1000.0,
                                key="loss_indirect_contractor"
                            )
                            loss_overtime_hours = st.number_input(
                                "Custos de Horas extras pessoal (R$):",
                                value=float(investigation.get('loss_overtime_hours', 0) or 0),
                                min_value=0.0,
                                step=1000.0,
                                key="loss_overtime_hours"
                            )
                            loss_civil_works = st.number_input(
                                "Obras civis – empreiteira (R$):",
                                value=float(investigation.get('loss_civil_works', 0) or 0),
                                min_value=0.0,
                                step=1000.0,
                                key="loss_civil_works"
                            )
                        
                        with col_l3:
                            loss_waste_containers = st.number_input(
                                "Caçambas de resíduos (R$):",
                                value=float(investigation.get('loss_waste_containers', 0) or 0),
                                min_value=0.0,
                                step=1000.0,
                                key="loss_waste_containers"
                            )
                            loss_mechanical_works = st.number_input(
                                "Obras mecânicas – empreiteira (R$):",
                                value=float(investigation.get('loss_mechanical_works', 0) or 0),
                                min_value=0.0,
                                step=1000.0,
                                key="loss_mechanical_works"
                            )
                            loss_mobilization = st.number_input(
                                "Mobilização - empreiteira (R$):",
                                value=float(investigation.get('loss_mobilization', 0) or 0),
                                min_value=0.0,
                                step=1000.0,
                                key="loss_mobilization"
                            )
                        
                        # Calcula valor total
                        loss_total = (loss_product + loss_material + loss_vacuum_truck + 
                                     loss_indirect_contractor + loss_overtime_hours + loss_civil_works +
                                     loss_waste_containers + loss_mechanical_works + loss_mobilization)
                        
                        st.metric(
                            "Valor Total (R$):",
                            f"{loss_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                        )
                
                else:
                    # Seção básica para Meio Ambiente (sem Segurança de Processo)
                    with st.expander("🔬 Seção 3: Detalhes do Vazamento/Processo", expanded=True):
                        st.info("💡 Esta seção aparece porque você marcou 'Meio Ambiente'")
                        
                        product_released = st.text_input(
                            "Produto Liberado:",
                            value=investigation.get('product_released', ''),
                            placeholder="Ex: Gasolina, Etanol, Diesel...",
                            help="Nome do produto que foi liberado/vazado"
                        )
                        
                        col_vol1, col_vol2 = st.columns(2)
                        with col_vol1:
                            vol_released_val = investigation.get('volume_released')
                            volume_released = st.number_input(
                                "Volume Liberado (m³):",
                                value=float(vol_released_val) if vol_released_val is not None else 0.0,
                                min_value=0.0,
                                step=0.1,
                                help="Volume total liberado em metros cúbicos"
                            )
                        
                        with col_vol2:
                            vol_recovered_val = investigation.get('volume_recovered')
                            volume_recovered = st.number_input(
                                "Volume Recuperado (m³):",
                                value=float(vol_recovered_val) if vol_recovered_val is not None else 0.0,
                                min_value=0.0,
                                step=0.1,
                                help="Volume recuperado em metros cúbicos"
                            )
                        
                        release_duration_val = investigation.get('release_duration_hours')
                        release_duration_hours = st.number_input(
                            "Duração do Vazamento (horas):",
                            value=float(release_duration_val) if release_duration_val is not None else 0.0,
                            min_value=0.0,
                            step=0.1,
                            help="Tempo de duração do vazamento em horas"
                        )
                        
                        equipment_involved = st.text_area(
                            "Equipamento Envolvido:",
                            value=investigation.get('equipment_involved', ''),
                            height=80,
                            help="Descrição do equipamento envolvido no acidente"
                        )
                        
                        area_affected = st.radio(
                            "Área Afetada:",
                            options=["", "Soil", "Water", "Not Applicable", "Other"],
                            index=0 if not investigation.get('area_affected') else 
                                  (["", "Soil", "Water", "Not Applicable", "Other"].index(investigation.get('area_affected'))
                                   if investigation.get('area_affected') in ["", "Soil", "Water", "Not Applicable", "Other"] else 0),
                            help="Tipo de área afetada pelo vazamento"
                        )
            
            # ========== SEÇÃO 4: ENVOLVIDOS ==========
            st.markdown("### 👥 Seção 4: Pessoas Envolvidas")
            st.markdown("**Motoristas, Vítimas e Testemunhas**")
            
            # Motoristas
            with st.expander("🚗 Motoristas", expanded=True):
                if st.session_state.get(f"num_drivers_{accident_id}", 0) == 0:
                    st.info("ℹ️ Configure a quantidade de motoristas acima para começar a preencher os dados.")
                drivers = []
                # Usa o valor do session_state (definido fora do form)
                num_drivers = st.session_state.get(f"num_drivers_{accident_id}", len(involved_drivers))
                for i in range(num_drivers):
                    with st.container():
                        col1, col2 = st.columns(2)
                        with col1:
                            driver_name = st.text_input(f"Nome {i+1}:", value=involved_drivers[i].get('name', '') if i < len(involved_drivers) else '', key=f"driver_name_{i}")
                            driver_reg = st.text_input(f"Matrícula/CPF {i+1}:", value=involved_drivers[i].get('registration_id', '') if i < len(involved_drivers) else '', key=f"driver_reg_{i}")
                            driver_company = st.text_input(f"Empresa {i+1}:", value=involved_drivers[i].get('company', '') if i < len(involved_drivers) else '', key=f"driver_company_{i}")
                        with col2:
                            driver_role = st.text_input(f"Cargo/Função {i+1}:", value=involved_drivers[i].get('job_title', '') if i < len(involved_drivers) else '', key=f"driver_role_{i}")
                            driver_age_val = involved_drivers[i].get('age') if i < len(involved_drivers) and involved_drivers[i].get('age') else 0
                            driver_age = st.number_input(f"Idade {i+1}:", min_value=0, max_value=100, value=int(driver_age_val) if driver_age_val else 0, key=f"driver_age_{i}")
                            
                            driver_aso_val = None
                            if i < len(involved_drivers) and involved_drivers[i].get('aso_date'):
                                try:
                                    driver_aso_val = pd.to_datetime(involved_drivers[i].get('aso_date')).date()
                                except:
                                    driver_aso_val = None
                            driver_aso = st.date_input(f"Data ASO {i+1}:", value=driver_aso_val, key=f"driver_aso_{i}")
                        
                        if driver_name:
                            driver_data = {
                                'person_type': 'Driver',
                                'name': driver_name,
                                'registration_id': driver_reg or None,
                                'job_title': driver_role or None,
                                'company': driver_company or None,
                                'age': driver_age if driver_age else None,
                                'aso_date': driver_aso.isoformat() if driver_aso else None
                            }
                            
                            # Adiciona campos adicionais se existirem na seção de segurança de processo
                            # Esses campos são coletados via session_state quando estiverem na seção 3
                            if class_process_safety and len(involved_drivers) > i:
                                # Busca dados adicionais do condutor se foram preenchidos na seção de segurança de processo
                                driver_key_marital = f"driver_marital_{i}"
                                driver_key_children = f"driver_children_{i}"
                                driver_key_time_company = f"driver_time_company_{i}"
                                driver_key_time_role = f"driver_time_role_{i}"
                                driver_key_time_vehicle = f"driver_time_vehicle_{i}"
                                driver_key_time_license = f"driver_time_license_{i}"
                                driver_key_observation = f"driver_observation_{i}"
                                
                                if driver_key_marital in st.session_state:
                                    driver_data['marital_status'] = st.session_state[driver_key_marital] if st.session_state[driver_key_marital] else None
                                if driver_key_children in st.session_state:
                                    driver_data['children_count'] = st.session_state[driver_key_children] if st.session_state[driver_key_children] else None
                                if driver_key_time_company in st.session_state:
                                    driver_data['time_in_company'] = st.session_state[driver_key_time_company] if st.session_state[driver_key_time_company] else None
                                if driver_key_time_role in st.session_state:
                                    driver_data['time_in_role'] = st.session_state[driver_key_time_role] if st.session_state[driver_key_time_role] else None
                                if driver_key_time_vehicle in st.session_state:
                                    driver_data['time_driving_vehicle_type'] = st.session_state[driver_key_time_vehicle] if st.session_state[driver_key_time_vehicle] else None
                                if driver_key_time_license in st.session_state:
                                    driver_data['time_license'] = st.session_state[driver_key_time_license] if st.session_state[driver_key_time_license] else None
                                if driver_key_observation in st.session_state:
                                    driver_data['driver_observation'] = st.session_state[driver_key_observation] if st.session_state[driver_key_observation] else None
                            
                            drivers.append(driver_data)
            
            # Vítimas/Lesionados
            with st.expander("🏥 Vítimas/Lesionados", expanded=True):
                # Usa o valor do session_state (definido fora do form)
                num_injured = st.session_state.get(f"num_injured_{accident_id}", len(involved_injured))
                
                if num_injured == 0:
                    st.info("ℹ️ Configure a quantidade de vítimas acima para começar a preencher os dados.")
                else:
                    # Mostra mensagem informativa quando há 1 vítima
                    if num_injured == 1:
                        st.success("✅ **1 vítima selecionada**: Os campos detalhados do perfil do acidentado aparecerão abaixo.")
                    elif num_injured > 1:
                        st.info(f"ℹ️ **{num_injured} vítimas selecionadas**: Formulário simplificado para múltiplas vítimas.")
                
                injured = []
                for i in range(num_injured):
                    # Se houver apenas 1 vítima, exibe formulário completo detalhado
                    if num_injured == 1:
                        with st.expander(f"📋 Perfil do Acidentado", expanded=True):
                            # Linha 1: Nome | Nascimento | Idade
                            col_nome, col_nasc, col_idade = st.columns(3)
                            with col_nome:
                                injured_name = st.text_input(
                                    "Nome:",
                                    value=involved_injured[i].get('name', '') if i < len(involved_injured) else '',
                                    key=f"injured_name_{i}"
                                )
                            with col_nasc:
                                birth_date_val = None
                                if i < len(involved_injured) and involved_injured[i].get('birth_date'):
                                    try:
                                        birth_date_val = pd.to_datetime(involved_injured[i].get('birth_date')).date()
                                    except:
                                        birth_date_val = None
                                injured_birth_date = st.date_input(
                                    "Nascimento:",
                                    value=birth_date_val,
                                    min_value=date(1900, 1, 1),
                                    max_value=date.today(),
                                    key=f"injured_birth_date_{i}",
                                    help="Selecione a data de nascimento da vítima"
                                )
                            with col_idade:
                                injured_age_val = involved_injured[i].get('age') if i < len(involved_injured) and involved_injured[i].get('age') else 0
                                injured_age = st.number_input(
                                    "Idade:",
                                    min_value=0,
                                    max_value=100,
                                    value=int(injured_age_val) if injured_age_val else 0,
                                    key=f"injured_age_{i}"
                                )
                            
                            # Linha 2: CPF | RG | Estado Civil
                            col_cpf, col_rg, col_estado = st.columns(3)
                            with col_cpf:
                                injured_reg = st.text_input(
                                    "CPF:",
                                    value=involved_injured[i].get('registration_id', '') if i < len(involved_injured) else '',
                                    key=f"injured_reg_{i}",
                                    placeholder="000.000.000-00"
                                )
                            with col_rg:
                                injured_rg = st.text_input(
                                    "RG:",
                                    value=involved_injured[i].get('rg', '') if i < len(involved_injured) else '',
                                    key=f"injured_rg_{i}"
                                )
                            with col_estado:
                                marital_status_options = ["", "Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)", "União Estável"]
                                current_marital = involved_injured[i].get('marital_status', '') if i < len(involved_injured) else ''
                                try:
                                    marital_index = marital_status_options.index(current_marital) if current_marital in marital_status_options else 0
                                except (ValueError, AttributeError):
                                    marital_index = 0
                                # Garante que o index está dentro dos limites
                                marital_index = max(0, min(marital_index, len(marital_status_options) - 1))
                                injured_marital_status = st.selectbox(
                                    "Estado Civil:",
                                    options=marital_status_options,
                                    index=marital_index,
                                    key=f"injured_marital_{i}",
                                    disabled=False
                                )
                            
                            # Linha 3: Naturalidade | Número de Filhos | [vazio]
                            col_natural, col_filhos, col_vazio = st.columns(3)
                            with col_natural:
                                injured_birthplace = st.text_input(
                                    "Naturalidade:",
                                    value=involved_injured[i].get('birthplace', '') if i < len(involved_injured) else '',
                                    key=f"injured_birthplace_{i}",
                                    placeholder="Ex: São Paulo"
                                )
                            with col_filhos:
                                injured_children_count = st.number_input(
                                    "Número de filhos:",
                                    min_value=0,
                                    max_value=20,
                                    value=int(involved_injured[i].get('children_count', 0)) if i < len(involved_injured) and involved_injured[i].get('children_count') else 0,
                                    key=f"injured_children_{i}"
                                )
                            with col_vazio:
                                st.empty()  # Espaço vazio
                            
                            # Linha 4: Tipo de Lesão | Parte do Corpo | Dias Perdidos
                            col_lesao, col_parte, col_dias = st.columns(3)
                            with col_lesao:
                                injured_injury_type = st.text_input(
                                    "Tipo de Lesão:",
                                    value=involved_injured[i].get('injury_type', '') if i < len(involved_injured) else '',
                                    key=f"injured_injury_type_{i}"
                                )
                            with col_parte:
                                injured_body_part = st.text_input(
                                    "Parte do Corpo:",
                                    value=involved_injured[i].get('body_part', '') if i < len(involved_injured) else '',
                                    key=f"injured_body_part_{i}",
                                    placeholder="Ex: Pé direito"
                                )
                            with col_dias:
                                injured_lost_days = st.number_input(
                                    "Dias Perdidos:",
                                    min_value=0,
                                    max_value=10000,
                                    value=int(involved_injured[i].get('lost_days', 0)) if i < len(involved_injured) and involved_injured[i].get('lost_days') else 0,
                                    key=f"injured_lost_days_{i}"
                                )
                            
                            # Linha 5: Data ASO | N° CAT | Fatalidade
                            col_aso, col_cat, col_fatal = st.columns(3)
                            with col_aso:
                                injured_aso_val = None
                                if i < len(involved_injured) and involved_injured[i].get('aso_date'):
                                    try:
                                        injured_aso_val = pd.to_datetime(involved_injured[i].get('aso_date')).date()
                                    except:
                                        injured_aso_val = None
                                injured_aso = st.date_input(
                                    "Data ASO:",
                                    value=injured_aso_val,
                                    key=f"injured_aso_{i}"
                                )
                            with col_cat:
                                injured_cat = st.text_input(
                                    "N° CAT:",
                                    value=involved_injured[i].get('cat_number', '') if i < len(involved_injured) else '',
                                    key=f"injured_cat_{i}"
                                )
                            with col_fatal:
                                injured_is_fatal = st.checkbox(
                                    "Fatalidade",
                                    value=bool(involved_injured[i].get('is_fatal', False)) if i < len(involved_injured) else False,
                                    key=f"injured_fatal_{i}"
                                )
                                st.markdown("Sim ☒  Não ☐" if injured_is_fatal else "Sim ☐  Não ☒")
                            
                            # Linha 6: Tipo (Empregado/Contratado/Terceiros)
                            col_tipo, col_empresa, col_role = st.columns(3)
                            with col_tipo:
                                employment_type_options = ["", "Empregado", "Contratado", "Terceiros/Comunidade"]
                                current_employment = involved_injured[i].get('employment_type', '') if i < len(involved_injured) else ''
                                try:
                                    employment_index = employment_type_options.index(current_employment) if current_employment in employment_type_options else 0
                                except (ValueError, AttributeError):
                                    employment_index = 0
                                # Garante que o index está dentro dos limites
                                employment_index = max(0, min(employment_index, len(employment_type_options) - 1))
                                injured_employment_type = st.selectbox(
                                    "Tipo:",
                                    options=employment_type_options,
                                    index=employment_index,
                                    key=f"injured_employment_{i}",
                                    disabled=False
                                )
                            with col_empresa:
                                injured_company = st.text_input(
                                    "Empresa:",
                                    value=involved_injured[i].get('company', '') if i < len(involved_injured) else '',
                                    key=f"injured_company_{i}"
                                )
                            with col_role:
                                injured_role = st.text_input(
                                    "Cargo/Função:",
                                    value=involved_injured[i].get('job_title', '') if i < len(involved_injured) else '',
                                    key=f"injured_role_{i}"
                                )
                            
                            # Histórico Acidente Anterior
                            injured_previous = st.checkbox(
                                "Histórico Acidente Anterior",
                                value=bool(involved_injured[i].get('previous_accident_history', False)) if i < len(involved_injured) else False,
                                key=f"injured_previous_{i}"
                            )
                            st.markdown("Sim ☒  Não ☐" if injured_previous else "Sim ☐  Não ☒")
                            
                            # Capacitações/Validade
                            st.markdown("**📚 Capacitações/Validade:**")
                            
                            # Controla número de capacitações usando input numérico (dentro do form)
                            num_certs_key = f"num_certs_{i}_{accident_id}"
                            
                            # Inicializa número de capacitações baseado no que existe no banco
                            if num_certs_key not in st.session_state:
                                existing_certs = involved_injured[i].get('certifications', '') if i < len(involved_injured) else ''
                                if existing_certs:
                                    if ';' in existing_certs:
                                        num_existing = len([c for c in existing_certs.split(';') if c.strip()])
                                        st.session_state[num_certs_key] = max(1, num_existing)
                                    else:
                                        st.session_state[num_certs_key] = 1 if existing_certs.strip() else 0
                                else:
                                    st.session_state[num_certs_key] = 0
                            
                            num_certifications = st.number_input(
                                "Número de Capacitações:",
                                min_value=0,
                                max_value=20,
                                value=st.session_state.get(num_certs_key, 0),
                                key=f"num_cert_input_{i}_{accident_id}",
                                help="Selecione quantas capacitações deseja adicionar"
                            )
                            
                            # Atualiza session_state se mudou
                            if num_certifications != st.session_state.get(num_certs_key, 0):
                                st.session_state[num_certs_key] = num_certifications
                            
                            # Carrega capacitações existentes
                            certs_key = f"injured_certifications_{i}_{accident_id}"
                            if certs_key not in st.session_state:
                                existing_certs = involved_injured[i].get('certifications', '') if i < len(involved_injured) else ''
                                if existing_certs:
                                    certs_list = []
                                    if ';' in existing_certs:
                                        for cert_str in existing_certs.split(';'):
                                            if '|' in cert_str:
                                                parts = cert_str.split('|', 1)
                                                certs_list.append({'name': parts[0].strip(), 'validity': parts[1].strip()})
                                    else:
                                        if existing_certs.strip():
                                            certs_list.append({'name': existing_certs.strip(), 'validity': ''})
                                    # Completa até o número necessário
                                    while len(certs_list) < num_certifications:
                                        certs_list.append({'name': '', 'validity': ''})
                                    st.session_state[certs_key] = certs_list
                                else:
                                    st.session_state[certs_key] = [{'name': '', 'validity': ''} for _ in range(num_certifications)]
                            
                            # Ajusta lista para ter o número correto de capacitações
                            certifications_list = st.session_state.get(certs_key, [])
                            while len(certifications_list) < num_certifications:
                                certifications_list.append({'name': '', 'validity': ''})
                            if len(certifications_list) > num_certifications:
                                certifications_list = certifications_list[:num_certifications]
                            st.session_state[certs_key] = certifications_list
                            
                            # Exibe campos de capacitações
                            updated_certs = []
                            for cert_idx in range(num_certifications):
                                if cert_idx < len(certifications_list):
                                    cert = certifications_list[cert_idx]
                                else:
                                    cert = {'name': '', 'validity': ''}
                                
                                col_cert_name, col_cert_date = st.columns([3, 2])
                                with col_cert_name:
                                    cert_name = st.text_input(
                                        f"Capacitação {cert_idx + 1}:",
                                        value=cert.get('name', ''),
                                        key=f"cert_name_{i}_{cert_idx}_{accident_id}",
                                        placeholder="Ex: NR-10, NR-35, Primeiros Socorros..."
                                    )
                                with col_cert_date:
                                    cert_validity_val = None
                                    if cert.get('validity'):
                                        try:
                                            cert_validity_val = pd.to_datetime(cert.get('validity')).date()
                                        except:
                                            cert_validity_val = None
                                    cert_validity = st.date_input(
                                        f"Validade {cert_idx + 1}:",
                                        value=cert_validity_val,
                                        min_value=date(2000, 1, 1),
                                        max_value=date(2100, 12, 31),
                                        key=f"cert_validity_{i}_{cert_idx}_{accident_id}",
                                        help="Data de validade da capacitação"
                                    )
                                
                                updated_certs.append({
                                    'name': cert_name,
                                    'validity': cert_validity.isoformat() if cert_validity else ''
                                })
                            
                            # Converte lista para string formatada para salvar no banco
                            # Formato: "Nome|Validade;Nome|Validade"
                            certs_string = ';'.join([
                                f"{c['name']}|{c['validity']}" 
                                for c in updated_certs 
                                if c.get('name', '').strip()
                            ])
                            injured_certifications = certs_string if certs_string else None
                            
                            if injured_name:
                                injured.append({
                                    'person_type': 'Injured',
                                    'name': injured_name,
                                    'registration_id': injured_reg or None,
                                    'job_title': injured_role or None,
                                    'company': injured_company or None,
                                    'age': injured_age if injured_age else None,
                                    'aso_date': injured_aso.isoformat() if injured_aso else None,
                                    'birth_date': injured_birth_date.isoformat() if injured_birth_date else None,
                                    'rg': injured_rg or None,
                                    'marital_status': injured_marital_status if injured_marital_status else None,
                                    'birthplace': injured_birthplace or None,
                                    'children_count': injured_children_count if injured_children_count else None,
                                    'injury_type': injured_injury_type or None,
                                    'body_part': injured_body_part or None,
                                    'lost_days': injured_lost_days if injured_lost_days else None,
                                    'cat_number': injured_cat or None,
                                    'is_fatal': injured_is_fatal,
                                    'employment_type': injured_employment_type if injured_employment_type else None,
                                    'previous_accident_history': injured_previous,
                                    'certifications': injured_certifications or None
                                })
                    else:
                        # Para múltiplas vítimas, mantém formulário simplificado
                        with st.container():
                            col1, col2 = st.columns(2)
                            with col1:
                                injured_name = st.text_input(f"Nome {i+1}:", value=involved_injured[i].get('name', '') if i < len(involved_injured) else '', key=f"injured_name_{i}")
                                injured_reg = st.text_input(f"Matrícula/CPF {i+1}:", value=involved_injured[i].get('registration_id', '') if i < len(involved_injured) else '', key=f"injured_reg_{i}")
                                injured_company = st.text_input(f"Empresa {i+1}:", value=involved_injured[i].get('company', '') if i < len(involved_injured) else '', key=f"injured_company_{i}")
                            with col2:
                                injured_role = st.text_input(f"Cargo/Função {i+1}:", value=involved_injured[i].get('job_title', '') if i < len(involved_injured) else '', key=f"injured_role_{i}")
                                injured_age_val = involved_injured[i].get('age') if i < len(involved_injured) and involved_injured[i].get('age') else 0
                                injured_age = st.number_input(f"Idade {i+1}:", min_value=0, max_value=100, value=int(injured_age_val) if injured_age_val else 0, key=f"injured_age_{i}")
                                
                                injured_aso_val = None
                                if i < len(involved_injured) and involved_injured[i].get('aso_date'):
                                    try:
                                        injured_aso_val = pd.to_datetime(involved_injured[i].get('aso_date')).date()
                                    except:
                                        injured_aso_val = None
                                injured_aso = st.date_input(f"Data ASO {i+1}:", value=injured_aso_val, key=f"injured_aso_{i}")
                            
                            if injured_name:
                                injured.append({
                                    'person_type': 'Injured',
                                    'name': injured_name,
                                    'registration_id': injured_reg or None,
                                    'job_title': injured_role or None,
                                    'company': injured_company or None,
                                    'age': injured_age if injured_age else None,
                                    'aso_date': injured_aso.isoformat() if injured_aso else None
                                })
            
            # Testemunhas
            with st.expander("👁️ Testemunhas", expanded=True):
                # Usa o valor do session_state (definido fora do form)
                num_witnesses = st.session_state.get(f"num_witnesses_{accident_id}", len(involved_witnesses))
                
                if num_witnesses == 0:
                    st.info("ℹ️ Configure a quantidade de testemunhas acima para começar a preencher os dados.")
                
                witnesses = []
                for i in range(num_witnesses):
                    with st.container():
                        witness_name = st.text_input(f"Nome {i+1}:", value=involved_witnesses[i].get('name', '') if i < len(involved_witnesses) else '', key=f"witness_name_{i}")
                        witness_reg = st.text_input(f"Matrícula/CPF {i+1}:", value=involved_witnesses[i].get('registration_id', '') if i < len(involved_witnesses) else '', key=f"witness_reg_{i}")
                        if witness_name:
                            witnesses.append({
                                'person_type': 'Witness',
                                'name': witness_name,
                                'registration_id': witness_reg or None
                            })
            
            # ========== SEÇÃO 5: COMISSÃO DE INVESTIGAÇÃO ==========
            with st.expander("👔 Seção 5: Comissão de Investigação", expanded=True):
                st.markdown("**Membros da Comissão de Investigação**")
                
                # Usa o valor do session_state (definido fora do form)
                num_commission = st.session_state[num_commission_key]
                
                if num_commission == 0:
                    st.info("💡 **Configure a quantidade de membros no campo acima (fora do formulário)** para começar a preencher os dados.")
                else:
                    st.info(f"📝 **Preencha os dados dos {num_commission} membro(s) da comissão:**")
                
                commission = []
                for i in range(num_commission):
                    with st.container():
                        col1, col2 = st.columns(2)
                        with col1:
                            comm_name = st.text_input(f"Nome {i+1}:", value=involved_commission[i].get('name', '') if i < len(involved_commission) else '', key=f"comm_name_{i}")
                            comm_reg = st.text_input(f"Matrícula/ID {i+1}:", value=involved_commission[i].get('registration_id', '') if i < len(involved_commission) else '', key=f"comm_reg_{i}")
                        with col2:
                            comm_job = st.text_input(f"Cargo/Função {i+1}:", value=involved_commission[i].get('job_title', '') if i < len(involved_commission) else '', key=f"comm_job_{i}", help="Cargo ou função profissional do membro")
                            comm_role_options = ["", "Coordenador", "Membro", "Relator", "Secretário", "Outro"]
                            comm_role_current = ""
                            if i < len(involved_commission):
                                # Tenta buscar de commission_role primeiro, depois training_status (para compatibilidade)
                                comm_role_current = involved_commission[i].get('commission_role') or involved_commission[i].get('training_status')
                                if comm_role_current and isinstance(comm_role_current, str):
                                    comm_role_current = comm_role_current
                                else:
                                    comm_role_current = ""
                            comm_role_index = comm_role_options.index(comm_role_current) if comm_role_current in comm_role_options else 0
                            comm_role = st.selectbox(
                                f"Função na Comissão {i+1}:",
                                options=comm_role_options,
                                index=comm_role_index,
                                key=f"comm_role_{i}",
                                help="Função específica do membro na comissão de investigação"
                            )
                            if comm_role == "Outro":
                                comm_role_other = st.text_input(f"Especificar função {i+1}:", value="", key=f"comm_role_other_{i}")
                                comm_role = comm_role_other if comm_role_other else comm_role
                        
                        if comm_name:
                            commission.append({
                                'person_type': 'Commission_Member',
                                'name': comm_name,
                                'registration_id': comm_reg or None,
                                'job_title': comm_job or None,  # Cargo profissional
                                'commission_role': comm_role or None  # Função na comissão (Coordenador, Membro, Relator, etc.)
                            })
            
            # Inicializa variáveis de processo (caso a seção não tenha sido exibida)
            if not show_process_details:
                product_released = None
                volume_released = 0.0
                volume_recovered = 0.0
                release_duration_hours = 0.0
                equipment_involved = None
                area_affected = None
            
            # Botão de salvar
            col_save, col_empty = st.columns([1, 1])
            with col_save:
                if st.form_submit_button("💾 Salvar Dados e Continuar", type="primary", width='stretch'):
                    # Atualiza dados do acidente - TODOS os campos válidos
                    # Garante que valores booleanos sejam sempre True ou False (nunca None)
                    update_data = {
                        'title': title if title else investigation.get('title', 'Acidente sem título'),
                        'description': description if description else None,
                        'registry_number': registry_number if registry_number else None,
                        'base_location': base_location if base_location else None,
                        'site_id': selected_site_id,
                        'occurrence_date': occurrence_datetime.isoformat() if occurrence_datetime else None,
                        'type': accident_type,  # Tipo do acidente: fatal, lesao, sem_lesao
                        'class_injury': bool(class_injury),
                        'class_community': bool(class_community),
                        'class_environment': bool(class_environment),
                        'class_process_safety': bool(class_process_safety),
                        'class_asset_damage': bool(class_asset_damage),
                        'class_near_miss': bool(class_near_miss),
                        'severity_level': severity_level if severity_level else None,
                        'estimated_loss_value': estimated_loss_value if estimated_loss_value > 0 else None
                    }
                    
                    # Adiciona dados de processo (sempre inclui, mesmo se None)
                    update_data.update({
                        'product_released': product_released if product_released else None,
                        'volume_released': volume_released if volume_released and volume_released > 0 else None,
                        'volume_recovered': volume_recovered if volume_recovered and volume_recovered > 0 else None,
                        'release_duration_hours': release_duration_hours if release_duration_hours and release_duration_hours > 0 else None,
                        'equipment_involved': equipment_involved if equipment_involved else None,
                        'area_affected': area_affected if area_affected and area_affected != "" else None
                    })
                    
                    # Adiciona campos de Segurança de Processo (se aplicável)
                    if class_process_safety:
                        # Campos de incêndio
                        update_data.update({
                            'has_fire': has_fire,
                            'fire_area': fire_area if fire_area else None,
                            'fire_duration_hours': fire_duration_hours if fire_duration_hours and fire_duration_hours > 0 else None,
                            'fire_observation': fire_observation if fire_observation else None,
                        })
                        
                        # Campos de explosão
                        update_data.update({
                            'has_explosion': has_explosion,
                            'explosion_type': explosion_type if explosion_type else None,
                            'explosion_area': explosion_area if explosion_area else None,
                            'explosion_duration_hours': explosion_duration_hours if explosion_duration_hours and explosion_duration_hours > 0 else None,
                            'explosion_observation': explosion_observation if explosion_observation else None,
                        })
                        
                        # Observação de segurança de processo
                        update_data.update({
                            'process_safety_observation': process_safety_observation if process_safety_observation else None,
                        })
                        
                        # Campos da transportadora
                        if transporter_not_applicable:
                            update_data.update({
                                'transporter_name': None,
                                'transporter_cnpj': None,
                                'transporter_contract_number': None,
                                'transporter_contract_start': None,
                                'transporter_contract_end': None,
                            })
                        else:
                            update_data.update({
                                'transporter_name': transporter_name if transporter_name else None,
                                'transporter_cnpj': transporter_cnpj if transporter_cnpj else None,
                                'transporter_contract_number': transporter_contract_number if transporter_contract_number else None,
                                'transporter_contract_start': transporter_contract_start.isoformat() if transporter_contract_start else None,
                                'transporter_contract_end': transporter_contract_end.isoformat() if transporter_contract_end else None,
                            })
                        
                        # Campos de perdas
                        update_data.update({
                            'loss_product': loss_product if loss_product > 0 else None,
                            'loss_material': loss_material if loss_material > 0 else None,
                            'loss_vacuum_truck': loss_vacuum_truck if loss_vacuum_truck > 0 else None,
                            'loss_indirect_contractor': loss_indirect_contractor if loss_indirect_contractor > 0 else None,
                            'loss_overtime_hours': loss_overtime_hours if loss_overtime_hours > 0 else None,
                            'loss_civil_works': loss_civil_works if loss_civil_works > 0 else None,
                            'loss_waste_containers': loss_waste_containers if loss_waste_containers > 0 else None,
                            'loss_mechanical_works': loss_mechanical_works if loss_mechanical_works > 0 else None,
                            'loss_mobilization': loss_mobilization if loss_mobilization > 0 else None,
                            'loss_total': loss_total if loss_total > 0 else None,
                        })
                    
                    # Logs para debug (terminal)
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"[INVESTIGATION] Salvando dados do acidente {accident_id}")
                    logger.info(f"[INVESTIGATION] Campos de update: {list(update_data.keys())}")
                    logger.info(f"[INVESTIGATION] Total de drivers: {len(drivers)}")
                    logger.info(f"[INVESTIGATION] Total de injured: {len(injured)}")
                    logger.info(f"[INVESTIGATION] Total de witnesses: {len(witnesses)}")
                    logger.info(f"[INVESTIGATION] Total de commission: {len(commission)}")
                    
                    # Salva dados do acidente
                    try:
                        success = update_accident(accident_id, **update_data)
                        
                        if success:
                            st.success("✅ Dados do acidente salvos com sucesso!")
                            
                            # Salva pessoas envolvidas (incluindo comissão)
                            all_people = drivers + injured + witnesses + commission
                            logger.info(f"[INVESTIGATION] Total de pessoas para salvar: {len(all_people)}")
                            logger.info(f"[INVESTIGATION] Tipos: {[p.get('person_type') for p in all_people]}")
                            
                            if all_people:
                                people_success = upsert_involved_people(accident_id, all_people)
                                
                                if people_success:
                                    logger.info(f"[INVESTIGATION] Dados salvos com sucesso para acidente {accident_id}")
                                    st.success(f"✅ {len(all_people)} pessoa(s) envolvida(s) salva(s) com sucesso!")
                                else:
                                    logger.warning(f"[INVESTIGATION] Dados do acidente salvos, mas houve problema ao salvar pessoas envolvidas")
                                    st.warning("⚠️ Dados do acidente salvos, mas houve problema ao salvar pessoas envolvidas.")
                                    st.info("ℹ️ Verifique os logs no terminal para mais detalhes sobre o erro.")
                            else:
                                logger.info("[INVESTIGATION] Nenhuma pessoa envolvida para salvar")
                                st.info("ℹ️ Nenhuma pessoa envolvida registrada.")
                            
                            # Avança para próximo passo
                            st.session_state['current_step'] = 1
                            st.rerun()
                        else:
                            logger.error(f"[INVESTIGATION] Erro ao salvar dados do acidente {accident_id}")
                            st.error("❌ Erro ao salvar dados do acidente. Verifique os logs no terminal.")
                    except Exception as save_error:
                        logger.error(f"[INVESTIGATION] Exceção ao salvar: {str(save_error)}", exc_info=True)
                        error_msg = str(save_error).lower()
                        if 'permission' in error_msg or 'policy' in error_msg or 'rls' in error_msg:
                            st.error("❌ Erro de permissão (RLS). Verifique se você tem acesso a este acidente.")
                        else:
                            st.error(f"❌ Erro ao salvar: {str(save_error)}")
            
            # Upload de evidências (separado do formulário)
        st.divider()
        st.markdown("### 📷 Adicionar Evidências (Fotos/Vídeos)")
        with st.expander("➕ Upload de Fotos/Vídeos", expanded=False):
            uploaded_file = st.file_uploader(
                "Selecione uma imagem:",
                type=['png', 'jpg', 'jpeg'],
                help="📸 Faça upload de fotos que documentem o acidente. Quanto mais evidências, melhor a investigação.",
                key="evidence_uploader"
            )
            evidence_description = st.text_area(
                "O que esta imagem mostra?",
                placeholder="Descreva o que a imagem documenta...",
                height=80,
                key="evidence_description"
            )
            
            if st.button("📤 Enviar Evidência", type="primary", key="upload_evidence_btn"):
                if uploaded_file and evidence_description:
                    file_bytes = uploaded_file.read()
                    result = upload_evidence_image(accident_id, file_bytes, uploaded_file.name, evidence_description)
                    if result:
                        st.success("✅ Evidência enviada com sucesso!")
                        st.rerun()
                else:
                    st.warning("⚠️ Selecione um arquivo e forneça uma descrição")
        
        # Galeria
        st.markdown("### 🖼️ Galeria de Evidências")
        evidence_list = get_evidence(accident_id)
        
        if evidence_list:
            cols_per_row = 3
            for i in range(0, len(evidence_list), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, col in enumerate(cols):
                    if i + j < len(evidence_list):
                        evidence = evidence_list[i + j]
                        with col:
                            image_url = evidence.get('image_url')
                            if image_url:
                                # Prioriza download direto do Supabase Storage (mais confiável)
                                image_loaded = False
                                
                                # Extrai o path da URL
                                path = None
                                if '/storage/v1/object/public/evidencias/' in image_url:
                                    path = image_url.split('/storage/v1/object/public/evidencias/')[1]
                                elif '/evidencias/' in image_url:
                                    parts = image_url.split('/evidencias/')
                                    if len(parts) > 1:
                                        path = parts[1]
                                
                                # Tenta baixar do Supabase Storage primeiro
                                if path:
                                    try:
                                        from managers.supabase_config import get_service_role_client
                                        supabase = get_service_role_client()
                                        if supabase:
                                            image_bytes = supabase.storage.from_('evidencias').download(path)
                                            if image_bytes:
                                                st.image(
                                                    image_bytes, 
                                                    width='stretch', 
                                                    caption=evidence.get('description', 'Sem descrição')
                                                )
                                                image_loaded = True
                                    except Exception as e:
                                        # Se falhar, continua para tentar outros métodos
                                        pass
                                
                                # Se não carregou pelo download direto, tenta pela URL
                                if not image_loaded:
                                    try:
                                        st.image(
                                            image_url, 
                                            width='stretch', 
                                            caption=evidence.get('description', 'Sem descrição')
                                        )
                                        image_loaded = True
                                    except Exception as e:
                                        # Se falhar, tenta baixar via HTTP
                                        try:
                                            response = requests.get(image_url, timeout=10)
                                            if response.status_code == 200:
                                                st.image(
                                                    response.content, 
                                                    width='stretch', 
                                                    caption=evidence.get('description', 'Sem descrição')
                                                )
                                                image_loaded = True
                                        except Exception as e2:
                                            pass
                                
                                # Se nada funcionou, mostra erro e link
                                if not image_loaded:
                                    st.error("⚠️ Não foi possível carregar a imagem")
                                    st.markdown(f"**URL:** [{image_url}]({image_url})")
                                    if path:
                                        st.caption(f"Path: {path}")
                                    st.caption(evidence.get('description', 'Sem descrição'))
                            else:
                                st.warning("⚠️ URL da imagem não disponível")
                                st.caption(evidence.get('description', 'Sem descrição'))
        else:
            st.info("📭 Nenhuma evidência adicionada ainda. Adicione fotos para documentar o acidente.")
        
        # Navegação
        col_prev, col_next = st.columns([1, 1])
        with col_next:
            if st.button("➡️ Próximo: Linha do Tempo", type="primary", width='stretch'):
                st.session_state['current_step'] = 1
                st.rerun()
    
    # ========== PASSO 2: LINHA DO TEMPO ==========
    elif st.session_state['current_step'] == 1:
        st.header("📅 Passo 2: Linha do Tempo")
        st.markdown("**Quando aconteceu?** Reconstrua a sequência temporal dos eventos.")
        
        # Formulário para adicionar evento
        with st.expander("➕ Adicionar Evento", expanded=True):
            col_date, col_time = st.columns(2)
            with col_date:
                event_date = st.date_input("Data do evento:", value=date.today(), key="timeline_date")
            with col_time:
                event_time_input = st.time_input("Hora do evento:", value=time(12, 0), key="timeline_time")
            
            # Combina data e hora (sem timezone - mantém horário como inserido pelo usuário)
            event_datetime = datetime.combine(event_date, event_time_input)
            
            event_description = st.text_area(
                "O que aconteceu neste momento?",
                placeholder="Descreva o evento...",
                height=100,
                help="📝 Seja específico: o que aconteceu, quem estava presente, quais ações foram tomadas?",
                key="timeline_description"
            )
            
            if st.button("➕ Adicionar Evento", type="primary", key="add_timeline_btn"):
                if event_description:
                    if add_timeline_event(accident_id, event_datetime, event_description):
                        st.success("✅ Evento adicionado à timeline!")
                        st.rerun()
                else:
                    st.warning("⚠️ Forneça uma descrição do evento")
        
        # Timeline visual
        st.markdown("### ⏱️ Cronologia de Eventos")
        timeline_events = get_timeline(accident_id)
        
        if timeline_events:
            timeline_df = pd.DataFrame(timeline_events)
            timeline_df['event_time'] = pd.to_datetime(timeline_df['event_time'])
            timeline_df = timeline_df.sort_values('event_time')
            
            for idx, event in timeline_df.iterrows():
                event_id = str(event.get('id', ''))
                event_time_raw = event.get('event_time')
                description_raw = event.get('description', '')
                
                # Converte para tipos corretos, removendo timezone para manter horário original
                if isinstance(event_time_raw, pd.Timestamp):
                    event_time_dt = event_time_raw
                else:
                    event_time_dt = pd.to_datetime(event_time_raw)
                
                # Remove timezone se existir para manter o horário original
                if event_time_dt.tz is not None:
                    event_time_dt = event_time_dt.tz_localize(None)
                
                event_time = event_time_dt.to_pydatetime()
                
                description = str(description_raw) if description_raw else ''
                
                # Expander para cada evento com opções de editar/deletar
                event_preview = description[:50] + '...' if len(description) > 50 else description
                with st.expander(f"🕐 {event_time.strftime('%d/%m/%Y %H:%M')} - {event_preview}", expanded=False):
                    # Campos de edição
                    col_date_edit, col_time_edit = st.columns(2)
                    with col_date_edit:
                        edit_date = st.date_input(
                            "Data:",
                            value=event_time.date(),
                            key=f"edit_date_{event_id}"
                        )
                    with col_time_edit:
                        edit_time = st.time_input(
                            "Hora:",
                            value=event_time.time(),
                            key=f"edit_time_{event_id}"
                        )
                    
                    # Combina data e hora (sem timezone - mantém horário como inserido pelo usuário)
                    edit_datetime = datetime.combine(edit_date, edit_time)
                    
                    edit_description = st.text_area(
                        "Descrição:",
                        value=description,
                        key=f"edit_desc_{event_id}",
                        height=100
                    )
                    
                    # Botões de ação
                    col_save, col_delete = st.columns([1, 1])
                    with col_save:
                        if st.button("💾 Salvar Alterações", key=f"save_{event_id}"):
                            desc_clean = (edit_description or '').strip()
                            if desc_clean:
                                if update_timeline_event(event_id, edit_datetime, desc_clean):
                                    st.success("✅ Evento atualizado!")
                                    st.rerun()
                            else:
                                st.warning("⚠️ A descrição não pode estar vazia")
                    
                    with col_delete:
                        if st.button("🗑️ Deletar", key=f"delete_{event_id}"):
                            if delete_timeline_event(event_id):
                                st.success("✅ Evento removido!")
                                st.rerun()
        else:
            st.info("📭 Nenhum evento adicionado ainda. Adicione eventos na ordem cronológica.")
        
        # Linha do tempo de ações da comissão
        st.divider()
        st.markdown("### 👥 Ações da Comissão")
        st.markdown("**O que a comissão fez?** Registre as ações executadas pela comissão durante a investigação.")
        
        # Formulário para adicionar ação da comissão
        with st.expander("➕ Adicionar Ação da Comissão", expanded=True):
            col_date_action, col_time_action = st.columns(2)
            with col_date_action:
                action_date = st.date_input("Data da ação:", value=date.today(), key="action_date")
            with col_time_action:
                action_time_input = st.time_input("Hora da ação:", value=time(12, 0), key="action_time")
            
            # Combina data e hora (sem timezone - mantém horário como inserido pelo usuário)
            action_datetime = datetime.combine(action_date, action_time_input)
            
            col_type, col_resp = st.columns(2)
            with col_type:
                action_type = st.selectbox(
                    "Tipo de ação:",
                    options=["", "Entrevista", "Inspeção", "Análise", "Reunião", "Coleta de Evidências", "Outro"],
                    key="action_type",
                    help="Selecione o tipo de ação executada"
                )
            with col_resp:
                responsible_person = st.text_input(
                    "Responsável:",
                    placeholder="Nome da pessoa responsável",
                    key="responsible_person",
                    help="Nome da pessoa que executou ou coordenou a ação"
                )
            
            action_description = st.text_area(
                "O que foi feito?",
                placeholder="Descreva a ação executada pela comissão...",
                height=100,
                help="📝 Descreva detalhadamente a ação: o que foi feito, quem participou, quais resultados foram obtidos?",
                key="action_description"
            )
            
            if st.button("➕ Adicionar Ação", type="primary", key="add_action_btn"):
                if action_description:
                    if add_commission_action(accident_id, action_datetime, action_description, action_type if action_type else None, responsible_person if responsible_person else None):
                        st.success("✅ Ação adicionada à linha do tempo!")
                        st.rerun()
                else:
                    st.warning("⚠️ Forneça uma descrição da ação")
        
        # Timeline visual de ações
        st.markdown("### ⏱️ Cronologia de Ações da Comissão")
        commission_actions = get_commission_actions(accident_id)
        
        if commission_actions:
            actions_df = pd.DataFrame(commission_actions)
            actions_df['action_time'] = pd.to_datetime(actions_df['action_time'])
            actions_df = actions_df.sort_values('action_time')
            
            for idx, action in actions_df.iterrows():
                action_id = str(action.get('id', ''))
                action_time_raw = action.get('action_time')
                description_raw = action.get('description', '')
                action_type_raw = action.get('action_type', '')
                responsible_raw = action.get('responsible_person', '')
                
                # Converte para tipos corretos, removendo timezone para manter horário original
                if isinstance(action_time_raw, pd.Timestamp):
                    action_time_dt = action_time_raw
                else:
                    action_time_dt = pd.to_datetime(action_time_raw)
                
                # Remove timezone se existir para manter o horário original
                if action_time_dt.tz is not None:
                    action_time_dt = action_time_dt.tz_localize(None)
                
                action_time = action_time_dt.to_pydatetime()
                
                description = str(description_raw) if description_raw else ''
                action_type = str(action_type_raw) if action_type_raw else ''
                responsible = str(responsible_raw) if responsible_raw else ''
                
                # Expander para cada ação com opções de editar/deletar
                action_preview = description[:50] + '...' if len(description) > 50 else description
                action_type_label = f" [{action_type}]" if action_type else ""
                responsible_label = f" - {responsible}" if responsible else ""
                with st.expander(f"👥 {action_time.strftime('%d/%m/%Y %H:%M')}{action_type_label}{responsible_label} - {action_preview}", expanded=False):
                    # Campos de edição
                    col_date_edit, col_time_edit = st.columns(2)
                    with col_date_edit:
                        edit_date = st.date_input(
                            "Data:",
                            value=action_time.date(),
                            key=f"edit_action_date_{action_id}"
                        )
                    with col_time_edit:
                        edit_time = st.time_input(
                            "Hora:",
                            value=action_time.time(),
                            key=f"edit_action_time_{action_id}"
                        )
                    
                    # Combina data e hora (sem timezone - mantém horário como inserido pelo usuário)
                    edit_datetime = datetime.combine(edit_date, edit_time)
                    
                    col_type_edit, col_resp_edit = st.columns(2)
                    with col_type_edit:
                        edit_action_type = st.selectbox(
                            "Tipo de ação:",
                            options=["", "Entrevista", "Inspeção", "Análise", "Reunião", "Coleta de Evidências", "Outro"],
                            index=0 if not action_type else (["", "Entrevista", "Inspeção", "Análise", "Reunião", "Coleta de Evidências", "Outro"].index(action_type) if action_type in ["", "Entrevista", "Inspeção", "Análise", "Reunião", "Coleta de Evidências", "Outro"] else 0),
                            key=f"edit_action_type_{action_id}"
                        )
                    with col_resp_edit:
                        edit_responsible = st.text_input(
                            "Responsável:",
                            value=responsible,
                            key=f"edit_responsible_{action_id}"
                        )
                    
                    edit_description = st.text_area(
                        "Descrição:",
                        value=description,
                        key=f"edit_action_desc_{action_id}",
                        height=100
                    )
                    
                    # Botões de ação
                    col_save, col_delete = st.columns([1, 1])
                    with col_save:
                        if st.button("💾 Salvar Alterações", key=f"save_action_{action_id}"):
                            desc_clean = (edit_description or '').strip()
                            if desc_clean:
                                if update_commission_action(action_id, edit_datetime, desc_clean, edit_action_type if edit_action_type else None, edit_responsible if edit_responsible else None):
                                    st.success("✅ Ação atualizada!")
                                    st.rerun()
                            else:
                                st.warning("⚠️ A descrição não pode estar vazia")
                    
                    with col_delete:
                        if st.button("🗑️ Deletar", key=f"delete_action_{action_id}"):
                            if delete_commission_action(action_id):
                                st.success("✅ Ação removida!")
                                st.rerun()
        else:
            st.info("📭 Nenhuma ação registrada ainda. Adicione ações executadas pela comissão.")
        
        # Navegação
        col_prev, col_next = st.columns([1, 1])
        with col_prev:
            if st.button("⬅️ Anterior: Fatos & Fotos", width='stretch'):
                st.session_state['current_step'] = 0
                st.rerun()
        with col_next:
            if st.button("➡️ Próximo: Árvore de Porquês", type="primary", width='stretch'):
                st.session_state['current_step'] = 2
                st.rerun()
    
    # ========== PASSO 3: ÁRVORE DE PORQUÊS ==========
    elif st.session_state['current_step'] == 2:
        st.header("🌳 Passo 3: Árvore de Porquês")
        st.markdown("**Por que aconteceu?** Identifique todas as causas possíveis usando a metodologia de árvore de falhas.")
        
        # Verifica/cria nó raiz automaticamente
        root_node = get_root_node(accident_id)
        if not root_node:
            root_label = investigation.get('title', 'Evento Principal')
            root_id = create_root_node(accident_id, root_label)
            if root_id:
                st.success(f"✅ Árvore iniciada: {root_label}")
                st.rerun()
        
        # Constrói JSON hierárquico
        tree_json = build_fault_tree_json(accident_id)
        
        # Visualização da árvore
        st.markdown("### 🌳 Estrutura da Árvore de Causas")
        
        if tree_json:
            # Usa visualização HTML bonita como padrão
            tree_html = render_fault_tree_html(tree_json)
            if tree_html:
                # Renderiza HTML usando st.markdown com unsafe_allow_html
                st.markdown(tree_html, unsafe_allow_html=True)
                
                # Legenda de cores (menor)
                st.markdown("""
                <div style="background-color: #f8f9fa; padding: 10px; border-radius: 6px; margin: 15px 0; border: 1px solid #dee2e6;">
                    <strong style="font-size: 0.95em;">📊 Legenda de Status:</strong><br>
                    <div style="display: flex; gap: 15px; flex-wrap: wrap; margin-top: 8px;">
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span style="font-size: 1em;">✅</span>
                            <span style="color: #155724; font-weight: 500; font-size: 0.9em;">Verde</span> = Causa confirmada
                        </div>
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span style="font-size: 1em;">❌</span>
                            <span style="color: #721c24; font-weight: 500; font-size: 0.9em;">Vermelho</span> = Causa descartada
                        </div>
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span style="font-size: 1em;">⏳</span>
                            <span style="color: #383d41; font-weight: 500; font-size: 0.9em;">Cinza</span> = Em análise
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("⚠️ Erro ao renderizar árvore")
        else:
            st.info("🌱 A árvore ainda não possui nós. Adicione causas abaixo.")
        
        st.divider()
        
        # Interface conversacional para adicionar causas
        st.markdown("### 💭 Adicionar uma Causa")
        st.markdown("**Pergunta:** Por que isso aconteceu?")
        
        # Busca nós para seleção
        nodes = get_tree_nodes(accident_id)
        
        if nodes:
            # Seleção do evento/causa pai (terminologia natural)
            parent_options = {}
            for node in nodes:
                node_label = f"{node['label']}"
                parent_options[node_label] = node['id']
            
            selected_parent_label = st.selectbox(
                "Para qual evento/causa você quer adicionar uma nova causa?",
                options=list(parent_options.keys()),
                help="💡 Selecione o evento ou causa ao qual esta nova causa está relacionada. Ex: Se você selecionar 'Vazamento na PLECT', a nova causa será 'Por que houve vazamento na PLECT?'",
                key="parent_node_selector"
            )
            parent_id = parent_options[selected_parent_label]
            
            st.markdown(f"**🎯 Pergunta de investigação:** Por que **{selected_parent_label}** aconteceu?")
            st.caption("💡 Pense nas possíveis causas e fatores contribuintes. Seja específico e detalhado na descrição.")
        else:
            parent_id = None
            st.info("ℹ️ Adicione a primeira causa relacionada ao evento principal.")
        
        # Tipo de causa
        node_type = st.radio(
            "Tipo de causa/hipótese:",
            options=['hypothesis', 'fact'],
            format_func=lambda x: "🔍 Hipótese (precisa investigar e validar)" if x == 'hypothesis' else "🔗 Causa Intermediária (já confirmada, pode ter subcausas)",
            help="""
            **🔍 Hipótese:** Use quando você suspeita de uma possível causa mas ainda precisa investigar e validar com evidências. 
            Exemplos: "Possível falha no sistema de bloqueio", "Suspeita de treinamento inadequado", "Pode ter havido falha humana".
            
            **🔗 Causa Intermediária:** Use quando já tem certeza de que a causa existe e deseja investigar suas causas raízes (subcausas). 
            Exemplos: "Falhas de Inspeção e Manutenção" (pode ter subcausas como "Ausência de checklists" ou "Equipamento de teste calibrado incorretamente").
            
            💡 **Dica:** Comece com hipóteses, valide-as, e então transforme as confirmadas em causas intermediárias para aprofundar a análise.
            """,
            key="node_type_selector"
        )
        
        node_label = st.text_area(
            "Descreva a causa ou hipótese:",
            placeholder="Ex: Falta de treinamento adequado do operador na operação de equipamentos específicos",
            height=120,
            help="💡 **Seja específico e detalhado**: Descreva claramente a possível causa. Inclua informações relevantes como: quem estava envolvido, qual processo/equipamento, em que condições ocorreu. Uma descrição bem elaborada facilita a validação posterior. Exemplos: 'Ausência de procedimento operacional para a atividade', 'Falha no sistema de bloqueio e etiquetagem', 'Condições climáticas adversas não consideradas no planejamento'.",
            key="node_label_input"
        )
        
        if st.button("➕ Adicionar Causa", type="primary", key="add_node_btn"):
            if node_label:
                new_node_id = add_fault_tree_node(accident_id, parent_id, node_label, node_type)
                if new_node_id:
                    st.success("✅ Causa adicionada à árvore!")
                    st.rerun()
            else:
                st.warning("⚠️ Forneça uma descrição da causa")
        
        st.divider()
        
        # Validação de hipóteses (interface conversacional)
        st.markdown("### ✅ Validar Hipóteses e Causas Intermediárias")
        st.markdown("""
        **Processo de Validação:**
        
        Para cada hipótese ou causa intermediária identificada, você deve:
        
        1. **Revisar cuidadosamente** a descrição da hipótese/causa
        2. **Coletar evidências** que suportem ou refutem a hipótese (fotos, depoimentos, relatórios, etc.)
        3. **Documentar a justificativa** de forma clara e objetiva, explicando por que a hipótese foi confirmada ou descartada
        4. **Incluir imagens** quando disponíveis, pois elas reforçam a análise e aparecem no relatório final
        
        **💡 Dica:** Causas intermediárias validadas podem ter subcausas adicionadas para aprofundar a análise.
        """)
        
        # Inclui:
        # 1. Hipóteses (hypothesis) - todas
        # 2. Causas intermediárias (fact) - todas, mesmo validadas (para poder adicionar subcausas)
        # 3. Exclui root
        hypothesis_nodes = [n for n in nodes if n['type'] in ['hypothesis', 'fact'] and n.get('type') != 'root']
        
        # Ordena: fact validados primeiro (causas intermediárias), depois hypothesis, depois fact pending
        def sort_key(n):
            if n['type'] == 'fact' and n['status'] == 'validated':
                return (0, n.get('label', ''))
            elif n['type'] == 'hypothesis':
                return (1, n.get('label', ''))
            else:
                return (2, n.get('label', ''))
        hypothesis_nodes.sort(key=sort_key)
        
        if hypothesis_nodes:
            # Constrói a árvore JSON para calcular números corretamente
            tree_json = build_fault_tree_json(accident_id)
            
            # Função para calcular números dos nós (mesma lógica da árvore)
            node_number_map = {}  # Mapeia node_id -> número (H1, H2, CB1, etc.)
            hypothesis_counter = 0
            basic_cause_counter = 0
            contributing_cause_counter = 0
            
            def calculate_node_numbers(node_data: Dict[str, Any]):
                """Calcula números dos nós recursivamente (mesma lógica da renderização)"""
                nonlocal hypothesis_counter, basic_cause_counter, contributing_cause_counter
                
                node_id = node_data.get('id')
                node_type = node_data.get('type', 'hypothesis')
                status = node_data.get('status', 'pending')
                children = node_data.get('children', [])
                has_children = len(children) > 0
                is_basic_cause = node_data.get('is_basic_cause', False)
                is_contributing_cause = node_data.get('is_contributing_cause', False)
                
                # Calcula número do nó (mesma lógica da função get_node_number)
                node_number = ""
                if node_type != 'root':
                    if is_basic_cause:
                        basic_cause_counter += 1
                        node_number = f"CB{basic_cause_counter}"
                    elif is_contributing_cause:
                        contributing_cause_counter += 1
                        node_number = f"CC{contributing_cause_counter}"
                    elif node_type == 'hypothesis':
                        hypothesis_counter += 1
                        node_number = f"H{hypothesis_counter}"
                    elif node_type == 'fact' and has_children:
                        hypothesis_counter += 1
                        node_number = f"H{hypothesis_counter}"
                    elif status == 'validated' and has_children and node_type != 'root':
                        hypothesis_counter += 1
                        node_number = f"H{hypothesis_counter}"
                    elif status in ['pending', 'discarded'] and node_type != 'root':
                        hypothesis_counter += 1
                        node_number = f"H{hypothesis_counter}"
                
                # Armazena o número no mapeamento
                if node_number:
                    node_number_map[node_id] = node_number
                
                # Processa filhos recursivamente
                for child in children:
                    calculate_node_numbers(child)
            
            # Calcula números se houver árvore
            if tree_json:
                calculate_node_numbers(tree_json)
            
            # Verifica quais nós têm filhos
            node_ids = {n['id'] for n in nodes}
            children_count = {}
            for n in nodes:
                parent_id = n.get('parent_id')
                if parent_id and parent_id in node_ids:
                    children_count[parent_id] = children_count.get(parent_id, 0) + 1
            
            for node in hypothesis_nodes:
                current_status = node['status']
                node_type = node['type']
                has_children = children_count.get(node['id'], 0) > 0
                num_children = children_count.get(node['id'], 0)
                
                # Verifica se é causa contribuinte
                is_contributing = node.get('is_contributing_cause', False)
                is_basic = node.get('is_basic_cause', False)
                
                # Obtém o número do nó (H1, H2, CB1, CC1, etc.)
                node_number = node_number_map.get(node['id'], '')
                number_prefix = f"{node_number}: " if node_number else ""
                
                # Determina tipo e status para exibição
                if is_basic:
                    # Causa básica
                    node_type_label = "🔵 Causa Básica"
                elif is_contributing:
                    # Causa contribuinte - usa símbolo de mão
                    node_type_label = "🤝 Causa Contribuinte"
                elif node_type == 'fact' and has_children:
                    # Causa intermediária (fact validada com filhos)
                    node_type_label = "🔗 Causa Intermediária"
                elif node_type == 'fact' and current_status == 'pending' and not has_children:
                    # Hipótese confirmada (fact pending sem filhos)
                    node_type_label = "✅ Hipótese Confirmada"
                elif node_type == 'hypothesis':
                    node_type_label = "❓ Hipótese"
                else:
                    node_type_label = "📋 Causa"
                
                # Determina cor e texto baseado no status
                if current_status == 'validated':
                    status_color = "#28a745"
                    status_text = "✅ Confirmado/Verdadeiro"
                elif current_status == 'discarded':
                    status_color = "#dc3545"
                    status_text = "❌ Descartado/Falso"
                else:
                    status_color = "#6c757d"
                    status_text = "⏳ Em Análise"
                
                # Título do expander com numeração
                if has_children:
                    title = f"{number_prefix}{node_type_label} ({status_text}): {node['label'][:50]}... [tem {num_children} subcausa(s)]"
                else:
                    title = f"{number_prefix}{node_type_label} ({status_text}): {node['label'][:60]}..."
                
                with st.expander(title, expanded=False):
                    # Botão de melhoria com IA para descrição
                    col_ai_btn, col_empty = st.columns([1, 5])
                    with col_ai_btn:
                        ai_improve_key = f"ai_improve_{node['id']}"
                        if st.button("✨ Melhorar Descrição com IA", key=ai_improve_key, help="Use IA para melhorar a descrição desta hipótese/causa tornando-a mais clara e específica"):
                            with st.spinner("🔄 Gerando descrição melhorada com IA..."):
                                try:
                                    # Obtém contexto do acidente
                                    accident_context = investigation.get('description', '') if investigation else ''
                                    base_location = investigation.get('base_location', '') if investigation else ''
                                    
                                    # Contexto adicional das pessoas envolvidas
                                    involved_context = ""
                                    if 'involved_injured' in locals() and involved_injured:
                                        for inv in involved_injured:
                                            if inv.get('name'):
                                                involved_context += f"Vítima: {inv.get('name')}, {inv.get('age', '')} anos, {inv.get('job_title', '')} da empresa {inv.get('company', '')}. "
                                    
                                    current_label = node['label']
                                    
                                    # Constrói prompt para IA melhorar o texto, usando a descrição atual como contexto
                                    prompt = f"""Você é um especialista em investigação de acidentes de trabalho.

=== CONTEXTO DO ACIDENTE ===
Local: {base_location}
Descrição: {accident_context}
{f'Pessoas envolvidas: {involved_context}' if involved_context else ''}

=== DESCRIÇÃO ATUAL DA HIPÓTESE/CAUSA ===
"{current_label}"

Esta é a descrição atual que precisa ser melhorada. Use esta descrição como base e contexto para criar uma versão melhorada.

=== INSTRUÇÕES ===
1. MELHORE a descrição acima tornando-a mais clara, específica, profissional e contextualizada
2. USE a descrição atual "{current_label}" como contexto - mantenha o significado, mas torne mais clara e específica
3. USE os dados reais do acidente quando relevante (local: {base_location})
4. A descrição melhorada deve ser:
   - Clara e precisa
   - Específica (evite termos genéricos)
   - Profissional
   - Adequada para investigação técnica
   - Contextualizada com os dados do acidente quando aplicável

Retorne APENAS o texto da descrição melhorada, sem explicações adicionais."""
                                    
                                    # Tenta usar Google Gemini
                                    improved_text = None
                                    if GEMINI_AVAILABLE:
                                        try:
                                            api_key = os.getenv('GOOGLE_AI_API_KEY') or st.secrets.get('general', {}).get('GOOGLE_AI_API_KEY', None)
                                            if api_key:
                                                genai.configure(api_key=api_key)
                                                # Usa gemini-3-flash-preview ou gemini-2.5-flash como fallback
                                                try:
                                                    model = genai.GenerativeModel('gemini-3-flash-preview')
                                                except:
                                                    model = genai.GenerativeModel('gemini-2.5-flash')
                                                
                                                # Configuração para melhor geração
                                                generation_config = {
                                                    "temperature": 0.7,
                                                    "top_p": 0.8,
                                                    "top_k": 40,
                                                    "max_output_tokens": 1024,
                                                }
                                                
                                                response = model.generate_content(
                                                    prompt,
                                                    generation_config=generation_config
                                                )
                                                
                                                # Extrai o texto de forma robusta
                                                try:
                                                    improved_text = response.text.strip() if response.text else None
                                                    if not improved_text or len(improved_text) < 10:
                                                        improved_text = current_label  # Mantém original se resposta inválida
                                                except:
                                                    improved_text = current_label  # Mantém original se erro na extração
                                        except Exception as e:
                                            st.warning(f"⚠️ Erro ao conectar com IA: {str(e)}")
                                    
                                    # Se não conseguiu usar IA, usa método básico
                                    if not improved_text:
                                        improved_text = current_label  # Mantém o original se não conseguir melhorar
                                    
                                    # Salva no session_state para preencher o campo
                                    edit_label_key = f"edit_label_{node['id']}"
                                    st.session_state[edit_label_key] = improved_text
                                    st.success("✅ Descrição melhorada gerada! Revise o texto abaixo e ajuste se necessário antes de salvar.")
                                    
                                except Exception as e:
                                    st.error(f"❌ Erro ao melhorar descrição: {str(e)}")
                    
                    # Campo de edição do label
                    edit_label_key = f"edit_label_{node['id']}"
                    edit_label_text = "✏️ Editar descrição da causa:" if node_type == 'fact' else "✏️ Editar descrição da hipótese:"
                    
                    # Usa session_state se foi gerada uma descrição melhorada
                    default_label = st.session_state.get(edit_label_key, node['label'])
                    
                    edited_label = st.text_area(
                        edit_label_text,
                        value=default_label,
                        key=edit_label_key,
                        help="💡 **Melhore a descrição:** Certifique-se de que a descrição seja clara, específica e completa. Inclua detalhes relevantes como: contexto, envolvidos, equipamentos, condições, etc. Uma boa descrição facilita a compreensão e validação da causa/hipótese.",
                        height=100
                    )
                    
                    # Botão para salvar edição do label
                    if edited_label != node['label']:
                        col_edit, _ = st.columns([1, 2])
                        with col_edit:
                            if st.button("💾 Salvar Edição", key=f"save_edit_{node['id']}"):
                                if edited_label.strip():
                                    if update_node_label(node['id'], edited_label.strip()):
                                        success_msg = "✅ Causa atualizada!" if node_type == 'fact' else "✅ Hipótese atualizada!"
                                        st.success(success_msg)
                                        st.rerun()
                                else:
                                    st.warning("⚠️ O texto não pode estar vazio")
                    
                    st.markdown(f"**Status atual:** {status_text}")
                    
                    # Mostra justificativa existente se houver
                    if node.get('justification'):
                        st.markdown("---")
                        st.markdown("### 📝 Justificativa Registrada")
                        st.info(f"**Análise documentada:**\n\n{node['justification']}")
                        st.markdown("---")
                    
                    # Mostra imagem de justificativa existente se houver (mesma lógica da galeria de evidências)
                    justification_image_url = node.get('justification_image_url')
                    if justification_image_url:
                        # Valida se a URL não está vazia
                        if justification_image_url and isinstance(justification_image_url, str) and justification_image_url.strip():
                            st.markdown("**📷 Imagem da justificativa:**")
                            
                            # Mesma lógica da galeria de evidências
                            image_loaded = False
                            
                            # Extrai o path da URL
                            path = None
                            if '/storage/v1/object/public/evidencias/' in justification_image_url:
                                path = justification_image_url.split('/storage/v1/object/public/evidencias/')[1]
                            elif '/evidencias/' in justification_image_url:
                                parts = justification_image_url.split('/evidencias/')
                                if len(parts) > 1:
                                    path = parts[1]
                            
                            # Tenta baixar do Supabase Storage primeiro (mais confiável)
                            if path:
                                try:
                                    from managers.supabase_config import get_service_role_client
                                    supabase = get_service_role_client()
                                    if supabase:
                                        image_bytes = supabase.storage.from_('evidencias').download(path)
                                        if image_bytes:
                                            st.image(
                                                image_bytes, 
                                                width=300, 
                                                caption="Imagem da justificativa"
                                            )
                                            image_loaded = True
                                except Exception as e:
                                    # Se falhar, continua para tentar outros métodos
                                    pass
                            
                            # Se não carregou pelo download direto, tenta pela URL
                            if not image_loaded:
                                try:
                                    st.image(
                                        justification_image_url, 
                                        width=300, 
                                        caption="Imagem da justificativa"
                                    )
                                    image_loaded = True
                                except Exception as e:
                                    # Se falhar, tenta baixar via HTTP
                                    try:
                                        response = requests.get(justification_image_url, timeout=10)
                                        if response.status_code == 200:
                                            st.image(
                                                response.content, 
                                                width=300, 
                                                caption="Imagem da justificativa"
                                            )
                                            image_loaded = True
                                    except Exception as e2:
                                        pass
                            
                            # Se nada funcionou, mostra erro e link
                            if not image_loaded:
                                st.error("⚠️ Não foi possível carregar a imagem")
                                st.markdown(f"**URL:** [{justification_image_url}]({justification_image_url})")
                                if path:
                                    st.caption(f"Path: {path}")
                        
                        if st.button("🗑️ Remover imagem", key=f"remove_img_{node['id']}"):
                            from services.investigation import update_node_justification_image
                            if update_node_justification_image(node['id'], None):
                                st.success("✅ Imagem removida!")
                                st.rerun()
                    
                    # Campo de justificativa
                    justification_key = f"justification_{node['id']}"
                    justification_label = "📝 Justificativa da Análise (obrigatória para confirmar ou descartar)"
                    
                    # Botão de melhoria de justificativa com IA
                    col_ai_just, col_empty_just = st.columns([1, 5])
                    with col_ai_just:
                        ai_improve_just_key = f"ai_improve_just_{node['id']}"
                        if st.button("✨ Melhorar Justificativa com IA", key=ai_improve_just_key, help="Use IA para melhorar e contextualizar a justificativa usando os dados reais do acidente"):
                            with st.spinner("🔄 Gerando justificativa melhorada com IA..."):
                                try:
                                    # Obtém contexto completo
                                    accident_context = investigation.get('description', '') if investigation else ''
                                    base_location = investigation.get('base_location', '') if investigation else ''
                                    occurrence_date = investigation.get('occurrence_date', '') if investigation else ''
                                    accident_type = investigation.get('type', '') if investigation else ''
                                    
                                    # Contexto das pessoas envolvidas
                                    involved_context = ""
                                    try:
                                        # Tenta usar involved_injured se disponível, senão busca
                                        if 'involved_injured' in locals() and involved_injured:
                                            involved_list = involved_injured
                                        else:
                                            involved_list = get_involved_people(accident_id, 'Injured')
                                        
                                        for inv in involved_list:
                                            if inv.get('name'):
                                                involved_context += f"Vítima: {inv.get('name')}, {inv.get('age', '')} anos, {inv.get('job_title', '')} da empresa {inv.get('company', '')}. "
                                                if inv.get('injury_type'):
                                                    involved_context += f"Tipo de lesão: {inv.get('injury_type')}, parte do corpo: {inv.get('body_part', '')}. "
                                    except:
                                        pass
                                    
                                    # Obtém outras hipóteses relacionadas para contexto
                                    related_context = ""
                                    related_nodes = [n for n in nodes if n['id'] != node['id'] and n.get('status') in ['validated', 'discarded']]
                                    if related_nodes:
                                        related_context = "\nHipóteses já analisadas neste acidente:\n"
                                        for rn in related_nodes[:3]:  # Limita a 3 para não ficar muito longo
                                            related_context += f"- {rn['label']} (Status: {rn['status']})\n"
                                    
                                    # Justificativa atual
                                    current_justification = node.get('justification', '')
                                    
                                    # Status atual do nó (garante que está definido)
                                    current_status = node.get('status', 'pending')
                                    
                                    # Formata a data de forma legível para o prompt
                                    try:
                                        if occurrence_date:
                                            date_obj = datetime.fromisoformat(occurrence_date.replace('Z', '+00:00'))
                                            formatted_date_prompt = date_obj.strftime('%d/%m/%Y às %H:%M')
                                        else:
                                            formatted_date_prompt = occurrence_date if occurrence_date else "data não informada"
                                    except:
                                        formatted_date_prompt = occurrence_date if occurrence_date else "data não informada"
                                    
                                    # Constrói prompt para IA mais específico e direto, usando hipótese e justificativa como contexto
                                    prompt = f"""Você é um especialista técnico em investigação de acidentes de trabalho, seguindo a metodologia NBR 14280.

TAREFA: {"Melhorar e contextualizar" if current_justification else "Gerar"} uma justificativa técnica profissional para uma hipótese de causa raiz de acidente.

=== CONTEXTO DO ACIDENTE ===
Tipo: {accident_type}
Local: {base_location}
Data/Hora: {formatted_date_prompt}
Descrição completa: {accident_context}
{f'Pessoas envolvidas: {involved_context}' if involved_context else ''}
{f'Hipóteses relacionadas já analisadas: {related_context}' if related_context else ''}

=== HIPÓTESE/CAUSA A ANALISAR ===
"{node['label']}"

Esta é a hipótese que precisa ser justificada. Use esta descrição como base para sua análise e explique como ela se relaciona com o acidente ocorrido.

STATUS ATUAL: {current_status} ({"confirmada" if current_status == 'validated' else "descartada" if current_status == 'discarded' else "em análise"})

=== JUSTIFICATIVA ATUAL ===
{"A justificativa abaixo já existe e deve ser MELHORADA e CONTEXTUALIZADA com os dados do acidente:" if current_justification else "Nenhuma justificativa ainda escrita - GERE uma completa:"}
{current_justification if current_justification else '[Nenhuma justificativa ainda escrita - gere uma completa baseada na hipótese e nos dados do acidente]'}

Use a justificativa acima como base e contexto. Se ela existir, melhore-a. Se não existir, crie uma nova usando a hipótese e os dados do acidente como referência.

=== INSTRUÇÕES CRÍTICAS ===
{"1. MELHORE a justificativa existente, tornando-a mais específica e contextualizada com os dados reais do acidente" if current_justification else "1. GERE uma justificativa técnica completa e profissional baseada na hipótese e nos dados do acidente"}
2. USE a HIPÓTESE "{node['label']}" como contexto central - explique como ela se relaciona com o acidente
3. USE os dados reais do acidente: local "{base_location}", data "{formatted_date_prompt}", tipo "{accident_type}"
4. SEJA ESPECÍFICO: cite detalhes concretos, evite termos genéricos como "análise realizada", "verificações", "investigação"
5. EXPLIQUE claramente POR QUE esta hipótese foi {"confirmada" if current_status == 'validated' else "descartada" if current_status == 'discarded' else "está em análise"}
6. CONTEXTUALIZE usando os dados reais: mencione o local específico, a data/hora, o tipo de acidente
7. ESTRUTURA: Comece contextualizando o acidente, depois analise a hipótese "{node['label']}", e conclua com o raciocínio de confirmação/descarte
8. TOM: Profissional, técnico, adequado para relatório oficial de investigação
9. REFERENCIE a hipótese explicitamente no texto da justificativa

=== EXEMPLO DE BOM ESTILO ===
"Após análise detalhada do acidente ocorrido em {base_location} em {formatted_date_prompt}, classificado como {accident_type}, foi identificado que a hipótese '{node['label']}' foi {"confirmada" if current_status == 'validated' else "descartada" if current_status == 'discarded' else "requer análise"} porque [EXPLICAÇÃO ESPECÍFICA COM DETALHES REAIS DO CASO, REFERENCIANDO A HIPÓTESE E OS DADOS DO ACIDENTE]..."

=== IMPORTANTE ===
- NÃO use termos genéricos ou vagos
- NÃO repita apenas a descrição do acidente
- FOQUE na análise específica da hipótese "{node['label']}" usando os dados reais
- USE a justificativa atual como contexto se ela existir
- GERE um texto completo de pelo menos 200 palavras
- Retorne APENAS o texto da justificativa, sem explicações ou formatação markdown adicional"""
                                    
                                    # Tenta usar Google Gemini
                                    improved_text = None
                                    error_msg = None
                                    
                                    if GEMINI_AVAILABLE:
                                        try:
                                            api_key = os.getenv('GOOGLE_AI_API_KEY') or st.secrets.get('general', {}).get('GOOGLE_AI_API_KEY', None)
                                            if not api_key:
                                                error_msg = "Chave da API do Google Gemini não configurada. Configure GOOGLE_AI_API_KEY nas variáveis de ambiente ou secrets."
                                            else:
                                                genai.configure(api_key=api_key)
                                                # Usa gemini-3-flash-preview ou gemini-2.5-flash como fallback
                                                try:
                                                    model = genai.GenerativeModel('gemini-3-flash-preview')
                                                except:
                                                    model = genai.GenerativeModel('gemini-2.5-flash')
                                                
                                                # Configuração de segurança e parâmetros
                                                generation_config = {
                                                    "temperature": 0.7,
                                                    "top_p": 0.8,
                                                    "top_k": 40,
                                                    "max_output_tokens": 2048,  # Aumentado para permitir textos mais longos
                                                }
                                                
                                                response = model.generate_content(
                                                    prompt,
                                                    generation_config=generation_config
                                                )
                                                
                                                # Extrai o texto de forma mais robusta
                                                try:
                                                    improved_text = response.text.strip() if response.text else None
                                                    
                                                    # Verifica se a resposta foi truncada
                                                    if improved_text:
                                                        # Verifica se termina abruptamente (sem pontuação final)
                                                        if not improved_text.endswith(('.', '!', '?', ':', ';', '\n')):
                                                            # Pode estar truncada, mas ainda usa o texto disponível
                                                            st.info("ℹ️ A resposta pode estar incompleta. Revise o texto gerado.")
                                                        
                                                        # Verifica se a resposta é válida
                                                        if len(improved_text) < 50:
                                                            error_msg = "A IA retornou uma resposta muito curta ou vazia."
                                                            improved_text = None
                                                    else:
                                                        error_msg = "A IA retornou uma resposta vazia."
                                                        improved_text = None
                                                except Exception as extract_error:
                                                    error_msg = f"Erro ao extrair texto da resposta: {str(extract_error)}"
                                                    improved_text = None
                                        except Exception as e:
                                            error_msg = f"Erro ao conectar com IA: {str(e)}"
                                            improved_text = None
                                    
                                    # Se não conseguiu usar IA, gera uma justificativa inteligente baseada nos dados
                                    if not improved_text:
                                        # Formata a data de forma legível
                                        try:
                                            if occurrence_date:
                                                date_obj = datetime.fromisoformat(occurrence_date.replace('Z', '+00:00'))
                                                formatted_date = date_obj.strftime('%d/%m/%Y às %H:%M')
                                            else:
                                                formatted_date = "data não informada"
                                        except:
                                            formatted_date = occurrence_date if occurrence_date else "data não informada"
                                        
                                        # Gera justificativa contextualizada baseada nos dados reais
                                        if current_justification:
                                            # Se já existe justificativa, melhora ela adicionando contexto
                                            improved_text = f"""{current_justification}

**Contextualização com dados do acidente:**
- **Local:** {base_location}
- **Data/Hora:** {formatted_date}
- **Tipo de acidente:** {accident_type}
{f'- **Contexto das pessoas envolvidas:** {involved_context}' if involved_context else ''}

Esta análise foi realizada considerando as circunstâncias específicas deste evento ocorrido em {base_location}, em {formatted_date}. A justificativa acima deve ser revisada e complementada com evidências concretas coletadas durante a investigação, incluindo fotos, relatórios técnicos, depoimentos e análises do local do acidente."""
                                        else:
                                            # Gera uma justificativa completa do zero
                                            status_text = "confirmada" if current_status == 'validated' else "descartada" if current_status == 'discarded' else "em análise"
                                            
                                            improved_text = f"""**Análise da hipótese: "{node['label']}"**

Após investigação detalhada do acidente ocorrido em **{base_location}** em **{formatted_date}**, esta hipótese foi **{status_text}** com base nas seguintes considerações:

**Contexto do acidente:**
- Local: {base_location}
- Data/Hora: {formatted_date}
- Tipo: {accident_type}
{f'- Pessoas envolvidas: {involved_context}' if involved_context else ''}

**Análise da hipótese:**
{node['label']}

**Justificativa:**
[COMPLETE AQUI com evidências específicas que confirmam ou descartam esta hipótese. Cite fotos, relatórios técnicos, depoimentos, inspeções do local, análises de equipamentos, ou outros dados concretos coletados durante a investigação. Seja específico e profissional, evitando termos genéricos.]

**Conclusão:**
Com base nas evidências coletadas e na análise realizada, esta hipótese foi **{status_text}** porque [EXPLIQUE O MOTIVO ESPECÍFICO baseado nas evidências reais do acidente]."""
                                        
                                        # Mostra aviso se a IA não foi usada
                                        if error_msg:
                                            st.warning(f"⚠️ {error_msg} Uma justificativa base foi gerada automaticamente. Revise e complete com os dados específicos da investigação.")
                                        elif not GEMINI_AVAILABLE:
                                            st.info("ℹ️ Biblioteca do Google Gemini não disponível. Uma justificativa base foi gerada automaticamente. Revise e complete com os dados específicos da investigação.")
                                    
                                    # Salva no session_state para preencher o campo
                                    st.session_state[justification_key] = improved_text
                                    st.success("✅ Justificativa melhorada gerada! Revise o texto abaixo e ajuste se necessário antes de salvar.")
                                    
                                except Exception as e:
                                    st.error(f"❌ Erro ao melhorar justificativa: {str(e)}")
                                    st.info("💡 Tente melhorar a justificativa manualmente usando o contexto do acidente.")
                    
                    if node_type == 'fact':
                        justification_help = """
                        **Como elaborar uma boa justificativa:**
                        
                        Explique **claramente e de forma fundamentada** por que esta causa intermediária foi confirmada ou descartada:
                        
                        ✅ **Para confirmar:** Cite as evidências que comprovam a causa (ex: "Análise do relatório técnico identificou falha no sistema de bloqueio"; "Fotos do local mostram ausência de sinalização"; "Depoimento do operador confirma que não havia procedimento específico").
                        
                        ❌ **Para descartar:** Explique por que a causa não se aplica ao caso (ex: "Verificação dos registros mostra que o treinamento estava atualizado"; "Inspeção do equipamento não identificou falhas mecânicas"; "Análise dos dados confirma que as condições ambientais estavam dentro dos parâmetros normais").
                        
                        Esta justificativa será incluída no relatório PDF oficial e deve ser precisa e profissional.
                        """
                    else:
                        justification_help = """
                        **Como elaborar uma boa justificativa:**
                        
                        Explique **claramente e de forma fundamentada** por que esta hipótese foi confirmada ou descartada:
                        
                        ✅ **Para confirmar:** Cite as evidências que comprovam a hipótese (ex: "Análise do relatório técnico identificou falha no sistema de bloqueio"; "Fotos do local mostram ausência de sinalização"; "Depoimento do operador confirma que não havia procedimento específico").
                        
                        ❌ **Para descartar:** Explique por que a hipótese não se aplica ao caso (ex: "Verificação dos registros mostra que o treinamento estava atualizado"; "Inspeção do equipamento não identificou falhas mecânicas"; "Análise dos dados confirma que as condições ambientais estavam dentro dos parâmetros normais").
                        
                        **💡 Importante:** Base sua justificativa em fatos, evidências e análises concretas, não em suposições. Esta justificativa será incluída no relatório PDF oficial e deve ser precisa e profissional.
                        """
                    
                    # Verifica se a chave já existe no session_state para evitar conflito
                    # Se existir, não passa value= para deixar o Streamlit usar o valor do session_state
                    # Se não existir, inicializa com o valor do node
                    if justification_key not in st.session_state:
                        st.session_state[justification_key] = node.get('justification', '')
                    
                    justification = st.text_area(
                        justification_label,
                        key=justification_key,
                        help=justification_help,
                        height=150,
                        placeholder="Ex: Após análise detalhada das evidências coletadas (fotos, relatórios técnicos e depoimentos), foi identificado que..."
                    )
                    
                    # Upload de imagem para justificativa
                    st.markdown("**📷 Evidência Visual da Justificativa (opcional, mas recomendado):**")
                    uploaded_justification_image = st.file_uploader(
                        "Adicione uma foto, diagrama ou documento que comprove ou descarte esta hipótese/causa:",
                        type=['png', 'jpg', 'jpeg'],
                        key=f"justification_image_{node['id']}",
                        help="💡 **Evidências visuais reforçam sua análise:** Fotos do local, diagramas técnicos, relatórios escaneados, prints de sistemas, etc. A imagem será exibida no relatório PDF junto com a justificativa, tornando a análise mais completa e convincente."
                    )
                    
                    if uploaded_justification_image:
                        # Mostra preview da imagem
                        st.image(uploaded_justification_image, caption="Preview da imagem", width=120)
                        
                        # Botão para fazer upload
                        if st.button("📤 Fazer upload da imagem", key=f"upload_img_{node['id']}"):
                            from services.investigation import upload_justification_image
                            file_bytes = uploaded_justification_image.read()
                            image_url = upload_justification_image(node['id'], accident_id, file_bytes, uploaded_justification_image.name)
                            if image_url:
                                st.success("✅ Imagem enviada com sucesso!")
                                st.rerun()
                            else:
                                st.error("❌ Erro ao fazer upload da imagem")
                    
                    col_val, col_disc, col_pend = st.columns(3)
                    
                    with col_val:
                        if st.button("✅ Confirmar/Verdadeiro", key=f"validate_{node['id']}", 
                                   help="Use quando tiver evidências concretas (relatórios, fotos, depoimentos, análises) que confirmam esta causa/hipótese. A justificativa deve explicar claramente por que a causa é verdadeira."):
                            justification_clean = (justification or '').strip()
                            if not justification_clean:
                                st.warning("⚠️ **Atenção:** Uma justificativa fundamentada é obrigatória para confirmar uma causa/hipótese. Por favor, descreva as evidências que comprovam esta causa antes de confirmar.")
                            else:
                                # Se houver imagem sendo enviada, faz upload primeiro
                                justification_img_url = None
                                if uploaded_justification_image:
                                    from services.investigation import upload_justification_image
                                    file_bytes = uploaded_justification_image.read()
                                    justification_img_url = upload_justification_image(node['id'], accident_id, file_bytes, uploaded_justification_image.name)
                                
                                if update_node_status(node['id'], 'validated', justification_clean, justification_img_url):
                                    st.success("✅ Hipótese confirmada com justificativa!")
                                    st.rerun()
                    
                    with col_disc:
                        # Ajuda específica para facts vs hipóteses
                        discard_help = "Use quando tiver evidências concretas que descartam esta causa/hipótese. A justificativa deve explicar claramente por que a causa não se aplica ao caso (ex: verificações realizadas, análises concluídas, condições não verificadas)."
                        if node_type == 'fact':
                            discard_help = "Use quando tiver evidências concretas que descartam esta causa intermediária. Facts (causas intermediárias) também precisam de justificativa detalhada quando descartados, mesmo que tenham sido confirmados anteriormente."
                        
                        if st.button("❌ Descartar/Falso", key=f"discard_{node['id']}",
                                   help=discard_help):
                            justification_clean = (justification or '').strip()
                            if not justification_clean:
                                st.warning("⚠️ **Atenção:** Uma justificativa fundamentada é obrigatória para descartar uma causa/hipótese. Por favor, explique claramente por que esta causa não se aplica ao caso antes de descartar.")
                            else:
                                # Aviso especial se for fact com filhos
                                if node_type == 'fact' and has_children:
                                    st.info("ℹ️ Você está descartando uma causa intermediária que possui subcausas. As subcausas permanecerão na árvore, mas esta causa será marcada como descartada.")
                                
                                # Se houver imagem sendo enviada, faz upload primeiro
                                justification_img_url = None
                                if uploaded_justification_image:
                                    from services.investigation import upload_justification_image
                                    file_bytes = uploaded_justification_image.read()
                                    justification_img_url = upload_justification_image(node['id'], accident_id, file_bytes, uploaded_justification_image.name)
                                
                                if update_node_status(node['id'], 'discarded', justification_clean, justification_img_url):
                                    success_msg = "❌ Causa descartada com justificativa!" if node_type == 'fact' else "❌ Hipótese descartada com justificativa!"
                                    st.success(success_msg)
                                    st.rerun()
                    
                    with col_pend:
                        if current_status != 'pending':
                            if st.button("⏳ Em Análise", key=f"pending_{node['id']}",
                                       help="Voltar ao status de investigação"):
                                # Ao voltar para pending, mantém a justificativa se houver
                                justification_clean = (justification or '').strip()
                                if update_node_status(node['id'], 'pending', justification_clean if justification_clean else None, None):
                                    st.success("⏳ Status alterado para em análise!")
                                    st.rerun()
                    
                    # Botão para excluir hipótese
                    st.divider()
                    st.markdown("**🗑️ Excluir Hipótese:**")
                    st.warning("⚠️ **Atenção:** Ao excluir esta hipótese, todos os nós filhos também serão excluídos permanentemente. Esta ação não pode ser desfeita.")
                    
                    # Verifica se o nó tem filhos
                    tree_json = build_fault_tree_json(accident_id)
                    has_children = False
                    if tree_json:
                        def check_children(node_data: Dict[str, Any], target_id: str) -> bool:
                            """Verifica recursivamente se um nó tem filhos"""
                            if node_data.get('id') == target_id:
                                return len(node_data.get('children', [])) > 0
                            for child in node_data.get('children', []):
                                if check_children(child, target_id):
                                    return True
                            return False
                        has_children = check_children(tree_json, node['id'])
                    
                    if has_children:
                        st.info(f"⚠️ Esta hipótese possui nós filhos. Todos serão excluídos junto com ela.")
                    
                    delete_confirm_key = f"delete_confirm_{node['id']}"
                    delete_confirm = st.checkbox(
                        "Confirmo que desejo excluir esta hipótese",
                        key=delete_confirm_key,
                        help="Marque esta opção para habilitar o botão de exclusão"
                    )
                    
                    if delete_confirm:
                        if st.button("🗑️ Excluir Hipótese Permanentemente", 
                                   key=f"delete_{node['id']}",
                                   type="primary",
                                   help="Exclui esta hipótese e todos os seus nós filhos"):
                            if delete_fault_tree_node(node['id']):
                                st.success("✅ Hipótese excluída com sucesso!")
                                st.rerun()
                            else:
                                st.error("❌ Erro ao excluir hipótese. Verifique se ela não é o nó raiz.")
                    
                    # Checkbox para marcar como causa básica ou contribuinte (apenas para nós validados)
                    if current_status == 'validated':
                        st.divider()
                        is_basic_cause = node.get('is_basic_cause', False)
                        is_contributing_cause = node.get('is_contributing_cause', False)
                        
                        basic_cause_key = f"is_basic_cause_{node['id']}"
                        new_is_basic_cause = st.checkbox(
                            "🎯 Marcar como Causa Básica",
                            value=is_basic_cause,
                            key=basic_cause_key,
                            help="Marque esta opção se esta é uma causa básica (causa raiz que não pode ser mais decomposta). Causas básicas aparecem como oval verde na árvore."
                        )
                        if new_is_basic_cause != is_basic_cause:
                            # Se marcar como causa básica, desmarca causa contribuinte
                            if new_is_basic_cause and is_contributing_cause:
                                update_node_is_contributing_cause(node['id'], False)
                            if update_node_is_basic_cause(node['id'], new_is_basic_cause):
                                st.success("✅ Causa básica atualizada!")
                                st.rerun()
                        
                        contributing_cause_key = f"is_contributing_cause_{node['id']}"
                        new_is_contributing_cause = st.checkbox(
                            "🤝 Marcar como Causa Contribuinte",
                            value=is_contributing_cause,
                            key=contributing_cause_key,
                            help="Marque esta opção se esta é uma causa contribuinte (fator que contribui para o acidente mas não é uma causa básica). Causas contribuintes aparecem como oval azul na árvore."
                        )
                        if new_is_contributing_cause != is_contributing_cause:
                            # Se marcar como causa contribuinte, desmarca causa básica
                            if new_is_contributing_cause and is_basic_cause:
                                update_node_is_basic_cause(node['id'], False)
                            if update_node_is_contributing_cause(node['id'], new_is_contributing_cause):
                                st.success("✅ Causa contribuinte atualizada!")
                                st.rerun()
        else:
            st.info("📭 Nenhuma hipótese para validar ainda. Adicione hipóteses acima.")
        
        # Verifica se há causas validadas para desbloquear próximo passo
        validated_count = len([n for n in nodes if n['status'] == 'validated'])
        
        # Navegação
        col_prev, col_next = st.columns([1, 1])
        with col_prev:
            if st.button("⬅️ Anterior: Linha do Tempo", width='stretch'):
                st.session_state['current_step'] = 1
                st.rerun()
        with col_next:
            if validated_count > 0:
                if st.button("➡️ Próximo: Classificação", type="primary", width='stretch'):
                    st.session_state['current_step'] = 3
                    st.rerun()
            else:
                st.info("💡 Valide pelo menos uma causa para continuar")
        
        # Expander JSON (opcional)
        with st.expander("📄 Ver Estrutura JSON da Árvore", expanded=False):
            if tree_json:
                st.json(tree_json)
            else:
                st.info("Nenhuma estrutura JSON disponível ainda.")
    
    # ========== PASSO 4: CLASSIFICAÇÃO OFICIAL ==========
    elif st.session_state['current_step'] == 3:
        st.header("📋 Passo 4: Classificação Oficial (NBR 14280)")
        st.markdown("**O que falhou na norma?** Classifique as causas confirmadas conforme os padrões NBR 14280.")
        
        # Busca todos os padrões NBR
        nbr_standards_list = get_nbr_standards()
        
        # Busca causas básicas e contribuintes (validadas E marcadas)
        nodes = get_tree_nodes(accident_id)
        basic_cause_nodes = [n for n in nodes if n['status'] == 'validated' and n.get('is_basic_cause', False) == True]
        contributing_cause_nodes = [n for n in nodes if n['status'] == 'validated' and n.get('is_contributing_cause', False) == True]
        
        if basic_cause_nodes:
            st.markdown("### ✅ Causas Básicas para Classificação")
            st.info(f"💡 Você tem **{len(basic_cause_nodes)}** causa(s) básica(s) confirmada(s) para classificar.")
            
            for node in basic_cause_nodes:
                with st.expander(f"🎯 {node['label'][:60]}...", expanded=True):
                    st.markdown(f"**Causa Básica:** {node['label']}")
                    st.info("💡 Esta é uma causa básica confirmada. Classifique-a conforme os padrões NBR 14280.")
                    
                    # Busca padrões NBR por categoria
                    categories = {
                        'unsafe_act': 'Falha Humana (Ato Inseguro)',
                        'unsafe_condition': 'Condição do Ambiente',
                        'personal_factor': 'Fator Pessoal',
                        'management_failure': 'Falha na Gestão',
                        'procedure_failure': 'Falha no Procedimento',
                        'engineering_failure': 'Falha de Engenharia'
                    }
                    
                    # Seleção de categoria
                    selected_category = st.selectbox(
                        "O que falhou?",
                        options=list(categories.keys()),
                        format_func=lambda x: categories[x],
                        help="💡 **Ato Inseguro**: Ação incorreta do trabalhador. **Condição do Ambiente**: Problema no ambiente/máquina. **Fator Pessoal**: Característica pessoal que contribuiu. **Falha na Gestão**: Problemas na gestão/organização. **Falha no Procedimento**: Procedimento inadequado ou ausente. **Falha de Engenharia**: Problema no projeto/engenharia.",
                        key=f"category_basic_{node['id']}"
                    )
                    
                    # Busca padrões NBR filtrados
                    search_term = st.text_input(
                        "🔍 Buscar código NBR (opcional):",
                        placeholder="Ex: treinamento, equipamento, proteção...",
                        key=f"search_basic_{node['id']}"
                    )
                    
                    # Filtra padrões NBR
                    filtered_standards = [s for s in nbr_standards_list if s['category'] == selected_category]
                    if search_term:
                        search_lower = search_term.lower()
                        filtered_standards = [s for s in filtered_standards if 
                                             search_lower in s['code'].lower() or 
                                             search_lower in s['description'].lower()]
                    
                    if filtered_standards:
                        # Cria opções para selectbox
                        standard_options = {
                            f"{std['code']} - {std['description']}": std['id'] 
                            for std in filtered_standards
                        }
                        
                        # Verifica se já tem padrão vinculado
                        current_standard_id = node.get('nbr_standard_id')
                        current_standard_code = None
                        if current_standard_id:
                            for std in nbr_standards_list:
                                if std['id'] == current_standard_id:
                                    current_standard_code = f"{std['code']} - {std['description']}"
                                    break
                        
                        selected_standard = st.selectbox(
                            "Selecione o código NBR:",
                            options=list(standard_options.keys()),
                            index=0 if not current_standard_code else list(standard_options.keys()).index(current_standard_code) if current_standard_code in standard_options else 0,
                            help="💡 Selecione o código NBR que melhor descreve esta causa.",
                            key=f"standard_basic_{node['id']}"
                        )
                        
                        standard_id = standard_options[selected_standard]
                        
                        # Exibe descrição completa do código selecionado
                        selected_std = next((s for s in filtered_standards if s['id'] == standard_id), None)
                        if selected_std:
                            st.markdown(f"**📋 Descrição completa:** {selected_std['description']}")
                        
                        if st.button("💾 Salvar Classificação", key=f"save_basic_{node['id']}"):
                            if link_nbr_standard_to_node(node['id'], standard_id):
                                st.success("✅ Classificação salva!")
                                st.rerun()
                    else:
                        st.warning("⚠️ Nenhum código NBR encontrado para esta categoria.")
                    
                    # Campo de recomendação
                    st.divider()
                    recommendation_key = f"recommendation_basic_{node['id']}"
                    
                    # Título e botão na mesma linha
                    col_title_rec, col_btn_rec = st.columns([3, 1])
                    with col_title_rec:
                        st.markdown("**💡 Recomendação para esta Causa Básica:**")
                    with col_btn_rec:
                        ai_generate_rec_key = f"ai_generate_rec_basic_{node['id']}"
                        if st.button("✨ Gerar com IA", key=ai_generate_rec_key, help="Use IA para gerar recomendações técnicas baseadas na causa, justificativa e dados do acidente"):
                            with st.spinner("🔄 Gerando recomendação com IA..."):
                                try:
                                    # Obtém contexto completo
                                    accident_context = investigation.get('description', '') if investigation else ''
                                    base_location = investigation.get('base_location', '') if investigation else ''
                                    occurrence_date = investigation.get('occurrence_date', '') if investigation else ''
                                    accident_type = investigation.get('type', '') if investigation else ''
                                    
                                    # Contexto das pessoas envolvidas
                                    involved_context = ""
                                    try:
                                        # Tenta usar involved_injured se disponível, senão busca
                                        if 'involved_injured' in locals() and involved_injured:
                                            involved_list = involved_injured
                                        else:
                                            involved_list = get_involved_people(accident_id, 'Injured')
                                        
                                        for inv in involved_list:
                                            if inv.get('name'):
                                                involved_context += f"Vítima: {inv.get('name')}, {inv.get('age', '')} anos, {inv.get('job_title', '')} da empresa {inv.get('company', '')}. "
                                    except:
                                        pass
                                    
                                    # Justificativa atual do nó
                                    current_justification = node.get('justification', '')
                                    current_recommendation = node.get('recommendation', '')
                                    
                                    # Formata a data
                                    try:
                                        if occurrence_date:
                                            date_obj = datetime.fromisoformat(occurrence_date.replace('Z', '+00:00'))
                                            formatted_date_prompt = date_obj.strftime('%d/%m/%Y às %H:%M')
                                        else:
                                            formatted_date_prompt = occurrence_date if occurrence_date else "data não informada"
                                    except:
                                        formatted_date_prompt = occurrence_date if occurrence_date else "data não informada"
                                    
                                    # Constrói prompt para IA gerar recomendação
                                    prompt = f"""Você é um especialista técnico em investigação de acidentes de trabalho, seguindo a metodologia NBR 14280.

TAREFA: {"Melhorar e contextualizar" if current_recommendation else "Gerar"} recomendações técnicas profissionais para prevenir ou corrigir uma causa básica de acidente.

=== CONTEXTO DO ACIDENTE ===
Tipo: {accident_type}
Local: {base_location}
Data/Hora: {formatted_date_prompt}
Descrição completa: {accident_context}
{f'Pessoas envolvidas: {involved_context}' if involved_context else ''}

=== CAUSA BÁSICA A CORRIGIR ===
"{node['label']}"

Esta é a causa básica identificada. As recomendações devem ser específicas para prevenir ou corrigir esta causa.

=== JUSTIFICATIVA DA CAUSA ===
{current_justification if current_justification else 'Nenhuma justificativa disponível ainda.'}

Use a justificativa acima para entender melhor a causa e gerar recomendações mais específicas e efetivas.

{"=== RECOMENDAÇÃO ATUAL (melhorar) ===" if current_recommendation else ""}
{current_recommendation if current_recommendation else ''}
{"Use a recomendação acima como base e melhore-a." if current_recommendation else "Gere recomendações completas e específicas."}

=== INSTRUÇÕES CRÍTICAS ===
{"1. MELHORE a recomendação existente, tornando-a mais específica e acionável" if current_recommendation else "1. GERE recomendações técnicas completas e profissionais"}
2. FOQUE na causa básica "{node['label']}" - as recomendações devem ser específicas para prevenir/corrigir esta causa
3. USE a justificativa como contexto para entender melhor a causa e gerar recomendações mais efetivas
4. USE os dados reais do acidente: local "{base_location}", data "{formatted_date_prompt}", tipo "{accident_type}"
5. SEJA ESPECÍFICO: recomendações devem ser acionáveis, com ações concretas
6. ESTRUTURA: Liste recomendações claras e objetivas, priorizando as mais importantes
7. TOM: Profissional, técnico, adequado para relatório oficial de investigação
8. FOQUE em prevenção: como evitar que esta causa ocorra novamente

=== EXEMPLO DE BOM ESTILO ===
"Para prevenir a causa '{node['label']}' identificada no acidente ocorrido em {base_location} em {formatted_date_prompt}, recomenda-se:
1. [Recomendação específica e acionável]
2. [Recomendação específica e acionável]
3. [Recomendação específica e acionável]"

=== IMPORTANTE ===
- NÃO use termos genéricos ou vagos
- FOQUE em ações concretas e acionáveis
- PRIORIZE recomendações que previnam a causa específica "{node['label']}"
- USE a justificativa como contexto para entender melhor a causa
- GERE pelo menos 3 recomendações específicas
- Retorne APENAS o texto das recomendações, sem explicações ou formatação markdown adicional"""
                                    
                                    # Tenta usar Google Gemini
                                    improved_recommendation = None
                                    error_msg = None
                                    
                                    if GEMINI_AVAILABLE:
                                        try:
                                            api_key = os.getenv('GOOGLE_AI_API_KEY') or st.secrets.get('general', {}).get('GOOGLE_AI_API_KEY', None)
                                            if not api_key:
                                                error_msg = "Chave da API do Google Gemini não configurada. Configure GOOGLE_AI_API_KEY nas variáveis de ambiente ou secrets."
                                            else:
                                                genai.configure(api_key=api_key)
                                                # Usa gemini-3-flash-preview ou gemini-2.5-flash como fallback
                                                try:
                                                    model = genai.GenerativeModel('gemini-3-flash-preview')
                                                except:
                                                    model = genai.GenerativeModel('gemini-2.5-flash')
                                                
                                                # Configuração de segurança e parâmetros
                                                generation_config = {
                                                    "temperature": 0.7,
                                                    "top_p": 0.8,
                                                    "top_k": 40,
                                                    "max_output_tokens": 2048,
                                                }
                                                
                                                response = model.generate_content(
                                                    prompt,
                                                    generation_config=generation_config
                                                )
                                                
                                                # Extrai o texto de forma mais robusta
                                                try:
                                                    improved_recommendation = response.text.strip() if response.text else None
                                                    
                                                    if improved_recommendation:
                                                        if not improved_recommendation.endswith(('.', '!', '?', ':', ';', '\n')):
                                                            st.info("ℹ️ A resposta pode estar incompleta. Revise o texto gerado.")
                                                        
                                                        if len(improved_recommendation) < 50:
                                                            error_msg = "A IA retornou uma resposta muito curta ou vazia."
                                                            improved_recommendation = None
                                                    else:
                                                        error_msg = "A IA retornou uma resposta vazia."
                                                        improved_recommendation = None
                                                except Exception as extract_error:
                                                    error_msg = f"Erro ao extrair texto da resposta: {str(extract_error)}"
                                                    improved_recommendation = None
                                        except Exception as e:
                                            error_msg = f"Erro ao conectar com IA: {str(e)}"
                                            improved_recommendation = None
                                    
                                    # Se não conseguiu usar IA, gera uma recomendação base
                                    if not improved_recommendation:
                                        if current_recommendation:
                                            improved_recommendation = current_recommendation
                                        else:
                                            # Gera uma recomendação contextualizada baseada nos dados reais
                                            improved_recommendation = f"""Para prevenir a causa básica "{node['label']}" identificada no acidente ocorrido em {base_location} em {formatted_date_prompt}, recomenda-se:

1. Implementar medidas preventivas específicas para esta causa
2. Realizar treinamento adequado dos envolvidos
3. Revisar procedimentos e normas relacionadas
4. Estabelecer controles e monitoramento contínuo

Esta recomendação deve ser revisada e complementada com ações específicas baseadas na análise técnica completa da causa."""
                                        
                                        if error_msg:
                                            st.warning(f"⚠️ {error_msg} Uma recomendação base foi gerada automaticamente. Revise e complete com ações específicas.")
                                        elif not GEMINI_AVAILABLE:
                                            st.info("ℹ️ Biblioteca do Google Gemini não disponível. Uma recomendação base foi gerada automaticamente. Revise e complete com ações específicas.")
                                    
                                    # Salva no session_state para preencher o campo
                                    st.session_state[recommendation_key] = improved_recommendation
                                    st.success("✅ Recomendação gerada! Revise o texto abaixo e ajuste se necessário antes de salvar.")
                                    
                                except Exception as e:
                                    st.error(f"❌ Erro ao gerar recomendação: {str(e)}")
                                    st.info("💡 Tente criar a recomendação manualmente usando o contexto do acidente.")
                    
                    # Verifica se a chave já existe no session_state para evitar conflito
                    # Se existir, não passa value= para deixar o Streamlit usar o valor do session_state
                    # Se não existir, inicializa com o valor do node
                    if recommendation_key not in st.session_state:
                        st.session_state[recommendation_key] = node.get('recommendation', '')
                    
                    recommendation = st.text_area(
                        "Descreva as recomendações para prevenir ou corrigir esta causa básica:",
                        key=recommendation_key,
                        help="Esta recomendação aparecerá no relatório PDF ao final, na seção de recomendações.",
                        height=120
                    )
                    if recommendation != node.get('recommendation', ''):
                        if st.button("💾 Salvar Recomendação", key=f"save_recommendation_basic_{node['id']}"):
                            from services.investigation import update_node_recommendation
                            if update_node_recommendation(node['id'], recommendation.strip() if recommendation.strip() else None):
                                st.success("✅ Recomendação salva!")
                                st.rerun()
        
        if contributing_cause_nodes:
            st.markdown("### 🤝 Causas Contribuintes para Classificação")
            st.info(f"💡 Você tem **{len(contributing_cause_nodes)}** causa(s) contribuinte(s) confirmada(s) para classificar.")
            
            for node in contributing_cause_nodes:
                with st.expander(f"🤝 {node['label'][:60]}...", expanded=True):
                    st.markdown(f"**Causa Contribuinte:** {node['label']}")
                    st.info("💡 Esta é uma causa contribuinte confirmada. Classifique-a conforme os padrões NBR 14280.")
                    
                    # Busca padrões NBR por categoria
                    categories = {
                        'unsafe_act': 'Falha Humana (Ato Inseguro)',
                        'unsafe_condition': 'Condição do Ambiente',
                        'personal_factor': 'Fator Pessoal',
                        'management_failure': 'Falha na Gestão',
                        'procedure_failure': 'Falha no Procedimento',
                        'engineering_failure': 'Falha de Engenharia'
                    }
                    
                    # Seleção de categoria
                    selected_category = st.selectbox(
                        "O que falhou?",
                        options=list(categories.keys()),
                        format_func=lambda x: categories[x],
                        help="💡 **Ato Inseguro**: Ação incorreta do trabalhador. **Condição do Ambiente**: Problema no ambiente/máquina. **Fator Pessoal**: Característica pessoal que contribuiu. **Falha na Gestão**: Problemas na gestão/organização. **Falha no Procedimento**: Procedimento inadequado ou ausente. **Falha de Engenharia**: Problema no projeto/engenharia.",
                        key=f"category_{node['id']}"
                    )
                    
                    # Busca padrões NBR filtrados
                    search_term = st.text_input(
                        "🔍 Buscar código NBR (opcional):",
                        placeholder="Ex: treinamento, equipamento, proteção...",
                        key=f"search_contributing_{node['id']}"
                    )
                    
                    # Filtra padrões NBR
                    filtered_standards = [s for s in nbr_standards_list if s['category'] == selected_category]
                    if search_term:
                        search_lower = search_term.lower()
                        filtered_standards = [s for s in filtered_standards if 
                                             search_lower in s['code'].lower() or 
                                             search_lower in s['description'].lower()]
                    
                    if filtered_standards:
                        # Cria opções para selectbox
                        standard_options = {
                            f"{std['code']} - {std['description']}": std['id'] 
                            for std in filtered_standards
                        }
                        
                        # Verifica se já tem padrão vinculado
                        current_standard_id = node.get('nbr_standard_id')
                        current_standard_code = None
                        if current_standard_id:
                            for std in nbr_standards_list:
                                if std['id'] == current_standard_id:
                                    current_standard_code = f"{std['code']} - {std['description']}"
                                    break
                        
                        selected_standard = st.selectbox(
                            "Selecione o código NBR:",
                            options=list(standard_options.keys()),
                            index=0 if not current_standard_code else list(standard_options.keys()).index(current_standard_code) if current_standard_code in standard_options else 0,
                            help="💡 Selecione o código NBR que melhor descreve esta causa.",
                            key=f"standard_contributing_{node['id']}"
                        )
                        
                        standard_id = standard_options[selected_standard]
                        
                        # Exibe descrição completa do código selecionado
                        selected_std = next((s for s in filtered_standards if s['id'] == standard_id), None)
                        if selected_std:
                            st.markdown(f"**📋 Descrição completa:** {selected_std['description']}")
                        
                        if st.button("💾 Salvar Classificação", key=f"save_contributing_{node['id']}"):
                            if link_nbr_standard_to_node(node['id'], standard_id):
                                st.success("✅ Classificação salva!")
                                st.rerun()
                    else:
                        st.warning("⚠️ Nenhum código NBR encontrado para esta categoria.")
                    
                    # Campo de recomendação
                    st.divider()
                    recommendation_key = f"recommendation_contributing_{node['id']}"
                    
                    # Título e botão na mesma linha
                    col_title_rec, col_btn_rec = st.columns([3, 1])
                    with col_title_rec:
                        st.markdown("**💡 Recomendação para esta Causa Contribuinte:**")
                    with col_btn_rec:
                        ai_generate_rec_key = f"ai_generate_rec_contributing_{node['id']}"
                        if st.button("✨ Gerar com IA", key=ai_generate_rec_key, help="Use IA para gerar recomendações técnicas baseadas na causa, justificativa e dados do acidente"):
                            with st.spinner("🔄 Gerando recomendação com IA..."):
                                try:
                                    # Obtém contexto completo
                                    accident_context = investigation.get('description', '') if investigation else ''
                                    base_location = investigation.get('base_location', '') if investigation else ''
                                    occurrence_date = investigation.get('occurrence_date', '') if investigation else ''
                                    accident_type = investigation.get('type', '') if investigation else ''
                                    
                                    # Contexto das pessoas envolvidas
                                    involved_context = ""
                                    try:
                                        # Tenta usar involved_injured se disponível, senão busca
                                        if 'involved_injured' in locals() and involved_injured:
                                            involved_list = involved_injured
                                        else:
                                            involved_list = get_involved_people(accident_id, 'Injured')
                                        
                                        for inv in involved_list:
                                            if inv.get('name'):
                                                involved_context += f"Vítima: {inv.get('name')}, {inv.get('age', '')} anos, {inv.get('job_title', '')} da empresa {inv.get('company', '')}. "
                                    except:
                                        pass
                                    
                                    # Justificativa atual do nó
                                    current_justification = node.get('justification', '')
                                    current_recommendation = node.get('recommendation', '')
                                    
                                    # Formata a data
                                    try:
                                        if occurrence_date:
                                            date_obj = datetime.fromisoformat(occurrence_date.replace('Z', '+00:00'))
                                            formatted_date_prompt = date_obj.strftime('%d/%m/%Y às %H:%M')
                                        else:
                                            formatted_date_prompt = occurrence_date if occurrence_date else "data não informada"
                                    except:
                                        formatted_date_prompt = occurrence_date if occurrence_date else "data não informada"
                                    
                                    # Constrói prompt para IA gerar recomendação
                                    prompt = f"""Você é um especialista técnico em investigação de acidentes de trabalho, seguindo a metodologia NBR 14280.

TAREFA: {"Melhorar e contextualizar" if current_recommendation else "Gerar"} recomendações técnicas profissionais para prevenir ou corrigir uma causa contribuinte de acidente.

=== CONTEXTO DO ACIDENTE ===
Tipo: {accident_type}
Local: {base_location}
Data/Hora: {formatted_date_prompt}
Descrição completa: {accident_context}
{f'Pessoas envolvidas: {involved_context}' if involved_context else ''}

=== CAUSA CONTRIBUINTE A CORRIGIR ===
"{node['label']}"

Esta é a causa contribuinte identificada. As recomendações devem ser específicas para prevenir ou corrigir esta causa.

=== JUSTIFICATIVA DA CAUSA ===
{current_justification if current_justification else 'Nenhuma justificativa disponível ainda.'}

Use a justificativa acima para entender melhor a causa e gerar recomendações mais específicas e efetivas.

{"=== RECOMENDAÇÃO ATUAL (melhorar) ===" if current_recommendation else ""}
{current_recommendation if current_recommendation else ''}
{"Use a recomendação acima como base e melhore-a." if current_recommendation else "Gere recomendações completas e específicas."}

=== INSTRUÇÕES CRÍTICAS ===
{"1. MELHORE a recomendação existente, tornando-a mais específica e acionável" if current_recommendation else "1. GERE recomendações técnicas completas e profissionais"}
2. FOQUE na causa contribuinte "{node['label']}" - as recomendações devem ser específicas para prevenir/corrigir esta causa
3. USE a justificativa como contexto para entender melhor a causa e gerar recomendações mais efetivas
4. USE os dados reais do acidente: local "{base_location}", data "{formatted_date_prompt}", tipo "{accident_type}"
5. SEJA ESPECÍFICO: recomendações devem ser acionáveis, com ações concretas
6. ESTRUTURA: Liste recomendações claras e objetivas, priorizando as mais importantes
7. TOM: Profissional, técnico, adequado para relatório oficial de investigação
8. FOQUE em prevenção: como evitar que esta causa ocorra novamente

=== EXEMPLO DE BOM ESTILO ===
"Para prevenir a causa contribuinte '{node['label']}' identificada no acidente ocorrido em {base_location} em {formatted_date_prompt}, recomenda-se:
1. [Recomendação específica e acionável]
2. [Recomendação específica e acionável]
3. [Recomendação específica e acionável]"

=== IMPORTANTE ===
- NÃO use termos genéricos ou vagos
- FOQUE em ações concretas e acionáveis
- PRIORIZE recomendações que previnam a causa específica "{node['label']}"
- USE a justificativa como contexto para entender melhor a causa
- GERE pelo menos 3 recomendações específicas
- Retorne APENAS o texto das recomendações, sem explicações ou formatação markdown adicional"""
                                    
                                    # Tenta usar Google Gemini
                                    improved_recommendation = None
                                    error_msg = None
                                    
                                    if GEMINI_AVAILABLE:
                                        try:
                                            api_key = os.getenv('GOOGLE_AI_API_KEY') or st.secrets.get('general', {}).get('GOOGLE_AI_API_KEY', None)
                                            if not api_key:
                                                error_msg = "Chave da API do Google Gemini não configurada. Configure GOOGLE_AI_API_KEY nas variáveis de ambiente ou secrets."
                                            else:
                                                genai.configure(api_key=api_key)
                                                # Usa gemini-3-flash-preview ou gemini-2.5-flash como fallback
                                                try:
                                                    model = genai.GenerativeModel('gemini-3-flash-preview')
                                                except:
                                                    model = genai.GenerativeModel('gemini-2.5-flash')
                                                
                                                # Configuração de segurança e parâmetros
                                                generation_config = {
                                                    "temperature": 0.7,
                                                    "top_p": 0.8,
                                                    "top_k": 40,
                                                    "max_output_tokens": 2048,
                                                }
                                                
                                                response = model.generate_content(
                                                    prompt,
                                                    generation_config=generation_config
                                                )
                                                
                                                # Extrai o texto de forma mais robusta
                                                try:
                                                    improved_recommendation = response.text.strip() if response.text else None
                                                    
                                                    if improved_recommendation:
                                                        if not improved_recommendation.endswith(('.', '!', '?', ':', ';', '\n')):
                                                            st.info("ℹ️ A resposta pode estar incompleta. Revise o texto gerado.")
                                                        
                                                        if len(improved_recommendation) < 50:
                                                            error_msg = "A IA retornou uma resposta muito curta ou vazia."
                                                            improved_recommendation = None
                                                    else:
                                                        error_msg = "A IA retornou uma resposta vazia."
                                                        improved_recommendation = None
                                                except Exception as extract_error:
                                                    error_msg = f"Erro ao extrair texto da resposta: {str(extract_error)}"
                                                    improved_recommendation = None
                                        except Exception as e:
                                            error_msg = f"Erro ao conectar com IA: {str(e)}"
                                            improved_recommendation = None
                                    
                                    # Se não conseguiu usar IA, gera uma recomendação base
                                    if not improved_recommendation:
                                        if current_recommendation:
                                            improved_recommendation = current_recommendation
                                        else:
                                            # Gera uma recomendação contextualizada baseada nos dados reais
                                            improved_recommendation = f"""Para prevenir a causa contribuinte "{node['label']}" identificada no acidente ocorrido em {base_location} em {formatted_date_prompt}, recomenda-se:

1. Implementar medidas preventivas específicas para esta causa
2. Realizar treinamento adequado dos envolvidos
3. Revisar procedimentos e normas relacionadas
4. Estabelecer controles e monitoramento contínuo

Esta recomendação deve ser revisada e complementada com ações específicas baseadas na análise técnica completa da causa."""
                                        
                                        if error_msg:
                                            st.warning(f"⚠️ {error_msg} Uma recomendação base foi gerada automaticamente. Revise e complete com ações específicas.")
                                        elif not GEMINI_AVAILABLE:
                                            st.info("ℹ️ Biblioteca do Google Gemini não disponível. Uma recomendação base foi gerada automaticamente. Revise e complete com ações específicas.")
                                    
                                    # Salva no session_state para preencher o campo
                                    st.session_state[recommendation_key] = improved_recommendation
                                    st.success("✅ Recomendação gerada! Revise o texto abaixo e ajuste se necessário antes de salvar.")
                                    
                                except Exception as e:
                                    st.error(f"❌ Erro ao gerar recomendação: {str(e)}")
                                    st.info("💡 Tente criar a recomendação manualmente usando o contexto do acidente.")
                    
                    # Verifica se a chave já existe no session_state para evitar conflito
                    # Se existir, não passa value= para deixar o Streamlit usar o valor do session_state
                    # Se não existir, inicializa com o valor do node
                    if recommendation_key not in st.session_state:
                        st.session_state[recommendation_key] = node.get('recommendation', '')
                    
                    recommendation = st.text_area(
                        "Descreva as recomendações para prevenir ou corrigir esta causa contribuinte:",
                        key=recommendation_key,
                        help="Esta recomendação aparecerá no relatório PDF ao final, na seção de recomendações.",
                        height=120
                    )
                    if recommendation != node.get('recommendation', ''):
                        if st.button("💾 Salvar Recomendação", key=f"save_recommendation_contributing_{node['id']}"):
                            from services.investigation import update_node_recommendation
                            if update_node_recommendation(node['id'], recommendation.strip() if recommendation.strip() else None):
                                st.success("✅ Recomendação salva!")
                                st.rerun()
        
        # Se não houver causas básicas nem contribuintes, mostra mensagem
        if not basic_cause_nodes and not contributing_cause_nodes:
            # Verifica se há causas validadas mas não marcadas como básicas ou contribuintes
            validated_nodes = [n for n in nodes if n['status'] == 'validated']
            if validated_nodes:
                basic_cause_count = len([n for n in validated_nodes if n.get('is_basic_cause', False) == True])
                contributing_cause_count = len([n for n in validated_nodes if n.get('is_contributing_cause', False) == True])
                if basic_cause_count == 0 and contributing_cause_count == 0:
                    st.warning("⚠️ Você tem **causas confirmadas**, mas nenhuma foi marcada como **Causa Básica** ou **Causa Contribuinte**.")
                    st.info("💡 **O que fazer:** Volte ao passo anterior (Árvore de Porquês) e marque as causas usando os checkboxes '🎯 Marcar como Causa Básica' ou '🤝 Marcar como Causa Contribuinte' na seção de validação de hipóteses.")
                else:
                    st.info("💡 Aguarde... recarregando a página.")
                    st.rerun()
            else:
                st.warning("⚠️ Nenhuma causa confirmada ainda. Volte ao passo anterior e valide pelo menos uma hipótese.")
            if st.button("⬅️ Voltar para Árvore de Porquês"):
                st.session_state['current_step'] = 2
                st.rerun()
        
        # Navegação
        col_prev, col_next = st.columns([1, 1])
        with col_prev:
            if st.button("⬅️ Anterior: Árvore de Porquês", width='stretch'):
                st.session_state['current_step'] = 2
                st.rerun()
        with col_next:
            st.success("✅ Investigação concluída! Você pode revisar os dados ou gerar o relatório PDF.")
        
        # ========== GERAÇÃO DE RELATÓRIO ==========
        st.divider()
        st.markdown("### 📄 Relatórios Finais")
        st.markdown("**Gere o relatório completo no padrão Vibra**")
        
        # Botões lado a lado
        col_pdf, col_word = st.columns(2)
        
        with col_pdf:
            if st.button("📥 Gerar Relatório PDF", type="primary", use_container_width=True):
                with st.spinner("🔄 Gerando PDF no padrão Vibra... Isso pode levar alguns segundos."):
                    try:
                        from utils.report_generator import generate_pdf_report
                        
                        # 1. Busca dados completos
                        accident_full = get_accident(accident_id)
                        if not accident_full:
                            st.error("Erro ao buscar dados do acidente")
                            return
                        
                        # 2. Busca pessoas envolvidas
                        all_people = get_involved_people(accident_id)
                        
                        # 3. Busca timeline
                        timeline_events = get_timeline(accident_id)
                        
                        # 4. Busca causas validadas com códigos NBR
                        validated_nodes = get_validated_nodes(accident_id)
                        verified_causes = []
                        
                        # Processa nós validados (já vem com join de nbr_standards)
                        # IMPORTANTE: Só inclui causas que foram validadas E classificadas com código NBR
                        for node in validated_nodes:
                            node_label = node.get('label', 'N/A')
                            nbr_info = node.get('nbr_standards')
                            
                            # Só adiciona se tiver código NBR (foi classificado)
                            if nbr_info:
                                # nbr_standards vem do join (pode ser dict ou list)
                                if isinstance(nbr_info, dict):
                                    verified_causes.append({
                                        'label': node_label,
                                        'nbr_code': nbr_info.get('code', 'N/A'),
                                        'nbr_description': nbr_info.get('description', 'N/A')
                                    })
                                elif isinstance(nbr_info, list) and len(nbr_info) > 0:
                                    nbr = nbr_info[0]
                                    verified_causes.append({
                                        'label': node_label,
                                        'nbr_code': nbr.get('code', 'N/A'),
                                        'nbr_description': nbr.get('description', 'N/A')
                                    })
                            # Se não tiver código NBR, não adiciona à lista (foi removido o else)
                        
                        # 5. Busca evidências
                        evidence_list = get_evidence(accident_id)
                        evidence_images = [e.get('image_url', '') for e in evidence_list if e.get('image_url')]
                        
                        # 5.5. Pré-carrega imagens no session state (mesma lógica da galeria)
                        # Isso garante que as imagens sejam baixadas corretamente antes de gerar o PDF
                        cache_key = f"pdf_images_cache_{accident_id}"
                        if cache_key not in st.session_state:
                            st.session_state[cache_key] = {}
                        
                        # Pré-carrega imagens de evidência
                        for i, img_url in enumerate(evidence_images):
                            if img_url and img_url not in st.session_state[cache_key]:
                                try:
                                    # Extrai o path da URL
                                    path = None
                                    if '/storage/v1/object/public/evidencias/' in img_url:
                                        path = img_url.split('/storage/v1/object/public/evidencias/')[1]
                                    elif '/evidencias/' in img_url:
                                        parts = img_url.split('/evidencias/')
                                        if len(parts) > 1:
                                            path = parts[1]
                                    
                                    # Tenta baixar do Supabase Storage
                                    if path:
                                        from managers.supabase_config import get_service_role_client
                                        supabase = get_service_role_client()
                                        if supabase:
                                            # Decodifica o path para usar no download
                                            from urllib.parse import unquote
                                            decoded_path = unquote(path)
                                            try:
                                                image_bytes = supabase.storage.from_('evidencias').download(decoded_path)
                                                if image_bytes:
                                                    # Converte para base64 e armazena
                                                    import base64
                                                    img_b64 = base64.b64encode(image_bytes).decode('utf-8')
                                                    st.session_state[cache_key][img_url] = f"data:image/jpeg;base64,{img_b64}"
                                                    print(f"[PDF_PRELOAD] Imagem de evidência {i+1} pré-carregada")
                                            except Exception as e:
                                                # Se falhar com path decodificado, tenta com path original
                                                try:
                                                    image_bytes = supabase.storage.from_('evidencias').download(path)
                                                    if image_bytes:
                                                        import base64
                                                        img_b64 = base64.b64encode(image_bytes).decode('utf-8')
                                                        st.session_state[cache_key][img_url] = f"data:image/jpeg;base64,{img_b64}"
                                                        print(f"[PDF_PRELOAD] Imagem de evidência {i+1} pré-carregada (path original)")
                                                except:
                                                    pass
                                except Exception as e:
                                    print(f"[PDF_PRELOAD] Erro ao pré-carregar evidência {i+1}: {str(e)}")
                        
                        # Substitui URLs por versões em cache se disponíveis
                        evidence_images_cached = []
                        for img_url in evidence_images:
                            if img_url in st.session_state[cache_key]:
                                evidence_images_cached.append(st.session_state[cache_key][img_url])
                            else:
                                evidence_images_cached.append(img_url)
                        evidence_images = evidence_images_cached
                        
                        # 6. Busca JSON da árvore para gerar imagem
                        tree_json = build_fault_tree_json(accident_id)
                        
                        # 6.3. Pré-carrega imagens de justificativa das hipóteses
                        if tree_json:
                            def extract_justification_images(node):
                                """Extrai URLs de imagens de justificativa recursivamente"""
                                images = []
                                justification_url = node.get('justification_image_url')
                                if justification_url:
                                    images.append(justification_url)
                                for child in node.get('children', []):
                                    images.extend(extract_justification_images(child))
                                return images
                            
                            justification_image_urls = extract_justification_images(tree_json)
                            
                            # Pré-carrega cada imagem de justificativa
                            for i, img_url in enumerate(justification_image_urls):
                                if img_url and img_url not in st.session_state[cache_key]:
                                    try:
                                        # Extrai o path da URL
                                        path = None
                                        if '/storage/v1/object/public/evidencias/' in img_url:
                                            path = img_url.split('/storage/v1/object/public/evidencias/')[1]
                                        elif '/evidencias/' in img_url:
                                            parts = img_url.split('/evidencias/')
                                            if len(parts) > 1:
                                                path = parts[1]
                                        
                                        # Tenta baixar do Supabase Storage
                                        if path:
                                            from managers.supabase_config import get_service_role_client
                                            supabase = get_service_role_client()
                                            if supabase:
                                                # Decodifica o path para usar no download
                                                from urllib.parse import unquote
                                                decoded_path = unquote(path)
                                                try:
                                                    image_bytes = supabase.storage.from_('evidencias').download(decoded_path)
                                                    if image_bytes:
                                                        # Converte para base64 e armazena
                                                        import base64
                                                        img_b64 = base64.b64encode(image_bytes).decode('utf-8')
                                                        st.session_state[cache_key][img_url] = f"data:image/jpeg;base64,{img_b64}"
                                                        print(f"[PDF_PRELOAD] Imagem de justificativa {i+1} pré-carregada")
                                                except Exception as e:
                                                    # Se falhar com path decodificado, tenta com path original
                                                    try:
                                                        image_bytes = supabase.storage.from_('evidencias').download(path)
                                                        if image_bytes:
                                                            import base64
                                                            img_b64 = base64.b64encode(image_bytes).decode('utf-8')
                                                            st.session_state[cache_key][img_url] = f"data:image/jpeg;base64,{img_b64}"
                                                            print(f"[PDF_PRELOAD] Imagem de justificativa {i+1} pré-carregada (path original)")
                                                    except:
                                                        pass
                                    except Exception as e:
                                        print(f"[PDF_PRELOAD] Erro ao pré-carregar justificativa {i+1}: {str(e)}")
                        
                        # 6.5. Busca ações da comissão
                        commission_actions = get_commission_actions(accident_id)
                        
                        # 7. Gera PDF (passa o cache de imagens)
                        pdf_bytes = generate_pdf_report(
                            accident_data=accident_full,
                            people_data=all_people,
                            timeline_events=timeline_events,
                            verified_causes=verified_causes,
                            evidence_images=evidence_images,
                            fault_tree_json=tree_json,
                            commission_actions=commission_actions,
                            image_cache=st.session_state.get(cache_key, {})
                        )
                        
                        # 8. Botão de download
                        registry_num = accident_full.get('registry_number', 'N/A').replace('/', '-') if accident_full.get('registry_number') else 'N/A'
                        filename = f"Relatorio_Vibra_{registry_num}_{datetime.now().strftime('%Y%m%d')}.pdf"
                        
                        st.success("✅ PDF gerado com sucesso!")
                        st.download_button(
                            label="⬇️ Baixar Relatório PDF",
                            data=pdf_bytes,
                            file_name=filename,
                            mime="application/pdf",
                            type="primary",
                            width='stretch'
                        )
                        
                        st.info("💡 **Dica:** O relatório segue o padrão visual da Vibra com todas as seções do documento original.")
                        
                    except ImportError as e:
                        st.error(f"❌ Erro: Bibliotecas não instaladas. Execute: `pip install jinja2 weasyprint`")
                        st.code("pip install jinja2 weasyprint", language="bash")
                    except Exception as e:
                        st.error(f"❌ Erro ao gerar PDF: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
        
        with col_word:
            if st.button("📄 Gerar Relatório Word", type="secondary", use_container_width=True):
                with st.spinner("🔄 Gerando Word no padrão Vibra... Isso pode levar alguns segundos."):
                    try:
                        from utils.word_generator import generate_word_report
                        
                        # 1. Busca dados completos (reutiliza mesma lógica do PDF)
                        accident_full = get_accident(accident_id)
                        if not accident_full:
                            st.error("Erro ao buscar dados do acidente")
                            return
                        
                        # 2. Busca pessoas envolvidas
                        all_people = get_involved_people(accident_id)
                        
                        # 3. Busca timeline
                        timeline_events = get_timeline(accident_id)
                        
                        # 4. Busca causas validadas com códigos NBR
                        validated_nodes = get_validated_nodes(accident_id)
                        verified_causes = []
                        
                        # Processa nós validados (já vem com join de nbr_standards)
                        for node in validated_nodes:
                            node_label = node.get('label', 'N/A')
                            nbr_info = node.get('nbr_standards')
                            
                            if nbr_info:
                                if isinstance(nbr_info, dict):
                                    verified_causes.append({
                                        'label': node_label,
                                        'nbr_code': nbr_info.get('code', 'N/A'),
                                        'nbr_description': nbr_info.get('description', 'N/A')
                                    })
                                elif isinstance(nbr_info, list) and len(nbr_info) > 0:
                                    nbr = nbr_info[0]
                                    verified_causes.append({
                                        'label': node_label,
                                        'nbr_code': nbr.get('code', 'N/A'),
                                        'nbr_description': nbr.get('description', 'N/A')
                                    })
                        
                        # 5. Busca evidências
                        evidence_list = get_evidence(accident_id)
                        evidence_images = [e.get('image_url', '') for e in evidence_list if e.get('image_url')]
                        
                        # 6. Busca JSON da árvore
                        tree_json = build_fault_tree_json(accident_id)
                        
                        # 7. Busca ações da comissão
                        commission_actions = get_commission_actions(accident_id)
                        
                        # 8. Gera Word
                        word_bytes = generate_word_report(
                            accident_data=accident_full,
                            people_data=all_people,
                            timeline_events=timeline_events,
                            verified_causes=verified_causes,
                            evidence_images=evidence_images,
                            fault_tree_json=tree_json,
                            commission_actions=commission_actions,
                            image_cache=None  # Word não precisa de cache de imagens
                        )
                        
                        # 9. Botão de download
                        registry_num = accident_full.get('registry_number', 'N/A').replace('/', '-') if accident_full.get('registry_number') else 'N/A'
                        filename_word = f"Relatorio_Vibra_{registry_num}_{datetime.now().strftime('%Y%m%d')}.docx"
                        
                        st.success("✅ Word gerado com sucesso!")
                        st.download_button(
                            label="⬇️ Baixar Relatório Word",
                            data=word_bytes,
                            file_name=filename_word,
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            type="secondary",
                            use_container_width=True
                        )
                        
                        st.info("💡 **Dica:** O relatório Word é editável e pode ser ajustado conforme necessário.")
                        
                    except ImportError as e:
                        st.error(f"❌ Erro: Biblioteca não instalada. Execute: `pip install python-docx`")
                        st.code("pip install python-docx", language="bash")
                    except Exception as e:
                        st.error(f"❌ Erro ao gerar Word: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
