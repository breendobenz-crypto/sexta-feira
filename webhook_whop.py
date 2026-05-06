# webhook_whop.py - INTEGRAÇÃO COMPLETA (WHOP + DB + TELEGRAM)
from fastapi import FastAPI, Request, HTTPException, Header
import hmac
import hashlib
import os
import sys
import string
import random
import requests
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
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID", "")
VIP_GROUP_ID = os.getenv("TELEGRAM_VIP_GROUP_ID", "")
BASE_URL = "https://sexta-feira-wm1s.onrender.com"

def verify_signature(payload: bytes, signature: str) -> bool:
    if not WHOP_SECRET:
        return False
    expected_signature = hmac.new(
        WHOP_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)

def generate_password(length=10):
    characters = string.ascii_letters + string.digits + "!@#$"
    return ''.join(random.choices(characters, k=length))

def get_telegram_invite_link():
    """Gera um link de convite único (expira após 1 uso) para o grupo VIP."""
    if not BOT_TOKEN or not VIP_GROUP_ID:
        return "Erro: Configuração do Telegram ausente."
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/createChatInviteLink"
    payload = {
        "chat_id": VIP_GROUP_ID,
        "member_limit": 1,  # Link serve para apenas 1 pessoa
        "name": "Acesso VIP Whop"
    }
    
    try:
        response = requests.post(url, json=payload)
        data = response.json()
        if data.get("ok"):
            return data["result"]["invite_link"]
        return "Erro ao gerar link"
    except Exception as e:
        return f"Erro: {str(e)}"

def notify_admin(message: str):
    """Envia mensagem para o Admin no Telegram."""
    if not BOT_TOKEN or not ADMIN_ID:
        return
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": ADMIN_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, json=payload)

@app.post("/whop/webhook")
async def whop_webhook(request: Request, x_whop_signature: str = Header(None)):
    try:
        body = await request.body()
        
        # Validação de segurança
        if x_whop_signature and not verify_signature(body, x_whop_signature):
            raise HTTPException(status_code=401, detail="Assinatura inválida")

        data = await request.json()
        event_type = data.get("event", {}).get("type") or data.get("type")
        
        customer = data.get("customer", {}) or data.get("data", {}).get("customer", {})
        user_id_whop = customer.get("id", "")
        email = customer.get("email", "")
        name = customer.get("name", "VIP User")
        
        final_user_id = f"whop_{user_id_whop}" if user_id_whop else email
        print(f"🔔 Webhook recebido: {event_type} para {email}")

        if not email:
            raise ValueError("Email não encontrado")

        # ==========================================
        # 🟢 EVENTO: MEMBRO ATIVADO (COMPRA/RENOVAÇÃO)
        # ==========================================
        if event_type in ["membership_activated", "order.completed"]:
            
            temp_pass = generate_password()
            
            # 1. Registra no Banco de Dados (Chaves OKX vazias por enquanto)
            success = register_user(final_user_id, name, email, "", "", "")
            
            if success:
                set_user_password(email, temp_pass)
                
                # 2. Gera Link do Grupo VIP
                invite_link = get_telegram_invite_link()
                
                # 3. Monta a mensagem para o Admin
                msg = f"""
🚀 <b>NOVA VENDA REALIZADA!</b>

👤 <b>Cliente:</b> {name}
📧 <b>Email:</b> {email}
🔑 <b>Senha Temp:</b> {temp_pass}

🔗 <b>Link Dashboard:</b>
{BASE_URL}

📲 <b>Link Grupo VIP (1 uso):</b>
{invite_link}

<i>Envie a senha e o link para o cliente iniciar!</i>
                """
                
                # 4. Notifica Você (Admin) no Telegram
                notify_admin(msg)
                
                print(f"✅ VIP {email} criado e Admin notificado.")
                
                return {"status": "success", "user_id": final_user_id}
            else:
                raise ValueError("Falha ao registrar no banco")

        # ==========================================
        # 🔴 EVENTO: CANCELAMENTO
        # ==========================================
        elif event_type in ["membership_deactivated", "membership_cancelled"]:
            update_user_status(final_user_id, "CANCELLED")
            print(f"🚫 Acesso de {email} cancelado.")
            
            notify_admin(f"🚫 <b>CANCELAMENTO</b>\nUsuário {email} teve o acesso cortado.")
            return {"status": "cancelled"}

        return {"status": "ignored"}

    except Exception as e:
        print(f"❌ Erro no Webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)