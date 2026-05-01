# reset_saas_test.py
import os
import sqlite3
from dotenv import load_dotenv
from saas_db import init_saas_db, register_user

load_dotenv()

DB_NAME = "jarvis_saas.db"

# 1. Remove banco antigo (limpa tokens inválidos)
if os.path.exists(DB_NAME):
    os.remove(DB_NAME)
    print("🗑️ Banco antigo removido.")

# 2. Recria estrutura limpa
init_saas_db()
print("✅ Novo banco criado.")

# 3. Cadastra VIP usando SUAS chaves reais do .env (para teste imediato)
register_user(
    user_id="vip_test_01",
    name="Breendo Admin",
    email="breendo@test.com",
    okx_key=os.getenv("OKX_API_KEY"),
    okx_secret=os.getenv("OKX_API_SECRET"),
    okx_pass=os.getenv("OKX_PASSPHRASE")
)
print("🟢 VIP 'vip_test_01' registrado com criptografia sincronizada!")