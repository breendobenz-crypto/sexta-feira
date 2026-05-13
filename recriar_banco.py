# recriar_banco.py - Recria o banco SQLite do zero
import sqlite3
import os
import hashlib

DB_PATH = "jarvis_saas.db"
SALT = "sexta-feira-advanced-vip-salt-2026"

def hash_password(password: str) -> str:
    return hashlib.sha256((password + SALT).encode()).hexdigest()

def criar_banco():
    # Remove banco antigo se existir
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"🗑️ Banco antigo removido: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Tabela users
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE,
            email TEXT UNIQUE NOT NULL,
            display_name TEXT,
            plan TEXT DEFAULT 'VIP',
            status TEXT DEFAULT 'ACTIVE',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            password_hash TEXT
        )
    ''')
    
    # Tabela api_credentials
    cur.execute('''
        CREATE TABLE IF NOT EXISTS api_credentials (
            user_id INTEGER PRIMARY KEY,
            api_key_enc TEXT NOT NULL,
            api_secret_enc TEXT NOT NULL,
            passphrase_enc TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Tabela trades
    cur.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            entry_price REAL NOT NULL,
            exit_price REAL,
            size REAL NOT NULL,
            pnl_usdt REAL,
            pnl_pct REAL,
            score INTEGER DEFAULT 70,
            status TEXT DEFAULT 'OPEN',
            open_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            close_time TIMESTAMP,
            ai_reasoning TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Cria usuário admin padrão
    admin_hash = hash_password("123456")
    cur.execute('''
        INSERT INTO users (email, display_name, plan, status, password_hash)
        VALUES (?, ?, ?, ?, ?)
    ''', ("admin@sextafeira.com", "Admin", "VIP", "ACTIVE", admin_hash))
    
    # Cria seu usuário breendobenz
    breendo_hash = hash_password("123456")
    cur.execute('''
        INSERT INTO users (email, display_name, plan, status, password_hash)
        VALUES (?, ?, ?, ?, ?)
    ''', ("breendobenz@gmail.com", "Breendo", "VIP", "active", breendo_hash))
    
    conn.commit()
    
    # Lista usuários criados
    cur.execute("SELECT id, email, display_name, status FROM users")
    print("\n✅ Usuários criados:")
    for row in cur.fetchall():
        print(f"  🆔 {row[0]} | {row[1]} | {row[2]} | {row[3]}")
    
    cur.close()
    conn.close()
    print(f"\n🎉 Banco criado com sucesso: {DB_PATH}")

if __name__ == "__main__":
    criar_banco()