# webhook_whop.py - ENDPOINT PARA WHOP (FastAPI)
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
    print("❌ ERRO CRÍTICO: Não foi possível importar saas_db. Verifique se o arquivo está na mesma pasta.")
    sys.exit(1)

app = FastAPI()

# Chave secreta do Webhook do Whop (Deve estar nas Variáveis de Ambiente do Render)
WHOP_SECRET = os.getenv("WHOP_WEBHOOK_SECRET", "")

def verify_signature(payload: bytes, signature: str) -> bool:
    """Verifica a assinatura HMAC do Whop para garantir que a requisição é legítima."""
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
    Recebe eventos do Whop (venda, cancelamento, etc).
    URL para configurar no Whop: https://seu-app.onrender.com/whop/webhook
    """
    try:
        # 1. Validar assinatura de segurança
        body = await request.body()
        if not verify_signature(body, x_whop_signature):
            raise HTTPException(status_code=401, detail="Assinatura inválida")

        data = await request.json()
        event_type = data.get("event", {}).get("type")
        
        # Estrutura de dados do Whop pode variar levemente, ajustando conforme o padrão
        customer = data.get("customer", {}) or data.get("data", {}).get("customer", {})
        metadata = customer.get("metadata", {}) or data.get("data", {}).get("metadata", {})
        
        # 2. Extrair dados essenciais
        user_id = metadata.get("user_id") or f"whop_{customer.get('id')}"
        name = customer.get("name") or "VIP User"
        email = customer.get("email")
        
        # Chaves OKX (Opcionais: se não vierem no metadata, salva vazio)
        okx_key = metadata.get("okx_api_key", "")
        okx_secret = metadata.get("okx_api_secret", "")
        okx_pass = metadata.get("okx_passphrase", "")

        print(f"🔔 Webhook recebido: {event_type} para {email}")

        if not email:
            raise ValueError("Email não encontrado nos dados do cliente")

        # 3. Lógica por Tipo de Evento
        
        if event_type in ["subscription.created", "order.completed"]:
            # Gerar senha temporária
            temp_pass = generate_password()
            
            # Registrar Usuário (Aceita chaves vazias se não forem enviadas)
            success = register_user(user_id, name, email, okx_key, okx_secret, okx_pass)
            
            if success:
                # Definir senha para permitir login imediato
                set_user_password(email, temp_pass)
                
                print(f"✅ VIP Criado com Sucesso: {email}")
                print(f"🔑 Senha Temporária Gerada: {temp_pass}")
                
                # IMPORTANTE: Em produção, você deve enviar essa senha por email/Telegram para o usuário.
                
                return {
                    "status": "success", 
                    "user_id": user_id,
                    "message": "Usuário criado com sucesso"
                }
            else:
                raise ValueError("Falha ao registrar no banco de dados")

        elif event_type == "subscription.cancelled":
            update_user_status(user_id, "CANCELLED")
            print(f"🚫 Acesso cancelado para {email}")
            return {"status": "cancelled"}

        elif event_type == "subscription.renewed":
            update_user_status(user_id, "ACTIVE")
            print(f"🔄 Acesso renovado para {email}")
            return {"status": "renewed"}

        return {"status": "ignored"}

    except Exception as e:
        print(f"❌ Erro no Webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}

# Para rodar localmente (apenas para testes)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)