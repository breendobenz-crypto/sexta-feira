# hard_reset_saas.py
import os
import sqlite3
import sys
from dotenv import load_dotenv

# Força reload
if 'crypto_vault' in sys.modules: del sys.modules['crypto_vault']
if 'saas_db' in sys.modules: del sys.modules['saas_db']

load_dotenv()

from saas_db import init_saas_db, register_user, get_user_credentials

DB_NAME = "jarvis_saas.db"

print("💣 DELETANDO BANCO ANTIGO...")
for f in [DB_NAME, f"{DB_NAME}-shm", f"{DB_NAME}-wal"]:
    if os.path.exists(f):
        os.remove(f)
        print(f"🗑️ {f} removido.")

print("🏗️ RECRIANDO BANCO...")
init_saas_db()

print("👤 CADASTRANDO VIP...")
success = register_user(
    user_id="vip_test_01",
    name="Breendo Admin",
    email="breendo@test.com",
    okx_key=os.getenv("OKX_API_KEY"),
    okx_secret=os.getenv("OKX_API_SECRET"),
    okx_pass=os.getenv("OKX_PASSPHRASE")
)

if success:
    print("🔍 VERIFICANDO BANCO DIRETAMENTE (SQL)...")
    # Lê o banco cru para ver o que foi salvo
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT api_key_enc FROM api_credentials WHERE user_id = 'vip_test_01'")
    token_bruto = cursor.fetchone()[0]
    conn.close()

    print(f"🔒 Token no banco: {token_bruto[:20]}...")

    if token_bruto.startswith("gAAAAA"):
        print("✅ SUCESSO ABSOLUTO! O banco está criptografado.")
        print("🟢 AGORA RODE: python main_saaS.py")
    else:
        print("❌ FALHA: O saas_db.py não está criptografando. Verifique o arquivo.")
else:
    print("❌ Falha ao cadastrar usuário.")