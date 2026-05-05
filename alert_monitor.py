# alert_monitor.py - Monitoramento de erros e alertas via Telegram
import os
import sys
import logging
import requests
import traceback
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ================= CONFIGURAÇÃO =================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")
ALERT_COOLDOWN = 300  # Segundos entre alertas do mesmo tipo (5 min)

# Cache interno para evitar spam
_alert_cache = {}

def send_telegram_alert(message: str, alert_type: str = "error", chat_id: str = None):
    """Envia alerta formatado para o Telegram. Suporta cooldown anti-spam."""
    global _alert_cache
    
    # Verifica cooldown
    now = datetime.now()
    last_sent = _alert_cache.get(alert_type)
    if last_sent and (now - last_sent).total_seconds() < ALERT_COOLDOWN:
        return  # Silencia alerta duplicado
    
    _alert_cache[alert_type] = now
    
    # Configura destino e emojis
    target_id = chat_id or TELEGRAM_ADMIN_ID
    emojis = {
        "error": "🚨", "warning": "⚠️", "info": "ℹ️", 
        "success": "✅", "killswitch": "🛑", "crash": "💥"
    }
    emoji = emojis.get(alert_type, "🔔")
    
    # Formata mensagem (Markdown)
    formatted = f"{emoji} *SEXTA-FEIRA ALERT*\n\n"
    formatted += f"🕒 {now.strftime('%d/%m %H:%M:%S')}\n"
    formatted += f"📋 {message}"
    
    # Envia via API
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": target_id,
        "text": formatted,
        "parse_mode": "Markdown"
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code != 200:
            logging.error(f"❌ Telegram API error: {resp.text}")
    except Exception as e:
        logging.error(f"❌ Falha ao enviar alerta Telegram: {e}")

def log_and_alert(level: str, message: str, alert_type: str = None):
    """Loga no console/arquivo E envia alerta se for ERROR/WARNING/CRITICAL."""
    type_map = {"ERROR": "error", "WARNING": "warning", "CRITICAL": "killswitch", "INFO": "info"}
    atype = alert_type or type_map.get(level, "info")
    
    if level == "ERROR": logging.error(message)
    elif level == "WARNING": logging.warning(message)
    elif level == "CRITICAL": logging.critical(message)
    else: logging.info(message)
    
    # Só notifica no Telegram se for relevante
    if level in ["ERROR", "WARNING", "CRITICAL"]:
        send_telegram_alert(message, atype)

def setup_global_crash_handler():
    """Captura exceções não tratadas (crashes) e notifica no Telegram."""
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # Formata traceback limitado a 1000 chars para não estourar limite do Telegram
        tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        tb_safe = tb_text[:1000].replace("`", "\\`")
        
        msg = f"💥 *CRASH DETECTADO*\n\n"
        msg += f"📦 Erro: `{exc_type.__name__}`\n"
        msg += f"📝 Detalhes: `{exc_value}`\n\n"
        msg += f" *Traceback:*\n```\n{tb_safe}\n```"
        
        send_telegram_alert(msg, "crash")
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    sys.excepthook = handle_exception

# Ativa o handler global ao importar
setup_global_crash_handler()

# ==========================================
# 💡 EXEMPLO DE USO NO main_saaS.py:
# ==========================================
# from alert_monitor import log_and_alert, send_telegram_alert
#
# # Em vez de: print("Erro ao conectar")
# log_and_alert("ERROR", f"Falha ao conectar na OKX para {user_id}")
#
# # Em vez de: logging.warning("Cooldown ativo")
# log_and_alert("WARNING", f"Cooldown ativo para {symbol}. Aguardando {cooldown}s")
#
# # Para enviar para grupo VIP específico:
# send_telegram_alert("🟢 Trade fechado com lucro: +$45.20", "success", chat_id=VIP_GROUP_ID)