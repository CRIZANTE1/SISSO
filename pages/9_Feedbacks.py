"""
Página de Feedbacks - Erros e Sugestões
Permite que usuários registrem feedbacks sobre o sistema
"""
import streamlit as st
from datetime import datetime
from typing import Optional
from auth.auth_utils import require_login, is_admin, get_user_id, get_user_email
from services.feedbacks import (
    get_user_feedbacks, 
    get_all_feedbacks, 
    create_feedback, 
    update_feedback_status, 
    delete_feedback,
    get_feedback_statistics
)

def feedback_form() -> Optional[dict]:
    """Formulário para criar novo feedback"""
    with st.form("new_feedback_form"):
        st.markdown("### 📝 Novo Feedback")
        st.info("💡 Use esta área para reportar erros, sugerir melhorias ou compartilhar ideias sobre o sistema!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            feedback_type = st.selectbox(
                "Tipo de Feedback",
                options=["erro", "sugestao", "melhoria", "outro"],
                format_func=lambda x: {
                    "erro": "🐛 Erro/Bug",
                    "sugestao": "💡 Sugestão",
                    "melhoria": "✨ Melhoria",
                    "outro": "📄 Outro"
                }[x],
                help="Selecione o tipo de feedback"
            )
        
        with col2:
            priority = st.selectbox(
                "Prioridade",
                options=["baixa", "media", "alta"],
                format_func=lambda x: {
                    "baixa": "🟢 Baixa",
                    "media": "🟡 Média",
                    "alta": "🔴 Alta"
                }[x],
                help="Nível de prioridade do feedback"
            )
        
        title = st.text_input(
            "Título do Feedback",
            placeholder="Ex: Erro ao salvar acidente",
            help="Um título descritivo para seu feedback"
        )
        
        description = st.text_area(
            "Descrição Detalhada",
            placeholder="Descreva o erro encontrado, sua sugestão ou melhoria em detalhes...",
            height=200,
            help="Forneça o máximo de detalhes possível para nos ajudar a entender melhor"
        )
        
        submitted = st.form_submit_button("📤 Enviar Feedback", type="primary")
        
        if submitted:
            if not title.strip():
                st.error("⚠️ O título é obrigatório!")
                return None
            
            if not description.strip():
                st.error("⚠️ A descrição é obrigatória!")
                return None
            
            if len(description.strip()) < 20:
                st.error("⚠️ Por favor, forneça uma descrição mais detalhada (mínimo 20 caracteres)")
                return None
            
            feedback_data = {
                "type": feedback_type,
                "title": title.strip(),
                "description": description.strip(),
                "priority": priority,
                "status": "aberto"
            }
            
            return feedback_data
    
    return None

def display_feedback_card(feedback: dict, is_admin_view: bool = False):
    """Exibe um card de feedback"""
    type_icons = {
        "erro": "🐛",
        "sugestao": "💡",
        "melhoria": "✨",
        "outro": "📄"
    }
    
    priority_colors = {
        "baixa": "🟢",
        "media": "🟡",
        "alta": "🔴"
    }
    
    status_labels = {
        "aberto": "🔵 Aberto",
        "em_analise": "🟠 Em Análise",
        "resolvido": "✅ Resolvido",
        "rejeitado": "❌ Rejeitado"
    }
    
    type_icon = type_icons.get(feedback.get("type", "outro"), "📄")
    priority_color = priority_colors.get(feedback.get("priority", "media"), "🟡")
    status_label = status_labels.get(feedback.get("status", "aberto"), "🔵 Aberto")
    
    with st.expander(f"{type_icon} **{feedback.get('title', 'Sem título')}** - {status_label} {priority_color}"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**📅 Criado em:** {feedback.get('created_at', 'N/A')}")
            if feedback.get('updated_at') and feedback.get('updated_at') != feedback.get('created_at'):
                st.markdown(f"**🔄 Atualizado em:** {feedback.get('updated_at', 'N/A')}")
            if feedback.get('resolved_at'):
                st.markdown(f"**✅ Resolvido em:** {feedback.get('resolved_at', 'N/A')}")
            
            st.markdown("---")
            st.markdown(f"**📝 Descrição:**")
            st.markdown(feedback.get('description', 'Sem descrição'))
        
        with col2:
            st.markdown(f"**Tipo:** {feedback.get('type', '-').title()}")
            st.markdown(f"**Prioridade:** {feedback.get('priority', '-').title()}")
            st.markdown(f"**Status:** {status_label}")
            
            # Ações para o usuário (se for seu feedback e estiver aberto)
            if not is_admin_view and feedback.get('status') == 'aberto':
                if st.button("🗑️ Remover", key=f"delete_{feedback.get('id')}"):
                    if delete_feedback(feedback.get('id')):
                        st.rerun()
            
            # Ações para admin
            if is_admin_view and feedback.get('status') != 'resolvido':
                st.markdown("---")
                st.markdown("**👤 Ações Admin:**")
                
                new_status = st.selectbox(
                    "Alterar Status",
                    options=["aberto", "em_analise", "resolvido", "rejeitado"],
                    index=["aberto", "em_analise", "resolvido", "rejeitado"].index(feedback.get("status", "aberto")),
                    key=f"status_{feedback.get('id')}"
                )
                
                admin_notes = st.text_area(
                    "Notas Admin (opcional)",
                    value=feedback.get('admin_notes', ''),
                    height=100,
                    key=f"notes_{feedback.get('id')}"
                )
                
                if new_status != feedback.get("status") or admin_notes != feedback.get('admin_notes', ''):
                    if st.button("💾 Salvar Alterações", key=f"update_{feedback.get('id')}"):
                        if update_feedback_status(feedback.get('id'), new_status, admin_notes if admin_notes else None):
                            st.success("✅ Feedback atualizado!")
                            st.rerun()
                
                if st.button("🗑️ Remover", key=f"delete_{feedback.get('id')}"):
                    if delete_feedback(feedback.get('id')):
                        st.rerun()

def app(filters=None):
    """Página principal de Feedbacks"""
    require_login()
    
    st.title("📝 Feedbacks - Erros e Sugestões")
    
    user_id = get_user_id()
    user_email = get_user_email()
    
    if not user_id:
        st.error("❌ Usuário não autenticado. Faça login novamente.")
        st.stop()
    
    # Tabs para diferentes visualizações
    if is_admin():
        tab1, tab2, tab3 = st.tabs(["📤 Novo Feedback", "📋 Meus Feedbacks", "👥 Todos os Feedbacks (Admin)"])
    else:
        tab1, tab2 = st.tabs(["📤 Novo Feedback", "📋 Meus Feedbacks"])
    
    # TAB 1: Novo Feedback
    with tab1:
        st.subheader("📤 Enviar Novo Feedback")
        
        # Instruções de cadastro
        with st.expander("📖 Como Enviar um Feedback", expanded=True):
            st.markdown("""
            **Siga estes passos para enviar seu feedback:**
            
            1. **Tipo de Feedback**: Selecione a categoria do seu feedback:
               - **🐛 Erro/Bug**: Para reportar problemas técnicos, bugs ou falhas do sistema
               - **💡 Sugestão**: Para propor novas funcionalidades ou ideias
               - **✨ Melhoria**: Para sugerir aprimoramentos em funcionalidades existentes
               - **📄 Outro**: Para qualquer outro tipo de comentário ou feedback
            
            2. **Prioridade**: Informe o nível de urgência:
               - **🔴 Alta**: Problema crítico que impede o uso ou sugestão muito importante
               - **🟡 Média**: Problema ou sugestão importante, mas não urgente
               - **🟢 Baixa**: Problema menor ou sugestão para consideração futura
            
            3. **Título**: Crie um título descritivo e claro
               - **Para erros**: "Erro ao salvar acidente" ou "Sistema não carrega página X"
               - **Para sugestões**: "Sugestão: adicionar filtro por período" ou "Ideia: exportar relatório em PDF"
            
            4. **Descrição Detalhada**: Seja o mais específico possível:
               - **Se for um erro**: Descreva o que aconteceu, quando ocorreu, o que você estava fazendo, e o que esperava que acontecesse
               - **Se for sugestão/melhoria**: Explique a ideia detalhadamente, como funcionaria, qual o benefício e por que seria útil
            
            **💡 Dicas para um bom feedback**: 
            - Quanto mais detalhes, melhor conseguiremos entender e resolver
            - Se for um erro, inclua passos para reproduzir o problema
            - Se for uma sugestão, explique o contexto de uso
            - Seus feedbacks são confidenciais e ajudam a melhorar o sistema para todos
            
            **📋 Campos Obrigatórios**: Tipo, Título (mínimo necessário) e Descrição (mínimo 20 caracteres)
            """)
        
        st.info("💡 **Sua opinião é muito importante!** Use este formulário para reportar erros, sugerir melhorias ou compartilhar ideias sobre o sistema.")
        
        new_feedback = feedback_form()
        
        if new_feedback:
            if create_feedback(new_feedback):
                st.rerun()
    
    # TAB 2: Meus Feedbacks
    with tab2:
        st.subheader("📋 Meus Feedbacks")
        st.info("📌 Você pode ver apenas seus próprios feedbacks. Apenas administradores podem ver todos os feedbacks.")
        
        with st.spinner("Carregando seus feedbacks..."):
            feedbacks = get_user_feedbacks()
        
        if feedbacks:
            st.info(f"📊 Você tem {len(feedbacks)} feedback(s) registrado(s)")
            
            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                filter_type = st.selectbox(
                    "Filtrar por Tipo",
                    options=["Todos"] + ["erro", "sugestao", "melhoria", "outro"],
                    format_func=lambda x: {
                        "Todos": "Todos",
                        "erro": "🐛 Erro/Bug",
                        "sugestao": "💡 Sugestão",
                        "melhoria": "✨ Melhoria",
                        "outro": "📄 Outro"
                    }.get(x, x)
                )
            
            with col2:
                filter_status = st.selectbox(
                    "Filtrar por Status",
                    options=["Todos"] + ["aberto", "em_analise", "resolvido", "rejeitado"],
                    format_func=lambda x: {
                        "Todos": "Todos",
                        "aberto": "🔵 Aberto",
                        "em_analise": "🟠 Em Análise",
                        "resolvido": "✅ Resolvido",
                        "rejeitado": "❌ Rejeitado"
                    }.get(x, x)
                )
            
            # Aplica filtros
            filtered_feedbacks = feedbacks
            if filter_type != "Todos":
                filtered_feedbacks = [f for f in filtered_feedbacks if f.get('type') == filter_type]
            if filter_status != "Todos":
                filtered_feedbacks = [f for f in filtered_feedbacks if f.get('status') == filter_status]
            
            if filtered_feedbacks:
                st.markdown("---")
                for feedback in filtered_feedbacks:
                    display_feedback_card(feedback, is_admin_view=False)
                    st.markdown("---")
            else:
                st.info("Nenhum feedback encontrado com os filtros aplicados.")
        else:
            st.info("📭 Você ainda não enviou nenhum feedback. Use a aba 'Novo Feedback' para começar!")
    
    # TAB 3: Todos os Feedbacks (Admin)
    if is_admin():
        with tab3:
            st.subheader("👥 Todos os Feedbacks do Sistema")
            st.warning("🔐 **Área Administrativa** - Como administrador, você pode ver, avaliar e gerenciar todos os feedbacks dos usuários")
            
            # Estatísticas
            with st.spinner("Carregando estatísticas..."):
                stats = get_feedback_statistics()
            
            if stats:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total de Feedbacks", stats.get("total", 0))
                with col2:
                    st.metric("Abertos", stats.get("por_status", {}).get("aberto", 0))
                with col3:
                    st.metric("Em Análise", stats.get("por_status", {}).get("em_analise", 0))
                with col4:
                    st.metric("Resolvidos", stats.get("por_status", {}).get("resolvido", 0))
            
            # Filtros para admin
            col1, col2, col3 = st.columns(3)
            with col1:
                include_resolved = st.checkbox("Incluir Resolvidos", value=False)
            with col2:
                admin_filter_type = st.selectbox(
                    "Filtrar por Tipo",
                    options=["Todos"] + ["erro", "sugestao", "melhoria", "outro"],
                    format_func=lambda x: {
                        "Todos": "Todos",
                        "erro": "🐛 Erro/Bug",
                        "sugestao": "💡 Sugestão",
                        "melhoria": "✨ Melhoria",
                        "outro": "📄 Outro"
                    }.get(x, x),
                    key="admin_filter_type"
                )
            with col3:
                admin_filter_status = st.selectbox(
                    "Filtrar por Status",
                    options=["Todos"] + ["aberto", "em_analise", "resolvido", "rejeitado"],
                    format_func=lambda x: {
                        "Todos": "Todos",
                        "aberto": "🔵 Aberto",
                        "em_analise": "🟠 Em Análise",
                        "resolvido": "✅ Resolvido",
                        "rejeitado": "❌ Rejeitado"
                    }.get(x, x),
                    key="admin_filter_status"
                )
            
            # Busca todos os feedbacks
            with st.spinner("Carregando feedbacks..."):
                all_feedbacks = get_all_feedbacks(include_resolved=include_resolved)
            
            if all_feedbacks:
                # Aplica filtros
                filtered_all = all_feedbacks
                if admin_filter_type != "Todos":
                    filtered_all = [f for f in filtered_all if f.get('type') == admin_filter_type]
                if admin_filter_status != "Todos":
                    filtered_all = [f for f in filtered_all if f.get('status') == admin_filter_status]
                
                if filtered_all:
                    st.info(f"📊 Exibindo {len(filtered_all)} de {len(all_feedbacks)} feedback(s)")
                    st.markdown("---")
                    
                    for feedback in filtered_all:
                        # Mostra informações do usuário que criou o feedback
                        try:
                            from managers.supabase_config import get_service_role_client
                            supabase_admin = get_service_role_client()
                            user_info = supabase_admin.table("profiles")\
                                .select("email, full_name")\
                                .eq("id", feedback.get('user_id'))\
                                .execute()
                            
                            if user_info.data:
                                user_data = user_info.data[0]
                                st.caption(f"👤 Usuário: {user_data.get('full_name', user_data.get('email', 'N/A'))} ({user_data.get('email', 'N/A')})")
                        except:
                            pass
                        
                        display_feedback_card(feedback, is_admin_view=True)
                        st.markdown("---")
                else:
                    st.info("Nenhum feedback encontrado com os filtros aplicados.")
            else:
                st.info("📭 Nenhum feedback registrado no sistema ainda.")

if __name__ == "__main__":
    app({})

