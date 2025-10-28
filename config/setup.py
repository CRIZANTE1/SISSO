#!/usr/bin/env python3
"""
Script de configuração inicial do Sistema SSO
"""
import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Verifica se a versão do Python é compatível"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ é necessário")
        sys.exit(1)
    print("✅ Versão do Python compatível")

def install_requirements():
    """Instala as dependências do requirements.txt"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependências instaladas com sucesso")
    except subprocess.CalledProcessError:
        print("❌ Erro ao instalar dependências")
        sys.exit(1)

def create_env_file():
    """Cria arquivo .env se não existir"""
    env_file = Path(".env")
    if not env_file.exists():
        env_content = """# Configurações do Supabase
SUPABASE_URL=your_supabase_url_here
SUPABASE_ANON_KEY=your_supabase_anon_key_here

# Configurações opcionais
# SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
"""
        env_file.write_text(env_content)
        print("✅ Arquivo .env criado")
        print("⚠️  Configure as variáveis SUPABASE_URL e SUPABASE_ANON_KEY no arquivo .env")
    else:
        print("✅ Arquivo .env já existe")

def create_directories():
    """Cria diretórios necessários"""
    directories = ["logs", "temp", "backups"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    print("✅ Diretórios criados")

def check_streamlit():
    """Verifica se o Streamlit está funcionando"""
    try:
        import streamlit
        print("✅ Streamlit disponível")
    except ImportError:
        print("❌ Streamlit não encontrado")
        return False
    return True

def main():
    """Função principal de setup"""
    print("🛡️  Configurando Sistema SSO - Monitoramento")
    print("=" * 50)
    
    # Verificações
    check_python_version()
    
    # Instalação
    install_requirements()
    
    # Configuração
    create_env_file()
    create_directories()
    
    # Verificação final
    if check_streamlit():
        print("\n✅ Setup concluído com sucesso!")
        print("\n📋 Próximos passos:")
        print("1. Configure as variáveis no arquivo .env")
        print("2. Execute o script database_setup.sql no Supabase")
        print("3. Configure o Storage no Supabase (bucket 'evidencias')")
        print("4. Execute: streamlit run app.py")
    else:
        print("\n❌ Setup incompleto. Verifique os erros acima.")

if __name__ == "__main__":
    main()
