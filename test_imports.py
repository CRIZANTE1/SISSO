#!/usr/bin/env python3
"""
Script de teste para verificar se todas as importações estão funcionando
"""
import sys
import traceback

def test_imports():
    """Testa todas as importações principais"""
    print("🔍 Testando importações...")
    
    try:
        print("1. Testando importação do Streamlit...")
        import streamlit as st
        print("✅ Streamlit importado com sucesso")
        
        print("2. Testando importação do Supabase config...")
        from managers.supabase_config import get_supabase_client, get_service_role_client
        print("✅ Supabase config importado com sucesso")
        
        print("3. Testando importação do auth utils...")
        from auth.auth_utils import require_login, show_user_info
        print("✅ Auth utils importado com sucesso")
        
        print("4. Testando importação dos componentes...")
        from components.filters import create_filter_sidebar
        print("✅ Components importado com sucesso")
        
        print("5. Testando importação dos serviços...")
        from services.kpi import fetch_kpi_data
        from services.uploads import upload_evidence
        print("✅ Services importado com sucesso")
        
        print("6. Testando importação das páginas...")
        from pages import pages
        print("✅ Pages importado com sucesso")
        
        print("\n🎉 Todas as importações foram bem-sucedidas!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro na importação: {str(e)}")
        print(f"Tipo do erro: {type(e).__name__}")
        print("\nTraceback completo:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
