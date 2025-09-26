import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime, timedelta
import re
from typing import List, Dict
from urllib.parse import urljoin, urlparse
from database import NewsDatabase
from config import SEARCH_KEYWORDS, RS_LOCATIONS, PORTAL_URLS
import time
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsScraper:
    def __init__(self):
        self.db = NewsDatabase()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        # Desabilita verificação SSL para sites com problemas de certificado
        self.session.verify = False
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def is_relevant_news(self, title: str, content: str) -> tuple:
        """
        Verifica se a notícia é relevante baseada nas palavras-chave específicas
        Retorna (is_relevant, category)
        """
        text = f"{title} {content}".lower()
        
        # Palavras-chave específicas e precisas
        target_keywords = [
            'drogas', 'armas', 'maconha', 'cocaína', 'ecstasy', 'skunk', 
            'apreensão', 'prisão', 'tráfico', 'facção', 'operação'
        ]
        
        # Verifica cada palavra-chave específica
        for keyword in target_keywords:
            if keyword in text:
                # Determina categoria baseada na palavra-chave
                if keyword in ['drogas', 'maconha', 'cocaína', 'ecstasy', 'skunk']:
                    category = "drogas"
                elif keyword == 'armas':
                    category = "armas"
                elif keyword in ['tráfico', 'facção']:
                    category = "tráfico"
                elif keyword in ['apreensão', 'prisão', 'operação']:
                    category = "policial"
                else:
                    category = "geral"
                
                logger.info(f"Notícia relevante ({category}): {title[:50]}... - Palavra-chave: {keyword}")
                return True, category
        
        return False, None
    
    def clean_text(self, text: str) -> str:
        """Limpa e normaliza texto"""
        if not text:
            return ""
        
        # Remove caracteres especiais e normaliza espaços
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def scrape_prf_news(self) -> List[Dict]:
        """Scraper para notícias da PRF"""
        news_list = []
        
        try:
            for url in PORTAL_URLS['PRF']:
                logger.info(f"Scraping PRF news from: {url}")
                
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Busca por links de notícias (ajuste conforme a estrutura do site)
                news_links = soup.find_all('a', href=True)
                
                for link in news_links[:20]:  # Limita a 20 links por página
                    try:
                        href = link.get('href')
                        if not href:
                            continue
                        
                        # Converte URL relativa para absoluta
                        full_url = urljoin(url, href)
                        
                        # Evita links externos desnecessários
                        if urlparse(full_url).netloc != urlparse(url).netloc:
                            continue
                        
                        title = link.get_text(strip=True)
                        
                        if not title or len(title) < 10:
                            continue
                        
                        # Verifica se é relevante
                        is_relevant, category = self.is_relevant_news(title, "")
                        
                        if is_relevant:
                            # Busca conteúdo completo da notícia
                            content = self.get_article_content(full_url)
                            
                            news_item = {
                                'title': self.clean_text(title),
                                'content': self.clean_text(content),
                                'url': full_url,
                                'source': 'PRF',
                                'category': category,
                                'published_date': datetime.now().isoformat()
                            }
                            
                            news_list.append(news_item)
                        
                        # Pequena pausa para não sobrecarregar o servidor
                        time.sleep(0.5)
                        
                    except Exception as e:
                        logger.error(f"Error processing PRF link: {e}")
                        continue
                
        except Exception as e:
            logger.error(f"Error scraping PRF news: {e}")
        
        return news_list
    
    def scrape_pf_news(self) -> List[Dict]:
        """Scraper para notícias da Polícia Federal"""
        news_list = []
        
        try:
            for url in PORTAL_URLS['PF']:
                logger.info(f"Scraping PF news from: {url}")
                
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Busca por links de notícias
                news_links = soup.find_all('a', href=True)
                
                for link in news_links[:20]:
                    try:
                        href = link.get('href')
                        if not href:
                            continue
                        
                        full_url = urljoin(url, href)
                        
                        if urlparse(full_url).netloc != urlparse(url).netloc:
                            continue
                        
                        title = link.get_text(strip=True)
                        
                        if not title or len(title) < 10:
                            continue
                        
                        is_relevant, category = self.is_relevant_news(title, "")
                        
                        if is_relevant:
                            content = self.get_article_content(full_url)
                            
                            news_item = {
                                'title': self.clean_text(title),
                                'content': self.clean_text(content),
                                'url': full_url,
                                'source': 'PF',
                                'category': category,
                                'published_date': datetime.now().isoformat()
                            }
                            
                            news_list.append(news_item)
                        
                        time.sleep(0.5)
                        
                    except Exception as e:
                        logger.error(f"Error processing PF link: {e}")
                        continue
                
        except Exception as e:
            logger.error(f"Error scraping PF news: {e}")
        
        return news_list
    
    def scrape_brigada_militar_news(self) -> List[Dict]:
        """Scraper para notícias da Brigada Militar"""
        news_list = []
        
        try:
            for url in PORTAL_URLS['Brigada_Militar']:
                logger.info(f"Scraping Brigada Militar news from: {url}")
                
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Busca por links de notícias
                news_links = soup.find_all('a', href=True)
                
                for link in news_links[:20]:
                    try:
                        href = link.get('href')
                        if not href:
                            continue
                        
                        full_url = urljoin(url, href)
                        
                        if urlparse(full_url).netloc != urlparse(url).netloc:
                            continue
                        
                        title = link.get_text(strip=True)
                        
                        if not title or len(title) < 10:
                            continue
                        
                        is_relevant, category = self.is_relevant_news(title, "")
                        
                        if is_relevant:
                            content = self.get_article_content(full_url)
                            
                            news_item = {
                                'title': self.clean_text(title),
                                'content': self.clean_text(content),
                                'url': full_url,
                                'source': 'Brigada Militar',
                                'category': category,
                                'published_date': datetime.now().isoformat()
                            }
                            
                            news_list.append(news_item)
                        
                        time.sleep(0.5)
                        
                    except Exception as e:
                        logger.error(f"Error processing Brigada Militar link: {e}")
                        continue
                
        except Exception as e:
            logger.error(f"Error scraping Brigada Militar news: {e}")
        
        return news_list
    
    def scrape_policia_civil_news(self) -> List[Dict]:
        """Scraper para notícias da Polícia Civil"""
        news_list = []
        
        try:
            for url in PORTAL_URLS['Policia_Civil']:
                logger.info(f"Scraping Polícia Civil news from: {url}")
                
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Busca por links de notícias - método mais específico
                news_links = []
                
                # Procura por links em diferentes estruturas
                for selector in ['a[href*="noticias"]', 'a[href*="apreens"]', '.news-item a', '.noticia a']:
                    links = soup.select(selector)
                    news_links.extend(links)
                
                # Se não encontrou com seletores específicos, pega todos os links
                if not news_links:
                    news_links = soup.find_all('a', href=True)
                
                for link in news_links[:30]:  # Aumenta o limite
                    try:
                        href = link.get('href')
                        if not href:
                            continue
                        
                        full_url = urljoin(url, href)
                        
                        # Verifica se é uma URL válida do mesmo domínio
                        if 'pc.rs.gov.br' not in full_url:
                            continue
                        
                        # Pula links que não são notícias
                        if any(skip in full_url.lower() for skip in ['javascript:', 'mailto:', '#', 'pdf']):
                            continue
                        
                        title = link.get_text(strip=True)
                        
                        # Busca título em elementos próximos se o link não tem texto
                        if not title or len(title) < 10:
                            parent = link.find_parent(['div', 'article', 'section'])
                            if parent:
                                title_elem = parent.find(['h1', 'h2', 'h3', 'h4'])
                                if title_elem:
                                    title = title_elem.get_text(strip=True)
                        
                        if not title or len(title) < 10:
                            continue
                        
                        # Verifica relevância
                        is_relevant, category = self.is_relevant_news(title, "")
                        
                        if is_relevant:
                            content = self.get_article_content(full_url)
                            
                            news_item = {
                                'title': self.clean_text(title),
                                'content': self.clean_text(content),
                                'url': full_url,
                                'source': 'Polícia Civil',
                                'category': category,
                                'published_date': datetime.now().isoformat()
                            }
                            
                            news_list.append(news_item)
                            logger.info(f"Notícia relevante encontrada: {title[:50]}...")
                        
                        time.sleep(0.3)  # Reduz o tempo de espera
                        
                    except Exception as e:
                        logger.error(f"Error processing Polícia Civil link: {e}")
                        continue
                
        except Exception as e:
            logger.error(f"Error scraping Polícia Civil news: {e}")
        
        return news_list
    
    def scrape_g1_rs_news(self) -> List[Dict]:
        """Scraper para notícias do G1 RS"""
        news_list = []
        
        try:
            for url in PORTAL_URLS['G1_RS']:
                logger.info(f"Scraping G1 RS news from: {url}")
                
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Busca por links de notícias
                news_links = soup.find_all('a', href=True)
                
                for link in news_links[:20]:
                    try:
                        href = link.get('href')
                        if not href:
                            continue
                        
                        full_url = urljoin(url, href)
                        
                        if urlparse(full_url).netloc != urlparse(url).netloc:
                            continue
                        
                        title = link.get_text(strip=True)
                        
                        if not title or len(title) < 10:
                            continue
                        
                        is_relevant, category = self.is_relevant_news(title, "")
                        
                        if is_relevant:
                            content = self.get_article_content(full_url)
                            
                            news_item = {
                                'title': self.clean_text(title),
                                'content': self.clean_text(content),
                                'url': full_url,
                                'source': 'G1 RS',
                                'category': category,
                                'published_date': datetime.now().isoformat()
                            }
                            
                            news_list.append(news_item)
                        
                        time.sleep(0.5)
                        
                    except Exception as e:
                        logger.error(f"Error processing G1 RS link: {e}")
                        continue
                
        except Exception as e:
            logger.error(f"Error scraping G1 RS news: {e}")
        
        return news_list
    
    def get_article_content(self, url: str) -> str:
        """Extrai o conteúdo completo de um artigo"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove scripts e estilos
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Busca por conteúdo principal (ajuste conforme necessário)
            content_selectors = [
                'article', '.article-content', '.news-content', 
                '.content', '.post-content', 'main'
            ]
            
            content = ""
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text(strip=True)
                    break
            
            # Se não encontrou conteúdo específico, pega o body
            if not content:
                body = soup.find('body')
                if body:
                    content = body.get_text(strip=True)
            
            # Limita o tamanho do conteúdo
            if len(content) > 2000:
                content = content[:2000] + "..."
            
            return content
            
        except Exception as e:
            logger.error(f"Error getting article content from {url}: {e}")
            return ""
    
    def scrape_all_sources(self) -> List[Dict]:
        """Executa scraping de todas as fontes"""
        all_news = []
        
        scrapers = [
            self.scrape_prf_news,
            self.scrape_pf_news,
            self.scrape_brigada_militar_news,
            self.scrape_policia_civil_news,
            self.scrape_g1_rs_news
        ]
        
        for scraper in scrapers:
            try:
                news = scraper()
                all_news.extend(news)
                logger.info(f"Found {len(news)} relevant news from {scraper.__name__}")
            except Exception as e:
                logger.error(f"Error in {scraper.__name__}: {e}")
        
        return all_news
    
    def save_news_to_db(self, news_list: List[Dict]) -> int:
        """Salva notícias no banco de dados"""
        saved_count = 0
        
        for news in news_list:
            try:
                # Verifica se a notícia já existe
                news_already_exists = False
                
                # Se tem URL, verifica por URL
                if news['url']:
                    news_already_exists = self.db.news_exists(news['url'])
                else:
                    # Se não tem URL, verifica por título e fonte
                    news_already_exists = self.db.news_exists_by_title(news['title'], news['source'])
                
                if not news_already_exists:
                    news_id = self.db.add_news(
                        title=news['title'],
                        content=news['content'],
                        url=news['url'],
                        source=news['source'],
                        category=news['category'],
                        published_date=news['published_date']
                    )
                    
                    if news_id:
                        saved_count += 1
                        logger.info(f"Saved news: {news['title'][:50]}...")
                    else:
                        logger.warning(f"Failed to save news: {news['title'][:50]}...")
                else:
                    logger.info(f"News already exists: {news['title'][:50]}...")
                    
            except Exception as e:
                logger.error(f"Error saving news: {e}")
        
        return saved_count
