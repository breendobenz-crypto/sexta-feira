# test_telegram.py - Teste simples de envio Telegram
import requests
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_FREE_GROUP_ID")

print(f"🔍 Token: {TOKEN[:20]}...")
print(f"🔍 Chat ID: {CHAT_ID}")

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
payload = {
    "chat_id": CHAT_ID,
    "text": "🧪 <b>TESTE DE CONEXÃO</b>\n\nSe você está lendo isso, o bot está funcionando!",
    "parse_mode": "HTML"
}

resp = requests.post(url, json=payload, timeout=10)
print(f"📡 Resposta: {resp.status_code}")
print(f"📦 Conteúdo: {resp.text}")