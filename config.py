import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')  # Chat onde o bot enviará as notícias


# Twitter/X API Configuration (opcional)
TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_SECRET = os.getenv('TWITTER_ACCESS_SECRET')

# Database Configuration
DATABASE_PATH = 'news_bot.db'

# Search Configuration
SEARCH_KEYWORDS = [
    # Drogas
    'apreensão drogas', 'cocaína', 'maconha', 'crack', 'ecstasy',
    'heroína', 'LSD', 'drogas ilícitas', 'entorpecentes',
    
    # Armas
    'apreensão armas', 'arma de fogo', 'munição', 'explosivo',
    'granada', 'fuzil', 'pistola', 'revólver',
    
    # Tráfico
    'tráfico drogas', 'tráfico armas', 'organização criminosa',
    'cartel', 'traficante', 'contrabando',
    
    # Facções
    'PCC', 'Comando Vermelho', 'Terceiro Comando',
    'Amigos dos Amigos', 'milícia', 'facção criminosa',
    
    # GAECO e operações especiais
    'GAECO', 'lavagem de dinheiro', 'contas abertas',
    'operação policial', 'investigação criminal'
]

RS_LOCATIONS = [
    'Rio Grande do Sul', 'RS', 'Porto Alegre', 'Caxias do Sul',
    'Pelotas', 'Canoas', 'Santa Maria', 'Gravataí', 'Viamão',
    'Novo Hamburgo', 'São Leopoldo', 'Rio Grande', 'Alvorada',
    'Passo Fundo', 'Sapucaia do Sul', 'Uruguaiana', 'Santa Cruz do Sul'
]

# Portal URLs
PORTAL_URLS = {
    'PRF': [
        'https://www.gov.br/prf/pt-br/acesso-a-informacao/acoes-e-programas/noticias/'
    ],
    'PF': [
        'https://www.gov.br/pf/pt-br/assuntos/noticias/'
    ],
    'Brigada_Militar': [
        'https://www.brigadamilitar.rs.gov.br/noticias/'
    ],
    'Policia_Civil': [
        'https://www.pc.rs.gov.br/noticias/'
    ],
    'Policia_Civil_SC': [
        'https://pc.sc.gov.br/noticias/'
    ],
    'Policia_Civil_PR': [
        'https://www.policiacivil.pr.gov.br/noticias/'
    ]
}

# Update intervals (in minutes)
UPDATE_INTERVAL = 30  # Buscar notícias a cada 30 minutos
CLEANUP_INTERVAL = 24 * 60  # Limpar notícias antigas a cada 24 horas
