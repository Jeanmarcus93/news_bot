import sqlite3
import logging
from datetime import datetime
from config import DATABASE_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsDatabase:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.init_database()
    
    def init_database(self):
        """Inicializa o banco de dados e cria as tabelas necessárias"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabela para armazenar notícias
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS news (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        content TEXT,
                        url TEXT UNIQUE,
                        source TEXT NOT NULL,
                        category TEXT,
                        location TEXT,
                        published_date TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        sent_to_telegram BOOLEAN DEFAULT FALSE,
                        viewed BOOLEAN DEFAULT FALSE
                    )
                ''')
                
                # Adiciona o campo 'viewed' se não existir (migração)
                try:
                    cursor.execute("ALTER TABLE news ADD COLUMN viewed BOOLEAN DEFAULT FALSE")
                    logger.info("Campo 'viewed' adicionado à tabela news")
                except sqlite3.OperationalError:
                    # Campo já existe
                    pass
                
                # Tabela para configurações do bot
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS bot_settings (
                        key TEXT PRIMARY KEY,
                        value TEXT,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Tabela para log de atividades
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS activity_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        activity TEXT NOT NULL,
                        details TEXT,
                        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Tabela para usuários ativos (para notificações)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS active_users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT UNIQUE NOT NULL,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        last_activity TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def add_news(self, title, content, url, source, category=None, location=None, published_date=None):
        """Adiciona uma nova notícia ao banco de dados"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verifica se a notícia já existe (baseado na URL)
                cursor.execute("SELECT id FROM news WHERE url = ?", (url,))
                if cursor.fetchone():
                    logger.info(f"Notícia já existe: {title[:50]}...")
                    return False
                
                # Insere a nova notícia
                cursor.execute('''
                    INSERT INTO news (title, content, url, source, category, location, published_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (title, content, url, source, category, location, published_date))
                
                conn.commit()
                logger.info(f"Nova notícia salva: {title[:50]}...")
                return True
                
        except Exception as e:
            logger.error(f"Error adding news: {e}")
            return False
    
    def get_all_news(self, limit=None):
        """Retorna todas as notícias do banco"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM news ORDER BY created_at DESC"
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor.execute(query)
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"Error getting all news: {e}")
            return []
    
    def get_unviewed_news(self, limit=None):
        """Retorna notícias não visualizadas"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM news WHERE viewed = FALSE ORDER BY created_at DESC"
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor.execute(query)
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"Error getting unviewed news: {e}")
            return []
    
    def get_unsent_news(self, limit=None):
        """Retorna notícias não enviadas para o Telegram"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM news WHERE sent_to_telegram = FALSE ORDER BY created_at DESC"
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor.execute(query)
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"Error getting unsent news: {e}")
            return []
    
    def get_sent_news(self, limit=None):
        """Retorna notícias enviadas para o Telegram"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM news WHERE sent_to_telegram = TRUE ORDER BY created_at DESC"
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor.execute(query)
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"Error getting sent news: {e}")
            return []
    
    def get_viewed_news(self, limit=None):
        """Retorna notícias já visualizadas"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM news WHERE viewed = TRUE ORDER BY created_at DESC"
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor.execute(query)
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"Error getting viewed news: {e}")
            return []
    
    def get_view_stats(self):
        """Retorna estatísticas de visualização das notícias"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total de notícias
                cursor.execute("SELECT COUNT(*) FROM news")
                total = cursor.fetchone()[0]
                
                # Notícias visualizadas
                cursor.execute("SELECT COUNT(*) FROM news WHERE viewed = TRUE")
                viewed = cursor.fetchone()[0]
                
                # Notícias não visualizadas
                unviewed = total - viewed
                
                # Porcentagem de visualizadas
                viewed_percentage = (viewed / total * 100) if total > 0 else 0
                
                return {
                    'total': total,
                    'viewed': viewed,
                    'unviewed': unviewed,
                    'viewed_percentage': viewed_percentage
                }
                
        except Exception as e:
            logger.error(f"Error getting view stats: {e}")
            return {
                'total': 0,
                'viewed': 0,
                'unviewed': 0,
                'viewed_percentage': 0
            }
    
    def get_news_by_category(self, category, limit=None):
        """Retorna notícias de uma categoria específica"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM news WHERE category = ? ORDER BY created_at DESC"
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor.execute(query, (category,))
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"Error getting news by category: {e}")
            return []
    
    def get_news_by_source(self, source, limit=None):
        """Retorna notícias de uma fonte específica"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM news WHERE source = ? ORDER BY created_at DESC"
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor.execute(query, (source,))
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"Error getting news by source: {e}")
            return []
    
    def mark_as_viewed(self, news_id):
        """Marca uma notícia como visualizada"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE news SET viewed = TRUE WHERE id = ?", (news_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error marking news as viewed: {e}")
            return False
    
    def mark_as_sent(self, news_id):
        """Marca uma notícia como enviada para o Telegram"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE news SET sent_to_telegram = TRUE WHERE id = ?", (news_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error marking news as sent: {e}")
            return False
    
    def get_stats(self):
        """Retorna estatísticas do banco de dados"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total de notícias
                cursor.execute("SELECT COUNT(*) FROM news")
                total_news = cursor.fetchone()[0]
                
                # Notícias por categoria
                cursor.execute("SELECT category, COUNT(*) FROM news WHERE category IS NOT NULL GROUP BY category")
                categories = dict(cursor.fetchall())
                
                # Notícias por fonte
                cursor.execute("SELECT source, COUNT(*) FROM news GROUP BY source ORDER BY COUNT(*) DESC")
                sources = dict(cursor.fetchall())
                
                # Notícias não visualizadas
                cursor.execute("SELECT COUNT(*) FROM news WHERE viewed = FALSE")
                unviewed = cursor.fetchone()[0]
                
                # Notícias não enviadas
                cursor.execute("SELECT COUNT(*) FROM news WHERE sent_to_telegram = FALSE")
                unsent = cursor.fetchone()[0]
                
                return {
                    'total_news': total_news,
                    'categories': categories,
                    'sources': sources,
                    'unviewed': unviewed,
                    'unsent': unsent
                }
                
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    def get_total_news_count(self):
        """Retorna o total de notícias no banco"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM news")
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting total news count: {e}")
            return 0
    
    def log_activity(self, activity, details=None):
        """Registra uma atividade no log"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO activity_log (activity, details)
                    VALUES (?, ?)
                ''', (activity, details))
                conn.commit()
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
    
    def get_recent_activities(self, limit=10):
        """Retorna atividades recentes"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT activity, details, timestamp 
                    FROM activity_log 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting recent activities: {e}")
            return []
    
    def add_active_user(self, user_id, username=None, first_name=None, last_name=None):
        """Adiciona ou atualiza um usuário ativo"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO active_users 
                    (user_id, username, first_name, last_name, is_active, last_activity)
                    VALUES (?, ?, ?, ?, TRUE, CURRENT_TIMESTAMP)
                ''', (user_id, username, first_name, last_name))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding active user: {e}")
            return False
    
    def get_active_users(self):
        """Retorna lista de usuários ativos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_id, username, first_name, last_name 
                    FROM active_users 
                    WHERE is_active = TRUE
                ''')
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            return []
    
    def deactivate_user(self, user_id):
        """Desativa um usuário (para parar notificações)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE active_users 
                    SET is_active = FALSE 
                    WHERE user_id = ?
                ''', (user_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error deactivating user: {e}")
            return False
    
    def news_exists(self, url):
        """Verifica se uma notícia já existe baseada na URL ou título"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Se a URL não for None, verifica por URL
                if url:
                    cursor.execute("SELECT id FROM news WHERE url = ?", (url,))
                    if cursor.fetchone():
                        return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error checking if news exists: {e}")
            return False
    
    def news_exists_by_title(self, title, source):
        """Verifica se uma notícia já existe baseada no título e fonte"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verifica por título e fonte (para casos onde URL é None)
                cursor.execute("SELECT id FROM news WHERE title = ? AND source = ?", (title, source))
                if cursor.fetchone():
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error checking if news exists by title: {e}")
            return False
    
