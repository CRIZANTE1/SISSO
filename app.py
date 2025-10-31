import streamlit as st
from auth.auth_utils import require_login, show_user_info
from components.filters import create_filter_sidebar
from utils.simple_logger import get_logger

# Configuração da página
st.set_page_config(
    page_title="Sistema SSO - Monitoramento",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
                "- Use o menu superior para acessar: Visão Geral, Acidentes, Quase-Acidentes, N/C, KPIs.\n"
                "- Use a barra lateral para aplicar filtros (usuários, período, datas, causas).\n"
                "- Em cada página, clique em '❓ Ajuda' para instruções específicas.\n\n"
                "**Dicas rápidas**\n\n"
                "- Se não aparecerem dados, reduza filtros ou amplie o período.\n"
                "- Evidências: acesse a aba '📎 Evidências' em cada módulo.\n"
                "- Para registrar, use as abas '➕ Novo ...' das páginas.\n\n"
                "**📝 Feedback e Sugestões**\n\n"
                "- Encontrou um erro ou tem uma sugestão? Acesse **Conta → Feedbacks** no menu.\n"
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
