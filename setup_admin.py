import psycopg2
import hashlib
import os

# ==========================================
# CONFIGURAÇÃO
# ==========================================

# ⚠️ COLE AQUI A URL EXTERNA DO SEU BANCO NO RENDER
# Ela começa com "postgresql://sextafeira_user..."
DATABASE_URL = "postgresql://sextafeira_user:tV57oiV1z4EgCfmP7fbvBKd4joBkvJ7b@dpg-d7t1fpugvqtc73a5s0eg-a.singapore-postgres.render.com/sextafeira"

SALT = "sexta-feira-advanced-vip-salt-2026"

def hash_password(password: str) -> str:
    """Cria o hash da senha igual ao sistema."""
    return hashlib.sha256((password + SALT).encode()).hexdigest()

try:
    print("🔄 Conectando ao banco no Render...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    email_admin = "admin@sextafeira.com"
    senha_admin = "123456"  # 👈 SENHA PADRÃO DO ADMIN
    nome_admin = "Admin Master"

    # 1. Verifica se o admin já existe
    cursor.execute("SELECT id FROM users WHERE email = %s", (email_admin,))
    existe = cursor.fetchone()

    if existe:
        print("✅ O usuário Admin já existe no banco.")
    else:
        print("🔨 Criando usuário Admin e Credenciais...")
        pwd_hash = hash_password(senha_admin)

        # 2. Cria o Usuário na tabela users
        cursor.execute("""
            INSERT INTO users (user_id, email, display_name, status, password_hash) 
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (email_admin, email_admin, nome_admin, 'ACTIVE', pwd_hash))
        
        user_id = cursor.fetchone()[0]

        # 3. Cria Credenciais Vazias (Placeholder) na tabela api_credentials
        # Usamos 'VAZIO' pois o script local não tem a chave de criptografia
        cursor.execute("""
            INSERT INTO api_credentials (user_id, api_key_enc, api_secret_enc, passphrase_enc) 
            VALUES (%s, %s, %s, %s)
        """, (user_id, 'VAZIO', 'VAZIO', 'VAZIO'))

        conn.commit()
        print("🎉 SUCESSO! Admin criado.")
        print(f"📧 Email: {email_admin}")
        print(f"🔑 Senha: {senha_admin}")
        print(f"🚀 Agora entre no site: https://sexta-feira-wm1s.onrender.com")

except Exception as e:
    print(f"❌ Erro ao conectar ou criar admin: {e}")
    print("💡 Verifique se você colou a URL EXTERNA correta.")
finally:
    if 'conn' in locals():
        conn.close()