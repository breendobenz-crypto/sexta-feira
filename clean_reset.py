# clean_reset.py - RESET LIMPO & TESTE IMEDIATO
import os
import sys
import importlib

# Força recarregamento dos módulos (evita cache .pyc)
if 'crypto_vault' in sys.modules: del sys.modules['crypto_vault']
if 'saas_db' in sys.modules: del sys.modules['saas_db']

from saas_db import init_saas_db, register_user
from crypto_vault import decrypt_key
from dotenv import load_dotenv
load_dotenv()

DB_NAME = "jarvis_saas.db"

print("🗑️ Limpando banco antigo...")
if os.path.exists(DB_NAME):
    os.remove(DB_NAME)
    if os.path.exists(f"{DB_NAME}-shm"): os.remove(f"{DB_NAME}-shm")
    if os.path.exists(f"{DB_NAME}-wal"): os.remove(f"{DB_NAME}-wal")
print("✅ Banco removido.")

print("🏗️ Recriando estrutura SaaS...")
init_saas_db()

print("👤 Cadastrando VIP de teste...")
register_user(
    user_id="vip_test_01",
    name="Breendo Admin",
    email="breendo@test.com",
    okx_key=os.getenv("OKX_API_KEY"),
    okx_secret=os.getenv("OKX_API_SECRET"),
    okx_pass=os.getenv("OKX_PASSPHRASE")
)

print("🔐 Testando descriptografia imediata...")
from saas_db import get_user_credentials
creds = get_user_credentials("vip_test_01")

if creds:
    test_decrypt = decrypt_key(creds["api_key"])
    print(f"✅ SUCESSO! Chave descriptografada: {test_decrypt[:8]}...")
    print("🟢 Sistema SaaS 100% sincronizado. Pode rodar `python main_saaS.py`")
else:
    print("❌ Falha: credenciais não encontradas no DB.")