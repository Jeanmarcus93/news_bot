# 🔓 Como Liberar o Repositório para o Render

## 📋 Passo a Passo Completo

### 1. Verificar se o Repositório está Público

**No GitHub:**
1. Acesse: https://github.com/Jeanmarcus93/news_bot
2. Clique em **"Settings"** (aba superior)
3. Role até **"Danger Zone"** (final da página)
4. Se estiver **"Private"**, clique em **"Change repository visibility"**
5. Selecione **"Make public"** e confirme

### 2. Conectar ao Render

**No Render.com:**
1. Acesse: https://render.com
2. Faça login ou crie uma conta
3. Clique em **"New +"** → **"Web Service"**

### 3. Conectar Repositório

**Na tela de criação:**
1. **Connect a repository:**
   - Clique em **"Connect GitHub"** ou **"Connect GitLab"**
   - Autorize o Render a acessar seus repositórios
   - Selecione: **Jeanmarcus93/news_bot**

2. **Configure o serviço:**
   ```
   Name: news-bot-rs
   Environment: Python 3
   Region: Oregon (US West)
   Branch: master
   Root Directory: (deixe vazio)
   Build Command: pip install -r requirements.txt
   Start Command: python web_app.py
   ```

### 4. Configurar Variáveis de Ambiente

**Na seção "Environment Variables":**
1. Clique em **"Add Environment Variable"**
2. Adicione:
   ```
   Key: TELEGRAM_TOKEN
   Value: [SEU_TOKEN_DO_BOT]
   ```
3. Clique em **"Add Environment Variable"** novamente
4. Adicione:
   ```
   Key: TELEGRAM_CHAT_ID
   Value: [SEU_CHAT_ID] (opcional)
   ```

### 5. Configurações Avançadas

**Na seção "Advanced":**
- **Auto-Deploy:** ✅ Yes
- **Health Check Path:** `/health`
- **Plan:** Free

### 6. Criar o Serviço

1. Clique em **"Create Web Service"**
2. Aguarde o build (pode levar 5-10 minutos)
3. Monitore os logs em tempo real

## 🔍 Verificação

### 1. Logs do Build
```
INFO:__main__:🚀 Iniciando aplicação web + bot...
INFO:__main__:🤖 Iniciando bot em thread separada...
INFO:__main__:🤖 Bot iniciado com sucesso!
INFO:__main__:📱 Use /start no Telegram para começar a usar o bot
INFO:__main__:⏰ Configurando atualização automática a cada 60 minutos...
INFO:__main__:✅ Scheduler iniciado - Atualização automática ativa!
```

### 2. Health Check
- Acesse a URL fornecida pelo Render
- Deve mostrar: `{"status": "online", "bot_running": true}`

### 3. Teste do Bot
- Envie `/start` para seu bot no Telegram
- Deve responder com a mensagem de boas-vindas

## 🛠️ Troubleshooting

### Problema: "Repository not found"
**Solução:**
1. Verifique se o repositório está público
2. Confirme se o nome do repositório está correto
3. Re-autorize o Render no GitHub

### Problema: "Build failed"
**Solução:**
1. Verifique se `requirements.txt` está correto
2. Confirme se a versão do Python está especificada
3. Verifique os logs de build para erros específicos

### Problema: "Bot not responding"
**Solução:**
1. Verifique se `TELEGRAM_TOKEN` está correto
2. Confirme se o bot foi iniciado com @BotFather
3. Verifique os logs do serviço

### Problema: "Service sleeping"
**Solução:**
1. Render suspende serviços gratuitos após inatividade
2. O sistema de keep-alive deve reativar automaticamente
3. Acesse a URL para "acordar" o serviço

## 📊 Monitoramento

### 1. Dashboard do Render
- Acesse: https://dashboard.render.com
- Clique no seu serviço
- Monitore logs, métricas e status

### 2. Logs em Tempo Real
- Clique em **"Logs"** no dashboard
- Monitore erros e status do bot

### 3. Health Check
- Endpoint: `https://seu-app.onrender.com/health`
- Deve retornar status healthy

## 🔄 Atualizações

### Deploy Automático
- Faça push para o GitHub
- O Render fará deploy automático
- Monitore os logs para confirmar

### Deploy Manual
- No dashboard do Render
- Clique em **"Manual Deploy"**
- Selecione o commit desejado

## 💡 Dicas Importantes

1. **Mantenha o repositório público** para o Render acessar
2. **Use Web Service** para melhor estabilidade
3. **Monitore os logs** regularmente
4. **Configure auto-deploy** para atualizações automáticas
5. **Teste localmente** antes do deploy

## 🆘 Suporte

Se encontrar problemas:
1. Verifique os logs no Render
2. Confirme as configurações do repositório
3. Teste localmente com `python web_app.py`
4. Verifique as variáveis de ambiente

## 📱 URLs Importantes

- **Render Dashboard:** https://dashboard.render.com
- **GitHub Repository:** https://github.com/Jeanmarcus93/news_bot
- **BotFather:** https://t.me/BotFather
- **Telegram API:** https://api.telegram.org/bot<TOKEN>/getUpdates
