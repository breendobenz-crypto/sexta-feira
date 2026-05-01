# ==========================================
# TRADE LIMITER - v3 (integrado ao strategy_engine)
# ==========================================
import json
import os
import threading
from datetime import datetime, timezone
from config import ASSET_CONFIG, SYMBOLS, HEARTBEAT_FILE

STATE_FILE = "trade_limiter_state.json"


class TradeLimiter:
    def __init__(self):
        self.lock = threading.Lock()
        self.data: dict = {}
        self._load_state()

    def _load_state(self):
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, "r") as f:
                    self.data = json.load(f)
        except Exception as e:
            print(f"[LIMITER WARN] Falha ao carregar estado: {e}")
            self.data = {}

    def _save_state(self):
        try:
            with open(STATE_FILE, "w") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"[LIMITER ERROR] Falha ao salvar estado: {e}")

    def _log_activity(self, action: str, symbol: str, count: int, limit: int):
        try:
            if os.path.exists(HEARTBEAT_FILE):
                with open(HEARTBEAT_FILE, "r") as f:
                    hb = json.load(f)
                hb["last_limiter_action"] = action
                hb["last_limiter_symbol"] = symbol
                hb["last_limiter_count"]  = f"{count}/{limit}"
                hb["last_limiter_time"]   = datetime.now(timezone.utc).isoformat()
                with open(HEARTBEAT_FILE, "w") as f:
                    json.dump(hb, f)
        except Exception:
            pass

    def verificar_limite(self, symbol: str) -> bool:
        hoje  = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        limit = ASSET_CONFIG.get(symbol, {}).get("max_trades_per_day", 3)

        with self.lock:
            if symbol not in self.data:
                self.data[symbol] = {"date": hoje, "count": 0}

            if self.data[symbol]["date"] != hoje:
                self.data[symbol]["date"]  = hoje
                self.data[symbol]["count"] = 0

            count = self.data[symbol]["count"]

            if count >= limit:
                print(f"[LIMITER] {symbol}: limite diario ({count}/{limit})")
                self._log_activity("limit_reached", symbol, count, limit)
                return False
            return True

    def registrar_trade(self, symbol: str):
        with self.lock:
            if symbol not in self.data:
                self.data[symbol] = {
                    "date":  datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "count": 0,
                }
            self.data[symbol]["count"] += 1
            self._save_state()
            print(f"[LIMITER] {symbol}: {self.data[symbol]['count']} trade(s) hoje.")

    def get_stats(self) -> dict:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        stats = {}
        for symbol in SYMBOLS:
            limit = ASSET_CONFIG.get(symbol, {}).get("max_trades_per_day", 3)
            count = (
                self.data[symbol]["count"]
                if symbol in self.data and self.data[symbol]["date"] == today
                else 0
            )
            stats[symbol] = {"count": count, "limit": limit, "remaining": max(0, limit - count)}
        return stats


limiter = TradeLimiter()
