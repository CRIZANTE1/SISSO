"""
Página de Logs do Sistema
"""
import streamlit as st
from utils.simple_logger import get_logger
from managers.supabase_config import test_connection
import json

def app(filters=None):
    # Verifica autenticação e trial
    from auth.auth_utils import require_login
    require_login()
    
    # Busca filtros do session state se não foram passados como parâmetro
    if filters is None:
        filters = st.session_state.get('filters', {})
    # Verifica se usuário tem permissão de admin
    from auth.auth_utils import check_permission
    check_permission('admin')
    
    st.title("📝 Logs do Sistema")
    st.markdown("Visualize e gerencie os logs do sistema de monitoramento SSO.")
    # Ajuda da página (popover)
    ll, lr = st.columns([6, 1])
    with lr:
        with st.popover("❓ Ajuda", key="logs_help_popover"):
            st.markdown(
                "**Como usar**\n\n"
                "- 'Logs Recentes': filtrar níveis e atualizar.\n"
                "- 'Filtros de Log': entender níveis e uso.\n"
                "- 'Status do Sistema': testar conexão e ver sessão.\n"
                "- 'Informações Técnicas': baixar/exportar e estatísticas."
            )
    
    # Inicializa logger
    logger = get_logger()
    
    # Tabs para diferentes funcionalidades
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Logs Recentes",
        "🔍 Filtros de Log",
        "🔧 Status do Sistema", 
        "📋 Informações Técnicas"
    ])
    
    with tab1:
        st.subheader("Logs Recentes")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            limit = st.slider("Número de logs", 10, 100, 50)
        
        with col2:
            if st.button("🔄 Atualizar", type="primary"):
                st.rerun()
        
        with col3:
            if st.button("🗑️ Limpar Logs"):
                logger.clear_memory_logs()
                st.success("Logs limpos com sucesso!")
                st.rerun()
        
        # Mostra logs
        logs = logger.get_memory_logs(limit)
        
        if logs:
            st.subheader(f"Últimos {len(logs)} logs")
            
            # Filtro por nível
            levels = st.multiselect(
                "Filtrar por nível:",
                ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                default=["INFO", "WARNING", "ERROR", "CRITICAL"]
            )
            
            filtered_logs = [log for log in logs if log["level"] in levels]
            
            if filtered_logs:
                for log in reversed(filtered_logs[-20:]):  # Mostra últimos 20
                    level_color = {
                        "DEBUG": "🔍",
                        "INFO": "ℹ️",
                        "WARNING": "⚠️",
                        "ERROR": "❌",
                        "CRITICAL": "🚨"
                    }.get(log["level"], "📝")
                    
                    with st.expander(f"{level_color} {log['timestamp']} - {log['level']}"):
                        st.write(f"**Mensagem:** {log['message']}")
                        if log['extra_data']:
                            st.write("**Dados adicionais:**")
                            st.json(log['extra_data'])
            else:
                st.info("Nenhum log encontrado com os filtros selecionados.")
        else:
            st.info("Nenhum log disponível no momento.")
    
    with tab2:
        st.subheader("Filtros de Log")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Níveis de Log Disponíveis:**")
            st.write("- 🔍 **DEBUG**: Informações detalhadas para debug")
            st.write("- ℹ️ **INFO**: Informações gerais do sistema")
            st.write("- ⚠️ **WARNING**: Avisos que não impedem funcionamento")
            st.write("- ❌ **ERROR**: Erros que afetam funcionalidades")
            st.write("- 🚨 **CRITICAL**: Erros críticos que impedem funcionamento")
        
        with col2:
            st.write("**Como usar os filtros:**")
            st.write("1. Selecione os níveis desejados")
            st.write("2. Ajuste o número de logs")
            st.write("3. Clique em 'Atualizar' para ver os resultados")
            st.write("4. Use 'Limpar Logs' para remover logs antigos")
    
    with tab3:
        st.subheader("Status do Sistema")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Teste de Conexão**")
            if st.button("🧪 Testar Conexão Supabase"):
                with st.spinner("Testando conexão..."):
                    if test_connection():
                        st.success("✅ Conexão com Supabase OK")
                        logger.info("Teste de conexão manual executado com sucesso")
                    else:
                        st.error("❌ Falha na conexão com Supabase")
                        logger.error("Teste de conexão manual falhou")
        
        with col2:
            st.write("**Informações da Sessão**")
            session_info = {
                "Usuário autenticado": bool(st.session_state.get('authenticated_user_email')),
                "Email": st.session_state.get('authenticated_user_email', 'N/A'),
                "Role": st.session_state.get('role', 'N/A'),
                "User ID": st.session_state.get('user_id', 'N/A')
            }
            
            for key, value in session_info.items():
                st.write(f"**{key}:** {value}")
        
        # Status do sistema
        st.subheader("Status Detalhado")
        system_info = logger.get_system_info()
        
        with st.expander("Ver informações do sistema"):
            st.json(system_info)
    
    with tab4:
        st.subheader("Informações Técnicas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Configuração de Logs**")
            st.write("- Logs são salvos em arquivos diários")
            st.write("- Pasta: `logs/sso_system_YYYYMMDD.log`")
            st.write("- Logs em memória limitados a 1000 entradas")
            st.write("- Níveis: DEBUG, INFO, WARNING, ERROR, CRITICAL")
        
        with col2:
            st.write("**Monitoramento**")
            st.write("- Logs de autenticação")
            st.write("- Logs de conexão Supabase")
            st.write("- Logs de criação de perfis")
            st.write("- Logs de erros e exceções")
        
        # Exportar logs
        st.subheader("Exportar Logs")
        
        if st.button("📥 Baixar Logs (JSON)"):
            logs_data = logger.get_memory_logs()
            logs_json = json.dumps(logs_data, indent=2, ensure_ascii=False)
            
            st.download_button(
                label="💾 Download Logs",
                data=logs_json,
                file_name=f"sso_logs_{st.session_state.get('authenticated_user_email', 'unknown')}.json",
                mime="application/json"
            )
        
        # Estatísticas de logs
        st.subheader("Estatísticas")
        logs = logger.get_memory_logs()
        
        if logs:
            level_counts = {}
            for log in logs:
                level = log["level"]
                level_counts[level] = level_counts.get(level, 0) + 1
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("DEBUG", level_counts.get("DEBUG", 0))
            with col2:
                st.metric("INFO", level_counts.get("INFO", 0))
            with col3:
                st.metric("WARNING", level_counts.get("WARNING", 0))
            with col4:
                st.metric("ERROR", level_counts.get("ERROR", 0))
            with col5:
                st.metric("CRITICAL", level_counts.get("CRITICAL", 0))
        else:
            st.info("Nenhum log disponível para estatísticas.")

if __name__ == "__main__":
    app({})
