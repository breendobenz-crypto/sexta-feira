import os
import hashlib
import psycopg2

# Configuração do banco
DATABASE_URL = os.getenv("DATABASE_URL")
SALT = "sexta-feira-advanced-vip-salt-2026"

def hash_password(password: str) -> str:
    return hashlib.sha256((password + SALT).encode()).hexdigest()

# Dados do admin (MUDE AQUI!)
EMAIL = "admin@sextafeira.com"
SENHA = "123456"  # ← Mude esta senha!
NOME = "Admin Sexta-Feira"

print("🔄 Criando usuário admin...")

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

try:
    # Criar usuário
    pwd_hash = hash_password(SENHA)
    cursor.execute("""
        INSERT INTO users (user_id, email, display_name, password_hash, status) 
        VALUES (%s, %s, %s, %s, 'ACTIVE')
        ON CONFLICT (user_id) DO NOTHING
        RETURNING id
    """, (EMAIL, EMAIL, NOME, pwd_hash))
    
    user_id = cursor.fetchone()
    if user_id:
        # Criar credenciais vazias
        cursor.execute("""
            INSERT INTO api_credentials (user_id, api_key_enc, api_secret_enc, passphrase_enc)
            VALUES (%s, 'VAZIO', 'VAZIO', 'VAZIO')
            ON CONFLICT (user_id) DO NOTHING
        """, (user_id[0],))
        conn.commit()
        print(f"✅ Admin criado com sucesso!")
        print(f"📧 Email: {EMAIL}")
        print(f"🔑 Senha: {SENHA}")
    else:
        print("⚠️ Usuário já existe")
        
except Exception as e:
    print(f"❌ Erro: {e}")
    conn.rollback()
finally:
    cursor.close()
    conn.close()