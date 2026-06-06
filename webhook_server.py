from flask import Flask, request, jsonify, redirect, send_from_directory
from flask_cors import CORS
import os
import stripe
import requests
from datetime import datetime, timezone, timedelta

import saas_db

app = Flask(__name__)
CORS(app)

MASTER_PASSWORD = os.getenv("MASTER_PASSWORD", "SextaFeira2026!")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_FREE_GROUP_ID = os.getenv("TELEGRAM_FREE_GROUP_ID", "")
TELEGRAM_VIP_GROUP_ID = os.getenv("TELEGRAM_VIP_GROUP_ID", "")
TELEGRAM_ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID", "")

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_VIP_LINK = os.getenv("STRIPE_VIP_LINK", "https://buy.stripe.com/3cI3co2kl0dx1mZ6F408g00")
STRIPE_FREE_LINK = os.getenv("STRIPE_FREE_LINK", "https://buy.stripe.com/aFa7sE5wx6BVaXz1kK08g01")

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


def send_telegram_message(chat_id, text):
    if not TELEGRAM_BOT_TOKEN or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }, timeout=10)
        return resp.json().get("ok", False)
    except Exception as e:
        print(f"Erro Telegram: {e}")
        return False


@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')


@app.route('/webhook/test', methods=['GET'])
def test_webhook():
    return jsonify({
        "status": "online",
        "database": "PostgreSQL" if saas_db.USE_POSTGRES else "SQLite",
        "message": "Webhook server is running!",
        "routes": [
            "GET  /webhook/test",
            "POST /webhook/verificar-id",
            "POST /webhook/ativar-usuario-simples",
            "POST /webhook/stripe",
            "POST /webhook/stripe-free-success",
            "POST /webhook/notify-team"
        ]
    }), 200


@app.route('/webhook/verificar-id', methods=['POST'])
def verificar_id():
    try:
        data = request.json
        bingx_uid = data.get('bingx_uid', '').strip()
        print(f"RECEBIDO UID: {bingx_uid}")

        if not bingx_uid:
            return jsonify({"status": "error", "text": "ID nao informado"}), 400
        if not bingx_uid.isdigit():
            return jsonify({"status": "error", "text": "ID invalido"}), 400
        if len(bingx_uid) < 6 or len(bingx_uid) > 12:
            return jsonify({"status": "error", "text": "ID deve ter 6-12 digitos"}), 400

        conn = saas_db.get_db_connection()
        cursor = conn.cursor()
        if saas_db.USE_POSTGRES:
            cursor.execute("SELECT COUNT(*) FROM users WHERE user_id = %s", (bingx_uid,))
        else:
            cursor.execute("SELECT COUNT(*) FROM users WHERE user_id = ?", (bingx_uid,))
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        if count > 0:
            return jsonify({"status": "exists", "text": f"ID {bingx_uid} ja cadastrado", "bingx_uid": bingx_uid})

        return jsonify({"status": "success", "text": f"ID {bingx_uid} verificado!", "bingx_uid": bingx_uid, "is_new": True})
    except Exception as e:
        print(f"ERRO: {e}")
        return jsonify({"status": "error", "text": str(e)}), 500


@app.route('/webhook/ativar-usuario-simples', methods=['POST'])
def ativar_usuario_simples():
    try:
        data = request.json
        bingx_uid = data.get('bingx_uid', '').strip()
        email = data.get('email', '').strip()

        if not bingx_uid or not bingx_uid.isdigit():
            return jsonify({"status": "error", "text": "ID invalido"}), 400
        if not email or '@' not in email:
            return jsonify({"status": "error", "text": "Email invalido"}), 400

        existing = saas_db.get_user_by_email(email)
        if existing:
            return jsonify({"status": "already_exists", "text": "Email ja cadastrado"}), 400

        temp_password = f"SF{bingx_uid[-4:]}2026!"
        success = saas_db.register_user(
            user_id=bingx_uid,
            name=f"User_{bingx_uid[-4:]}",
            email=email,
            bingx_key='VAZIO', bingx_secret='VAZIO', bingx_passphrase='VAZIO'
        )

        if not success:
            return jsonify({"status": "error", "text": "Erro ao cadastrar"}), 500

        saas_db.set_user_password(email, temp_password)
        return jsonify({"status": "success", "text": f"Acesso liberado! Senha: {temp_password}", "temp_password": temp_password})
    except Exception as e:
        print(f"ERRO: {e}")
        return jsonify({"status": "error", "text": str(e)}), 500


@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    print("STRIPE Webhook recebido!")

    try:
        if STRIPE_WEBHOOK_SECRET:
            event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        else:
            event = request.json
    except Exception as e:
        print(f"Erro assinatura: {e}")
        return jsonify({"error": str(e)}), 400

    event_type = event.get('type')
    print(f"Evento: {event_type}")

    if event_type == 'checkout.session.completed':
        session = event.get('data', {}).get('object', {})
        customer_email = session.get('customer_details', {}).get('email')
        payment_status = session.get('payment_status')

        print(f"Pagamento {payment_status} - Email: {customer_email}")

        if customer_email and payment_status == 'paid':
            try:
                saas_db.upgrade_to_lifetime_by_email(customer_email)
                print(f"Usuario {customer_email} atualizado para LIFETIME!")

                user = saas_db.get_user_by_email(customer_email)
                if user and user.get('telegram_chat_id'):
                    send_telegram_message(
                        user['telegram_chat_id'],
                        f"🎉 *PAGAMENTO CONFIRMADO!*\n\nSeu acesso VIP agora é **VITALÍCIO**! 💎\n\nEmail: `{customer_email}`"
                    )
            except Exception as e:
                print(f"Erro ao atualizar usuario: {e}")

    return jsonify({"status": "success"}), 200


@app.route('/webhook/stripe-free-success', methods=['GET'])
def stripe_free_success():
    session_id = request.args.get('session_id')
    user_id = request.args.get('user_id')
    telegram_chat_id = request.args.get('telegram_chat_id')

    if session_id and user_id:
        try:
            saas_db.register_user_free(
                user_id=user_id,
                name=f"User_{user_id[-4:]}",
                email=f"{user_id}@temp.com",
                telegram_chat_id=telegram_chat_id,
                stripe_session_id=session_id
            )
        except Exception as e:
            print(f"Erro ao registrar free: {e}")

        if telegram_chat_id:
            free_link = f"https://t.me/+{TELEGRAM_FREE_GROUP_ID}" if TELEGRAM_FREE_GROUP_ID else ""
            send_telegram_message(telegram_chat_id, f"Bem-vindo ao Sexta-Feira FREE! Grupo: {free_link}")

    redirect_url = f"https://t.me/+{TELEGRAM_FREE_GROUP_ID}" if TELEGRAM_FREE_GROUP_ID else "/"
    return redirect(redirect_url, code=302)


@app.route('/webhook/notify-team', methods=['POST'])
def notify_team():
    try:
        data = request.json
        print(f"SUPORTE: {data}")
        return jsonify({"status": "notified"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("WEBHOOK SERVER - SEXTA-FEIRA (BINGX)")
    print("=" * 60)
    print(f"Banco: {'PostgreSQL' if saas_db.USE_POSTGRES else 'SQLite'}")
    print(f"Telegram: {'OK' if TELEGRAM_BOT_TOKEN else 'NAO'}")
    print(f"Stripe: {'OK' if STRIPE_SECRET_KEY else 'NAO'}")
    print(f"Corretora: BINGX")
    print("=" * 60)

    saas_db.init_saas_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)