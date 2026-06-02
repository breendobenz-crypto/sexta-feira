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
            
            # ADICIONA COLUNAS FALTANTES EM TABELAS JÁ EXISTENTES
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_end_date TIMESTAMP")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_chat_id TEXT")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_session_id TEXT")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS plan TEXT DEFAULT 'FREE'")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT")
            cursor.execute("ALTER TABLE api_credentials ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            cursor.execute("ALTER TABLE trades ADD COLUMN IF NOT EXISTS ai_reasoning TEXT")
            cursor.execute("ALTER TABLE trades ADD COLUMN IF NOT EXISTS close_time TIMESTAMP")
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
            
            # Adiciona colunas faltantes no SQLite também
            try: cursor.execute("ALTER TABLE users ADD COLUMN plan TEXT DEFAULT 'FREE'")
            except: pass
            try: cursor.execute("ALTER TABLE users ADD COLUMN trial_end_date TIMESTAMP")
            except: pass
            try: cursor.execute("ALTER TABLE users ADD COLUMN telegram_chat_id TEXT")
            except: pass
            try: cursor.execute("ALTER TABLE users ADD COLUMN stripe_session_id TEXT")
            except: pass
            try: cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
            except: pass
            try: cursor.execute("ALTER TABLE api_credentials ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            except: pass
            try: cursor.execute("ALTER TABLE trades ADD COLUMN ai_reasoning TEXT")
            except: pass
            try: cursor.execute("ALTER TABLE trades ADD COLUMN close_time TIMESTAMP")
            except: pass
        
        conn.commit()
    finally:
        cursor.close()
        conn.close()