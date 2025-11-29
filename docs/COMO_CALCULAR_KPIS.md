# 📊 Como Calcular KPIs

## Como os KPIs são Calculados

Os KPIs **NÃO são calculados automaticamente**. Eles precisam ser calculados manualmente através do botão **"Recalcular KPIs"** na página de Admin.

## 📋 Processo de Cálculo

### 1. Dados Necessários

Para calcular KPIs, você precisa ter:
- ✅ **Acidentes** cadastrados na tabela `accidents`
- ✅ **Horas Trabalhadas** cadastradas na tabela `hours_worked_monthly`

### 2. Como Calcular

1. Acesse a página **"Admin" → "Dados Básicos"**
2. Vá para a aba **"Atualizar KPIs"**
3. Clique no botão **"🔄 Recalcular KPIs"**

### 3. O que Acontece no Cálculo

O sistema:
1. Busca todos os acidentes do banco
2. Busca todas as horas trabalhadas do banco
3. Agrupa por **período (mês/ano)** e **usuário (created_by)**
4. Calcula:
   - **Taxa de Frequência**: `(Acidentes × 1.000.000) ÷ Horas Trabalhadas`
   - **Taxa de Gravidade**: `((Dias Perdidos + Dias Debitados) × 1.000.000) ÷ Horas Trabalhadas`
5. Salva os resultados na tabela `kpi_monthly`

### 4. Fórmulas

#### Taxa de Frequência (TF)
```
TF = (N° de acidentes × 1.000.000) ÷ Horas trabalhadas
```

#### Taxa de Gravidade (TG)
```
TG = ((Dias Perdidos + Dias Debitados) × 1.000.000) ÷ Horas trabalhadas
```

**Dias Debitados** (conforme NBR 14280):
- Morte = 6.000 dias
- Amputação de mão = 3.000 dias
- Amputação de pé = 2.400 dias

## ⚠️ Por que a Tabela está Vazia?

A tabela `kpi_monthly` pode estar vazia se:

1. **Você ainda não clicou no botão "Recalcular KPIs"**
   - ✅ Solução: Acesse Admin → Dados Básicos → Atualizar KPIs e clique no botão

2. **Não há dados de acidentes ou horas trabalhadas**
   - ✅ Solução: Cadastre acidentes e/ou horas trabalhadas primeiro

3. **Os dados não estão no mesmo período**
   - ✅ O sistema precisa que acidentes e horas estejam no mesmo mês/ano para calcular

4. **Os dados não estão vinculados ao mesmo usuário**
   - ✅ Verifique se `created_by` está correto (UUID) em ambas as tabelas

## 🔍 Como Verificar

Execute o script `verificar_dados_kpi.sql` no SQL Editor do Supabase para verificar:
- Quantos acidentes existem
- Quantas horas trabalhadas existem
- Se há períodos sem horas ou sem acidentes

## 📝 Notas Importantes

- Os KPIs são calculados **por período (mês)** e **por usuário**
- Se você cadastrar novos acidentes ou horas, precisa **recalcular** os KPIs
- O sistema cria KPIs mesmo para períodos sem acidentes (com valores zero)
- As horas são armazenadas em **centenas** (ex: 176 = 17.600 horas)

