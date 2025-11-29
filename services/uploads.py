import io
import time
import streamlit as st
from typing import Optional, List, Dict, Any
from managers.supabase_config import get_supabase_client
import pandas as pd

def upload_evidence(file_bytes: bytes, 
                   filename: str, 
                   entity_type: str, 
                   entity_id: str,
                   user_email: Optional[str] = None,
                   description: str = "") -> Optional[str]:
    """Upload de evidência para Supabase Storage"""
    try:
        # Se user_email não fornecido, busca do usuário atual
        if not user_email:
            from auth.auth_utils import get_user_email
            user_email = get_user_email()
        
        if not user_email:
            st.error("Usuário não identificado para upload")
            return None
            
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            st.error("Erro ao conectar com o banco de dados")
            return None
        
        bucket = "evidencias"
        
        # Gera path único baseado no timestamp
        timestamp = int(time.time())
        file_extension = filename.split('.')[-1] if '.' in filename else ''
        safe_filename = f"{timestamp}_{filename}"
        path = f"{entity_type}/{entity_id}/{safe_filename}"
        
        # Upload do arquivo
        result = supabase.storage.from_(bucket).upload(path, io.BytesIO(file_bytes))
        
        if result:
            # Registra no banco de dados
            attachment_data = {
                "bucket": bucket,
                "path": path,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "uploaded_by": user_email,
                "uploaded_at": "now()"
            }
            
            response = supabase.table("attachments").insert(attachment_data).execute()
            
            if response.data:
                return path
            else:
                st.error("Erro ao registrar anexo no banco de dados")
                return None
        else:
            st.error("Erro no upload do arquivo")
            return None
            
    except Exception as e:
        st.error(f"Erro no upload: {str(e)}")
        return None

def get_attachments(entity_type: str, entity_id: str) -> List[Dict[str, Any]]:
    """Busca anexos de uma entidade"""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            return []
        
        response = supabase.table("attachments").select("*").eq("entity_type", entity_type).eq("entity_id", entity_id).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Erro ao buscar anexos: {str(e)}")
        return []

def download_attachment(bucket: str, path: str) -> Optional[bytes]:
    """Download de anexo do Supabase Storage"""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            return None
        
        response = supabase.storage.from_(bucket).download(path)
        return response
    except Exception as e:
        st.error(f"Erro no download: {str(e)}")
        return None

def delete_attachment(attachment_id: str) -> bool:
    """Remove anexo do banco e storage"""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            st.error("Erro ao conectar com o banco de dados")
            return False
        
        # Busca dados do anexo
        attachment = supabase.table("attachments").select("*").eq("id", attachment_id).execute()
        
        if attachment.data:
            att_data = attachment.data[0]
            
            # Remove do storage
            supabase.storage.from_(att_data["bucket"]).remove([att_data["path"]])
            
            # Remove do banco
            supabase.table("attachments").delete().eq("id", attachment_id).execute()
            
            return True
        return False
        
    except Exception as e:
        st.error(f"Erro ao remover anexo: {str(e)}")
        return False

def import_hours_csv(df: pd.DataFrame, site_mapping: Dict[str, str]) -> bool:
    """Importa dados de horas trabalhadas de CSV"""
    try:
        from auth.auth_utils import get_user_id
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            st.error("Erro ao conectar com o banco de dados")
            return False
        
        # Valida colunas necessárias (site_id removido da tabela)
        required_cols = ['year', 'month', 'hours']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(f"Colunas obrigatórias ausentes: {missing_cols}")
            return False
        
        user_id = get_user_id()
        if not user_id:
            st.error("Usuário não autenticado")
            return False
        
        # Prepara dados para inserção (alinhado com estrutura real)
        hours_rows = []
        for _, row in df.iterrows():
            hours_rows.append({
                "year": int(row['year']),
                "month": int(row['month']),
                "hours": float(row['hours']),
                "created_by": user_id
            })
            # site_id removido - não existe na tabela hours_worked_monthly
        
        if not hours_rows:
            st.error("Nenhum dado válido para importar")
            return False
        
        # Insere no banco (não há unique constraint para upsert)
        result = supabase.table("hours_worked_monthly").insert(hours_rows).execute()
        
        if result.data:
            st.success(f"✅ {len(hours_rows)} registros de horas importados com sucesso!")
            return True
        else:
            st.error("Erro ao importar dados")
            return False
            
    except Exception as e:
        st.error(f"Erro na importação: {str(e)}")
        return False

def import_accidents_csv(df: pd.DataFrame, site_mapping: Dict[str, str]) -> bool:
    """Importa dados de acidentes de CSV"""
    try:
        from auth.auth_utils import get_user_id
        from managers.supabase_config import get_service_role_client
        # Usa service_role para contornar RLS ao importar acidentes
        supabase = get_service_role_client()
        
        # Valida colunas necessárias (alinhado com estrutura real)
        required_cols = ['occurred_at', 'type', 'description']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(f"Colunas obrigatórias ausentes: {missing_cols}")
            return False
        
        user_id = get_user_id()
        if not user_id:
            st.error("Usuário não autenticado")
            return False
        
        # Prepara dados para inserção (alinhado com estrutura real da tabela accidents)
        accident_rows = []
        for _, row in df.iterrows():
            # Mapeia 'severity' do CSV para 'type' enum (fatal, lesao, sem_lesao)
            severity = str(row.get('severity', 'lesao')).lower()
            type_map = {
                'fatal': 'fatal',
                'lesao': 'lesao',
                'sem_lesao': 'sem_lesao',
                'com lesão': 'lesao',
                'sem lesão': 'sem_lesao'
            }
            accident_type = type_map.get(severity, 'lesao')
            
            accident_row = {
                "occurred_at": row['occurred_at'] if 'occurred_at' in row else row.get('date', ''),
                "type": accident_type,  # severity -> type (enum)
                "classification": row.get('classification', 'leve'),
                "body_part": row.get('body_part'),
                "description": row['description'],
                "lost_days": int(row.get('lost_days', 0)),
                "root_cause": row.get('root_cause', ''),
                "status": row.get('status', 'fechado'),  # default 'fechado'
                "created_by": user_id
            }
            
            # Adiciona employee_id se presente no CSV
            if 'employee_id' in row and row.get('employee_id'):
                accident_row["employee_id"] = row['employee_id']
            
            accident_rows.append(accident_row)
        
        if not accident_rows:
            st.error("Nenhum dado válido para importar")
            return False
        
        # Insere no banco
        result = supabase.table("accidents").insert(accident_rows).execute()
        
        if result.data:
            st.success(f"✅ {len(accident_rows)} acidentes importados com sucesso!")
            return True
        else:
            st.error("Erro ao importar dados")
            return False
            
    except Exception as e:
        st.error(f"Erro na importação: {str(e)}")
        return False
