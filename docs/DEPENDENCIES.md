# 📦 Dependências do Sistema SSO

## Visão Geral

Este documento descreve as dependências do Sistema de Monitoramento SSO, suas versões e propósitos.

## 📋 Arquivos de Requirements

### `requirements.txt` - Instalação Completa (Recomendada)
```bash
pip install -r requirements.txt
```
**Uso**: Instalação padrão com todas as funcionalidades.

### `requirements-minimal.txt` - Instalação Mínima
```bash
pip install -r requirements-minimal.txt
```
**Uso**: Ambientes com restrições de dependências ou instalação básica.

### `requirements-dev.txt` - Desenvolvimento
```bash
pip install -r requirements-dev.txt
```
**Uso**: Desenvolvedores que precisam de ferramentas de teste e qualidade de código.

## 🔧 Dependências Principais

### Core Framework
- **streamlit** `>=1.39.0,<2.0.0`
  - Framework web principal
  - Interface de usuário
  - Componentes interativos

### Data Processing
- **pandas** `>=2.2.0,<3.0.0`
  - Manipulação de dados
  - Análise estatística
  - Processamento de DataFrames

- **numpy** `>=1.24.0,<2.0.0`
  - Computação numérica
  - Operações matemáticas
  - Base para pandas e scipy

- **scipy** `>=1.11.0,<2.0.0`
  - Análise estatística avançada
  - Controles estatísticos
  - Funções científicas

### Visualization
- **plotly** `>=5.24.0,<6.0.0`
  - Gráficos interativos
  - Dashboards dinâmicos
  - Visualizações 3D

- **altair** `>=5.2.0,<6.0.0`
  - Gráficos declarativos
  - Visualizações estatísticas
  - Integração com Streamlit

### Database & API
- **supabase** `>=2.6.0,<3.0.0`
  - Cliente PostgreSQL
  - Autenticação
  - Storage de arquivos

### Environment & Configuration
- **python-dotenv** `>=1.0.0,<2.0.0`
  - Carregamento de variáveis de ambiente
  - Configuração de credenciais

### UI Components
- **streamlit-aggrid** `>=0.3.4,<1.0.0`
  - Tabelas avançadas
  - Edição inline
  - Filtros e ordenação

### Additional Dependencies
- **requests** `>=2.31.0,<3.0.0`
  - Requisições HTTP
  - Integração com APIs

- **urllib3** `>=2.0.0,<3.0.0`
  - Cliente HTTP de baixo nível
  - Dependência do requests

## 🛠️ Dependências de Desenvolvimento

### Testing
- **pytest** `>=7.4.0,<8.0.0` - Framework de testes
- **pytest-cov** `>=4.1.0,<5.0.0` - Cobertura de código
- **pytest-mock** `>=3.11.0,<4.0.0` - Mocks para testes

### Code Quality
- **black** `>=23.0.0,<24.0.0` - Formatação de código
- **flake8** `>=6.0.0,<7.0.0` - Linting
- **isort** `>=5.12.0,<6.0.0` - Ordenação de imports
- **mypy** `>=1.5.0,<2.0.0` - Verificação de tipos

### Documentation
- **mkdocs** `>=1.5.0,<2.0.0` - Geração de documentação
- **mkdocs-material** `>=9.4.0,<10.0.0` - Tema Material

### Development Tools
- **pre-commit** `>=3.4.0,<4.0.0` - Hooks de pré-commit
- **jupyter** `>=1.0.0,<2.0.0` - Notebooks
- **ipython** `>=8.15.0,<9.0.0` - Shell interativo

### Security
- **bandit** `>=1.7.0,<2.0.0` - Análise de segurança
- **safety** `>=2.3.0,<3.0.0` - Verificação de vulnerabilidades

## 🚀 Instalação Rápida

### Opção 1: Script Automático
```bash
python install.py
```

### Opção 2: Manual
```bash
# Instalação completa
pip install -r requirements.txt

# Ou instalação mínima
pip install -r requirements-minimal.txt

# Ou desenvolvimento
pip install -r requirements-dev.txt
```

## 🔍 Verificação da Instalação

```bash
# Verificar versões instaladas
python -c "import streamlit; print(f'Streamlit: {streamlit.__version__}')"
python -c "import pandas; print(f'Pandas: {pandas.__version__}')"
python -c "import plotly; print(f'Plotly: {plotly.__version__}')"
python -c "import supabase; print(f'Supabase: {supabase.__version__}')"
```

## ⚠️ Notas Importantes

### Compatibilidade
- **Python**: 3.8+ (recomendado 3.9+)
- **Sistema Operacional**: Windows, macOS, Linux
- **Navegador**: Chrome, Firefox, Safari, Edge (versões recentes)

### Resolução de Conflitos
Se houver conflitos de dependências:

1. **Use ambiente virtual**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou
   venv\Scripts\activate     # Windows
   ```

2. **Instale versões específicas**:
   ```bash
   pip install streamlit==1.39.0 pandas==2.2.2
   ```

3. **Use requirements-minimal.txt** para ambientes restritivos

### Atualizações
- **Atualizar todas**: `pip install --upgrade -r requirements.txt`
- **Atualizar específica**: `pip install --upgrade streamlit`
- **Verificar vulnerabilidades**: `safety check`

## 📊 Resumo de Tamanho

| Arquivo | Dependências | Tamanho Aprox. |
|---------|--------------|----------------|
| `requirements.txt` | 9 principais | ~200MB |
| `requirements-minimal.txt` | 5 essenciais | ~150MB |
| `requirements-dev.txt` | 9 + 12 dev | ~300MB |

## 🆘 Suporte

Se encontrar problemas com dependências:

1. Verifique a versão do Python
2. Use ambiente virtual
3. Consulte a documentação oficial de cada pacote
4. Abra uma issue no repositório do projeto
