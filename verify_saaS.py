# verify_saaS.py - VERIFICAÇÃO CRUZADA
import os
import sys

# Garante que estamos na pasta certa
os.chdir(os.path.dirname(os.path.abspath(__file__)))
print(f"📂 Pasta de trabalho: {os.getcwd()}")

# Força reload do dotenv
import importlib
if 'dotenv' in sys.modules: del sys.modules['dotenv']
if 'crypto_vault' in sys.modules: del sys.modules['crypto_vault']

from dotenv import load_dotenv
load_dotenv()

print(f"🔑 SAAS_MASTER_KEY detectada: {os.getenv('SAAS_MASTER_KEY', 'NÃO ENCONTRADA')[:15]}...")

try:
    from saas_db import get_user_credentials
    from crypto_vault import decrypt_key, fernet
    from cryptography.fernet import InvalidToken

    creds = get_user_credentials("vip_test_01")
    
    if creds:
        print("✅ Credenciais encontradas no DB.")
        # Tenta descriptografar manualmente
        raw_token = creds["api_key"]
        print(f"🔒 Token bruto: {raw_token[:30]}...")
        
        # Tenta descriptografar
        try:
            clear_key = decrypt_key(raw_token)
            print(f"🔑 Chave descriptografada com sucesso: {clear_key[:10]}...")
            print("🟢 SISTEMA SAAS VERIFICADO COM SUCESSO!")
        except InvalidToken:
            print("❌ InvalidToken: A chave mestra atual não bate com a usada para criptografar.")
            print("💡 Dica: Verifique se o .env tem SAAS_MASTER_KEY=JarvisSaaS2026!")
    else:
        print("⚠️ VIP 'vip_test_01' não encontrado. Rode setup_saas_final.py primeiro.")

except Exception as e:
    print(f"💥 Erro fatal: {e}")
    import traceback
    traceback.print_exc()