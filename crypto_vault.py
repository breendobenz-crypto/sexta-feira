# crypto_vault.py - COFRE SAAS (CHAVE FIXA & DETERMINÍSTICA)
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# 🔑 CHAVE FIXA (Elimina problemas de .env, aspas, cache ou parsing)
MASTER_PASSWORD = "JarvisSaaS2026!"

def _get_key(password: str) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'jarvis_saas_v3_fixed_salt',
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))

_fernet = Fernet(_get_key(MASTER_PASSWORD))
print(f"[CRYPTO] Master Key fixada: {MASTER_PASSWORD[:10]}...")

def encrypt_key(plain_text: str) -> str:
    if not plain_text: return ""
    return _fernet.encrypt(plain_text.encode('utf-8')).decode('utf-8')

def decrypt_key(token: str) -> str:
    if not token: return ""
    try:
        return _fernet.decrypt(token.encode('utf-8')).decode('utf-8')
    except Exception as e:
        raise ValueError(f"Token inválido. Erro: {e}")