# saas_db.py - GESTÃO DE USUÁRIOS SAAS (VERSÃO FINAL COMPLETA)
import sqlite3
import os
from datetime import datetime, timezone
from crypto_vault import encrypt_key, decrypt_key
from cryptography.fernet import InvalidToken

DB_NAME = "jarvis_saas.db"

def init_saas_db():
    """Cria a estrutura completa do banco de dados SaaS."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabela de Usuários VIP
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE,
            email TEXT UNIQUE NOT NULL,
            display_name TEXT,
            plan TEXT DEFAULT 'VIP',
            status TEXT DEFAULT 'ACTIVE',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Tabela de Credenciais OKX (Criptografadas)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_credentials (
            user_id INTEGER PRIMARY KEY,
            api_key_enc TEXT NOT NULL,
            api_secret_enc TEXT NOT NULL,
            passphrase_enc TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Tabela de Trades (com user_id para isolamento)
    cursor.execute('''
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
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Índices para performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_user ON trades(user_id, status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_close ON trades(user_id, close_time)")
    
    conn.commit()
    conn.close()

def register_user(user_id: str, name: str, email: str, okx_key: str, okx_secret: str, okx_pass: str) -> bool:
    """Cadastra um novo VIP com credenciais criptografadas."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        enc_key = encrypt_key(okx_key)
        enc_secret = encrypt_key(okx_secret)
        enc_pass = encrypt_key(okx_pass)
        
        if not enc_key.startswith("gAAAAA"):
            raise ValueError("Falha na criptografia")

        cursor.execute("""
            INSERT OR REPLACE INTO users (user_id, email, display_name, status, joined_at)
            VALUES (?, ?, ?, 'ACTIVE', CURRENT_TIMESTAMP)
        """, (user_id, email, name))
        
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        internal_id = cursor.fetchone()[0]
        
        cursor.execute("""
            INSERT OR REPLACE INTO api_credentials (user_id, api_key_enc, api_secret_enc, passphrase_enc)
            VALUES (?, ?, ?, ?)
        """, (internal_id, enc_key, enc_secret, enc_pass))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ [DB ERROR] Falha ao registrar {email}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_user_by_email(email: str) -> dict | None:
    """Busca usuário pelo email para login do dashboard."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, email, display_name, status FROM users WHERE email = ? AND status = 'ACTIVE'", (email,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row[0],
            "user_id": row[1],
            "email": row[2],
            "display_name": row[3],
            "status": row[4]
        }
    return None

def get_decrypted_credentials(internal_user_id: int) -> dict | None:
    """Retorna credenciais OKX descriptografadas para um usuário interno (dashboard)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT api_key_enc, api_secret_enc, passphrase_enc FROM api_credentials WHERE user_id = ?", (internal_user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        try:
            return {
                "api_key": decrypt_key(row[0]),
                "api_secret": decrypt_key(row[1]),
                "passphrase": decrypt_key(row[2])
            }
        except InvalidToken:
            print(f"❌ [DB] Token inválido para user_id {internal_user_id}")
            return None
    return None

def get_user_credentials(user_id: str) -> dict | None:
    """
    ALIAS PARA COMPATIBILIDADE COM main_saaS.py
    Retorna credenciais OKX descriptografadas pelo user_id externo.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Primeiro pega o internal_id pelo user_id externo
    cursor.execute("SELECT id FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        internal_id = row[0]
        return get_decrypted_credentials(internal_id)
    return None

def update_last_login(internal_user_id: int):
    """Atualiza o timestamp do último login."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (internal_user_id,))
    conn.commit()
    conn.close()

def get_closed_trades(internal_user_id: int, limit: int = 50) -> list[dict]:
    """Retorna trades fechados de um usuário específico."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT symbol, side, entry_price, exit_price, pnl_usdt, pnl_pct, score, close_time
        FROM trades
        WHERE user_id = ? AND status = 'CLOSED'
        ORDER BY close_time DESC LIMIT ?
    """, (internal_user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "symbol": r[0], "side": r[1], "entry_price": r[2],
            "exit_price": r[3], "pnl_usdt": r[4], "pnl_pct": r[5],
            "score": r[6], "close_time": r[7]
        }
        for r in rows
    ]

def get_open_trades(internal_user_id: int) -> list[dict]:
    """Retorna trades abertos de um usuário específico."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT symbol, side, entry_price, size, score, open_time
        FROM trades
        WHERE user_id = ? AND status = 'OPEN'
        ORDER BY open_time DESC
    """, (internal_user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "symbol": r[0], "side": r[1], "entry_price": r[2],
            "size": r[3], "score": r[4], "open_time": r[5]
        }
        for r in rows
    ]

def get_user_stats(internal_user_id: int) -> dict:
    """Retorna estatísticas de performance de um usuário."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            COUNT(*) AS total_trades,
            SUM(CASE WHEN pnl_usdt > 0 THEN 1 ELSE 0 END) AS wins,
            SUM(CASE WHEN pnl_usdt <= 0 THEN 1 ELSE 0 END) AS losses,
            COALESCE(SUM(pnl_usdt), 0) AS total_pnl,
            COALESCE(AVG(pnl_pct), 0) AS avg_pct,
            COALESCE(MIN(pnl_usdt), 0) AS worst_loss,
            COALESCE(MAX(pnl_usdt), 0) AS best_win
        FROM trades
        WHERE user_id = ? AND status = 'CLOSED'
    """, (internal_user_id,))
    row = cursor.fetchone()
    conn.close()
    
    total = row[0] or 0
    wins = row[1] or 0
    
    return {
        "total_trades": total,
        "wins": wins,
        "losses": row[2] or 0,
        "total_pnl": float(row[3] or 0),
        "avg_pct": float(row[4] or 0),
        "worst_loss": float(row[5] or 0),
        "best_win": float(row[6] or 0),
        "win_rate": wins / max(1, total)
    }

def get_equity_curve(internal_user_id: int, days: int = 30) -> list[dict]:
    """Retorna curva de equity diária de um usuário."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            date(close_time) as date,
            SUM(pnl_usdt) as daily_pnl,
            COUNT(*) as trades
        FROM trades
        WHERE user_id = ? AND status = 'CLOSED'
        AND close_time >= datetime('now', ?)
        GROUP BY date(close_time)
        ORDER BY date ASC
    """, (internal_user_id, f"-{days} days"))
    rows = cursor.fetchall()
    conn.close()
    
    equity = 0
    result = []
    for row in rows:
        equity += float(row[1] or 0)
        result.append({
            "date": row[0],
            "equity": round(equity, 2),
            "daily_pnl": round(float(row[1] or 0), 2),
            "trades": row[2]
        })
    return result

def get_active_users() -> list[str]:
    """Lista todos os user_id ativos (para o orquestrador main_saaS.py)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE status = 'ACTIVE'")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

def update_user_status(user_id: str, status: str):
    """Ativa ou cancela um usuário pelo user_id externo."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("UPDATE users SET status = ? WHERE user_id = ?", (status, user_id))
    conn.commit()
    conn.close()

# Inicializa ao importar
init_saas_db()