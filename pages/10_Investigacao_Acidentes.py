"""
Página de Investigação de Acidentes
Módulo completo baseado em FTA (Fault Tree Analysis) e NBR 14280
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date, time
from typing import Optional, Dict, Any, List
from services.investigation import (
    create_accident_investigation,
    get_accident_investigations,
    get_accident_investigation,
    upload_evidence_image,
    get_evidence,
    add_timeline_event,
    get_timeline,
    add_fault_tree_node,
    get_tree_nodes,
    update_node_validation_status,
    link_nbr_standard_to_node,
    get_nbr_standards,
    get_validated_nodes,
    update_accident_status
)
from auth.auth_utils import require_login

# Verifica disponibilidade do graphviz
try:
    import graphviz
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False


def render_fault_tree_graph(nodes: List[Dict[str, Any]]):
    """Renderiza a árvore de falhas usando graphviz"""
    if not GRAPHVIZ_AVAILABLE:
        return None
    import graphviz
    dot = graphviz.Digraph(comment='Fault Tree Analysis')
    dot.attr(rankdir='TB')
    dot.attr('node', shape='box', style='rounded')
    
    # Cores baseadas no status
    color_map = {
        'validated': 'green',
        'discarded': 'red',
        'pending': 'gray'
    }
    
    # Adiciona nós
    for node in nodes:
        node_id = str(node['id'])
        description = node['description'][:50] + '...' if len(node['description']) > 50 else node['description']
        status = node['validation_status']
        node_type = node['node_type']
        
        # Define cor e estilo
        color = color_map.get(status, 'gray')
        style = 'filled'
        if status == 'discarded':
            style = 'filled,strikethrough'
        
        # Label com tipo e status
        label = f"{description}\n[{node_type}]"
        if status == 'discarded':
            label = f"~~{description}~~\n[{node_type}] - DESCARTADO"
        
        dot.node(node_id, label, fillcolor=color, style=style, fontcolor='white' if status != 'pending' else 'black')
    
    # Adiciona arestas (relações pai-filho)
    for node in nodes:
        if node.get('parent_id'):
            dot.edge(str(node['parent_id']), str(node['id']))
    
    return dot


def main():
    require_login()
    
    st.title("🔍 Investigação de Acidentes")
    st.markdown("**Módulo de Análise de Árvore de Falhas (FTA) baseado em NBR 14280**")
    
    # Seleção/Criação de Investigação
    col1, col2 = st.columns([2, 1])
    
    with col1:
        investigations = get_accident_investigations()
        investigation_options = {f"{inv['top_event_description'][:50]}... ({inv['status']})": inv['id'] 
                                for inv in investigations}
        
        if investigation_options:
            selected_inv = st.selectbox(
                "Selecione uma investigação existente:",
                options=list(investigation_options.keys()),
                key="investigation_selector"
            )
            accident_id = investigation_options[selected_inv]
        else:
            accident_id = None
            st.info("Nenhuma investigação encontrada. Crie uma nova abaixo.")
    
    with col2:
        if st.button("➕ Nova Investigação", type="primary"):
            st.session_state.show_new_investigation = True
    
    # Modal para nova investigação
    if st.session_state.get('show_new_investigation', False):
        with st.form("new_investigation_form"):
            st.subheader("Nova Investigação de Acidente")
            top_event = st.text_area(
                "Descrição do Evento Principal (Top Event):",
                placeholder="Ex: Queda de funcionário durante manutenção de equipamento",
                height=100
            )
            
            col_submit, col_cancel = st.columns(2)
            with col_submit:
                submitted = st.form_submit_button("Criar Investigação", type="primary")
            with col_cancel:
                cancelled = st.form_submit_button("Cancelar")
            
            if submitted and top_event:
                new_id = create_accident_investigation(top_event)
                if new_id:
                    st.success("✅ Investigação criada com sucesso!")
                    st.session_state.show_new_investigation = False
                    st.rerun()
                else:
                    st.error("Erro ao criar investigação")
            
            if cancelled:
                st.session_state.show_new_investigation = False
                st.rerun()
    
    # Se não há investigação selecionada, não mostra as abas
    if not accident_id:
        st.info("👆 Selecione uma investigação existente ou crie uma nova para começar.")
        return
    
    # Carrega dados da investigação
    investigation = get_accident_investigation(accident_id)
    if not investigation:
        st.error("Investigação não encontrada")
        return
    
    # Header da investigação
    st.divider()
    col_status, col_desc = st.columns([1, 3])
    with col_status:
        status_color = "🟢" if investigation['status'] == 'Open' else "🔴"
        st.markdown(f"**Status:** {status_color} {investigation['status']}")
        new_status = "Closed" if investigation['status'] == 'Open' else "Open"
        if st.button(f"Alterar para {new_status}"):
            if update_accident_status(accident_id, new_status):
                st.rerun()
    
    with col_desc:
        st.markdown(f"**Evento Principal:** {investigation['top_event_description']}")
        st.caption(f"Criado em: {investigation['created_at']}")
    
    st.divider()
    
    # Abas principais
    tab1, tab2, tab3, tab4 = st.tabs([
        "📸 Evidências e Ações Imediatas",
        "📅 Cronologia",
        "🌳 Árvore de Falhas",
        "📋 Classificação Técnica"
    ])
    
    # ========== ABA 1: EVIDÊNCIAS ==========
    with tab1:
        st.subheader("Evidências e Ações Imediatas")
        st.markdown("**Colete e documente todas as evidências do acidente**")
        
        # Formulário de upload
        with st.expander("➕ Adicionar Evidência", expanded=False):
            uploaded_file = st.file_uploader(
                "Selecione uma imagem:",
                type=['png', 'jpg', 'jpeg'],
                help="Formatos suportados: PNG, JPG, JPEG"
            )
            evidence_description = st.text_area(
                "Descrição da evidência:",
                placeholder="Descreva o que a imagem mostra...",
                height=80
            )
            
            if st.button("📤 Upload Evidência", type="primary"):
                if uploaded_file and evidence_description:
                    file_bytes = uploaded_file.read()
                    result = upload_evidence_image(accident_id, file_bytes, uploaded_file.name, evidence_description)
                    if result:
                        st.success("✅ Evidência enviada com sucesso!")
                        st.rerun()
                else:
                    st.warning("⚠️ Selecione um arquivo e forneça uma descrição")
        
        # Galeria de evidências
        st.markdown("### 📷 Galeria de Evidências")
        evidence_list = get_evidence(accident_id)
        
        if evidence_list:
            # Organiza em grid
            cols_per_row = 3
            for i in range(0, len(evidence_list), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, col in enumerate(cols):
                    if i + j < len(evidence_list):
                        evidence = evidence_list[i + j]
                        with col:
                            if evidence.get('image_url'):
                                st.image(evidence['image_url'], use_container_width=True)
                                st.caption(evidence.get('description', 'Sem descrição'))
                                st.caption(f"📅 {evidence.get('uploaded_at', '')[:10]}")
        else:
            st.info("📭 Nenhuma evidência adicionada ainda.")
    
    # ========== ABA 2: CRONOLOGIA ==========
    with tab2:
        st.subheader("Cronologia de Eventos")
        st.markdown("**Reconstrua a sequência temporal dos eventos**")
        
        # Formulário para adicionar evento
        with st.expander("➕ Adicionar Evento à Timeline", expanded=False):
            col_date, col_time = st.columns(2)
            with col_date:
                event_date = st.date_input("Data do evento:", value=date.today())
            with col_time:
                event_time_input = st.time_input("Hora do evento:", value=time(12, 0))
            
            event_datetime = datetime.combine(event_date, event_time_input)
            
            event_description = st.text_area(
                "Descrição do evento:",
                placeholder="Descreva o que aconteceu neste momento...",
                height=100
            )
            
            if st.button("➕ Adicionar Evento", type="primary"):
                if event_description:
                    if add_timeline_event(accident_id, event_datetime, event_description):
                        st.success("✅ Evento adicionado à timeline!")
                        st.rerun()
                else:
                    st.warning("⚠️ Forneça uma descrição do evento")
        
        # Timeline visual
        st.markdown("### ⏱️ Linha do Tempo")
        timeline_events = get_timeline(accident_id)
        
        if timeline_events:
            # Cria DataFrame para visualização
            timeline_df = pd.DataFrame(timeline_events)
            timeline_df['event_time'] = pd.to_datetime(timeline_df['event_time'])
            timeline_df = timeline_df.sort_values('event_time')
            
            # Exibe timeline
            for idx, event in timeline_df.iterrows():
                event_time = event['event_time']
                description = event['description']
                
                st.markdown(f"""
                <div style="border-left: 3px solid #1f77b4; padding-left: 15px; margin: 10px 0;">
                    <strong>🕐 {event_time.strftime('%d/%m/%Y %H:%M')}</strong><br>
                    {description}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("📭 Nenhum evento adicionado à timeline ainda.")
    
    # ========== ABA 3: ÁRVORE DE FALHAS ==========
    with tab3:
        st.subheader("Construção da Árvore de Falhas (FTA)")
        st.markdown("**Identifique causas e hipóteses usando análise de árvore de falhas**")
        
        # Visualização da árvore
        st.markdown("### 🌳 Estrutura da Árvore")
        nodes = get_tree_nodes(accident_id)
        
        if nodes:
            # Renderiza gráfico
            if GRAPHVIZ_AVAILABLE:
                try:
                    tree_graph = render_fault_tree_graph(nodes)
                    if tree_graph:
                        st.graphviz_chart(tree_graph.source)
                    else:
                        raise Exception("Graphviz não disponível")
                except Exception as e:
                    st.warning(f"Erro ao renderizar árvore: {str(e)}")
                    # Fallback: exibe lista
                    for node in nodes:
                        status_icon = "✅" if node['validation_status'] == 'validated' else "❌" if node['validation_status'] == 'discarded' else "⏳"
                        st.markdown(f"{status_icon} **{node['node_type']}**: {node['description']}")
            else:
                # Fallback: exibe lista quando graphviz não está disponível
                st.info("📋 Visualização em lista (Graphviz não disponível)")
                for node in nodes:
                    status_icon = "✅" if node['validation_status'] == 'validated' else "❌" if node['validation_status'] == 'discarded' else "⏳"
                    status_text = "Validado" if node['validation_status'] == 'validated' else "Descartado" if node['validation_status'] == 'discarded' else "Pendente"
                    st.markdown(f"{status_icon} **{node['node_type'].upper()}** - {node['description']} [{status_text}]")
        else:
            st.info("🌱 A árvore ainda não possui nós. Adicione o primeiro nó (Top Event) abaixo.")
        
        st.divider()
        
        # Adicionar nó
        st.markdown("### ➕ Adicionar Nó à Árvore")
        
        # Seleção de nó pai
        parent_options = {"Nenhum (Nó Raiz)": None}
        for node in nodes:
            node_label = f"{node['description'][:50]}... [{node['node_type']}]"
            parent_options[node_label] = node['id']
        
        selected_parent_label = st.selectbox(
            "Nó Pai (selecione o nó ao qual este se conecta):",
            options=list(parent_options.keys()),
            help="Selecione o nó pai. Para o primeiro nó, selecione 'Nenhum'"
        )
        parent_id = parent_options[selected_parent_label]
        
        # Tipo de nó
        node_type = st.selectbox(
            "Tipo de nó:",
            options=['root', 'hypothesis', 'fact'],
            help="root: Evento principal, hypothesis: Hipótese a validar, fact: Fato confirmado"
        )
        
        node_description = st.text_area(
            "Descrição do nó (hipótese ou fato):",
            placeholder="Ex: Falta de treinamento do operador",
            height=100
        )
        
        if st.button("➕ Adicionar Nó", type="primary"):
            if node_description:
                new_node_id = add_fault_tree_node(accident_id, parent_id, node_description, node_type)
                if new_node_id:
                    st.success("✅ Nó adicionado à árvore!")
                    st.rerun()
            else:
                st.warning("⚠️ Forneça uma descrição do nó")
        
        st.divider()
        
        # Validação de hipóteses
        st.markdown("### ✅ Validação de Hipóteses")
        hypothesis_nodes = [n for n in nodes if n['node_type'] == 'hypothesis']
        
        if hypothesis_nodes:
            for node in hypothesis_nodes:
                with st.expander(f"⏳ {node['description'][:60]}...", expanded=False):
                    current_status = node['validation_status']
                    st.markdown(f"**Status atual:** {current_status}")
                    
                    col_val, col_disc, col_pend = st.columns(3)
                    
                    with col_val:
                        if st.button("✅ Validar", key=f"validate_{node['id']}"):
                            if update_node_validation_status(node['id'], 'validated'):
                                st.success("✅ Hipótese validada!")
                                st.rerun()
                    
                    with col_disc:
                        if st.button("❌ Descartar", key=f"discard_{node['id']}"):
                            if update_node_validation_status(node['id'], 'discarded'):
                                st.success("❌ Hipótese descartada!")
                                st.rerun()
                    
                    with col_pend:
                        if current_status != 'pending':
                            if st.button("⏳ Pendente", key=f"pending_{node['id']}"):
                                if update_node_validation_status(node['id'], 'pending'):
                                    st.success("⏳ Status alterado para pendente!")
                                    st.rerun()
        else:
            st.info("📭 Nenhuma hipótese para validar ainda.")
    
    # ========== ABA 4: CLASSIFICAÇÃO TÉCNICA ==========
    with tab4:
        st.subheader("Classificação Técnica (NBR 14280)")
        st.markdown("**Classifique as causas validadas conforme padrões NBR 14280**")
        
        validated_nodes = [n for n in nodes if n['validation_status'] == 'validated']
        
        if validated_nodes:
            st.markdown("### 📋 Nós Validados para Classificação")
            
            for node in validated_nodes:
                with st.expander(f"✅ {node['description'][:60]}...", expanded=False):
                    # Busca padrões NBR por categoria
                    categories = {
                        'unsafe_act': 'Atos Inseguros',
                        'unsafe_condition': 'Condições Inseguras',
                        'personal_factor': 'Fatores Pessoais',
                        'accident_type': 'Tipos de Acidente'
                    }
                    
                    selected_category = st.selectbox(
                        "Categoria NBR:",
                        options=list(categories.keys()),
                        format_func=lambda x: categories[x],
                        key=f"category_{node['id']}"
                    )
                    
                    # Busca padrões da categoria selecionada
                    nbr_standards_list = get_nbr_standards(selected_category)
                    
                    if nbr_standards_list:
                        # Cria opções para selectbox
                        standard_options = {f"{std['code']} - {std['description']}": std['id'] 
                                          for std in nbr_standards_list}
                        standard_options["Nenhum"] = None
                        
                        # Verifica se já tem padrão vinculado
                        current_standard_id = node.get('nbr_standard_id')
                        current_standard_code = None
                        if current_standard_id:
                            for std in nbr_standards_list:
                                if std['id'] == current_standard_id:
                                    current_standard_code = f"{std['code']} - {std['description']}"
                                    break
                        
                        selected_standard = st.selectbox(
                            "Padrão NBR:",
                            options=list(standard_options.keys()),
                            index=0 if not current_standard_code else list(standard_options.keys()).index(current_standard_code) if current_standard_code in standard_options else 0,
                            key=f"standard_{node['id']}"
                        )
                        
                        standard_id = standard_options[selected_standard]
                        
                        if st.button("💾 Salvar Classificação", key=f"save_{node['id']}"):
                            if standard_id:
                                if link_nbr_standard_to_node(node['id'], standard_id):
                                    st.success(f"✅ Padrão NBR vinculado: {selected_standard}")
                                    st.rerun()
                            else:
                                st.info("Nenhum padrão selecionado")
                    else:
                        st.warning("Nenhum padrão encontrado para esta categoria")
        else:
            st.info("📭 Nenhum nó validado ainda. Valide hipóteses na aba 'Árvore de Falhas' primeiro.")


if __name__ == "__main__":
    main()

