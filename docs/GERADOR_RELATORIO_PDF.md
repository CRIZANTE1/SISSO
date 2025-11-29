# 📄 Gerador de Relatório PDF - Padrão Vibra

## Visão Geral

Sistema de geração de relatórios PDF no padrão visual da Vibra, utilizando HTML/CSS + WeasyPrint para alta fidelidade visual.

## 🎯 Características

- **Alta Fidelidade Visual**: CSS permite replicar cores exatas (#005f2f - Verde Vibra)
- **Layout Complexo**: Tabelas, cabeçalhos coloridos, quebras de página automáticas
- **Árvore de Falhas**: Geração automática da imagem usando Graphviz
- **Evidências**: Conversão automática de URLs para base64
- **Dados Dinâmicos**: Template Jinja2 lida com listas variáveis

## 📦 Dependências

### Python (requirements.txt)
```
jinja2>=3.1.0
weasyprint>=60.0
matplotlib>=3.7.0
requests>=2.31.0
graphviz>=0.20.0
```

### Sistema (packages.txt)
```
libpango-1.0-0
libpangoft2-1.0-0
libfontconfig1
libcairo2
libgdk-pixbuf2.0-0
libffi-dev
shared-mime-info
graphviz
libgraphviz-dev
```

## 🏗️ Estrutura

### Arquivo Principal
- `utils/report_generator.py`: Gerador de PDF com templates HTML/CSS

### Funções Principais

1. **`generate_fault_tree_image(tree_json)`**
   - Gera imagem PNG da árvore de falhas usando Graphviz
   - Converte para base64 para embutir no HTML
   - Cores: Verde (validated), Vermelho (discarded), Cinza (pending)

2. **`convert_image_url_to_base64(image_url)`**
   - Converte URLs de evidências para base64
   - Suporta PNG, JPEG
   - Timeout de 10 segundos

3. **`generate_pdf_report(...)`**
   - Função principal que gera o PDF
   - Recebe dados do acidente, pessoas, timeline, causas, evidências
   - Retorna bytes do PDF

## 📋 Estrutura do Relatório

### Página 1: Capa
- Título "RELATÓRIO FINAL"
- Informações do evento
- Local e data

### Página 2: Resumo Gerencial
- Data/Hora
- Local
- Descrição resumida
- Tipo e classificação
- Fotos principais (até 3)

### Página 3: Informações Detalhadas
- **1.1 Dados Gerais**: Número do registro, local, data, status
- **1.2 Classificação**: Tipo de impacto, gravidade
- **1.4 Perfil dos Envolvidos**: Loop para cada pessoa envolvida
- **1.5 Vazamentos/Segurança de Processo**: Se aplicável
- **1.6 Cronologia**: Timeline de eventos

### Página 4: Árvore de Falhas
- Imagem gerada pelo Graphviz
- Tabela de classificação NBR 14280
- Causas validadas com códigos

### Página 5: Comissão
- Tabela com membros da comissão
- Nome, cargo, matrícula, participação

### Página 6: Evidências Completas (Opcional)
- Todas as evidências (se houver mais de 3)

## 🎨 Estilos CSS

### Cores Vibra
- **Verde Principal**: `#005f2f`
- **Fundo Cinza**: `#f0f0f0`
- **Bordas**: `#ccc`

### Classes CSS
- `.vibra-green`: Cabeçalhos verdes
- `.section-title`: Títulos de seção
- `.form-table`: Tabelas estilo formulário
- `.tree-image`: Imagem da árvore
- `.evidence-img`: Imagens de evidência
- `.timeline-item`: Itens da cronologia

## 🔧 Uso no Streamlit

### Integração na Página de Investigação

```python
from utils.report_generator import generate_pdf_report

# No Step 4 (Classificação Oficial)
if st.button("📥 Gerar Relatório PDF Oficial"):
    with st.spinner("Gerando PDF..."):
        # Busca dados
        accident = get_accident(accident_id)
        people = get_involved_people(accident_id)
        timeline = get_timeline(accident_id)
        evidence = get_evidence(accident_id)
        tree_json = build_fault_tree_json(accident_id)
        
        # Prepara causas validadas
        validated_nodes = get_validated_nodes(accident_id)
        verified_causes = []
        # ... processa nós ...
        
        # Gera PDF
        pdf_bytes = generate_pdf_report(
            accident_data=accident,
            people_data=people,
            timeline_events=timeline,
            verified_causes=verified_causes,
            evidence_images=[e['image_url'] for e in evidence],
            fault_tree_json=tree_json
        )
        
        # Download
        st.download_button(
            label="⬇️ Baixar Relatório PDF",
            data=pdf_bytes,
            file_name=f"Relatorio_Vibra_{registry_num}.pdf",
            mime="application/pdf"
        )
```

## 📝 Formato do Nome do Arquivo

```
Relatorio_Vibra_{REGISTRO}_{DATA}.pdf
```

Exemplo:
```
Relatorio_Vibra_XX-2024_20240115.pdf
```

## ⚠️ Requisitos do Sistema

### Windows
- Instalar Graphviz: https://graphviz.org/download/
- Ou via Chocolatey: `choco install graphviz`

### Linux
```bash
sudo apt-get install graphviz libpango-1.0-0 libpangoft2-1.0-0 libfontconfig1 libcairo2
```

### macOS
```bash
brew install graphviz
```

## 🐛 Troubleshooting

### Erro: "WeasyPrint não encontrado"
```bash
pip install weasyprint
```

### Erro: "Graphviz não encontrado"
- Instalar Graphviz no sistema
- Verificar PATH do sistema

### Erro: "Imagens não aparecem no PDF"
- Verificar se URLs são acessíveis
- Verificar timeout (10 segundos)
- Converter para base64 manualmente se necessário

### Erro: "Fontes não renderizam corretamente"
- Instalar fontes do sistema
- WeasyPrint usa fontes do sistema

## 🎯 Vantagens desta Abordagem

1. **Fidelidade Visual**: CSS permite replicar exatamente o design
2. **Manutenção Fácil**: Alterar cores/estilos é simples (só CSS)
3. **Layout Complexo**: Tabelas e quebras de página automáticas
4. **Dados Dinâmicos**: Jinja2 lida com listas variáveis
5. **Árvore Gráfica**: Graphviz gera imagem automaticamente

## 📚 Referências

- [WeasyPrint Documentation](https://weasyprint.org/)
- [Jinja2 Templates](https://jinja.palletsprojects.com/)
- [Graphviz Documentation](https://graphviz.org/documentation/)

---

**Gerador de relatórios PDF implementado com sucesso!** ✅

