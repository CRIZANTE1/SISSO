import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from services.kpi import fetch_kpi_data
from services.uploads import upload_evidence, get_attachments
from components.cards import create_metric_row, create_bar_chart, create_pie_chart
from components.filters import apply_filters_to_df
from managers.supabase_config import get_supabase_client
from services.employees import get_all_employees
# Imports da NBR 14280 removidos

def calculate_work_days_until_accident(accident_date, employee_identifier=None, employee_id=None):
    """
    Calcula quantos dias o funcionário trabalhou até o acidente acontecer.
    Prioriza dados do acidentado (employees): admission_date e horas por employee_id.
    Aceita também identificador de usuário (e-mail ou UUID) como fallback.
    """
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()

        admission_date = None
        user_email = None
        user_profile_id = None

        # 1) Prioriza employees.employee_id
        if employee_id:
            try:
                emp_resp = supabase.table("employees").select("id, email, admission_date, user_id").eq("id", employee_id).limit(1).execute()
                if emp_resp and hasattr(emp_resp, 'data') and emp_resp.data:
                    emp = emp_resp.data[0]
                    if emp.get('admission_date'):
                        admission_date = pd.to_datetime(emp['admission_date']).date()
                    # Mapeamentos auxiliares
                    user_email = emp.get('email') or user_email
                    user_profile_id = emp.get('user_id') or user_profile_id
            except Exception:
                pass

        # 2) Resolve identificador do funcionário para fallback (profiles)
        if not user_email and not user_profile_id and employee_identifier:
            if isinstance(employee_identifier, str) and '@' in employee_identifier:
                user_email = employee_identifier
            else:
                user_profile_id = employee_identifier

        # 3) Busca perfil (apenas se ainda não temos admission_date do employees)
        if admission_date is None and (user_email or user_profile_id):
            if user_email:
                profile_response = supabase.table("profiles").select("id, email, created_at").eq("email", user_email).limit(1).execute()
            else:
                profile_response = supabase.table("profiles").select("id, email, created_at").eq("id", user_profile_id).limit(1).execute()

            if profile_response and hasattr(profile_response, 'data') and profile_response.data:
                profile = profile_response.data[0]
                # created_at como proxy de admissão
                if profile.get('created_at'):
                    admission_date = pd.to_datetime(profile['created_at']).date()
                # Garantir email/id para busca de horas
                user_profile_id = profile.get('id', user_profile_id)
                user_email = profile.get('email', user_email)

        # 4) Calcula dias corridos entre admissão e acidente (se conhecido)
        days_since_admission = None
        if admission_date is not None:
            days_since_admission = (accident_date - admission_date).days
            if days_since_admission < 0:
                days_since_admission = 0

        # 5) Busca horas trabalhadas mensais (alinhado com estrutura real)
        total_hours = 0.0
        hours_response = None
        # employee_id e site_id removidos da tabela hours_worked_monthly
        # Busca apenas por created_by (UUID do usuário)
        if user_profile_id:
            try:
                from auth.auth_utils import get_user_id
                # Usa UUID do usuário para buscar horas
                hours_response = supabase.table("hours_worked_monthly").select("year, month, hours, created_by").eq("created_by", user_profile_id).execute()
            except Exception:
                hours_response = None
        elif user_email:
            # Se não tiver UUID, tenta buscar pelo email (mas created_by agora é UUID, não email)
            # Isso pode não funcionar - melhor usar UUID sempre
            try:
                # Tenta buscar pelo perfil do email primeiro
                profile_resp = supabase.table("profiles").select("id").eq("email", user_email).limit(1).execute()
                if profile_resp and profile_resp.data:
                    profile_id = profile_resp.data[0].get('id')
                    hours_response = supabase.table("hours_worked_monthly").select("year, month, hours, created_by").eq("created_by", profile_id).execute()
            except Exception:
                hours_response = None

        if hours_response and hasattr(hours_response, 'data') and hours_response.data:
            for row in hours_response.data:
                if 'year' in row and 'month' in row:
                    try:
                        month_date = pd.to_datetime(f"{row['year']}-{int(row['month']):02d}-01").date()
                        if month_date <= accident_date:
                            total_hours += float(row.get('hours', 0) or 0)
                    except Exception:
                        continue

        # 6) Converte horas para dias úteis (8h/dia) com escala *100
        if total_hours > 0:
            work_days = (total_hours * 100.0) / 8.0
            return min(work_days, days_since_admission) if days_since_admission is not None else work_days

        # 7) Fallback: sem horas, usar dias corridos desde admissão
        if days_since_admission is not None:
            return days_since_admission

        # 8) Último fallback: aproximar pela diferença desde o primeiro acidente do mesmo criador
        if employee_identifier:
            try:
                first_acc = supabase.table("accidents").select("occurred_at").eq("created_by", employee_identifier).order("occurred_at").limit(1).execute()
                if first_acc and hasattr(first_acc, 'data') and first_acc.data:
                    first_date = pd.to_datetime(first_acc.data[0]['occurred_at']).date()
                    approx_days = (accident_date - first_date).days
                    return max(0, approx_days)
            except Exception:
                pass

        return 0

    except Exception as e:
        st.error(f"Erro ao calcular dias trabalhados: {str(e)}")
        return 0

def get_work_days_analysis(df):
    """
    Analisa os dias trabalhados até acidentes e retorna estatísticas.
    """
    if df.empty or 'occurred_at' not in df.columns:
        return {}, df
    
    try:
        # Cria uma cópia para não modificar o DataFrame original
        df_work = df.copy()
        
        # Converte data para datetime
        df_work['occurred_at'] = pd.to_datetime(df_work['occurred_at'])
        df_work['accident_date'] = df_work['occurred_at'].dt.date
        
        # Otimização: pré-carregar todos os dados necessários
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        
        # Carregar todos os funcionários de uma vez
        all_employees = {}
        try:
            emp_response = supabase.table("employees").select("id, email, admission_date, user_id").execute()
            if emp_response and hasattr(emp_response, 'data'):
                for emp in emp_response.data:
                    all_employees[emp['id']] = emp
        except Exception:
            pass  # Se não tiver permissão ou erro, continua sem dados de funcionários
        
        # Carregar todos os perfis de uma vez
        all_profiles = {}
        try:
            profile_response = supabase.table("profiles").select("id, email, created_at").execute()
            if profile_response and hasattr(profile_response, 'data'):
                for profile in profile_response.data:
                    all_profiles[profile['id']] = profile
                    all_profiles[profile['email']] = profile  # Adiciona também pelo email para busca direta
        except Exception:
            pass
        
        # Carregar todas as horas trabalhadas de uma vez
        all_hours = {}
        try:
            # Alinhado com estrutura real: employee_id removido, apenas created_by (UUID)
            hours_response = supabase.table("hours_worked_monthly").select("year, month, hours, created_by").execute()
            if hours_response and hasattr(hours_response, 'data'):
                for hour_row in hours_response.data:
                    # Agrupa por created_by (UUID do usuário)
                    created_by = hour_row.get('created_by')
                    if created_by:
                        if created_by not in all_hours:
                            all_hours[created_by] = []
                        all_hours[created_by].append(hour_row)
        except Exception:
            pass
        
        # Carregar primeiros acidentes por criador (para fallback)
        first_accidents = {}
        try:
            first_accs_response = supabase.table("accidents").select("occurred_at, created_by").order("occurred_at").execute()
            if first_accs_response and hasattr(first_accs_response, 'data'):
                for acc in first_accs_response.data:
                    created_by = acc.get('created_by')
                    if created_by and created_by not in first_accidents:
                        first_accidents[created_by] = acc
        except Exception:
            pass
        
        # Função interna otimizada que usa os dados pré-carregados
        def calculate_work_days_optimized(accident_date, employee_identifier=None, employee_id=None):
            """
            Calcula dias trabalhados usando dados pré-carregados
            """
            try:
                admission_date = None
                user_email = None
                user_profile_id = None

                # 1) Prioriza employees.employee_id
                if employee_id and employee_id in all_employees:
                    emp = all_employees[employee_id]
                    if emp.get('admission_date'):
                        admission_date = pd.to_datetime(emp['admission_date']).date()
                    user_email = emp.get('email')
                    user_profile_id = emp.get('user_id')

                # 2) Resolve identificador do funcionário para fallback (profiles)
                if not user_email and not user_profile_id and employee_identifier:
                    if isinstance(employee_identifier, str) and '@' in employee_identifier:
                        user_email = employee_identifier
                    else:
                        user_profile_id = employee_identifier

                # 3) Busca perfil nos dados pré-carregados
                if admission_date is None and (user_email or user_profile_id):
                    profile = None
                    if user_email and user_email in all_profiles:
                        profile = all_profiles[user_email]
                    elif user_profile_id and user_profile_id in all_profiles:
                        profile = all_profiles[user_profile_id]
                    
                    if profile:
                        # created_at como proxy de admissão
                        if profile.get('created_at'):
                            admission_date = pd.to_datetime(profile['created_at']).date()
                        user_profile_id = profile.get('id', user_profile_id)
                        user_email = profile.get('email', user_email)

                # 4) Calcula dias corridos entre admissão e acidente (se conhecido)
                days_since_admission = None
                if admission_date is not None:
                    days_since_admission = (accident_date - admission_date).days
                    if days_since_admission < 0:
                        days_since_admission = 0

                # 5) Busca horas trabalhadas nos dados pré-carregados
                total_hours = 0.0
                hours_list = []
                
                # 5.1) Por employee_id
                if employee_id and employee_id in all_hours:
                    hours_list = all_hours[employee_id]
                # 5.2) Por email (apenas se NÃO houver employee_id)
                elif (not employee_id) and user_email and user_email in all_hours:
                    hours_list = all_hours[user_email]

                if hours_list:
                    for row in hours_list:
                        if 'year' in row and 'month' in row:
                            try:
                                month_date = pd.to_datetime(f"{row['year']}-{int(row['month']):02d}-01").date()
                                if month_date <= accident_date:
                                    total_hours += float(row.get('hours', 0) or 0)
                            except Exception:
                                continue

                # 6) Converte horas para dias úteis (8h/dia) com escala *100
                if total_hours > 0:
                    work_days = (total_hours * 100.0) / 8.0
                    return min(work_days, days_since_admission) if days_since_admission is not None else work_days

                # 7) Fallback: sem horas, usar dias corridos desde admissão
                if days_since_admission is not None:
                    return days_since_admission

                # 8) Último fallback: aproximar pela diferença desde o primeiro acidente do mesmo criador
                if employee_identifier and employee_identifier in first_accidents:
                    first_acc = first_accidents[employee_identifier]
                    first_date = pd.to_datetime(first_acc['occurred_at']).date()
                    approx_days = (accident_date - first_date).days
                    return max(0, approx_days)

                return 0

            except Exception as e:
                # st.error(f"Erro ao calcular dias trabalhados: {str(e)}")  # Comentei para não poluir a interface
                return 0
        
        # Calcula dias trabalhados para cada acidente usando a função otimizada
        work_days_list = []
        for idx, row in df_work.iterrows():
            work_days = calculate_work_days_optimized(
                row['accident_date'],
                row.get('created_by'),
                row.get('employee_id') if 'employee_id' in row else None
            )
            # Garante que não há valores negativos
            work_days = max(0, work_days)
            work_days_list.append(work_days)
        
        df_work['work_days_until_accident'] = work_days_list
        
        # Filtra apenas valores válidos (maiores que 0)
        valid_work_days = df_work[df_work['work_days_until_accident'] > 0]['work_days_until_accident']
        
        # Estatísticas
        analysis = {
            'total_accidents': len(df_work),
            'avg_work_days': valid_work_days.mean() if len(valid_work_days) > 0 else 0,
            'median_work_days': valid_work_days.median() if len(valid_work_days) > 0 else 0,
            'min_work_days': valid_work_days.min() if len(valid_work_days) > 0 else 0,
            'max_work_days': valid_work_days.max() if len(valid_work_days) > 0 else 0,
            'accidents_first_week': len(df_work[df_work['work_days_until_accident'] <= 7]),
            'accidents_first_month': len(df_work[df_work['work_days_until_accident'] <= 30]),
            'accidents_first_year': len(df_work[df_work['work_days_until_accident'] <= 365])
        }
        
        return analysis, df_work
        
    except Exception as e:
        st.error(f"Erro na análise de dias trabalhados: {str(e)}")
        return {}, df

def fetch_accidents(start_date=None, end_date=None):
    """Busca dados de acidentes - filtra por usuário logado"""
    try:
        from managers.supabase_config import get_service_role_client
        from auth.auth_utils import get_user_id, is_admin, get_user_email
        user_id = get_user_id()
        user_email = get_user_email()
        
        if not user_id:
            return pd.DataFrame()
        
        # Usa service_role para contornar RLS e aplicar filtro de segurança no código
        supabase = get_service_role_client()
        
        query = supabase.table("accidents").select("*")
        
        # Filtra por usuário logado, exceto se for admin
        # Admin vê todos os dados sem filtro de created_by
        if not is_admin():
            # Usuário comum vê apenas seus próprios acidentes
            query = query.eq("created_by", user_id)
        # Admin vê todos os acidentes - não aplica filtro de created_by
        
        if start_date:
            query = query.gte("occurred_at", start_date.isoformat())
        if end_date:
            query = query.lte("occurred_at", end_date.isoformat())
            
        response = query.order("occurred_at", desc=True).execute()
        
        if response and hasattr(response, 'data'):
            df = pd.DataFrame(response.data) if response.data else pd.DataFrame()
            
            # Validação adicional de segurança para usuários não-admin
            if not is_admin() and not df.empty:
                # Filtra novamente para garantir (segurança em camadas)
                df = df[df['created_by'] == user_id]
            
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao buscar acidentes: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return pd.DataFrame()

def app(filters=None):
    # Verifica autenticação e trial
    from auth.auth_utils import require_login
    require_login()
    
    st.title("🚨 Acidentes")
    
    # Busca filtros do session state se não foram passados como parâmetro
    if filters is None:
        filters = st.session_state.get('filters', {})
    
    # Tabs para diferentes visualizações
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 Análise", "📋 Registros", "📎 Evidências", "➕ Novo Acidente", "✅ Ações Corretivas", "📚 Instruções"])
    
    # Busca dados uma única vez no início
    with st.spinner("Carregando dados de acidentes..."):
        df = fetch_accidents(
            start_date=filters.get("start_date"),
            end_date=filters.get("end_date")
        )
    
    if df.empty:
        # Verifica se é problema de autenticação ou realmente não há dados
        from auth.auth_utils import get_user_id, get_user_email
        user_id = get_user_id()
        user_email = get_user_email()
        
        if not user_id:
            st.error("❌ **Erro**: Usuário não autenticado. Faça login novamente.")
        else:
            st.warning("Nenhum acidente encontrado com os filtros aplicados.")
        
        work_days_analysis = {}
        df_with_work_days = df
    else:
        # Aplica filtros adicionais
        df = apply_filters_to_df(df, filters)
        
        # Análise de dias trabalhados até acidente
        work_days_analysis, df_with_work_days = get_work_days_analysis(df)
    
    with tab1:
        st.subheader("Análise de Acidentes")
        # Ajuda removida (st.dialog descontinuado)
        with st.expander("Guia rápido de análise", expanded=False):
            st.markdown(
                "1. Confira os filtros na barra lateral para definir escopo.\n"
                "2. Leia as métricas para um panorama imediato (totais, lesões, dias).\n"
                "3. Use os gráficos para identificar tendências por mês, tipo e causa raiz.\n"
                "4. Se necessário, vá para 'Registros' para detalhamento e busca textual.\n"
                "5. Consulte a aba '📚 Instruções' para o passo a passo completo."
            )
        with st.popover("❓ Dicas" ):
            st.markdown(
                "- Os filtros afetam todas as seções desta página.\n"
                "- Sem dados? Tente desmarcar 'Filtrar por data' ou ampliar o período.\n"
                "- Para análise de 'Dias Trabalhados', cadastre funcionários e horas.\n\n"
                "**📝 Encontrou um erro ou tem uma sugestão?**\n"
                "- Acesse **Conta → Feedbacks** no menu para reportar ou sugerir melhorias!"
            )
        
        if not df.empty:
            
            # Métricas principais
            total_accidents = len(df)
            fatal_accidents = len(df[df['type'] == 'fatal'])
            with_injury = len(df[df['type'] == 'lesao'])
            without_injury = len(df[df['type'] == 'sem_lesao'])
            total_lost_days = df['lost_days'].sum() if 'lost_days' in df.columns else 0
            
            metrics = [
                {
                    "title": "Total de Acidentes",
                    "value": total_accidents,
                    "icon": "🚨",
                    "color": "danger" if total_accidents > 0 else "success"
                },
                {
                    "title": "Acidentes Fatais",
                    "value": fatal_accidents,
                    "icon": "💀",
                    "color": "danger" if fatal_accidents > 0 else "success"
                },
                {
                    "title": "Com Lesão",
                    "value": with_injury,
                    "icon": "🏥",
                    "color": "warning"
                },
                {
                    "title": "Dias Perdidos",
                    "value": total_lost_days,
                    "icon": "📅",
                    "color": "info"
                }
            ]
            
            create_metric_row(metrics)
            
            # Análise de Dias Trabalhados até Acidente
            if work_days_analysis and work_days_analysis.get('total_accidents', 0) > 0:
                st.subheader("📅 Análise de Dias Trabalhados até Acidente")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    avg_days = work_days_analysis.get('avg_work_days', 0)
                    if avg_days > 0:
                        st.metric(
                            "Média de Dias",
                            f"{avg_days:.0f}",
                            help="Média de dias trabalhados até o acidente"
                        )
                    else:
                        st.metric(
                            "Média de Dias",
                            "N/A",
                            help="Dados insuficientes para calcular média"
                        )
                
                with col2:
                    st.metric(
                        "Primeira Semana",
                        f"{work_days_analysis.get('accidents_first_week', 0)}",
                        help="Acidentes nos primeiros 7 dias de trabalho"
                    )
                
                with col3:
                    st.metric(
                        "Primeiro Mês",
                        f"{work_days_analysis.get('accidents_first_month', 0)}",
                        help="Acidentes nos primeiros 30 dias de trabalho"
                    )
                
                with col4:
                    st.metric(
                        "Primeiro Ano",
                        f"{work_days_analysis.get('accidents_first_year', 0)}",
                        help="Acidentes nos primeiros 365 dias de trabalho"
                    )
                
                # Informação adicional sobre dados
                if work_days_analysis.get('avg_work_days', 0) == 0:
                    st.info("ℹ️ **Nota**: Para análise precisa de dias trabalhados, é necessário ter dados de funcionários e horas trabalhadas cadastrados no sistema.")
                
                # Gráfico de distribuição de dias trabalhados
                if 'work_days_until_accident' in df_with_work_days.columns:
                    st.subheader("📊 Distribuição de Dias Trabalhados até Acidente")
                    
                    # Filtra apenas valores válidos para o gráfico
                    valid_data = df_with_work_days[df_with_work_days['work_days_until_accident'] > 0].copy()
                    
                    if len(valid_data) > 0:
                        # Cria faixas de dias
                        valid_data['work_days_range'] = pd.cut(
                            valid_data['work_days_until_accident'],
                            bins=[0, 7, 30, 90, 365, float('inf')],
                            labels=['0-7 dias', '8-30 dias', '31-90 dias', '91-365 dias', 'Mais de 1 ano'],
                            include_lowest=True
                        )
                        
                        range_counts = valid_data['work_days_range'].value_counts()
                        
                        fig_work_days = px.bar(
                            x=range_counts.index,
                            y=range_counts.values,
                            title="Acidentes por Faixa de Dias Trabalhados",
                            color=range_counts.values,
                            color_continuous_scale="Oranges"
                        )
                        fig_work_days.update_layout(
                            xaxis_title="Faixa de Dias Trabalhados",
                            yaxis_title="Número de Acidentes",
                            showlegend=False,
                            height=400
                        )
                        st.plotly_chart(fig_work_days, width='stretch')
                    else:
                        st.info("📊 **Distribuição de Dias Trabalhados**\n\nNão há dados suficientes para gerar o gráfico de distribuição.")
            
            # Gráficos
            col1, col2 = st.columns(2)
            
            with col1:
                # Distribuição por tipo - Simplificada
                if 'type' in df.columns:
                    type_counts = df['type'].value_counts()
                    type_names = {'fatal': 'Fatal', 'lesao': 'Com Lesão', 'sem_lesao': 'Sem Lesão'}
                    
                    fig1 = px.pie(
                        values=type_counts.values,
                        names=[type_names.get(t, t) for t in type_counts.index],
                        title="Distribuição por Tipo de Acidente",
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig1.update_layout(
                        height=400,
                        font=dict(size=12)
                    )
                    st.plotly_chart(fig1, width='stretch')
                else:
                    st.info("📊 **Distribuição por Tipo**\n\nNenhum dado de tipo disponível.")
            
            with col2:
                # Acidentes por mês - Simplificada
                if 'occurred_at' in df.columns:
                    df_temp = df.copy()
                    df_temp['month'] = pd.to_datetime(df_temp['occurred_at']).dt.to_period('M')
                    monthly_counts = df_temp.groupby('month').size().reset_index(name='count')
                    monthly_counts['month'] = monthly_counts['month'].astype(str)
                    
                    fig2 = px.bar(
                        monthly_counts,
                        x='month',
                        y='count',
                        title="Acidentes por Mês",
                        color='count',
                        color_continuous_scale="Reds"
                    )
                    fig2.update_layout(
                        height=400,
                        xaxis_title="Mês",
                        yaxis_title="Número de Acidentes",
                        showlegend=False,
                        font=dict(size=12)
                    )
                    fig2.update_traces(marker_line_width=0)
                    st.plotly_chart(fig2, width='stretch')
                else:
                    st.info("📅 **Acidentes por Mês**\n\nNenhum dado de data disponível.")
            
            # Análise por causa raiz - Simplificada
            if 'root_cause' in df.columns and not df['root_cause'].isna().all():
                st.subheader("📋 Análise por Causa Raiz")
                root_cause_counts = df['root_cause'].value_counts()
                
                fig3 = px.bar(
                    x=root_cause_counts.values,
                    y=root_cause_counts.index,
                    orientation='h',
                    title="Acidentes por Causa Raiz",
                    color=root_cause_counts.values,
                    color_continuous_scale="Blues"
                )
                fig3.update_layout(
                    height=400,
                    xaxis_title="Número de Acidentes",
                    yaxis_title="Causa Raiz",
                    showlegend=False,
                    font=dict(size=12)
                )
                fig3.update_traces(marker_line_width=0)
                st.plotly_chart(fig3, width='stretch')
            else:
                st.info("📋 **Análise por Causa Raiz**\n\nNenhum dado de causa raiz disponível.")
    
            # Análise por Classificação (NBR 14280)
            if 'classification' in df.columns and not df['classification'].isna().all():
                st.subheader("📚 Análise por Classificação (NBR 14280)")
                class_counts = df['classification'].value_counts()

                fig_class = px.pie(
                    values=class_counts.values,
                    names=class_counts.index,
                    title="Distribuição por Classificação",
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                fig_class.update_layout(height=380, font=dict(size=12))
                st.plotly_chart(fig_class, width='stretch')
            else:
                st.info("📚 **Classificação (NBR 14280)**\n\nNenhum dado de classificação disponível.")

            # Análise por Parte do Corpo Afetada (NBR 14280)
            if 'body_part' in df.columns and not df['body_part'].isna().all():
                st.subheader("🧍 Análise por Parte do Corpo Afetada (NBR 14280)")
                body_counts = df['body_part'].value_counts().sort_values(ascending=True)

                fig_body = px.bar(
                    x=body_counts.values,
                    y=body_counts.index,
                    orientation='h',
                    title="Acidentes por Parte do Corpo",
                    color=body_counts.values,
                    color_continuous_scale="Tealgrn"
                )
                fig_body.update_layout(
                    height=420,
                    xaxis_title="Número de Acidentes",
                    yaxis_title="Parte do Corpo",
                    showlegend=False,
                    font=dict(size=12)
                )
                fig_body.update_traces(marker_line_width=0)
                st.plotly_chart(fig_body, width='stretch')
            else:
                st.info("🧍 **Parte do Corpo Afetada (NBR 14280)**\n\nNenhum dado disponível.")

    with tab2:
        st.subheader("Registros de Acidentes")
        
        if not df.empty:
            # Filtros adicionais para a tabela
            col1, col2, col3 = st.columns(3)
            
            with col1:
                type_filter = st.selectbox(
                    "Filtrar por Tipo",
                    options=["Todos"] + list(df['type'].unique()) if 'type' in df.columns else ["Todos"],
                    key="accident_type_filter"
                )
            
            with col2:
                status_filter = st.selectbox(
                    "Filtrar por Status",
                    options=["Todos"] + list(df['status'].unique()) if 'status' in df.columns else ["Todos"],
                    key="accident_status_filter"
                )
            
            with col3:
                search_term = st.text_input("Buscar na descrição", key="accident_search")
            
            # Aplica filtros
            filtered_df = df.copy()
            
            if type_filter != "Todos" and 'type' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['type'] == type_filter]
            
            if status_filter != "Todos" and 'status' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['status'] == status_filter]
            
            if search_term and 'description' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['description'].astype(str).str.contains(search_term, case=False, na=False)]
            
            # Exibe tabela de acidentes
            display_cols = ['occurred_at', 'type', 'description', 'lost_days', 'root_cause', 'status']
            available_cols = [col for col in display_cols if col in filtered_df.columns]
            
            # Adiciona coluna de dias trabalhados se disponível
            if 'work_days_until_accident' in filtered_df.columns:
                available_cols.append('work_days_until_accident')
            
            if available_cols:
                st.dataframe(
                    filtered_df[available_cols],
                    width='stretch',
                    hide_index=True
                )
            else:
                st.dataframe(filtered_df, width='stretch', hide_index=True)
        else:
            st.info("Nenhum acidente encontrado.")
    
    with tab3:
        st.subheader("Evidências dos Acidentes")
        
        if not df.empty:
            # Seleciona acidente para ver evidências
            accident_options = {}
            for idx, row in df.iterrows():
                accident_id = row.get('id', idx)
                description = row.get('description', f'Acidente {accident_id}')[:50]
                date_str = row.get('occurred_at', 'Data não informada')
                accident_options[f"{date_str} - {description}..."] = accident_id
            
            selected_accident = st.selectbox(
                "Selecionar Acidente",
                options=list(accident_options.keys()),
                key="evidence_accident_selector"
            )
            
            if selected_accident:
                accident_id = accident_options[selected_accident]
                
                # Busca evidências
                try:
                    attachments = get_attachments("accident", str(accident_id))
                except:
                    attachments = []
                
                if attachments:
                    st.write(f"**Evidências para o acidente selecionado:**")
                    
                    for attachment in attachments:
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.write(f"📎 {attachment['filename']}")
                            if attachment.get('description'):
                                st.caption(attachment['description'])
                        
                        with col2:
                            if st.button("📥 Download", key=f"download_{attachment.get('id', 'unknown')}"):
                                try:
                                    file_data = download_attachment(attachment.get('bucket', ''), attachment.get('path', ''))
                                    if file_data:
                                        st.download_button(
                                            "💾 Baixar Arquivo",
                                            file_data,
                                            attachment.get('filename', 'arquivo'),
                                            key=f"download_btn_{attachment.get('id', 'unknown')}"
                                        )
                                except:
                                    st.error("Erro ao baixar arquivo")
                        
                        with col3:
                            if st.button("🗑️ Remover", key=f"remove_{attachment.get('id', 'unknown')}"):
                                try:
                                    if delete_attachment(attachment.get('id', '')):
                                        st.success("Evidência removida!")
                                        st.rerun()
                                except:
                                    st.error("Erro ao remover evidência")
                else:
                    st.info("Nenhuma evidência encontrada para este acidente.")
        else:
            st.info("Nenhum acidente encontrado para exibir evidências.")
    
    with tab4:
        st.subheader("Registrar Novo Acidente")
        
        with st.expander("📖 Como Cadastrar um Acidente", expanded=False):
            st.markdown("""
            1. Cadastre ou selecione o **funcionário** envolvido  
            2. Preencha data, tipo, classificação e descrição  
            3. Salve o acidente  
            """)

        # ---- Funcionário: seleção + cadastro FORA do form do acidente ----
        from auth.auth_utils import get_user_id
        from services.employees import create_employee, get_all_employees

        st.markdown("### 👷 Funcionário envolvido")
        current_user_id = get_user_id()
        if not current_user_id:
            st.error("Sessão inválida: faça login novamente para cadastrar/selecionar funcionários.")

        employees = get_all_employees()
        emp_options = {"— (Sem funcionário) —": None}
        for e in employees:
            name = e.get("full_name") or "Sem Nome"
            dept = e.get("department") or "-"
            email = e.get("email") or ""
            label = f"{name} ({dept})"
            if email:
                label += f" — {email}"
            emp_options[label] = e.get("id")

        if not employees:
            st.warning(
                "Nenhum funcionário cadastrado ainda. Use o formulário abaixo para adicionar "
                "o acidentado e depois selecione-o na lista."
            )
        else:
            st.caption(f"{len(employees)} funcionário(s) disponível(is).")

        selected_emp_label = st.selectbox(
            "Selecionar funcionário",
            options=list(emp_options.keys()),
            key="accident_employee_select",
            help="Lista dos funcionários vinculados à sua conta.",
        )
        st.session_state["accident_selected_employee_id"] = emp_options[selected_emp_label]

        with st.expander("➕ Cadastrar novo funcionário", expanded=not employees):
            with st.form("new_employee_accident_form", clear_on_submit=True):
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    emp_full_name = st.text_input("Nome Completo *")
                    emp_document = st.text_input("CPF/Documento")
                    emp_email = st.text_input("E-mail (opcional)")
                with col_e2:
                    emp_department = st.text_input("Departamento")
                    emp_job_title = st.text_input("Cargo")
                    emp_admission = st.date_input("Data de Admissão", value=date.today())
                    emp_active = st.checkbox("Funcionário Ativo", value=True)

                if st.form_submit_button("💾 Cadastrar Funcionário", type="primary"):
                    errors = []
                    if not (emp_full_name or "").strip():
                        errors.append("Nome completo é obrigatório.")
                    if not current_user_id:
                        errors.append("Sessão inválida: não foi possível identificar o usuário logado.")

                    if errors:
                        for error in errors:
                            st.error(error)
                    else:
                        ok = create_employee({
                            "full_name": emp_full_name.strip(),
                            "document_id": (emp_document or "").strip() or None,
                            "email": (emp_email or "").strip().lower() or None,
                            "job_title": (emp_job_title or "").strip() or None,
                            "department": (emp_department or "").strip() or None,
                            "admission_date": emp_admission.isoformat() if emp_admission else None,
                            "status": "active" if emp_active else "inactive",
                            "user_id": current_user_id,
                        })
                        if ok:
                            st.rerun()

        st.markdown("---")
        
        with st.form("new_accident_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                date_input = st.date_input("Data do Acidente", value=date.today())
                accident_type = st.selectbox(
                    "Tipo",
                    options=["fatal", "lesao", "sem_lesao"],
                    format_func=lambda x: {
                        "fatal": "Fatal",
                        "lesao": "Com Lesão", 
                        "sem_lesao": "Sem Lesão"
                    }[x]
                )
                lost_days = st.number_input("Dias Perdidos", min_value=0, value=0)
            
            with col2:
                classification_options = [
                    "Típico",
                    "Trajeto",
                    "Doença do Trabalho",
                    "Outro"
                ]
                classification_sel = st.selectbox("Classificação", options=classification_options)
                # Evita widget condicional dentro do form (quebra o estado do Streamlit)
                classification_other = st.text_input(
                    "Se Outro, especifique a classificação",
                    placeholder="Preencha apenas se escolheu Outro",
                )
                classification = (
                    classification_other.strip()
                    if classification_sel == "Outro" and classification_other.strip()
                    else classification_sel
                )

                body_part_options = [
                    "Cabeça",
                    "Olhos",
                    "Face",
                    "Pescoço",
                    "Membros Superiores",
                    "Mãos",
                    "Membros Inferiores",
                    "Pés",
                    "Tronco",
                    "Abdome",
                    "Coluna Vertebral",
                    "Múltiplas Partes",
                    "Outras"
                ]
                body_part_sel = st.selectbox("Parte do Corpo Afetada", options=body_part_options)
                body_part_other = st.text_input(
                    "Se Outras, especifique a parte do corpo",
                    placeholder="Preencha apenas se escolheu Outras",
                )
                body_part = (
                    body_part_other.strip()
                    if body_part_sel == "Outras" and body_part_other.strip()
                    else body_part_sel
                )
                root_cause = st.selectbox(
                    "Causa Raiz",
                    options=["Fator Humano", "Fator Material", "Fator Ambiental", 
                            "Fator Organizacional", "Fator Técnico", "Outros"]
                )

            employee_id = st.session_state.get("accident_selected_employee_id")
            if employee_id:
                st.info(f"Funcionário selecionado: **{selected_emp_label}**")
            else:
                st.caption("Nenhum funcionário selecionado (opcional).")
            
            title = st.text_input(
                "Título do Acidente",
                placeholder="Ex: Queda durante manutenção, Vazamento de produto, etc.",
                help="Título breve que identifica o acidente. Será usado na página de investigação."
            )
            
            description = st.text_area("Descrição do Acidente", height=100)

            status = st.selectbox(
                "Status",
                options=["aberto", "fechado"],
                format_func=lambda x: {
                    "aberto": "Aberto",
                    "fechado": "Fechado"
                }[x]
            )
            
            uploaded_files = st.file_uploader(
                "Evidências (Fotos, PDFs, etc.)",
                accept_multiple_files=True,
                type=['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx']
            )
            
            submitted = st.form_submit_button("💾 Salvar Acidente", type="primary")
            
            if submitted:
                if not description.strip():
                    st.error("Descrição é obrigatória.")
                else:
                    try:
                        from managers.supabase_config import get_service_role_client
                        # Usa service_role para contornar RLS ao inserir acidente
                        supabase = get_service_role_client()
                        
                        user_id = get_user_id()
                        if not user_id:
                            st.error("Usuário não autenticado.")
                            return
                        
                        # Insere acidente
                        accident_data = {
                            "occurred_at": date_input.isoformat(),
                            "type": accident_type,
                            "classification": classification,
                            "body_part": body_part,
                            "description": description,
                            "lost_days": lost_days,
                            "root_cause": root_cause,
                            "status": status,
                            "created_by": user_id
                        }
                        
                        # Adiciona título se fornecido (usa description como fallback)
                        if title and title.strip():
                            accident_data["title"] = title.strip()
                        else:
                            # Se não forneceu título, usa os primeiros 50 caracteres da descrição
                            accident_data["title"] = description[:50].strip() if description else "Acidente sem título"
                        
                        # Adiciona employee_id se um funcionário foi selecionado
                        if employee_id:
                            accident_data["employee_id"] = employee_id
                        
                        result = supabase.table("accidents").insert(accident_data).execute()
                        
                        if result.data:
                            accident_id = result.data[0]['id']
                            st.success("✅ Acidente registrado com sucesso!")
                            st.info("💡 **Dica:** Agora você pode iniciar a investigação deste acidente na página 'Investigação de Acidentes'.")
                            
                            # Registra log da ação
                            try:
                                from services.user_logs import log_action
                                log_action(
                                    action_type="create",
                                    entity_type="accident",
                                    description=f"Acidente criado: {description[:100]}...",
                                    entity_id=accident_id,
                                    metadata={"type": accident_type, "status": status, "lost_days": lost_days}
                                )
                            except:
                                pass  # Não interrompe o fluxo se houver erro no log
                            
                            # Upload de evidências
                            if uploaded_files:
                                for uploaded_file in uploaded_files:
                                    file_bytes = uploaded_file.read()
                                    upload_evidence(
                                        file_bytes,
                                        uploaded_file.name,
                                        "accident",
                                        str(accident_id),
                                        description=f"Evidência do acidente de {date_input}"
                                    )
                                st.success(f"✅ {len(uploaded_files)} evidência(s) enviada(s)!")
                            
                            st.rerun()
                        else:
                            st.error("Erro ao salvar acidente.")
                            
                    except Exception as e:
                        st.error(f"Erro: {str(e)}")
    
    with tab5:
        st.subheader("✅ Ações Corretivas")
        st.info("📋 Registre e gerencie ações corretivas relacionadas aos acidentes usando a metodologia 5W2H")
        
        # Busca todos os acidentes para seleção
        if df.empty:
            st.warning("Nenhum acidente encontrado. Registre acidentes primeiro para criar ações corretivas.")
        else:
            # Seleção de acidente
            accident_options = {f"ID: {row['id'][:8]}... - {row.get('description', 'Sem descrição')[:50]}": row['id'] 
                              for _, row in df.iterrows()}
            
            selected_accident_id = st.selectbox(
                "Selecione o Acidente",
                options=list(accident_options.keys()),
                help="Selecione o acidente para ver ou criar ações corretivas"
            )
            
            if selected_accident_id:
                accident_id = accident_options[selected_accident_id]
                
                # Busca ações existentes
                from services.actions import get_actions_by_entity, create_action, update_action_status, delete_action, action_form
                
                actions = get_actions_by_entity("accident", accident_id)
                
                # Mostra ações existentes
                if actions:
                    st.markdown("### Ações Corretivas Existentes")
                    for action in actions:
                        with st.expander(f"🔹 {action.get('what', 'Sem descrição')[:60]}... - Status: {action.get('status', 'N/A')}"):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown(f"**O QUE:** {action.get('what', '-')}")
                                st.markdown(f"**QUEM:** {action.get('who', '-')}")
                                st.markdown(f"**QUANDO:** {action.get('when_date', '-')}")
                                st.markdown(f"**ONDE:** {action.get('where_text', '-')}")
                                st.markdown(f"**POR QUÊ:** {action.get('why', '-')}")
                                st.markdown(f"**COMO:** {action.get('how', '-')}")
                                if action.get('how_much'):
                                    st.markdown(f"**QUANTO:** R$ {action.get('how_much', 0):,.2f}")
                            
                            with col2:
                                # Atualizar status
                                new_status = st.selectbox(
                                    "Alterar Status",
                                    options=["aberta", "em_andamento", "fechada"],
                                    index=["aberta", "em_andamento", "fechada"].index(action.get("status", "aberta")),
                                    key=f"status_{action.get('id')}"
                                )
                                
                                if new_status != action.get("status"):
                                    if st.button("Atualizar", key=f"update_{action.get('id')}"):
                                        if update_action_status(action.get('id'), new_status):
                                            st.success("Status atualizado!")
                                            st.rerun()
                                
                                if st.button("🗑️ Remover", key=f"delete_{action.get('id')}"):
                                    if delete_action(action.get('id')):
                                        st.success("Ação removida!")
                                        st.rerun()
                else:
                    st.info("Nenhuma ação corretiva registrada para este acidente.")
                
                # Formulário para nova ação
                st.markdown("---")
                st.markdown("### ➕ Nova Ação Corretiva")
                
                new_action = action_form("accident", accident_id)
                if new_action:
                    if create_action(new_action):
                        st.success("✅ Ação corretiva registrada com sucesso!")
                        st.rerun()
    
    with tab6:
        # Importa e exibe instruções
        from components.instructions import create_instructions_page, get_accidents_instructions
        
        instructions_data = get_accidents_instructions()
        create_instructions_page(
            title=instructions_data["title"],
            description=instructions_data["description"],
            sections=instructions_data["sections"],
            tips=instructions_data["tips"],
            warnings=instructions_data["warnings"],
            references=instructions_data["references"]
        )


def download_attachment(bucket, path):
    """Download de anexo"""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if supabase:
            response = supabase.storage.from_(bucket).download(path)
            return response
        return None
    except:
        return None

def delete_attachment(attachment_id):
    """Remove anexo"""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if supabase:
            supabase.table("attachments").delete().eq("id", attachment_id).execute()
            return True
        return False
    except:
        return False

def get_employees():
    """Busca funcionários (employees) - filtra por usuário logado"""
    try:
        from services.employees import get_all_employees
        return get_all_employees()
    except:
        return []

if __name__ == "__main__":
    app({})
