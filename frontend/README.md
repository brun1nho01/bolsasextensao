# Sistema UENF Bolsas de Extensão

Sistema moderno para consulta e gerenciamento de bolsas de extensão da Universidade Estadual do Norte Fluminense Darcy Ribeiro (UENF).

## ✨ Funcionalidades

- 🔍 **Busca Avançada**: Filtros por tipo, centro, valor da bolsa e status
- 📱 **Interface Responsiva**: Design moderno otimizado para desktop e mobile
- 🔔 **Sistema de Alertas**: Notificações automáticas via Telegram para novos editais
- 📊 **Dashboard Analytics**: Visualizações e estatísticas em tempo real
- 🎯 **Ranking de Bolsas**: Sistema de visualização das melhores oportunidades
- ⚡ **Atualizações Automáticas**: Scraping automático de novos editais

## 🚀 Tecnologias

### Frontend

- **React 18** com TypeScript
- **Vite** para build otimizado
- **Tailwind CSS** para estilização
- **Radix UI** para componentes acessíveis
- **React Query** para gerenciamento de estado
- **React Router** para navegação

### Backend

- **Python** com Flask
- **Supabase** para banco de dados
- **Telegram Bot API** para notificações
- **Beautiful Soup** para web scraping
- **Vercel** para deploy e hosting

## 🛠️ Desenvolvimento Local

### Pré-requisitos

- Node.js 18+
- Python 3.9+
- Git

### Instalação

```bash
# Clonar o repositório
git clone <seu-repositorio>
cd projeto-scraper-uenfinovador

# Instalar dependências do frontend
cd frontend
npm install

# Executar em modo desenvolvimento
npm run dev
```

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz com:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

## 📁 Estrutura do Projeto

```
projeto-scraper-uenfinovador/
├── api/                    # Backend Python (Vercel Functions)
│   ├── index.py           # API principal
│   └── requirements.txt   # Dependências Python
├── frontend/              # Frontend React
│   ├── src/
│   │   ├── components/    # Componentes React
│   │   ├── pages/        # Páginas da aplicação
│   │   └── lib/          # Utilitários e configurações
│   ├── package.json
│   └── vite.config.ts
└── vercel.json           # Configuração de deploy
```

## 🔄 Deploy

O projeto está configurado para deploy automático no Vercel:

1. Conecte seu repositório ao Vercel
2. Configure as variáveis de ambiente
3. O deploy acontece automaticamente a cada push

## 🤖 Sistema de Alertas Telegram

Para usar o sistema de notificações:

1. Procure por `@uenf_alertas_bot` no Telegram
2. Envie `/start` para obter seu Chat ID
3. Cadastre seu Chat ID no sistema
4. Receba alertas automáticos sobre novos editais

## 📊 APIs Disponíveis

- `GET /api/bolsas` - Lista todas as bolsas
- `GET /api/bolsas/{id}` - Detalhes de uma bolsa específica
- `GET /api/analytics` - Estatísticas do sistema
- `GET /api/editais` - Lista de editais
- `POST /api/alertas/notify` - Enviar notificação
- `POST /api/telegram/webhook` - Webhook do Telegram

## 🎯 Roadmap

- [ ] Sistema de favoritos
- [ ] Exportação para PDF/Excel
- [ ] Notificações por email
- [ ] API pública documentada
- [ ] Aplicativo mobile nativo

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto é desenvolvido para a UENF - Universidade Estadual do Norte Fluminense Darcy Ribeiro.

## 🔧 Suporte

Para suporte técnico ou dúvidas sobre o sistema, entre em contato através dos canais oficiais da UENF.

---

**Sistema UENF Bolsas** - Democratizando o acesso às oportunidades de extensão universitária.
