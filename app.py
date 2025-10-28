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
    # Header principal
    st.title("🛡️ Sistema de Monitoramento SSO")
    st.markdown("Segurança e Saúde Ocupacional - Análise de Acidentes e KPIs")
    
    logger = get_logger()
    logger.info("Iniciando aplicação principal")
    
    # Verifica autenticação
    require_login()
    
    # Mostra informações do usuário
    show_user_info()
    
    # Cria filtros na sidebar
    filters = create_filter_sidebar()
    
    # Define as páginas organizadas em seções
    pages = {
        "📊 Análises": [
            st.Page("pages/1_Visao_Geral.py", title="Visão Geral", icon="📊"),
            st.Page("pages/2_Acidentes.py", title="Acidentes", icon="🚨"),
            st.Page("pages/3_Quase_Acidentes.py", title="Quase-Acidentes", icon="⚠️"),
            st.Page("pages/4_Nao_Conformidades.py", title="Não Conformidades", icon="📋"),
        ],
        "📈 Controles": [
            st.Page("pages/5_KPIs_e_Controles.py", title="KPIs e Controles", icon="📈"),
        ],
        "⚙️ Administração": [
            st.Page("pages/6_Admin_Dados_Basicos.py", title="Dados Básicos", icon="⚙️"),
            st.Page("pages/7_Logs_Sistema.py", title="Logs do Sistema", icon="📝"),
        ]
    }
    
    # Cria navegação com posição superior
    page = st.navigation(pages, position="top", expanded=True)
    
    # Executa a página selecionada
    try:
        # Obtém o caminho do arquivo da página
        page_path = str(page)
        logger.info(f"Carregando página: {page_path}")
        
        # Importa e executa a página
        import importlib.util
        spec = importlib.util.spec_from_file_location("page_module", page_path)
        if spec is None or spec.loader is None:
            error_msg = f"Não foi possível carregar o módulo {page_path}"
            logger.error(error_msg)
            raise ImportError(error_msg)
        page_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(page_module)
        
        # Executa a função app() da página passando os filtros
        if hasattr(page_module, 'app'):
            logger.info(f"Executando página: {page_path}")
            page_module.app(filters)
        else:
            error_msg = f"Página {page_path} não possui função 'app'"
            logger.error(error_msg)
            st.error(error_msg)
            
    except Exception as e:
        logger.error(f"Erro ao carregar página: {str(e)}")
        st.error(f"Erro ao carregar página: {str(e)}")
        st.info("Verifique se o arquivo da página existe e está configurado corretamente.")

if __name__ == "__main__":
    main()
