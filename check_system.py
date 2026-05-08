import requests
import time

print("🔍 Verificando sistema Sexta-Feira Advanced...\n")

# 1. Dashboard
print("1️⃣ Dashboard Render...")
try:
    r = requests.get("https://sexta-feira-wm1s.onrender.com", timeout=10)
    print(f"   ✅ Status: {r.status_code}")
except:
    print("   ❌ Offline")

# 2. GitHub Pages
print("\n2️⃣ Página de Vendas...")
try:
    r = requests.get("https://breendobenz-crypto.github.io/sexta-feira/", timeout=10)
    print(f"   ✅ Status: {r.status_code}")
except:
    print("   ❌ Offline")

# 3. Webhook (teste)
print("\n3️⃣ Webhook...")
try:
    r = requests.post(
        "https://sexta-feira-wm1s.onrender.com/whop/webhook",
        json={"test": True},
        timeout=10
    )
    print(f"   ✅ Status: {r.status_code}")
except:
    print("   ❌ Offline")

print("\n✅ Verificação concluída!")