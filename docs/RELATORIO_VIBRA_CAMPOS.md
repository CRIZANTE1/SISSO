# 📋 Campos do Relatório Vibra - Implementação

## Visão Geral

O sistema de investigação foi expandido para capturar **todos os campos detalhados** do relatório oficial da Vibra, permitindo registro completo e estruturado de acidentes.

## 🗄️ Estrutura do Banco de Dados

### Tabela `accidents` (Expandida)

#### Identificação
- `registry_number` (TEXT): Número do registro (ex: "XX/2024")
- `base_location` (TEXT): Localização da base (ex: "Base de Barueri")

#### Classificação (Booleans)
- `class_injury` (BOOLEAN): Com Lesão
- `class_community` (BOOLEAN): Impacto na Comunidade
- `class_environment` (BOOLEAN): Meio Ambiente
- `class_process_safety` (BOOLEAN): Segurança de Processo
- `class_asset_damage` (BOOLEAN): Dano ao Patrimônio
- `class_near_miss` (BOOLEAN): Quase-Acidente

#### Gravidade
- `severity_level` (ENUM): 'Low', 'Medium', 'High', 'Catastrophic'

#### Perdas
- `estimated_loss_value` (NUMERIC): Valor estimado de perdas em R$

#### Segurança de Processo
- `product_released` (TEXT): Produto liberado
- `volume_released` (NUMERIC): Volume liberado (m³)
- `volume_recovered` (NUMERIC): Volume recuperado (m³)
- `release_duration_hours` (NUMERIC): Duração do vazamento (horas)
- `equipment_involved` (TEXT): Equipamento envolvido

#### Meio Ambiente
- `area_affected` (ENUM): 'Soil', 'Water', 'Not Applicable', 'Other'

### Tabela `involved_people` (Nova)

Armazena todas as pessoas envolvidas no acidente usando um campo `person_type` para diferenciar:

- **Driver**: Motoristas
- **Injured**: Vítimas/Lesionados
- **Commission_Member**: Membros da Comissão
- **Witness**: Testemunhas

#### Campos
- `id` (UUID, PK)
- `accident_id` (UUID, FK → accidents.id)
- `person_type` (TEXT, ENUM)
- `name` (TEXT)
- `registration_id` (TEXT): Matrícula/CPF
- `job_title` (TEXT): Cargo/Função
- `company` (TEXT): Empresa (Vibra, Contratada)
- `age` (INTEGER)
- `time_in_role` (TEXT): Tempo na função
- `aso_date` (DATE): Data do ASO
- `training_status` (TEXT): Status de treinamento

## 🖥️ Interface do Usuário (Step 1)

O Passo 1 foi completamente refatorado em **5 seções organizadas** com `st.expander`:

### Seção 1: Dados Gerais
**Campos:**
- Número do Registro
- Data e Hora da Ocorrência
- Local da Base (Selectbox)
- Título do Acidente
- Descrição Detalhada

**Mapeamento PDF:** Páginas 1 e 2

### Seção 2: Classificação e Gravidade
**Campos:**
- Checkboxes (Multi-select):
  - ☑️ Com Lesão
  - ☑️ Meio Ambiente
  - ☑️ Segurança de Processo
  - ☑️ Dano ao Patrimônio
  - ☑️ Impacto na Comunidade
  - ☑️ Quase-Acidente
- Selectbox: Nível de Gravidade (Baixa, Média, Alta, Catastrófica)
- Number Input: Valor Estimado de Perdas (R$)

**Mapeamento PDF:** Página 4 (Item 1.2)

### Seção 3: Detalhes do Vazamento/Processo
**Condicional:** Só aparece se "Meio Ambiente" ou "Segurança de Processo" estiver marcado

**Campos:**
- Produto Liberado
- Volume Liberado (m³)
- Volume Recuperado (m³)
- Duração do Vazamento (horas)
- Equipamento Envolvido
- Área Afetada (Radio: Solo, Água, N/A, Outro)

**Mapeamento PDF:** Página 4 (Itens 1.5 e 1.6)

### Seção 4: Pessoas Envolvidas
**Subseções:**

#### 🚗 Motoristas
- Nome, Matrícula/CPF, Cargo/Função
- Empresa, Idade, Data ASO

#### 🏥 Vítimas/Lesionados
- Nome, Matrícula/CPF, Cargo/Função
- Empresa, Idade, Data ASO

#### 👁️ Testemunhas
- Nome, Matrícula/CPF

**Mapeamento PDF:** Páginas 4 e 5 (Itens 1.4, 1.7, 1.8)

### Seção 5: Comissão de Investigação
**Campos:**
- Nome, Matrícula/ID, Função/Cargo

**Mapeamento PDF:** Página 11 (Item 7)

## 🔧 Funcionalidades Implementadas

### 1. Carregamento de Dados Existentes
- Ao abrir uma investigação existente, todos os campos são preenchidos automaticamente
- Pessoas envolvidas são carregadas e exibidas nos formulários dinâmicos

### 2. Formulário Dinâmico
- Quantidade de pessoas ajustável (0-10 para cada tipo)
- Campos aparecem/desaparecem conforme necessário
- Validação: apenas pessoas com nome são salvas

### 3. Lógica Condicional
- Seção 3 (Vazamento/Processo) só aparece se relevante
- Campos opcionais tratados corretamente

### 4. Upsert Inteligente
- Remove pessoas existentes antes de inserir novas
- Garante integridade dos dados

## 📊 Funções do Serviço

### `update_accident(accident_id, **kwargs)`
Atualiza dados do acidente com todos os campos expandidos.

### `get_involved_people(accident_id, person_type=None)`
Busca pessoas envolvidas, opcionalmente filtradas por tipo.

### `upsert_involved_people(accident_id, people)`
Remove pessoas existentes e insere novas (upsert completo).

## 🎯 Fluxo de Uso

1. **Criar/Selecionar Investigação**
   - Cria nova ou seleciona existente na sidebar

2. **Preencher Step 1**
   - Abre cada seção (expander)
   - Preenche todos os campos relevantes
   - Adiciona pessoas envolvidas (quantidade dinâmica)
   - Clica em "💾 Salvar Dados e Continuar"

3. **Dados Salvos**
   - Acidente atualizado no banco
   - Pessoas envolvidas salvas/atualizadas
   - Pode continuar para Step 2

4. **Upload de Evidências**
   - Separado do formulário principal
   - Pode adicionar fotos a qualquer momento

## 📋 Mapeamento Completo PDF → Sistema

| PDF (Página/Item) | Campo no Sistema | Seção |
|-------------------|------------------|-------|
| Pág 1-2 | Dados Gerais | Seção 1 |
| Pág 4 (1.2) | Classificação | Seção 2 |
| Pág 4 (1.5) | Vazamento/Processo | Seção 3 |
| Pág 4 (1.6) | Meio Ambiente | Seção 3 |
| Pág 4 (1.4) | Motoristas | Seção 4 |
| Pág 4 (1.7) | Vítimas | Seção 4 |
| Pág 4 (1.8) | Testemunhas | Seção 4 |
| Pág 11 (7) | Comissão | Seção 5 |

## 🔍 Exemplos de Uso

### Exemplo 1: Acidente com Vazamento
1. Marca "Meio Ambiente" e "Segurança de Processo"
2. Seção 3 aparece automaticamente
3. Preenche: Produto (Gasolina), Volume (10 m³), etc.

### Exemplo 2: Acidente com Lesão
1. Marca "Com Lesão"
2. Na Seção 4, adiciona vítima(s)
3. Preenche dados completos da vítima

### Exemplo 3: Quase-Acidente
1. Marca "Quase-Acidente"
2. Gravidade: "Baixa"
3. Não precisa preencher vítimas

## ⚠️ Observações Importantes

1. **Campos Obrigatórios:**
   - Título do Acidente
   - Data e Hora da Ocorrência

2. **Campos Condicionais:**
   - Seção 3 só aparece se relevante
   - Pessoas envolvidas são opcionais

3. **Validação:**
   - Apenas pessoas com nome são salvas
   - Campos numéricos aceitam 0 (zero)

4. **Performance:**
   - Upsert remove e reinsere (garante integridade)
   - Índices criados para consultas rápidas

## 🚀 Próximos Passos (Opcional)

- [ ] Validação de campos obrigatórios
- [ ] Exportação para PDF no formato Vibra
- [ ] Histórico de alterações
- [ ] Relatórios estatísticos por classificação
- [ ] Integração com sistema de treinamentos (ASO)

---

**Sistema completo de captura de dados do Relatório Vibra implementado** ✅

