# 🌳 Estrutura JSON da Árvore de Falhas

## Visão Geral

A aba "Árvore de Falhas" agora utiliza uma **estrutura JSON hierárquica** gerada em tempo real a partir dos dados relacionais do banco de dados. Isso permite:

- ✅ Visualização dinâmica da estrutura hierárquica
- ✅ Inspeção do modelo de dados em tempo real
- ✅ Renderização do Graphviz baseada em JSON (não DataFrame)
- ✅ Manutenção dos dados relacionais no banco (melhor para estatísticas)

## 🔄 Fluxo de Dados

### 1. Banco de Dados (Supabase)
Armazena dados **planos** e relacionais:
```
fault_tree_nodes:
- id: uuid
- parent_id: uuid (nullable)
- accident_id: uuid
- label: text
- type: 'root' | 'hypothesis' | 'fact'
- status: 'pending' | 'validated' | 'discarded'
- nbr_standard_id: integer (nullable)
```

**Exemplo de dados planos:**
```
Nó A: id=1, parent_id=null, label="Acidente"
Nó B: id=2, parent_id=1, label="Hipótese 1"
Nó C: id=3, parent_id=1, label="Hipótese 2"
```

### 2. Python (Middleware)
A função `build_fault_tree_json(accident_id)` converte dados planos em JSON hierárquico:

```python
def build_fault_tree_json(accident_id: str) -> Optional[Dict[str, Any]]:
    """
    Converte dados planos do banco em estrutura hierárquica JSON.
    Função recursiva que constrói a árvore de falhas.
    """
    # 1. Busca todos os nós do acidente
    # 2. Encontra o nó raiz (parent_id is None)
    # 3. Recursivamente constrói estrutura hierárquica
    # 4. Retorna JSON completo
```

### 3. Frontend (Streamlit)
- **Visualizador JSON**: Expander com `st.json()` mostra a estrutura completa
- **Visualizador Gráfico**: Graphviz lê o JSON para desenhar nós e arestas

## 📋 Estrutura JSON

### Formato
```json
{
  "id": "uuid-do-no",
  "label": "Descrição do nó",
  "type": "root" | "hypothesis" | "fact",
  "status": "pending" | "validated" | "discarded",
  "nbr_code": "50.30.05.000" | null,
  "children": [
    {
      "id": "uuid-do-filho",
      "label": "Hipótese 1",
      "type": "hypothesis",
      "status": "pending",
      "nbr_code": null,
      "children": []
    }
  ]
}
```

### Campos

- **id**: UUID do nó (string)
- **label**: Descrição/hipótese do nó
- **type**: Tipo do nó (`root`, `hypothesis`, `fact`)
- **status**: Status de validação (`pending`, `validated`, `discarded`)
- **nbr_code**: Código NBR vinculado (se existir, caso contrário `null`)
- **children**: Array de nós filhos (estrutura recursiva)

## 🎨 Renderização Graphviz

A função `render_fault_tree_graph_from_json(tree_json)` percorre o JSON recursivamente:

```python
def render_fault_tree_graph_from_json(tree_json: Dict[str, Any]):
    """
    Renderiza a árvore usando Graphviz a partir do JSON hierárquico.
    Função recursiva que percorre o JSON.
    """
    def add_node_recursive(node_json):
        # Adiciona nó ao gráfico
        # Processa filhos recursivamente
        # Adiciona arestas pai->filho
```

### Cores por Status
- 🟢 **Verde**: `status == 'validated'`
- 🔴 **Vermelho**: `status == 'discarded'`
- ⚪ **Cinza**: `status == 'pending'`

### Informações Exibidas
- Label do nó
- Tipo (`[root]`, `[hypothesis]`, `[fact]`)
- Código NBR (se vinculado)
- Status visual (cor)

## 🔧 Funções Principais

### `build_fault_tree_json(accident_id)`
**Localização**: `services/investigation.py`

**Funcionalidade**:
1. Busca todos os nós do acidente
2. Busca códigos NBR para mapeamento
3. Encontra nó raiz (`parent_id is None`)
4. Constrói estrutura hierárquica recursivamente
5. Retorna JSON completo ou `None` se não houver raiz

**Tratamento de Erros**:
- Retorna `None` se não houver nós
- Retorna `None` se não houver nó raiz
- Continua sem códigos NBR se falhar ao buscar

### `render_fault_tree_graph_from_json(tree_json)`
**Localização**: `pages/investigation.py`

**Funcionalidade**:
1. Cria objeto Graphviz
2. Percorre JSON recursivamente
3. Adiciona nós com cores baseadas em status
4. Adiciona arestas pai->filho
5. Retorna objeto Graphviz ou `None`

## 🖥️ Interface do Usuário

### Expander "Ver Estrutura JSON da Árvore"
- Localizado na aba "Árvore de Falhas"
- Mostra JSON formatado usando `st.json()`
- Atualiza em tempo real quando nós são adicionados/modificados
- Útil para:
  - Inspeção do modelo de dados
  - Debugging
  - Exportação manual (copiar JSON)

### Visualização Gráfica
- Renderizada usando Graphviz
- Baseada no JSON (não no DataFrame)
- Atualiza automaticamente após adicionar/modificar nós
- Fallback para JSON formatado se Graphviz não disponível

## 🔄 Atualização em Tempo Real

O JSON é **regenerado a cada renderização** da página:

1. Usuário adiciona nó → Insere no banco
2. Página recarrega (`st.rerun()`)
3. `build_fault_tree_json()` é chamado novamente
4. JSON atualizado é exibido
5. Graphviz renderiza com nova estrutura

## 💡 Por Que Esta Abordagem?

### Vantagens

1. **Dados Relacionais no Banco**
   - Fácil fazer queries estatísticas
   - Ex: "Quantos acidentes tiveram falha de overfill?"
   - Ex: "Qual a distribuição de tipos de nós?"

2. **JSON na Aplicação**
   - Estrutura hierárquica fácil de trabalhar
   - Renderização Graphviz simplificada
   - Inspeção visual do modelo

3. **Melhor dos Dois Mundos**
   - Banco: Dados relacionais (estatísticas)
   - App: JSON hierárquico (visualização)

### Alternativa (Não Recomendada)

❌ **Salvar JSON direto no banco**:
- Difícil fazer estatísticas
- Queries complexas
- Perda de integridade relacional

## 🐛 Troubleshooting

### JSON está vazio/null
- **Causa**: Nó raiz não existe
- **Solução**: O sistema cria automaticamente ao acessar a aba

### Código NBR não aparece no JSON
- **Causa**: Nó não está validado ou padrão não vinculado
- **Solução**: Valide o nó e vincule um padrão NBR na aba "Classificação Técnica"

### Graphviz não renderiza
- **Causa**: Graphviz não instalado
- **Solução**: JSON ainda é exibido como fallback

### Erro ao construir JSON
- **Causa**: Dados inconsistentes no banco
- **Solução**: Verifique se há nós órfãos (parent_id aponta para nó inexistente)

## 📝 Exemplo de Uso

### 1. Criar Investigação
```
Título: "Queda durante manutenção"
```

### 2. Acessar Aba "Árvore de Falhas"
- Nó raiz é criado automaticamente: "Queda durante manutenção"

### 3. Adicionar Hipóteses
```
Hipótese 1: "Falta de treinamento" (filho do raiz)
Hipótese 2: "Equipamento defeituoso" (filho do raiz)
```

### 4. Validar Hipóteses
- Validar "Falta de treinamento"
- Descartar "Equipamento defeituoso"

### 5. Vincular Código NBR
- Na aba "Classificação Técnica"
- Vincular "40.30.00.000" à hipótese validada

### 6. Ver JSON Resultante
```json
{
  "id": "...",
  "label": "Queda durante manutenção",
  "type": "root",
  "status": "pending",
  "nbr_code": null,
  "children": [
    {
      "id": "...",
      "label": "Falta de treinamento",
      "type": "hypothesis",
      "status": "validated",
      "nbr_code": "40.30.00.000",
      "children": []
    },
    {
      "id": "...",
      "label": "Equipamento defeituoso",
      "type": "hypothesis",
      "status": "discarded",
      "nbr_code": null,
      "children": []
    }
  ]
}
```

---

**Implementado conforme especificação: Dados relacionais no banco, JSON hierárquico na aplicação**

