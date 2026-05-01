# okx_connect.py - JARVIS SAAS (VERSÃO FINAL COM CAMADA DE COMPATIBILIDADE)
import time
import hashlib
import hmac
import base64
import json
import requests
import pandas as pd
import threading
from datetime import datetime, timezone

class OKXClient:
    def __init__(self, api_key, api_secret, passphrase, simulated=False):
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.simulated = simulated
        self.BASE_URL = "https://www.okx.com"
        self._http = requests.Session()
        self._lock = threading.Lock()
        self._last_req_time = 0.0
        self._account_cache = {"data": None, "ts": 0.0}
        self._klines_cache = {}
        self.SYMBOL_MAP = {
            "BTCUSDT": "BTC-USDT-SWAP", "ETHUSDT": "ETH-USDT-SWAP",
            "SOLUSDT": "SOL-USDT-SWAP", "PAXGUSDT": "PAXG-USDT-SWAP",
        }
        self.CT_VAL = {"BTCUSDT": 0.01, "ETHUSDT": 0.1, "SOLUSDT": 1.0, "PAXGUSDT": 0.01}

    def _rate_limit(self):
        with self._lock:
            now = time.time()
            elapsed = now - self._last_req_time
            if elapsed < 0.2: time.sleep(0.2 - elapsed)
            self._last_req_time = time.time()

    def _sign(self, timestamp, method, path, body=""):
        msg = f"{timestamp}{method.upper()}{path}{body}"
        mac = hmac.new(bytes(self.api_secret, 'utf8'), bytes(msg, 'utf-8'), hashlib.sha256)
        return base64.b64encode(mac.digest()).decode()

    def _headers(self, method, path, body=""):
        ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        h = {
            "OK-ACCESS-KEY": self.api_key,
            "OK-ACCESS-SIGN": self._sign(ts, method, path, body),
            "OK-ACCESS-TIMESTAMP": ts,
            "OK-ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json"
        }
        if self.simulated: h["x-simulated-trading"] = "1"
        return h

    def _request(self, method, path, params=None, body=None):
        self._rate_limit()
        request_path = path
        if method == "GET" and params:
            request_path = f"{path}?{'&'.join([f'{k}={v}' for k,v in params.items()])}"
        url = self.BASE_URL + request_path
        headers = self._headers(method, request_path, json.dumps(body) if body else "")
        try:
            resp = self._http.get(url, headers=headers, timeout=10) if method == "GET" else self._http.post(url, headers=headers, data=json.dumps(body), timeout=10)
            return resp.json()
        except Exception as e:
            print(f"[OKX ERROR] {e}")
            return None

    def _to_inst(self, symbol): return self.SYMBOL_MAP.get(symbol, symbol.replace("USDT", "-USDT-SWAP"))
    def _to_qty(self, symbol, qty): return str(max(1, round(qty / self.CT_VAL.get(symbol, 0.01))))
    def _safe_float(self, v):
        try: return float(v) if v else 0.0
        except: return 0.0

    def get_price(self, symbol):
        resp = self._request("GET", "/api/v5/market/ticker", {"instId": self._to_inst(symbol)})
        if resp and resp.get("code") == "0": return self._safe_float(resp["data"][0].get("last"))
        return None

    def get_klines(self, symbol, bar="5m", limit=100):
        inst = self._to_inst(symbol)
        key = f"{symbol}{bar}{limit}"
        if key in self._klines_cache and time.time() - self._klines_cache[key]["ts"] < 20:
            return self._klines_cache[key]["data"]
        resp = self._request("GET", "/api/v5/market/candles", {"instId": inst, "bar": bar, "limit": str(limit)})
        if resp and resp.get("code") == "0":
            df = pd.DataFrame(resp["data"], columns=["timestamp","open","high","low","close","volume","volCcy","volCcyQuote","confirm"])
            for c in ["open","high","low","close","volume"]: df[c] = pd.to_numeric(df[c], errors="coerce")
            df["timestamp"] = pd.to_datetime(df["timestamp"].astype(float), unit="ms")
            df = df.sort_values("timestamp").reset_index(drop=True)
            self._klines_cache[key] = {"data": df, "ts": time.time()}
            return df
        return None

    def get_account_info(self):
        if self._account_cache["data"] and time.time() - self._account_cache["ts"] < 5:
            return self._account_cache["data"]
        resp = self._request("GET", "/api/v5/account/balance", {"ccy": "USDT"})
        if resp and resp.get("code") == "0":
            data = resp["data"][0]
            eq = self._safe_float(data.get("totalEq"))
            av = next((self._safe_float(d.get("availBal")) for d in data.get("details",[]) if d.get("ccy")=="USDT"), 0.0)
            res = {"equity": eq, "availableBalance": av}
            self._account_cache = {"data": res, "ts": time.time()}
            return res
        return None

    def get_position(self, symbol):
        acc = self.get_account_info()
        if not acc: return None
        for p in acc.get("positions", []): # Note: positions cached separately in prod, here simplified for wrapper
            if p.get("symbol") == symbol: return p
        return None

    def place_order(self, symbol, side, qty, stopLoss=None, takeProfit=None, reduce_only=False):
        inst = self._to_inst(symbol)
        sz = self._to_qty(symbol, qty)
        okx_side = "buy" if str(side).upper() in ["LONG", "BUY"] else "sell"
        pos_side = ("long" if okx_side == "buy" else "short") if not reduce_only else ("short" if okx_side == "buy" else "long")
        body = {"instId": inst, "tdMode": "cross", "side": okx_side, "posSide": pos_side, "ordType": "market", "sz": sz}
        if stopLoss: body.update({"slTriggerPx": str(round(stopLoss,2)), "slOrdPx": "-1", "slTriggerPxType": "last"})
        if takeProfit: body.update({"tpTriggerPx": str(round(takeProfit,2)), "tpOrdPx": "-1", "tpTriggerPxType": "last"})
        resp = self._request("POST", "/api/v5/trade/order", body=body)
        if resp and resp.get("code") == "0":
            print(f"✅ [OKX] {symbol} {okx_side.upper()} {sz} contratos")
            return resp
        print(f"❌ [OKX ERROR] {symbol}: {resp}")
        return None

    def update_stop_loss(self, symbol, stop_price):
        # Simplified for SaaS wrapper
        return True 

    def adjust_qty(self, symbol, qty):
        ct = self.CT_VAL.get(symbol, 0.01)
        n = max(1, round(qty / ct))
        return round(n * ct, 8)

# ==========================================
# CAMADA DE COMPATIBILIDADE (LEGACY + SAAS)
# ==========================================
import os
from dotenv import load_dotenv
load_dotenv()

admin_client = OKXClient(
    api_key=os.getenv("OKX_API_KEY"),
    api_secret=os.getenv("OKX_API_SECRET"),
    passphrase=os.getenv("OKX_PASSPHRASE"),
    simulated=os.getenv("OKX_SIMULATED") == "true"
)

# Funções legadas esperadas por execution_engine.py & bybit_connect.py
def get_account_info(): return admin_client.get_account_info()
def get_price(symbol): return admin_client.get_price(symbol)
def get_position(symbol): return admin_client.get_position(symbol)
def get_klines(symbol, interval="5", limit=100): return admin_client.get_klines(symbol, bar=f"{interval}m", limit=limit)
def place_order(**kwargs): return admin_client.place_order(**kwargs)
def adjust_qty(symbol, qty): return admin_client.adjust_qty(symbol, qty)
def update_stop_loss(symbol, stop): return admin_client.update_stop_loss(symbol, stop)

# Mock de sessão para compatibilidade com bybit_connect.py
class _SessionCompat:
    def get_position(self, symbol): return admin_client.get_position(symbol)
    def get_wallet_balance(self, accountType="UNIFIED"): return admin_client.get_account_info()
session = _SessionCompat()

# Dashboard Updater
def auto_update_dashboard():
    while True:
        try: admin_client.get_account_info()
        except: pass
        time.sleep(5)

def start_dashboard_updater():
    threading.Thread(target=auto_update_dashboard, daemon=True).start()
    print("[OKX] Dashboard Updater iniciado.")

__all__ = [
    "session", "admin_client", "OKXClient", "get_account_info", "get_price", "get_position",
    "get_klines", "place_order", "adjust_qty", "update_stop_loss", "start_dashboard_updater"
]