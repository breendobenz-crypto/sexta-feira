# setup_saas_final.py - RESET NUCLEAR & VERIFICAÇÃO VISUAL
import os
import sys
import sqlite3
from dotenv import load_dotenv

# 1. Força recarregamento limpo do ambiente
load_dotenv(override=True)

# 2. Importa módulos SaaS (recarrega para evitar cache .pyc)
if 'crypto_vault' in sys.modules: del sys.modules['crypto_vault']
if 'saas_db' in sys.modules: del sys.modules['saas_db']

from crypto_vault import encrypt_key, decrypt_key
from saas_db import init_saas_db, register_user, get_user_credentials

DB_NAME = "jarvis_saas.db"

print("🛑 PARANDO E LIMPANDO...")
# Tenta deletar todos os arquivos de DB
for f in [DB_NAME, f"{DB_NAME}-shm", f"{DB_NAME}-wal"]:
    if os.path.exists(f):
        try:
            os.remove(f)
            print(f"🗑️ Removido: {f}")
        except PermissionError:
            print(f"⚠️ Erro ao remover {f}. Feche outros terminais/VSCode e tente novamente.")
            sys.exit(1)

print("🏗️ Recriando estrutura...")
init_saas_db()

print("👤 Cadastrando VIP de teste...")
# Registra com suas chaves reais do .env
register_user(
    user_id="vip_test_01",
    name="Breendo Admin",
    email="breendo@test.com",
    okx_key=os.getenv("OKX_API_KEY"),
    okx_secret=os.getenv("OKX_API_SECRET"),
    okx_pass=os.getenv("OKX_PASSPHRASE")
)

print("🔍 Verificando integridade dos dados...")
# Pega o token bruto do banco para inspeção visual
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()
cursor.execute("SELECT api_key_enc FROM api_credentials WHERE user_id = ?", ("vip_test_01",))
row = cursor.fetchone()
conn.close()

if row:
    raw_token = row[0]
    print(f"🔒 Token salvo no banco: {raw_token[:20]}...")
    
    # Verifica se é um token Fernet válido (começa com gAAAAA)
    if raw_token.startswith("gAAAAA"):
        print("✅ Formato de criptografia válido detectado.")
    else:
        print("⚠️ Formato inválido! O banco pode estar salvando texto puro.")
        print("💡 Dica: Verifique se saas_db.py tem 'from crypto_vault import encrypt_key'")

    # Testa descriptografia real
    try:
        creds = get_user_credentials("vip_test_01")
        print(f"🔑 Chave descriptografada com sucesso: {creds['api_key'][:10]}...")
        print("🟢 SISTEMA SAAS 100% SINCRONIZADO! Pode rodar `python main_saaS.py`")
    except Exception as e:
        print(f"❌ Falha ao descriptografar: {e}")
else:
    print("❌ Erro: Nenhuma credencial encontrada no banco.")