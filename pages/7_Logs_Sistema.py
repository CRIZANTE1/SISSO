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
        with st.popover("❓ Ajuda"):
            st.markdown(
                "**Guia rápido**\n\n"
                "- Logs Recentes: filtre níveis e atualize.\n"
                "- Status do Sistema: teste conexão e veja sessão.\n\n"
                "**Dicas**\n\n"
                "- Baixe logs em JSON para auditoria.\n\n"
                "**📝 Feedback**\n"
                "- Encontrou um erro ou tem uma sugestão? Acesse **Conta → Feedbacks** para reportar!"
            )
    
    # Inicializa logger
    logger = get_logger()
    
    # Tabs para diferentes funcionalidades
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Logs Recentes",
        "👥 Logs de Ações",
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
        st.subheader("Logs de Ações dos Usuários")
        st.info("📋 Esta seção exibe logs temporários de ações realizadas pelos usuários no sistema")
        
        from services.user_logs import get_all_logs, cleanup_expired_logs, get_log_statistics
        from datetime import datetime, timedelta
        import pandas as pd
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            days_back = st.selectbox("Últimos dias", [7, 15, 30, 60, 90], index=2)
        
        with col2:
            action_filter = st.selectbox(
                "Tipo de ação",
                ["Todos", "create", "update", "delete", "view", "export", "import", "other"],
                index=0
            )
        
        with col3:
            entity_filter = st.selectbox(
                "Tipo de entidade",
                ["Todos", "accident", "near_miss", "nonconformity", "action", "feedback", "profile"],
                index=0
            )
        
        with col4:
            limit = st.selectbox("Limite", [50, 100, 200, 500], index=1)
        
        # Botões de ação
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🔄 Atualizar", type="primary"):
                st.rerun()
        
        with col_btn2:
            if st.button("🧹 Limpar Logs Expirados"):
                with st.spinner("Limpando logs expirados..."):
                    deleted = cleanup_expired_logs()
                    if deleted > 0:
                        st.success(f"✅ {deleted} logs expirados foram removidos!")
                        st.rerun()
                    else:
                        st.info("Nenhum log expirado encontrado.")
        
        # Busca logs
        start_date = datetime.now() - timedelta(days=days_back)
        end_date = datetime.now()
        
        action_type = None if action_filter == "Todos" else action_filter
        entity_type = None if entity_filter == "Todos" else entity_filter
        
        with st.spinner("Carregando logs de ações..."):
            logs = get_all_logs(
                start_date=start_date,
                end_date=end_date,
                action_type=action_type,
                entity_type=entity_type,
                limit=limit
            )
        
        if logs:
            st.success(f"✅ {len(logs)} logs encontrados")
            
            # Estatísticas
            st.subheader("📊 Estatísticas")
            stats = get_log_statistics()
            
            if stats:
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                
                with col_stat1:
                    st.metric("Total de Logs", stats.get("total", 0))
                
                with col_stat2:
                    if stats.get("por_action_type"):
                        most_common_action = max(stats["por_action_type"].items(), key=lambda x: x[1])
                        st.metric("Ação Mais Comum", f"{most_common_action[0]} ({most_common_action[1]})")
                
                with col_stat3:
                    if stats.get("por_entity_type"):
                        most_common_entity = max(stats["por_entity_type"].items(), key=lambda x: x[1])
                        st.metric("Entidade Mais Comum", f"{most_common_entity[0]} ({most_common_entity[1]})")
            
            # Tabela de logs
            st.subheader("📋 Lista de Logs")
            
            # Prepara dados para exibição
            logs_data = []
            for log in logs:
                logs_data.append({
                    "Data/Hora": pd.to_datetime(log.get("created_at", "")).strftime("%d/%m/%Y %H:%M:%S") if log.get("created_at") else "N/A",
                    "Ação": log.get("action_type", "N/A"),
                    "Entidade": log.get("entity_type", "N/A"),
                    "Descrição": log.get("description", "")[:100] + "..." if len(log.get("description", "")) > 100 else log.get("description", "N/A"),
                    "Usuário": log.get("user_id", "N/A")[:8] + "..." if log.get("user_id") else "N/A",
                    "ID Entidade": log.get("entity_id", "N/A")[:8] + "..." if log.get("entity_id") else "N/A"
                })
            
            if logs_data:
                df_logs = pd.DataFrame(logs_data)
                st.dataframe(df_logs, use_container_width=True, hide_index=True)
            
            # Detalhes de cada log
            st.subheader("🔍 Detalhes dos Logs")
            
            for log in logs[:20]:  # Mostra apenas os últimos 20 para performance
                action_icon = {
                    "create": "➕",
                    "update": "✏️",
                    "delete": "🗑️",
                    "view": "👁️",
                    "export": "📥",
                    "import": "📤",
                    "login": "🔐",
                    "logout": "🚪",
                    "other": "📝"
                }.get(log.get("action_type", "other"), "📝")
                
                with st.expander(
                    f"{action_icon} {log.get('action_type', 'N/A').upper()} - {log.get('entity_type', 'N/A')} - "
                    f"{pd.to_datetime(log.get('created_at', '')).strftime('%d/%m/%Y %H:%M') if log.get('created_at') else 'N/A'}"
                ):
                    col_detail1, col_detail2 = st.columns(2)
                    
                    with col_detail1:
                        st.markdown(f"**Data/Hora:** {pd.to_datetime(log.get('created_at', '')).strftime('%d/%m/%Y %H:%M:%S') if log.get('created_at') else 'N/A'}")
                        st.markdown(f"**Tipo de Ação:** {log.get('action_type', 'N/A')}")
                        st.markdown(f"**Tipo de Entidade:** {log.get('entity_type', 'N/A')}")
                        st.markdown(f"**ID da Entidade:** {log.get('entity_id', 'N/A')}")
                        st.markdown(f"**Usuário (ID):** {log.get('user_id', 'N/A')}")
                    
                    with col_detail2:
                        if log.get("ip_address"):
                            st.markdown(f"**IP Address:** {log.get('ip_address')}")
                        if log.get("user_agent"):
                            st.markdown(f"**User Agent:** {log.get('user_agent')[:100]}...")
                        if log.get("expires_at"):
                            expires = pd.to_datetime(log.get("expires_at", ""))
                            if expires < datetime.now():
                                st.warning(f"**Expira em:** {expires.strftime('%d/%m/%Y %H:%M')} (EXPIRADO)")
                            else:
                                st.info(f"**Expira em:** {expires.strftime('%d/%m/%Y %H:%M')}")
                    
                    st.markdown(f"**Descrição:** {log.get('description', 'N/A')}")
                    
                    if log.get("metadata"):
                        st.markdown("**Metadata:**")
                        st.json(log.get("metadata"))
        else:
            st.info("📭 Nenhum log de ação encontrado com os filtros selecionados.")
    
    with tab3:
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
