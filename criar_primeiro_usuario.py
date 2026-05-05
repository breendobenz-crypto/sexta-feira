from saas_db import register_user

# Dados do primeiro usuário
EMAIL = "breendobenz@gmail.com"  # ← MUDE AQUI
SENHA = "SextaFeira2026!"    # ← MUDE AQUI  
NOME = "breendobenz"        # ← MUDE AQUI

# Chaves OKX (opcional - pode deixar vazio por enquanto)
OKX_API_KEY = ""
OKX_SECRET = ""
OKX_PASSPHRASE = ""

# Registrar usuário
if register_user(EMAIL, NOME, EMAIL, OKX_API_KEY, OKX_SECRET, OKX_PASSPHRASE):
    print(f"✅ Usuário cadastrado com sucesso!")
    print(f"📧 Email: {EMAIL}")
    print(f"🔑 Senha: {SENHA}")
    print(f"\nAgora você pode fazer login no dashboard!")
else:
    print("❌ Erro ao cadastrar usuário")