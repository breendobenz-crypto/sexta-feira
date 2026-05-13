# criar_usuario_cloud.py - Cria usuário no PostgreSQL da nuvem (Render/Railway)
import os
import sys
import hashlib
import psycopg2
from psycopg2.extras import RealDictCursor

# Adiciona pasta atual ao path para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ⚠️ MESMO SALT USADO NO dashboard_saas.py
SALT = "sexta-feira-advanced-vip-salt-2026"

def hash_password(password: str) -> str:
    """Gera hash da senha igual ao dashboard."""
    return hashlib.sha256((password + SALT).encode()).hexdigest()

def criar_usuario_cloud(db_url: str, email: str, nome: str, senha: str) -> bool:
    """Cria ou atualiza usuário no PostgreSQL remoto."""
    
    senha_hash = hash_password(senha)
    
    try:
        # Conecta ao PostgreSQL
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # Cria tabela users se não existir (schema compatível)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                user_id TEXT UNIQUE,
                email TEXT UNIQUE NOT NULL,
                display_name TEXT,
                plan TEXT DEFAULT 'VIP',
                status TEXT DEFAULT 'ACTIVE',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                password_hash TEXT
            )
        """)
        
        # INSERT com UPSERT (se email existir, atualiza)
        cur.execute("""
            INSERT INTO users (email, display_name, password_hash, status, plan)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (email) 
            DO UPDATE SET 
                password_hash = EXCLUDED.password_hash,
                display_name = EXCLUDED.display_name,
                status = EXCLUDED.status
            RETURNING id, email, status;
        """, (email, nome, senha_hash, 'active', 'VIP'))
        
        user = cur.fetchone()
        conn.commit()
        
        print(f"✅ Usuário criado/atualizado na nuvem!")
        print(f"🆔 ID: {user['id']}")
        print(f"📧 Email: {user['email']}")
        print(f"🔐 Status: {user['status']}")
        print(f"🔑 Senha para login: {senha}")
        print(f"\n🌐 Acesse: https://sexta-feira-wm1s.onrender.com")
        
        cur.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Erro PostgreSQL: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

if __name__ == "__main__":
    # 🔐 COLE SUA DATABASE_URL COMPLETA AQUI
    # Formato correto: postgresql://user:pass@host.region-postgres.render.com:5432/dbname
    DB_URL = "postgresql://sextafeira_user:tV57oiV1z4EgCfmP7fbvBKd4joBkvJ7b@dpg-d7t1fpugvqtc73a5s0eg-a.singapore-postgres.render.com:5432/sextafeira"
    
    print("🔄 Conectando ao PostgreSQL da nuvem...")
    
    sucesso = criar_usuario_cloud(
        db_url=DB_URL,
        email="breendobenz@gmail.com",
        nome="Breendo",
        senha="123456"  # ← Troque por uma senha segura após criar
    )
    
    if not sucesso:
        print("\n💡 Dicas para resolver:")
        print("  • Verifique se a DATABASE_URL está COMPLETA (com .region-postgres.render.com)")
        print("  • Confirme se o banco permite conexões externas")
        print("  • Verifique se a tabela 'users' tem permissão de escrita")
        print("  • Rode: pip install psycopg2-binary")