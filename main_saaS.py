# main_saaS.py - ORQUESTRADOR SAAS (V7 - INTEGRADO COM IA ANTHROPIC)
import os
import sys
import time
import logging
import traceback
from datetime import datetime
from dotenv import load_dotenv

# Carrega variáveis de ambiente
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
logger = logging.getLogger(__name__)  # ✅ Corrigido: __name__

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

try:
    from indicators import gerar_sinal
    from execution_engine import executar_ordem
    from alert_monitor import log_and_alert, send_telegram_alert
except ImportError as e:
    logger.error(f"❌ Erro ao importar módulos auxiliares: {e}")
    sys.exit(1)

# ✅ IMPORTA FUNÇÕES DO BOT TELEGRAM (VIP + FREE)
try:
    from telegram_bot import enviar_sinal_vip, enviar_alerta_free
    logger.info("✅ Módulos de Telegram importados com sucesso.")
except ImportError:
    logger.warning("⚠️ Funções de Telegram não importadas.")
    enviar_sinal_vip = None
    enviar_alerta_free = None

# ==========================================
# CONFIGURAÇÕES
# ==========================================
SCAN_INTERVAL = 30  # Segundos entre ciclos
SYMBOLS_TO_SCAN = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "PAXGUSDT"]
_shutdown_flag = False

# ==========================================
# CICLO POR VIP
# ==========================================
def process_vip_user(user_id: str, keys: dict):
    logger.info(f"🔄 [{user_id}] Iniciando ciclo...")
    try:
        # Chaves já vêm descriptografadas do saas_db
        creds = {
            "api_key": keys["api_key"],
            "api_secret": keys["api_secret"],
            "passphrase": keys["passphrase"],
        }
        
        if USE_CLASS_CLIENT:
            client = OKXClient(
                api_key=creds["api_key"],
                api_secret=creds["api_secret"],
                passphrase=creds["passphrase"],
                simulated=False
            )
            acc = client.get_account_info()
        else:
            log_and_alert("ERROR", f"[{user_id}] Modo Legacy não suportado no SaaS.")
            return

        if not acc or acc.get("equity", 0) == 0:
            log_and_alert("WARNING", f"[{user_id}] Falha ao conectar ou equity zero. Pulando.")
            return

        logger.info(f"✅ [{user_id}] Conectado | Equity: ${acc['equity']:.4f}")
        send_telegram_alert(f"✅ [{user_id}] Conectado na OKX. Equity: ${acc['equity']:.4f}", "success")

        for symbol in SYMBOLS_TO_SCAN:
            try:
                # Injeta o cliente isolado no módulo de indicadores
                import indicators
                original_func = indicators.get_klines
                indicators.get_klines = client.get_klines if hasattr(client, "get_klines") else indicators.get_klines

                signal = gerar_sinal(symbol)
                
                # Restaura função original para evitar vazamento entre VIPs
                indicators.get_klines = original_func

                if signal:
                    direction, score, price, stop, take = signal
                    logger.info(f"📊 [{user_id}] SINAL DETECTADO: {symbol} {direction} | Score: {score}")
                    
                    signal_data = {
                        "direction": direction, "entry": price,
                        "stop": stop, "take": take, "score": score
                    }
                    
                    # 1️⃣ ENVIA PARA O VIP (SINAL COMPLETO)
                    if enviar_sinal_vip:
                        enviar_sinal_vip(
                            ativo=symbol, direcao=direction, score=score,
                            entrada=price, take=take, stop=stop,
                            hora=datetime.now().strftime("%H:%M")
                        )
                    
                    # 2️⃣ ENVIA PARA O FREE (TEASER / FUNIL)
                    # Só envia se o score for alto (>=80) para gerar valor
                    if enviar_alerta_free and score >= 80:
                        enviar_alerta_free(ativo=symbol, direcao=direction, score=score)
                        logger.info(f"📢 Teaser enviado para Grupo Free: {symbol}")

                    # Executa ordem se estiver conectado
                    if USE_CLASS_CLIENT:
                        executar_ordem(client, symbol, direction, signal_data, user_id=user_id)
                    else:
                        executar_ordem(symbol, direction, price, stop, take, 0.01, score=score, user_id=user_id)
                        
            except Exception as e:
                log_and_alert("ERROR", f"[{user_id}-{symbol}] Erro no scan: {e}")
                logger.debug(traceback.format_exc())

    except Exception as e:
        log_and_alert("CRITICAL", f"[{user_id}] Erro crítico no ciclo: {e}", "killswitch")
        logger.error(traceback.format_exc())

# ==========================================
# LOOP PRINCIPAL
# ==========================================
def main():
    logger.info("🟣 SEXTA-FEIRA SAAS - ORQUESTRADOR V7 INICIADO")
    logger.info(f"🌐 Ambiente: {'Classe SaaS' if USE_CLASS_CLIENT else 'Legacy Global'}")
    send_telegram_alert("🟢 Orquestrador SaaS v7 (IA Ativa) iniciado com sucesso!", "info")
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
                        log_and_alert("WARNING", f"[{user_id}] Chaves não encontradas no DB.")
                    time.sleep(2)  # Pausa entre usuários para respeitar Rate Limit

            logger.info(f"⏳ Próximo ciclo em {SCAN_INTERVAL}s...")
            time.sleep(SCAN_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info("🛑 Interrompido pelo usuário.")
        send_telegram_alert("🛑 Orquestrador interrompido manualmente.", "warning")
    except Exception as e:
        log_and_alert("CRITICAL", f"Falha fatal no orquestrador: {e}", "crash")
        logger.critical(traceback.format_exc())

# ✅ Corrigido
if __name__ == "__main__":
    main()