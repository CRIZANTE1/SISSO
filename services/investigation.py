"""
Serviço para operações de investigação de acidentes
Adaptado para arquitetura multi-acidente com session_state
"""
import io
import time
from typing import Optional, List, Dict, Any
from datetime import datetime
from managers.supabase_config import get_supabase_client
from auth.auth_utils import get_user_id, get_user_email
import streamlit as st


def create_accident(title: str, description: str = "", occurrence_date: Optional[datetime] = None, 
                   **kwargs) -> Optional[str]:
    """Cria uma nova investigação de acidente com campos expandidos do relatório Vibra"""
    try:
        supabase = get_supabase_client()
        user_id = get_user_id()
        
        if not user_id:
            st.error("Usuário não autenticado")
            return None
        
        data = {
            "title": title,
            "description": description,
            "status": "Open",
            "created_by": user_id
        }
        
        if occurrence_date:
            data["occurrence_date"] = occurrence_date.isoformat()
        
        # Adiciona campos opcionais do relatório Vibra
        optional_fields = [
            'registry_number', 'base_location',
            'class_injury', 'class_community', 'class_environment', 
            'class_process_safety', 'class_asset_damage', 'class_near_miss',
            'severity_level', 'estimated_loss_value',
            'product_released', 'volume_released', 'volume_recovered',
            'release_duration_hours', 'equipment_involved', 'area_affected'
        ]
        
        for field in optional_fields:
            if field in kwargs and kwargs[field] is not None:
                data[field] = kwargs[field]
        
        response = supabase.table("accidents").insert(data).execute()
        
        if response.data:
            return response.data[0]["id"]
        return None
    except Exception as e:
        st.error(f"Erro ao criar investigação: {str(e)}")
        return None


def update_accident(accident_id: str, **kwargs) -> bool:
    """Atualiza dados de uma investigação de acidente"""
    try:
        supabase = get_supabase_client()
        
        # Remove campos None
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        
        if not update_data:
            return True  # Nada para atualizar
        
        response = supabase.table("accidents").update(update_data).eq("id", accident_id).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Erro ao atualizar investigação: {str(e)}")
        return False


def get_involved_people(accident_id: str, person_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Busca pessoas envolvidas em uma investigação"""
    try:
        supabase = get_supabase_client()
        query = supabase.table("involved_people").select("*").eq("accident_id", accident_id)
        
        if person_type:
            query = query.eq("person_type", person_type)
        
        response = query.order("created_at", desc=False).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Erro ao buscar pessoas envolvidas: {str(e)}")
        return []


def upsert_involved_people(accident_id: str, people: List[Dict[str, Any]]) -> bool:
    """Insere ou atualiza pessoas envolvidas (remove existentes e insere novas)"""
    try:
        supabase = get_supabase_client()
        user_id = get_user_id()
        
        if not user_id:
            st.error("Usuário não autenticado")
            return False
        
        # Remove pessoas existentes
        supabase.table("involved_people").delete().eq("accident_id", accident_id).execute()
        
        # Insere novas pessoas
        if people:
            for person in people:
                person['accident_id'] = accident_id
                person['created_by'] = user_id
            
            response = supabase.table("involved_people").insert(people).execute()
            return bool(response.data)
        
        return True
    except Exception as e:
        st.error(f"Erro ao salvar pessoas envolvidas: {str(e)}")
        return False


def get_accidents() -> List[Dict[str, Any]]:
    """Busca todos os acidentes da tabela accidents para investigação"""
    try:
        from auth.auth_utils import get_user_id, is_admin
        supabase = get_supabase_client()
        user_id = get_user_id()
        
        # Busca acidentes (filtra por usuário se não for admin)
        query = supabase.table("accidents").select("id, title, description, occurrence_date, occurred_at, status, created_at, type, classification")
        
        if not is_admin() and user_id:
            query = query.eq("created_by", user_id)
        
        response = query.order("created_at", desc=True).execute()
        
        if response.data:
            # Normaliza os dados: usa title se existir, senão usa description
            # usa occurrence_date se existir, senão usa occurred_at
            normalized_data = []
            for acc in response.data:
                normalized = {
                    "id": acc.get("id"),
                    "title": acc.get("title") or acc.get("description", "Acidente sem título")[:50],
                    "description": acc.get("description", ""),
                    "occurrence_date": acc.get("occurrence_date") or acc.get("occurred_at"),
                    "status": acc.get("status", "aberto"),
                    "created_at": acc.get("created_at"),
                    "type": acc.get("type"),
                    "classification": acc.get("classification")
                }
                normalized_data.append(normalized)
            
            return normalized_data
        return []
    except Exception as e:
        st.error(f"Erro ao buscar acidentes: {str(e)}")
        return []


def get_accident(accident_id: str) -> Optional[Dict[str, Any]]:
    """Busca um acidente específico da tabela accidents"""
    try:
        supabase = get_supabase_client()
        response = supabase.table("accidents").select("*").eq("id", accident_id).execute()
        
        if response.data and len(response.data) > 0:
            acc = response.data[0]
            # Normaliza os dados para compatibilidade
            normalized = {
                "id": acc.get("id"),
                "title": acc.get("title") or acc.get("description", "Acidente sem título"),
                "description": acc.get("description", ""),
                "occurrence_date": acc.get("occurrence_date") or acc.get("occurred_at"),
                # Normaliza status: 'aberto'/'fechado' -> 'Open'/'Closed'
                "status": "Open" if acc.get("status", "aberto").lower() in ["aberto", "open"] else "Closed",
                "created_at": acc.get("created_at"),
                "type": acc.get("type"),
                "classification": acc.get("classification"),
                # Campos expandidos do relatório Vibra
                "registry_number": acc.get("registry_number"),
                "base_location": acc.get("base_location"),
                "class_injury": acc.get("class_injury"),
                "class_community": acc.get("class_community"),
                "class_environment": acc.get("class_environment"),
                "class_process_safety": acc.get("class_process_safety"),
                "class_asset_damage": acc.get("class_asset_damage"),
                "class_near_miss": acc.get("class_near_miss"),
                "severity_level": acc.get("severity_level"),
                "estimated_loss_value": acc.get("estimated_loss_value"),
                "product_released": acc.get("product_released"),
                "volume_released": acc.get("volume_released"),
                "volume_recovered": acc.get("volume_recovered"),
                "release_duration_hours": acc.get("release_duration_hours"),
                "equipment_involved": acc.get("equipment_involved"),
                "area_affected": acc.get("area_affected")
            }
            return normalized
        return None
    except Exception as e:
        st.error(f"Erro ao buscar acidente: {str(e)}")
        return None


def upload_evidence_image(accident_id: str, file_bytes: bytes, filename: str, description: str = "") -> Optional[str]:
    """Upload de imagem de evidência para Supabase Storage"""
    try:
        supabase = get_supabase_client()
        user_id = get_user_id()
        
        if not user_id:
            st.error("Usuário não autenticado")
            return None
        
        bucket = "evidencias"
        
        # Gera path único
        timestamp = int(time.time())
        file_extension = filename.split('.')[-1] if '.' in filename else ''
        safe_filename = f"{timestamp}_{filename}"
        path = f"investigations/{accident_id}/{safe_filename}"
        
        # Upload do arquivo (substitui se já existir)
        try:
            supabase.storage.from_(bucket).remove([path])
        except:
            pass
        
        result = supabase.storage.from_(bucket).upload(path, io.BytesIO(file_bytes), file_options={"content-type": f"image/{file_extension}", "upsert": "true"})
        
        if result:
            # Obtém URL pública
            try:
                public_url = supabase.storage.from_(bucket).get_public_url(path)
            except:
                # Se não conseguir URL pública, constrói manualmente
                import os
                url = os.environ.get("SUPABASE_URL") or st.secrets.get("supabase", {}).get("url", "")
                public_url = f"{url}/storage/v1/object/public/{bucket}/{path}"
            
            # Registra no banco de dados
            evidence_data = {
                "accident_id": accident_id,
                "image_url": public_url,
                "description": description,
                "uploaded_by": user_id
            }
            
            response = supabase.table("evidence").insert(evidence_data).execute()
            
            if response.data:
                return public_url
            else:
                st.error("Erro ao registrar evidência no banco de dados")
                return None
        else:
            st.error("Erro no upload do arquivo")
            return None
            
    except Exception as e:
        st.error(f"Erro no upload: {str(e)}")
        return None


def get_evidence(accident_id: str) -> List[Dict[str, Any]]:
    """Busca evidências de uma investigação"""
    try:
        supabase = get_supabase_client()
        response = supabase.table("evidence").select("*").eq("accident_id", accident_id).order("uploaded_at", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Erro ao buscar evidências: {str(e)}")
        return []


def add_timeline_event(accident_id: str, event_time: datetime, description: str) -> bool:
    """Adiciona evento à timeline"""
    try:
        supabase = get_supabase_client()
        user_id = get_user_id()
        
        if not user_id:
            st.error("Usuário não autenticado")
            return False
        
        data = {
            "accident_id": accident_id,
            "event_time": event_time.isoformat(),
            "description": description,
            "created_by": user_id
        }
        
        response = supabase.table("timeline").insert(data).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Erro ao adicionar evento: {str(e)}")
        return False


def get_timeline(accident_id: str) -> List[Dict[str, Any]]:
    """Busca timeline de uma investigação"""
    try:
        supabase = get_supabase_client()
        response = supabase.table("timeline").select("*").eq("accident_id", accident_id).order("event_time", desc=False).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Erro ao buscar timeline: {str(e)}")
        return []


def get_root_node(accident_id: str) -> Optional[Dict[str, Any]]:
    """Busca o nó raiz de uma investigação"""
    try:
        supabase = get_supabase_client()
        response = supabase.table("fault_tree_nodes").select("*").eq("accident_id", accident_id).eq("type", "root").limit(1).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Erro ao buscar nó raiz: {str(e)}")
        return None


def create_root_node(accident_id: str, label: str) -> Optional[str]:
    """Cria nó raiz para uma investigação"""
    try:
        supabase = get_supabase_client()
        user_id = get_user_id()
        
        if not user_id:
            st.error("Usuário não autenticado")
            return None
        
        data = {
            "accident_id": accident_id,
            "label": label,
            "type": "root",
            "status": "pending",
            "created_by": user_id
        }
        
        response = supabase.table("fault_tree_nodes").insert(data).execute()
        
        if response.data:
            return response.data[0]["id"]
        return None
    except Exception as e:
        st.error(f"Erro ao criar nó raiz: {str(e)}")
        return None


def add_fault_tree_node(accident_id: str, parent_id: Optional[str], label: str, node_type: str) -> Optional[str]:
    """Adiciona nó à árvore de falhas"""
    try:
        supabase = get_supabase_client()
        user_id = get_user_id()
        
        if not user_id:
            st.error("Usuário não autenticado")
            return None
        
        data = {
            "accident_id": accident_id,
            "label": label,
            "type": node_type,
            "status": "pending",
            "created_by": user_id
        }
        
        if parent_id:
            data["parent_id"] = parent_id
        
        response = supabase.table("fault_tree_nodes").insert(data).execute()
        
        if response.data:
            return response.data[0]["id"]
        return None
    except Exception as e:
        st.error(f"Erro ao adicionar nó: {str(e)}")
        return None


def get_tree_nodes(accident_id: str) -> List[Dict[str, Any]]:
    """Busca todos os nós da árvore de falhas de uma investigação"""
    try:
        supabase = get_supabase_client()
        response = supabase.table("fault_tree_nodes").select("*").eq("accident_id", accident_id).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Erro ao buscar nós: {str(e)}")
        return []


def update_node_status(node_id: str, status: str) -> bool:
    """Atualiza status de validação de um nó"""
    try:
        supabase = get_supabase_client()
        response = supabase.table("fault_tree_nodes").update({"status": status}).eq("id", node_id).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Erro ao atualizar status: {str(e)}")
        return False


def link_nbr_standard_to_node(node_id: str, nbr_standard_id: int) -> bool:
    """Vincula um padrão NBR a um nó validado"""
    try:
        supabase = get_supabase_client()
        response = supabase.table("fault_tree_nodes").update({"nbr_standard_id": nbr_standard_id}).eq("id", node_id).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Erro ao vincular padrão NBR: {str(e)}")
        return False


def get_nbr_standards(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Busca padrões NBR, opcionalmente filtrados por categoria"""
    try:
        supabase = get_supabase_client()
        query = supabase.table("nbr_standards").select("*")
        
        if category:
            query = query.eq("category", category)
        
        response = query.order("code").execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Erro ao buscar padrões NBR: {str(e)}")
        return []


def get_validated_nodes(accident_id: str) -> List[Dict[str, Any]]:
    """Busca apenas nós validados de uma investigação"""
    try:
        supabase = get_supabase_client()
        response = supabase.table("fault_tree_nodes").select("*, nbr_standards(code, description, category)").eq("accident_id", accident_id).eq("status", "validated").execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Erro ao buscar nós validados: {str(e)}")
        return []


def build_fault_tree_json(accident_id: str) -> Optional[Dict[str, Any]]:
    """
    Converte dados planos do banco em estrutura hierárquica JSON.
    Função recursiva que constrói a árvore de falhas.
    
    Retorna None se não houver nó raiz, ou um dicionário com a estrutura completa.
    """
    try:
        # Busca todos os nós do acidente
        nodes = get_tree_nodes(accident_id)
        
        if not nodes:
            return None
        
        # Busca padrões NBR para incluir códigos
        nbr_standards_map = {}
        try:
            supabase = get_supabase_client()
            # Busca todos os padrões NBR
            nbr_response = supabase.table("nbr_standards").select("id, code").execute()
            if nbr_response.data:
                # Cria mapa: nbr_standard_id (int) -> code (string)
                nbr_standards_map = {int(std['id']): std['code'] for std in nbr_response.data}
        except Exception as e:
            # Se falhar, continua sem códigos NBR
            pass
        
        # Cria dicionário indexado por ID para acesso rápido
        nodes_dict = {node['id']: node for node in nodes}
        
        # Encontra o nó raiz (parent_id é None)
        root_node = None
        for node in nodes:
            if node.get('parent_id') is None:
                root_node = node
                break
        
        if not root_node:
            return None
        
        def build_node_json(node_id: str) -> Optional[Dict[str, Any]]:
            """Função recursiva para construir JSON de um nó e seus filhos"""
            node = nodes_dict.get(node_id)
            if not node:
                return None
            
            # Busca código NBR se existir
            nbr_code = None
            nbr_standard_id = node.get('nbr_standard_id')
            if nbr_standard_id is not None:
                # Converte para int se necessário
                nbr_standard_id_int = int(nbr_standard_id) if not isinstance(nbr_standard_id, int) else nbr_standard_id
                if nbr_standard_id_int in nbr_standards_map:
                    nbr_code = nbr_standards_map[nbr_standard_id_int]
            
            # Constrói objeto do nó
            node_json = {
                "id": str(node['id']),
                "label": node['label'],
                "type": node['type'],
                "status": node['status'],
                "nbr_code": nbr_code,
                "children": []
            }
            
            # Busca filhos (nós que têm este nó como pai)
            children = [n for n in nodes if n.get('parent_id') == node_id]
            
            # Recursivamente constrói filhos
            for child in children:
                child_json = build_node_json(child['id'])
                if child_json:
                    node_json["children"].append(child_json)
            
            return node_json
        
        # Constrói JSON a partir do nó raiz
        return build_node_json(root_node['id'])
        
    except Exception as e:
        st.error(f"Erro ao construir JSON da árvore: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None


def update_accident_status(accident_id: str, status: str) -> bool:
    """Atualiza status do acidente (normaliza para 'aberto'/'fechado')"""
    try:
        supabase = get_supabase_client()
        # Normaliza status: 'Open'/'Closed' -> 'aberto'/'fechado'
        normalized_status = "aberto" if status.lower() in ['open', 'aberto'] else "fechado"
        response = supabase.table("accidents").update({"status": normalized_status}).eq("id", accident_id).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Erro ao atualizar status: {str(e)}")
        return False
