# 📱 **TELEGRAM BOT - ALERTAS UENF 100% GRATUITOS**

## 🎯 **POR QUE TELEGRAM É MELHOR:**

✅ **100% GRATUITO** - API oficial do Telegram  
✅ **SEM EXPOSIÇÃO** do seu número pessoal  
✅ **BOT DEDICADO** profissional  
✅ **MAIS SIMPLES** - sem QR codes ou conexões complexas  
✅ **UNLIMITED** - sem limites de mensagens  
✅ **MAIS CONFIÁVEL** - API oficial estável  
✅ **MARKDOWN SUPPORT** - mensagens formatadas lindas

---

## 🤖 **PASSO 1: CRIAR SEU BOT (3 MINUTOS)**

### **1.1 Conversar com @BotFather:**

1. **Abra Telegram** no seu celular ou desktop
2. **Procure por:** `@BotFather`
3. **Inicie conversa** clicando em "START"

### **1.2 Criar o Bot:**

```
Você: /newbot
BotFather: Alright, a new bot. How are we going to call it? Please choose a name for your bot.

Você: UENF Alertas Bot
BotFather: Good. Now let's choose a username for your bot. It must end in `bot`. Like this, for example: TetrisBot or tetris_bot.

Você: uenf_alertas_bot
BotFather: Done! Congratulations on your new bot. You will find it at t.me/uenf_alertas_bot. You can now add a description...

Here is your token: 1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ1234567890
```

### **1.3 Guardar o Token:**

⚠️ **IMPORTANTE:** Copie e guarde o token que aparece! Ele será algo como:

```
1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ1234567890
```

---

## 🔧 **PASSO 2: CONFIGURAR BOT (OPCIONAL MAS RECOMENDADO)**

### **2.1 Definir Descrição:**

```
Você: /setdescription
BotFather: Choose a bot to change description.

Você: @uenf_alertas_bot
BotFather: Send me the new description for the bot.

Você: 🎓 Bot oficial de alertas UENF
Receba notificações sobre:
• Novos editais de extensão
• Resultados de seleções
• Oportunidades de bolsas

Digite /start para começar!
```

### **2.2 Definir Comandos:**

```
Você: /setcommands
BotFather: Choose a bot to change the list of commands.

Você: @uenf_alertas_bot
BotFather: Send me a list of commands for your bot.

Você: start - Iniciar bot e ver instruções
stop - Parar de receber alertas
help - Ver ajuda e comandos
status - Ver status das notificações
```

### **2.3 Adicionar Foto (Opcional):**

```
Você: /setuserpic
BotFather: Choose a bot to change profile photo.

Você: @uenf_alertas_bot
BotFather: Send me the new profile photo for the bot.

[Envie uma foto 512x512 da UENF ou logo universitário]
```

---

## 🗄️ **PASSO 3: CRIAR TABELA NO SUPABASE**

### **3.1 Acessar Supabase:**

1. **Acesse:** [supabase.com](https://supabase.com)
2. **Vá para:** Seu projeto UENF
3. **Clique:** "Table Editor" (lado esquerdo)

### **3.2 Criar Tabela `telegram_alerts`:**

1. **Clique:** "Create a new table"
2. **Nome:** `telegram_alerts`
3. **Colunas:**

| Nome          | Tipo          | Configuração                      |
| ------------- | ------------- | --------------------------------- |
| `id`          | `int8`        | ✅ Primary Key, ✅ Auto-increment |
| `telegram_id` | `text`        | ✅ Unique, ❌ Not null            |
| `status`      | `text`        | Default: `'ativo'`                |
| `created_at`  | `timestamptz` | Default: `now()`                  |

### **3.3 SQL Alternativo:**

```sql
CREATE TABLE telegram_alerts (
  id BIGSERIAL PRIMARY KEY,
  telegram_id TEXT UNIQUE NOT NULL,
  status TEXT DEFAULT 'ativo' CHECK (status IN ('ativo', 'inativo')),
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 🌐 **PASSO 4: CONFIGURAR NO VERCEL**

### **4.1 Adicionar Variável de Ambiente:**

1. **Acesse:** [vercel.com](https://vercel.com)
2. **Vá para:** Seu projeto → Settings → Environment Variables
3. **Adicione:**
   - **Name:** `TELEGRAM_BOT_TOKEN`
   - **Value:** `1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ1234567890`
   - **Environment:** Production + Preview + Development

### **4.2 Fazer Deploy:**

```bash
# Se você modificou código, faça commit e push
git add .
git commit -m "Implementado sistema de alertas Telegram"
git push

# O Vercel fará deploy automaticamente
```

---

## 🧪 **PASSO 5: TESTAR O SISTEMA**

### **5.1 Testar Frontend (PROCESSO COMPLETO):**

**⚠️ IMPORTANTE: Faça na ordem certa!**

1. **PRIMEIRO:** Procure seu bot no Telegram (`@seubot_bot`)
2. **Clique "START"** e envie uma mensagem qualquer
3. **DEPOIS:** Abra https://seusite.vercel.app
4. **Clique:** Botão azul flutuante (📱)
5. **Digite:** Seu ID do Telegram (ex: `@joao123`)
6. **Clique:** "Receber Alertas"
7. **Deve aparecer:** "✅ Cadastrado com sucesso!"

### **5.2 Testar API Diretamente:**

```javascript
// No console do browser (F12)
fetch("/api/alertas/telegram", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ telegram: "@joao123" }),
})
  .then((r) => r.json())
  .then((data) => {
    console.log("📱 CADASTRO:", data);
    if (data.status === "success") {
      console.log("✅ Telegram cadastrado!");
    }
  });
```

### **5.3 Listar Usuários Cadastrados:**

```javascript
fetch("/api/alertas/listar", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({}),
})
  .then((r) => r.json())
  .then((data) => {
    console.log("👥 USUÁRIOS:", data);
    console.log(`Total: ${data.total_usuarios} usuários`);
  });
```

### **5.4 Testar Notificação:**

```javascript
fetch("/api/alertas/notify", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    titulo: "🎉 TESTE - Resultado Final Mestrado CCT",
    link: "https://uenf.br/teste-telegram",
    tipo: "resultado",
  }),
})
  .then((r) => r.json())
  .then((data) => {
    console.log("📱 RESULTADO:", data);
    if (data.sent_count > 0) {
      console.log("🎉 FUNCIONOU! Telegram enviado!");
    }
  });
```

---

## 👥 **COMO ORIENTAR OS USUÁRIOS FINAIS:**

### **📋 Instruções para seus usuários:**

**"Para receber alertas da UENF, faça assim:"**

1. **📱 PRIMEIRO:** Abra o Telegram e procure por `@seubot_bot`
2. **▶️ Clique em "START"** (é obrigatório!)
3. **💻 DEPOIS:** Vá no site https://seusite.vercel.app
4. **🔵 Clique** no botão azul no canto inferior direito
5. **✏️ Digite** seu nome de usuário do Telegram (ex: @joao123)
6. **✅ Pronto!** Você receberá alertas automáticos

**⚠️ Aviso importante:** Se você não fizer o passo 1 e 2 primeiro, os alertas NÃO chegarão!

### **📄 Exemplo de aviso no seu site:**

```html
<div class="alert alert-info">
  ⚠️ <strong>Antes de se cadastrar:</strong> Procure <code>@seubot_bot</code> no
  Telegram e clique "START"
</div>
```

---

## 💬 **COMO AS MENSAGENS APARECEM:**

### **📋 Edital de Extensão:**

```
🎓 *EDITAL DE EXTENSÃO UENF!*

📋 Edital de Extensão Universitária - Bolsas 2025

🔗 [Acessar Edital](https://uenf.br/editais/extensao)

💡 Oportunidade de extensão universitária!

💻 [Ver mais bolsas](https://seusite.vercel.app)

_Para cancelar alertas, digite /stop_
```

### **🏆 Resultado Publicado:**

```
🏆 *RESULTADO PUBLICADO UENF!*

📋 Lista de Aprovados - Mestrado CCT

🔗 [Acessar Edital](https://uenf.br/editais/resultado)

🔍 Confira se você foi aprovado(a)!

💻 [Ver mais bolsas](https://seusite.vercel.app)

_Para cancelar alertas, digite /stop_
```

---

## 🔄 **COMO FUNCIONA O FLUXO AUTOMÁTICO:**

### **⏰ Cronograma Diário:**

1. **04:00 AM** - Vercel Cron executa `/api/scrape?secret=...`
2. **Sistema detecta** novos editais de extensão/resultado
3. **Para cada novo edital:**
   - Classifica automaticamente o tipo
   - Se for `extensao` ou `resultado` → envia alertas
   - Se for `outros` → apenas salva no banco
4. **Para cada usuário ativo:**
   - Busca `telegram_id` na tabela `telegram_alerts`
   - Envia mensagem via Telegram API
   - Log do resultado (sucesso/erro)

### **🎯 Detecção Automática de Tipos:**

- **Extensão:** "extensão", "discente", "voluntário"
- **Resultado:** "resultado", "classificação", "aprovados"
- **Outros:** Qualquer coisa que não se encaixe acima

---

## 🛠️ **TROUBLESHOOTING:**

### **❌ "Telegram simulado"**

**Causa:** Token não configurado  
**Solução:**

1. Verifique se `TELEGRAM_BOT_TOKEN` está no Vercel
2. Faça redeploy: `git commit --allow-empty -m "redeploy" && git push`

### **❌ "Telegram API error: Unauthorized"**

**Causa:** Token inválido  
**Solução:**

1. Volte no @BotFather
2. Digite `/token` e escolha seu bot
3. Copie o novo token
4. Atualize no Vercel

### **❌ "Chat not found" - MAIS COMUM**

**Causa:** Usuário nunca conversou com o bot (regra do Telegram)  
**Solução OBRIGATÓRIA:**

1. **ANTES de se cadastrar** no site, cada usuário deve:
2. **Procurar o bot:** `@seubot_bot` no Telegram
3. **Clicar "START"** ou enviar qualquer mensagem
4. **SÓ DEPOIS** se cadastrar no site
5. **Importante:** Sem este passo, o bot NÃO consegue enviar mensagens

**⚠️ Este é o erro mais comum! Usuários DEVEM iniciar conversa primeiro.**

### **❌ Bot não responde**

**Causa:** Bot não implementa comandos ainda (só envia mensagens)  
**Solução:**

- Isso é normal! O bot só **ENVIA** notificações
- Não precisa responder comandos por enquanto
- No futuro pode implementar `/start`, `/stop`, etc.

---

## 📊 **ENDPOINTS DISPONÍVEIS:**

### **POST /api/alertas/telegram**

Cadastra usuário para receber alertas.

```json
{
  "telegram": "@joao123"
}
```

### **POST /api/alertas/notify**

Testa envio de notificação.

```json
{
  "titulo": "Teste de Edital",
  "link": "https://uenf.br/teste",
  "tipo": "resultado"
}
```

### **POST /api/alertas/test-detection**

Testa detecção automática de tipo.

```json
{
  "titulo": "Resultado Final - Mestrado CCT"
}
```

### **POST /api/alertas/listar**

Lista usuários cadastrados (para debug).

```json
{}
```

---

## 💰 **CUSTOS:**

- **Telegram Bot API:** **100% GRATUITO**
- **Vercel Hosting:** Gratuito até 100GB de bandwidth
- **Supabase Database:** Gratuito até 500MB
- **Total:** **R$ 0,00/mês** ✅

---

## 🎉 **VANTAGENS DO TELEGRAM VS WHATSAPP:**

| Aspecto               | WhatsApp              | Telegram            |
| --------------------- | --------------------- | ------------------- |
| **Custo**             | R$ 0,10/msg (Twilio)  | **R$ 0,00**         |
| **Setup**             | QR codes, Baileys     | **3 minutos**       |
| **Confiabilidade**    | Dependente de conexão | **API oficial**     |
| **Exposição pessoal** | Seu número            | **Bot dedicado**    |
| **Manutenção**        | Alta (desconexões)    | **Zero**            |
| **Recursos**          | Texto simples         | **Markdown, links** |
| **Limites**           | Variados              | **Ilimitado**       |

---

## ✅ **CHECKLIST FINAL:**

- [ ] ✅ Bot criado no @BotFather
- [ ] ✅ Token salvo no Vercel
- [ ] ✅ Deploy realizado
- [ ] ✅ Frontend testado (botão azul)
- [ ] ✅ Cadastro testado via API
- [ ] ✅ Notificação testada
- [ ] ✅ Bot funcionando 100%

---

## 🚀 **PRÓXIMOS PASSOS (OPCIONAIS):**

### **Melhorias Futuras:**

1. **Comando /start** - Mensagem de boas-vindas
2. **Comando /stop** - Descadastrar alertas
3. **Comando /help** - Lista de comandos
4. **Webhook** - Bot responde mensagens
5. **Grupos/Canais** - Alertas em canais públicos
6. **Inline Keyboard** - Botões nas mensagens

### **Para implementar comandos:**

```python
# Adicionar no api/index.py
def handle_telegram_webhook(update):
    """Processa mensagens recebidas do Telegram"""
    message = update.get('message', {})
    chat_id = message.get('chat', {}).get('id')
    text = message.get('text', '')

    if text == '/start':
        send_telegram_message(chat_id, """
🎓 *Bem-vindo ao UENF Alertas!*

Você receberá notificações sobre:
• Editais de extensão
• Resultados de seleções

Digite /stop para parar os alertas.
        """)
    elif text == '/stop':
        # Desativar usuário na tabela
        pass
```

---

**🎯 TELEGRAM = SOLUÇÃO PERFEITA PARA ALERTAS UENF!**

**✅ Gratuito, confiável e profissional!** 📱
