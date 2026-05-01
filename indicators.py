# indicators.py - JARVIS PRO (V5 - CORRIGIDO)
import numpy as np
import pandas as pd
from okx_connect import get_klines  # ✅ Corrigido para okx_connect
from config import ASSET_CONFIG

# =====================================
# HELPER: Obtém perfil do ativo
# =====================================
def get_profile(symbol: str) -> dict:
    """Retorna configurações do ativo ou defaults seguros."""
    defaults = {
        "atr_multiplier_stop": 2.5,
        "atr_multiplier_tp": 4.0,
        "min_stop_pct": 0.003,
        "max_stop_pct": 0.03,
        "sweep_lookback": 15,
        "min_volume_mult": 1.1,
        "htf_required": True,
        "rsi_block_long": 70,
        "rsi_block_short": 30,
        "btc_correlation": symbol != "BTCUSDT",
        "use_gold_filter": symbol == "PAXGUSDT",
        "session_filter": False,
        "allow_counter_trend": False
    }
    return {**defaults, **ASSET_CONFIG.get(symbol, {})}

# =====================================
# ATR
# =====================================
def calcular_atr(df: pd.DataFrame, period: int = 14) -> pd.Series | None:
    if df is None or len(df) < period:
        return None
    # ✅ Removidos espaços das colunas
    df = df[["high", "low", "close"]].astype(float).dropna().reset_index(drop=True)
    df["prev_close"] = df["close"].shift(1)
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["prev_close"]).abs(),
        (df["low"]  - df["prev_close"]).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()

# =====================================
# RSI
# =====================================
def calcular_rsi(df: pd.DataFrame, period: int = 14) -> float | None:
    if df is None or len(df) < period + 1:
        return None
    close = df["close"].astype(float)
    delta = close.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss.replace(0, np.nan)
    rsi   = 100 - (100 / (1 + rs))
    val   = float(rsi.iloc[-1])
    return None if np.isnan(val) else val

# =====================================
# VOLUME ACIMA DA MÉDIA
# =====================================
def volume_acima_media(df: pd.DataFrame, mult: float = 1.2, period: int = 20) -> bool:
    if df is None or len(df) < period + 1:
        return True
    vol = df["volume"].astype(float)
    avg = vol.iloc[-period - 1:-1].mean()
    return float(vol.iloc[-1]) >= avg * mult

# =====================================
# FILTRO LATERAL
# =====================================
def mercado_lateral(df: pd.DataFrame) -> bool:
    if len(df) < 50:
        return True
    high      = df["high"].rolling(20).max().iloc[-1]
    low       = df["low"].rolling(20).min().iloc[-1]
    range_pct = (high - low) / df["close"].iloc[-1]
    return range_pct < 0.006

# =====================================
# LIQUIDITY SWEEP
# =====================================
def detectar_liquidez(df: pd.DataFrame, lookback: int = 15,
                      min_vol_mult: float = 1.1) -> tuple[str | None, int]:
    if df is None or len(df) < lookback + 2:
        return None, 0

    last_high = df["high"].rolling(lookback).max().iloc[-2]
    last_low  = df["low"].rolling(lookback).min().iloc[-2]
    high      = float(df["high"].iloc[-1])
    low       = float(df["low"].iloc[-1])
    close     = float(df["close"].iloc[-1])
    vol_ok    = volume_acima_media(df, mult=min_vol_mult)

    if low < last_low and close > last_low:
        return "LONG",  (90 if vol_ok else 72)
    if high > last_high and close < last_high:
        return "SHORT", (90 if vol_ok else 72)
    return None, 0

# =====================================
# HTF TREND (BLINDADO EM 1H / 60min)
# =====================================
def tendencia_htf(symbol: str) -> str | None:
    """Analisa a tendência macro no gráfico de 1H."""
    try:
        # ✅ Removido espaço do intervalo
        df = get_klines(symbol, interval="60") 
        if df is None or len(df) < 50:
            return None
        df    = df.dropna().reset_index(drop=True)
        ema21 = float(df["close"].ewm(span=21).mean().iloc[-1])
        ema50 = float(df["close"].ewm(span=50).mean().iloc[-1])
        if ema21 > ema50: return "LONG"
        if ema21 < ema50: return "SHORT"
        return "RANGING"
    except Exception:
        return None

# =====================================
# CORRELAÇÃO BTC (TAMBÉM EM 1H)
# =====================================
def btc_confirma_direcao(direcao: str) -> bool:
    """Confirma se o BTC está alinhado no gráfico de 1H."""
    try:
        df = get_klines("BTCUSDT", interval="60")
        if df is None or len(df) < 30:
            return True
        ema9  = float(df["close"].ewm(span=9).mean().iloc[-1])
        ema21 = float(df["close"].ewm(span=21).mean().iloc[-1])
        return (ema9 > ema21) if direcao == "LONG" else (ema9 < ema21)
    except Exception:
        return True

# =====================================
# FAKE BREAKOUT
# =====================================
def fake_breakout(df: pd.DataFrame, direcao: str) -> bool:
    high_range = df["high"].rolling(20).max().iloc[-2]
    low_range  = df["low"].rolling(20).min().iloc[-2]
    high       = float(df["high"].iloc[-1])
    low        = float(df["low"].iloc[-1])
    close      = float(df["close"].iloc[-1])

    if direcao == "LONG" and high > high_range and close < high_range:
        return True
    if direcao == "SHORT" and low < low_range and close > low_range:
        return True
    return False

# =====================================
# STOP LOSS DINÂMICO
# =====================================
def calcular_stop(df: pd.DataFrame, direcao: str, atr: float,
                  entry: float, profile: dict) -> float:
    mult    = profile.get("atr_multiplier_stop", 2.5)
    min_pct = profile.get("min_stop_pct", 0.003)
    max_pct = profile.get("max_stop_pct", 0.03)

    if direcao == "LONG":
        recent_low  = float(df["low"].rolling(5).min().iloc[-1])
        stop_atr = entry - (atr * mult)
        stop_swing = recent_low
        stop = max(stop_atr, stop_swing)
        min_stop = entry * (1 - min_pct)
        max_stop = entry * (1 - max_pct)
        return float(np.clip(stop, max_stop, min_stop))
    else:
        recent_high = float(df["high"].rolling(5).max().iloc[-1])
        stop_atr = entry + (atr * mult)
        stop_swing = recent_high
        stop = min(stop_atr, stop_swing)
        min_stop = entry * (1 + min_pct)
        max_stop = entry * (1 + max_pct)
        return float(np.clip(stop, min_stop, max_stop))

# =====================================
# GERADOR DE SINAL PRINCIPAL
# =====================================
def gerar_sinal(symbol: str):
    try:
        profile = get_profile(symbol)
        df = get_klines(symbol)
        if df is None or len(df) < 200:
            return None

        df    = df.copy().dropna().reset_index(drop=True)
        price = float(df["close"].iloc[-1])

        atr_series = calcular_atr(df)
        if atr_series is None: return None
        atr = float(atr_series.iloc[-1])
        if atr == 0 or np.isnan(atr): return None

        rsi = calcular_rsi(df)
        htf = tendencia_htf(symbol)

        # Session filter
        if profile.get("session_filter"):
            from datetime import datetime, timezone
            hora = datetime.now(timezone.utc).hour
            if symbol == "PAXGUSDT":
                # London (7-11) + NY (13-17)
                if not ((7 <= hora <= 11) or (13 <= hora <= 17)):
                    return None
            else:
                # Fallback genérico
                if not (7 <= hora <= 11 or 13 <= hora <= 17):
                    return None

        # 1. LIQUIDITY SWEEP
        liq, liq_score = detectar_liquidez(df)

        if liq and liq_score >= 72:
            if profile.get("htf_required", True) and htf and htf != "RANGING" and htf != liq:
                liq = None
            
            if liq and rsi is not None:
                if liq == "LONG" and rsi > profile.get("rsi_block_long", 70): liq = None
                elif liq == "SHORT" and rsi < profile.get("rsi_block_short", 30): liq = None
            
            if liq and profile.get("btc_correlation", False) and not btc_confirma_direcao(liq):
                liq = None
            
            if liq:
                stop = calcular_stop(df, liq, atr, price, profile)
                take = (price + atr * profile.get("atr_multiplier_tp", 4.0)) if liq == "LONG" else (price - atr * profile.get("atr_multiplier_tp", 4.0))
                return liq, liq_score, price, stop, take

        # 2. EMA CROSS TREND FOLLOWING
        df["ema9"]  = df["close"].ewm(span=9).mean()
        df["ema21"] = df["close"].ewm(span=21).mean()
        df["ema50"] = df["close"].ewm(span=50).mean()

        ema9  = float(df["ema9"].iloc[-1])
        ema21 = float(df["ema21"].iloc[-1])
        ema50 = float(df["ema50"].iloc[-1])

        direcao = None
        if ema9 > ema21 and ema21 > ema50:
            direcao = "LONG"
        elif ema9 < ema21 and ema21 < ema50:
            direcao = "SHORT"

        if not direcao: return None

        # Filtros de bloqueio
        if htf and htf != "RANGING" and htf != direcao: return None
        if fake_breakout(df, direcao): return None
        if rsi is not None:
            if direcao == "LONG" and rsi > profile.get("rsi_block_long", 70): return None
            if direcao == "SHORT" and rsi < profile.get("rsi_block_short", 30): return None
        if profile.get("btc_correlation", False) and not btc_confirma_direcao(direcao): return None

        distancia  = abs(ema9 - ema21) / price
        mom_series = df["close"].pct_change().rolling(5).mean()
        momentum   = abs(float(mom_series.iloc[-1])) if not np.isnan(mom_series.iloc[-1]) else 0
        score      = int(60 + min((distancia * 10000) + (momentum * 25000), 40))

        if score < 70: return None

        stop = calcular_stop(df, direcao, atr, price, profile)
        take = (price + atr * profile.get("atr_multiplier_tp", 4.0)) if direcao == "LONG" else (price - atr * profile.get("atr_multiplier_tp", 4.0))

        return direcao, score, price, stop, take

    except Exception as e:
        print(f"[INDICATORS ERROR] {symbol}: {e}")
        return None