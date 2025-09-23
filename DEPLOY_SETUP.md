# 🚀 Configuração de Deploy na Vercel

## 📋 Variáveis de Ambiente Necessárias

Configure essas variáveis no painel da Vercel:

### **Supabase (Obrigatório)**

```
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua_chave_publica_supabase
```

### **Gemini AI (Obrigatório)**

```
GEMINI_API_KEYS=chave1,chave2,chave3
```

_Múltiplas chaves separadas por vírgula para rotação automática_

### **Segurança (Obrigatório)**

```
SCRAPER_API_KEY=sua_chave_secreta_aqui
```

### **CORS (Opcional)**

```
CORS_ORIGINS=https://seu-dominio.vercel.app
```

## 🔧 Passos para Deploy

1. **Fazer push das alterações**

   ```bash
   git add .
   git commit -m "Configure Vercel for FastAPI backend"
   git push
   ```

2. **Configurar variáveis na Vercel**

   - Acesse o painel da Vercel
   - Vá em Settings > Environment Variables
   - Adicione todas as variáveis acima

3. **Redesployar**
   - O deploy será automático após o push
   - Ou force um redeploy no painel da Vercel

## 🧪 Testar a API

Após o deploy, teste:

- `https://seu-app.vercel.app/api/` → Deve retornar "Bem-vindo à API"
- `https://seu-app.vercel.app/api/bolsas` → Deve retornar lista de bolsas

## ❓ Problemas Comuns

- **Backend não responde**: Verifique se as variáveis de ambiente estão configuradas
- **Erro 500**: Verifique os logs da Vercel na aba Functions
- **CORS Error**: Configure CORS_ORIGINS com sua URL do Vercel
