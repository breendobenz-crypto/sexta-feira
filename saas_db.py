# saas_db.py - GESTÃO SAAS COM POSTGRESQL (RENDER/SUPABASE)
import os
import hashlib
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone
from crypto_vault import encrypt_key, decrypt_key
from cryptography.fernet import InvalidToken

# ==========================================
# CONEXÃO COM POSTGRESQL
# ==========================================
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    """Retorna uma conexão com o banco PostgreSQL."""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL não configurada nas variáveis de ambiente.")
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

SALT = "sexta-feira-advanced-vip-salt-2026"

def hash_password(password: str) -> str:
    """Gera hash SHA256 da senha com salt."""
    return hashlib.sha256((password + SALT).encode()).hexdigest()

def init_saas_db():
    """Cria as tabelas se não existirem."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Tabela de Usuários
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            user_id TEXT UNIQUE,
            email TEXT UNIQUE NOT NULL,
            display_name TEXT,
            plan TEXT DEFAULT 'VIP',
            status TEXT DEFAULT 'ACTIVE',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            password_hash TEXT
        )''')

        # Tabela de Credenciais
        cursor.execute('''CREATE TABLE IF NOT EXISTS api_credentials (
            user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            api_key_enc TEXT NOT NULL,
            api_secret_enc TEXT NOT NULL,
            passphrase_enc TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        # Tabela de Trades
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
        
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def register_user(user_id: str, name: str, email: str, okx_key: str, okx_secret: str, okx_pass: str) -> bool:
    """Registra um novo usuário e suas credenciais."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        enc_key, enc_secret, enc_pass = encrypt_key(okx_key), encrypt_key(okx_secret), encrypt_key(okx_pass)
        if not enc_key.startswith("gAAAAA"):
            raise ValueError("Falha na criptografia")
        
        # Upsert para users
        cursor.execute("""
            INSERT INTO users (user_id, email, display_name, status)
            VALUES (%s, %s, %s, 'ACTIVE')
            ON CONFLICT (user_id) DO UPDATE SET
                email=EXCLUDED.email,
                display_name=EXCLUDED.display_name,
                status='ACTIVE'
            RETURNING id
        """, (user_id, email, name))
        
        internal_id = cursor.fetchone()['id']
        
        # Upsert para credenciais
        cursor.execute("""
            INSERT INTO api_credentials (user_id, api_key_enc, api_secret_enc, passphrase_enc)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                api_key_enc=EXCLUDED.api_key_enc,
                api_secret_enc=EXCLUDED.api_secret_enc,
                passphrase_enc=EXCLUDED.passphrase_enc,
                updated_at=CURRENT_TIMESTAMP
        """, (internal_id, enc_key, enc_secret, enc_pass))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ [DB ERROR] {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def get_user_by_email(email: str) -> dict | None:
    """Busca usuário pelo email."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, user_id, email, display_name, status FROM users WHERE email = %s AND status = 'ACTIVE'",
            (email,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        cursor.close()
        conn.close()

def get_user_full(email: str) -> dict | None:
    """Retorna usuário completo incluindo password_hash."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, user_id, email, display_name, status, password_hash FROM users WHERE email = %s",
            (email,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        cursor.close()
        conn.close()

def set_user_password(email: str, password: str):
    """Define ou atualiza a senha do usuário."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        pwd_hash = hash_password(password)
        cursor.execute("UPDATE users SET password_hash = %s WHERE email = %s", (pwd_hash, email))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def verify_password(email: str, password: str) -> bool:
    """Verifica se a senha está correta."""
    user = get_user_full(email)
    if not user:
        return False
    stored_hash = user.get('password_hash')
    if not stored_hash:
        return False
    return stored_hash == hash_password(password)

def update_user_credentials(user_id: int, api_key: str, api_secret: str, passphrase: str) -> bool:
    """Atualiza as credenciais OKX do usuário (criptografadas)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        enc_key = encrypt_key(api_key)
        enc_secret = encrypt_key(api_secret)
        enc_pass = encrypt_key(passphrase)
        
        if not enc_key.startswith("gAAAAA"):
            raise ValueError("Falha na criptografia")
        
        cursor.execute("""
            INSERT INTO api_credentials (user_id, api_key_enc, api_secret_enc, passphrase_enc, updated_at)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id) DO UPDATE SET
                api_key_enc=EXCLUDED.api_key_enc,
                api_secret_enc=EXCLUDED.api_secret_enc,
                passphrase_enc=EXCLUDED.passphrase_enc,
                updated_at=CURRENT_TIMESTAMP
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

def get_decrypted_credentials(internal_user_id: int) -> dict | None:
    """Busca e descriptografa credenciais pelo ID interno."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT api_key_enc, api_secret_enc, passphrase_enc FROM api_credentials WHERE user_id = %s",
            (internal_user_id,)
        )
        row = cursor.fetchone()
        if row:
            return {
                "api_key": decrypt_key(row['api_key_enc']),
                "api_secret": decrypt_key(row['api_secret_enc']),
                "passphrase": decrypt_key(row['passphrase_enc'])
            }
        return None
    except InvalidToken:
        return None
    finally:
        cursor.close()
        conn.close()

def get_user_credentials(user_id: str) -> dict | None:
    """Busca credenciais pelo ID externo (string/email). Usado pelo Bot principal."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()
        if row:
            return get_decrypted_credentials(row['id'])
        return None
    finally:
        cursor.close()
        conn.close()

def update_last_login(internal_user_id: int):
    """Atualiza o último login do usuário."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s", (internal_user_id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def get_all_users() -> list[dict]:
    """Retorna todos os usuários."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, user_id, email, display_name, plan, status, joined_at FROM users ORDER BY joined_at DESC")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        cursor.close()
        conn.close()

def update_user_status(user_id: str, status: str):
    """Atualiza o status do usuário."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET status = %s WHERE user_id = %s", (status, user_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def save_trade(user_id: int, symbol: str, side: str, entry: float, qty: float, score: int, reasoning: str = ""):
    """Salva um novo trade."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO trades (user_id, symbol, side, entry_price, size, score, ai_reasoning, open_time, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, 'OPEN')
        """, (user_id, symbol, side, entry, qty, score, reasoning))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def update_trade_exit(user_id: int, symbol: str, close_time: str, exit_price: float, pnl_usdt: float, pnl_pct: float):
    """Atualiza um trade com dados de saída."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE trades SET exit_price = %s, pnl_usdt = %s, pnl_pct = %s, status = 'CLOSED', close_time = %s
            WHERE user_id = %s AND symbol = %s AND status = 'OPEN'
        """, (exit_price, pnl_usdt, pnl_pct, close_time, user_id, symbol))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def get_closed_trades(internal_user_id: int, limit: int = 50) -> list[dict]:
    """Retorna trades fechados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT symbol, side, entry_price, exit_price, pnl_usdt, pnl_pct, score, close_time, ai_reasoning
            FROM trades WHERE user_id = %s AND status = 'CLOSED' ORDER BY close_time DESC LIMIT %s
        """, (internal_user_id, limit))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        cursor.close()
        conn.close()

def get_open_trades(internal_user_id: int) -> list[dict]:
    """Retorna trades abertos."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT symbol, side, entry_price, size, score, open_time FROM trades WHERE user_id = %s AND status = 'OPEN' ORDER BY open_time DESC",
            (internal_user_id,)
        )
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        cursor.close()
        conn.close()

def get_user_stats(internal_user_id: int) -> dict:
    """Retorna estatísticas do usuário."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(*) as total_trades,
                   SUM(CASE WHEN pnl_usdt > 0 THEN 1 ELSE 0 END) as wins,
                   SUM(CASE WHEN pnl_usdt <= 0 THEN 1 ELSE 0 END) as losses,
                   COALESCE(SUM(pnl_usdt), 0) as total_pnl,
                   COALESCE(AVG(pnl_pct), 0) as avg_pct,
                   COALESCE(MIN(pnl_usdt), 0) as worst_loss,
                   COALESCE(MAX(pnl_usdt), 0) as best_win
            FROM trades WHERE user_id = %s AND status = 'CLOSED'
        """, (internal_user_id,))
        row = cursor.fetchone()
        if not row:
            return {
                "total_trades": 0, "wins": 0, "losses": 0,
                "total_pnl": 0.0, "avg_pct": 0.0,
                "worst_loss": 0.0, "best_win": 0.0, "win_rate": 0.0
            }
        
        total = row['total_trades'] or 0
        wins = row['wins'] or 0
        
        return {
            "total_trades": total,
            "wins": wins,
            "losses": row['losses'] or 0,
            "total_pnl": float(row['total_pnl'] or 0),
            "avg_pct": float(row['avg_pct'] or 0),
            "worst_loss": float(row['worst_loss'] or 0),
            "best_win": float(row['best_win'] or 0),
            "win_rate": wins / max(1, total)
        }
    finally:
        cursor.close()
        conn.close()

def get_equity_curve(internal_user_id: int, days: int = 30) -> list[dict]:
    """Retorna curva de equity."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT DATE(close_time) as date, SUM(pnl_usdt) as daily_pnl, COUNT(*) as trades
            FROM trades
            WHERE user_id = %s AND status = 'CLOSED' AND close_time >= NOW() - (INTERVAL '1 day' * %s)
            GROUP BY DATE(close_time) ORDER BY date ASC
        """, (internal_user_id, days))
        
        rows = cursor.fetchall()
        equity = 0
        result = []
        for row in rows:
            equity += float(row['daily_pnl'] or 0)
            result.append({
                "date": str(row['date']),
                "equity": round(equity, 2),
                "daily_pnl": round(float(row['daily_pnl'] or 0), 2),
                "trades": row['trades']
            })
        return result
    finally:
        cursor.close()
        conn.close()

def get_active_users() -> list[str]:
    """Retorna lista de IDs de usuários ativos."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT user_id FROM users WHERE status = 'ACTIVE'")
        return [row['user_id'] for row in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()

# Inicializa o banco ao importar
init_saas_db()