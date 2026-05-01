# ==========================================
# MARKET REGIME - v3 (FIX: import os faltando causava NameError)
# ==========================================
import os
import json
import time
import threading
from datetime import datetime, timezone

import pandas as pd
from bybit_connect import get_klines
from indicators import calcular_atr
from config import SYMBOLS, ASSET_CONFIG, HEARTBEAT_FILE

_regime_cache = {}
_cache_lock   = threading.Lock()
CACHE_TTL     = 60


def _log_regime_activity(symbol: str, regime: str, details: dict = None):
    try:
        if os.path.exists(HEARTBEAT_FILE):
            with open(HEARTBEAT_FILE, "r") as f:
                hb = json.load(f)
            hb["last_regime_symbol"]  = symbol
            hb["last_regime_value"]   = regime
            hb["last_regime_details"] = details or {}
            hb["last_regime_time"]    = datetime.now(timezone.utc).isoformat()
            with open(HEARTBEAT_FILE, "w") as f:
                json.dump(hb, f)
    except Exception:
        pass


def _get_thresholds(symbol: str) -> dict:
    defaults = {
        "volatile_atr_mult":  1.5,
        "trending_slope_mult": 2.0,
        "allow_volatile":     False,
        "trend_lookback":     20,
        "atr_mean_period":    30,
    }
    return {**defaults, **ASSET_CONFIG.get(symbol, {})}


def detectar_regime(symbol: str, force_refresh: bool = False) -> str:
    now = time.time()
    with _cache_lock:
        cached = _regime_cache.get(symbol)
        if cached and not force_refresh and (now - cached["ts"]) < CACHE_TTL:
            return cached["regime"]

    try:
        data = get_klines(symbol)
        if data is None or len(data) < 50:
            return "UNKNOWN"

        df  = data[["open", "high", "low", "close"]].astype(float)
        if df.empty:
            return "UNKNOWN"

        atr_series = calcular_atr(df)
        if atr_series is None or atr_series.empty:
            return "UNKNOWN"

        atr_val    = float(atr_series.iloc[-1])
        thresholds = _get_thresholds(symbol)
        media_atr  = atr_series.tail(thresholds["atr_mean_period"]).mean()

        lookback  = thresholds["trend_lookback"]
        tendencia = float(df["close"].iloc[-1] - df["close"].iloc[-lookback])

        if media_atr > 0 and atr_val > media_atr * thresholds["volatile_atr_mult"]:
            regime = "VOLATILE"
        elif abs(tendencia) > (atr_val * thresholds["trending_slope_mult"]):
            regime = "TRENDING"
        else:
            regime = "RANGING"

        with _cache_lock:
            _regime_cache[symbol] = {"regime": regime, "ts": now}

        if regime in ("VOLATILE", "UNKNOWN"):
            _log_regime_activity(symbol, regime, {"atr": atr_val, "trend": tendencia})

        return regime

    except Exception as e:
        print(f"[REGIME ERROR] {symbol}: {e}")
        return "RANGING"


def get_regime_details(symbol: str) -> dict:
    regime = detectar_regime(symbol)
    try:
        data      = get_klines(symbol)
        df        = data[["close"]].astype(float)
        atr_val   = float(calcular_atr(df).iloc[-1])
        tendencia = float(df["close"].iloc[-1] - df["close"].iloc[-20])
        return {
            "regime":         regime,
            "atr":            round(atr_val, 4),
            "trend_strength": round(tendencia, 2),
            "timestamp":      datetime.now(timezone.utc).isoformat(),
        }
    except Exception:
        return {"regime": regime, "atr": 0.0, "trend_strength": 0.0}


def mercado_favoravel(symbol: str) -> bool:
    try:
        regime     = detectar_regime(symbol)
        thresholds = _get_thresholds(symbol)
        if regime == "UNKNOWN":
            return False
        if regime == "VOLATILE":
            return thresholds["allow_volatile"]
        return True
    except Exception:
        return False
