import streamlit as st
from auth.auth_utils import require_login, show_user_info
from components.filters import create_filter_sidebar
from utils.simple_logger import get_logger

# Configuração da página
st.set_page_config(
    page_title="Sistema SSO - Monitoramento",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None  # Remove menu padrão do Streamlit
)

# CSS e JavaScript para garantir que menus apareçam apenas no topo e remover completamente qualquer navegação da sidebar
st.markdown("""
<style>
    /* Esconde completamente qualquer navegação na sidebar - seletores abrangentes */
    [data-testid="stSidebar"] [data-testid="stNavigation"],
    [data-testid="stSidebar"] nav,
    [data-testid="stSidebar"] .stNavigation,
    [data-testid="stSidebar"] [class*="navigation"],
    [data-testid="stSidebar"] [class*="Navigation"],
    [data-testid="stSidebar"] ul[role="navigation"],
    [data-testid="stSidebar"] div[role="navigation"],
    [data-testid="stSidebar"] [data-testid="stSidebarNav"],
    [data-testid="stSidebar"] [class*="sidebar-nav"],
    [data-testid="stSidebar"] [class*="page-nav"],
    [data-testid="stSidebar"] [class*="stPageLink"],
    [data-testid="stSidebar"] [class*="stPageLink-NavLink"],
    [data-testid="stSidebar"] a[href*="page="],
    [data-testid="stSidebar"] [class*="css-"]:has(a[href*="page="]) {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        overflow: hidden !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Remove todos os elementos filhos de navegação */
    [data-testid="stSidebar"] [data-testid="stNavigation"] *,
    [data-testid="stSidebar"] nav *,
    [data-testid="stSidebar"] [data-testid="stSidebarNav"] * {
        display: none !important;
    }
    
    /* Remove links de páginas na sidebar */
    [data-testid="stSidebar"] a[href*="page="],
    [data-testid="stSidebar"] button[data-testid*="page"] {
        display: none !important;
    }
    
    /* Garante que a navegação no topo seja visível */
    [data-testid="stHeader"] {
        z-index: 999;
    }
    
    /* Remove qualquer lista de páginas na sidebar */
    [data-testid="stSidebar"] ul:has(li a[href*="page="]),
    [data-testid="stSidebar"] ol:has(li a[href*="page="]) {
        display: none !important;
    }
</style>
<script>
    // Remove dinamicamente qualquer menu de navegação que apareça na sidebar
    function removeSidebarNavigation() {
        const sidebar = document.querySelector('[data-testid="stSidebar"]');
        if (sidebar) {
            // Remove elementos de navegação
            const navElements = sidebar.querySelectorAll(
                'nav, [data-testid="stNavigation"], [data-testid="stSidebarNav"], ' +
                '[class*="navigation"], [class*="Navigation"], [class*="page-nav"], ' +
                'a[href*="page="], [class*="stPageLink"]'
            );
            navElements.forEach(el => {
                el.style.display = 'none';
                el.remove();
            });
            
            // Remove listas que contenham links de páginas
            const lists = sidebar.querySelectorAll('ul, ol');
            lists.forEach(list => {
                const pageLinks = list.querySelectorAll('a[href*="page="]');
                if (pageLinks.length > 0) {
                    list.style.display = 'none';
                    list.remove();
                }
            });
        }
    }
    
    // Executa imediatamente e após o carregamento
    removeSidebarNavigation();
    window.addEventListener('load', removeSidebarNavigation);
    document.addEventListener('DOMContentLoaded', removeSidebarNavigation);
    
    // Observa mudanças no DOM e remove navegação se aparecer
    const observer = new MutationObserver(removeSidebarNavigation);
    if (document.body) {
        observer.observe(document.body, { childList: true, subtree: true });
    }
</script>
""", unsafe_allow_html=True)

def main():
    logger = get_logger()
    logger.info("Iniciando aplicação principal")
    
    # Verifica autenticação
    require_login()
    
    # Mostra informações do usuário
    show_user_info()
    
    # Verifica e mostra informações do trial
    try:
        from services.trial_manager import show_trial_notification
        show_trial_notification()
    except ImportError:
        pass  # Se não tiver o trial manager, continua normalmente
    
    # Cria filtros na sidebar
    filters = create_filter_sidebar()
    
    # Ajuda global do sistema (popover)
    top_l, top_r = st.columns([6, 1])
    with top_r:
        with st.popover("❓ Ajuda"):
            st.markdown(
                "**Como navegar e analisar**\n\n"
                "- Use o **menu superior** para acessar todas as páginas: Visão Geral, Acidentes, Quase-Acidentes, N/C, KPIs.\n"
                "- Use a **barra lateral** para aplicar filtros de período e datas quando necessário.\n"
                "- Em cada página, clique em '❓ Ajuda' para instruções específicas.\n\n"
                "**Dicas rápidas**\n\n"
                "- Se não aparecerem dados, ajuste os filtros de período na barra lateral.\n"
                "- Evidências: acesse a aba '📎 Evidências' em cada módulo.\n"
                "- Para registrar, use as abas '➕ Novo ...' das páginas.\n\n"
                "**📝 Feedback e Sugestões**\n\n"
                "- Encontrou um erro ou tem uma sugestão? Acesse **Conta → Feedbacks** no menu superior.\n"
                "- Lá você pode reportar bugs, sugerir melhorias ou compartilhar ideias.\n"
                "- Seu feedback é muito importante para melhorarmos o sistema!"
            )
    
    # Armazena filtros no session state para as páginas acessarem
    st.session_state.filters = filters
    
    # Define as páginas disponíveis com seções organizadas
    pages = {
        "📊 Análise": [
            st.Page("pages/1_Visao_Geral.py", title="Visão Geral", icon="📊"),
            st.Page("pages/2_Acidentes.py", title="Acidentes", icon="🚨"),
            st.Page("pages/3_Quase_Acidentes.py", title="Quase-Acidentes", icon="⚠️"),
            st.Page("pages/4_Nao_Conformidades.py", title="Não Conformidades", icon="📋"),
            st.Page("pages/investigation.py", title="Investigação Formal (FTA)", icon="🔍"),
        ],
        "📈 Controles": [
            st.Page("pages/5_KPIs_e_Controles.py", title="KPIs e Controles", icon="📈"),
        ],
        "👤 Conta": [
            st.Page("pages/8_Perfil_Usuario.py", title="Perfil do Usuário", icon="👤"),
            st.Page("pages/9_Feedbacks.py", title="Feedbacks", icon="📝"),
        ],
        "⚙️ Administração": [
            st.Page("pages/6_Admin_Dados_Basicos.py", title="Dados Básicos", icon="⚙️"),
            st.Page("pages/7_Logs_Sistema.py", title="Logs do Sistema", icon="📝"),
        ]
    }
    
    # Cria navegação no topo
    pg = st.navigation(pages, position="top", expanded=True)
    
    # Executa a página selecionada
    try:
        logger.info(f"Executando página: {pg}")
        
        # O st.navigation retorna um objeto StreamlitPage, então usamos .run()
        pg.run()
            
    except Exception as e:
        logger.error(f"Erro ao carregar página: {str(e)}")
        st.error(f"Erro ao carregar página: {str(e)}")
        st.info("Verifique se o arquivo da página existe e está configurado corretamente.")

if __name__ == "__main__":
    main()
