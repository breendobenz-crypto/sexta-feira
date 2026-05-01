# main_saaS.py - ORQUESTRADOR SAAS (V6 - CORRIGIDO)
import os
import sys
import time
import logging
import traceback
from dotenv import load_dotenv

# 1. Carrega variáveis de ambiente
load_dotenv()

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    handlers=[
        logging.FileHandler("jarvis_saas.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==========================================
# IMPORTS CORE
# ==========================================
try:
    from saas_db import get_active_users, get_user_credentials
except ImportError as e:
    logger.critical(f"❌ Módulos SaaS não encontrados: {e}")
    sys.exit(1)

try:
    from okx_connect import OKXClient
    USE_CLASS_CLIENT = True
except ImportError:
    USE_CLASS_CLIENT = False
    logger.warning("⚠️ okx_connect.py não encontrado.")

from indicators import gerar_sinal
from execution_engine import executar_ordem

# ==========================================
# CONFIGURAÇÕES
# ==========================================
SCAN_INTERVAL = 30  # Segundos entre ciclos
SYMBOLS_TO_SCAN = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
_shutdown_flag = False

# ==========================================
# CICLO POR VIP
# ==========================================
def process_vip_user(user_id: str, keys: dict):
    logger.info(f"🔄 [{user_id}] Iniciando ciclo...")
    try:
        # ✅ CORREÇÃO: O saas_db.py JÁ retorna as chaves descriptografadas.
        # Removemos a chamada decrypt_key() que estava causando o erro.
        creds = {
            "api_key": keys["api_key"],
            "api_secret": keys["api_secret"],
            "passphrase": keys["passphrase"],
        }

        # 2. Cria cliente OKX isolado para este VIP
        if USE_CLASS_CLIENT:
            client = OKXClient(
                api_key=creds["api_key"],
                api_secret=creds["api_secret"],
                passphrase=creds["passphrase"],
                simulated=False
            )
            acc = client.get_account_info()
        else:
            logger.error(f"❌ [{user_id}] Modo Legacy não suportado no SaaS.")
            return

        if not acc or acc.get("equity", 0) == 0:
            logger.warning(f"⚠️ [{user_id}] Falha ao conectar ou equity zero. Pulando.")
            return

        logger.info(f"✅ [{user_id}] Conectado | Equity: ${acc['equity']:.4f}")

        # 3. Loop de Varredura de Sinais
        for symbol in SYMBOLS_TO_SCAN:
            try:
                # Injeta o cliente no módulo de indicadores temporariamente
                import indicators
                original_func = indicators.get_klines
                indicators.get_klines = client.get_klines if hasattr(client, "get_klines") else indicators.get_klines

                signal = gerar_sinal(symbol)
                
                # Restaura função original para não vazar para o próximo VIP
                indicators.get_klines = original_func

                if signal:
                    direction, score, price, stop, take = signal
                    logger.info(f"📊 [{user_id}] SINAL DETECTADO: {symbol} {direction} | Score: {score}")
                    
                    signal_data = {
                        "direction": direction, "entry": price,
                        "stop": stop, "take": take, "score": score
                    }
                    
                    # Executa ordem (passa o cliente isolado)
                    if USE_CLASS_CLIENT:
                        executar_ordem(client, symbol, direction, signal_data)
                    else:
                        executar_ordem(symbol, direction, price, stop, take, 0.01, score=score)
                        
            except Exception as e:
                logger.error(f"❌ [{user_id}-{symbol}] Erro no scan: {e}")
                logger.debug(traceback.format_exc())

    except Exception as e:
        logger.error(f"💥 [{user_id}] Erro crítico no ciclo:")
        logger.error(traceback.format_exc())

# ==========================================
# LOOP PRINCIPAL
# ==========================================
def main():
    logger.info("🟣 SEXTA-FEIRA SAAS - ORQUESTRADOR V6 INICIADO")
    logger.info(f"🌐 Ambiente: {'Classe SaaS' if USE_CLASS_CLIENT else 'Legacy Global'}")
    
    try:
        while not _shutdown_flag:
            vip_users = get_active_users()
            
            if not vip_users:
                logger.info("💤 Nenhum VIP ativo. Aguardando...")
            else:
                logger.info(f"👥 {len(vip_users)} VIP(s) ativo(s). Processando...")
                for user_id in vip_users:
                    keys = get_user_credentials(user_id)
                    if keys:
                        process_vip_user(user_id, keys)
                    else:
                        logger.warning(f"⚠️ [{user_id}] Chaves não encontradas no DB.")
                    time.sleep(2)  # Pausa entre usuários para respeitar Rate Limit

            logger.info(f"⏳ Próximo ciclo em {SCAN_INTERVAL}s...")
            time.sleep(SCAN_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info("🛑 Interrompido pelo usuário.")
    except Exception as e:
        logger.critical(f"💥 Falha fatal no orquestrador:")
        logger.critical(traceback.format_exc())

if __name__ == "__main__":
    main()