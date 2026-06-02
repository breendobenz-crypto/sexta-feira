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

SALT = os.getenv("SALT", "sexta-feira-advanced-vip-salt-2026")
DB_NAME = "jarvis_saas.db"


def hash_password(password: str) -> str:
    return hashlib.sha256((password + SALT).encode()).hexdigest()


def get_db_connection():
    if USE_POSTGRES:
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return sqlite3.connect(DB_NAME)


def init_saas_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if USE_POSTGRES:
            cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                user_id TEXT UNIQUE,
                email TEXT UNIQUE NOT NULL,
                display_name TEXT,
                plan TEXT DEFAULT 'FREE',
                status TEXT DEFAULT 'ACTIVE',
                trial_end_date TIMESTAMP,
                telegram_chat_id TEXT,
                stripe_session_id TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                password_hash TEXT
            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS api_credentials (
                user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                api_key_enc TEXT NOT NULL,
                api_secret_enc TEXT NOT NULL,
                passphrase_enc TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS trades (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
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
                ai_reasoning TEXT
            )''')
        else:
            cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE,
                email TEXT UNIQUE NOT NULL,
                display_name TEXT,
                plan TEXT DEFAULT 'FREE',
                status TEXT DEFAULT 'ACTIVE',
                trial_end_date TIMESTAMP,
                telegram_chat_id TEXT,
                stripe_session_id TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                password_hash TEXT
            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS api_credentials (
                user_id INTEGER PRIMARY KEY,
                api_key_enc TEXT NOT NULL,
                api_secret_enc TEXT NOT NULL,
                passphrase_enc TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS trades (
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
            )''')
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def _dictify(row, cursor=None):
    if row is None:
        return None
    if USE_POSTGRES:
        return dict(row) if hasattr(row, 'keys') else row
    if cursor and hasattr(cursor, 'description'):
        return {desc[0]: row[i] for i, desc in enumerate(cursor.description)}
    return row


# ==========================================
# FUNÇÕES PRINCIPAIS
# ==========================================

def register_user_free(user_id: str, name: str, email: str, telegram_chat_id: str = None, stripe_session_id: str = None) -> bool:
    """Registra usuário com acesso FREE imediato"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if USE_POSTGRES:
            cursor.execute("""
                INSERT INTO users (user_id, email, display_name, plan, status, telegram_chat_id, stripe_session_id)
                VALUES (%s, %s, %s, 'FREE', 'ACTIVE', %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET 
                    email=EXCLUDED.email, 
                    telegram_chat_id=EXCLUDED.telegram_chat_id, 
                    stripe_session_id=EXCLUDED.stripe_session_id
                RETURNING id
            """, (user_id, email, name, telegram_chat_id, stripe_session_id))
        else:
            cursor.execute(
                "INSERT OR REPLACE INTO users (user_id, email, display_name, plan, status, telegram_chat_id, stripe_session_id) VALUES (?, ?, ?, 'FREE', 'ACTIVE', ?, ?)",
                (user_id, email, name, telegram_chat_id, stripe_session_id)
            )
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ [DB ERROR] {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def start_vip_trial(user_id: str, email: str, telegram_chat_id: str = None, trial_days: int = 7) -> bool:
    """Ativa trial VIP para usuário existente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        from datetime import timedelta
        trial_end = datetime.now(timezone.utc) + timedelta(days=trial_days)
        
        if USE_POSTGRES:
            cursor.execute("""
                UPDATE users SET plan = 'TRIAL', trial_end_date = %s, status = 'ACTIVE', telegram_chat_id = COALESCE(%s, telegram_chat_id)
                WHERE user_id = %s OR email = %s
            """, (trial_end, telegram_chat_id, user_id, email))
        else:
            cursor.execute(
                "UPDATE users SET plan = 'TRIAL', trial_end_date = ?, status = 'ACTIVE' WHERE user_id = ? OR email = ?",
                (trial_end, user_id, email)
            )
            if telegram_chat_id:
                cursor.execute("UPDATE users SET telegram_chat_id = ? WHERE user_id = ?", (telegram_chat_id, user_id))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ [DB ERROR] {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def upgrade_to_lifetime(user_id: str) -> bool:
    """Atualiza usuário para plano Vitalício"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if USE_POSTGRES:
            cursor.execute("UPDATE users SET plan = 'LIFETIME', trial_end_date = NULL WHERE user_id = %s", (user_id,))
        else:
            cursor.execute("UPDATE users SET plan = 'LIFETIME', trial_end_date = NULL WHERE user_id = ?", (user_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ [DB ERROR] {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def get_expired_trials():
    """Busca usuários com trial expirado que ainda não pagaram"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        now = datetime.now(timezone.utc)
        if USE_POSTGRES:
            cursor.execute(
                "SELECT user_id, email, telegram_chat_id FROM users WHERE plan = 'TRIAL' AND trial_end_date < %s AND status = 'ACTIVE'",
                (now,)
            )
        else:
            cursor.execute(
                "SELECT user_id, email, telegram_chat_id FROM users WHERE plan = 'TRIAL' AND trial_end_date < ? AND status = 'ACTIVE'",
                (now,)
            )
        rows = cursor.fetchall()
        return [_dictify(r, cursor) for r in rows]
    finally:
        cursor.close()
        conn.close()


def get_user_by_email(email: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if USE_POSTGRES:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        else:
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        return _dictify(row, cursor) if row else None
    finally:
        cursor.close()
        conn.close()


def get_user_by_telegram_id(telegram_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if USE_POSTGRES:
            cursor.execute("SELECT * FROM users WHERE telegram_chat_id = %s", (telegram_id,))
        else:
            cursor.execute("SELECT * FROM users WHERE telegram_chat_id = ?", (telegram_id,))
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


# Inicializa ao importar
init_saas_db()