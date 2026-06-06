import saas_db

email_admin = "breendobenz@gmail.com"
senha_admin = "Garavelo1"

print("=" * 60)
print("🔐 CRIANDO USUÁRIO ADMINISTRADOR - BINGX")
print("=" * 60)

sucesso = saas_db.register_user(
    user_id="admin_master",
    name="Administrador",
    email=email_admin,
    bingx_key='VAZIO', 
    bingx_secret='VAZIO', 
    bingx_passphrase='VAZIO'
)

if sucesso:
    saas_db.set_user_password(email_admin, senha_admin)
    print(f"\n✅ SUCESSO! Admin criado!")
    print(f"📧 Email: {email_admin}")
    print(f"🔑 Senha: {senha_admin}")
    print("\n👉 Agora você pode fazer login no Dashboard!")
else:
    print("\n❌ Erro ao criar usuário.")