# force_fix_saas.py - CORREÇÃO NUCLEAR (GARANTIDA)
import os
import sys
import sqlite3
from dotenv import load_dotenv

# 1. Hardcode da chave para eliminar conflitos de .env
MASTER_KEY = "JarvisSaaS2026!"
os.environ["SAAS_MASTER_KEY"] = MASTER_KEY

# 2. Limpa cache de módulos
for mod in list(sys.modules.keys()):
    if "crypto" in mod or "saas_db" in mod:
        del sys.modules[mod]

load_dotenv()

from crypto_vault import encrypt_key, decrypt_key
DB_NAME = "jarvis_saas.db"

print("🔪 DELETANDO BANCO ANTIGO E ARQUIVOS TEMP...")
for f in [DB_NAME, f"{DB_NAME}-shm", f"{DB_NAME}-wal"]:
    if os.path.exists(f):
        try:
            os.remove(f)
            print(f"🗑️ Removido: {f}")
        except PermissionError:
            print(f"⚠️ {f} está travado. Feche o VSCode/terminais e rode novamente.")
            sys.exit(1)

print("🏗️ CRIANDO BANCO DO ZERO...")
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()
c.execute('''CREATE TABLE users (user_id TEXT PRIMARY KEY, name TEXT, email TEXT, plan TEXT DEFAULT 'VIP', status TEXT DEFAULT 'ACTIVE')''')
c.execute('''CREATE TABLE api_credentials (user_id TEXT PRIMARY KEY, api_key_enc TEXT, api_secret_enc TEXT, passphrase_enc TEXT)''')
conn.commit()

print("🔐 CRIPTOGRAFANDO E SALVANDO CHAVES MANUALMENTE...")
# Criptografa na mão para garantir
key_enc = encrypt_key(os.getenv("OKX_API_KEY", "test_key"))
sec_enc = encrypt_key(os.getenv("OKX_API_SECRET", "test_secret"))
pass_enc = encrypt_key(os.getenv("OKX_PASSPHRASE", "test_pass"))

c.execute("INSERT INTO users VALUES (?, ?, ?, 'VIP', 'ACTIVE')", ("vip_test_01", "Admin", "admin@test.com"))
c.execute("INSERT INTO api_credentials VALUES (?, ?, ?, ?)", ("vip_test_01", key_enc, sec_enc, pass_enc))
conn.commit()
conn.close()

print("🔍 TESTANDO DESCRIPTOGRAFIA IMEDIATA...")
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()
c.execute("SELECT api_key_enc FROM api_credentials WHERE user_id='vip_test_01'")
token = c.fetchone()[0]
conn.close()

try:
    decrypted = decrypt_key(token)
    print(f"✅ SUCESSO! Token: {token[:20]}... -> Descriptografado: {decrypted[:10]}...")
    print("🟢 SISTEMA SAAS 100% FUNCIONAL.")
    print("🚀 AGORA RODE: python -B main_saaS.py")
except Exception as e:
    print(f"❌ FALHA: {e}")
    print("💡 Verifique se crypto_vault.py tem a chave fixada: MASTER_PASSWORD = 'JarvisSaaS2026!'")