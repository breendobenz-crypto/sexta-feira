from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import os
import stripe
import requests
from datetime import datetime, timezone, timedelta
import saas_db

app = Flask(__name__)
CORS(app)

# ==========================================
# CONFIGURAÇÕES
# ==========================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_FREE_GROUP_ID = os.getenv("TELEGRAM_FREE_GROUP_ID")
TELEGRAM_VIP_GROUP_ID = os.getenv("TELEGRAM_VIP_GROUP_ID")
TELEGRAM_ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_FREE_PRICE_ID = os.getenv("STRIPE_FREE_PRICE_ID")
STRIPE_VIP_PRICE_ID = os.getenv("STRIPE_VIP_PRICE_ID")

# Links de pagamento
STRIPE_FREE_LINK = os.getenv("STRIPE_FREE_LINK", "https://buy.stripe.com/aFa7sE5wx6BVaXz1kK08g01")
STRIPE_VIP_LINK = os.getenv("STRIPE_VIP_LINK", "https://buy.stripe.com/3cI3co2kl0dx1mZ6F408g00")

# URLs de sucesso
SUCCESS_URL_FREE = os.getenv("SUCCESS_URL_FREE", f"https://t.me/+{TELEGRAM_FREE_GROUP_ID}")
SUCCESS_URL_VIP = os.getenv("SUCCESS_URL_VIP", "https://seusite.com/vip-ativado")

stripe.api_key = STRIPE_SECRET_KEY

# ==========================================
# FUNÇÕES TELEGRAM
# ==========================================

def send_telegram_message(chat_id: str, text: str, parse_mode: str = "Markdown"):
    """Envia mensagem via Telegram Bot API"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json().get("ok", False)
    except Exception as e:
        print(f"❌ Erro ao enviar Telegram: {e}")
        return False

def generate_free_invite_link():
    """Gera link de convite para o grupo FREE"""
    # Para grupo público, use o link direto
    return f"https://t.me/+{TELEGRAM_FREE_GROUP_ID}"

def generate_vip_invite_link():
    """Gera link de convite único para o grupo VIP"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/createChatInviteLink"
    payload = {
        "chat_id": TELEGRAM_VIP_GROUP_ID,
        "member_limit": 1,
        "name": f"VIP Access - {datetime.now().strftime('%Y-%m-%d')}"
    }
    try:
        response = requests.post(url, json=payload, timeout=10).json()
        if response.get("ok"):
            return response["result"]["invite_link"]
    except:
        pass
    return f"https://t.me/+{TELEGRAM_VIP_GROUP_ID}"

# ==========================================
# ROTAS PRINCIPAIS
# ==========================================

@app.route('/webhook/stripe-free-success', methods=['GET'])
def stripe_free_success():
    """
    Redireciona usuário para grupo FREE após checkout gratuito
    Chamar como success_url do Stripe FREE
    Ex: https://seusite.com/webhook/stripe-free-success?session_id={CHECKOUT_SESSION_ID}&user_id=123
    """
    session_id = request.args.get('session_id')
    user_id = request.args.get('user_id')
    telegram_chat_id = request.args.get('telegram_chat_id')
    
    if session_id and user_id:
        # Registra usuário como FREE
        saas_db.register_user_free(
            user_id=user_id,
            name=f"User_{user_id[-4:]}",
            email=f"{user_id}@temp.com",  # Pode ser atualizado depois
            telegram_chat_id=telegram_chat_id,
            stripe_session_id=session_id
        )
        
        # Envia mensagem de boas-vindas no Telegram se tiver chat_id
        if telegram_chat_id:
            free_link = generate_free_invite_link()
            send_telegram_message(telegram_chat_id, f"""
🎉 *Bem-vindo ao Sexta-Feira FREE!*

✅ Seu acesso gratuito foi ativado!

👥 Entre no grupo agora:
{free_link}

💡 *Quer acesso VIP com sinais premium?*
Digite `/vip` para ganhar 7 dias grátis!
            """)
    
    # Redireciona para o grupo FREE
    return redirect(SUCCESS_URL_FREE, code=302)

@app.route('/webhook/start-vip-trial', methods=['POST'])
def start_vip_trial():
    """Ativa trial VIP de 7 dias"""
    try:
        data = request.json
        bingx_uid = data.get('bingx_uid', '').strip()
        email = data.get('email', '').strip()
        telegram_chat_id = data.get('telegram_chat_id')
        
        if not all([bingx_uid, email, telegram_chat_id]):
            return jsonify({"status": "error", "text": "❌ Dados incompletos."}), 400
        
        # Ativa trial no banco
        saas_db.start_vip_trial(bingx_uid, email, telegram_chat_id, trial_days=7)
        
        # Gera link de convite VIP
        vip_link = generate_vip_invite_link()
        
        # Envia mensagem no PV
        send_telegram_message(telegram_chat_id, f"""
🚀 *TRIAL VIP ATIVADO!*

✅ Você tem **7 dias de acesso VIP** gratuito!

👥 Grupo VIP: {vip_link}

📊 Benefícios VIP:
• Sinais premium em tempo real
• Análises exclusivas
• Suporte prioritário

⏰ *Seu trial expira em 7 dias.*
Após isso, enviaremos o link para manter seu acesso vitalício!

Dúvidas? Digite `/ajuda`
        """)
        
        return jsonify({
            "status": "success",
            "text": f"✅ Trial VIP de 7 dias ativado!\n\nLink VIP: {vip_link}",
            "vip_link": vip_link,
            "trial_ends": (datetime.now() + timedelta(days=7)).strftime("%d/%m/%Y")
        })
        
    except Exception as e:
        return jsonify({"status": "error", "text": f"❌ Erro: {str(e)}"}), 500

@app.route('/webhook/send-payment-link', methods=['POST'])
def send_payment_link():
    """Envia link de pagamento VIP via Telegram (para trials expirados)"""
    try:
        data = request.json
        bingx_uid = data.get('bingx_uid')
        telegram_chat_id = data.get('telegram_chat_id')
        
        if not all([bingx_uid, telegram_chat_id]):
            return jsonify({"status": "error"}), 400
        
        # Envia mensagem com link de pagamento
        send_telegram_message(telegram_chat_id, f"""
⏰ *Seu trial VIP expirou!*

Mas não se preocupe - você pode manter seu acesso **VITALÍCIO** com um único pagamento! 💎

💰 *Oferta Especial:*
• Acesso vitalício ao grupo VIP
• Todos os benefícios premium
• Sem mensalidades!

🔗 *Garanta seu acesso agora:*
{STRIPE_VIP_LINK}

Após o pagamento, seu acesso será mantido automaticamente! 🎉

Dúvidas? Digite `/suporte`
        """)
        
        print(f"✅ Link de pagamento enviado para {bingx_uid} ({telegram_chat_id})")
        return jsonify({"status": "success"})
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Recebe confirmação de pagamento do Stripe (para VIP)"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        bingx_uid = session.get('metadata', {}).get('bingx_uid')
        customer_email = session.get('customer_details', {}).get('email')
        
        if bingx_uid:
            # Atualiza para LIFETIME
            saas_db.upgrade_to_lifetime(bingx_uid)
            
            # Busca usuário para pegar telegram_chat_id
            user = saas_db.get_user_by_email(customer_email) if customer_email else None
            
            # Envia confirmação
            if user and user.get('telegram_chat_id'):
                vip_link = generate_vip_invite_link()
                send_telegram_message(user['telegram_chat_id'], f"""
🎉 *PAGAMENTO CONFIRMADO!*

✅ Seu acesso VIP agora é **VITALÍCIO**! 💎

👥 Continue no grupo VIP:
{vip_link}

Obrigado por confiar no Sexta-Feira! 🚀
                """)
            
            print(f"✅ Pagamento confirmado! {bingx_uid} agora é VIP Vitalício.")
    
    return jsonify({'status': 'success'})

@app.route('/webhook/check-expired-trials', methods=['POST'])
def check_expired_trials():
    """Rota para verificar e notificar usuários com trial expirado"""
    try:
        expired = saas_db.get_expired_trials()
        notified = 0
        
        for user in expired:
            telegram_id = user.get('telegram_chat_id')
            bingx_uid = user.get('user_id')
            
            if telegram_id:
                # Envia link de pagamento
                send_payment_link({'bingx_uid': bingx_uid, 'telegram_chat_id': telegram_id})
                notified += 1
                
                # Atualiza status para "EXPIRED" para não notificar de novo
                saas_db.update_user_status(bingx_uid, "EXPIRED")
        
        return jsonify({
            "status": "success",
            "checked": len(expired),
            "notified": notified
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Rota de teste
@app.route('/webhook/test', methods=['GET'])
def test_webhook():
    return jsonify({
        "status": "online",
        "database": "PostgreSQL" if saas_db.USE_POSTGRES else "SQLite",
        "message": "Webhook server is running!"
    }), 200

# ==========================================
# INICIALIZAÇÃO
# ==========================================
if __name__ == '__main__':
    print("\n" + "="*60)
    print("🤖 WEBHOOK SERVER - SEXTA-FEIRA ADVANCED")
    print("="*60)
    print(f"💾 Banco: {'PostgreSQL' if saas_db.USE_POSTGRES else 'SQLite'}")
    print(f"📱 Telegram Bot: {'✅ Configurado' if TELEGRAM_BOT_TOKEN else '❌ Não configurado'}")
    print(f"💳 Stripe: {'✅ Configurado' if STRIPE_SECRET_KEY else '❌ Não configurado'}")
    print("="*60)
    print("\n📡 Rotas disponíveis:")
    print("   GET  /webhook/stripe-free-success  ← Redireciona ao grupo FREE")
    print("   POST /webhook/start-vip-trial     ← Ativa trial VIP 7 dias")
    print("   POST /webhook/send-payment-link   ← Envia link pagamento")
    print("   POST /webhook/stripe              ← Webhook Stripe VIP")
    print("   POST /webhook/check-expired-trials← Verifica trials expirados")
    print("   GET  /webhook/test                ← Teste de conexão")
    print("\n🚀 Iniciando servidor...")
    print("="*60 + "\n")
    
    saas_db.init_saas_db()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)