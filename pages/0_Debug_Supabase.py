"""
Página de Debug para Conexão Supabase
"""
import streamlit as st
import os
import traceback
from datetime import datetime
from managers.supabase_config import get_supabase_client, get_service_role_client, test_connection
from utils.supabase_debug import get_debugger

def app(filters=None):
    st.title("🔧 Debug - Conexão Supabase")
    st.markdown("Esta página ajuda a diagnosticar problemas de conexão com o Supabase.")
    
    # Inicializa o debugger
    debugger = get_debugger()
    
    # Seção 1: Verificação de Configuração
    st.header("1. 📋 Verificação de Configuração")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Variáveis de Ambiente")
        env_url = os.environ.get("SUPABASE_URL")
        env_key = os.environ.get("SUPABASE_ANON_KEY")
        env_service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        
        st.write(f"**SUPABASE_URL:** {'✅ Definida' if env_url else '❌ Não definida'}")
        if env_url:
            st.code(env_url[:50] + "..." if len(env_url) > 50 else env_url)
        
        st.write(f"**SUPABASE_ANON_KEY:** {'✅ Definida' if env_key else '❌ Não definida'}")
        if env_key:
            st.code(env_key[:20] + "..." if len(env_key) > 20 else env_key)
            
        st.write(f"**SUPABASE_SERVICE_ROLE_KEY:** {'✅ Definida' if env_service_key else '❌ Não definida'}")
        if env_service_key:
            st.code(env_service_key[:20] + "..." if len(env_service_key) > 20 else env_service_key)
    
    with col2:
        st.subheader("Streamlit Secrets")
        try:
            secrets_url = st.secrets.get("supabase", {}).get("url")
            secrets_key = st.secrets.get("supabase", {}).get("anon_key")
            secrets_service_key = st.secrets.get("supabase", {}).get("service_role_key")
            
            st.write(f"**URL:** {'✅ Definida' if secrets_url else '❌ Não definida'}")
            if secrets_url:
                st.code(secrets_url[:50] + "..." if len(secrets_url) > 50 else secrets_url)
            
            st.write(f"**ANON_KEY:** {'✅ Definida' if secrets_key else '❌ Não definida'}")
            if secrets_key:
                st.code(secrets_key[:20] + "..." if len(secrets_key) > 20 else secrets_key)
                
            st.write(f"**SERVICE_ROLE_KEY:** {'✅ Definida' if secrets_service_key else '❌ Não definida'}")
            if secrets_service_key:
                st.code(secrets_service_key[:20] + "..." if len(secrets_service_key) > 20 else secrets_service_key)
                
        except Exception as e:
            st.error(f"Erro ao acessar secrets: {str(e)}")
    
    # Seção 2: Status Detalhado da Configuração
    st.header("2. 🔍 Status Detalhado")
    
    if st.button("🔄 Atualizar Status"):
        config_status = debugger.get_configuration_status()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Variáveis de Ambiente")
            for key, value in config_status["env_vars"].items():
                status_icon = "✅" if value else "❌"
                st.write(f"{status_icon} **{key}**")
        
        with col2:
            st.subheader("Streamlit Secrets")
            for key, value in config_status["secrets"].items():
                status_icon = "✅" if value else "❌"
                st.write(f"{status_icon} **{key}**")
        
        # Mostra valores (mascarados)
        st.subheader("Valores de Configuração")
        with st.expander("Ver valores (mascarados)"):
            for key, value in config_status["values"].items():
                if value:
                    masked_value = value[:10] + "..." + value[-5:] if len(value) > 15 else value
                    st.write(f"**{key}:** `{masked_value}`")
                else:
                    st.write(f"**{key}:** `Não definido`")
    
    # Seção 3: Teste de Conexão
    st.header("3. 🔌 Teste de Conexão")
    
    if st.button("🧪 Testar Conexão Anônima", type="primary"):
        with st.spinner("Testando conexão..."):
            try:
                client = get_supabase_client()
                if client:
                    st.success("✅ Cliente Supabase criado com sucesso!")
                    
                    # Teste de query simples
                    try:
                        response = client.table("profiles").select("id").limit(1).execute()
                        try:
                            if hasattr(response, 'data'):
                                data = getattr(response, 'data', [])
                                if data and len(data) > 0:
                                    st.success(f"✅ Query executada com sucesso! Retornou {len(data)} registros.")
                                    st.json(data[0])
                                else:
                                    st.info("ℹ️ Tabela 'profiles' está vazia ou não existe.")
                            else:
                                st.info("ℹ️ Resposta não contém dados esperados.")
                        except Exception:
                            st.info("ℹ️ Erro ao processar resposta da query.")
                            
                    except Exception as query_error:
                        st.error(f"❌ Erro na query: {str(query_error)}")
                        st.code(traceback.format_exc())
                        
                else:
                    st.error("❌ Falha ao criar cliente Supabase")
                    
            except Exception as e:
                st.error(f"❌ Erro geral: {str(e)}")
                st.code(traceback.format_exc())
    
    if st.button("🔐 Testar Conexão Service Role"):
        with st.spinner("Testando conexão service role..."):
            try:
                client = get_service_role_client()
                if client:
                    st.success("✅ Cliente Service Role criado com sucesso!")
                    
                    # Teste de query com service role
                    try:
                        response = client.table("profiles").select("id").limit(1).execute()
                        try:
                            if hasattr(response, 'data'):
                                data = getattr(response, 'data', [])
                                if data and len(data) > 0:
                                    st.success(f"✅ Query Service Role executada! Retornou {len(data)} registros.")
                                else:
                                    st.info("ℹ️ Query Service Role executada, mas sem dados retornados.")
                            else:
                                st.info("ℹ️ Resposta Service Role não contém dados esperados.")
                        except Exception:
                            st.info("ℹ️ Erro ao processar resposta Service Role.")
                        
                    except Exception as query_error:
                        st.error(f"❌ Erro na query Service Role: {str(query_error)}")
                        st.code(traceback.format_exc())
                        
                else:
                    st.error("❌ Falha ao criar cliente Service Role")
                    
            except Exception as e:
                st.error(f"❌ Erro Service Role: {str(e)}")
                st.code(traceback.format_exc())
    
    # Seção 4: Teste de Tabelas
    st.header("4. 📊 Teste de Tabelas")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        table_name = st.selectbox(
            "Selecione uma tabela para testar:",
            ["profiles", "acidentes", "quase_acidentes", "nao_conformidades", "kpis"],
            index=0
        )
        
        if st.button("🔍 Testar Acesso à Tabela"):
            with st.spinner(f"Testando acesso à tabela {table_name}..."):
                result = debugger.test_table_access(table_name)
                
                if result["table_exists"]:
                    st.success(f"✅ Tabela '{table_name}' existe")
                    
                    if result["can_read"]:
                        st.success("✅ Acesso de leitura OK")
                        if result["columns"]:
                            st.write(f"**Colunas:** {', '.join(result['columns'])}")
                    else:
                        st.error("❌ Erro no acesso de leitura")
                    
                    if result["can_write"]:
                        st.success("✅ Acesso de escrita OK")
                    else:
                        st.warning("⚠️ Acesso de escrita limitado")
                        
                    if result["error"]:
                        st.error(f"❌ Erro: {result['error']}")
                else:
                    st.error(f"❌ Tabela '{table_name}' não existe ou não acessível")
    
    with col2:
        st.subheader("Tabelas Conhecidas")
        st.markdown("""
        - **profiles**: Perfis de usuários
        - **acidentes**: Registros de acidentes
        - **quase_acidentes**: Registros de quase-acidentes
        - **nao_conformidades**: Registros de não conformidades
        - **kpis**: Dados de KPIs e controles
        """)
    
    # Seção 5: Teste de Autenticação
    st.header("5. 👤 Teste de Autenticação")
    
    if st.button("🔍 Testar Autenticação de Usuário"):
        with st.spinner("Testando autenticação..."):
            try:
                from auth.auth_utils import check_user_in_database, get_user_email
                
                user_email = get_user_email()
                if user_email:
                    st.info(f"Email do usuário: {user_email}")
                    
                    user_info = check_user_in_database(user_email)
                    if user_info:
                        st.success("✅ Usuário autenticado com sucesso!")
                        st.json(user_info)
                    else:
                        st.warning("⚠️ Usuário não encontrado na base de dados")
                else:
                    st.warning("⚠️ Nenhum usuário logado via OIDC")
                    
            except Exception as e:
                st.error(f"❌ Erro na autenticação: {str(e)}")
                st.code(traceback.format_exc())
    
    # Seção 6: Informações do Sistema
    st.header("6. ℹ️ Informações do Sistema")
    
    if st.button("🔄 Atualizar Informações do Sistema"):
        system_info = debugger.get_system_info()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Versões")
            st.write(f"**Python:** {system_info['python_version']}")
            st.write(f"**Streamlit:** {system_info['streamlit_version']}")
            st.write(f"**Supabase:** {system_info['supabase_version']}")
            st.write(f"**Plataforma:** {system_info['platform']}")
        
        with col2:
            st.subheader("Status da Sessão")
            st.write(f"**Usuário logado:** {'✅ Sim' if st.session_state.get('authenticated_user_email') else '❌ Não'}")
            st.write(f"**Role:** {st.session_state.get('role', 'N/A')}")
            st.write(f"**User ID:** {st.session_state.get('user_id', 'N/A')}")
            st.write(f"**Diretório:** {system_info['working_directory']}")
    
    # Seção 7: Logs de Debug
    st.header("7. 📝 Logs de Debug")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Mostra logs do debugger
        logs = debugger.get_logs(limit=20)
        if logs:
            st.subheader("Logs Recentes")
            for log in reversed(logs[-10:]):  # Últimos 10 logs
                st.text(log)
        else:
            st.info("Nenhum log disponível")
    
    with col2:
        if st.button("🔄 Atualizar Logs"):
            st.rerun()
        
        if st.button("🗑️ Limpar Logs"):
            debugger.clear_logs()
            st.rerun()
        
        if st.button("📋 Copiar Logs"):
            logs_text = "\n".join(debugger.get_logs())
            st.code(logs_text)
            st.info("Logs copiados para a área de transferência")
    
    # Seção 8: Comandos de Diagnóstico
    st.header("8. 🛠️ Comandos de Diagnóstico")
    
    st.markdown("""
    ### Para diagnosticar problemas:
    
    1. **Verifique se as variáveis de ambiente estão definidas:**
       ```bash
       echo $SUPABASE_URL
       echo $SUPABASE_ANON_KEY
       ```
    
    2. **Verifique o arquivo .streamlit/secrets.toml:**
       ```toml
       [supabase]
       url = "sua_url_aqui"
       anon_key = "sua_chave_aqui"
       ```
    
    3. **Teste a conexão diretamente no Python:**
       ```python
       from supabase import create_client
       client = create_client(url, key)
       result = client.table("profiles").select("*").execute()
       print(result)
       ```
    
    4. **Verifique se a tabela 'profiles' existe no Supabase:**
       - Acesse o painel do Supabase
       - Vá em Table Editor
       - Verifique se a tabela 'profiles' existe
    
    5. **Verifique as políticas RLS (Row Level Security):**
       - Acesse Authentication > Policies no Supabase
       - Verifique se as políticas estão configuradas corretamente
    """)
    
    # Seção de resumo
    st.header("9. 📋 Resumo do Debug")
    
    if st.button("🔍 Executar Diagnóstico Completo"):
        with st.spinner("Executando diagnóstico completo..."):
            # Testa configuração
            config_status = debugger.get_configuration_status()
            
            # Testa conexão anônima
            conn_result = debugger.test_connection(use_service_role=False)
            
            # Testa conexão service role
            service_result = debugger.test_connection(use_service_role=True)
            
            # Mostra resumo
            st.subheader("Resumo do Diagnóstico")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Configuração", "✅ OK" if any(config_status["env_vars"].values()) or any(config_status["secrets"].values()) else "❌ Falha")
            
            with col2:
                st.metric("Conexão Anônima", "✅ OK" if conn_result["success"] else "❌ Falha")
            
            with col3:
                st.metric("Service Role", "✅ OK" if service_result["success"] else "❌ Falha")
            
            # Recomendações
            st.subheader("Recomendações")
            if not conn_result["success"]:
                st.error("❌ Verifique as credenciais do Supabase")
            if not service_result["success"]:
                st.warning("⚠️ Service Role Key pode estar incorreta")
            if conn_result["success"] and service_result["success"]:
                st.success("🎉 Sistema funcionando corretamente!")
