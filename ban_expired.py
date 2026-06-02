# ban_expired.py
import saas_db
import requests
import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
VIP_GROUP_ID = os.getenv("VIP_GROUP_ID")

def ban_users():
    # Pega lista de quem venceu o trial
    expired_users = saas_db.get_expired_trials()
    
    for user in expired_users:
        uid = user['user_id']
        print(f"🚫 Banindo usuário Trial vencido: {uid}")
        
        # 1. Bane do Telegram
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/kickChatMember"
        # Nota: Kick remove o usuário. Se quiser apenas silenciar, use restrictChatMember
        requests.post(url, json={"chat_id": VIP_GROUP_ID, "user_id": uid})
        
        # 2. Atualiza status no banco para BANNED
        saas_db.update_user_status(uid, "BANNED")

if __name__ == "__main__":
    ban_users()