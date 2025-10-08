# 🗄️ Migrações do Supabase

✅ **VERSÃO FINAL CORRIGIDA** - Baseada na estrutura REAL do banco

Este diretório contém as migrações SQL para otimização e segurança do banco de dados.

📖 **Leia**: `APLICAR_MIGRACOES.md` para instruções passo a passo  
📊 **Estrutura**: `ESTRUTURA_REAL.md` para ver todas as colunas do banco

---

## 📋 Migrações Disponíveis

### 001 - Índices Compostos (🚀 Performance)

**Arquivo**: `001_indices_compostos.sql`  
**Objetivo**: Melhorar performance de queries em 10x  
**Impacto**: Queries >500ms → <50ms

**O que faz**:

- ✅ 13 índices compostos criados
- ✅ Índices GIN para JSONB
- ✅ Partial indexes para economia de espaço
- ✅ Análise automática de tabelas

**Como aplicar**:

```bash
# Opção 1: Via Supabase Dashboard
# 1. Ir em SQL Editor
# 2. Colar conteúdo de 001_indices_compostos.sql
# 3. Executar

# Opção 2: Via CLI
supabase db push 001_indices_compostos.sql
```

---

### 002 - Row Level Security (🔒 Segurança)

**Arquivo**: `002_row_level_security.sql`  
**Objetivo**: Adicionar camada extra de segurança  
**Impacto**: Proteção granular de dados

**O que faz**:

- ✅ RLS habilitado em 5 tabelas
- ✅ Políticas de leitura pública
- ✅ Políticas de escrita restrita (apenas service_role)
- ✅ Auditoria opcional

**Como aplicar**:

```bash
# Via Supabase Dashboard SQL Editor
# Colar e executar 002_row_level_security.sql
```

**⚠️ IMPORTANTE**:

- Service role bypassa RLS automaticamente
- Anon users só podem ler dados públicos
- Scraper usa service_role para escrever

---

### 003 - Constraints de Integridade (✅ Validação)

**Arquivo**: `003_constraints_integridade.sql`  
**Objetivo**: Prevenir dados inválidos  
**Impacto**: Validação automática no banco

**O que faz**:

- ✅ 16 constraints CHECK criadas
- ✅ Validação de status, modalidade, centro
- ✅ Validação de valores numéricos
- ✅ Validação de datas lógicas

**Como aplicar**:

```bash
# Via Supabase Dashboard SQL Editor
# Colar e executar 003_constraints_integridade.sql
```

**Exemplos de validação**:

```sql
-- ❌ FALHA: Status inválido
INSERT INTO bolsas (status) VALUES ('invalido');

-- ❌ FALHA: Vagas = 0
INSERT INTO bolsas (vagas) VALUES (0);

-- ✅ OK: Valores válidos
INSERT INTO bolsas (status, vagas) VALUES ('disponivel', 5);
```

---

## 🚀 Ordem de Aplicação Recomendada

1. **Primeiro**: `003_constraints_integridade.sql`
   - Garante integridade antes de criar índices
2. **Segundo**: `001_indices_compostos.sql`
   - Cria índices em dados já validados
3. **Terceiro**: `002_row_level_security.sql`
   - Adiciona segurança final

---

## 📊 Verificação

### Verificar Índices

```sql
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
```

### Verificar RLS

```sql
SELECT
    schemaname,
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

### Verificar Constraints

```sql
SELECT
    tc.table_name,
    tc.constraint_name,
    tc.constraint_type,
    cc.check_clause
FROM information_schema.table_constraints tc
LEFT JOIN information_schema.check_constraints cc
    ON tc.constraint_name = cc.constraint_name
WHERE tc.table_schema = 'public'
    AND tc.constraint_type = 'CHECK'
ORDER BY tc.table_name;
```

---

## 🧪 Testes

### Testar Performance (EXPLAIN ANALYZE)

```sql
-- Antes dos índices
EXPLAIN ANALYZE
SELECT * FROM bolsas_view_agrupada
WHERE status = 'disponivel' AND centro = 'cct';

-- Depois dos índices
-- Deve mostrar "Index Scan" ao invés de "Seq Scan"
```

### Testar RLS

```sql
-- Testar como anon (sem permissões)
SET ROLE anon;

-- Deve funcionar (leitura pública)
SELECT * FROM editais LIMIT 1;

-- Deve falhar (escrita restrita)
INSERT INTO editais (titulo, link) VALUES ('Teste', 'http://teste.com');

RESET ROLE;
```

### Testar Constraints

```sql
-- Deve falhar (status inválido)
INSERT INTO bolsas (status) VALUES ('teste');

-- Deve falhar (vagas <= 0)
INSERT INTO bolsas (vagas) VALUES (0);

-- Deve funcionar
INSERT INTO bolsas (status, vagas) VALUES ('disponivel', 5);
```

---

## 🔄 Rollback (Se Necessário)

### Remover Índices

```sql
-- Listar índices criados
\di

-- Remover específico
DROP INDEX IF EXISTS idx_bolsas_filter;

-- Remover todos (cuidado!)
DROP INDEX IF EXISTS idx_bolsas_filter;
DROP INDEX IF EXISTS idx_bolsas_disponivel;
-- ... etc
```

### Desabilitar RLS

```sql
ALTER TABLE editais DISABLE ROW LEVEL SECURITY;
ALTER TABLE projetos DISABLE ROW LEVEL SECURITY;
ALTER TABLE bolsas DISABLE ROW LEVEL SECURITY;
```

### Remover Constraints

```sql
ALTER TABLE bolsas DROP CONSTRAINT IF EXISTS bolsas_status_check;
ALTER TABLE editais DROP CONSTRAINT IF EXISTS editais_modalidade_check;
-- ... etc
```

---

## 📈 Resultados Esperados

### Performance

- ⚡ Queries 10x mais rápidas
- 📉 Redução de CPU usage no banco
- 💾 Uso eficiente de memória

### Segurança

- 🔒 Camada extra de proteção (RLS)
- ✅ Dados sempre válidos (constraints)
- 🛡️ Acesso granular por role

### Manutenibilidade

- 📋 Validação automática
- 🚫 Menos bugs de dados inválidos
- 🔍 Fácil auditoria

---

## 📚 Referências

- [Supabase RLS](https://supabase.com/docs/guides/auth/row-level-security)
- [PostgreSQL Indexes](https://www.postgresql.org/docs/current/indexes.html)
- [PostgreSQL Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)

---

## ✅ Checklist de Aplicação

- [ ] Fazer backup do banco
- [ ] Aplicar `003_constraints_integridade.sql`
- [ ] Aplicar `001_indices_compostos.sql`
- [ ] Aplicar `002_row_level_security.sql`
- [ ] Executar queries de verificação
- [ ] Testar performance com EXPLAIN ANALYZE
- [ ] Testar RLS com diferentes roles
- [ ] Monitorar uso de índices
- [ ] Documentar resultados

---

**Data**: 08/10/2025  
**Versão**: 1.0  
**Status**: ✅ Pronto para produção
