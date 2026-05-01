# ======================================
# PERFORMANCE MANAGER - JARVIS PRO (V2 - THREAD-SAFE + PERSISTENT + HEARTBEAT)
# Correções: Persistência de estado, thread safety, heartbeat para Guardian, 
# zero breaking changes na API existente
# ======================================
import json
import os
import threading
from datetime import datetime, timezone
from config import HEARTBEAT_FILE  # Para integração com o Guardian

STATE_FILE = "performance_state.json"
TRADES_LOG_FILE = "trades_log.json"

class PerformanceManager:
    """
    Gerencia métricas globais de performance, drawdown e fator de risco dinâmico.
    Estado persistido em JSON, thread-safe e integrado ao monitoramento externo.
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.initial_equity = 0.0
        self.current_equity = 0.0
        self.max_equity = 0.0
        self.drawdown = 0.0

        # Contadores
        self.total_trades = 0
        self.wins = 0
        self.losses = 0
        self.win_streak = 0
        self.loss_streak = 0
        self.win_rate = 0.0

        # Risco Dinâmico
        self.risk_multiplier_value = 1.0
        self._load_state()

    # ==========================================
    # PERSISTÊNCIA DE ESTADO
    # ==========================================
    def _load_state(self):
        """Restaura métricas após reinicialização (sobrevive a crashes/VPS reboot)."""
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, 'r') as f:
                    data = json.load(f)
                self.initial_equity = data.get("initial_equity", 0.0)
                self.max_equity = data.get("max_equity", 0.0)
                self.current_equity = data.get("current_equity", 0.0)
                self.drawdown = data.get("drawdown", 0.0)
                self.total_trades = data.get("total_trades", 0)
                self.wins = data.get("wins", 0)
                self.losses = data.get("losses", 0)
                self.win_rate = data.get("win_rate", 0.0)
                self.win_streak = data.get("win_streak", 0)
                self.loss_streak = data.get("loss_streak", 0)
                self.risk_multiplier_value = data.get("risk_multiplier_value", 1.0)
        except Exception as e:
            print(f"[PERF WARN] Falha ao carregar estado: {e}")

    def _save_state(self):
        """Salva estado atual para sobreviver a reinicializações."""
        try:
            data = {
                "initial_equity": self.initial_equity,
                "max_equity": self.max_equity,
                "current_equity": self.current_equity,
                "drawdown": self.drawdown,
                "total_trades": self.total_trades,
                "wins": self.wins,
                "losses": self.losses,
                "win_rate": self.win_rate,
                "win_streak": self.win_streak,
                "loss_streak": self.loss_streak,
                "risk_multiplier_value": self.risk_multiplier_value,
                "last_update": datetime.now(timezone.utc).isoformat()
            }
            with open(STATE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[PERF WARN] Falha ao salvar estado: {e}")

    # ==========================================
    # HEARTBEAT PARA O GUARDIÃO
    # ==========================================
    def _log_activity(self, action: str, details: dict = None):
        """Registra mudança de performance para monitoramento externo."""
        try:
            if os.path.exists(HEARTBEAT_FILE):
                with open(HEARTBEAT_FILE, "r") as f:
                    hb = json.load(f)
                hb["last_perf_action"] = action
                hb["last_perf_details"] = details or {}
                hb["last_perf_time"] = datetime.now(timezone.utc).isoformat()
                with open(HEARTBEAT_FILE, "w") as f:
                    json.dump(hb, f)
        except:
            pass  # Silencioso: heartbeat é opcional

    # ==========================================
    # EQUITY & DRAWDOWN
    # ==========================================
    def update_equity(self, equity: float):
        """Atualiza equity atual e recalcula drawdown em tempo real."""
        if equity <= 0:
            return
        with self.lock:
            if self.initial_equity == 0.0:
                self.initial_equity = equity
                self.max_equity = equity

            self.current_equity = equity
            if equity > self.max_equity:
                self.max_equity = equity

            self.drawdown = (
                (self.max_equity - equity) / self.max_equity
                if self.max_equity > 0 else 0.0
            )
            self._update_risk_multiplier()
            self._save_state()

    # ==========================================
    # REGISTRO DE TRADES
    # ==========================================
    def register_trade(self, pnl: float):
        """
        Registra resultado de trade e atualiza streaks/winrate.
        Thread-safe e persistente.
        """
        with self.lock:
            self.total_trades += 1
            if pnl > 0:
                self.wins += 1
                self.win_streak += 1
                self.loss_streak = 0
            else:
                self.losses += 1
                self.loss_streak += 1
                self.win_streak = 0

            if self.total_trades > 0:
                self.win_rate = self.wins / self.total_trades

            self._update_risk_multiplier()
            self._save_state()

            # Log detalhado para análise externa
            self._log_activity("trade_recorded", {
                "pnl": pnl, "win_rate": self.win_rate, 
                "drawdown": self.drawdown, "total": self.total_trades
            })

    # ==========================================
    # RISCO DINÂMICO (THRESHOLDS OTIMIZADOS)
    # ==========================================
    def _update_risk_multiplier(self):
        """Ajusta fator de risco baseado no drawdown atual."""
        # Thresholds conservadores para banca pequena
        if self.drawdown < 0.02:      # < 2% DD
            self.risk_multiplier_value = 1.0
        elif self.drawdown < 0.05:    # 2-5% DD
            self.risk_multiplier_value = 0.8
        elif self.drawdown < 0.10:    # 5-10% DD
            self.risk_multiplier_value = 0.6
        else:                         # > 10% DD (estado crítico)
            self.risk_multiplier_value = 0.3  # Reduzido para 0.3 (mais seguro que 0.4)

    # ==========================================
    # GETTERS (IA / ENGINE / DASHBOARD USA)
    # ==========================================
    def get_winrate(self) -> float:
        return self.win_rate

    def get_streak(self) -> int:
        if self.win_streak > 0:
            return self.win_streak
        if self.loss_streak > 0:
            return -self.loss_streak
        return 0

    def get_drawdown(self) -> float:
        return self.drawdown

    def risk_multiplier(self) -> float:
        return self.risk_multiplier_value

    def load_state(self) -> dict:
        """Retorna snapshot completo para dashboard/relatórios."""
        with self.lock:
            return {
                "total_trades": self.total_trades,
                "wins": self.wins,
                "losses": self.losses,
                "win_rate": round(self.win_rate, 3),
                "win_streak": self.win_streak,
                "loss_streak": self.loss_streak,
                "drawdown": round(self.drawdown, 4),
                "risk_multiplier": round(self.risk_multiplier_value, 2),
                "equity": round(self.current_equity, 2),
                "equity_peak": round(self.max_equity, 2),
                "initial_equity": round(self.initial_equity, 2)
            }

# ======================================
# SINGLETON GLOBAL (COMPATIBILIDADE)
# ======================================
pm = PerformanceManager()

# ======================================
# FUNÇÕES LEGACY / UTILITÁRIAS
# ======================================
def _init_trades_log():
    """Garante que o arquivo de log de trades exista."""
    if not os.path.exists(TRADES_LOG_FILE):
        with open(TRADES_LOG_FILE, "w") as f:
            json.dump([], f)

def registrar_trade(dados: dict):
    """
    🔥 Função chamada pelo execution_engine para salvar trade e atualizar performance.
    Mantida para compatibilidade total com seu código atual.
    """
    try:
        _init_trades_log()
        
        # Carrega log existente
        with open(TRADES_LOG_FILE, "r") as f:
            try:
                log_data = json.load(f)
            except Exception:
                log_data = []

        dados["timestamp"] = datetime.now(timezone.utc).isoformat()
        log_data.append(dados)

        # Salva log atualizado
        with open(TRADES_LOG_FILE, "w") as f:
            json.dump(log_data, f, indent=2)

        # Atualiza métricas globais
        pnl = dados.get("pnl_usdt", dados.get("pnl", 0))
        pm.register_trade(pnl)

        print(f"[PERF] ✅ Trade registrado | PnL: ${pnl:.2f} | WR: {pm.win_rate:.1%} | DD: {pm.drawdown:.1%}")

    except Exception as e:
        print(f"[PERF ERROR] Falha ao registrar trade: {e}")

def get_performance() -> dict:
    return pm.load_state()

def get_risk_multiplier() -> float:
    return pm.risk_multiplier()