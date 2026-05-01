# ==========================================
# BYBIT SPREAD FILTER - JARVIS PRO (V2 - CACHED + CONFIG-DRIVEN + HEARTBEAT)
# Otimização: Cache de 15s, thresholds por ativo, heartbeat para Guardian, 
# zero breaking changes na assinatura da função
# ==========================================

import os
import time
import threading
import json
from datetime import datetime, timezone
from bybit_connect import get_orderbook
from config import SYMBOLS, ASSET_CONFIG, HEARTBEAT_FILE

# ==========================================
# 🔒 CACHE THREAD-SAFE
# ==========================================
_spread_cache = {}
_cache_lock = threading.Lock()
CACHE_TTL = 15  # segundos (suficiente para scan de 10s)

# ==========================================
# ❤️ HEARTBEAT PARA O GUARDIÃO
# ==========================================
def _log_spread_block(symbol: str, spread: float):
    """Registra bloqueio por spread alto para monitoramento externo."""
    try:
        if os.path.exists(HEARTBEAT_FILE):
            with open(HEARTBEAT_FILE, "r") as f:
                hb = json.load(f)
            hb["last_spread_block"] = symbol
            hb["last_spread_value"] = round(spread, 6)
            hb["last_spread_time"] = datetime.now(timezone.utc).isoformat()
            with open(HEARTBEAT_FILE, "w") as f:
                json.dump(hb, f)
    except:
        pass  # Silencioso

# ==========================================
# CONFIG POR ATIVO
# ==========================================
def _get_max_spread(symbol: str) -> float:
    """Retorna spread máximo permitido por ativo ou defaults conservadores."""
    defaults = {
        "BTCUSDT": 0.0008,   # 0.08% (alta liquidez)
        "ETHUSDT": 0.0010,   # 0.10%
        "SOLUSDT": 0.0015,   # 0.15% (volatilidade natural)
        "PAXGUSDT": 0.0012   # 0.12%
    }
    # Config do ativo sobrescreve default
    return ASSET_CONFIG.get(symbol, {}).get("max_spread_pct", defaults.get(symbol, 0.0015))

# ==========================================
# FUNÇÃO PRINCIPAL (RETROCOMPATÍVEL)
# ==========================================
def spread_ok(symbol: str, force_refresh: bool = False) -> bool:
    """
    Verifica se o spread está dentro do limite aceitável.
    Usa cache de 15s para evitar spam na API durante o scan.
    Retorna True se ok, False se alto ou erro.
    """
    now = time.time()
    
    # 1. Verifica cache
    with _cache_lock:
        cached = _spread_cache.get(symbol)
        if cached and not force_refresh and (now - cached["ts"]) < CACHE_TTL:
            return cached["ok"]

    # 2. Busca na API
    max_spread = _get_max_spread(symbol)
    book = get_orderbook(symbol)

    if not book or "bid" not in book or "ask" not in book:
        print(f"[SPREAD WARN] {symbol}: Orderbook inválido/incompleto. Bloqueando por segurança.")
        with _cache_lock:
            _spread_cache[symbol] = {"ok": False, "ts": now}
        return False

    # 3. Cálculo seguro
    try:
        bid = float(book["bid"])
        ask = float(book["ask"])
        
        if bid <= 0 or ask <= bid:
            print(f"[SPREAD WARN] {symbol}: Preço inválido (bid={bid}, ask={ask})")
            with _cache_lock:
                _spread_cache[symbol] = {"ok": False, "ts": now}
            return False

        spread = (ask - bid) / bid
        ok = spread <= max_spread

        if not ok:
            print(f"[SPREAD] {symbol} bloqueado: spread {spread:.6f} > máx {max_spread:.6f}")
            _log_spread_block(symbol, spread)
        # else: opcional -> print(f"[SPREAD OK] {symbol}: {spread:.6f}")

        with _cache_lock:
            _spread_cache[symbol] = {"ok": ok, "ts": now}
        return ok

    except (KeyError, TypeError, ValueError) as e:
        print(f"[SPREAD ERROR] {symbol}: Falha ao calcular spread - {e}")
        with _cache_lock:
            _spread_cache[symbol] = {"ok": False, "ts": now}
        return False