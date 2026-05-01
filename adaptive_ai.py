# ======================================
# ADAPTIVE AI - JARVIS PRO (V2 - ASSET-AWARE + PERSISTENT + GUARDIAN READY)
# Integração: config.ASSET_CONFIG, heartbeat, persistência de estado, fallback seguro
# ======================================
import json
import os
from datetime import datetime, timezone
from config import ASSET_CONFIG, HEARTBEAT_FILE, SYMBOLS

STATE_FILE = "adaptive_ai_state.json"

class AdaptiveAI:
    """
    Cérebro adaptativo que ajusta estado de mercado, confiança e fator de risco
    baseado em métricas de performance. Suporta modo global ou por ativo.
    """
    def __init__(self, symbol: str = None):
        self.symbol = symbol
        self.last_action = None
        self.market_state = "neutral"
        self.confidence = 0.5
        self.risk_factor = 1.0
        self.last_update = None
        self._load_state()

    # ==========================================
    # PERSISTÊNCIA DE ESTADO
    # ==========================================
    def _load_state(self):
        """Carrega estado salvo anteriormente (por ativo ou global)."""
        try:
            key = self.symbol or "global"
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, 'r') as f:
                    data = json.load(f)
                state = data.get(key, {})
                self.market_state = state.get("market_state", "neutral")
                self.confidence = state.get("confidence", 0.5)
                self.risk_factor = state.get("risk_factor", 1.0)
                self.last_update = state.get("last_update")
        except Exception as e:
            print(f"[AI WARN] Falha ao carregar estado: {e}")

    def _save_state(self):
        """Salva estado atual para sobreviver a reinicializações."""
        try:
            key = self.symbol or "global"
            data = {}
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, 'r') as f:
                    data = json.load(f)
            data[key] = {
                "market_state": self.market_state,
                "confidence": self.confidence,
                "risk_factor": self.risk_factor,
                "last_update": datetime.now(timezone.utc).isoformat()
            }
            with open(STATE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[AI WARN] Falha ao salvar estado: {e}")

    # ==========================================
    # HEARTBEAT PARA O GUARDIÃO
    # ==========================================
    def _log_activity(self, action: str, details: dict = None):
        """Registra mudança de estado para monitoramento externo."""
        try:
            if os.path.exists(HEARTBEAT_FILE):
                with open(HEARTBEAT_FILE, "r") as f:
                    hb = json.load(f)
                hb["last_ai_action"] = action
                hb["last_ai_symbol"] = self.symbol
                hb["last_ai_state"] = self.market_state
                hb["last_ai_time"] = datetime.now(timezone.utc).isoformat()
                with open(HEARTBEAT_FILE, "w") as f:
                    json.dump(hb, f)
        except:
            pass  # Silencioso: heartbeat é opcional

    # ==========================================
    # UPDATE PRINCIPAL (CHAMADO PELO ENGINE)
    # ==========================================
    def update(self, performance: dict | object):
        """
        Recebe métricas de performance e ajusta comportamento.
        Aceita dict ou objeto com métodos get_winrate(), get_streak(), get_drawdown().
        """
        # Extrair métricas de forma segura (compatível com dict ou objeto)
        if isinstance(performance, dict):
            winrate = performance.get("win_rate", 0.5)
            streak = performance.get("streak", 0)
            drawdown = performance.get("max_drawdown", 0.0)
        else:
            winrate = getattr(performance, "get_winrate", lambda: 0.5)()
            streak = getattr(performance, "get_streak", lambda: 0)()
            drawdown = getattr(performance, "get_drawdown", lambda: 0.0)()

        # Obter thresholds do config (por ativo ou global)
        thresholds = ASSET_CONFIG.get(self.symbol, {}) if self.symbol else {}
        aggressive_win = thresholds.get("aggressive_winrate", 0.60)
        defensive_dd = thresholds.get("defensive_drawdown", 0.05)
        min_streak = thresholds.get("streak_threshold", 2)

        # Leitura de Cenário
        if winrate >= aggressive_win and streak >= min_streak:
            new_state = "aggressive"
            new_confidence = min(0.95, self.confidence + 0.1)
        elif drawdown >= defensive_dd:
            new_state = "defensive"
            new_confidence = max(0.2, self.confidence - 0.2)
        else:
            new_state = "neutral"
            new_confidence = 0.5

        # Atualizar estado interno
        state_changed = new_state != self.market_state
        self.market_state = new_state
        self.confidence = new_confidence
        self.last_update = datetime.now(timezone.utc).isoformat()

        # Ajuste de Risco baseado no estado
        risk_multipliers = {
            "aggressive": 1.2,
            "defensive": 0.5,
            "neutral": 1.0
        }
        self.risk_factor = risk_multipliers.get(self.market_state, 1.0)

        # Logs e Persistência
        if state_changed:
            print(f"[AI 🧠] {self.symbol or 'GLOBAL'} -> Estado: {self.market_state} | "
                  f"Confiança: {self.confidence:.2f} | Risco: {self.risk_factor}x")
            self._log_activity("state_changed", {
                "from": self.market_state, "to": new_state, 
                "winrate": winrate, "dd": drawdown
            })
        self._save_state()

    # ==========================================
    # GETTERS PARA INTEGRAÇÃO
    # ==========================================
    def get_risk_factor(self) -> float:
        return self.risk_factor

    def get_confidence(self) -> float:
        return self.confidence

    def get_market_state(self) -> str:
        return self.market_state

    def status(self) -> dict:
        return {
            "symbol": self.symbol,
            "state": self.market_state,
            "confidence": round(self.confidence, 3),
            "risk_factor": round(self.risk_factor, 2),
            "last_update": self.last_update
        }