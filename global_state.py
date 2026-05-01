# ======================================
# GLOBAL STATE - JARVIS CORE MEMORY (V2 - API ALIGNED)
# Registro central de singletons compartilhados entre Strategy Engine, 
# Risk Manager, IA e Dashboard.
# ======================================

from performance_manager import PerformanceManager

# ======================================
# FALLBACK IA (COMPATÍVEL COM API V2)
# ======================================
try:
    from adaptive_ai import AdaptiveAI
except ImportError:
    # Fallback seguro caso adaptive_ai.py não exista ou falhe no import
    class AdaptiveAI:
        def __init__(self, symbol: str = None):
            self.symbol = symbol
            self.market_state = "neutral"
            self.confidence = 0.5
            self.risk_factor = 1.0

        def update(self, performance_data: dict | object = None) -> None:
            """No-op: mantém compatibilidade de chamada sem quebrar o loop."""
            pass

        def get_risk_factor(self) -> float:
            return self.risk_factor

        def get_confidence(self) -> float:
            return self.confidence

        def status(self) -> dict:
            return {
                "state": self.market_state,
                "confidence": self.confidence,
                "risk_factor": self.risk_factor
            }

# ======================================
# SINGLETONS GLOBAIS
# ======================================
# Instâncias únicas compartilhadas por todo o ecossistema
performance = PerformanceManager()
adaptive_ai = AdaptiveAI(symbol=None)  # Modo global (aplica a todos os ativos)