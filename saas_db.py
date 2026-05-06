# saas_db.py - HÍBRIDO: PostgreSQL (Render) + SQLite (Local)
import os
import hashlib
import sqlite3
from datetime import datetime, timezone
from crypto_vault import encrypt_key, decrypt_key
from cryptography.fernet import InvalidToken

# ==========================================
# DETECÇÃO AUTOMÁTICA DO BANCO
# ==========================================
DATABASE_URL = os.getenv("DATABASE_URL")
USE_POSTGRES = bool(DATABASE_URL)

if USE_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor

SALT = "sexta-feira-advanced-vip-salt-2026"
DB_NAME = "jarvis_saas.db"  # Para SQLite local

def hash_password(password: str) -> str:
    return hashlib.sha256((password + SALT).encode()).hexdigest()

def get_db_connection():
    """Retorna conexão com PostgreSQL ou SQLite, conforme disponível."""
    if USE_POSTGRES:
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    else:
        return sqlite3.connect(DB_NAME)

def init_saas_db():
    """Cria as tabelas no banco configurado."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if USE_POSTGRES:
            # PostgreSQL
            cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY, user_id TEXT UNIQUE, email TEXT UNIQUE NOT NULL,
                display_name TEXT, plan TEXT DEFAULT 'VIP', status TEXT DEFAULT 'ACTIVE',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, last_login TIMESTAMP, password_hash TEXT
            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS api_credentials (
                user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                api_key_enc TEXT NOT NULL, api_secret_enc TEXT NOT NULL,
                passphrase_enc TEXT NOT NULL, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS trades (
                id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                symbol TEXT NOT NULL, side TEXT NOT NULL, entry_price REAL NOT NULL,
                exit_price REAL, size REAL NOT NULL, pnl_usdt REAL, pnl_pct REAL,
                score INTEGER DEFAULT 70, status TEXT DEFAULT 'OPEN',
                open_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, close_time TIMESTAMP, ai_reasoning TEXT
            )''')
        else:
            # SQLite local
            cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT UNIQUE, email TEXT UNIQUE NOT NULL,
                display_name TEXT, plan TEXT DEFAULT 'VIP', status TEXT DEFAULT 'ACTIVE',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, last_login TIMESTAMP, password_hash TEXT
            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS api_credentials (
                user_id INTEGER PRIMARY KEY, api_key_enc TEXT NOT NULL, api_secret_enc TEXT NOT NULL,
                passphrase_enc TEXT NOT NULL, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
                symbol TEXT NOT NULL, side TEXT NOT NULL, entry_price REAL NOT NULL,
                exit_price REAL, size REAL NOT NULL, pnl_usdt REAL, pnl_pct REAL,
                score INTEGER DEFAULT 70, status TEXT DEFAULT 'OPEN',
                open_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, close_time TIMESTAMP, ai_reasoning TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )''')
            # Adiciona colunas se não existirem (SQLite)
            try: cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
            except: pass
            try: cursor.execute("ALTER TABLE trades ADD COLUMN ai_reasoning TEXT")
            except: pass
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def _dictify(row, cursor=None):
    """Converte linha do banco para dicionário."""
    if row is None: return None
    if USE_POSTGRES:
        return dict(row) if hasattr(row, 'keys') else row
    else:
        if cursor and hasattr(cursor, 'description'):
            return {desc[0]: row[i] for i, desc in enumerate(cursor.description)}
        return row

# ========== FUNÇÕES PRINCIPAIS ==========

def register_user(user_id: str, name: str, email: str, okx_key: str, okx_secret: str, okx_pass: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        enc_key, enc_secret, enc_pass = encrypt_key(okx_key), encrypt_key(okx_secret), encrypt_key(okx_pass)
        if not enc_key.startswith("gAAAAA"): raise ValueError("Falha na criptografia")
        
        if USE_POSTGRES:
            cursor.execute("""
                INSERT INTO users (user_id, email, display_name, status) VALUES (%s, %s, %s, 'ACTIVE')
                ON CONFLICT (user_id) DO UPDATE SET email=EXCLUDED.email, display_name=EXCLUDED.display_name, status='ACTIVE'
                RETURNING id
            """, (user_id, email, name))
            internal_id = cursor.fetchone()['id']
            cursor.execute("""
                INSERT INTO api_credentials (user_id, api_key_enc, api_secret_enc, passphrase_enc)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET api_key_enc=EXCLUDED.api_key_enc,
                api_secret_enc=EXCLUDED.api_secret_enc, passphrase_enc=EXCLUDED.passphrase_enc, updated_at=CURRENT_TIMESTAMP
            """, (internal_id, enc_key, enc_secret, enc_pass))
        else:
            cursor.execute("INSERT OR REPLACE INTO users (user_id, email, display_name, status) VALUES (?, ?, ?, 'ACTIVE')", (user_id, email, name))
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            internal_id = cursor.fetchone()[0]
            cursor.execute("INSERT OR REPLACE INTO api_credentials (user_id, api_key_enc, api_secret_enc, passphrase_enc) VALUES (?, ?, ?, ?)", (internal_id, enc_key, enc_secret, enc_pass))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ [DB ERROR] {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def get_user_by_email(email: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if USE_POSTGRES:
            cursor.execute("SELECT id, user_id, email, display_name, status FROM users WHERE email = %s AND status = 'ACTIVE'", (email,))
        else:
            cursor.execute("SELECT id, user_id, email, display_name, status FROM users WHERE email = ? AND status = 'ACTIVE'", (email,))
        row = cursor.fetchone()
        return _dictify(row, cursor) if row else None
    finally:
        cursor.close()
        conn.close()

def get_user_full(email: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if USE_POSTGRES:
            cursor.execute("SELECT id, user_id, email, display_name, status, password_hash FROM users WHERE email = %s", (email,))
        else:
            cursor.execute("SELECT id, user_id, email, display_name, status, password_hash FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        return _dictify(row, cursor) if row else None
    finally:
        cursor.close()
        conn.close()

def set_user_password(email: str, password: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        pwd_hash = hash_password(password)
        if USE_POSTGRES:
            cursor.execute("UPDATE users SET password_hash = %s WHERE email = %s", (pwd_hash, email))
        else:
            cursor.execute("UPDATE users SET password_hash = ? WHERE email = ?", (pwd_hash, email))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def verify_password(email: str, password: str) -> bool:
    user = get_user_full(email)
    if not user: return False
    stored_hash = user.get('password_hash')
    if not stored_hash: return False
    return stored_hash == hash_password(password)

def update_user_credentials(user_id: int, api_key: str, api_secret: str, passphrase: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        enc_key, enc_secret, enc_pass = encrypt_key(api_key), encrypt_key(api_secret), encrypt_key(passphrase)
        if not enc_key.startswith("gAAAAA"): raise ValueError("Falha na criptografia")
        if USE_POSTGRES:
            cursor.execute("""
                INSERT INTO api_credentials (user_id, api_key_enc, api_secret_enc, passphrase_enc, updated_at)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE SET api_key_enc=EXCLUDED.api_key_enc,
                api_secret_enc=EXCLUDED.api_secret_enc, passphrase_enc=EXCLUDED.passphrase_enc, updated_at=CURRENT_TIMESTAMP
            """, (user_id, enc_key, enc_secret, enc_pass))
        else:
            cursor.execute("""
                INSERT OR REPLACE INTO api_credentials (user_id, api_key_enc, api_secret_enc, passphrase_enc, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, enc_key, enc_secret, enc_pass))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Erro ao atualizar credenciais: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def get_decrypted_credentials(internal_user_id: int):
    """Busca credenciais. Se falhar (token inválido), retorna None sem crashar."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if USE_POSTGRES:
            cursor.execute("SELECT api_key_enc, api_secret_enc, passphrase_enc FROM api_credentials WHERE user_id = %s", (internal_user_id,))
        else:
            cursor.execute("SELECT api_key_enc, api_secret_enc, passphrase_enc FROM api_credentials WHERE user_id = ?", (internal_user_id,))
        row = cursor.fetchone()
        if row:
            d = _dictify(row, cursor)
            # Verifica se há dados válidos
            raw_key = d.get('api_key_enc', '')
            if not raw_key or raw_key in ('VAZIO', 'N/A', 'NONE'):
                return None
            
            try:
                return {
                    "api_key": decrypt_key(d['api_key_enc']),
                    "api_secret": decrypt_key(d['api_secret_enc']),
                    "passphrase": decrypt_key(d['passphrase_enc'])
                }
            except Exception:
                # ⚠️ Token inválido ou erro de criptografia
                return None
        return None
    finally:
        cursor.close()
        conn.close()

def get_user_credentials(user_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if USE_POSTGRES:
            cursor.execute("SELECT id FROM users WHERE user_id = %s", (user_id,))
        else:
            cursor.execute("SELECT id FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            d = _dictify(row, cursor)
            return get_decrypted_credentials(d['id'])
        return None
    finally:
        cursor.close()
        conn.close()

def update_last_login(internal_user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if USE_POSTGRES:
            cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s", (internal_user_id,))
        else:
            cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (internal_user_id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if USE_POSTGRES:
            cursor.execute("SELECT id, user_id, email, display_name, plan, status, joined_at FROM users ORDER BY joined_at DESC")
        else:
            cursor.execute("SELECT id, user_id, email, display_name, plan, status, joined_at FROM users ORDER BY joined_at DESC")
        rows = cursor.fetchall()
        return [_dictify(r, cursor) for r in rows]
    finally:
        cursor.close()
        conn.close()

def update_user_status(user_id: str, status: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if USE_POSTGRES:
            cursor.execute("UPDATE users SET status = %s WHERE user_id = %s", (status, user_id))
        else:
            cursor.execute("UPDATE users SET status = ? WHERE user_id = ?", (status, user_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def save_trade(user_id: int, symbol: str, side: str, entry: float, qty: float, score: int, reasoning: str = ""):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if USE_POSTGRES:
            cursor.execute("""
                INSERT INTO trades (user_id, symbol, side, entry_price, size, score, ai_reasoning, open_time, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, 'OPEN')
            """, (user_id, symbol, side, entry, qty, score, reasoning))
        else:
            cursor.execute("""
                INSERT INTO trades (user_id, symbol, side, entry_price, size, score, ai_reasoning, open_time, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 'OPEN')
            """, (user_id, symbol, side, entry, qty, score, reasoning))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def update_trade_exit(user_id: int, symbol: str, close_time: str, exit_price: float, pnl_usdt: float, pnl_pct: float):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if USE_POSTGRES:
            cursor.execute("""
                UPDATE trades SET exit_price = %s, pnl_usdt = %s, pnl_pct = %s, status = 'CLOSED', close_time = %s
                WHERE user_id = %s AND symbol = %s AND status = 'OPEN'
            """, (exit_price, pnl_usdt, pnl_pct, close_time, user_id, symbol))
        else:
            cursor.execute("""
                UPDATE trades SET exit_price = ?, pnl_usdt = ?, pnl_pct = ?, status = 'CLOSED', close_time = ?
                WHERE user_id = ? AND symbol = ? AND status = 'OPEN'
            """, (exit_price, pnl_usdt, pnl_pct, close_time, user_id, symbol))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def get_closed_trades(internal_user_id: int, limit: int = 50):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if USE_POSTGRES:
            cursor.execute("""
                SELECT symbol, side, entry_price, exit_price, pnl_usdt, pnl_pct, score, close_time, ai_reasoning
                FROM trades WHERE user_id = %s AND status = 'CLOSED' ORDER BY close_time DESC LIMIT %s
            """, (internal_user_id, limit))
        else:
            cursor.execute("""
                SELECT symbol, side, entry_price, exit_price, pnl_usdt, pnl_pct, score, close_time, ai_reasoning
                FROM trades WHERE user_id = ? AND status = 'CLOSED' ORDER BY close_time DESC LIMIT ?
            """, (internal_user_id, limit))
        rows = cursor.fetchall()
        return [_dictify(r, cursor) for r in rows]
    finally:
        cursor.close()
        conn.close()

def get_open_trades(internal_user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if USE_POSTGRES:
            cursor.execute("SELECT symbol, side, entry_price, size, score, open_time FROM trades WHERE user_id = %s AND status = 'OPEN' ORDER BY open_time DESC", (internal_user_id,))
        else:
            cursor.execute("SELECT symbol, side, entry_price, size, score, open_time FROM trades WHERE user_id = ? AND status = 'OPEN' ORDER BY open_time DESC", (internal_user_id,))
        rows = cursor.fetchall()
        return [_dictify(r, cursor) for r in rows]
    finally:
        cursor.close()
        conn.close()

def get_user_stats(internal_user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if USE_POSTGRES:
            cursor.execute("""
                SELECT COUNT(*) as total_trades, SUM(CASE WHEN pnl_usdt > 0 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN pnl_usdt <= 0 THEN 1 ELSE 0 END) as losses, COALESCE(SUM(pnl_usdt), 0) as total_pnl,
                COALESCE(AVG(pnl_pct), 0) as avg_pct, COALESCE(MIN(pnl_usdt), 0) as worst_loss,
                COALESCE(MAX(pnl_usdt), 0) as best_win FROM trades WHERE user_id = %s AND status = 'CLOSED'
            """, (internal_user_id,))
        else:
            cursor.execute("""
                SELECT COUNT(*), SUM(CASE WHEN pnl_usdt > 0 THEN 1 ELSE 0 END),
                SUM(CASE WHEN pnl_usdt <= 0 THEN 1 ELSE 0 END), COALESCE(SUM(pnl_usdt), 0),
                COALESCE(AVG(pnl_pct), 0), COALESCE(MIN(pnl_usdt), 0), COALESCE(MAX(pnl_usdt), 0)
                FROM trades WHERE user_id = ? AND status = 'CLOSED'
            """, (internal_user_id,))
        row = cursor.fetchone()
        if not row:
            return {"total_trades": 0, "wins": 0, "losses": 0, "total_pnl": 0.0, "avg_pct": 0.0, "worst_loss": 0.0, "best_win": 0.0, "win_rate": 0.0}
        d = _dictify(row, cursor) if USE_POSTGRES else {"total_trades": row[0], "wins": row[1], "losses": row[2], "total_pnl": row[3], "avg_pct": row[4], "worst_loss": row[5], "best_win": row[6]}
        total = d['total_trades'] or 0
        wins = d['wins'] or 0
        return {"total_trades": total, "wins": wins, "losses": d['losses'] or 0, "total_pnl": float(d['total_pnl'] or 0), "avg_pct": float(d['avg_pct'] or 0), "worst_loss": float(d['worst_loss'] or 0), "best_win": float(d['best_win'] or 0), "win_rate": wins / max(1, total)}
    finally:
        cursor.close()
        conn.close()

def get_equity_curve(internal_user_id: int, days: int = 30):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if USE_POSTGRES:
            cursor.execute("""
                SELECT DATE(close_time) as date, SUM(pnl_usdt) as daily_pnl, COUNT(*) as trades
                FROM trades WHERE user_id = %s AND status = 'CLOSED' AND close_time >= NOW() - (INTERVAL '1 day' * %s)
                GROUP BY DATE(close_time) ORDER BY date ASC
            """, (internal_user_id, days))
        else:
            cursor.execute("""
                SELECT date(close_time) as date, SUM(pnl_usdt) as daily_pnl, COUNT(*) as trades
                FROM trades WHERE user_id = ? AND status = 'CLOSED' AND close_time >= datetime('now', ?)
                GROUP BY date(close_time) ORDER BY date ASC
            """, (internal_user_id, f"-{days} days"))
        rows = cursor.fetchall()
        equity = 0
        result = []
        for row in rows:
            d = _dictify(row, cursor) if USE_POSTGRES else {"date": row[0], "daily_pnl": row[1], "trades": row[2]}
            equity += float(d['daily_pnl'] or 0)
            result.append({"date": str(d['date']), "equity": round(equity, 2), "daily_pnl": round(float(d['daily_pnl'] or 0), 2), "trades": d['trades']})
        return result
    finally:
        cursor.close()
        conn.close()

def get_active_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if USE_POSTGRES:
            cursor.execute("SELECT user_id FROM users WHERE status = 'ACTIVE'")
        else:
            cursor.execute("SELECT user_id FROM users WHERE status = 'ACTIVE'")
        rows = cursor.fetchall()
        return [(_dictify(r, cursor) if USE_POSTGRES else r)[0] for r in rows]
    finally:
        cursor.close()
        conn.close()

        # --- INÍCIO: CÓDIGO PARA CRIAR ADMIN AUTOMÁTICO ---
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            print("⚠️ Banco vazio! Criando Admin padrão...")
            pwd_hash = hash_password("123456")
            cursor.execute(
                "INSERT INTO users (user_id, email, display_name, status, password_hash) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                ("admin@sextafeira.com", "admin@sextafeira.com", "Admin", "ACTIVE", pwd_hash)
            )
            # Se for Postgres
            if USE_POSTGRES:
                uid = cursor.fetchone()['id']
            else:
                uid = cursor.fetchone()[0]
            
            cursor.execute(
                "INSERT INTO api_credentials (user_id, api_key_enc, api_secret_enc, passphrase_enc) VALUES (%s, %s, %s, %s)",
                (uid, 'VAZIO', 'VAZIO', 'VAZIO')
            )
            print("✅ Admin criado com sucesso (Email: admin@sextafeira.com / Senha: 123456)")
        # --- FIM: CÓDIGO PARA CRIAR ADMIN AUTOMÁTICO ---

# Inicializa o banco ao importar
init_saas_db()