#!/usr/bin/env python3
"""
Script de inicialização para o bot de notícias
Inclui tratamento de erros e logs para deploy em nuvem
"""

import os
import sys
import logging
import time
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

def check_environment():
    """Verifica se as variáveis de ambiente necessárias estão configuradas"""
    required_vars = ['TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Variáveis de ambiente faltando: {', '.join(missing_vars)}")
        return False
    
    logger.info("✅ Todas as variáveis de ambiente estão configuradas")
    return True

def main():
    """Função principal"""
    logger.info("🚀 Iniciando Bot de Notícias RS...")
    logger.info(f"📅 Data/Hora: {datetime.now()}")
    logger.info(f"🐍 Python: {sys.version}")
    
    # Verifica ambiente
    if not check_environment():
        logger.error("❌ Falha na verificação do ambiente. Encerrando.")
        sys.exit(1)
    
    try:
        # Importa e inicia o bot
        logger.info("📦 Importando módulos...")
        from bot import main as bot_main
        
        logger.info("🤖 Iniciando bot...")
        bot_main()
        
    except KeyboardInterrupt:
        logger.info("⏹️ Bot interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}", exc_info=True)
        logger.info("🔄 Tentando reiniciar em 30 segundos...")
        time.sleep(30)
        main()  # Tenta reiniciar

if __name__ == "__main__":
    main()
