# ==========================================
# EXPOSURE CONTROL - v3 (integrado ao strategy_engine)
# ==========================================
import os
import json
from datetime import datetime, timezone
from bybit_connect import get_account_info
from config import MAX_GLOBAL_EXPOSURE, HEARTBEAT_FILE


def _log_exposure_activity(action: str, details: dict = None):
    try:
        if os.path.exists(HEARTBEAT_FILE):
            with open(HEARTBEAT_FILE, "r") as f:
                hb = json.load(f)
            hb["last_exposure_action"]  = action
            hb["last_exposure_details"] = details or {}
            hb["last_exposure_time"]    = datetime.now(timezone.utc).isoformat()
            with open(HEARTBEAT_FILE, "w") as f:
                json.dump(hb, f)
    except Exception:
        pass


def calcular_exposicao_atual() -> dict:
    try:
        info = get_account_info()
        if not info:
            return {"total_notional": 0.0, "equity": 0.0, "positions": []}

        equity          = float(info.get("equity", 0))
        positions       = info.get("positions", [])
        total_notional  = 0.0
        active_positions = []

        for p in positions:
            size = float(p.get("size", 0))
            if size > 0:
                price    = float(p.get("markPrice", p.get("entryPrice", 0)))
                notional = size * price
                total_notional += notional
                active_positions.append({
                    "symbol":   p.get("symbol"),
                    "side":     p.get("side"),
                    "size":     size,
                    "notional": round(notional, 2),
                })

        return {
            "total_notional": round(total_notional, 2),
            "equity":         round(equity, 2),
            "positions":      active_positions,
        }
    except Exception as e:
        print(f"[EXPOSURE ERROR] {e}")
        _log_exposure_activity("calculation_failed", {"error": str(e)})
        return {"total_notional": 0.0, "equity": 0.0, "positions": []}


def exposicao_permitida(risco_novo_usdt: float) -> bool:
    try:
        metrics  = calcular_exposicao_atual()
        equity   = metrics["equity"]
        current  = metrics["total_notional"]

        if equity <= 0:
            _log_exposure_activity("blocked_equity_zero")
            return False

        max_allowed = equity * MAX_GLOBAL_EXPOSURE
        projected   = current + risco_novo_usdt

        if projected > max_allowed:
            print(
                f"[EXPOSURE BLOCK] Limite global excedido. "
                f"Atual:${current:.2f} + Novo:${risco_novo_usdt:.2f} > Max:${max_allowed:.2f}"
            )
            _log_exposure_activity("limit_exceeded", {
                "current": current, "new": risco_novo_usdt, "max": max_allowed,
            })
            return False
        return True
    except Exception as e:
        print(f"[EXPOSURE ERROR] {e}")
        _log_exposure_activity("validation_failed", {"error": str(e)})
        return False


def get_exposure_status() -> dict:
    metrics    = calcular_exposicao_atual()
    equity     = metrics["equity"]
    max_allow  = equity * MAX_GLOBAL_EXPOSURE
    usage_pct  = (metrics["total_notional"] / max_allow * 100) if max_allow > 0 else 0.0
    return {
        "total_notional":       metrics["total_notional"],
        "equity":               metrics["equity"],
        "max_allowed_notional": round(max_allow, 2),
        "usage_percent":        round(usage_pct, 2),
        "active_positions":     len(metrics["positions"]),
        "positions":            metrics["positions"],
    }
