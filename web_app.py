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
import requests

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Variável global para controlar o bot
bot_thread = None
bot_running = False
keep_alive_thread = None
keep_alive_running = False

def run_bot():
    """Executa o bot em uma thread separada com restart automático"""
    global bot_running
    restart_count = 0
    max_restarts = 5
    
    while restart_count < max_restarts:
        try:
            bot_running = True
            logger.info(f"🤖 Iniciando bot em thread separada... (tentativa {restart_count + 1})")
            
            # Importa e executa o bot real
            from bot import NewsBot
            from config import TELEGRAM_TOKEN
            from telegram.ext import Application
            import asyncio
            
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
            
            # Inicia o bot usando asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(application.initialize())
            loop.run_until_complete(application.start())
            loop.run_until_complete(application.updater.start_polling())
            
            # Mantém o bot rodando
            try:
                loop.run_forever()
            except KeyboardInterrupt:
                logger.info("🛑 Parando bot...")
                break
            except Exception as e:
                logger.error(f"❌ Erro no loop do bot: {e}")
                restart_count += 1
                if restart_count < max_restarts:
                    logger.info(f"🔄 Reiniciando bot em 10 segundos... (tentativa {restart_count + 1})")
                    time.sleep(10)
                    continue
                else:
                    logger.error("❌ Máximo de tentativas de restart atingido!")
                    break
            finally:
                # Para o bot
                try:
                    loop.run_until_complete(application.stop())
                    loop.run_until_complete(application.shutdown())
                    loop.close()
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"❌ Erro crítico no bot: {e}")
            restart_count += 1
            if restart_count < max_restarts:
                logger.info(f"🔄 Reiniciando bot em 15 segundos... (tentativa {restart_count + 1})")
                time.sleep(15)
                continue
            else:
                logger.error("❌ Máximo de tentativas de restart atingido!")
                break
    
    bot_running = False
    logger.error("❌ Bot parou definitivamente após múltiplas tentativas de restart")

def keep_alive_ping():
    """Sistema de keep-alive para evitar suspensão do Render"""
    global keep_alive_running
    
    keep_alive_running = True
    logger.info("🔄 Sistema de keep-alive iniciado (ping a cada 5s)")
    
    while keep_alive_running:
        try:
            # Faz uma requisição para o próprio servidor
            port = int(os.environ.get('PORT', 5000))
            url = f"http://localhost:{port}/health"
            
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                logger.debug("💓 Keep-alive ping realizado com sucesso")
            else:
                logger.warning(f"⚠️ Keep-alive ping falhou: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Erro no keep-alive ping: {e}")
        
        # Aguarda 5 segundos antes do próximo ping (ainda mais frequente)
        time.sleep(5)

@app.route('/')
def health_check():
    """Endpoint de health check"""
    return jsonify({
        "status": "online",
        "bot_running": bot_running,
        "keep_alive_active": keep_alive_running,
        "service": "News Bot RS",
        "message": "Bot de notícias de segurança pública funcionando"
    })

@app.route('/health')
def health():
    """Endpoint de saúde do serviço"""
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "bot_active": bot_running,
        "keep_alive_active": keep_alive_running,
        "uptime": "Servidor ativo com keep-alive"
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

@app.route('/restart')
def restart_bot():
    """Endpoint para reiniciar o bot"""
    global bot_thread, bot_running
    
    logger.info("🔄 Reiniciando bot via endpoint...")
    bot_running = False
    
    if bot_thread and bot_thread.is_alive():
        # Aguarda a thread atual terminar
        bot_thread.join(timeout=5)
    
    # Inicia nova thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    return jsonify({"message": "Bot reiniciado", "status": "restarted"})

if __name__ == "__main__":
    # Inicia o bot automaticamente
    logger.info("🚀 Iniciando aplicação web + bot...")
    
    # Inicia o bot em thread separada
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Aguarda um pouco para o bot inicializar
    time.sleep(3)
    
    # Inicia o sistema de keep-alive em thread separada
    keep_alive_thread = threading.Thread(target=keep_alive_ping, daemon=True)
    keep_alive_thread.start()
    
    # Inicia o servidor web
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🌐 Servidor web iniciando na porta {port}")
    logger.info("🔄 Sistema de keep-alive ativo para evitar suspensão do Render (ping a cada 5s)")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar servidor web: {e}")
    finally:
        # Para o keep-alive quando o servidor parar
        keep_alive_running = False
