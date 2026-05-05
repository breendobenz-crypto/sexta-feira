# process_whop_form.py - Lê Google Forms e cadastra VIPs automaticamente
import os
import sys
import time
import json
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Configuração
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from saas_db import register_user

# ID da planilha do Google Forms
SPREADSHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")

# Caminho para o arquivo de credenciais (prioritário) ou fallback para env var
CREDS_FILE = os.getenv("GOOGLE_CREDS_FILE", "")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "{}")

def load_credentials():
    """Carrega credenciais do arquivo JSON ou da variável de ambiente."""
    try:
        # ✅ Prioridade: Arquivo JSON (evita problemas de escape no .env)
        if CREDS_FILE and os.path.exists(CREDS_FILE):
            return Credentials.from_service_account_file(
                CREDS_FILE,
                scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
            )
        
        # Fallback: Variável de ambiente (JSON em uma linha)
        if GOOGLE_CREDENTIALS and GOOGLE_CREDENTIALS != "{}":
            creds_info = json.loads(GOOGLE_CREDENTIALS)
            return Credentials.from_service_account_info(
                creds_info,
                scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
            )
        
        print("❌ Nenhuma credencial do Google encontrada.")
        return None
        
    except Exception as e:
        print(f"❌ Erro ao carregar credenciais: {e}")
        return None

def get_form_responses():
    """Lê as respostas mais recentes do Google Forms via Google Sheets API."""
    try:
        creds = load_credentials()
        if not creds:
            return []
            
        service = build("sheets", "v4", credentials=creds)
        
        # Lê a aba "Respostas ao formulário 1" (nome padrão)
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range="Respostas ao formulário 1!A2:E"
        ).execute()
        
        return result.get("values", [])
        
    except Exception as e:
        print(f"❌ Erro ao ler formulário: {e}")
        return []

def process_new_responses():
    """Processa respostas não processadas e cadastra VIPs."""
    PROCESSED_FILE = "processed_vips.txt"
    processed = set()
    
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
            processed = set(line.strip() for line in f)
    
    responses = get_form_responses()
    new_count = 0
    
    for row in responses:
        if len(row) < 5:
            continue
            
        timestamp = row[0]
        email = row[1]
        okx_key = row[2]
        okx_secret = row[3]
        okx_pass = row[4]
        user_id = row[5] if len(row) > 5 else f"whop_{email.split('@')[0]}"
        
        if email in processed:
            continue
            
        print(f"🔄 Processando: {email}")
        
        if register_user(user_id, email.split("@")[0], email, okx_key, okx_secret, okx_pass):
            print(f"✅ VIP cadastrado: {user_id}")
            new_count += 1
            with open(PROCESSED_FILE, "a", encoding="utf-8") as f:
                f.write(f"{email}\n")
        else:
            print(f"❌ Falha ao cadastrar {email}")
    
    return new_count

if __name__ == "__main__":
    print("🟣 Processador de Formulário Whop — Iniciado")
    while True:
        new = process_new_responses()
        if new > 0:
            print(f"✨ {new} novo(s) VIP(s) processado(s)")
        time.sleep(60)