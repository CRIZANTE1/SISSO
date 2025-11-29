# 🔍 Módulo de Investigação de Acidentes

## Visão Geral

Módulo completo de investigação de acidentes baseado em **Fault Tree Analysis (FTA)** e **NBR 14280**, implementado no sistema SSO.

## 📋 Estrutura do Banco de Dados

### Tabelas Criadas

1. **nbr_standards**: Armazena códigos e descrições dos padrões NBR 14280
   - Categorias: `unsafe_act`, `unsafe_condition`, `personal_factor`, `accident_type`
   - Populada com 40 registros iniciais (10 por categoria)

2. **accidents_investigation**: Investigações de acidentes
   - Campos: `id`, `top_event_description`, `status` (Open/Closed), `created_at`

3. **evidence**: Evidências coletadas (imagens)
   - Campos: `id`, `accident_id`, `image_url`, `description`, `uploaded_at`

4. **timeline**: Cronologia de eventos
   - Campos: `id`, `accident_id`, `event_time`, `description`

5. **fault_tree_nodes**: Nós da árvore de falhas
   - Campos: `id`, `accident_id`, `parent_id`, `description`, `node_type` (root/hypothesis/fact), `validation_status` (pending/validated/discarded), `nbr_standard_id`

### Políticas RLS

Todas as tabelas têm RLS habilitado com políticas públicas para testes. **IMPORTANTE**: Ajuste as políticas RLS conforme sua necessidade de segurança antes de produção.

## 🚀 Funcionalidades Implementadas

### 1. Aba: Evidências e Ações Imediatas
- ✅ Upload de imagens (PNG, JPG, JPEG)
- ✅ Galeria de evidências em grid
- ✅ Descrição e data de cada evidência

### 2. Aba: Cronologia
- ✅ Adição de eventos com data e hora
- ✅ Visualização da timeline ordenada cronologicamente
- ✅ Interface visual com linha do tempo

### 3. Aba: Árvore de Falhas (FTA)
- ✅ Visualização gráfica da árvore usando Graphviz
- ✅ Adição de nós (root, hypothesis, fact)
- ✅ Hierarquia pai-filho
- ✅ Validação de hipóteses (Validar/Descartar/Pendente)
- ✅ Cores visuais: Verde (validado), Vermelho (descartado), Cinza (pendente)
- ✅ Fallback para lista quando Graphviz não disponível

### 4. Aba: Classificação Técnica
- ✅ Filtro para mostrar apenas nós validados
- ✅ Dropdowns por categoria NBR (Atos Inseguros, Condições Inseguras, Fatores Pessoais, Tipos de Acidente)
- ✅ Vinculação de códigos NBR aos nós validados
- ✅ Salvamento da classificação

## 📁 Arquivos Criados

1. **`services/investigation.py`**: Serviço com todas as funções de banco de dados
2. **`pages/10_Investigacao_Acidentes.py`**: Página principal do Streamlit
3. **`requirements.txt`**: Atualizado com `graphviz>=0.20.0`

## ⚙️ Configuração Necessária

### 1. Bucket de Storage

O código usa o bucket **`evidencias`** que já existe no projeto. Se você preferir usar um bucket específico chamado **`evidence`**, você pode:

1. Criar o bucket no Supabase Storage
2. Configurá-lo como público ou privado (conforme necessidade)
3. Atualizar a linha 72 em `services/investigation.py`:
   ```python
   bucket = "evidence"  # ao invés de "evidencias"
   ```

### 2. Instalação de Dependências

```bash
pip install -r requirements.txt
```

**Nota sobre Graphviz**: Para visualização completa da árvore de falhas, você também precisa instalar o Graphviz no sistema:

- **Windows**: Baixe do [site oficial](https://graphviz.org/download/) ou use `choco install graphviz`
- **Linux**: `sudo apt-get install graphviz` (Ubuntu/Debian) ou `sudo yum install graphviz` (RHEL/CentOS)
- **macOS**: `brew install graphviz`

Se o Graphviz não estiver instalado, o sistema funcionará normalmente, mas mostrará a árvore em formato de lista ao invés de gráfico.

### 3. Verificação das Tabelas

Execute no SQL Editor do Supabase para verificar se as tabelas foram criadas:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('nbr_standards', 'accidents_investigation', 'evidence', 'timeline', 'fault_tree_nodes');
```

## 🎯 Como Usar

1. **Acesse a página**: No menu do Streamlit, vá para "10_Investigacao_Acidentes"

2. **Crie uma investigação**: Clique em "➕ Nova Investigação" e descreva o evento principal

3. **Colete evidências**: Na aba "Evidências", faça upload de imagens

4. **Construa a timeline**: Na aba "Cronologia", adicione eventos na ordem temporal

5. **Construa a árvore de falhas**:
   - Adicione o nó raiz (Top Event)
   - Adicione hipóteses como filhos
   - Valide ou descarte hipóteses
   - Adicione fatos confirmados

6. **Classifique tecnicamente**: Na aba "Classificação Técnica", vincule códigos NBR aos nós validados

## 🔧 Funções Helper Disponíveis

Todas as funções estão em `services/investigation.py`:

- `create_accident_investigation()`: Cria nova investigação
- `get_accident_investigations()`: Lista todas as investigações
- `upload_evidence_image()`: Upload de evidência
- `add_timeline_event()`: Adiciona evento à timeline
- `add_fault_tree_node()`: Adiciona nó à árvore
- `update_node_validation_status()`: Atualiza status de validação
- `link_nbr_standard_to_node()`: Vincula padrão NBR
- `get_nbr_standards()`: Busca padrões NBR por categoria

## 📊 Dados Iniciais

A tabela `nbr_standards` foi populada com:

- **10 Atos Inseguros** (códigos 50.30.xx.xxx, 50.60.xx.xxx)
- **10 Condições Inseguras** (códigos 60.10.xx.xxx, 60.20.xx.xxx, 60.30.xx.xxx, 60.40.xx.xxx)
- **10 Fatores Pessoais** (códigos 40.xx.xx.xxx)
- **10 Tipos de Acidente** (códigos 10.xx.xx.xxx, 20.xx.xx.xxx, 30.xx.xx.xxx, 40.xx.xx.xxx, 50.xx.xx.xxx)

## 🔐 Segurança

⚠️ **IMPORTANTE**: As políticas RLS estão configuradas para acesso público apenas para testes. Antes de colocar em produção:

1. Revise e ajuste as políticas RLS conforme seu modelo de segurança
2. Implemente controle de acesso baseado em usuário/organização
3. Considere usar políticas baseadas em roles (Admin, Editor, Viewer)

## 🐛 Troubleshooting

### Erro ao fazer upload de imagem
- Verifique se o bucket existe e está configurado corretamente
- Verifique permissões do bucket (público ou privado com políticas adequadas)

### Árvore de falhas não renderiza
- Instale o Graphviz no sistema operacional
- Verifique se `graphviz` está instalado via pip: `pip install graphviz`
- O sistema funcionará em modo lista se Graphviz não estiver disponível

### Erro ao buscar padrões NBR
- Verifique se a tabela `nbr_standards` foi populada corretamente
- Execute a migration `seed_nbr_standards_safe` novamente se necessário

## 📝 Próximos Passos (Opcional)

- [ ] Adicionar exportação de relatório PDF da investigação
- [ ] Implementar busca e filtros avançados
- [ ] Adicionar comentários/notas aos nós da árvore
- [ ] Implementar versionamento da árvore de falhas
- [ ] Adicionar métricas e estatísticas da investigação
- [ ] Integração com outros módulos do sistema (Acidentes, N/C)

---

**Desenvolvido conforme especificações NBR 14280 e metodologia FTA**

