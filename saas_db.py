import os
import hashlib
import sqlite3
from datetime import datetime, timezone
from crypto_vault import encrypt_key, decrypt_key
from cryptography.fernet import InvalidToken

DATABASE_URL = os.getenv("DATABASE_URL")
USE_POSTGRES = bool(DATABASE_URL)

if USE_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor

SALT = "sexta-feira-advanced-vip-salt-2026"
DB_NAME = "jarvis_saas.db"


def hash_password(password: str) -> str:
    return hashlib.sha256((password + SALT).encode()).hexdigest()


def get_db_connection():
    if USE_POSTGRES:
        url = DATABASE_URL
        # Render interno NÃO precisa de SSL — Supabase SIM
        # Detecta pelo hostname: interno do Render tem "dpg-" no host
        is_render_internal = "dpg-" in url or ".render.com" in url.split("@")[-1].split("/")[0]

        if is_render_internal:
            # Render interno: sem SSL, conexão direta
            try:
                conn = psycopg2.connect(url, cursor_factory=RealDictCursor, connect_timeout=15)
                return conn
            except Exception as e:
                print(f"❌ Render internal DB error: {e}")
                raise
        else:
            # Externo (Supabase, etc): precisa de SSL
            if "sslmode" not in url:
                sep = "&" if "?" in url else "?"
                url = f"{url}{sep}sslmode=require"
            try:
                conn = psycopg2.connect(url, cursor_factory=RealDictCursor, connect_timeout=15)
                return conn
            except Exception as e:
                print(f"❌ External DB error: {e}")
                raise
    return sqlite3.connect(DB_NAME)


def init_saas_db():
    try:
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
                cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS plan TEXT DEFAULT 'FREE'")
                cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_end_date TIMESTAMP")
                cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_chat_id TEXT")
                cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_session_id TEXT")
                cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT")
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
            print("✅ Tabelas inicializadas com sucesso!")
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        print(f"⚠️ Erro ao inicializar banco: {e}")
        print("⚠️ O servidor continuará rodando, mas algumas funções podem não funcionar.")


def _dictify(row, cursor=None):
    if row is None:
        return None
    if USE_POSTGRES:
        return dict(row) if hasattr(row, 'keys') else row
    if cursor and hasattr(cursor, 'description'):
        return {desc[0]: row[i] for i, desc in enumerate(cursor.description)}
    return row


def register_user(user_id: str, name: str, email: str, bingx_key: str, bingx_secret: str, bingx_passphrase: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        enc_key = encrypt_key(bingx_key)
        enc_secret = encrypt_key(bingx_secret)
        enc_pass = encrypt_key(bingx_passphrase)
        if not enc_key.startswith("gAAAAA"):
            raise ValueError("Falha na criptografia")
        if USE_POSTGRES:
            cursor.execute("""
                INSERT INTO users (user_id, email, display_name, status, plan)
                VALUES (%s, %s, %s, 'ACTIVE', 'FREE')
                ON CONFLICT (user_id) DO UPDATE
                SET email=EXCLUDED.email, display_name=EXCLUDED.display_name, status='ACTIVE'
                RETURNING id
            """, (user_id, email, name))
            internal_id = cursor.fetchone()['id']
            cursor.execute("""
                INSERT INTO api_credentials (user_id, api_key_enc, api_secret_enc, passphrase_enc)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE
                SET api_key_enc=EXCLUDED.api_key_enc,
                    api_secret_enc=EXCLUDED.api_secret_enc,
                    passphrase_enc=EXCLUDED.passphrase_enc,
                    updated_at=CURRENT_TIMESTAMP
            """, (internal_id, enc_key, enc_secret, enc_pass))
        else:
            cursor.execute(
                "INSERT OR REPLACE INTO users (user_id, email, display_name, status, plan) VALUES (?, ?, ?, 'ACTIVE', 'FREE')",
                (user_id, email, name)
            )
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            internal_id = cursor.fetchone()[0]
            cursor.execute(
                "INSERT OR REPLACE INTO api_credentials (user_id, api_key_enc, api_secret_enc, passphrase_enc) VALUES (?, ?, ?, ?)",
                (internal_id, enc_key, enc_secret, enc_pass)
            )
        conn.commit()
        return True
    except Exception as e:
        print(f"DB ERROR: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def register_user_free(user_id: str, name: str, email: str, telegram_chat_id: str = None, stripe_session_id: str = None) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if USE_POSTGRES:
            cursor.execute("""
                INSERT INTO users (user_id, email, display_name, plan, status, telegram_chat_id, stripe_session_id)
                VALUES (%s, %s, %s, 'FREE', 'ACTIVE', %s, %s)
                ON CONFLICT (user_id) DO UPDATE
                SET email=EXCLUDED.email, telegram_chat_id=EXCLUDED.telegram_chat_id
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
        print(f"DB ERROR: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def upgrade_to_lifetime(user_id: str) -> bool:
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
        print(f"DB ERROR: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def upgrade_to_lifetime_by_email(email: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if USE_POSTGRES:
            cursor.execute("UPDATE users SET plan = 'LIFETIME', trial_end_date = NULL WHERE email = %s", (email,))
        else:
            cursor.execute("UPDATE users SET plan = 'LIFETIME', trial_end_date = NULL WHERE email = ?", (email,))
        conn.commit()
        return True
    except Exception as e:
        print(f"DB ERROR: {e}")
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
            cursor.execute("SELECT id, user_id, email, display_name, status, plan, telegram_chat_id FROM users WHERE email = %s", (email,))
        else:
            cursor.execute("SELECT id, user_id, email, display_name, status, plan, telegram_chat_id FROM users WHERE email = ?", (email,))
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


# Inicialização mais tolerante a erros
try:
    init_saas_db()
except Exception as e:
    print(f"⚠️ Erro na inicialização: {e}")
    print("⚠️ O servidor continuará rodando.")