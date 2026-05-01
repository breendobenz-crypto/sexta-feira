# reset_db_nuclear.py
import os
import sqlite3

DB_NAME = "jarvis_saas.db"

print("💣 DELETANDO BANCO ANTIGO...")
for f in [DB_NAME, f"{DB_NAME}-shm", f"{DB_NAME}-wal"]:
    if os.path.exists(f):
        os.remove(f)
        print(f"🗑️ Removido: {f}")

print("✅ Banco antigo removido. O saas_db.py criará a estrutura correta ao ser importado.")
print("🚀 Agora execute: python -B main_saaS.py")