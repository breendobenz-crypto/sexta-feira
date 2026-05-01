
# ==========================================
# POSITION MANAGER - JARVIS PRO (V2 - CACHED + THREAD-SAFE + HEARTBEAT)
# Otimização: Cache explícito de posições, thread-safe, heartbeat para Guardian,
# validação robusta, zero breaking changes na API
# ==========================================

import os
import time
import threading
import json
from datetime import datetime, timezone
from bybit_connect import get_account_info
from config import MAX_TRADES_ABERTOS, HEARTBEAT_FILE

# ==========================================
# 🔒 CACHE & THREAD SAFETY
# ==========================================
_pos_cache = {"data": None, "ts": 0.0}
_cache_lock = threading.Lock()
CACHE_TTL = 10  # segundos (suficiente para ciclo de scan)

# ==========================================
# ❤️ HEARTBEAT PARA O GUARDIÃO
# ==========================================
def _log_position_activity(action: str, symbol: str = None, details: dict = None):
    """Registra atividades de posição para monitoramento externo."""
    try:
        if os.path.exists(HEARTBEAT_FILE):
            with open(HEARTBEAT_FILE, "r") as f:
                hb = json.load(f)
            hb["last_pos_action"] = action
            hb["last_pos_symbol"] = symbol
            hb["last_pos_details"] = details or {}
            hb["last_pos_time"] = datetime.now(timezone.utc).isoformat()
            with open(HEARTBEAT_FILE, "w") as f:
                json.dump(hb, f)
    except:
        pass  # Silencioso

# ==========================================
# FETCH POSIÇÕES (COM CACHE)
# ==========================================
def _fetch_positions():
    """Busca posições da API com cache. Reutiliza cache interno do bybit_connect."""
    now = time.time()
    with _cache_lock:
        if _pos_cache["data"] is not None and (now - _pos_cache["ts"]) < CACHE_TTL:
            return _pos_cache["data"]

    try:
        info = get_account_info()  # Já possui cache de 5s no bybit_connect
        positions = info.get("positions", []) if info else []
        with _cache_lock:
            _pos_cache["data"] = positions
            _pos_cache["ts"] = now
        return positions
    except Exception as e:
        print(f"[POS ERROR] Falha ao buscar posições: {e}")
        _log_position_activity("fetch_failed", details={"error": str(e)})
        # Retorna cache antigo se existir, ou lista vazia
        with _cache_lock:
            return _pos_cache["data"] or []

# ==========================================
# FUNÇÕES PÚBLICAS (RETROCOMPATÍVEIS)
# ==========================================
def get_positions() -> list[dict]:
    """Retorna lista de posições atuais (com cache)."""
    return _fetch_positions()

def total_posicoes_abertas() -> int:
    """Conta posições com size > 0."""
    positions = get_positions()
    return sum(1 for p in positions if float(p.get("size", 0)) > 0)

def limite_global() -> bool:
    """Verifica se limite global de trades abertos foi atingido."""
    count = total_posicoes_abertas()
    if count >= MAX_TRADES_ABERTOS:
        print(f"[BLOCK] Limite global de posições atingido ({count}/{MAX_TRADES_ABERTOS})")
        _log_position_activity("global_limit_reached", details={"count": count, "max": MAX_TRADES_ABERTOS})
        return False
    return True

def tem_posicao_no_ativo(symbol: str) -> bool:
    """Verifica se há posição ativa (size > 0) no símbolo."""
    positions = get_positions()
    for p in positions:
        if p.get("symbol") == symbol and float(p.get("size", 0)) > 0:
            return True
    return False

def pode_abrir_trade(symbol: str, direcao: str = None) -> bool:
    """
    Validação final antes de enviar ordem.
    - Bloqueia se já houver posição no ativo (evita hedge não intencional)
    - Respeita limite global
    """
    # 1. Verifica posição no ativo
    if tem_posicao_no_ativo(symbol):
        print(f"[BLOCK] Já existe posição ativa em {symbol}")
        _log_position_activity("asset_position_exists", symbol=symbol)
        return False

    # 2. Verifica limite global
    if not limite_global():
        return False

    # 3. Aprovado
    _log_position_activity("trade_allowed", symbol=symbol)
    return True

def invalidate_cache():
    """
    Força invalidação do cache de posições.
    Chame após execução bem-sucedida de ordem para refresh imediato.
    """
    with _cache_lock:
        _pos_cache["data"] = None
        _pos_cache["ts"] = 0.0