# webhook.py
from fastapi import FastAPI, Request
import sqlite3

app = FastAPI()

@app.post("/whop/webhook")
async def whop_webhook(req: Request):
    data = await req.json()
    action = data.get("event")  # "subscription.created" ou "subscription.cancelled"
    user_email = data["customer"]["email"]
    user_id = data["customer"]["id"]
    
    conn = sqlite3.connect("jarvis_saas.db")
    if action == "subscription.created":
        conn.execute("INSERT OR REPLACE INTO users (user_id, email, plan, status) VALUES (?, ?, 'vip', 'active')",
                     (user_id, user_email))
    elif action == "subscription.cancelled":
        conn.execute("UPDATE users SET status = 'cancelled' WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return {"status": "ok"}