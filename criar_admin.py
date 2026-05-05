import sqlite3
import hashlib

# Configurações
DB_NAME = "jarvis_saas.db"
SALT = "sexta-feira-advanced-vip-salt-2026"

# ==========================================
# ⚠️ DADOS DO SEU PRIMEIRO ACESSO (MUDE AQUI)
# ==========================================
EMAIL = "breendobenz@gmail.com"  # ← Coloque seu email aqui
NOME = "breendobenz"      # ← Seu nome
SENHA = "123456"                # ← Sua senha de acesso
# ==========================================

def hash_password(password: str) -> str:
    """Gera o hash da senha para salvar no banco."""
    return hashlib.sha256((password + SALT).encode()).hexdigest()

def main():
    print("🔄 Criando usuário VIP no banco de dados...")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        # 1. Gerar hash da senha
        pwd_hash = hash_password(SENHA)
        
        # 2. Inserir usuário na tabela 'users'
        # status='ACTIVE' permite login imediato
        cursor.execute("""
            INSERT INTO users (user_id, email, display_name, password_hash, status) 
            VALUES (?, ?, ?, ?, 'ACTIVE')
        """, (EMAIL, EMAIL, NOME, pwd_hash))
        
        # 3. Pegar o ID do usuário criado
        cursor.execute("SELECT id FROM users WHERE email = ?", (EMAIL,))
        user_id = cursor.fetchone()[0]
        
        # 4. Inserir credenciais vazias (placeholder) na tabela 'api_credentials'
        # Isso evita erros se o sistema tentar buscar chaves que não existem
        cursor.execute("""
            INSERT OR REPLACE INTO api_credentials (user_id, api_key_enc, api_secret_enc, passphrase_enc)
            VALUES (?, 'VAZIO', 'VAZIO', 'VAZIO')
        """, (user_id,))
        
        conn.commit()
        
        print("✅ SUCESSO! Usuário cadastrado.")
        print(f" Nome: {NOME}")
        print(f"📧 Email: {EMAIL}")
        print(f"🔑 Senha: {SENHA}")
        print("\n🚀 Agora acesse o dashboard e faça login com esses dados!")
        
    except sqlite3.IntegrityError:
        print("⚠️ AVISO: Este email já está cadastrado no banco.")
    except Exception as e:
        print(f"❌ ERRO: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()