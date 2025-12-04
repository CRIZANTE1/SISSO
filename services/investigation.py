"""
Serviço para operações de investigação de acidentes
Adaptado para arquitetura multi-acidente com session_state
"""
import io
import time
import tempfile
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from managers.supabase_config import get_supabase_client
from auth.auth_utils import get_user_id, get_user_email
import streamlit as st


def get_sites() -> List[Dict[str, Any]]:
    """Busca todos os sites ativos da tabela sites (com bypass RLS)"""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            return []
        
        # Busca sites ativos, ordenados por nome
        response = supabase.table("sites").select("id, code, name, type, is_active").eq("is_active", True).order("name").execute()
        
        if response and hasattr(response, 'data'):
            return response.data if response.data else []
        return []
    except Exception as e:
        st.error(f"Erro ao buscar sites: {str(e)}")
        return []


def create_accident(title: str, description: str = "", occurrence_date: Optional[datetime] = None, 
                   **kwargs) -> Optional[str]:
    """Cria uma nova investigação de acidente com campos expandidos do relatório Vibra"""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            st.error("Erro ao conectar com o banco de dados")
            return None
        
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
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from managers.supabase_config import get_service_role_client
        from auth.auth_utils import get_user_id, is_admin
        
        logger.info(f"[UPDATE_ACCIDENT] Iniciando atualização do acidente {accident_id}")
        logger.info(f"[UPDATE_ACCIDENT] Campos recebidos: {list(kwargs.keys())}")
        
        # Usa service_role para contornar RLS
        supabase = get_service_role_client()
        if not supabase:
            logger.error("[UPDATE_ACCIDENT] Erro ao conectar com o banco de dados - Service Role não disponível")
            return False
        
        logger.info("[UPDATE_ACCIDENT] Cliente Service Role obtido com sucesso (RLS bypass ativo)")
        
        # Validação de segurança: verifica se usuário tem acesso
        user_id = get_user_id()
        is_admin_user = is_admin()
        
        if not is_admin_user and user_id:
            # Verifica se o acidente pertence ao usuário
            check_response = supabase.table("accidents").select("created_by").eq("id", accident_id).execute()
            if check_response.data and len(check_response.data) > 0:
                if check_response.data[0].get('created_by') != user_id:
                    logger.warning(f"[UPDATE_ACCIDENT] Usuário {user_id} não tem permissão para atualizar acidente {accident_id}")
                    return False
        
        # Mantém todos os campos válidos (incluindo None para limpar campos)
        valid_columns = [
            'title', 'description', 'occurrence_date', 'registry_number', 'base_location', 'site_id',
            'class_injury', 'class_community', 'class_environment', 'class_process_safety',
            'class_asset_damage', 'class_near_miss', 'severity_level', 'estimated_loss_value',
            'product_released', 'volume_released', 'volume_recovered', 'release_duration_hours',
            'equipment_involved', 'area_affected', 'status'
        ]
        
        # Filtra apenas campos válidos, mantém todos (incluindo None)
        filtered_data = {k: v for k, v in kwargs.items() if k in valid_columns}
        
        logger.info(f"[UPDATE_ACCIDENT] Campos filtrados: {list(filtered_data.keys())}")
        logger.info(f"[UPDATE_ACCIDENT] Valores: {filtered_data}")
        
        if not filtered_data:
            logger.warning("[UPDATE_ACCIDENT] Nenhum campo válido para atualizar")
            return True  # Nada para atualizar
        
        # Envia todos os campos válidos
        # Remove apenas campos None para campos obrigatórios, mantém None para nullable
        final_data = {}
        for k, v in filtered_data.items():
            # Campos obrigatórios que não podem ser None
            required_fields = ['title']
            if k in required_fields and v is None:
                continue  # Pula campos obrigatórios None
            final_data[k] = v
        
        logger.info(f"[UPDATE_ACCIDENT] Payload final: {list(final_data.keys())}")
        logger.info(f"[UPDATE_ACCIDENT] Valores: {final_data}")
        
        if not final_data:
            logger.warning("[UPDATE_ACCIDENT] Nenhum campo para atualizar após filtro")
            return True
        
        # Executa atualização
        try:
            response = supabase.table("accidents").update(final_data).eq("id", accident_id).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"[UPDATE_ACCIDENT] Acidente {accident_id} atualizado com sucesso. Registros afetados: {len(response.data)}")
                return True
            else:
                logger.error(f"[UPDATE_ACCIDENT] Nenhum dado foi atualizado para acidente {accident_id}")
                logger.error(f"[UPDATE_ACCIDENT] Response: {response}")
                return False
        except Exception as update_error:
            logger.error(f"[UPDATE_ACCIDENT] Erro na execução do update: {str(update_error)}")
            logger.error(f"[UPDATE_ACCIDENT] Tipo de erro: {type(update_error).__name__}")
            # Verifica se é erro de RLS
            error_str = str(update_error).lower()
            if 'permission' in error_str or 'policy' in error_str or 'rls' in error_str:
                logger.error("[UPDATE_ACCIDENT] Possível problema de RLS detectado")
            raise update_error
    except Exception as e:
        logger.error(f"[UPDATE_ACCIDENT] Erro ao atualizar investigação: {str(e)}", exc_info=True)
        return False


def get_involved_people(accident_id: str, person_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Busca pessoas envolvidas em uma investigação"""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            return []
        
        query = supabase.table("involved_people").select("*").eq("accident_id", accident_id)
        
        if person_type:
            query = query.eq("person_type", person_type)
        
        response = query.order("created_at", desc=False).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Erro ao buscar pessoas envolvidas: {str(e)}")
        return []


def upsert_involved_people(accident_id: str, people: List[Dict[str, Any]]) -> bool:
    """Insere ou atualiza pessoas envolvidas (remove existentes e insere novas) usando batch insert"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            logger.error("[UPSERT_PEOPLE] Erro ao conectar com o banco de dados - Service Role não disponível")
            return False
        
        logger.info("[UPSERT_PEOPLE] Cliente Service Role obtido com sucesso (RLS bypass ativo)")
        
        # O campo created_by aponta para auth.users.id, não profiles.id
        # Como o campo é nullable e pode causar problemas de FK, não vamos passá-lo
        # Isso evita erros quando o ID de profiles não corresponde ao ID de auth.users
        logger.info(f"[UPSERT_PEOPLE] Salvando {len(people)} pessoas para acidente {accident_id}")
        logger.info("[UPSERT_PEOPLE] Campo created_by não será passado (nullable) para evitar problemas de FK com auth.users")
        
        # Remove pessoas existentes do mesmo accident_id
        delete_response = supabase.table("involved_people").delete().eq("accident_id", accident_id).execute()
        logger.info(f"[UPSERT_PEOPLE] Removidas pessoas existentes: {delete_response}")
        
        # Prepara dados para inserção em lote
        if people:
            batch_data = []
            for person in people:
                # Valida campos obrigatórios
                person_type = person.get('person_type')
                name = person.get('name')
                
                if not person_type or not name:
                    logger.warning(f"[UPSERT_PEOPLE] Pessoa ignorada: person_type={person_type}, name={name}")
                    continue
                
                person_data = {
                    'accident_id': accident_id,
                    'person_type': person_type,
                    'name': name,
                    'registration_id': person.get('registration_id'),
                    'job_title': person.get('job_title'),
                    'company': person.get('company'),
                    'age': person.get('age'),
                    'time_in_role': person.get('time_in_role'),
                    'aso_date': person.get('aso_date'),
                    'training_status': person.get('training_status'),
                    'commission_role': person.get('commission_role'),  # Função na comissão de investigação
                    # created_by não é passado (será NULL no banco) para evitar erro de FK com auth.users
                }
                # Remove campos None para não enviar dados desnecessários
                person_data = {k: v for k, v in person_data.items() if v is not None}
                batch_data.append(person_data)
            
            if not batch_data:
                logger.warning("[UPSERT_PEOPLE] Nenhum dado válido após validação")
                return False
            
            logger.info(f"[UPSERT_PEOPLE] Dados preparados: {len(batch_data)} registros")
            logger.info(f"[UPSERT_PEOPLE] Tipos de pessoas: {[p.get('person_type') for p in batch_data]}")
            
            # Insere em lote (batch insert)
            try:
                logger.info(f"[UPSERT_PEOPLE] Tentando inserir {len(batch_data)} registros")
                logger.info(f"[UPSERT_PEOPLE] Primeiro registro (exemplo): {batch_data[0] if batch_data else 'N/A'}")
                
                response = supabase.table("involved_people").insert(batch_data).execute()
                
                if response.data:
                    logger.info(f"[UPSERT_PEOPLE] {len(response.data)} pessoas salvas com sucesso")
                    logger.info(f"[UPSERT_PEOPLE] Dados salvos: {[p.get('person_type') + ' - ' + p.get('name', 'N/A') for p in response.data]}")
                    return True
                else:
                    logger.error(f"[UPSERT_PEOPLE] Nenhum dado foi inserido. Response: {response}")
                    logger.error(f"[UPSERT_PEOPLE] Response completo: {response}")
                    return False
            except Exception as insert_error:
                error_msg = str(insert_error)
                logger.error(f"[UPSERT_PEOPLE] Erro na execução do insert: {error_msg}")
                logger.error(f"[UPSERT_PEOPLE] Tipo de erro: {type(insert_error).__name__}")
                
                # Log detalhado do erro
                if hasattr(insert_error, 'message'):
                    logger.error(f"[UPSERT_PEOPLE] Mensagem do erro: {insert_error.message}")
                if hasattr(insert_error, 'code'):
                    logger.error(f"[UPSERT_PEOPLE] Código do erro: {insert_error.code}")
                if hasattr(insert_error, 'details'):
                    logger.error(f"[UPSERT_PEOPLE] Detalhes do erro: {insert_error.details}")
                
                # Verifica se é erro de RLS
                error_str = error_msg.lower()
                if 'permission' in error_str or 'policy' in error_str or 'rls' in error_str:
                    logger.error("[UPSERT_PEOPLE] Possível problema de RLS detectado")
                elif 'foreign key' in error_str or 'constraint' in error_str:
                    logger.error("[UPSERT_PEOPLE] Erro de foreign key constraint detectado")
                elif 'null value' in error_str or 'not null' in error_str:
                    logger.error("[UPSERT_PEOPLE] Erro de campo obrigatório (NOT NULL) detectado")
                
                # Não faz raise, retorna False para que a UI mostre o erro
                return False
        
        logger.info("[UPSERT_PEOPLE] Nenhuma pessoa para salvar")
        return True
    except Exception as e:
        logger.error(f"[UPSERT_PEOPLE] Erro ao salvar pessoas envolvidas: {str(e)}", exc_info=True)
        return False


def get_accidents() -> List[Dict[str, Any]]:
    """Busca todos os acidentes da tabela accidents para investigação"""
    try:
        from auth.auth_utils import get_user_id, is_admin
        from managers.supabase_config import get_service_role_client
        
        user_id = get_user_id()
        is_admin_user = is_admin()
        
        # Usa service_role para contornar RLS e garantir acesso
        # Admin vê todos, usuário comum vê apenas os seus
        supabase = get_service_role_client()
        
        if not supabase:
            st.error("Erro ao conectar com o banco de dados")
            return []
        
        # Busca acidentes (filtra por usuário se não for admin)
        query = supabase.table("accidents").select("id, title, description, occurrence_date, occurred_at, status, created_at, type, classification, created_by")
        
        # Aplica filtro de segurança no código (não confia apenas em RLS)
        if not is_admin_user and user_id:
            query = query.eq("created_by", user_id)
        
        response = query.order("created_at", desc=True).execute()
        
        if response.data:
            # Validação adicional de segurança para usuários não-admin
            if not is_admin_user and user_id:
                # Filtra novamente para garantir (segurança em camadas)
                response.data = [acc for acc in response.data if acc.get('created_by') == user_id]
            # Normaliza os dados: usa title se existir, senão usa description
            # usa occurrence_date se existir, senão usa occurred_at
            normalized_data = []
            for acc in response.data:
                # Garante que title nunca seja None
                title = acc.get("title")
                description = acc.get("description", "")
                
                if not title or title.strip() == "":
                    # Se não tem title, usa description (limitado a 50 chars)
                    if description:
                        title = description[:50] + ("..." if len(description) > 50 else "")
                    else:
                        title = "Acidente sem título"
                
                normalized = {
                    "id": acc.get("id"),
                    "title": title,
                    "description": description,
                    "occurrence_date": acc.get("occurrence_date") or acc.get("occurred_at"),
                    "status": acc.get("status", "aberto"),
                    "created_at": acc.get("created_at"),
                    "type": acc.get("type"),
                    "classification": acc.get("classification"),
                    "created_by": acc.get("created_by")
                }
                normalized_data.append(normalized)
            
            return normalized_data
        return []
    except Exception as e:
        st.error(f"Erro ao buscar acidentes: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return []


def get_accident(accident_id: str) -> Optional[Dict[str, Any]]:
    """Busca um acidente específico da tabela accidents por ID (UUID)"""
    try:
        from managers.supabase_config import get_service_role_client
        from auth.auth_utils import get_user_id, is_admin
        
        if not accident_id:
            return None
        
        # Garante que accident_id é uma string válida (UUID)
        accident_id = str(accident_id).strip()
        if not accident_id or len(accident_id) < 10:  # UUID mínimo tem 36 caracteres, mas vamos ser flexíveis
            st.warning(f"ID de acidente inválido: {accident_id}")
            return None
        
        # Usa service_role para contornar RLS
        supabase = get_service_role_client()
        if not supabase:
            st.error("Erro ao conectar com o banco de dados")
            return None
        
        # Busca EXCLUSIVAMENTE por ID (nunca por nome/título) com JOIN na tabela sites
        # Nota: Supabase usa sintaxe especial para foreign keys
        try:
            response = supabase.table("accidents").select("*, sites!accidents_site_id_fkey(name, code)").eq("id", accident_id).execute()
        except:
            # Fallback: busca sem JOIN e depois busca site separadamente
            response = supabase.table("accidents").select("*").eq("id", accident_id).execute()
            if response.data and len(response.data) > 0:
                acc = response.data[0]
                site_id = acc.get('site_id')
                if site_id:
                    site_response = supabase.table("sites").select("name, code").eq("id", site_id).execute()
                    if site_response.data and len(site_response.data) > 0:
                        acc['sites'] = site_response.data[0]
                response.data[0] = acc
        
        # Validação de segurança: verifica se usuário tem acesso
        if response.data and len(response.data) > 0:
            acc = response.data[0]
            user_id = get_user_id()
            is_admin_user = is_admin()
            
            # Se não for admin, verifica se o acidente pertence ao usuário
            if not is_admin_user and user_id:
                if acc.get('created_by') != user_id:
                    st.warning("Você não tem permissão para acessar este acidente")
                    return None
            
            # Extrai informações do site (se houver)
            site_info = acc.get('sites')
            site_name = None
            if site_info:
                if isinstance(site_info, dict):
                    site_name = site_info.get('name')
                elif isinstance(site_info, list) and len(site_info) > 0:
                    site_name = site_info[0].get('name')
            
            # Normaliza os dados para compatibilidade
            normalized = {
                "id": acc.get("id"),
                "title": acc.get("title") or acc.get("description", "Acidente sem título"),
                "description": acc.get("description", ""),
                "site_id": acc.get("site_id"),
                "site_name": site_name,
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
        import traceback
        st.code(traceback.format_exc())
        return None
        
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
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            st.error("Erro ao conectar com o banco de dados")
            return None
        
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
        
        # Cria arquivo temporário para upload (Supabase Storage requer caminho de arquivo)
        temp_file_path = None
        result = None
        try:
            # Cria arquivo temporário
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
                temp_file.write(file_bytes)
                temp_file_path = temp_file.name
            
            # Faz upload usando o caminho do arquivo temporário
            result = supabase.storage.from_(bucket).upload(
                path, 
                temp_file_path, 
                file_options={"content-type": f"image/{file_extension}", "upsert": "true"}
            )
        except Exception as upload_error:
            st.error(f"Erro no upload do arquivo: {str(upload_error)}")
            result = None
        finally:
            # Remove arquivo temporário após upload
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass  # Ignora erros ao remover arquivo temporário
        
        if result:
            # Obtém URL pública
            try:
                # Tenta obter URL pública do Supabase
                public_url_response = supabase.storage.from_(bucket).get_public_url(path)
                if public_url_response:
                    public_url = public_url_response
                else:
                    raise Exception("URL pública não retornada")
            except Exception as url_error:
                # Se não conseguir URL pública, constrói manualmente
                try:
                    # Tenta obter URL do Supabase de várias fontes
                    url = None
                    
                    # 1. Tenta variável de ambiente
                    url = os.environ.get("SUPABASE_URL")
                    
                    # 2. Tenta secrets do Streamlit
                    if not url:
                        try:
                            url = st.secrets.get("supabase", {}).get("url", "")
                        except:
                            pass
                    
                    # 3. Tenta obter do cliente Supabase (se tiver atributo)
                    if not url:
                        try:
                            if hasattr(supabase, 'supabase_url'):
                                url = supabase.supabase_url
                            elif hasattr(supabase, 'url'):
                                url = supabase.url
                        except:
                            pass
                    
                    if url:
                        # Remove barra final se houver
                        url = url.rstrip('/')
                        public_url = f"{url}/storage/v1/object/public/{bucket}/{path}"
                    else:
                        st.error("Não foi possível obter URL do Supabase para gerar URL pública da imagem")
                        return None
                except Exception as e:
                    st.error(f"Erro ao construir URL pública: {str(e)}")
                    return None
            
            # Registra no banco de dados
            # Nota: uploaded_by referencia auth.users.id, mas get_user_id() retorna profiles.id
            # Como o campo é nullable, deixamos como NULL para evitar erro de foreign key
            evidence_data = {
                "accident_id": accident_id,
                "image_url": public_url,
                "description": description,
                "uploaded_by": None  # Campo nullable - evita erro de FK (evidence.uploaded_by -> auth.users.id)
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
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            return []
        
        response = supabase.table("evidence").select("*").eq("accident_id", accident_id).order("uploaded_at", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Erro ao buscar evidências: {str(e)}")
        return []


def add_timeline_event(accident_id: str, event_time: datetime, description: str) -> bool:
    """Adiciona evento à timeline"""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            st.error("Erro ao conectar com o banco de dados")
            return False
        
        # Nota: created_by referencia auth.users.id, mas get_user_id() retorna profiles.id
        # Como o campo é nullable, deixamos como NULL para evitar erro de foreign key
        # Conforme documentado no schema: "O campo created_by é deixado como NULL para evitar erros de FK"
        data = {
            "accident_id": accident_id,
            "event_time": event_time.isoformat(),
            "description": description,
            "created_by": None  # Campo nullable - evita erro de FK (timeline.created_by -> auth.users.id)
        }
        
        response = supabase.table("timeline").insert(data).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Erro ao adicionar evento: {str(e)}")
        return False


def get_timeline(accident_id: str) -> List[Dict[str, Any]]:
    """Busca timeline de uma investigação"""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            return []
        
        response = supabase.table("timeline").select("*").eq("accident_id", accident_id).order("event_time", desc=False).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Erro ao buscar timeline: {str(e)}")
        return []


def update_timeline_event(event_id: str, event_time: datetime, description: str) -> bool:
    """Atualiza um evento da timeline"""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            st.error("Erro ao conectar com o banco de dados")
            return False
        
        data = {
            "event_time": event_time.isoformat(),
            "description": description
        }
        
        response = supabase.table("timeline").update(data).eq("id", event_id).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Erro ao atualizar evento: {str(e)}")
        return False


def delete_timeline_event(event_id: str) -> bool:
    """Remove um evento da timeline"""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            st.error("Erro ao conectar com o banco de dados")
            return False
        
        response = supabase.table("timeline").delete().eq("id", event_id).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Erro ao remover evento: {str(e)}")
        return False


def get_root_node(accident_id: str) -> Optional[Dict[str, Any]]:
    """Busca o nó raiz de uma investigação"""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            return None
        
        response = supabase.table("fault_tree_nodes").select("*").eq("accident_id", accident_id).eq("type", "root").limit(1).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Erro ao buscar nó raiz: {str(e)}")
        return None


def create_root_node(accident_id: str, label: str) -> Optional[str]:
    """Cria nó raiz para uma investigação"""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            st.error("Erro ao conectar com o banco de dados")
            return None
        
        # Nota: created_by referencia auth.users.id, mas get_user_id() retorna profiles.id
        # Como o campo é nullable, deixamos como NULL para evitar erro de foreign key
        data = {
            "accident_id": accident_id,
            "label": label,
            "type": "root",
            "status": "pending",
            "created_by": None  # Campo nullable - evita erro de FK (fault_tree_nodes.created_by -> auth.users.id)
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
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            st.error("Erro ao conectar com o banco de dados")
            return None
        
        # Calcula display_order: próximo número disponível para o mesmo parent_id
        max_order = 0
        if parent_id:
            existing_nodes = supabase.table("fault_tree_nodes").select("display_order").eq("accident_id", accident_id).eq("parent_id", parent_id).execute()
            if existing_nodes.data:
                max_order = max([n.get('display_order', 0) or 0 for n in existing_nodes.data], default=0)
        else:
            # Para nós raiz
            existing_nodes = supabase.table("fault_tree_nodes").select("display_order").eq("accident_id", accident_id).is_("parent_id", "null").execute()
            if existing_nodes.data:
                max_order = max([n.get('display_order', 0) or 0 for n in existing_nodes.data], default=0)
        
        # Nota: created_by referencia auth.users.id, mas get_user_id() retorna profiles.id
        # Como o campo é nullable, deixamos como NULL para evitar erro de foreign key
        data = {
            "accident_id": accident_id,
            "label": label,
            "type": node_type,
            "status": "pending",
            "display_order": max_order + 1,
            "created_by": None  # Campo nullable - evita erro de FK (fault_tree_nodes.created_by -> auth.users.id)
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
    """Busca todos os nós da árvore de falhas de uma investigação, ordenados por display_order"""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            return []
        
        response = supabase.table("fault_tree_nodes").select("*").eq("accident_id", accident_id).order("display_order", desc=False).order("created_at", desc=False).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Erro ao buscar nós: {str(e)}")
        return []


def reorganize_nodes(accident_id: str, sort_by: str = "status") -> bool:
    """
    Reorganiza nós da árvore de falhas de forma inteligente
    
    Args:
        accident_id: ID do acidente
        sort_by: Critério de ordenação:
            - "status": Por status (validated primeiro, depois pending, depois discarded)
            - "type": Por tipo (root, fact, hypothesis)
            - "alphabetical": Alfabético por label
            - "chronological": Por data de criação
            - "priority": Validated primeiro, depois por tipo
    """
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            st.error("Erro ao conectar com o banco de dados")
            return False
        
        # Busca todos os nós do acidente
        nodes = supabase.table("fault_tree_nodes").select("*").eq("accident_id", accident_id).execute()
        if not nodes.data:
            return True
        
        # Agrupa nós por parent_id para reorganizar cada nível separadamente
        nodes_by_parent = {}
        for node in nodes.data:
            parent_key = str(node.get('parent_id') or 'root')
            if parent_key not in nodes_by_parent:
                nodes_by_parent[parent_key] = []
            nodes_by_parent[parent_key].append(node)
        
        # Define função de ordenação baseada no critério
        status_order = {'validated': 1, 'pending': 2, 'discarded': 3}
        type_order = {'root': 1, 'fact': 2, 'hypothesis': 3}
        
        def get_sort_key(node):
            if sort_by == "status":
                return (status_order.get(node.get('status', 'pending'), 99), node.get('label', '').lower())
            elif sort_by == "type":
                return (type_order.get(node.get('type', 'hypothesis'), 99), node.get('label', '').lower())
            elif sort_by == "alphabetical":
                return node.get('label', '').lower()
            elif sort_by == "chronological":
                return node.get('created_at', '')
            elif sort_by == "priority":
                return (
                    status_order.get(node.get('status', 'pending'), 99),
                    type_order.get(node.get('type', 'hypothesis'), 99),
                    node.get('label', '').lower()
                )
            else:
                return node.get('display_order', 0) or 0
        
        # Reorganiza cada grupo de nós com o mesmo parent_id
        updates = []
        for parent_key, group_nodes in nodes_by_parent.items():
            # Ordena o grupo
            sorted_nodes = sorted(group_nodes, key=get_sort_key)
            
            # Atribui novos display_order
            for idx, node in enumerate(sorted_nodes, start=1):
                updates.append({
                    'id': node['id'],
                    'display_order': idx
                })
        
        # Atualiza em lote
        for update in updates:
            supabase.table("fault_tree_nodes").update({"display_order": update['display_order']}).eq("id", update['id']).execute()
        
        return True
    except Exception as e:
        st.error(f"Erro ao reorganizar nós: {str(e)}")
        return False


def update_node_display_order(node_id: str, new_order: int) -> bool:
    """Atualiza a ordem de exibição de um nó específico"""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            st.error("Erro ao conectar com o banco de dados")
            return False
        
        response = supabase.table("fault_tree_nodes").update({"display_order": new_order}).eq("id", node_id).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Erro ao atualizar ordem: {str(e)}")
        return False


def update_node_status(node_id: str, status: str, justification: Optional[str] = None, justification_image_url: Optional[str] = None) -> bool:
    """Atualiza status de validação de um nó, opcionalmente com justificativa e imagem"""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            st.error("Erro ao conectar com o banco de dados")
            return False
        
        update_data = {"status": status}
        if justification is not None:
            update_data["justification"] = justification
        if justification_image_url is not None:
            update_data["justification_image_url"] = justification_image_url
        
        response = supabase.table("fault_tree_nodes").update(update_data).eq("id", node_id).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Erro ao atualizar status: {str(e)}")
        return False


def upload_justification_image(node_id: str, accident_id: str, file_bytes: bytes, filename: str) -> Optional[str]:
    """Upload de imagem de justificativa para Supabase Storage"""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            st.error("Erro ao conectar com o banco de dados")
            return None
        
        bucket = "evidencias"
        
        # Gera path único
        timestamp = int(time.time())
        file_extension = filename.split('.')[-1] if '.' in filename else ''
        safe_filename = f"{timestamp}_{filename}"
        path = f"investigations/{accident_id}/justifications/{node_id}/{safe_filename}"
        
        # Upload do arquivo (substitui se já existir)
        try:
            supabase.storage.from_(bucket).remove([path])
        except:
            pass
        
        # Cria arquivo temporário para upload
        temp_file_path = None
        result = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
                temp_file.write(file_bytes)
                temp_file_path = temp_file.name
            
            # Faz upload usando o caminho do arquivo temporário
            result = supabase.storage.from_(bucket).upload(
                path, 
                temp_file_path, 
                file_options={"content-type": f"image/{file_extension}", "upsert": "true"}
            )
        except Exception as upload_error:
            st.error(f"Erro no upload do arquivo: {str(upload_error)}")
            result = None
        finally:
            # Remove arquivo temporário após upload
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass
        
        if result:
            # Obtém URL pública
            try:
                public_url_response = supabase.storage.from_(bucket).get_public_url(path)
                if public_url_response:
                    public_url = public_url_response
                else:
                    raise Exception("URL pública não retornada")
            except Exception as url_error:
                # Se não conseguir URL pública, constrói manualmente
                try:
                    url = None
                    url = os.environ.get("SUPABASE_URL")
                    
                    if not url:
                        try:
                            url = st.secrets.get("supabase", {}).get("url", "")
                        except:
                            pass
                    
                    if not url:
                        try:
                            if hasattr(supabase, 'supabase_url'):
                                url = supabase.supabase_url
                            elif hasattr(supabase, 'url'):
                                url = supabase.url
                        except:
                            pass
                    
                    if url:
                        url = url.rstrip('/')
                        public_url = f"{url}/storage/v1/object/public/{bucket}/{path}"
                    else:
                        st.error("Não foi possível obter URL do Supabase para gerar URL pública da imagem")
                        return None
                except Exception as e:
                    st.error(f"Erro ao construir URL pública: {str(e)}")
                    return None
            
            # Atualiza o nó com a URL da imagem
            update_response = supabase.table("fault_tree_nodes").update({"justification_image_url": public_url}).eq("id", node_id).execute()
            
            if update_response.data:
                return public_url
            else:
                st.error("Erro ao atualizar nó com URL da imagem")
                return None
        else:
            st.error("Erro no upload do arquivo")
            return None
            
    except Exception as e:
        st.error(f"Erro no upload: {str(e)}")
        return None


def update_node_justification_image(node_id: str, image_url: Optional[str]) -> bool:
    """Atualiza a URL da imagem de justificativa de um nó"""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            st.error("Erro ao conectar com o banco de dados")
            return False
        
        response = supabase.table("fault_tree_nodes").update({"justification_image_url": image_url}).eq("id", node_id).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Erro ao atualizar imagem de justificativa: {str(e)}")
        return False


def update_node_recommendation(node_id: str, recommendation: Optional[str]) -> bool:
    """Atualiza a recomendação de um nó (causa básica ou contribuinte)"""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            st.error("Erro ao conectar com o banco de dados")
            return False
        
        response = supabase.table("fault_tree_nodes").update({"recommendation": recommendation}).eq("id", node_id).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Erro ao atualizar recomendação: {str(e)}")
        return False


def update_node_label(node_id: str, label: str) -> bool:
    """Atualiza o label (texto) de um nó da árvore de falhas"""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            st.error("Erro ao conectar com o banco de dados")
            return False
        
        response = supabase.table("fault_tree_nodes").update({"label": label}).eq("id", node_id).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Erro ao atualizar label: {str(e)}")
        return False


def update_node_is_basic_cause(node_id: str, is_basic_cause: bool) -> bool:
    """Atualiza o campo is_basic_cause de um nó da árvore de falhas"""
    try:
        import logging
        logger = logging.getLogger(__name__)
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            logger.error("[UPDATE_BASIC_CAUSE] Erro ao conectar com o banco de dados")
            return False
        
        response = supabase.table("fault_tree_nodes").update({"is_basic_cause": is_basic_cause}).eq("id", node_id).execute()
        if response.data:
            logger.info(f"[UPDATE_BASIC_CAUSE] Nó {node_id} atualizado: is_basic_cause={is_basic_cause}")
            return True
        else:
            logger.warning(f"[UPDATE_BASIC_CAUSE] Nenhum dado retornado ao atualizar nó {node_id}")
            return False
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"[UPDATE_BASIC_CAUSE] Erro ao atualizar is_basic_cause: {str(e)}", exc_info=True)
        return False


def update_node_is_contributing_cause(node_id: str, is_contributing_cause: bool) -> bool:
    """Atualiza o campo is_contributing_cause de um nó da árvore de falhas"""
    try:
        import logging
        logger = logging.getLogger(__name__)
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            logger.error("[UPDATE_CONTRIBUTING_CAUSE] Erro ao conectar com o banco de dados")
            return False
        
        response = supabase.table("fault_tree_nodes").update({"is_contributing_cause": is_contributing_cause}).eq("id", node_id).execute()
        if response.data:
            logger.info(f"[UPDATE_CONTRIBUTING_CAUSE] Nó {node_id} atualizado: is_contributing_cause={is_contributing_cause}")
            return True
        else:
            logger.warning(f"[UPDATE_CONTRIBUTING_CAUSE] Nenhum dado retornado ao atualizar nó {node_id}")
            return False
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"[UPDATE_CONTRIBUTING_CAUSE] Erro ao atualizar is_contributing_cause: {str(e)}", exc_info=True)
        return False


def link_nbr_standard_to_node(node_id: str, nbr_standard_id: int) -> bool:
    """Vincula um padrão NBR a um nó validado"""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            st.error("Erro ao conectar com o banco de dados")
            return False
        
        response = supabase.table("fault_tree_nodes").update({"nbr_standard_id": nbr_standard_id}).eq("id", node_id).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Erro ao vincular padrão NBR: {str(e)}")
        return False


def get_nbr_standards(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Busca padrões NBR, opcionalmente filtrados por categoria"""
    try:
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            return []
        
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
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            return []
        
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
        
        # Busca padrões NBR para incluir códigos e descrições
        nbr_standards_map = {}
        try:
            from managers.supabase_config import get_service_role_client
            supabase = get_service_role_client()
            if supabase:
                # Busca todos os padrões NBR com código e descrição
                nbr_response = supabase.table("nbr_standards").select("id, code, description").execute()
                if nbr_response.data:
                    # Cria mapa: nbr_standard_id (int) -> {code, description}
                    nbr_standards_map = {
                        int(std['id']): {
                            'code': std['code'],
                            'description': std.get('description', '')
                        } for std in nbr_response.data
                    }
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
            
            # Busca código NBR e descrição se existir
            nbr_code = None
            nbr_description = None
            nbr_standard_id = node.get('nbr_standard_id')
            if nbr_standard_id is not None:
                # Converte para int se necessário
                nbr_standard_id_int = int(nbr_standard_id) if not isinstance(nbr_standard_id, int) else nbr_standard_id
                if nbr_standard_id_int in nbr_standards_map:
                    nbr_info = nbr_standards_map[nbr_standard_id_int]
                    nbr_code = nbr_info.get('code')
                    nbr_description = nbr_info.get('description')
            
            # Constrói objeto do nó
            node_json = {
                "id": str(node['id']),
                "label": node['label'],
                "type": node['type'],
                "status": node['status'],
                "is_basic_cause": node.get('is_basic_cause', False),  # Campo para marcar manualmente como causa básica
                "is_contributing_cause": node.get('is_contributing_cause', False),  # Campo para marcar manualmente como causa contribuinte
                "nbr_code": nbr_code,
                "nbr_description": nbr_description,
                "justification": node.get('justification', ''),  # Justificativa para confirmação/descarte
                "justification_image_url": node.get('justification_image_url'),  # URL da imagem da justificativa
                "recommendation": node.get('recommendation'),  # Recomendação para prevenir/corrigir a causa
                "children": []
            }
            
            # Busca filhos (nós que têm este nó como pai) e ordena por display_order
            children = [n for n in nodes if n.get('parent_id') == node_id]
            # Ordena filhos por display_order, depois por created_at
            children.sort(key=lambda x: (
                x.get('display_order', 0) or 0,
                x.get('created_at', '') or ''
            ))
            
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
        from managers.supabase_config import get_service_role_client
        supabase = get_service_role_client()
        if not supabase:
            st.error("Erro ao conectar com o banco de dados")
            return False
        
        # Normaliza status: 'Open'/'Closed' -> 'aberto'/'fechado'
        normalized_status = "aberto" if status.lower() in ['open', 'aberto'] else "fechado"
        response = supabase.table("accidents").update({"status": normalized_status}).eq("id", accident_id).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Erro ao atualizar status: {str(e)}")
        return False
