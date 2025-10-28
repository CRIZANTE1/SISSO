# Este arquivo foi substituído pela nova arquitetura OIDC
# Use auth/auth_utils.py e auth/login_page.py

from auth.auth_utils import (
    require_login,
    show_user_info,
    get_current_user,
    get_user_id,
    get_user_info,
    get_user_role,
    is_admin,
    is_editor,
    can_edit,
    check_permission
)

# Mantém compatibilidade com código existente
def require_role(required_roles: list[str]):
    """Middleware que exige papel específico"""
    require_login()
    user = get_current_user()
    if user and user.get('role') not in required_roles:
        st.error("❌ Acesso negado. Papel insuficiente.")
        st.stop()
