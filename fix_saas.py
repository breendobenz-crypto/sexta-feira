# fix_saas.py - REPARO E VERIFICAÇÃO VISUAL
import os
import sys
from dotenv import load_dotenv

# 1. Carregar .env PRIMEIRO
load_dotenv()

# 2. Importar módulos
from saas_db import init_saas_db, register_user, get_user_credentials
from crypto_vault import decrypt_key

DB_NAME = "jarvis_saas.db"

print("🛑 PARANDO E LIMPANDO...")
# Tenta deletar todos os arquivos de DB
for f in [DB_NAME, f"{DB_NAME}-shm", f"{DB_NAME}-wal"]:
    if os.path.exists(f):
        try:
            os.remove(f)
            print(f"🗑️ Removido: {f}")
        except PermissionError:
            print(f"⚠️ Erro ao remover {f}. Feche outros terminais/programas e tente novamente.")
            sys.exit(1)

print("🏗️ Recriando estrutura...")
init_saas_db()

print("👤 Cadastrando VIP de teste...")
# Registra com suas chaves reais
register_user(
    user_id="vip_test_01",
    name="Breendo Admin",
    email="breendo@test.com",
    okx_key=os.getenv("OKX_API_KEY"),
    okx_secret=os.getenv("OKX_API_SECRET"),
    okx_pass=os.getenv("OKX_PASSPHRASE")
)

print("🔍 Verificando integridade dos dados...")
creds = get_user_credentials("vip_test_01")

if creds:
    # Pega o token bruto do banco para inspeção
    conn = sqlite3.connect(DB_NAME)
    token = conn.execute("SELECT api_key_enc FROM api_credentials WHERE user_id=?", ("vip_test_01",)).fetchone()[0]
    conn.close()
    
    print(f"✅ SUCESSO! VIP cadastrado.")
    print(f"🔒 Token no banco: {token[:20]}... (Deve começar com gAAAAA)")
    print(f"🔑 Chave descriptografada: {creds['api_key'][:10]}...")
    print("🟢 SISTEMA PRONTO! Pode rodar `python main_saaS.py`")
else:
    print("❌ Falha: credenciais não encontradas.")