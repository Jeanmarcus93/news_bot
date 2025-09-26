# 🚀 Deploy do Bot de Notícias no Render

## 📋 Pré-requisitos

1. **Conta no Render.com** (gratuita)
2. **Token do Telegram Bot** (obtido com @BotFather)
3. **Chat ID do Telegram** (opcional, para notificações)

## 🔧 Configuração

### 1. Criar Bot no Telegram
1. Fale com @BotFather no Telegram
2. Use `/newbot` e siga as instruções
3. Copie o **TOKEN** fornecido
4. (Opcional) Configure o bot com `/setdescription` e `/setabouttext`

### 2. Obter Chat ID (Opcional)
1. Envie uma mensagem para seu bot
2. Acesse: `https://api.telegram.org/bot<SEU_TOKEN>/getUpdates`
3. Procure por `"chat":{"id":` e copie o número

## 🌐 Deploy no Render

### Opção 1: Deploy como Web Service (Recomendado)

1. **Acesse [Render.com](https://render.com)**
2. **Clique em "New +" → "Web Service"**
3. **Conecte seu repositório GitHub**
4. **Configure o serviço:**

```
Name: news-bot-rs
Environment: Python 3
Build Command: pip install -r requirements.txt
Start Command: python web_app.py
```

5. **Adicione as variáveis de ambiente:**
   - `TELEGRAM_TOKEN`: Seu token do bot
   - `TELEGRAM_CHAT_ID`: Seu chat ID (opcional)

6. **Clique em "Create Web Service"**

### Opção 2: Deploy como Worker Service

1. **Acesse [Render.com](https://render.com)**
2. **Clique em "New +" → "Background Worker"**
3. **Conecte seu repositório GitHub**
4. **Configure o serviço:**

```
Name: news-bot-worker
Environment: Python 3
Build Command: pip install -r requirements.txt
Start Command: python start.py
```

5. **Adicione as variáveis de ambiente:**
   - `TELEGRAM_TOKEN`: Seu token do bot
   - `TELEGRAM_CHAT_ID`: Seu chat ID (opcional)

6. **Clique em "Create Background Worker"**

## 📁 Arquivos de Configuração

O projeto já inclui os arquivos necessários:

- `render-web.yaml` - Configuração para Web Service
- `render.yaml` - Configuração para Worker Service
- `requirements.txt` - Dependências Python
- `runtime.txt` - Versão do Python
- `web_app.py` - Aplicação Flask com bot em background
- `start.py` - Script de inicialização do bot

## 🔍 Verificação do Deploy

### Para Web Service:
- Acesse a URL fornecida pelo Render
- Deve mostrar: `{"status": "online", "bot_running": true}`
- Endpoint `/health` deve retornar status healthy

### Para Worker Service:
- Verifique os logs no dashboard do Render
- Deve mostrar: `🤖 Bot iniciado com sucesso!`
- Teste enviando `/start` para seu bot no Telegram

## 🛠️ Troubleshooting

### Problemas Comuns:

1. **Bot não responde:**
   - Verifique se `TELEGRAM_TOKEN` está correto
   - Confirme que o bot foi iniciado com @BotFather

2. **Erro de dependências:**
   - Verifique se `requirements.txt` está atualizado
   - Confirme que a versão do Python está correta

3. **Serviço para de funcionar:**
   - Render suspende serviços gratuitos após inatividade
   - Use Web Service com keep-alive automático

4. **Logs de erro:**
   - Acesse "Logs" no dashboard do Render
   - Verifique se todas as variáveis de ambiente estão configuradas

## 📊 Monitoramento

### Endpoints disponíveis (Web Service):
- `/` - Status geral do bot
- `/health` - Health check
- `/start` - Iniciar bot manualmente

### Logs:
- Acesse "Logs" no dashboard do Render
- Monitore o status do bot e erros

## 🔄 Atualizações

Para atualizar o bot:
1. Faça push das mudanças para o GitHub
2. O Render fará deploy automático
3. Monitore os logs para confirmar a atualização

## 💡 Dicas

1. **Use Web Service** para melhor estabilidade
2. **Configure auto-deploy** para atualizações automáticas
3. **Monitore os logs** regularmente
4. **Teste localmente** antes do deploy
5. **Mantenha o repositório atualizado**

## 🆘 Suporte

Se encontrar problemas:
1. Verifique os logs no Render
2. Teste localmente com `python web_app.py`
3. Confirme as variáveis de ambiente
4. Verifique a conectividade do bot com o Telegram
