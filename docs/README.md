# Bot de Notícias RS - Crimes e Apreensões

Um bot do Telegram que monitora automaticamente notícias sobre apreensão de drogas, armas, tráfico e facções no Rio Grande do Sul, buscando informações em portais oficiais e redes sociais.

## 🎯 Funcionalidades

- **Monitoramento Automático**: Busca notícias a cada 30 minutos
- **Múltiplas Fontes**: Portais oficiais e veículos de comunicação
- **Categorização Inteligente**: Classifica notícias por tipo (drogas, armas, tráfico, facções)
- **Banco de Dados**: Armazena notícias e evita duplicatas
- **Comandos do Telegram**: Interface amigável para consultar notícias

## 📰 Fontes Monitoradas

### Portais Oficiais
- **PRF** (Polícia Rodoviária Federal)
- **PF** (Polícia Federal) 
- **Brigada Militar RS**
- **Polícia Civil RS**

### Veículos de Comunicação
- **G1 Rio Grande do Sul**
- **Zero Hora**
- **Correio do Povo**

### Redes Sociais

## 🚀 Instalação

### 1. Clone o repositório
```bash
git clone <url-do-repositorio>
cd news_bot
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente
Copie o arquivo de exemplo e configure suas credenciais:
```bash
cp env_example.txt .env
```

Edite o arquivo `.env` com suas credenciais:
```env
# Telegram Bot Configuration
TELEGRAM_TOKEN=seu_token_do_telegram_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui

```

### 4. Obter Token do Telegram

1. Fale com [@BotFather](https://t.me/botfather) no Telegram
2. Use o comando `/newbot`
3. Siga as instruções para criar seu bot
4. Copie o token fornecido para o arquivo `.env`

### 5. Obter Chat ID (opcional)

Para receber notícias automaticamente em um chat específico:

1. Adicione seu bot ao chat desejado
2. Envie uma mensagem para o bot
3. Acesse: `https://api.telegram.org/bot<SEU_TOKEN>/getUpdates`
4. Encontre o `chat.id` na resposta


## 🎮 Como Usar

### Iniciar o Bot
```bash
python main.py
```

### Comandos do Telegram

- `/start` - Mensagem de boas-vindas
- `/help` - Lista de comandos disponíveis
- `/latest` - Últimas 10 notícias encontradas
- `/category` - Filtrar notícias por categoria
- `/stats` - Estatísticas do bot
- `/search <termo>` - Buscar notícias por termo específico
- `/refresh` - Força uma nova busca por notícias

### Categorias Disponíveis

- 💊 **Drogas** - Apreensões de substâncias ilícitas
- 🔫 **Armas** - Apreensões de armas de fogo
- 🚨 **Tráfico** - Operações contra tráfico
- 👥 **Facções** - Ações contra organizações criminosas

## 📁 Estrutura do Projeto

```
news_bot/
├── main.py                 # Arquivo principal
├── config.py              # Configurações
├── database.py            # Gerenciamento do banco de dados
├── telegram_bot.py        # Bot do Telegram
├── news_scrapers.py       # Scrapers para portais de notícias
├── scheduler.py           # Sistema de agendamento
├── requirements.txt       # Dependências Python
├── env_example.txt        # Exemplo de configuração
├── README.md             # Este arquivo
└── news_bot.log          # Arquivo de log (criado automaticamente)
```

## ⚙️ Configurações

### Intervalos de Busca
- **Busca de notícias**: A cada 30 minutos (configurável em `config.py`)
- **Limpeza de dados**: Diariamente às 02:00
- **Notificações automáticas**: A cada 2 horas

### Palavras-chave Monitoradas
O bot monitora automaticamente termos relacionados a:
- Drogas (cocaína, maconha, crack, etc.)
- Armas (arma de fogo, munição, explosivos, etc.)
- Tráfico (organização criminosa, cartel, etc.)
- Facções (PCC, Comando Vermelho, milícia, etc.)

## 🔧 Desenvolvimento

### Executar Testes
```bash
# Testar scraper de notícias
python news_scrapers.py


# Testar agendador
python scheduler.py
```

### Logs
Os logs são salvos em `news_bot.log` e também exibidos no console.

## 📊 Banco de Dados

O bot usa SQLite para armazenar:
- Notícias encontradas
- Configurações
- Logs de atividade

O banco é criado automaticamente em `news_bot.db`.

## 🛡️ Considerações de Segurança

- **Rate Limiting**: O bot respeita limites de requisições dos sites
- **User-Agent**: Usa headers apropriados para web scraping
- **Tratamento de Erros**: Continua funcionando mesmo com falhas em fontes específicas
- **Logs**: Registra todas as atividades para auditoria

## 📝 Licença

Este projeto é para fins educacionais e de monitoramento de informações públicas.

## 🤝 Contribuições

Contribuições são bem-vindas! Por favor:

1. Faça um fork do projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Abra um Pull Request

## ⚠️ Aviso Legal

Este bot monitora apenas informações públicas disponíveis em portais oficiais e veículos de comunicação. É responsabilidade do usuário garantir que o uso esteja em conformidade com os termos de serviço das plataformas monitoradas e com a legislação aplicável.

## 📞 Suporte

Para suporte ou dúvidas, abra uma issue no repositório ou entre em contato através do Telegram.


