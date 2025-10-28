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
            
        supabase = get_client()
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
        supabase = get_client()
        response = supabase.table("attachments").select("*").eq("entity_type", entity_type).eq("entity_id", entity_id).execute()
        return response.data
    except Exception as e:
        st.error(f"Erro ao buscar anexos: {str(e)}")
        return []

def download_attachment(bucket: str, path: str) -> Optional[bytes]:
    """Download de anexo do Supabase Storage"""
    try:
        supabase = get_client()
        response = supabase.storage.from_(bucket).download(path)
        return response
    except Exception as e:
        st.error(f"Erro no download: {str(e)}")
        return None

def delete_attachment(attachment_id: str) -> bool:
    """Remove anexo do banco e storage"""
    try:
        supabase = get_client()
        
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
        supabase = get_client()
        
        # Valida colunas necessárias
        required_cols = ['site_code', 'year', 'month', 'hours']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(f"Colunas obrigatórias ausentes: {missing_cols}")
            return False
        
        # Prepara dados para inserção
        hours_rows = []
        for _, row in df.iterrows():
            site_code = row['site_code']
            if site_code not in site_mapping:
                st.warning(f"Site {site_code} não encontrado no mapeamento")
                continue
                
            hours_rows.append({
                "site_id": site_mapping[site_code],
                "year": int(row['year']),
                "month": int(row['month']),
                "hours": float(row['hours']),
            })
        
        if not hours_rows:
            st.error("Nenhum dado válido para importar")
            return False
        
        # Upsert no banco
        result = supabase.table("hours_worked_monthly").upsert(
            hours_rows, 
            on_conflict="site_id,year,month"
        ).execute()
        
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
        supabase = get_client()
        
        # Valida colunas necessárias
        required_cols = ['site_code', 'date', 'severity', 'description']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(f"Colunas obrigatórias ausentes: {missing_cols}")
            return False
        
        # Prepara dados para inserção
        accident_rows = []
        for _, row in df.iterrows():
            site_code = row['site_code']
            if site_code not in site_mapping:
                st.warning(f"Site {site_code} não encontrado no mapeamento")
                continue
                
            accident_rows.append({
                "site_id": site_mapping[site_code],
                "date": row['date'],
                "severity": row['severity'],
                "description": row['description'],
                "lost_days": int(row.get('lost_days', 0)),
                "root_cause": row.get('root_cause', ''),
                "corrective_actions": row.get('corrective_actions', ''),
            })
        
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
