# 🧪 **GUIA COMPLETO DE TESTE - SISTEMA WHATSAPP ALERTS**

## 🚀 **COMO TESTAR APÓS CADASTRAR SEU NÚMERO**

### **PASSO 1: 📱 Cadastrar Seu Número**

#### **1.1 Pelo Botão do Site:**

- ✅ Abra seu site
- ✅ Clique no **botão verde WhatsApp** (canto inferior direito)
- ✅ Digite seu número: exemplo `(22) 99999-9999`
- ✅ Deve aparecer formatado enquanto digita
- ✅ Clique em "📱 Receber Alertas"

#### **1.2 Se o número não aparecer:**

- ✅ Abra **F12** (DevTools)
- ✅ Vá na aba **Console**
- ✅ Deve aparecer: `WhatsApp digitado: 22999999999 → Formatado: (22) 99999-9999`
- ✅ Se não aparece, recarregue a página

#### **1.3 Resposta esperada:**

```json
{
  "status": "success",
  "message": "WhatsApp cadastrado com sucesso! Você receberá alertas de novos editais.",
  "numero": "+5522999999999"
}
```

---

### **PASSO 2: ✅ Verificar se Foi Cadastrado**

#### **2.1 Via API (Terminal/Postman):**

```bash
curl -X POST https://seusite.vercel.app/api/alertas/listar \
  -H "Content-Type: application/json" \
  -d '{}'
```

#### **2.2 Resposta esperada:**

```json
{
  "total_usuarios": 1,
  "usuarios_ativos": 1,
  "usuarios": [
    {
      "numero_mascarado": "+552299999****",
      "status": "ativo",
      "data_cadastro": "2025-09-23T15:30:00.000Z"
    }
  ],
  "message": "Total de 1 usuário(s) cadastrado(s)"
}
```

---

### **PASSO 3: 🧪 Testar Detecção de Tipos**

#### **3.1 Teste: Edital de Extensão (DEVE notificar)**

```bash
curl -X POST https://seusite.vercel.app/api/alertas/test-detection \
  -H "Content-Type: application/json" \
  -d '{"titulo": "Edital de Extensão Universitária - Bolsas 2025"}'
```

**Resposta esperada:**

```json
{
  "titulo": "Edital de Extensão Universitária - Bolsas 2025",
  "tipo_detectado": "extensao",
  "sera_notificado": true
}
```

#### **3.2 Teste: Resultado (DEVE notificar)**

```bash
curl -X POST https://seusite.vercel.app/api/alertas/test-detection \
  -H "Content-Type: application/json" \
  -d '{"titulo": "Resultado Final - Mestrado CCT"}'
```

**Resposta esperada:**

```json
{
  "tipo_detectado": "resultado",
  "sera_notificado": true
}
```

#### **3.3 Teste: Mestrado Regular (NÃO deve notificar)**

```bash
curl -X POST https://seusite.vercel.app/api/alertas/test-detection \
  -H "Content-Type: application/json" \
  -d '{"titulo": "Edital de Mestrado em Biologia"}'
```

**Resposta esperada:**

```json
{
  "tipo_detectado": "outros",
  "sera_notificado": false
}
```

---

### **PASSO 4: 📤 Testar Envio de WhatsApp**

#### **4.1 Teste de Extensão:**

```bash
curl -X POST https://seusite.vercel.app/api/alertas/notify \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "TESTE - Edital de Extensão Comunitária",
    "link": "https://uenf.br/teste",
    "tipo": "extensao"
  }'
```

#### **4.2 Teste de Resultado:**

```bash
curl -X POST https://seusite.vercel.app/api/alertas/notify \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "TESTE - Lista de Aprovados Mestrado",
    "link": "https://uenf.br/teste-resultado",
    "tipo": "resultado"
  }'
```

#### **4.3 Resposta esperada (se você cadastrou):**

```json
{
  "status": "completed",
  "sent_count": 1,
  "total_subscribers": 1,
  "edital_type": "extensao",
  "errors": []
}
```

---

### **PASSO 5: 📱 WhatsApp que Deve Chegar**

#### **5.1 Para Extensão:**

```
🎓 *EDITAL DE EXTENSÃO UENF!*

📋 TESTE - Edital de Extensão Comunitária

🔗 Acesse: https://uenf.br/teste

💡 Oportunidade de extensão universitária!

💻 Veja mais em: https://seusite.vercel.app

_Para cancelar alertas, responda PARAR_
```

#### **5.2 Para Resultado:**

```
🏆 *RESULTADO PUBLICADO UENF!*

📋 TESTE - Lista de Aprovados Mestrado

🔗 Acesse: https://uenf.br/teste-resultado

🔍 Confira se você foi aprovado(a)!

💻 Veja mais em: https://seusite.vercel.app

_Para cancelar alertas, responda PARAR_
```

---

### **PASSO 6: 🔄 Testar Scraping Automático**

#### **6.1 Executar scraping manualmente:**

```bash
# Use o secret configurado no seu vercel.json
curl -X GET "https://seusite.vercel.app/api/scrape?secret=my-scraping-secret-2024"
```

#### **6.2 Resposta possível:**

```json
{
  "status": "success",
  "message": "Scraping executado - 1 novos editais encontrados",
  "new_editais": 1,
  "notifications_sent": [
    {
      "status": "completed",
      "sent_count": 1,
      "edital_type": "extensao"
    }
  ]
}
```

---

## 🛠️ **TROUBLESHOOTING**

### **❌ "Número não aparece no campo"**

**Soluções:**

1. Aperte **F12** → Console → veja se há erros
2. Recarregue a página (Ctrl+F5)
3. Tente em navegador privado
4. Verifique se há **logs**: `WhatsApp digitado: ...`

### **❌ "Erro ao cadastrar"**

**Soluções:**

1. Verifique se API está rodando: `/api/`
2. Teste direto via curl (exemplo acima)
3. Verifique logs do Vercel

### **❌ "Supabase não disponível"**

**Soluções:**

1. Crie tabela `whatsapp_alerts` no Supabase:

```sql
CREATE TABLE whatsapp_alerts (
    id SERIAL PRIMARY KEY,
    numero TEXT UNIQUE NOT NULL,
    status TEXT DEFAULT 'ativo',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

2. Verifique env vars: `SUPABASE_URL` e `SUPABASE_KEY`

### **❌ "Twilio não configurado"**

**Normal!** Sistema funciona em **modo simulação**:

- ✅ Logs mostram `"status": "simulated"`
- ✅ Tudo funciona, mas WhatsApp não é enviado de verdade
- 🔧 Para receber WhatsApp real, configure Twilio

### **❌ WhatsApp não chega (Twilio configurado)**

**Soluções:**

1. **Sandbox Twilio:** Você precisa enviar código específico primeiro
2. **Número formato internacional:** Deve ter `+55`
3. **Saldo Twilio:** Verifique se tem crédito

---

## ✅ **CHECKLIST - SISTEMA FUNCIONANDO**

### **Frontend:**

- [ ] Botão WhatsApp aparece no canto da tela
- [ ] Modal abre ao clicar no botão
- [ ] Número aparece enquanto digita (com máscara)
- [ ] Console mostra logs de formatação
- [ ] Mensagem de sucesso após cadastro

### **Backend:**

- [ ] `/api/` retorna endpoints WhatsApp
- [ ] `/api/alertas/listar` mostra seu número mascarado
- [ ] `/api/alertas/test-detection` detecta tipos corretos
- [ ] `/api/alertas/notify` retorna "completed"

### **WhatsApp (se Twilio configurado):**

- [ ] Mensagem chega no seu celular
- [ ] Texto correto com emojis
- [ ] Link é clicável
- [ ] Formatação (negrito/itálico) funciona

---

## 🎉 **RESULTADO ESPERADO**

### **✅ Se tudo estiver funcionando:**

1. **Cadastro:** Número aparece, formulário funciona
2. **Detecção:** Sistema identifica extensão/resultado
3. **Notificação:** API retorna sucesso ("completed")
4. **WhatsApp:** Chega no celular (se Twilio configurado)
5. **Automático:** Cron 4h funciona e envia alertas

### **🚀 Parabéns!**

Seu sistema de alertas WhatsApp específicos está **100% funcional**!

---

## 💡 **DICAS EXTRAS**

### **Para testar sem Twilio:**

- Sistema funciona em **modo simulação**
- Todos os logs aparecem nos **Vercel Functions Logs**
- Use `/api/alertas/listar` para ver cadastros

### **Para produção com WhatsApp real:**

1. Criar conta Twilio
2. Configurar **Sandbox WhatsApp**
3. Adicionar env vars: `TWILIO_SID`, `TWILIO_TOKEN`, `TWILIO_WHATSAPP`
4. Testar com `/api/alertas/notify`

### **Para usuários finais:**

- Botão sempre visível no site
- Cadastro super fácil (só clicar e digitar)
- Alertas apenas para extensão e resultados
- Possibilidade de cancelar respondendo "PARAR"
