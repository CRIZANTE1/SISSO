"""
Página de Investigação de Acidentes - Versão Wizard/Guided
Experiência intuitiva passo a passo baseada em FTA e NBR 14280
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date, time
from typing import Optional, Dict, Any, List
from services.investigation import (
    create_accident,
    get_accidents,
    get_accident,
    update_accident,
    upload_evidence_image,
    get_evidence,
    add_timeline_event,
    get_timeline,
    get_root_node,
    create_root_node,
    add_fault_tree_node,
    get_tree_nodes,
    update_node_status,
    link_nbr_standard_to_node,
    get_nbr_standards,
    get_validated_nodes,
    update_accident_status,
    build_fault_tree_json,
    get_involved_people,
    upsert_involved_people,
    get_sites
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
    
    st.title("🔍 Investigação de Acidentes")
    st.markdown("**Assistente de Análise de Árvore de Falhas (FTA) - NBR 14280**")
    
    # ========== SIDEBAR - CONTEXT MANAGER ==========
    with st.sidebar:
        st.header("📋 Gerenciamento de Investigação")
        
        # Seleção de acidente para investigação
        st.subheader("Selecionar Acidente para Investigação")
        st.info("💡 **Crie o acidente na página 'Acidentes' primeiro, depois selecione aqui para iniciar a investigação.**")
        
        # Botão de refresh para forçar atualização
        if st.button("🔄 Atualizar Lista de Acidentes", help="Clique se o acidente não aparecer"):
            st.session_state['current_accident'] = None
            st.rerun()
        
        # Debug temporário (pode remover depois)
        if st.checkbox("🔍 Debug: Mostrar informações", help="Ativa modo debug para verificar problemas"):
            from auth.auth_utils import get_user_id, is_admin, get_user_email
            user_id = get_user_id()
            user_email = get_user_email()
            st.write(f"**User ID:** {user_id}")
            st.write(f"**User Email:** {user_email}")
            st.write(f"**É Admin:** {is_admin()}")
            
            from managers.supabase_config import get_service_role_client
            supabase = get_service_role_client()
            if supabase:
                all_accidents = supabase.table("accidents").select("id, title, description, created_by").limit(5).execute()
                st.write(f"**Total de acidentes no banco:** {len(all_accidents.data) if all_accidents.data else 0}")
                if all_accidents.data:
                    st.json(all_accidents.data)
        
        investigations = get_accidents()
        
        # Debug: mostra quantos foram encontrados
        if st.session_state.get('debug_mode', False):
            st.write(f"🔍 Debug: {len(investigations)} acidente(s) encontrado(s) pela função get_accidents()")
        
        if investigations:
            # Cria opções com informações do acidente
            investigation_options = {}
            for inv in investigations:
                # Formata a label com informações relevantes
                acc_type = inv.get('type', 'N/A')
                
                # Pega título ou descrição (já normalizado em get_accidents)
                title_text = inv.get('title', 'Acidente sem título')
                if not title_text or title_text == 'Acidente sem título':
                    title_text = inv.get('description', 'Acidente sem título')
                
                # Limita tamanho do título
                if len(title_text) > 35:
                    title_text = title_text[:35] + "..."
                
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
                    label = f"{title_text} | {acc_type} | {acc_date}"
                else:
                    label = f"{title_text} | {acc_type}"
                
                investigation_options[label] = inv['id']
            
            investigation_options["-- Selecione um acidente --"] = None
            
            selected_label = st.selectbox(
                "Acidente:",
                options=list(investigation_options.keys()),
                key="investigation_selector",
                index=0 if not st.session_state.get('current_accident') else None,
                help="Selecione um acidente criado na página 'Acidentes' para iniciar a investigação"
            )
            
            # Obtém o ID do acidente selecionado (NUNCA usa nome/título)
            selected_id = investigation_options.get(selected_label)
            
            # Valida que selected_id é um UUID válido
            if selected_id:
                selected_id = str(selected_id).strip()
                # UUID tem 36 caracteres, mas vamos aceitar qualquer string não vazia
                if len(selected_id) < 10:
                    st.error(f"❌ ID de acidente inválido: {selected_id}")
                    selected_id = None
            
            if selected_id and selected_id != st.session_state.get('current_accident'):
                # Armazena o ID (UUID) no session_state
                st.session_state['current_accident'] = selected_id
                st.session_state['current_step'] = 0  # Reset step ao mudar investigação
                st.rerun()
            elif selected_id is None:
                st.session_state['current_accident'] = None
                st.session_state['current_step'] = 0
        else:
            st.warning("⚠️ Nenhum acidente encontrado.")
            st.info("""
            **Como iniciar uma investigação:**
            1. Vá para a página **"Acidentes"** no menu
            2. Crie um novo acidente usando o formulário
            3. Volte para esta página e selecione o acidente criado
            """)
            st.session_state['current_accident'] = None
            st.session_state['current_step'] = 0
        
        st.divider()
        st.markdown("""
        **📋 Fluxo de Investigação:**
        1. **Criar Acidente** → Página "Acidentes"
        2. **Selecionar Acidente** → Esta página (sidebar)
        3. **Preencher Investigação** → Passos 1-4 abaixo
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
    
    with col_info:
        st.markdown(f"**📋 Investigação:** {investigation.get('title', 'N/A')}")
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
        
        # Campo de quantidade de membros da comissão FORA do form para permitir interação dinâmica
        form_key = f"num_commission_{accident_id}"
        if form_key not in st.session_state:
            st.session_state[form_key] = len(involved_commission) if involved_commission else 0
        
        # Campo de quantidade FORA do form (permite interação dinâmica)
        with st.expander("👔 Configurar Comissão de Investigação", expanded=True):
            num_commission = st.number_input(
                "Quantidade de membros:", 
                min_value=0, 
                max_value=10, 
                value=st.session_state[form_key], 
                key=f"num_commission_input_{accident_id}",
                help="Defina quantos membros da comissão você deseja cadastrar. Os campos aparecerão no formulário abaixo."
            )
            if num_commission != st.session_state[form_key]:
                st.session_state[form_key] = num_commission
                st.rerun()
        
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
                        occ_date = pd.to_datetime(investigation.get('occurrence_date')).date()
                        occ_time = pd.to_datetime(investigation.get('occurrence_date')).time()
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
                
                selected_site_label = st.selectbox(
                    "Base:",
                    options=site_options,
                    index=current_site_index,
                    help="Selecione a base da tabela de sites cadastrados"
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
                    class_injury = st.checkbox(
                        "Com Lesão",
                        value=investigation.get('class_injury', False),
                        help="Acidente com lesão física"
                    )
                    class_environment = st.checkbox(
                        "Meio Ambiente",
                        value=investigation.get('class_environment', False),
                        help="Impacto ambiental"
                    )
                    class_process_safety = st.checkbox(
                        "Segurança de Processo",
                        value=investigation.get('class_process_safety', False),
                        help="Relacionado à segurança de processo"
                    )
                
                with col_class2:
                    class_asset_damage = st.checkbox(
                        "Dano ao Patrimônio",
                        value=investigation.get('class_asset_damage', False),
                        help="Danos materiais/patrimoniais"
                    )
                    class_community = st.checkbox(
                        "Impacto na Comunidade",
                        value=investigation.get('class_community', False),
                        help="Impacto na comunidade local"
                    )
                    class_near_miss = st.checkbox(
                        "Quase-Acidente",
                        value=investigation.get('class_near_miss', False),
                        help="Evento de quase-acidente"
                    )
                
                # Mapeamento entre português (interface) e inglês (banco)
                severity_options_pt = ["", "Baixa", "Média", "Alta", "Catastrófica"]
                severity_options_en = ["", "Low", "Medium", "High", "Catastrophic"]
                
                # Converte valor do banco (inglês) para índice em português
                current_severity_en = investigation.get('severity_level', '') or ''
                current_index = 0
                if current_severity_en and current_severity_en in severity_options_en:
                    current_index = severity_options_en.index(current_severity_en)
                
                severity_level_pt = st.selectbox(
                    "Nível de Gravidade:",
                    options=severity_options_pt,
                    index=current_index,
                    help="Gravidade do acidente: Baixa, Média, Alta ou Catastrófica"
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
                with st.expander("🔬 Seção 3: Detalhes do Vazamento/Processo", expanded=True):
                    st.info("💡 Esta seção aparece porque você marcou 'Meio Ambiente' ou 'Segurança de Processo'")
                    
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
            with st.expander("👥 Seção 4: Pessoas Envolvidas", expanded=True):
                st.markdown("**Motoristas, Vítimas e Testemunhas**")
                
                # Motoristas
                st.subheader("🚗 Motoristas")
                num_drivers = st.number_input("Quantidade de motoristas:", min_value=0, max_value=10, value=len(involved_drivers), key="num_drivers")
                drivers = []
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
                            drivers.append({
                                'person_type': 'Driver',
                                'name': driver_name,
                                'registration_id': driver_reg or None,
                                'job_title': driver_role or None,
                                'company': driver_company or None,
                                'age': driver_age if driver_age else None,
                                'aso_date': driver_aso.isoformat() if driver_aso else None
                            })
                
                # Vítimas/Lesionados
                st.subheader("🏥 Vítimas/Lesionados")
                num_injured = st.number_input("Quantidade de vítimas:", min_value=0, max_value=10, value=len(involved_injured), key="num_injured")
                injured = []
                for i in range(num_injured):
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
                st.subheader("👁️ Testemunhas")
                num_witnesses = st.number_input("Quantidade de testemunhas:", min_value=0, max_value=10, value=len(involved_witnesses), key="num_witnesses")
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
                num_commission = st.session_state[form_key]
                
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
                                training_status = involved_commission[i].get('training_status')
                                if training_status and isinstance(training_status, str):
                                    comm_role_current = training_status
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
                                'training_status': comm_role or None  # Função na comissão (usando campo training_status temporariamente)
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
                if st.form_submit_button("💾 Salvar Dados e Continuar", type="primary", use_container_width=True):
                    # Atualiza dados do acidente
                    update_data = {
                        'registry_number': registry_number if registry_number else None,
                        'base_location': base_location if base_location else None,
                        'site_id': selected_site_id,
                        'title': title,
                        'description': description if description else None,
                        'occurrence_date': occurrence_datetime.isoformat() if occurrence_datetime else None,
                        'class_injury': class_injury,
                        'class_community': class_community,
                        'class_environment': class_environment,
                        'class_process_safety': class_process_safety,
                        'class_asset_damage': class_asset_damage,
                        'class_near_miss': class_near_miss,
                        'severity_level': severity_level if severity_level else None,
                        'estimated_loss_value': estimated_loss_value if estimated_loss_value > 0 else None
                    }
                    
                    # Adiciona dados de processo se a seção foi exibida
                    if show_process_details:
                        update_data.update({
                            'product_released': product_released if product_released else None,
                            'volume_released': volume_released if volume_released > 0 else None,
                            'volume_recovered': volume_recovered if volume_recovered > 0 else None,
                            'release_duration_hours': release_duration_hours if release_duration_hours > 0 else None,
                            'equipment_involved': equipment_involved if equipment_involved else None,
                            'area_affected': area_affected if area_affected else None
                        })
                    
                    # Debug: mostra dados que serão salvos
                    if st.session_state.get('debug_save', False):
                        st.json(update_data)
                        st.write(f"Accident ID: {accident_id}")
                    
                    # Salva dados do acidente
                    success = update_accident(accident_id, **update_data)
                    
                    if success:
                        # Salva pessoas envolvidas
                        all_people = drivers + injured + witnesses + commission
                        people_success = upsert_involved_people(accident_id, all_people)
                        
                        if people_success:
                            st.success("✅ Dados salvos com sucesso!")
                        else:
                            st.warning("⚠️ Dados do acidente salvos, mas houve problema ao salvar pessoas envolvidas.")
                        
                        # Avança para próximo passo
                        st.session_state['current_step'] = 1
                        st.rerun()
                    else:
                        st.error("❌ Erro ao salvar dados. Verifique os campos e tente novamente.")
            
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
                            if evidence.get('image_url'):
                                st.image(evidence['image_url'], use_container_width=True)
                                st.caption(evidence.get('description', 'Sem descrição'))
        else:
            st.info("📭 Nenhuma evidência adicionada ainda. Adicione fotos para documentar o acidente.")
        
        # Navegação
        col_prev, col_next = st.columns([1, 1])
        with col_next:
            if st.button("➡️ Próximo: Linha do Tempo", type="primary", use_container_width=True):
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
                event_time = event['event_time']
                description = event['description']
                
                st.markdown(f"""
                <div style="border-left: 3px solid #1f77b4; padding-left: 15px; margin: 10px 0;">
                    <strong>🕐 {event_time.strftime('%d/%m/%Y %H:%M')}</strong><br>
                    {description}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("📭 Nenhum evento adicionado ainda. Adicione eventos na ordem cronológica.")
        
        # Navegação
        col_prev, col_next = st.columns([1, 1])
        with col_prev:
            if st.button("⬅️ Anterior: Fatos & Fotos", use_container_width=True):
                st.session_state['current_step'] = 0
                st.rerun()
        with col_next:
            if st.button("➡️ Próximo: Árvore de Porquês", type="primary", use_container_width=True):
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
            if GRAPHVIZ_AVAILABLE:
                try:
                    tree_graph = render_fault_tree_graph_from_json(tree_json)
                    if tree_graph:
                        st.graphviz_chart(tree_graph.source)
                        
                        # Legenda de cores
                        st.markdown("""
                        <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin: 10px 0;">
                            <strong>Legenda:</strong><br>
                            🟢 <span style="color: #28a745;">Verde</span> = Causa confirmada (Verdadeiro)<br>
                            🔴 <span style="color: #dc3545;">Vermelho</span> = Causa descartada (Falso)<br>
                            ⚪ <span style="color: #6c757d;">Cinza</span> = Em análise (Investigando...)
                        </div>
                        """, unsafe_allow_html=True)
                except Exception as e:
                    st.warning(f"Erro ao renderizar árvore: {str(e)}")
                    st.json(tree_json)
            else:
                st.info("📋 Graphviz não disponível - Exibindo estrutura:")
                st.json(tree_json)
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
            
            st.markdown(f"**Pergunta:** Por que **{selected_parent_label}** aconteceu?")
        else:
            parent_id = None
            st.info("ℹ️ Adicione a primeira causa relacionada ao evento principal.")
        
        # Tipo de causa
        node_type = st.radio(
            "Tipo de causa:",
            options=['hypothesis', 'fact'],
            format_func=lambda x: "Hipótese (precisa validar)" if x == 'hypothesis' else "Fato confirmado",
            help="💡 **Hipótese**: Uma possível causa que você precisa investigar e validar. **Fato**: Uma causa já confirmada com evidências.",
            key="node_type_selector"
        )
        
        node_label = st.text_area(
            "Qual é a causa?",
            placeholder="Ex: Falta de treinamento do operador",
            height=100,
            help="💡 Liste todas as causas possíveis, mesmo que não tenha certeza. Você poderá validá-las depois.",
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
        st.markdown("### ✅ Validar Hipóteses")
        st.markdown("**Revise cada hipótese e confirme se é verdadeira ou falsa:**")
        
        hypothesis_nodes = [n for n in nodes if n['type'] == 'hypothesis']
        
        if hypothesis_nodes:
            for node in hypothesis_nodes:
                current_status = node['status']
                
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
                
                with st.expander(f"{status_text}: {node['label'][:60]}...", expanded=False):
                    st.markdown(f"**Hipótese:** {node['label']}")
                    st.markdown(f"**Status atual:** {status_text}")
                    
                    col_val, col_disc, col_pend = st.columns(3)
                    
                    with col_val:
                        if st.button("✅ Confirmar/Verdadeiro", key=f"validate_{node['id']}", 
                                   help="Use quando tiver evidências que confirmam esta causa"):
                            if update_node_status(node['id'], 'validated'):
                                st.success("✅ Hipótese confirmada!")
                                st.rerun()
                    
                    with col_disc:
                        if st.button("❌ Descartar/Falso", key=f"discard_{node['id']}",
                                   help="Use quando tiver evidências que descartam esta causa"):
                            if update_node_status(node['id'], 'discarded'):
                                st.success("❌ Hipótese descartada!")
                                st.rerun()
                    
                    with col_pend:
                        if current_status != 'pending':
                            if st.button("⏳ Em Análise", key=f"pending_{node['id']}",
                                       help="Voltar ao status de investigação"):
                                if update_node_status(node['id'], 'pending'):
                                    st.success("⏳ Status alterado para em análise!")
                                    st.rerun()
        else:
            st.info("📭 Nenhuma hipótese para validar ainda. Adicione hipóteses acima.")
        
        # Verifica se há causas validadas para desbloquear próximo passo
        validated_count = len([n for n in nodes if n['status'] == 'validated'])
        
        # Navegação
        col_prev, col_next = st.columns([1, 1])
        with col_prev:
            if st.button("⬅️ Anterior: Linha do Tempo", use_container_width=True):
                st.session_state['current_step'] = 1
                st.rerun()
        with col_next:
            if validated_count > 0:
                if st.button("➡️ Próximo: Classificação", type="primary", use_container_width=True):
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
        
        # Busca nós validados
        nodes = get_tree_nodes(accident_id)
        validated_nodes = [n for n in nodes if n['status'] == 'validated']
        
        if validated_nodes:
            st.markdown("### ✅ Causas Confirmadas para Classificação")
            st.info(f"💡 Você tem **{len(validated_nodes)}** causa(s) confirmada(s) para classificar.")
            
            for node in validated_nodes:
                with st.expander(f"✅ {node['label'][:60]}...", expanded=True):
                    st.markdown(f"**Causa confirmada:** {node['label']}")
                    
                    # Busca padrões NBR por categoria
                    categories = {
                        'unsafe_act': 'Falha Humana (Ato Inseguro)',
                        'unsafe_condition': 'Condição do Ambiente',
                        'personal_factor': 'Fator Pessoal'
                    }
                    
                    # Seleção de categoria
                    selected_category = st.selectbox(
                        "O que falhou?",
                        options=list(categories.keys()),
                        format_func=lambda x: categories[x],
                        help="💡 **Ato Inseguro**: Ação incorreta do trabalhador. **Condição do Ambiente**: Problema no ambiente/máquina. **Fator Pessoal**: Característica pessoal que contribuiu.",
                        key=f"category_{node['id']}"
                    )
                    
                    # Busca padrões da categoria
                    nbr_standards_list = get_nbr_standards(selected_category)
                    
                    if nbr_standards_list:
                        # Campo de busca inteligente
                        search_term = st.text_input(
                            "🔍 Buscar código NBR (digite palavras-chave):",
                            placeholder="Ex: treinamento, conhecimento, experiência...",
                            help="💡 Digite palavras relacionadas à causa. O sistema filtrará os códigos NBR relevantes.",
                            key=f"search_{node['id']}"
                        )
                        
                        # Filtra padrões baseado na busca
                        if search_term:
                            search_lower = search_term.lower()
                            filtered_standards = [
                                std for std in nbr_standards_list
                                if search_lower in std['description'].lower() or 
                                   search_lower in std['code'].lower()
                            ]
                        else:
                            filtered_standards = nbr_standards_list
                        
                        if filtered_standards:
                            # Cria opções para selectbox
                            standard_options = {f"{std['code']} - {std['description']}": std['id'] 
                                              for std in filtered_standards}
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
                                "Selecione o código NBR:",
                                options=list(standard_options.keys()),
                                index=0 if not current_standard_code else list(standard_options.keys()).index(current_standard_code) if current_standard_code in standard_options else 0,
                                help="💡 Selecione o código NBR que melhor descreve esta causa.",
                                key=f"standard_{node['id']}"
                            )
                            
                            standard_id = standard_options[selected_standard]
                            
                            # Exibe descrição completa do código selecionado
                            if selected_standard != "Nenhum":
                                selected_std_obj = next((s for s in filtered_standards if s['id'] == standard_id), None)
                                if selected_std_obj:
                                    st.success(f"📋 **Código selecionado:** {selected_std_obj['code']}")
                                    st.info(f"**Descrição:** {selected_std_obj['description']}")
                            
                            if st.button("💾 Salvar Classificação", key=f"save_{node['id']}"):
                                if standard_id:
                                    if link_nbr_standard_to_node(node['id'], standard_id):
                                        st.success(f"✅ Padrão NBR vinculado: {selected_standard}")
                                        st.rerun()
                                else:
                                    st.info("Nenhum padrão selecionado")
                        else:
                            st.warning(f"🔍 Nenhum código encontrado para '{search_term}'. Tente outras palavras-chave.")
                    else:
                        st.warning("Nenhum padrão encontrado para esta categoria")
        else:
            st.warning("⚠️ Nenhuma causa confirmada ainda. Volte ao passo anterior e valide pelo menos uma hipótese.")
            if st.button("⬅️ Voltar para Árvore de Porquês"):
                st.session_state['current_step'] = 2
                st.rerun()
        
        # Navegação
        col_prev, col_next = st.columns([1, 1])
        with col_prev:
            if st.button("⬅️ Anterior: Árvore de Porquês", use_container_width=True):
                st.session_state['current_step'] = 2
                st.rerun()
        with col_next:
            st.success("✅ Investigação concluída! Você pode revisar os dados ou gerar o relatório PDF.")
        
        # ========== GERAÇÃO DE RELATÓRIO PDF ==========
        st.divider()
        st.markdown("### 📄 Relatório Final PDF")
        st.markdown("**Gere o relatório completo no padrão Vibra**")
        
        if st.button("📥 Gerar Relatório PDF Oficial", type="primary", use_container_width=True):
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
                    for node in validated_nodes:
                        node_label = node.get('label', 'N/A')
                        nbr_info = node.get('nbr_standards')
                        
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
                        else:
                            # Nó validado mas sem código NBR ainda
                            verified_causes.append({
                                'label': node_label,
                                'nbr_code': 'Pendente',
                                'nbr_description': 'Aguardando classificação NBR'
                            })
                    
                    # 5. Busca evidências
                    evidence_list = get_evidence(accident_id)
                    evidence_images = [e.get('image_url', '') for e in evidence_list if e.get('image_url')]
                    
                    # 6. Busca JSON da árvore para gerar imagem
                    tree_json = build_fault_tree_json(accident_id)
                    
                    # 7. Gera PDF
                    pdf_bytes = generate_pdf_report(
                        accident_data=accident_full,
                        people_data=all_people,
                        timeline_events=timeline_events,
                        verified_causes=verified_causes,
                        evidence_images=evidence_images,
                        fault_tree_json=tree_json
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
                        use_container_width=True
                    )
                    
                    st.info("💡 **Dica:** O relatório segue o padrão visual da Vibra com todas as seções do documento original.")
                    
                except ImportError as e:
                    st.error(f"❌ Erro: Bibliotecas não instaladas. Execute: `pip install jinja2 weasyprint`")
                    st.code("pip install jinja2 weasyprint", language="bash")
                except Exception as e:
                    st.error(f"❌ Erro ao gerar PDF: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
