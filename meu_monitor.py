# ==========================================
# WATCHDOG - SEXTA-FEIRA PRO (OKX)
# Reinicia o bot automaticamente após qualquer crash.
# Execute: python watchdog.py
# ==========================================
import subprocess
import sys
import time
import os
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [WATCHDOG] %(message)s",
    handlers=[
        logging.FileHandler("watchdog.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("watchdog")

MAIN_SCRIPT     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
RESTART_DELAY   = int(os.getenv("WATCHDOG_RESTART_SECONDS", "10"))
MAX_RESTARTS_1H = 10

restart_times = []


def too_many_restarts() -> bool:
    now    = time.time()
    recent = [t for t in restart_times if now - t < 3600]
    return len(recent) >= MAX_RESTARTS_1H


def notify_telegram(msg: str):
    try:
        import requests
        from dotenv import load_dotenv
        load_dotenv()
        token   = os.getenv("TELEGRAM_TOKEN", "")
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        if token and chat_id:
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": msg},
                timeout=5,
            )
    except Exception:
        pass


def run():
    log.info(f"Watchdog iniciado. Monitorando: {MAIN_SCRIPT}")
    notify_telegram("🐕 Watchdog OKX iniciado — Sexta-Feira supervisionada.")

    while True:
        if too_many_restarts():
            log.error(f"Mais de {MAX_RESTARTS_1H} reinícios em 1h. Watchdog pausado.")
            notify_telegram(f"🛑 Watchdog: {MAX_RESTARTS_1H}+ crashes em 1h. Verificação manual necessária.")
            for _ in range(360):
                time.sleep(10)
            restart_times.clear()
            continue

        log.info("Iniciando bot...")
        start = time.time()

        proc = subprocess.Popen(
            [sys.executable, MAIN_SCRIPT],
            cwd=os.path.dirname(MAIN_SCRIPT),
        )
        proc.wait()

        elapsed = time.time() - start
        code    = proc.returncode

        if code == 0:
            log.info("Bot encerrado normalmente (código 0). Saindo do watchdog.")
            break

        restart_times.append(time.time())
        log.warning(
            f"Bot encerrou com código {code} após {elapsed:.0f}s. "
            f"Reiniciando em {RESTART_DELAY}s... "
            f"(reinício #{len(restart_times)} na última hora)"
        )
        notify_telegram(
            f"⚠️ Bot OKX caiu (código {code}, uptime {elapsed:.0f}s). "
            f"Reiniciando em {RESTART_DELAY}s..."
        )
        time.sleep(RESTART_DELAY)


if __name__ == "__main__":
    run()
