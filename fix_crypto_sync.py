# fix_crypto_sync.py - REPARO NUCLEAR DE CRIPTOGRAFIA
import os
import sys
from dotenv import load_dotenv

# 1. Força limpeza de cache
load_dotenv(override=True)
for mod in list(sys.modules.keys()):
    if 'crypto' in mod or 'saas_db' in mod:
        del sys.modules[mod]

from crypto_vault import encrypt_key, decrypt_key
from saas_db import init_saas_db, register_user, get_user_credentials

DB_NAME = "jarvis_saas.db"

print("🗑️ Deletando banco corrompido...")
for f in [DB_NAME, f"{DB_NAME}-shm", f"{DB_NAME}-wal"]:
    if os.path.exists(f):
        os.remove(f)

print("🏗️ Recriando banco com chave sincronizada...")
init_saas_db()

print("👤 Cadastrando VIP com chaves reais do .env...")
register_user(
    user_id="vip_test_01",
    name="Admin",
    email="admin@test.com",
    okx_key=os.getenv("OKX_API_KEY"),
    okx_secret=os.getenv("OKX_API_SECRET"),
    okx_pass=os.getenv("OKX_PASSPHRASE")
)

print("🔍 Verificando integridade...")
creds = get_user_credentials("vip_test_01")
if creds and len(creds['api_key']) > 5:
    print(f"✅ SUCESSO! API Key descriptografada: {creds['api_key'][:8]}...")
    print("🟢 SINCRONIA PERFEITA. Agora rode: python -B main_saaS.py")
else:
    print("❌ FALHA. Verifique se SAAS_MASTER_KEY está correta no .env.")