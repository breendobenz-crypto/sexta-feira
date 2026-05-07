# webhook_whop.py - ENDPOINT FINAL (WHOP + DB + TELEGRAM AUTOMÁTICO)
from fastapi import FastAPI, Request, HTTPException, Header
import hmac, hashlib, os, sys, string, random, requests
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

try:
    from saas_db import register_user, update_user_status, set_user_password
except ImportError:
    print("❌ ERRO CRÍTICO: Não foi possível importar saas_db.")
    sys.exit(1)

app = FastAPI()

# ==========================================
# CONFIGURAÇÕES
# ==========================================
WHOP_SECRET = os.getenv("WHOP_WEBHOOK_SECRET", "")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
VIP_GROUP_ID = os.getenv("TELEGRAM_VIP_GROUP_ID", "")
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID", "")
DASHBOARD_URL = "https://sexta-feira-wm1s.onrender.com"

def verify_signature(payload: bytes, signature: str) -> bool:
    if not WHOP_SECRET: return False
    expected = hmac.new(WHOP_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

def generate_password(length=12):
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choices(characters, k=length))

def send_telegram(chat_id: str, text: str, btn_text: str = None, btn_url: str = None):
    if not BOT_TOKEN or not chat_id: return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if btn_text and btn_url:
        payload["reply_markup"] = {"inline_keyboard": [[{"text": btn_text, "url": btn_url}]]}
    try:
        return requests.post(url, json=payload, timeout=10).status_code == 200
    except Exception as e:
        print(f"⚠️ Erro Telegram: {e}")
        return False

@app.post("/whop/webhook")
async def whop_webhook(request: Request, x_whop_signature: str = Header(None)):
    body = await request.body()
    if x_whop_signature and not verify_signature(body, x_whop_signature):
        raise HTTPException(status_code=401, detail="Assinatura inválida")

    data = await request.json()
    event_type = data.get("event", {}).get("type") or data.get("type")
    customer = data.get("customer", {}) or data.get("data", {}).get("customer", {})
    email = customer.get("email", "")
    name = customer.get("name", "VIP User")
    final_user_id = f"whop_{customer.get('id', '')}" or email

    if not email:
        raise ValueError("Email não encontrado no payload")

    # ✅ COMPRA / ATIVAÇÃO
    if event_type in ["membership_activated", "order.completed"]:
        temp_pass = generate_password()
        success = register_user(final_user_id, name, email, "", "", "")
        
        if success:
            set_user_password(email, temp_pass)
            
            # 1. Notifica Grupo VIP com botão do Dashboard
            send_telegram(
                VIP_GROUP_ID,
                f"🎉 **Bem-vindo(a), {name}!**\n\nSeu acesso ao **Sexta-Feira Advanced** foi ativado.\nClique abaixo para abrir seu Dashboard VIP:",
                "📊 Abrir Dashboard",
                DASHBOARD_URL
            )
            
            # 2. Notifica Admin (você) com credenciais
            send_telegram(
                ADMIN_ID,
                f"🚀 **NOVA VENDA**\n👤 Nome: {name}\n📧 Email: {email}\n🔑 Senha Temp: `{temp_pass}`"
            )
            
            print(f"✅ VIP Criado: {email} | Senha: {temp_pass}")
            return {"status": "success", "user_id": final_user_id}
        raise ValueError("Falha ao registrar no banco")

    # ❌ CANCELAMENTO
    elif event_type in ["membership_deactivated", "membership_cancelled"]:
        update_user_status(final_user_id, "CANCELLED")
        print(f"🚫 Acesso cancelado para {email}")
        return {"status": "cancelled"}

    # ⏳ RENOVAÇÃO
    elif event_type == "membership_renewed":
        update_user_status(final_user_id, "ACTIVE")
        print(f"🔄 Acesso renovado para {email}")
        return {"status": "renewed"}

    return {"status": "ignored"}

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)