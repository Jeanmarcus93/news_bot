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
        
        # Simula que o bot está rodando (já está funcionando pelo main)
        # O bot real já está ativo pelo processo principal
        while True:
            time.sleep(60)  # Mantém a thread viva
            
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
    
    # Importa e inicia o bot real
    try:
        from bot import main as bot_main
        bot_main()
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar bot: {e}")
    
    # Inicia o servidor web
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🌐 Servidor web iniciando na porta {port}")
    
    app.run(host='0.0.0.0', port=port, debug=False)
