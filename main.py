# main.py - ORQUESTRADOR PRINCIPAL (CORRIGIDO)
import sys
import signal
import time
import logging
import os
import json
from threading import Thread
from datetime import datetime
import pytz

sys.path.append(os.path.dirname(os.path.abspath(__file__))) # ✅ __file__

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

HEARTBEAT_FILE = "bot_heartbeat.json"
_shutdown_flag = False

# ==========================================
# HEARTBEAT
# ==========================================
def _update_heartbeat(equity=None, status="alive"):
    try:
        data = {"timestamp": datetime.now().isoformat(), "status": status, "equity": equity}
        with open(HEARTBEAT_FILE, "w") as f:
            json.dump(data, f)
    except: pass

# ==========================================
# IMPORTS
# ==========================================
try:
    # ✅ Corrigido para okx_connect
    from okx_connect import get_account_info, start_dashboard_updater
except ImportError as e:
    logger.error(f"Erro ao importar okx_connect: {e}")

try:
    import telegram_bot as tg
except:
    tg = None

# Tenta importar o engine de estratégia, mas não quebra se não existir
try:
    from strategy_engine import engine as run_strategy
except:
    run_strategy = None

try:
    from indicators import gerar_sinal
except:
    gerar_sinal = None

# ==========================================
# MAIN LOOP
# ==========================================
def main():
    logger.info("SEXTA-FEIRA ADVANCED - INICIANDO...")
    _update_heartbeat(status="starting")

    # Verifica conexão
    try:
        info = get_account_info()
        if info and info.get("equity"):
            logger.info(f"Conectado! Equity: ${info['equity']}")
        else:
            logger.error("Falha ao conectar na Exchange.")
            return
    except Exception as e:
        logger.error(f"Erro de conexão: {e}")
        return

    # Inicia Updater do Dashboard (Thread separada)
    try:
        start_dashboard_updater()
        logger.info("Dashboard Updater iniciado.")
    except Exception as e:
        logger.warning(f"Dashboard Updater falhou: {e}")

    # Se tiver strategy engine, roda ele. Senão, roda loop simples.
    if run_strategy:
        logger.info("Rodando Strategy Engine...")
        try:
            run_strategy()
        except KeyboardInterrupt:
            logger.info("Bot parado pelo usuário.")
    else:
        logger.warning("Strategy Engine não encontrado. Rodando loop de verificação simples.")
        # Loop simples para não morrer
        while not _shutdown_flag:
            # Aqui você poderia chamar o indicador para testar
            # ex: signal = gerar_sinal("BTCUSDT")
            time.sleep(10)
            
            # Atualiza heartbeat
            try:
                info = get_account_info()
                _update_heartbeat(equity=info.get("equity") if info else 0, status="monitoring")
            except: pass

if __name__ == "__main__": # ✅ __name__ corrigido
    main()