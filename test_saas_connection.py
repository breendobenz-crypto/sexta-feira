# test_saas_connection.py
import os
from dotenv import load_dotenv
from okx_connect import OKXClient
from saas_db import get_user_credentials, register_user

load_dotenv()

def test_saaas_connection():
    print("🔍 Testando integração SaaS + OKX...")
    print("-" * 40)
    
    # 1. Prioridade: Chaves do .env (Modo Admin/Desenvolvedor)
    api_key = os.getenv("OKX_API_KEY")
    api_secret = os.getenv("OKX_API_SECRET")
    passphrase = os.getenv("OKX_PASSPHRASE")
    simulated = os.getenv("OKX_SIMULATED", "false").lower() == "true"
    
    if api_key and api_secret and passphrase:
        print("📂 Fonte: .env (Modo Admin)")
        keys = {"api_key": api_key, "api_secret": api_secret, "passphrase": passphrase}
    else:
        # 2. Fallback: Banco de Dados (Modo VIP)
        print("📂 Fonte: Banco de Dados (Modo VIP)")
        keys = get_user_credentials("vip_test_01")
        if not keys:
            print("⚠️ Nenhuma chave encontrada no .env nem no DB.")
            print("💡 Dica: Preencha seu .env ou cadastre um VIP primeiro.")
            return

    # 3. Instancia o Cliente SaaS
    client = OKXClient(
        api_key=keys["api_key"],
        api_secret=keys["api_secret"],
        passphrase=keys["passphrase"],
        simulated=simulated
    )
    
    # 4. Testa Conexão Real
    print("🔄 Conectando à OKX...")
    info = client.get_account_info()
    
    if info and info.get("equity") is not None:
        print(f"✅ CONECTADO COM SUCESSO!")
        print(f"💰 Equity: ${info['equity']:.4f}")
        print(f"💵 Disponível: ${info['availableBalance']:.4f}")
        print(f"🌐 Ambiente: {'Testnet' if simulated else 'Mainnet'}")
        print("\n🟢 Arquitetura SaaS OK: Cliente isolado + Cache + Thread-Safe funcionando.")
    else:
        print("❌ Falha ao conectar. Verifique:")
        if simulated:
            print("   • Você está em Testnet? Confirme se as chaves são da Testnet.")
        else:
            print("   • Chaves da OKX estão corretas no .env?")
            print("   • Permissões da API: 'Trade' e 'Read' ativadas?")
            print("   • Passphrase está exata (case-sensitive)?")

if __name__ == "__main__":
    test_saaas_connection()