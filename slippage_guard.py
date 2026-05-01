# ==========================================
# SLIPPAGE GUARD - v3 (integrado ao strategy_engine)
# ==========================================
import os
import time
import threading
import json
from datetime import datetime, timezone
from bybit_connect import get_price
from config import SYMBOLS, ASSET_CONFIG, HEARTBEAT_FILE

_price_cache = {}
_cache_lock  = threading.Lock()
CACHE_TTL    = 10


def _log_slippage_block(symbol: str, diff_pct: float):
    try:
        if os.path.exists(HEARTBEAT_FILE):
            with open(HEARTBEAT_FILE, "r") as f:
                hb = json.load(f)
            hb["last_slippage_block"]    = symbol
            hb["last_slippage_diff_pct"] = round(diff_pct, 3)
            hb["last_slippage_time"]     = datetime.now(timezone.utc).isoformat()
            with open(HEARTBEAT_FILE, "w") as f:
                json.dump(hb, f)
    except Exception:
        pass


def _get_max_slippage(symbol: str) -> float:
    defaults = {
        "BTCUSDT":  0.15,
        "ETHUSDT":  0.15,
        "SOLUSDT":  0.25,
        "PAXGUSDT": 0.15,
    }
    return ASSET_CONFIG.get(symbol, {}).get("max_slippage_pct", defaults.get(symbol, 0.2))


def slippage_ok(symbol: str, entry: float, max_slippage_percent: float = None) -> bool:
    if not entry or entry <= 0:
        return False

    limit = max_slippage_percent if max_slippage_percent is not None else _get_max_slippage(symbol)
    now   = time.time()

    with _cache_lock:
        cached = _price_cache.get(symbol)
        if cached and (now - cached["ts"]) < CACHE_TTL:
            current_price = cached["price"]
        else:
            current_price = get_price(symbol)
            if current_price is None:
                print(f"[SLIPPAGE WARN] {symbol}: preco indisponivel. Bloqueando.")
                return False
            _price_cache[symbol] = {"price": current_price, "ts": now}

    diff_pct = abs(current_price - entry) / entry * 100

    if diff_pct > limit:
        print(
            f"[SLIPPAGE] {symbol} bloqueado: drift {diff_pct:.3f}% > max {limit:.3f}% "
            f"(entry:{entry}, atual:{current_price})"
        )
        _log_slippage_block(symbol, diff_pct)
        return False
    return True
