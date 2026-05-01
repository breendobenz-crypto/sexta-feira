# ==========================================
# BRAIN OPTIMIZER - v3 (FIX CRITICO: paradoxo win_rate=0)
# Quando win_rate=0 o sistema TRAVA em score alto, nao relaxa filtros.
# ==========================================
import json
import os
import threading
from datetime import datetime, timezone
from config import SYMBOLS, ASSET_CONFIG, HEARTBEAT_FILE
from database import get_win_rate, get_all_closed_trades

MEMORY_FILE = "brain_memory.json"
lock = threading.Lock()

# Score minimo absoluto quando sem dados suficientes ou win_rate=0
FROZEN_SCORE = 82


def _log_activity(action: str, details: dict = None):
    try:
        if os.path.exists(HEARTBEAT_FILE):
            with open(HEARTBEAT_FILE, "r") as f:
                hb = json.load(f)
            hb["last_brain_action"] = action
            hb["last_brain_details"] = details or {}
            hb["last_brain_time"] = datetime.now(timezone.utc).isoformat()
            with open(HEARTBEAT_FILE, "w") as f:
                json.dump(hb, f)
    except Exception:
        pass


def _save_memory(key: str, entry: dict):
    try:
        full_memory = {}
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r") as f:
                full_memory = json.load(f)

        full_memory[key] = entry
        # Chaves raiz para compatibilidade com strategy_engine
        full_memory["optimized_min_score"] = entry["optimized_min_score"]
        full_memory["risk_level"]          = entry["risk_level"]

        with open(MEMORY_FILE, "w") as f:
            json.dump(full_memory, f, indent=2)
    except Exception as e:
        print(f"[BRAIN ERROR] Falha ao salvar memoria: {e}")


def optimize_strategy(symbol: str = None):
    """
    Ajusta MIN_SCORE dinamicamente baseado na performance real.
    FIX CRITICO: win_rate=0 trava score em FROZEN_SCORE=82 e retorna.
    Nunca mais reduz score quando o sistema esta perdendo.
    """
    defaults = {
        "aggressive_wr":    0.60,
        "conservative_wr":  0.40,
        "base_score":       75,
        "aggressive_score": 68,
        "conservative_score": 82,
        "min_score_bound":  68,
        "max_score_bound":  85,
    }
    if symbol and symbol in ASSET_CONFIG:
        thresholds = {**defaults, **ASSET_CONFIG[symbol]}
    else:
        thresholds = defaults

    with lock:
        min_trades = 3 if symbol else 5
        win_rate   = get_win_rate(symbol=symbol, min_trades=min_trades)
        trades     = get_all_closed_trades(limit=100, symbol=symbol)

    key = symbol if symbol else "global"

    # --- SEM DADOS SUFICIENTES ---
    if win_rate is None:
        print(f"[BRAIN] {key.upper()}: trades insuficientes (<{min_trades}). Mantendo padrao {thresholds['base_score']}.")
        return

    total   = len(trades)
    winners = [t for t in trades if (t.get("pnl_usdt") or 0) > 0]
    losers  = [t for t in trades if (t.get("pnl_usdt") or 0) <= 0]

    # --- FIX CRITICO: WIN_RATE = 0 ---
    if win_rate == 0.0 or len(winners) == 0:
        new_min_score = FROZEN_SCORE
        risk_level    = "FROZEN"
        print(
            f"BRAIN FROZEN ({key.upper()}): 0% win rate com {total} trades. "
            f"Score TRAVADO em {new_min_score}. Nao operar ate resolver perdas."
        )
        entry = {
            "optimized_min_score": new_min_score,
            "risk_level":          risk_level,
            "win_rate":            0.0,
            "total_trades":        total,
            "avg_score_winners":   0,
            "avg_score_losers":    round(sum(t.get("score", 70) for t in losers) / max(1, len(losers)), 1),
            "last_updated":        datetime.now(timezone.utc).isoformat(),
        }
        _save_memory(key, entry)
        _log_activity("brain_frozen", {"symbol": key, "score": new_min_score})
        return

    # --- CALCULO NORMAL (tem winners) ---
    avg_win_score  = sum(t.get("score", 70) for t in winners) / len(winners)
    avg_loss_score = sum(t.get("score", 70) for t in losers)  / max(1, len(losers))

    if win_rate >= thresholds["aggressive_wr"]:
        new_min_score = max(thresholds["aggressive_score"], avg_loss_score + 5)
        risk_level    = "AGGRESSIVE"
    elif win_rate <= thresholds["conservative_wr"]:
        new_min_score = min(thresholds["conservative_score"], avg_win_score - 5)
        risk_level    = "CONSERVATIVE"
    else:
        new_min_score = thresholds["base_score"]
        risk_level    = "NORMAL"

    new_min_score = int(max(thresholds["min_score_bound"],
                            min(thresholds["max_score_bound"], new_min_score)))

    entry = {
        "optimized_min_score": new_min_score,
        "risk_level":          risk_level,
        "win_rate":            round(win_rate, 4),
        "total_trades":        total,
        "avg_score_winners":   round(avg_win_score, 1),
        "avg_score_losers":    round(avg_loss_score, 1),
        "last_updated":        datetime.now(timezone.utc).isoformat(),
    }
    _save_memory(key, entry)
    _log_activity("brain_updated", {"symbol": key, "score": new_min_score, "wr": win_rate})

    print(
        f"CEREBRO ATUALIZADO ({key.upper()}) | Score min: {new_min_score} | "
        f"Risco: {risk_level} | WR: {win_rate:.1%} | Trades: {total} | "
        f"Score winners: {avg_win_score:.1f} | losers: {avg_loss_score:.1f}"
    )


def optimize_all_assets():
    optimize_strategy(symbol=None)
    for sym in SYMBOLS:
        optimize_strategy(symbol=sym)
    print("[BRAIN] Otimizacao completa (global + ativos) finalizada.")


if __name__ == "__main__":
    optimize_all_assets()
