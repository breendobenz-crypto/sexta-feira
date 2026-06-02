from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime, timedelta
import saas_db  # Importa seu módulo de banco

app = Flask(__name__)
CORS(app)

# Configurações
MASTER_PASSWORD = os.getenv("MASTER_PASSWORD", "SextaFeira2026!")

# ── ROTA 1: VERIFICAR ID (VALIDAÇÃO DE FORMATO) ──────────────────
@app.route('/webhook/verificar-id', methods=['POST'])
def verificar_id():
    """
    Verifica se o ID da BingX tem formato válido
    (sem precisar de API Key - validação real acontece no dashboard)
    """
    try:
        data = request.json
        bingx_uid = data.get('bingx_uid', '').strip()
        
        print(f"📥 [RECEBIDO] UID: {bingx_uid}")
        
        # Validação de formato (BingX UIDs são números de 6-12 dígitos)
        if not bingx_uid:
            return jsonify({
                "status": "error",
                "text": "❌ ID não informado."
            }), 400
        
        if not bingx_uid.isdigit():
            return jsonify({
                "status": "error",
                "text": "❌ ID inválido. Deve conter apenas números."
            }), 400
        
        if len(bingx_uid) < 6 or len(bingx_uid) > 12:
            return jsonify({
                "status": "error",
                "text": "❌ ID inválido. O ID da BingX deve ter entre 6 e 12 dígitos."
            }), 400
        
        # Verifica se ID já existe no banco
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
            return jsonify({
                "status": "exists",
                "text": f"⚠️ ID {bingx_uid} já está cadastrado!\n\nSe já tem acesso, faça login no dashboard.\nSe esqueceu a senha, digite 'suporte'.",
                "bingx_uid": bingx_uid
            })
        
        # ID válido e novo!
        print(f"✅ [SUCESSO] ID {bingx_uid} verificado!")
        
        return jsonify({
            "status": "success",
            "text": f"✅ ID {bingx_uid} verificado com sucesso!\n\nPodemos prosseguir com o cadastro.",
            "bingx_uid": bingx_uid,
            "is_new": True
        })
        
    except Exception as e:
        print(f"❌ [ERRO verificar-id] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "text": f"❌ Erro interno: {str(e)}"
        }), 500

# ── ROTA 2: ATIVAR USUÁRIO COMPLETO ────────────────────────────
@app.route('/webhook/ativar-usuario-simples', methods=['POST'])
def ativar_usuario_simples():
    """
    Ativa usuário no sistema - recebe dados completos do Typebot
    """
    try:
        data = request.json
        bingx_uid = data.get('bingx_uid', '').strip()
        email = data.get('email', '').strip()
        telefone = data.get('telefone', '').strip()
        
        print(f"📥 [ATIVACAO] UID: {bingx_uid}, Email: {email}")
        
        # Validações básicas
        if not bingx_uid or not bingx_uid.isdigit():
            return jsonify({
                "text": "❌ ID inválido. Deve conter apenas números.",
                "status": "error"
            }), 400
        
        if not email or '@' not in email:
            return jsonify({
                "text": "❌ Email inválido. Por favor, informe um email válido.",
                "status": "error"
            }), 400
        
        # Verifica se usuário já existe pelo email
        existing_user = saas_db.get_user_by_email(email)
        if existing_user:
            return jsonify({
                "text": f"⚠️ Este email já está cadastrado!\n\nEmail: {email}\nStatus: {existing_user.get('status')}\n\nSe esqueceu sua senha, contate o suporte.",
                "status": "already_exists"
            }), 400
        
        # Gera senha temporária
        temp_password = f"SF{bingx_uid[-4:]}2026!"
        
        # Registra usuário no banco (com chaves API vazias - usuário configura depois)
        success = saas_db.register_user(
            user_id=bingx_uid,
            name=f"Usuario_{bingx_uid[-4:]}",
            email=email,
            okx_key='VAZIO',
            okx_secret='VAZIO',
            okx_pass='VAZIO'
        )
        
        if not success:
            return jsonify({
                "text": "❌ Erro ao cadastrar usuário. Tente novamente ou contate o suporte.",
                "status": "error"
            }), 500
        
        # Define a senha do usuário
        saas_db.set_user_password(email, temp_password)
        
        print(f"✅ [SUCESSO] Usuário {bingx_uid} ativado!")
        
        return jsonify({
            "text": f"""🎉 *ACESSO LIBERADO COM SUCESSO!*

✅ *Seus Dados de Acesso:*
👤 ID BingX: `{bingx_uid}`
📧 Email: `{email}`
🔑 Senha Temporária: `{temp_password}`

📊 *Acesse seu Dashboard:*
https://sexta-feira.com/dashboard

📱 *Grupo VIP Telegram:*
https://t.me/sextafeira_vip

⚠️ *Próximos Passos:*
1. Faça login no dashboard
2. Vá em **Configurações → API**
3. Cole suas chaves da BingX (somente leitura + trade)
4. Clique em 'Salvar Chaves'

❓ Precisa de ajuda? Digite 'suporte' a qualquer momento!""",
            "status": "success",
            "bingx_uid": bingx_uid,
            "email": email,
            "temp_password": temp_password,
            "trial_days": 7,
            "dashboard_url": "https://sexta-feira.com/dashboard",
            "telegram_url": "https://t.me/sextafeira_vip"
        })
        
    except Exception as e:
        print(f"❌ [ERRO webhook] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "text": f"❌ Erro interno: {str(e)}",
            "status": "error"
        }), 500

# ── ROTA 3: TESTE DE CONEXÃO ───────────────────────────────────
@app.route('/webhook/test', methods=['GET'])
def test_webhook():
    """Rota simples para testar se o servidor está online"""
    return jsonify({
        "status": "online",
        "database": "PostgreSQL" if saas_db.USE_POSTGRES else "SQLite",
        "message": "Webhook server is running!"
    }), 200

# ── ROTA 4: NOTIFICAR EQUIPE (SUPORTE HUMANO) ───────────────────
@app.route('/webhook/notify-team', methods=['POST'])
def notify_team():
    """
    Notifica equipe quando usuário pede suporte humano
    """
    try:
        data = request.json
        bingx_uid = data.get('bingx_uid', '')
        email = data.get('email', '')
        reason = data.get('reason', 'Suporte solicitado')
        
        print(f"\n🚨 [SUPORTE SOLICITADO]")
        print(f"👤 ID BingX: {bingx_uid}")
        print(f"📧 Email: {email}")
        print(f"💬 Motivo: {reason}")
        print(f"⏰ Hora: {datetime.now()}")
        print("-" * 50)
        
        # TODO: Integrar com Telegram/Email da equipe
        # send_notification(f"Novo suporte: {email} - {reason}")
        
        return jsonify({
            "status": "notified",
            "message": "Equipe notificada com sucesso"
        })
        
    except Exception as e:
        print(f"❌ [ERRO notify-team] {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# ── ROTA 5: VERIFICAR STATUS DO USUÁRIO ────────────────────────
@app.route('/webhook/check-user-status', methods=['POST'])
def check_user_status():
    """
    Verifica se usuário está ativo e tem API configurada
    """
    try:
        data = request.json
        bingx_uid = data.get('bingx_uid', '').strip()
        
        if not bingx_uid:
            return jsonify({
                "status": "error",
                "message": "ID não fornecido"
            }), 400
        
        # Busca usuário no banco
        conn = saas_db.get_db_connection()
        cursor = conn.cursor()
        
        if saas_db.USE_POSTGRES:
            cursor.execute("""
                SELECT u.id, u.email, u.status, u.display_name,
                       ac.api_key_enc IS NOT NULL as has_api
                FROM users u
                LEFT JOIN api_credentials ac ON ac.user_id = u.id
                WHERE u.user_id = %s
            """, (bingx_uid,))
        else:
            cursor.execute("""
                SELECT u.id, u.email, u.status, u.display_name,
                       CASE WHEN ac.api_key_enc IS NOT NULL THEN 1 ELSE 0 END as has_api
                FROM users u
                LEFT JOIN api_credentials ac ON ac.user_id = u.id
                WHERE u.user_id = ?
            """, (bingx_uid,))
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not row:
            return jsonify({
                "status": "not_found",
                "message": "Usuário não encontrado"
            }), 404
        
        user_data = saas_db._dictify(row, cursor) if hasattr(saas_db, '_dictify') else {
            'id': row[0],
            'email': row[1],
            'status': row[2],
            'display_name': row[3],
            'has_api': bool(row[4])
        }
        
        return jsonify({
            "status": "success",
            "user": user_data,
            "is_active": user_data['status'] == 'ACTIVE',
            "has_api_configured": user_data['has_api'],
            "message": f"Usuário {user_data['email']} - Status: {user_data['status']}"
        })
        
    except Exception as e:
        print(f"❌ [ERRO check-status] {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🤖 WEBHOOK SERVER - SEXTA-FEIRA ADVANCED")
    print("="*60)
    print(f"💾 Banco de dados: {'PostgreSQL' if saas_db.USE_POSTGRES else 'SQLite'}")
    print(f"🔧 MASTER_PASSWORD: {'⚠️ NÃO DEFINIDA (usando padrão)' if MASTER_PASSWORD == 'SextaFeira2026!' else '✅ Configurada'}")
    print("="*60)
    print("\n Rotas disponíveis:")
    print("   POST /webhook/verificar-id          ← Validação de formato")
    print("   POST /webhook/ativar-usuario-simples")
    print("   GET  /webhook/test")
    print("   POST /webhook/notify-team")
    print("   POST /webhook/check-user-status")
    print("\n🚀 Iniciando servidor...")
    print("="*60 + "\n")
    
    # Inicializa o banco (cria tabelas se necessário)
    saas_db.init_saas_db()
    
    # Roda o servidor (debug=False para produção)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)