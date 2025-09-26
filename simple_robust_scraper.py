#!/usr/bin/env python3
"""
Scraper robusto simplificado para sites oficiais de segurança pública
Foco em fontes oficiais e confiáveis
"""

import requests
from bs4 import BeautifulSoup
import time
import logging
from datetime import datetime, timedelta
import re

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleRobustScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Configurações para ignorar problemas de SSL
        self.session.verify = False
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Configurações de timeout e retry
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
    def get_scraping_configs(self):
        """
        Configurações de scraping apenas para fontes oficiais de segurança
        """
        return [
            {
                'name': 'PRF Nacional',
                'url': 'https://www.gov.br/prf/pt-br/noticias/ultimas/',
                'selectors': {
                    'articles': 'h2',  # PRF usa h2 para notícias
                    'title': 'h2 a',  # Títulos são links dentro de h2
                    'link': 'h2 a',  # Links das notícias
                    'date': '.documentByLine, .summary-view-icon, .date'  # Datas das notícias
                },
                'rate_limit': 2.0
            },
            {
                'name': 'PF Nacional',
                'url': 'https://www.gov.br/pf/pt-br/assuntos/noticias/ultimas-noticias/',
                'selectors': {
                    'articles': 'article, .item, .noticia, .materia',
                    'title': 'h3 a, h2 a, .titulo a, .materia-titulo a',
                    'link': 'h3 a, h2 a, .titulo a, .materia-titulo a',
                    'date': '.data, .date, time, .materia-data'
                },
                'rate_limit': 2.0
            },
            {
                'name': 'MPRS',
                'url': 'https://www.mprs.mp.br/noticias/',
                'selectors': {
                    'articles': 'h2, a[href*="/noticias/"]',  # h2 para títulos e links diretos para notícias
                    'title': 'h2 a, a[href*="/noticias/"]',   # Títulos são links dentro de h2 ou links diretos
                    'link': 'h2 a, a[href*="/noticias/"]',    # Links das notícias
                    'date': '.data, .date, time, .materia-data, .publicado'  # Datas das notícias
                },
                'rate_limit': 2.0
            },
            {
                'name': 'Polícia Civil',
                'url': 'https://www.pc.rs.gov.br/noticias/',
                'selectors': {
                    'articles': 'h3, h4, .item, .noticia, article',  # Múltiplos selectors para capturar
                    'title': 'h3 a, h4 a, .titulo a, a',  # Títulos das notícias
                    'link': 'h3 a, h4 a, .titulo a, a',  # Links das notícias
                    'date': '.data, .date, time, .timestamp'  # Datas das notícias
                },
                'rate_limit': 2.0
            },
            {
                'name': 'Brigada Militar',
                'url': 'https://www.brigadamilitar.rs.gov.br/noticias/',
                'selectors': {
                    'articles': 'h3',  # Notícias estão nos h3
                    'title': 'h3 a',  # Títulos são links dentro de h3
                    'link': 'h3 a',  # Links das notícias
                    'date': '.data, .date, time, .timestamp, .news-date'  # Datas das notícias
                },
                'rate_limit': 3.0
            },
            {
                'name': 'PM SC',
                'url': 'https://www.pm.sc.gov.br/noticias/',
                'selectors': {
                    'articles': 'a[href*="/noticias/"]',  # Links diretos para notícias
                    'title': 'a[href*="/noticias/"]',  # Título é o texto do link
                    'link': 'a[href*="/noticias/"]',  # Link direto
                    'date': '.data, .date, time, .timestamp'
                },
                'rate_limit': 2.0
            },
            {
                'name': 'PM PR',
                'url': 'https://www.pmpr.pr.gov.br/Noticias/',
                'selectors': {
                    'articles': 'article, .item, .noticia, .materia',
                    'title': 'h3 a, h2 a, .titulo a, .materia-titulo a',
                    'link': 'h3 a, h2 a, .titulo a, .materia-titulo a',
                    'date': '.data, .date, time, .materia-data'
                },
                'rate_limit': 2.0
            },
            {
                'name': 'DOF MS',
                'url': 'https://www.dof.ms.gov.br/noticias/',
                'selectors': {
                    'articles': '.card, .card-body, .post',
                    'title': 'h5.card-title a, h5.card-title, .card-title a',
                    'link': 'h5.card-title a, .card-title a, a',
                    'date': '.card-text small, .date, time, .timestamp'
                },
                'rate_limit': 2.0
            },
            {
                'name': 'PC SC',
                'url': 'https://pc.sc.gov.br/noticias/',
                'selectors': {
                    'articles': 'h3, article',
                    'title': 'h3 a, h3',
                    'link': 'h3 a, h3',
                    'date': '.data, .date, time, .timestamp'
                },
                'rate_limit': 2.0
            },
            {
                'name': 'PC PR',
                'url': 'https://www.policiacivil.pr.gov.br/noticias/',
                'selectors': {
                    'articles': 'article, .item, h3, h4',
                    'title': 'h3 a, h4 a, .titulo a',
                    'link': 'h3 a, h4 a, .titulo a',
                    'date': 'time, .date, .data, .timestamp'
                },
                'rate_limit': 2.0
            }
        ]

    def is_relevant_news(self, title, content=""):
        """
        Verifica se a notícia é relevante baseada no título e conteúdo
        Foco em crimes, operações policiais, tráfico, etc.
        """
        if not title:
            return False
            
        # Converte para minúsculas para comparação
        title_lower = title.lower()
        content_lower = content.lower()
        text_to_check = f"{title_lower} {content_lower}"
        
        # Palavras-chave específicas e precisas
        target_keywords = [
            'drogas', 'armas', 'maconha', 'cocaína', 'ecstasy', 'skunk', 
            'apreensão', 'prisão', 'tráfico', 'facção', 'operação',
            'gaeco', 'lavagem de dinheiro', 'contas abertas', 'investigação criminal',
            'bunker', 'entorpecentes', 'desmantela', 'grupo criminoso', 'narcóticos', 'substâncias ilícitas'
        ]
        
        # Verifica se alguma palavra-chave está presente
        for keyword in target_keywords:
            if keyword in text_to_check:
                return True
                
        return False

    def extract_news_data(self, element, selectors, base_url):
        """
        Extrai dados da notícia de um elemento HTML
        """
        try:
            # Título
            title_elem = element.select_one(selectors['title'])
            if not title_elem:
                # Tenta pegar o texto do próprio elemento se não encontrar título
                title = element.get_text(strip=True)
            else:
                title = title_elem.get_text(strip=True)
            
            if not title or len(title) < 10:
                return None
            
            # Link
            link_elem = element.select_one(selectors['link'])
            if link_elem and link_elem.get('href'):
                link = link_elem['href']
                if link.startswith('/'):
                    # Remove /noticias/ da base_url se o link já contém
                    base_clean = base_url.rstrip('/')
                    if base_clean.endswith('/noticias') and link.startswith('/noticias/'):
                        link = base_clean.replace('/noticias', '') + link
                    else:
                        link = base_clean + link
                elif not link.startswith('http'):
                    link = base_url.rstrip('/') + '/' + link
            else:
                # Se não encontrar link, usa o próprio elemento
                if element.get('href'):
                    link = element['href']
                    if link.startswith('/'):
                        # Remove /noticias/ da base_url se o link já contém
                        base_clean = base_url.rstrip('/')
                        if base_clean.endswith('/noticias') and link.startswith('/noticias/'):
                            link = base_clean.replace('/noticias', '') + link
                        else:
                            link = base_clean + link
                    elif not link.startswith('http'):
                        link = base_url.rstrip('/') + '/' + link
                else:
                    link = base_url
            
            # Data (tenta extrair, mas não é obrigatória)
            date_elem = element.select_one(selectors['date'])
            date_str = ""
            if date_elem:
                date_str = date_elem.get_text(strip=True)
            
            return {
                'title': title,
                'link': link,
                'date': date_str,
                'source': base_url
            }
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados: {e}")
            return None

    def scrape_site(self, config):
        """
        Faz scraping de um site específico
        """
        news_list = []
        
        try:
            logger.info(f"🔄 Fazendo scraping: {config['name']}")
            
            # Rate limiting
            time.sleep(config.get('rate_limit', 2.0))
            
            # Tenta fazer a requisição com retry automático
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.session.get(config['url'], timeout=30)
                    response.raise_for_status()
                    break
                except (requests.exceptions.SSLError, requests.exceptions.ConnectionError, 
                        requests.exceptions.ConnectionResetError, requests.exceptions.Timeout,
                        requests.exceptions.ChunkedEncodingError, requests.exceptions.ConnectTimeout,
                        requests.exceptions.ReadTimeout, requests.exceptions.HTTPError) as e:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Backoff exponencial: 2s, 4s, 8s
                        logger.warning(f"Tentativa {attempt + 1} falhou para {config['name']}: {e}")
                        logger.info(f"⏳ Aguardando {wait_time}s antes da próxima tentativa...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"❌ Falha final ao acessar {config['name']} após {max_retries} tentativas: {e}")
                        return []
                except Exception as e:
                    logger.error(f"❌ Erro inesperado ao acessar {config['name']}: {e}")
                    return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Busca por artigos/notícias
            articles = soup.select(config['selectors']['articles'])
            logger.info(f"📰 Encontrados {len(articles)} elementos")
            
            for article in articles[:20]:  # Limita a 20 notícias por site
                news_data = self.extract_news_data(article, config['selectors'], config['url'])
                
                if news_data and self.is_relevant_news(news_data['title']):
                    # Determina categoria baseada na palavra-chave
                    title_lower = news_data['title'].lower()
                    
                    if any(word in title_lower for word in ['gaeco', 'lavagem', 'investigação']):
                        news_data['category'] = "investigação"
                    elif any(word in title_lower for word in ['drogas', 'maconha', 'cocaína', 'ecstasy', 'skunk', 'bunker', 'entorpecentes', 'narcóticos']):
                        news_data['category'] = "drogas"
                    elif 'armas' in title_lower:
                        news_data['category'] = "armas"
                    elif any(word in title_lower for word in ['tráfico', 'facção', 'grupo criminoso']):
                        news_data['category'] = "tráfico"
                    elif any(word in title_lower for word in ['apreensão', 'prisão', 'operação', 'desmantela']):
                        news_data['category'] = "policial"
                    else:
                        news_data['category'] = "geral"
                    
                    news_list.append(news_data)
                    logger.info(f"✅ Notícia relevante: {news_data['title'][:50]}...")
            
            logger.info(f"🎯 Total de notícias relevantes encontradas: {len(news_list)}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao fazer scraping de {config['name']}: {e}")
        
        return news_list

    def scrape_all_sites(self):
        """
        Faz scraping de todos os sites configurados
        """
        all_news = []
        configs = self.get_scraping_configs()
        
        logger.info(f"🚀 Iniciando scraping de {len(configs)} sites oficiais...")
        
        for config in configs:
            try:
                site_news = self.scrape_site(config)
                all_news.extend(site_news)
                
                # Rate limiting entre sites
                time.sleep(1.0)
                
            except Exception as e:
                logger.error(f"❌ Erro ao processar {config['name']}: {e}")
                continue
        
        # Remove duplicatas baseadas no título
        unique_news = []
        seen_titles = set()
        
        for news in all_news:
            title_key = news['title'].lower().strip()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_news.append(news)
        
        logger.info(f"📊 Total final: {len(unique_news)} notícias únicas")
        return unique_news

def main():
    """
    Função principal para teste
    """
    scraper = SimpleRobustScraper()
    news = scraper.scrape_all_sites()
    
    print(f"\n🎯 RESULTADO FINAL: {len(news)} notícias relevantes")
    print("=" * 60)
    
    for i, item in enumerate(news[:10], 1):  # Mostra apenas as primeiras 10
        print(f"\n{i}. [{item['category'].upper()}] {item['title']}")
        print(f"   🔗 {item['link']}")
        if item['date']:
            print(f"   📅 {item['date']}")

if __name__ == "__main__":
    main()
