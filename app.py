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
    
    # Define as páginas disponíveis
    page_options = {
        "📊 Visão Geral": "pages/1_Visao_Geral.py",
        "🚨 Acidentes": "pages/2_Acidentes.py", 
        "⚠️ Quase-Acidentes": "pages/3_Quase_Acidentes.py",
        "📋 Não Conformidades": "pages/4_Nao_Conformidades.py",
        "📈 KPIs e Controles": "pages/5_KPIs_e_Controles.py",
        "⚙️ Dados Básicos": "pages/6_Admin_Dados_Basicos.py",
        "📝 Logs do Sistema": "pages/7_Logs_Sistema.py"
    }
    
    # Cria navegação por seleção
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        selected_page = st.selectbox(
            "Selecione uma página:",
            options=list(page_options.keys()),
            index=0,
            key="page_selector"
        )
    
    # Executa a página selecionada
    try:
        page_path = page_options[selected_page]
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
