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

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f77b4 0%, #17a2b8 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #1f77b4;
    }
    
    .alert-box {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>🛡️ Sistema de Monitoramento SSO</h1>
        <p>Segurança e Saúde Ocupacional - Análise de Acidentes e KPIs</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Verifica autenticação
    require_login()
    
    # Mostra informações do usuário
    show_user_info()
    
    # Cria filtros na sidebar
    filters = create_filter_sidebar()
    
    # Menu de navegação
    st.markdown("---")
    
    # Páginas disponíveis
    pages = {
        "📊 Visão Geral": "pages/1_Visao_Geral.py",
        "🚨 Acidentes": "pages/2_Acidentes.py", 
        "⚠️ Quase-Acidentes": "pages/3_Quase_Acidentes.py",
        "📋 Não Conformidades": "pages/4_Nao_Conformidades.py",
        "📈 KPIs e Controles": "pages/5_KPIs_e_Controles.py",
        "⚙️ Admin - Dados Básicos": "pages/6_Admin_Dados_Basicos.py"
    }
    
    # Seleção de página
    selected_page = st.selectbox(
        "Navegação",
        options=list(pages.keys()),
        key="page_selector"
    )
    
    # Carrega página selecionada
    page_file = pages[selected_page]
    
    try:
        # Importa e executa a página
        import importlib.util
        spec = importlib.util.spec_from_file_location("page_module", page_file)
        if spec is None or spec.loader is None:
            raise ImportError(f"Não foi possível carregar o módulo {page_file}")
        page_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(page_module)
        
        # Executa a função app() da página
        if hasattr(page_module, 'app'):
            page_module.app(filters)
        else:
            st.error(f"Página {page_file} não possui função 'app'")
            
    except Exception as e:
        st.error(f"Erro ao carregar página {selected_page}: {str(e)}")
        st.info("Verifique se o arquivo da página existe e está configurado corretamente.")

if __name__ == "__main__":
    main()
