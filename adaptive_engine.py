# ======================================
# ADAPTIVE ENGINE - JARVIS PRO
# FIX: Filtro de momentum menos restritivo + score_dinamico consistente
# ======================================
import json
import os
from collections import defaultdict
from global_state import performance as perf

TRADE_LOG = "trade_log.json"


# ==============================
# LEITURA DO LOG
# ==============================
def carregar_dados() -> list:
    if not os.path.exists(TRADE_LOG):
        return []
    try:
        with open(TRADE_LOG) as f:
            return json.load(f)
    except Exception:
        return []


# ==============================
# ANÁLISE POR ATIVO
# ==============================
def analisar_ativos() -> dict:
    stats = defaultdict(lambda: {"pnl": 0.0, "trades": 0})
    for t in carregar_dados():
        sym = t.get("symbol")
        if sym:
            stats[sym]["pnl"]    += t.get("pnl_pct", 0)
            stats[sym]["trades"] += 1
    return stats


# ==============================
# BLOQUEIO INTELIGENTE
# ==============================
def bloquear_ativo(symbol: str) -> bool:
    stats = analisar_ativos()
    data  = stats.get(symbol)
    if not data or data["trades"] < 5:
        return False
    # Bloqueia apenas se consistentemente ruim
    return data["pnl"] < -0.02


# ==============================
# SCORE DINÂMICO
# FIX: limites mais suaves e consistentes com brain_optimizer (65-80)
# ==============================
def score_dinamico() -> int:
    if perf.loss_streak >= 4:
        return 85          # só os melhores sinais após 4 losses seguidos
    if perf.loss_streak >= 2:
        return 78
    if perf.win_rate > 0.65:
        return 68          # mercado favorável → aceita sinais um pouco mais fracos
    return 75              # padrão


# ==============================
# APROVAÇÃO FINAL
# FIX: aceita momentum NORMAL quando score é suficientemente alto
# ==============================
def aprovar_trade(symbol: str, score: int, momentum: str) -> bool:
    if bloquear_ativo(symbol):
        print(f"[BLOCK] {symbol} bloqueado por performance ruim.")
        return False

    score_min = score_dinamico()
    if score < score_min:
        print(f"[REPROVADO] Score {score} < mínimo {score_min}")
        return False

    # FORTE / EXPLOSIVO → aceito sem restrição adicional
    if momentum in ("FORTE", "EXPLOSIVO"):
        return True

    # NORMAL → aceito desde que score seja bom (≥ 75)
    if momentum == "NORMAL" and score >= 75:
        return True

    print(f"[REPROVADO] Momentum '{momentum}' insuficiente para score {score}")
    return False


# ==============================
# RISCO ADAPTATIVO
# ==============================
def ajustar_risco(base_size: float, pnl_hoje: float = 0) -> float:
    try:
        size = base_size

        if perf.loss_streak >= 4:
            size *= 0.3
        elif perf.loss_streak >= 2:
            size *= 0.5

        if pnl_hoje < -100:
            size *= 0.5
        elif pnl_hoje < -50:
            size *= 0.7

        if perf.win_rate > 0.75:
            size *= 1.4
        elif perf.win_rate > 0.65:
            size *= 1.2

        return max(0.1, min(size, 2.0))

    except Exception as e:
        print(f"[AI RISK ERROR] {e}")
        return base_size
