# form_processor.py - PROCESSADOR AUTOMÁTICO DE CADASTRO VIP
import os
import sys
import time
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

# Imports do seu sistema
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from saas_db import register_user
from crypto_vault import encrypt_key

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

# Configurações Google Sheets
SHEET_URL = os.getenv("GOOGLE_SHEET_URL", "https://docs.google.com/spreadsheets/d/SEU_ID_AQUI/edit")
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS_FILE = os.getenv("GOOGLE_CREDS_FILE", "google_creds.json")

# Processados (para não duplicar)
PROCESSED_FILE = "processed_vips.txt"

def load_processed():
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, "r") as f:
            return set(line.strip() for line in f)
    return set()

def save_processed(email):
    with open(PROCESSED_FILE, "a") as f:
        f.write(f"{email}\n")

def connect_to_sheet():
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
    client = gspread.authorize(creds)
    return client.open_by_url(SHEET_URL).sheet1

def process_new_signups():
    """Lê planilha e registra VIPs novos no banco."""
    try:
        sheet = connect_to_sheet()
        rows = sheet.get_all_records()
        processed = load_processed()
        new_count = 0
        
        for row in rows:
            email = row.get("Email", "").strip().lower()
            if not email or email in processed:
                continue
            
            # Dados do formulário
            name = row.get("Nome", "").strip()
            api_key = row.get("API Key OKX", "").strip()
            api_secret = row.get("API Secret OKX", "").strip()
            passphrase = row.get("Passphrase OKX", "").strip()
            
            if not all([name, email, api_key, api_secret, passphrase]):
                logger.warning(f"⚠️ Dados incompletos para {email}")
                continue
            
            # Registra no banco (criptografa automaticamente)
            if register_user(email, name, email, api_key, api_secret, passphrase):
                save_processed(email)
                new_count += 1
                logger.info(f"✅ VIP registrado: {name} ({email})")
                
                # Notifica no Telegram (opcional)
                try:
                    import telegram_bot as tg
                    if tg.TOKEN and tg.ADMIN_ID:
                        tg._send(f"🎉 *Novo VIP cadastrado!*\n\n👤 {name}\n📧 {email}", chat_id=tg.ADMIN_ID)
                except:
                    pass
            else:
                logger.error(f"❌ Falha ao registrar {email}")
        
        if new_count > 0:
            logger.info(f"📊 {new_count} novo(s) VIP(s) processado(s)")
        return new_count
        
    except Exception as e:
        logger.error(f"❌ Erro no processamento: {e}")
        return 0

def main():
    logger.info("🔄 Processador de Cadastro VIP iniciado")
    while True:
        try:
            process_new_signups()
        except Exception as e:
            logger.error(f"❌ Erro no loop principal: {e}")
        time.sleep(300)  # Verifica a cada 5 minutos

if __name__ == "__main__":
    main()