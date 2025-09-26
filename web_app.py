#!/usr/bin/env python3
"""
Versão web do bot para compatibilidade com Render Web Service
Inclui um endpoint simples para health check
"""

import os
import logging
from flask import Flask, jsonify
import threading
import time

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Variável global para controlar o bot
bot_thread = None
bot_running = False

def run_bot():
    """Executa o bot em uma thread separada"""
    global bot_running
    try:
        bot_running = True
        logger.info("🤖 Iniciando bot em thread separada...")
        
        # Importa e executa o bot real
        from bot import NewsBot
        from config import TELEGRAM_TOKEN
        from telegram.ext import Application
        
        if not TELEGRAM_TOKEN:
            logger.error("❌ TELEGRAM_TOKEN não configurado!")
            return
            
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
        
        # Inicia o scheduler para atualização automática
        bot.start_scheduler()
        
        # Inicia o bot
        application.run_polling()
            
    except Exception as e:
        logger.error(f"❌ Erro no bot: {e}")
        bot_running = False

@app.route('/')
def health_check():
    """Endpoint de health check"""
    return jsonify({
        "status": "online",
        "bot_running": bot_running,
        "service": "News Bot RS",
        "message": "Bot de notícias de segurança pública funcionando"
    })

@app.route('/health')
def health():
    """Endpoint de saúde do serviço"""
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "bot_active": bot_running
    })

@app.route('/start')
def start_bot():
    """Endpoint para iniciar o bot manualmente"""
    global bot_thread, bot_running
    
    if not bot_running:
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        return jsonify({"message": "Bot iniciado", "status": "started"})
    else:
        return jsonify({"message": "Bot já está rodando", "status": "running"})

if __name__ == "__main__":
    # Inicia o bot automaticamente
    logger.info("🚀 Iniciando aplicação web + bot...")
    
    # Inicia o bot em thread separada
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Aguarda um pouco para o bot inicializar
    time.sleep(3)
    
    # Inicia o servidor web
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🌐 Servidor web iniciando na porta {port}")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar servidor web: {e}")
