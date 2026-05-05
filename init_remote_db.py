# init_remote_db.py - Cria admin no banco PostgreSQL do Render
import os
import hashlib
import psycopg2

# ==========================================
# CONFIGURAÇÕES (DEFINIDAS AQUI!)
# ==========================================
SALT = "sexta-feira-advanced-vip-salt-2026"

# ⚠️ COLE AQUI SUA DATABASE_URL DO RENDER (URL EXTERNA!)
DATABASE_URL = "postgresql://sextafeira_user:SENHA_AQUI@dpg-d7t1fpugvqtc73a5s0eg-a.db.rendervps.com:5432/sextafeira"

# Dados do admin (MUDE AQUI!)
EMAIL = "admin@sextafeira.com"
SENHA = "123456"  # ← Mude esta senha!
NOME = "Admin Sexta-Feira"

def hash_password(password: str) -> str:
    """Gera hash SHA256 da senha com salt."""
    return hashlib.sha256((password + SALT).encode()).hexdigest()

def main():
    print("🔄 Conectando ao banco no Render...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Criar usuário
        pwd_hash = hash_password(SENHA)
        cursor.execute("""
            INSERT INTO users (user_id, email, display_name, password_hash, status) 
            VALUES (%s, %s, %s, %s, 'ACTIVE')
            ON CONFLICT (user_id) DO NOTHING
            RETURNING id
        """, (EMAIL, EMAIL, NOME, pwd_hash))
        
        result = cursor.fetchone()
        
        if result:
            user_id = result[0]
            print(f"✅ Usuário criado com ID: {user_id}")
            
            # Criar credenciais vazias
            cursor.execute("""
                INSERT INTO api_credentials (user_id, api_key_enc, api_secret_enc, passphrase_enc)
                VALUES (%s, 'VAZIO', 'VAZIO', 'VAZIO')
                ON CONFLICT (user_id) DO NOTHING
            """, (user_id,))
            
            conn.commit()
            print(f"✅ Admin criado com sucesso!")
            print(f"📧 Email: {EMAIL}")
            print(f"🔑 Senha: {SENHA}")
            print(f"\n🚀 Agora acesse seu dashboard e faça login!")
        else:
            print("⚠️ Usuário já existe no banco")
            conn.rollback()
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        print("\n💡 Verifique se:")
        print("  1. A DATABASE_URL está correta (use a URL EXTERNA com .db.rendervps.com)")
        print("  2. O psycopg2 está instalado: pip install psycopg2-binary")
        print("  3. O banco está acessível")

if __name__ == "__main__":
    main()