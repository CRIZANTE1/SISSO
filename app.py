import streamlit as st
from auth.auth_utils import require_login, show_user_info
from components.filters import create_filter_sidebar

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
    
    # Verifica autenticação
    require_login()
    
    # Mostra informações do usuário
    show_user_info()
    
    # Cria filtros na sidebar
    filters = create_filter_sidebar()
    
    # Define as páginas organizadas em seções
    pages = {
        "🔧 Debug": [
            st.Page("pages/0_Debug_Supabase.py", title="Debug Supabase", icon="🔧"),
        ],
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
        ]
    }
    
    # Cria navegação com posição superior
    page = st.navigation(pages, position="top", expanded=True)
    
    # Executa a página selecionada
    try:
        # Obtém o caminho do arquivo da página
        page_path = str(page)
        
        # Importa e executa a página
        import importlib.util
        spec = importlib.util.spec_from_file_location("page_module", page_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Não foi possível carregar o módulo {page_path}")
        page_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(page_module)
        
        # Executa a função app() da página passando os filtros
        if hasattr(page_module, 'app'):
            page_module.app(filters)
        else:
            st.error(f"Página {page_path} não possui função 'app'")
            
    except Exception as e:
        st.error(f"Erro ao carregar página: {str(e)}")
        st.info("Verifique se o arquivo da página existe e está configurado corretamente.")

if __name__ == "__main__":
    main()
