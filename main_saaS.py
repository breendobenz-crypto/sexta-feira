# main_saaS.py - ORQUESTRADOR SAAS (V7 - INTEGRADO COM IA ANTHROPIC)
import os
import sys
import time
import logging
import traceback
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
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
logger = logging.getLogger(__name__)  # ✅ CORRIGIDO: __name__

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
# NOVAS MENSAGENS PERSONALIZADAS (Opção 2)
# ==========================================
def msg_conexao_sucesso(user_id: str, equity: float) -> str:
    """Mensagem personalizada para conexão bem-sucedida."""
    return (
        f"🟢 **CONEXÃO ATIVA**\n\n"
        f"👤 ID: {user_id}\n"
        f"💰 Equity: ${equity:,.4f}\n"
        f"⏰ {datetime.now().strftime('%H:%M:%S')}\n\n"
        f"_Bot operando normalmente_"
    )

def msg_conexao_falha(user_id: str) -> str:
    """Mensagem personalizada para falha de conexão."""
    return (
        f"🔴 **ATENÇÃO**\n\n"
        f"👤 ID: {user_id}\n"
        f"❌ Falha na conexão ou saldo insuficiente\n"
        f"💡 Verifique as credenciais na OKX\n\n"
        f"_Tentativa registrada_"
    )

def msg_chaves_nao_encontradas(user_id: str) -> str:
    """Mensagem para chaves API não encontradas."""
    return (
        f"⚠️ **CONFIGURAÇÃO PENDENTE**\n\n"
        f"👤 ID: {user_id}\n"
        f"❌ Chaves API não encontradas\n"
        f"📋 Preencha o formulário: /formulario\n\n"
        f"_Aguardando configuração_"
    )

def msg_inicio_sistema() -> str:
    """Mensagem de início do orquestrador."""
    return (
        f"🚀 **SEXTA-FEIRA ADVANCED ONLINE**\n\n"
        f"🤖 Orquestrador V7 ativo\n"
        f"🧠 IA Anthropic integrada\n"
        f"📡 Monitorando: {', '.join(SYMBOLS_TO_SCAN)}\n\n"
        f"_Sistema operacional_"
    )

def msg_parada_sistema() -> str:
    """Mensagem de parada do sistema."""
    return (
        f"🛑 **SISTEMA PAUSADO**\n\n"
        f"⏰ {datetime.now().strftime('%d/%m %H:%M:%S')}\n"
        f"🔄 Reinicie manualmente para retomar\n\n"
        f"_Operações suspensas_"
    )

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
            # ✅ NOVA MENSAGEM PERSONALIZADA PARA FALHA
            log_and_alert("WARNING", msg_conexao_falha(user_id))
            logger.warning(f"⚠️ [{user_id}] Falha na conexão ou equity zero")
            return

        logger.info(f"✅ [{user_id}] Conectado | Equity: ${acc['equity']:.4f}")
        
        # ✅ NOVA MENSAGEM PERSONALIZADA PARA SUCESSO
        send_telegram_alert(msg_conexao_sucesso(user_id, acc['equity']), "success")

        for symbol in SYMBOLS_TO_SCAN:
            try:
                # ✅ FIX: client injetado via parâmetro — sem monkey-patch global
                signal = gerar_sinal(symbol, client=client)

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
                    if enviar_alerta_free and score >= 80:
                        enviar_alerta_free(ativo=symbol, direcao=direction, score=score)
                        logger.info(f"📢 Teaser enviado para Grupo Free: {symbol}")

                    # Executa ordem se estiver conectado
                    if USE_CLASS_CLIENT:
                        executar_ordem(client, symbol, direction, signal_data, user_id=user_id)
                    else:
                        executar_ordem(symbol, direction, price, stop, take, 0.01, score=score, user_id=user_id)
                        
            except Exception as e:
                log_and_alert("ERROR", f"[{user_id}-{symbol}] Erro no scan: {str(e)[:100]}")
                logger.debug(traceback.format_exc())

    except Exception as e:
        log_and_alert("CRITICAL", f"[{user_id}] Erro crítico: {str(e)[:100]}", "killswitch")
        logger.error(traceback.format_exc())

# ==========================================
# LOOP PRINCIPAL
# ==========================================
def _start_telegram_polling():
    """Inicia o polling do bot Telegram em thread daemon.
    ✅ FIX: só uma instância roda (dentro do main_saaS) — elimina conflito 409."""
    try:
        from telegram_bot import main as telegram_main
        t = threading.Thread(target=telegram_main, name="TelegramPolling", daemon=True)
        t.start()
        logger.info("✅ Telegram polling iniciado em thread daemon.")
    except Exception as e:
        logger.warning(f"⚠️ Telegram polling não iniciado: {e}")

def main():
    logger.info("🟣 SEXTA-FEIRA SAAS - ORQUESTRADOR V7 INICIADO")
    logger.info(f"🌐 Ambiente: {'Classe SaaS' if USE_CLASS_CLIENT else 'Legacy Global'}")

    # Inicia Telegram polling em thread (sem processo separado)
    _start_telegram_polling()

    # ✅ NOVA MENSAGEM DE INÍCIO PERSONALIZADA
    send_telegram_alert(msg_inicio_sistema(), "info")
    
    try:
        while not _shutdown_flag:
            vip_users = get_active_users()
            
            if not vip_users:
                logger.info("💤 Nenhum VIP ativo. Aguardando...")
            else:
                logger.info(f"👥 {len(vip_users)} VIP(s) ativo(s). Processando em paralelo...")
                # ✅ FIX 4: VIPs processados em paralelo — max 5 simultâneos
                def _run_vip(uid):
                    keys = get_user_credentials(uid)
                    if keys:
                        process_vip_user(uid, keys)
                    else:
                        log_and_alert("WARNING", msg_chaves_nao_encontradas(uid))
                        logger.warning(f"⚠️ [{uid}] Chaves não encontradas no DB")

                with ThreadPoolExecutor(max_workers=5) as pool:
                    futures = {pool.submit(_run_vip, uid): uid for uid in vip_users}
                    for future in as_completed(futures):
                        uid = futures[future]
                        try:
                            future.result()
                        except Exception as e:
                            logger.error(f"[{uid}] Falha na thread: {e}")

            logger.info(f"⏳ Próximo ciclo em {SCAN_INTERVAL}s...")
            time.sleep(SCAN_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info("🛑 Interrompido pelo usuário.")
        # ✅ NOVA MENSAGEM DE PARADA PERSONALIZADA
        send_telegram_alert(msg_parada_sistema(), "warning")
    except Exception as e:
        log_and_alert("CRITICAL", f"Falha fatal no orquestrador: {str(e)[:100]}", "crash")
        logger.critical(traceback.format_exc())

# ✅ CORRIGIDO: __name__
if __name__ == "__main__":
    main()