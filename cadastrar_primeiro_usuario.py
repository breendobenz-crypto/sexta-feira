# cadastrar_primeiro_usuario.py
import sqlite3
import hashlib
from crypto_vault import encrypt_key

DB_NAME = "jarvis_saas.db"
SALT = "sexta-feira-advanced-vip-salt-2026"

def hash_password(password: str) -> str:
    return hashlib.sha256((password + SALT).encode()).hexdigest()

# Dados do primeiro usuário
EMAIL = "seu@email.com"  # ← MUDE AQUI
SENHA = "SuaSenha123"    # ← MUDE AQUI
NOME = "Seu Nome"        # ← MUDE AQUI

# Criptografar senha
pwd_hash = hash_password(SENHA)

# Conectar ao banco
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Inserir usuário
cursor.execute("""
    INSERT OR REPLACE INTO users (user_id, email, display_name, password_hash, status)
    VALUES (?, ?, ?, ?, 'ACTIVE')
""", (EMAIL, EMAIL, NOME, pwd_hash))

conn.commit()
conn.close()

print(f"✅ Usuário cadastrado com sucesso!")
print(f"📧 Email: {EMAIL}")
print(f"🔑 Senha: {SENHA}")
print(f"\nAgora você pode fazer login no dashboard!")