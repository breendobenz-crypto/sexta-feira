# webhook_whop.py - ENDPOINT FINAL PARA WHOP (V1 API)
from fastapi import FastAPI, Request, HTTPException, Header
import hmac
import hashlib
import os
import sys
import string
import random
from dotenv import load_dotenv

# Configurar caminho para garantir que o saas_db seja encontrado
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

try:
    from saas_db import register_user, update_user_status, set_user_password
except ImportError:
    print("❌ ERRO CRÍTICO: Não foi possível importar saas_db.")
    sys.exit(1)

app = FastAPI()

# Chave secreta do Webhook do Whop (Já configurada no seu Render!)
WHOP_SECRET = os.getenv("WHOP_WEBHOOK_SECRET", "")

def verify_signature(payload: bytes, signature: str) -> bool:
    """Verifica a assinatura HMAC do Whop."""
    if not WHOP_SECRET:
        return False
    expected_signature = hmac.new(
        WHOP_SECRET.encode(), 
        payload, 
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)

def generate_password(length=12):
    """Gera uma senha temporária segura."""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choices(characters, k=length))

@app.post("/whop/webhook")
async def whop_webhook(request: Request, x_whop_signature: str = Header(None)):
    """
    Recebe eventos do Whop (V1 API).
    URL: https://sexta-feira-wm1s.onrender.com/whop/webhook
    """
    try:
        # 1. Validar assinatura de segurança
        body = await request.body()
        
        # Se não tiver assinatura no header (testes locais), ignora a verificação
        if x_whop_signature and not verify_signature(body, x_whop_signature):
            raise HTTPException(status_code=401, detail="Assinatura inválida")

        data = await request.json()
        
        # Na V1 da Whop, o evento vem em data.event.type ou data.type
        event_type = data.get("event", {}).get("type") or data.get("type")
        
        # Dados do cliente (pode variar levemente dependendo do payload)
        customer = data.get("customer", {}) or data.get("data", {}).get("customer", {})
        user_id_whop = customer.get("id", "")
        email = customer.get("email", "")
        name = customer.get("name", "VIP User")
        
        # Tentar pegar ID do usuário da Whop para usar como ID único
        final_user_id = f"whop_{user_id_whop}" if user_id_whop else email

        print(f"🔔 Webhook recebido: {event_type} para {email}")

        if not email:
            raise ValueError("Email não encontrado no payload")

        # 2. Lógica por Tipo de Evento (Mapeado para o que você selecionou no Whop)
        
        # ✅ QUANDO ALGUÉM COMPRA / ASSINA
        if event_type in ["membership_activated", "order.completed"]:
            temp_pass = generate_password()
            
            # Registra o VIP (chaves OKX vazias, ele configura depois)
            success = register_user(final_user_id, name, email, "", "", "")
            
            if success:
                # Define a senha para ele poder logar
                set_user_password(email, temp_pass)
                
                print(f"✅ VIP Criado: {email} | Senha Temp: {temp_pass}")
                
                return {
                    "status": "success", 
                    "user_id": final_user_id,
                    "message": "Usuário criado com sucesso"
                }
            else:
                raise ValueError("Falha ao registrar no banco")

        # ❌ QUANDO A ASSINATURA CANCELADA / DESATIVADA
        elif event_type in ["membership_deactivated", "membership_cancelled"]:
            update_user_status(final_user_id, "CANCELLED")
            print(f"🚫 Acesso cancelado para {email}")
            return {"status": "cancelled"}

        # ⏳ QUANDO RENOVADA
        elif event_type in ["membership_renewed"]:
            update_user_status(final_user_id, "ACTIVE")
            print(f"🔄 Acesso renovado para {email}")
            return {"status": "renewed"}

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