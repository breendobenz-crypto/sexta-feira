# webhook_whop.py - ENDPOINT PARA WHOP (FastAPI)
from fastapi import FastAPI, Request, HTTPException, Header
import hmac, hashlib, os, sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()
from saas_db import register_user, update_user_status

app = FastAPI()
WHOP_SECRET = os.getenv("WHOP_WEBHOOK_SECRET", "sua_chave_aqui")

def verify_signature(payload: bytes, signature: str) -> bool:
    expected = hmac.new(WHOP_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

@app.post("/whop/webhook")
async def whop_webhook(request: Request, x_whop_signature: str = Header(None)):
    body = await request.body()
    if not verify_signature(body, x_whop_signature):
        raise HTTPException(status_code=401, detail="Assinatura inválida")
    
    data = await request.json()
    event = data.get("event", {}).get("type")
    customer = data.get("customer", {})
    metadata = customer.get("metadata", {})
    
    user_id = metadata.get("user_id") or f"whop_{customer.get('id')}"
    name = customer.get("name") or "VIP User"
    email = customer.get("email")
    okx_key = metadata.get("okx_api_key")
    okx_secret = metadata.get("okx_api_secret")
    okx_pass = metadata.get("okx_passphrase")
    
    print(f"🔔 Webhook: {event} para {email}")
    
    if event == "subscription.created":
        if not all([okx_key, okx_secret, okx_pass]):
            return {"status": "pending_keys", "message": "Aguardando chaves OKX"}
        if register_user(user_id, name, email, okx_key, okx_secret, okx_pass):
            print(f"✅ {email} cadastrado como VIP!")
            return {"status": "success", "user_id": user_id}
        raise HTTPException(status_code=500, detail="Registration failed")
    
    elif event == "subscription.cancelled":
        update_user_status(user_id, "CANCELLED")
        print(f"🚫 Acesso de {email} cancelado.")
        return {"status": "cancelled"}
    
    elif event == "subscription.renewed":
        update_user_status(user_id, "ACTIVE")
        print(f"🔄 Acesso de {email} renovado.")
        return {"status": "renewed"}
    
    return {"status": "ignored"}

@app.get("/health")
def health(): return {"status": "ok"}