import requests

TOKEN = "8352588624:AAHZmC-fyLYK4F8taL6NpDrncmB9JbmS8Lo"
URL = f"https://api.telegram.org/bot{TOKEN}/getMe"

resp = requests.get(URL, timeout=5)
if resp.status_code == 200 and resp.json().get("ok"):
    print("✅ Bot Telegram ONLINE e respondendo")
else:
    print("❌ Bot OFFLINE ou Token inválido")