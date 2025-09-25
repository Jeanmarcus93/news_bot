#!/usr/bin/env python3
"""
Bot de Notícias RS - Versão Corrigida
Bot simples e funcional sem problemas de formatação
"""

import logging
import schedule
import threading
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from datetime import datetime
from database import NewsDatabase
from news_scrapers import NewsScraper
from simple_robust_scraper import SimpleRobustScraper
# Twitter removido temporariamente devido a rate limits
# from twitter_scraper import TwitterScraper
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class NewsBot:
    def __init__(self):
        self.db = NewsDatabase()
        self.robust_scraper = SimpleRobustScraper()
        
        # Mapeamento de emojis para fontes (na ordem solicitada)
        self.source_emojis = {
            'PRF Nacional': '🚔',
            'PF Nacional': '🏛️',
            'MPRS': '⚖️',
            'Polícia Civil': '👮',
            'Brigada Militar': '🚔',
            'PM SC': '🚔',
            'PM PR': '🚔',
            'DOF MS': '🚔',
            'PC SC': '👮',
            'PC PR': '👮',
            'G1 RS': '📺',
            'R7 RS': '📺',
            'SB News': '📺',
            'Correio do Povo': '📰',
            'GauchaZH': '📱',
            'Diário SM': '📰',
            'Gaz': '📰',
            'NewsAPI': '📰',
            'Sul21': '🌐',
            'Terra POA': '🌍'
        }
        self.scraper = NewsScraper()
        # Twitter removido temporariamente devido a rate limits
        # self.twitter_scraper = TwitterScraper()
        self.application = None  # Será definido quando o bot iniciar
        
        # Configura os teclados
        self._setup_keyboards()
    
    def get_source_emoji(self, source: str) -> str:
        """Obtém o emoji para uma fonte específica"""
        # Remove prefixo "Scraping Robusto - " se presente
        clean_source = source.replace("Scraping Robusto - ", "")
        return self.source_emojis.get(clean_source, "📰")
    
    def _setup_keyboards(self):
        """Configura todos os teclados do bot"""
        # Teclado fixo na parte inferior - apenas o botão MENU
        self.reply_keyboard = ReplyKeyboardMarkup([
            [KeyboardButton("📋 MENU")]
        ], resize_keyboard=True)
        
        # Teclado inline para categorias
        self.category_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💊 Drogas", callback_data="cat_drogas"),
             InlineKeyboardButton("🔫 Armas", callback_data="cat_armas")],
            [InlineKeyboardButton("🚨 Tráfico", callback_data="cat_trafico"),
             InlineKeyboardButton("👥 Facções", callback_data="cat_faccoes")],
            [InlineKeyboardButton("📰 Todas", callback_data="cat_all")]
        ])
        
        # Teclado inline para o menu principal - 4 opções em uma coluna
        self.menu_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Atualizar Notícias", callback_data="menu_update_news")],
            [InlineKeyboardButton("📰 Últimas Notícias", callback_data="menu_latest")],
            [InlineKeyboardButton("👁️ Notícias Visualizadas", callback_data="menu_viewed")],
            [InlineKeyboardButton("📡 Fontes", callback_data="menu_sources")]
        ])
        
        # Teclado para menu de fontes
        self.sources_keyboard = self._create_sources_keyboard()
    
    def _create_sources_keyboard(self):
        """Cria o teclado com botões para cada fonte de notícias"""
        # Lista de fontes na ordem solicitada
        sources = [
            ("🚔 PRF Nacional", "source_prf"),
            ("🏛️ PF Nacional", "source_pf"),
            ("⚖️ MPRS", "source_mprs"),
            ("👮 Polícia Civil", "source_pc"),
            ("🚔 Brigada Militar", "source_brigada"),
            ("🚔 PM SC", "source_pm_sc"),
            ("🚔 PM PR", "source_pm_pr"),
            ("🚔 DOF MS", "source_dof"),
            ("👮 PC SC", "source_pc_sc"),
            ("👮 PC PR", "source_pc_pr"),
            ("📰 Todas as Fontes", "source_all")
        ]
        
        # Organiza em grupos de 2 botões por linha
        keyboard = []
        for i in range(0, len(sources), 2):
            row = [InlineKeyboardButton(sources[i][0], callback_data=sources[i][1])]
            if i + 1 < len(sources):
                row.append(InlineKeyboardButton(sources[i + 1][0], callback_data=sources[i + 1][1]))
            keyboard.append(row)
        
        # Adiciona botão de voltar
        keyboard.append([InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data="menu_main")])
        
        return InlineKeyboardMarkup(keyboard)
    
    def _get_available_sources(self):
        """Retorna fontes com notícias disponíveis"""
        try:
            all_news = self.db.get_all_news()
            source_counts = {}
            
            for news in all_news:
                source = news[4]
                source_counts[source] = source_counts.get(source, 0) + 1
            
            # Remove prefixo "Scraping Robusto - " para exibição mais limpa
            clean_sources = {}
            for source, count in source_counts.items():
                if source.startswith("Scraping Robusto - "):
                    clean_name = source.replace("Scraping Robusto - ", "")
                else:
                    clean_name = source
                clean_sources[clean_name] = count
            
            return clean_sources
        except Exception as e:
            logger.error(f"Error getting available sources: {e}")
            return {}
    
    def get_source_name_from_url(self, url):
        """Converte URL da fonte para nome limpo"""
        url_mapping = {
            'https://www.gov.br/prf/pt-br/noticias/ultimas': 'PRF Nacional',
            'https://www.gov.br/pf/pt-br/assuntos/noticias/ultimas-noticias': 'PF Nacional',
            'https://www.mprs.mp.br/noticias/': 'MPRS',
            'https://www.pc.rs.gov.br/noticias': 'Polícia Civil RS',
            'https://www.brigadamilitar.rs.gov.br/noticias': 'Brigada Militar',
            'https://www.pm.sc.gov.br/noticias/index?page=2': 'PM SC',
            'https://www.pmpr.pr.gov.br/Noticias': 'PM PR',
            'https://www.dof.ms.gov.br/noticias/': 'DOF MS',
            'https://pc.sc.gov.br/noticias/': 'PC SC',
            'https://www.policiacivil.pr.gov.br/noticias': 'PC PR'
        }
        
        # Busca por correspondência exata primeiro
        if url in url_mapping:
            return url_mapping[url]
        
        # Busca por correspondência parcial
        for source_url, source_name in url_mapping.items():
            if source_url in url:
                return source_name
        
        # Se não encontrar, retorna nome genérico
        return 'Fonte Oficial'
    
    async def scrape_all_news_robust(self):
        """Faz scraping de todas as fontes robustas e salva no banco"""
        try:
            logger.info("🔄 Iniciando scraping robusto de todas as fontes...")
            news_list = self.robust_scraper.scrape_all_sites()
            
            saved_count = 0
            for news in news_list:
                try:
                    # Determina o nome da fonte baseado na URL
                    source_url = news.get('source', '')
                    source_name = self.get_source_name_from_url(source_url)
                    
                    # Salva no banco de dados
                    self.db.add_news(
                        title=news['title'],
                        content='',  # Conteúdo não é extraído no scraper simples
                        url=news['link'],
                        source=source_name,
                        category=news.get('category', 'geral'),
                        published_date=news.get('date', '')
                    )
                    saved_count += 1
                except Exception as e:
                    logger.error(f"Erro ao salvar notícia: {e}")
                    continue
            
            logger.info(f"✅ Scraping robusto concluído: {saved_count} notícias salvas")
            return saved_count
            
        except Exception as e:
            logger.error(f"❌ Erro no scraping robusto: {e}")
            return 0
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start - Mensagem de boas-vindas"""
        welcome_message = """🔍 Bot de Notícias RS - Crimes e Apreensões

Bem-vindo ao bot que monitora notícias sobre:
• 🚨 Apreensão de drogas
• 🔫 Apreensão de armas  
• 🏴 Tráfico e organizações criminosas
• 👥 Facções e milícias

Fontes: 🚀 Fontes Oficiais de Segurança

🎯 **Interface Ultra Simplificada:**
Use o botão **📋 MENU** abaixo para acessar:
• 🔄 Atualizar Notícias
• 📋 Notícias Apresentadas  
• 📊 Estatísticas

Digite /help para ver todos os comandos disponíveis."""
        
        await update.message.reply_text(welcome_message, reply_markup=self.reply_keyboard)
        self.db.log_activity("Bot started", f"User: {update.effective_user.username}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /help - Lista de comandos"""
        help_message = """📋 **Comandos do Bot:**

**🎯 Interface Principal:**
📋 **MENU** - Acesse as funcionalidades principais do bot

        **🎯 Opções do Menu:**
        🔄 **Atualizar Notícias** - Busca novas notícias em todas as fontes
        📰 **Últimas Notícias** - Ver notícias não visualizadas
        👁️ **Notícias Visualizadas** - Ver notícias já lidas
        📡 **Fontes** - Ver notícias por fonte específica

**📝 Comandos por Texto:**
/start - Mensagem de boas-vindas
/latest - Últimas notícias
/category - Filtrar por categoria
/stats - Estatísticas do bot
/search <termo> - Buscar notícias específicas
/refresh_api - Buscar via NewsAPI
/refresh_twitter - Buscar no Twitter/X
/refresh_all - Buscar em todas as fontes
/help - Esta ajuda

**🎯 Dica:** Use o botão **📋 MENU** para acesso rápido às funcionalidades principais!"""
        
        await update.message.reply_text(help_message, reply_markup=self.reply_keyboard)
    
    async def latest_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /latest - Mostra as notícias não visualizadas"""
        try:
            news_list = self.db.get_unviewed_news(limit=10)
            
            if not news_list:
                error_msg = "📭 Nenhuma notícia encontrada. Use '📋 MENU' para buscar."
                if update.callback_query:
                    await update.callback_query.edit_message_text(error_msg)
                else:
                    await update.message.reply_text(error_msg, reply_markup=self.reply_keyboard)
                return
            
            # Envia mensagem inicial
            total_count = len(news_list)
            initial_msg = f"📰 Encontradas {total_count} notícias relevantes:\n\nEnviando cada notícia separadamente..."
            
            if update.callback_query:
                await update.callback_query.edit_message_text(initial_msg)
            else:
                await update.message.reply_text(initial_msg, reply_markup=self.reply_keyboard)
            
            # Envia cada notícia em mensagem separada
            for i, news in enumerate(news_list[:10], 1):
                try:
                    title = news[1]
                    content = news[2] if news[2] else ""
                    source = news[4]
                    category = news[5] if news[5] else "Geral"
                    url = news[3]
                    published_date = news[6] if len(news) > 6 and news[6] else "Data não disponível"
                    
                    category_emoji = {
                        'drogas': '🚨',
                        'armas': '🔫',
                        'tráfico': '🚨',
                        'facções': '👥'
                    }.get(category, '📰')
                    
                    # Formata a data se disponível
                    formatted_date = ""
                    if published_date and published_date != "Data não disponível":
                        try:
                            if 'T' in published_date:
                                dt = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                                formatted_date = f"📅 {dt.strftime('%d/%m/%Y %H:%M')}\n"
                        except:
                            formatted_date = f"📅 {published_date}\n"
                    
                    # Cria mensagem detalhada para cada notícia
                    source_emoji = self.get_source_emoji(source)
                    clean_source = source.replace("Scraping Robusto - ", "")
                    message = f"{source_emoji} {clean_source}\n\n"
                    
                    # Adiciona resumo (usa título se não há conteúdo)
                    if content and len(content.strip()) > 10:
                        if len(content) > 800:
                            content = content[:800] + "..."
                        message += f"📝 Resumo:\n{content}\n\n"
                    else:
                        # Usa o título como resumo se não há conteúdo
                        message += f"📝 Resumo:\n{title}\n\n"
                    
                    # Informações da notícia
                    message += f"🏷️ Categoria: {category.title()}\n"
                    message += formatted_date
                    message += f"🔗 {url}"
                    
                    # Cria botão para marcar como lida
                    news_id = news[0]  # ID da notícia
                    inline_keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("✅ Marcar como Lida", callback_data=f"mark_read_{news_id}")]
                    ])
                    
                    # Para callbacks, usa context.bot.send_message
                    if update.callback_query:
                        await context.bot.send_message(
                            chat_id=update.callback_query.message.chat_id,
                            text=message,
                            reply_markup=inline_keyboard,
                            disable_web_page_preview=True
                        )
                    else:
                        await update.message.reply_text(message, reply_markup=inline_keyboard, disable_web_page_preview=True)
                    
                    # Pequena pausa entre mensagens
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Erro ao enviar notícia {i}: {e}")
                    continue
            
            # Mensagem final
            final_msg = f"✅ Concluído! {total_count} notícias enviadas.\n\nUse '📋 MENU' para mais opções:"
            
            if update.callback_query:
                await context.bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text=final_msg,
                    reply_markup=self.reply_keyboard
                )
            else:
                await update.message.reply_text(final_msg, reply_markup=self.reply_keyboard)
            
        except Exception as e:
            logger.error(f"Error in latest_command: {e}")
            error_msg = "❌ Erro ao buscar notícias. Tente novamente."
            if update.callback_query:
                await update.callback_query.edit_message_text(error_msg)
            else:
                await update.message.reply_text(error_msg, reply_markup=self.reply_keyboard)
    
    async def category_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /category - Menu para filtrar por categoria"""
        await update.message.reply_text("📋 Selecione uma categoria:", reply_markup=self.category_keyboard)
    
    async def category_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Callback para seleção de categoria"""
        query = update.callback_query
        await query.answer()
        
        category = query.data.replace("cat_", "")
        
        try:
            if category == "all":
                news_list = self.db.get_unsent_news(limit=10)
                category_name = "todas as categorias"
            else:
                news_list = self.db.get_news_by_category(category, limit=10)
                category_name = category
            
            if not news_list:
                await query.edit_message_text(f"📭 Nenhuma notícia encontrada na categoria {category_name}. Use '🔄 Buscar Notícias' para buscar.", reply_markup=self.reply_keyboard)
                return
            
            # Mensagem inicial
            total_count = len(news_list)
            await query.edit_message_text(f"📰 {total_count} notícias encontradas na categoria: {category_name.title()}\n\nEnviando cada notícia separadamente...")
            
            # Envia cada notícia em mensagem separada
            for i, news in enumerate(news_list[:10], 1):
                try:
                    title = news[1]
                    content = news[2] if news[2] else ""
                    source = news[4]
                    url = news[3]
                    published_date = news[6] if len(news) > 6 and news[6] else "Data não disponível"
                    
                    category_emoji = {
                        'drogas': '🚨',
                        'armas': '🔫',
                        'tráfico': '🚨',
                        'facções': '👥'
                    }.get(news[5], '📰')
                    
                    # Formata a data se disponível
                    formatted_date = ""
                    if published_date and published_date != "Data não disponível":
                        try:
                            if 'T' in published_date:
                                dt = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                                formatted_date = f"📅 {dt.strftime('%d/%m/%Y %H:%M')}\n"
                        except:
                            formatted_date = f"📅 {published_date}\n"
                    
                    # Cria mensagem detalhada para cada notícia
                    message = f"{category_emoji} {title}\n\n"
                    
                    # Adiciona resumo se disponível
                    if content and len(content.strip()) > 10:
                        if len(content) > 800:
                            content = content[:800] + "..."
                        message += f"📝 Resumo:\n{content}\n\n"
                    
                    # Informações da notícia
                    message += f"📍 Fonte: {source}\n"
                    message += f"🏷️ Categoria: {news[5].title() if news[5] else 'Geral'}\n"
                    message += formatted_date
                    message += f"🔗 {url}"
                    
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=message,
                        reply_markup=self.reply_keyboard,
                        disable_web_page_preview=True
                    )
                    
                    # Pequena pausa entre mensagens
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Erro ao enviar notícia da categoria {i}: {e}")
                    continue
            
            # Mensagem final
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"✅ Concluído! {total_count} notícias da categoria {category_name.title()} enviadas.",
                reply_markup=self.reply_keyboard
            )
            
        except Exception as e:
            logger.error(f"Error in category_callback: {e}")
            await query.edit_message_text("❌ Erro ao buscar notícias. Tente novamente.", reply_markup=self.reply_keyboard)
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /stats - Estatísticas do bot"""
        try:
            stats = self.db.get_stats()
            
            message = "📊 Estatísticas do Bot:\n\n"
            message += f"📰 Total de notícias: {stats.get('total_news', 0)}\n"
            message += f"📭 Notícias não enviadas: {stats.get('unsent_news', 0)}\n\n"
            
            category_stats = stats.get('category_stats', {})
            if category_stats:
                message += "📋 Por categoria:\n"
                for category, count in category_stats.items():
                    emoji = {'drogas': '🚨', 'armas': '🔫', 'tráfico': '🚨', 'facções': '👥'}.get(category, '📰')
                    message += f"   {emoji} {category}: {count}\n"
            
            message += "\n🔧 Status das fontes:\n"
            message += "✅ Fontes oficiais de segurança\n"
            message += "✅ Scraping tradicional\n"
            message += f"\n🕐 Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            
            await update.message.reply_text(message, reply_markup=self.reply_keyboard)
            
        except Exception as e:
            logger.error(f"Error in stats_command: {e}")
            await update.message.reply_text("❌ Erro ao buscar estatísticas.", reply_markup=self.reply_keyboard)
    
    
    async def refresh_twitter_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando para buscar notícias no Twitter/X"""
        try:
            # Twitter/X removido temporariamente devido a rate limits
            await update.message.reply_text("🚫 Twitter/X temporariamente desabilitado devido a rate limits da API.\n\nUse '🔄 Atualizar Notícias' para buscar em outras fontes.", reply_markup=self.reply_keyboard)
            
            
        except Exception as e:
            logger.error(f"Error in refresh_twitter_command: {e}")
            await update.message.reply_text("❌ Erro no comando Twitter/X. Tente novamente.", reply_markup=self.reply_keyboard)
    
    async def refresh_all_sources_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando para buscar em todas as fontes"""
        try:
            # Verifica se é callback (botão) ou mensagem de texto
            if update.callback_query:
                await update.callback_query.edit_message_text("🔄 Buscando notícias em todas as fontes...\n\n🚀 Fontes Oficiais de Segurança")
            else:
                await update.message.reply_text("🔄 Buscando notícias em todas as fontes...\n\n🚀 Fontes Oficiais de Segurança", reply_markup=self.reply_keyboard)
            
            total_found = 0
            total_saved = 0
            
            # 1. Twitter/X removido temporariamente devido a rate limits
            logger.info("Twitter/X temporariamente desabilitado devido a rate limits")
            
            # 2. Busca via scraping robusto (Fontes oficiais)
            try:
                robust_count = await self.scrape_all_news_robust()
                total_saved += robust_count
                logger.info(f"Scraping Robusto: {robust_count} novas notícias salvas")
            except Exception as e:
                logger.error(f"Erro no Scraping Robusto: {e}")
            
            # 3. Busca via scraping tradicional (fallback)
            try:
                traditional_list = self.scraper.scrape_all_sources()
                if traditional_list:
                    saved_traditional = self.scraper.save_news_to_db(traditional_list)
                    total_found += len(traditional_list)
                    total_saved += saved_traditional
                    logger.info(f"Tradicional: {len(traditional_list)} encontradas, {saved_traditional} salvas")
            except Exception as e:
                logger.error(f"Erro Scraping Tradicional: {e}")
            
            message = f"✅ Busca completa concluída!\n\n"
            message += f"📊 Total encontrado: {total_found} notícias\n"
            message += f"💾 Total salvo: {total_saved} novas notícias\n\n"
            message += "Use '📋 MENU' para ver as últimas notícias."
            
            # Verifica se é callback (botão) ou mensagem de texto
            if update.callback_query:
                await update.callback_query.edit_message_text(message)
            else:
                await update.message.reply_text(message, reply_markup=self.reply_keyboard)
            
            self.db.log_activity("Manual refresh (All Sources)", f"Found: {total_found}, Saved: {total_saved}")
            
        except Exception as e:
            logger.error(f"Error in refresh_all_sources_command: {e}")
            error_message = "❌ Erro ao buscar notícias em todas as fontes. Tente novamente."
            # Verifica se é callback (botão) ou mensagem de texto
            if update.callback_query:
                await update.callback_query.edit_message_text(error_message)
            else:
                await update.message.reply_text(error_message, reply_markup=self.reply_keyboard)
    
    async def auto_refresh_news(self):
        """Método para atualização automática de notícias"""
        try:
            logger.info("🔄 Iniciando atualização automática de notícias...")
            
            total_found = 0
            total_saved = 0
            
            # 1. Busca via scraping robusto (Fontes oficiais)
            try:
                robust_count = await self.scrape_all_news_robust()
                total_saved += robust_count
                logger.info(f"Scraping Robusto (Auto): {robust_count} novas notícias salvas")
            except Exception as e:
                logger.error(f"Erro no Scraping Robusto (Auto): {e}")
            
            # 2. Busca via scraping tradicional (fallback)
            try:
                traditional_list = self.scraper.scrape_all_sources()
                if traditional_list:
                    saved_traditional = self.scraper.save_news_to_db(traditional_list)
                    total_found += len(traditional_list)
                    total_saved += saved_traditional
                    logger.info(f"Tradicional (Auto): {len(traditional_list)} encontradas, {saved_traditional} salvas")
            except Exception as e:
                logger.error(f"Erro Scraping Tradicional (Auto): {e}")
            
            # Log da atividade
            self.db.log_activity("Auto refresh (60min)", f"Found: {total_found}, Saved: {total_saved}")
            
            # Notifica no chat se há novas notícias
            if total_saved > 0 and TELEGRAM_CHAT_ID:
                try:
                    message = f"🔄 **Atualização Automática Concluída**\n\n"
                    message += f"📊 **{total_saved} novas notícias** encontradas!\n"
                    message += f"📰 Total de notícias no banco: {self.db.get_total_news_count()}\n\n"
                    message += "Use '📋 MENU' → '📰 Últimas Notícias' para ver as novidades!"
                    
                    await self.application.bot.send_message(
                        chat_id=TELEGRAM_CHAT_ID,
                        text=message,
                        parse_mode='Markdown'
                    )
                    logger.info(f"✅ Notificação enviada para chat {TELEGRAM_CHAT_ID}: {total_saved} novas notícias")
                except Exception as e:
                    logger.error(f"Erro ao enviar notificação automática: {e}")
            
            logger.info(f"✅ Atualização automática concluída: {total_saved} novas notícias")
            
        except Exception as e:
            logger.error(f"Erro na atualização automática: {e}")
    
    def run_auto_refresh(self):
        """Executa a atualização automática em uma thread separada"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.auto_refresh_news())
        except Exception as e:
            logger.error(f"Erro ao executar auto_refresh: {e}")
    
    def start_scheduler(self):
        """Inicia o scheduler para atualização automática a cada 60 minutos"""
        logger.info("⏰ Configurando atualização automática a cada 60 minutos...")
        
        # Agenda a execução a cada 60 minutos
        schedule.every(60).minutes.do(self.run_auto_refresh)
        
        def run_scheduler():
            """Executa o scheduler em uma thread separada"""
            while True:
                schedule.run_pending()
                threading.Event().wait(60)  # Verifica a cada minuto
        
        # Inicia o scheduler em uma thread separada
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        logger.info("✅ Scheduler iniciado - Atualização automática ativa!")
    
    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando do menu principal com opções simplificadas"""
        menu_message = """📋 **MENU PRINCIPAL**

Escolha uma das opções abaixo:

🔄 **Atualizar Notícias** - Busca novas notícias em todas as fontes
📰 **Últimas Notícias** - Ver notícias não visualizadas
👁️ **Notícias Visualizadas** - Ver notícias já lidas

**💡 Dica:** As notícias são marcadas como visualizadas automaticamente quando você as vê!"""
        
        await update.message.reply_text(menu_message, reply_markup=self.menu_keyboard, parse_mode='Markdown')
    
    async def show_sent_news(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostra notícias que já foram apresentadas"""
        try:
            query = update.callback_query
            await query.answer()
            
            # Busca notícias que já foram enviadas
            sent_news = self.db.get_sent_news(limit=10)
            
            if not sent_news:
                await query.edit_message_text("📭 Nenhuma notícia foi apresentada ainda. Use '🔄 BUSCAR NOTÍCIAS' primeiro.")
                return
            
            # Mensagem inicial
            total_count = len(sent_news)
            await query.edit_message_text(f"📋 **{total_count} Notícias Apresentadas**\n\nEnviando cada notícia...", parse_mode='Markdown')
            
            # Envia cada notícia em mensagem separada
            for i, news in enumerate(sent_news[:10], 1):
                try:
                    title = news[1]
                    content = news[2] if news[2] else ""
                    source = news[4]
                    url = news[3]
                    category = news[5] if news[5] else "Geral"
                    published_date = news[6] if len(news) > 6 and news[6] else "Data não disponível"
                    sent_date = news[7] if len(news) > 7 and news[7] else "Data não disponível"
                    
                    category_emoji = {
                        'drogas': '🚨',
                        'armas': '🔫',
                        'tráfico': '🚨',
                        'facções': '👥'
                    }.get(category, '📰')
                    
                    # Formata as datas
                    formatted_published = ""
                    if published_date and published_date != "Data não disponível":
                        try:
                            from datetime import datetime
                            if 'T' in published_date:
                                dt = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                                formatted_published = f"📅 Publicado: {dt.strftime('%d/%m/%Y %H:%M')}\n"
                        except:
                            formatted_published = f"📅 Publicado: {published_date}\n"
                    
                    formatted_sent = ""
                    if sent_date and sent_date != "Data não disponível":
                        try:
                            from datetime import datetime
                            if 'T' in sent_date:
                                dt = datetime.fromisoformat(sent_date.replace('Z', '+00:00'))
                                formatted_sent = f"📤 Enviado: {dt.strftime('%d/%m/%Y %H:%M')}\n"
                        except:
                            formatted_sent = f"📤 Enviado: {sent_date}\n"
                    
                    # Cria mensagem detalhada
                    source_emoji = self.get_source_emoji(source)
                    clean_source = source.replace("Scraping Robusto - ", "")
                    message = f"**{i}. {source_emoji} {clean_source}**\n\n"
                    
                    if content and len(content.strip()) > 10:
                        if len(content) > 600:
                            content = content[:600] + "..."
                        message += f"📝 **Resumo:**\n{content}\n\n"
                    else:
                        # Usa o título como resumo se não há conteúdo
                        message += f"📝 **Resumo:**\n{title}\n\n"
                    
                    message += f"🏷️ **Categoria:** {category.title()}\n"
                    message += formatted_published
                    message += formatted_sent
                    message += f"🔗 {url}"
                    
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=message,
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )
                    
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Erro ao enviar notícia apresentada {i}: {e}")
                    continue
            
            # Mensagem final
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"✅ **Concluído!** {total_count} notícias apresentadas enviadas.\n\nUse os botões abaixo para mais opções:",
                parse_mode='Markdown',
                reply_markup=self.reply_keyboard
            )
            
        except Exception as e:
            logger.error(f"Error in show_sent_news: {e}")
            await query.edit_message_text("❌ Erro ao buscar notícias apresentadas. Tente novamente.")
    
    
    
    async def menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Callback para opções do menu simplificado"""
        query = update.callback_query
        await query.answer()
        
        action = query.data.replace("menu_", "")
        
        try:
            if action == "update_news":
                # Busca notícias em todas as fontes
                await self.refresh_all_sources_command(update, context)
            elif action == "latest":
                # Mostra notícias não visualizadas
                await self.latest_command(update, context)
            elif action == "viewed":
                # Mostra notícias visualizadas
                await self.show_viewed_news(update, context)
            elif action == "sources":
                # Mostra menu de fontes
                await self.show_sources_menu(update, context)
            elif action == "main":
                # Volta ao menu principal
                await self.show_main_menu(update, context)
            else:
                await query.edit_message_text("❌ Opção não reconhecida.")
        except Exception as e:
            logger.error(f"Error in menu_callback: {e}")
            await query.edit_message_text("❌ Erro ao processar opção do menu.")
    
    async def show_sources_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostra o menu de fontes"""
        try:
            message = "📡 **Menu de Fontes**\n\n"
            message += "Selecione uma fonte para ver todas as notícias:\n"
            message += "• 🚨 Inclui notícias já visualizadas\n"
            message += "• 📰 Mostra histórico completo da fonte\n"
            message += "• 🔍 Útil para análise detalhada\n\n"
            message += "_Clique em uma fonte abaixo:_"
            
            await update.callback_query.edit_message_text(
                message, 
                parse_mode='Markdown',
                reply_markup=self.sources_keyboard
            )
        except Exception as e:
            logger.error(f"Error in show_sources_menu: {e}")
            await update.callback_query.edit_message_text("❌ Erro ao mostrar menu de fontes.")
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostra o menu principal"""
        try:
            message = "📋 **Menu Principal**\n\n"
            message += "Escolha uma opção abaixo:"
            
            await update.callback_query.edit_message_text(
                message, 
                parse_mode='Markdown',
                reply_markup=self.menu_keyboard
            )
        except Exception as e:
            logger.error(f"Error in show_main_menu: {e}")
            await update.callback_query.edit_message_text("❌ Erro ao mostrar menu principal.")
    
    async def source_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Callback para fontes específicas"""
        query = update.callback_query
        await query.answer()
        
        # Mapeamento de fontes para nomes no banco de dados
        source_names = {
            "prf": "PRF Nacional",
            "pf": "PF Nacional",
            "mprs": "MPRS",
            "pc": "Polícia Civil RS",
            "brigada": "Brigada Militar",
            "pm_sc": "PM SC",
            "pm_pr": "PM PR",
            "dof": "DOF MS",
            "pc_sc": "PC SC",
            "pc_pr": "PC PR",
            "all": "Todas as Fontes"
        }
        
        try:
            source = query.data.replace("source_", "")
            source_name = source_names.get(source, source.title())
            
            if source == "all":
                await self.show_all_sources_news(update, context)
            else:
                await self.show_source_news(update, context, source, source_name)
                
        except Exception as e:
            logger.error(f"Error in source_callback: {e}")
            await query.edit_message_text("❌ Erro ao processar fonte selecionada.")
    
    async def show_source_news(self, update: Update, context: ContextTypes.DEFAULT_TYPE, source: str, source_name: str):
        """Mostra notícias de uma fonte específica"""
        try:
            # Busca notícias da fonte específica (todas, incluindo visualizadas)
            news_list = self.db.get_news_by_source(source_name)
            
            if not news_list:
                # Mostra fontes disponíveis quando não há notícias
                available_sources = self._get_available_sources()
                message = f"📰 **{source_name}**\n\n"
                message += "❌ Nenhuma notícia encontrada desta fonte.\n\n"
                message += "📊 **Fontes com notícias disponíveis:**\n"
                for source, count in available_sources.items():
                    message += f"• {source}: {count} notícias\n"
                message += "\nUse '🔄 Atualizar Notícias' para buscar novas notícias."
                
                await update.callback_query.edit_message_text(
                    message,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️ Voltar às Fontes", callback_data="menu_sources")]
                    ])
                )
                return
            
            # Mensagem inicial
            total_news = len(news_list)
            message = f"📰 **{source_name}**\n\n"
            message += f"📊 **{total_news} notícias encontradas**\n"
            message += f"🔍 Mostrando todas as notícias (incluindo visualizadas)\n\n"
            
            await update.callback_query.edit_message_text(
                message,
                parse_mode='Markdown'
            )
            
            # Envia cada notícia
            for i, news in enumerate(news_list[:15], 1):  # Limita a 15 notícias
                try:
                    title = news[1]
                    content = news[2] if news[2] else ""
                    source = news[4]
                    category = news[5] if news[5] else "Geral"
                    url = news[3]
                    published_date = news[6] if len(news) > 6 and news[6] else "Data não disponível"
                    viewed = news[9] if len(news) > 9 else False  # Campo viewed
                    
                    category_emoji = {
                        'drogas': '🚨',
                        'armas': '🔫',
                        'tráfico': '🚨',
                        'facções': '👥'
                    }.get(category, '📰')
                    
                    # Emoji de status de visualização
                    view_status = "👁️" if viewed else "🆕"
                    
                    # Formata a data se disponível
                    formatted_date = ""
                    if published_date and published_date != "Data não disponível":
                        try:
                            if 'T' in published_date:
                                dt = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                                formatted_date = f"📅 {dt.strftime('%d/%m/%Y %H:%M')}\n"
                        except:
                            formatted_date = f"📅 {published_date}\n"
                    
                    # Cria mensagem para a notícia
                    source_emoji = self.get_source_emoji(source)
                    clean_source = source.replace("Scraping Robusto - ", "")
                    message = f"{view_status} {source_emoji} {clean_source}\n\n"
                    
                    # Adiciona resumo (usa título se não há conteúdo)
                    if content and len(content.strip()) > 10:
                        if len(content) > 600:
                            content = content[:600] + "..."
                        message += f"📝 Resumo:\n{content}\n\n"
                    else:
                        # Usa o título como resumo se não há conteúdo
                        message += f"📝 Resumo:\n{title}\n\n"
                    
                    # Informações da notícia
                    message += f"🏷️ Categoria: {category.title()}\n"
                    message += formatted_date
                    message += f"🔗 {url}"
                    
                    # Envia a notícia
                    await context.bot.send_message(
                        chat_id=update.callback_query.message.chat_id,
                        text=message,
                        disable_web_page_preview=True
                    )
                    
                    # Pequena pausa entre mensagens
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Erro ao enviar notícia {i} da fonte {source_name}: {e}")
                    continue
            
            # Mensagem final
            final_msg = f"✅ **Concluído!**\n\n"
            final_msg += f"📊 Mostradas {min(total_news, 15)} de {total_news} notícias de **{source_name}**\n\n"
            final_msg += "Use '📡 Fontes' para ver outras fontes."
            
            await context.bot.send_message(
                chat_id=update.callback_query.message.chat_id,
                text=final_msg,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📡 Ver Outras Fontes", callback_data="menu_sources")]
                ])
            )
            
        except Exception as e:
            logger.error(f"Error in show_source_news: {e}")
            await update.callback_query.edit_message_text("❌ Erro ao carregar notícias da fonte.")
    
    async def show_all_sources_news(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostra notícias de todas as fontes"""
        try:
            # Busca todas as notícias
            news_list = self.db.get_all_news(limit=20)
            
            if not news_list:
                message = "📰 **Todas as Fontes**\n\n"
                message += "❌ Nenhuma notícia encontrada.\n\n"
                message += "Use '🔄 Atualizar Notícias' para buscar novas notícias."
                
                await update.callback_query.edit_message_text(
                    message,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️ Voltar às Fontes", callback_data="menu_sources")]
                    ])
                )
                return
            
            # Mensagem inicial
            total_news = len(news_list)
            message = f"📰 **Todas as Fontes**\n\n"
            message += f"📊 **{total_news} notícias mais recentes**\n"
            message += f"🔍 Mostrando de todas as fontes\n\n"
            
            await update.callback_query.edit_message_text(
                message,
                parse_mode='Markdown'
            )
            
            # Envia cada notícia (similar ao show_source_news)
            for i, news in enumerate(news_list, 1):
                try:
                    title = news[1]
                    content = news[2] if news[2] else ""
                    source = news[4]
                    category = news[5] if news[5] else "Geral"
                    url = news[3]
                    published_date = news[6] if len(news) > 6 and news[6] else "Data não disponível"
                    viewed = news[9] if len(news) > 9 else False
                    
                    category_emoji = {
                        'drogas': '🚨',
                        'armas': '🔫',
                        'tráfico': '🚨',
                        'facções': '👥'
                    }.get(category, '📰')
                    
                    view_status = "👁️" if viewed else "🆕"
                    
                    # Formata a data se disponível
                    formatted_date = ""
                    if published_date and published_date != "Data não disponível":
                        try:
                            if 'T' in published_date:
                                dt = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                                formatted_date = f"📅 {dt.strftime('%d/%m/%Y %H:%M')}\n"
                        except:
                            formatted_date = f"📅 {published_date}\n"
                    
                    # Cria mensagem para a notícia
                    source_emoji = self.get_source_emoji(source)
                    clean_source = source.replace("Scraping Robusto - ", "")
                    message = f"{view_status} {source_emoji} {clean_source}\n\n"
                    
                    # Adiciona resumo (usa título se não há conteúdo)
                    if content and len(content.strip()) > 10:
                        if len(content) > 600:
                            content = content[:600] + "..."
                        message += f"📝 Resumo:\n{content}\n\n"
                    else:
                        # Usa o título como resumo se não há conteúdo
                        message += f"📝 Resumo:\n{title}\n\n"
                    
                    # Informações da notícia
                    message += f"🏷️ Categoria: {category.title()}\n"
                    message += formatted_date
                    message += f"🔗 {url}"
                    
                    # Envia a notícia
                    await context.bot.send_message(
                        chat_id=update.callback_query.message.chat_id,
                        text=message,
                        disable_web_page_preview=True
                    )
                    
                    # Pequena pausa entre mensagens
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Erro ao enviar notícia {i} de todas as fontes: {e}")
                    continue
            
            # Mensagem final
            final_msg = f"✅ **Concluído!**\n\n"
            final_msg += f"📊 Mostradas {total_news} notícias de **todas as fontes**\n\n"
            final_msg += "Use '📡 Fontes' para ver fontes específicas."
            
            await context.bot.send_message(
                chat_id=update.callback_query.message.chat_id,
                text=final_msg,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📡 Ver Fontes Específicas", callback_data="menu_sources")]
                ])
            )
            
        except Exception as e:
            logger.error(f"Error in show_all_sources_news: {e}")
            await update.callback_query.edit_message_text("❌ Erro ao carregar notícias de todas as fontes.")
    
    async def mark_read_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Callback para marcar notícia como lida"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Extrai o ID da notícia do callback_data
            news_id = int(query.data.replace("mark_read_", ""))
            
            # Marca a notícia como visualizada
            success = self.db.mark_as_viewed(news_id)
            
            if success:
                # Atualiza o botão para mostrar que foi marcada
                new_keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Lida", callback_data="already_read")]
                ])
                
                # Atualiza a mensagem com o novo botão
                await query.edit_message_reply_markup(reply_markup=new_keyboard)
            else:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text="❌ Erro ao marcar notícia como lida. Tente novamente."
                )
                
        except Exception as e:
            logger.error(f"Error in mark_read_callback: {e}")
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="❌ Erro ao processar solicitação. Tente novamente."
            )
    
    async def already_read_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Callback para notícias já marcadas como lidas"""
        query = update.callback_query
        await query.answer("✅ Esta notícia já foi marcada como lida!", show_alert=True)
    
    async def show_viewed_news(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostra notícias já visualizadas"""
        try:
            news_list = self.db.get_viewed_news(limit=10)
            stats = self.db.get_view_stats()
            
            if not news_list:
                message = "👁️ **Nenhuma notícia visualizada ainda.**\n\n"
                message += "📊 **Estatísticas:**\n"
                message += f"• Total: {stats['total']} notícias\n"
                message += f"• Não visualizadas: {stats['unviewed']}\n"
                message += f"• Visualizadas: {stats['viewed']}\n\n"
                message += "Use '📰 Últimas Notícias' para ver notícias novas!"
                
                await update.callback_query.edit_message_text(message, parse_mode='Markdown')
                return
            
            # Mensagem inicial com estatísticas
            total_viewed = len(news_list)
            stats_message = f"👁️ **{total_viewed} notícias visualizadas**\n\n"
            stats_message += f"📊 **Estatísticas:**\n"
            stats_message += f"• Total: {stats['total']} notícias\n"
            stats_message += f"• Visualizadas: {stats['viewed']} ({stats['viewed_percentage']:.1f}%)\n"
            stats_message += f"• Não visualizadas: {stats['unviewed']}\n\n"
            
            if update.callback_query:
                await update.callback_query.edit_message_text(stats_message, parse_mode='Markdown')
            
            # Envia cada notícia visualizada
            for i, news in enumerate(news_list[:10], 1):
                try:
                    title = news[1]
                    content = news[2] if news[2] else ""
                    source = news[4]
                    category = news[5] if news[5] else "Geral"
                    url = news[3]
                    published_date = news[6] if len(news) > 6 and news[6] else "Data não disponível"
                    
                    category_emoji = {
                        'drogas': '🚨',
                        'armas': '🔫',
                        'tráfico': '🚨',
                        'facções': '👥'
                    }.get(category, '📰')
                    
                    # Formata a data se disponível
                    formatted_date = ""
                    if published_date and published_date != "Data não disponível":
                        try:
                            if 'T' in published_date:
                                dt = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                                formatted_date = f"📅 {dt.strftime('%d/%m/%Y %H:%M')}\n"
                        except:
                            formatted_date = f"📅 {published_date}\n"
                    
                    # Cria mensagem para notícia visualizada
                    source_emoji = self.get_source_emoji(source)
                    clean_source = source.replace("Scraping Robusto - ", "")
                    message = f"👁️ {source_emoji} {clean_source}\n\n"
                    
                    # Adiciona resumo (usa título se não há conteúdo)
                    if content and len(content.strip()) > 10:
                        if len(content) > 600:
                            content = content[:600] + "..."
                        message += f"📝 Resumo:\n{content}\n\n"
                    else:
                        # Usa o título como resumo se não há conteúdo
                        message += f"📝 Resumo:\n{title}\n\n"
                    
                    # Informações da notícia
                    message += f"🏷️ Categoria: {category.title()}\n"
                    message += formatted_date
                    message += f"🔗 {url}"
                    
                    # Envia a notícia
                    if update.callback_query:
                        await context.bot.send_message(
                            chat_id=update.callback_query.message.chat_id,
                            text=message,
                            disable_web_page_preview=True
                        )
                    
                    # Pequena pausa entre mensagens
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Erro ao enviar notícia visualizada {i}: {e}")
                    continue
            
            # Mensagem final
            final_msg = f"✅ Concluído! {total_viewed} notícias visualizadas mostradas.\n\nUse '📋 MENU' para mais opções."
            
            if update.callback_query:
                await context.bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text=final_msg,
                    reply_markup=self.reply_keyboard
                )
            
        except Exception as e:
            logger.error(f"Error in show_viewed_news: {e}")
            error_message = "❌ Erro ao carregar notícias visualizadas. Tente novamente."
            await update.callback_query.edit_message_text(error_message)
    
    async def show_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostra configurações e status das fontes"""
        try:
            query = update.callback_query
            await query.answer()
            
            message = "⚙️ **CONFIGURAÇÕES E STATUS**\n\n"
            
            # Status das fontes
            message += "📡 **Status das Fontes:**\n"
            
            # Fontes oficiais
            message += "✅ Fontes Oficiais de Segurança - Ativas\n"
            
            # Twitter/X
            message += "🚫 Twitter/X - Temporariamente desabilitado\n"
            message += "   ⚠️ Rate limits da API causando travamentos\n"
            
            # Scraping tradicional
            message += "✅ Scraping Tradicional - Sempre ativo\n"
            message += "   🌐 Portais: PRF, PF, Brigada Militar, Polícia Civil\n"
            
            # Configurações do bot
            message += "\n🤖 **Configurações do Bot:**\n"
            message += f"📱 Chat ID: {TELEGRAM_CHAT_ID}\n"
            message += f"🗄️ Banco de dados: news_bot.db\n"
            message += f"🔄 Intervalo de busca: 30 minutos\n"
            
            # Estatísticas de uso
            stats = self.db.get_stats()
            message += "\n📊 **Estatísticas de Uso:**\n"
            message += f"📰 Total de notícias: {stats.get('total_news', 0)}\n"
            message += f"📭 Notícias pendentes: {stats.get('unsent_news', 0)}\n"
            
            message += f"\n🕐 **Última atualização:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
            
            reply_markup = self.reply_keyboard
            await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error in show_settings: {e}")
            await query.edit_message_text("❌ Erro ao buscar configurações.")
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Trata mensagens de texto dos botões fixos"""
        text = update.message.text
        
        if text == "📋 MENU":
            await self.menu_command(update, context)
        else:
            await update.message.reply_text("❓ Comando não reconhecido. Use o botão **📋 MENU** para acessar todas as opções.", reply_markup=self.reply_keyboard, parse_mode='Markdown')
    
    def setup_handlers(self, application):
        """Configura os handlers do bot"""
        # Command handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("latest", self.latest_command))
        application.add_handler(CommandHandler("category", self.category_command))
        application.add_handler(CommandHandler("stats", self.stats_command))
        application.add_handler(CommandHandler("refresh_twitter", self.refresh_twitter_command))
        application.add_handler(CommandHandler("refresh_all", self.refresh_all_sources_command))
        
        # Callback query handlers
        application.add_handler(CallbackQueryHandler(self.category_callback, pattern=r'^cat_'))
        application.add_handler(CallbackQueryHandler(self.menu_callback, pattern=r'^menu_'))
        application.add_handler(CallbackQueryHandler(self.source_callback, pattern=r'^source_'))
        application.add_handler(CallbackQueryHandler(self.mark_read_callback, pattern=r'^mark_read_'))
        application.add_handler(CallbackQueryHandler(self.already_read_callback, pattern=r'^already_read$'))
        
        # Message handler para botões fixos
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))

def main():
    """Função principal"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║         Bot de Notícias RS - ATUALIZAÇÃO AUTOMÁTICA        ║
    ║                                                              ║
    ║  Monitora notícias sobre:                                   ║
    ║  • 🚨 Apreensão de drogas                                   ║
    ║  • 🔫 Apreensão de armas                                    ║
    ║  • 🏴 Tráfico e organizações criminosas                     ║
    ║  • 👥 Facções e milícias                                    ║
    ║                                                              ║
    ║  🎯 Botões fixos na parte inferior para fácil acesso!      ║
    ║  ⏰ Atualização automática a cada 60 minutos                ║
    ║  Fontes: NewsAPI + Scraping Robusto + Portais Oficiais      ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    if not TELEGRAM_TOKEN:
        logger.error("❌ TELEGRAM_TOKEN não configurado!")
        sys.exit(1)
    
    # Cria o bot
    bot = NewsBot()
    
    # Configura a aplicação
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Configura os handlers
    bot.setup_handlers(application)
    
    # Define a aplicação no bot para usar no scheduler
    bot.application = application
    
    logger.info("🤖 Bot iniciado com sucesso!")
    logger.info("📱 Use /start no Telegram para começar a usar o bot")
    
    logger.info("✅ Bot iniciado com fontes oficiais de segurança")
    
    # Inicia o scheduler para atualização automática
    bot.start_scheduler()
    
    # Inicia o bot
    application.run_polling()

if __name__ == "__main__":
    main()
