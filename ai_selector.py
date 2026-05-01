# ==========================================
# AI ASSET SELECTOR - JARVIS PRO (V2 - CACHED + DB-INTEGRATED + NON-BLOCKING)
# Integração: performance_manager, database, market_regime
# Otimização: Cache de performance, normalização percentual, fallback seguro
# ==========================================

import time
from market_regime import detectar_regime
from performance_manager import pm
from database import get_asset_performance

# ==========================================
# CACHE LEVE DE PERFORMANCE POR ATIVO
# ==========================================
_perf_cache = {}
_perf_cache_ts = {}
PERF_CACHE_TTL = 300  # 5 minutos

def _get_cached_perf(symbol: str) -> dict:
    """Retorna métricas do ativo com cache para evitar queries repetidas no scan."""
    now = time.time()
    if symbol in _perf_cache and (now - _perf_cache_ts.get(symbol, 0)) < PERF_CACHE_TTL:
        return _perf_cache[symbol]
    
    # Busca no SQLite (últimos 20 trades para relevância recente)
    data = get_asset_performance(symbol, limit=20)
    _perf_cache[symbol] = data
    _perf_cache_ts[symbol] = now
    return data

# ==========================================
# PESOS (AUTO-NORMALIZAÇÃO)
# ==========================================
WEIGHTS = {
    "score": 0.4,
    "regime": 0.2,
    "momentum": 0.2,
    "performance": 0.2
}

def _normalizar_pesos(weights: dict) -> dict:
    total = sum(weights.values())
    return {k: v / total for k, v in weights.items()} if total > 0 else weights

WEIGHTS = _normalizar_pesos(WEIGHTS)

# ==========================================
# SCORE DE REGIME
# ==========================================
def _regime_score(regime: str) -> float:
    """Mapeia regime de mercado para fator multiplicador."""
    return {
        "TRENDING": 1.0,
        "VOLATILE": 0.8,
        "RANGING": 0.5,
        "UNKNOWN": 0.0
    }.get(regime, 0.0)

# ==========================================
# MOMENTUM (BASEADO NO SCORE TÉCNICO)
# ==========================================
def _momentum_score(score: float) -> float:
    """Converte score técnico bruto em fator de momentum."""
    if score >= 90: return 1.0
    if score >= 80: return 0.85
    if score >= 70: return 0.65
    return 0.3

# ==========================================
# PERFORMANCE DO ATIVO (ATUALIZADO PARA BANCA PEQUENA)
# ==========================================
def _performance_score(symbol: str) -> float:
    """
    Avalia win rate, pnl médio percentual e consistência.
    Retorna 0.5 (neutro) se não houver dados suficientes.
    """
    try:
        stats = _get_cached_perf(symbol)
        winrate = stats.get("win_rate", 0.5)
        avg_pnl_pct = stats.get("avg_pnl_pct", 0.0)  # Já vem em % do database
        total_trades = stats.get("total_trades", 0)

        # Normalização de PnL percentual (cap em ±5% por trade para estabilidade)
        pnl_norm = max(-1.0, min(avg_pnl_pct / 5.0, 1.0))

        # Bônus de consistência (mínimo 3 trades para confiar nos dados)
        consistencia = min(total_trades / 10.0, 1.0) if total_trades >= 3 else 0.0

        score = (winrate * 0.5) + (pnl_norm * 0.3) + (consistencia * 0.2)
        return max(0.0, min(score, 1.0))
    except Exception:
        return 0.5  # Fallback neutro

# ==========================================
# SCORE FINAL DO ATIVO
# ==========================================
def calcular_score_ativo(trade: dict) -> tuple[float, str]:
    """Calcula score composto e retorna (ai_score, regime)."""
    try:
        symbol = trade.get("symbol")
        base_score = float(trade.get("score", 0))

        if not symbol or base_score <= 0:
            return 0.0, "UNKNOWN"

        regime = detectar_regime(symbol)

        s_score = base_score / 100.0
        r_score = _regime_score(regime)
        m_score = _momentum_score(base_score)
        p_score = _performance_score(symbol)

        final = (
            s_score * WEIGHTS["score"] +
            r_score * WEIGHTS["regime"] +
            m_score * WEIGHTS["momentum"] +
            p_score * WEIGHTS["performance"]
        )

        return round(final, 4), regime

    except Exception as e:
        print(f"[AI SCORE ERROR] {trade.get('symbol', '?')}: {e}")
        return 0.0, "UNKNOWN"

# ==========================================
# RANQUEAR ATIVOS
# ==========================================
def rankear_ativos(oportunidades: list[dict]) -> list[dict]:
    """Ordena oportunidades pelo AI score decrescente."""
    ranking = []
    for trade in oportunidades:
        score_final, regime = calcular_score_ativo(trade)
        trade["ai_score"] = score_final
        trade["regime"] = regime
        
        if score_final > 0:
            ranking.append(trade)
            
    ranking.sort(key=lambda x: x["ai_score"], reverse=True)
    return ranking

# ==========================================
# ESCOLHER MELHOR ATIVO (SINGLE)
# ==========================================
def escolher_melhor_ativo(oportunidades: list[dict]) -> dict | None:
    ranking = rankear_ativos(oportunidades)
    return ranking[0] if ranking else None

# ==========================================
# ESCOLHER TOP N ATIVOS (MULTI) - NON-BLOCKING
# ==========================================
def escolher_melhores_ativos(oportunidades: list[dict], top_n: int = 2) -> list[dict]:
    ranking = rankear_ativos(oportunidades)
    if not ranking:
        return []

    # Fallback seguro: UNKNOWN assume RANGING com leve penalidade
    for trade in ranking:
        if trade.get("regime") == "UNKNOWN":
            trade["regime"] = "RANGING"
            trade["ai_score"] *= 0.9  # Penaliza 10% por falta de dados de regime

    # Reordena após ajustes
    ranking.sort(key=lambda x: x["ai_score"], reverse=True)
    return ranking[:top_n]