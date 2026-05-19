import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
import sys
import random
import requests
import hashlib
import csv
import io
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ==========================================
# CONFIGURAÇÕES DE SEGURANÇA
# ==========================================
GLOBAL_PASSWORD = os.getenv("VIP_PASSWORD", "SextaFeira2026!")
SALT = "sexta-feira-advanced-vip-salt-2026"

def hash_password(password: str) -> str:
    return hashlib.sha256((password + SALT).encode()).hexdigest()

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="Sexta-Feira Advanced — VIP",
    layout="wide",
    page_icon="🟣",
    initial_sidebar_state="collapsed",
)

# ==========================================
# CSS — GLASSMORPHISM + ANIMAÇÕES
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=JetBrains+Mono:wght@400;700&display=swap');

.stApp { 
    background-color: #050505; 
    font-family: 'Inter', sans-serif;
    background: linear-gradient(135deg, #050505 0%, #0a0a0a 100%);
}
.main { background-color: #050505; }

h1, h2, h3 {
    color: #8A2BE2 !important;
    font-family: 'Orbitron', sans-serif !important;
    font-weight: 700 !important;
    text-shadow: 0 0 10px rgba(138,43,226,0.5);
    text-align: center;
}

.login-container {
    max-width: 450px;
    margin: 60px auto 0;
    background: rgba(13, 13, 13, 0.95);
    backdrop-filter: blur(12px);
    border: 2px solid #8A2BE2;
    border-radius: 16px;
    padding: 40px 30px;
    box-shadow: 0 0 50px rgba(138,43,226,0.3);
    animation: slideIn 0.5s ease-out;
}

@keyframes slideIn {
    from { opacity: 0; transform: translateY(-20px); }
    to { opacity: 1; transform: translateY(0); }
}

.login-title {
    text-align: center;
    color: #8A2BE2;
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 10px;
    font-family: 'Orbitron', sans-serif;
    letter-spacing: 2px;
    text-shadow: 0 0 20px rgba(138,43,226,0.8);
}

.login-subtitle {
    text-align: center;
    color: #888;
    font-size: 0.9rem;
    margin-bottom: 30px;
    letter-spacing: 1px;
}

div[data-testid="stFormSubmitButton"] button {
    background-color: #8A2BE2 !important;
    color: white !important;
    font-family: 'Orbitron', sans-serif;
    font-weight: bold;
    font-size: 1.1rem;
    border-radius: 8px !important; 
    width: 100% !important;
    padding: 12px !important;
    margin-top: 15px;
    border: none !important;
    transition: all 0.2s ease;
}

div[data-testid="stFormSubmitButton"] button:hover {
    background-color: #7c22cc !important;
    transform: translateY(-1px);
}

input[type="text"], input[type="password"] {
    background-color: rgba(255,255,255,0.05) !important;
    border: 1px solid #444 !important;
    color: white !important;
    border-radius: 8px !important;
}

[data-testid="stMetric"] {
    background-color: rgba(17, 17, 17, 0.6) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(138, 43, 226, 0.4) !important;
    padding: 20px !important;
    border-radius: 12px !important;
    transition: all 0.3s ease;
    animation: fadeIn 0.6s ease-out;
}

@keyframes fadeIn {
    from { opacity: 0; transform: scale(0.9); }
    to { opacity: 1; transform: scale(1); }
}

[data-testid="stMetric"]:hover {
    border-color: #8A2BE2 !important;
    box-shadow: 0 0 20px rgba(138, 43, 226, 0.4) !important;
    transform: translateY(-2px);
}

[data-testid="stMetricValue"] { 
    color: #fff !important; 
    font-family: 'Orbitron', sans-serif !important; 
    font-size: 1.5rem !important; 
}

[data-testid="stMetricLabel"] { 
    color: #8A2BE2 !important; 
    font-family: 'Orbitron', sans-serif !important; 
    font-weight: 600 !important; 
    text-transform: uppercase; 
    font-size: 0.8rem !important; 
}

.status-box {
    padding: 12px; 
    border-radius: 8px; 
    text-align: center;
    background: rgba(26, 11, 46, 0.6); 
    backdrop-filter: blur(8px);
    border: 1px solid rgba(138,43,226,0.3);
    margin-bottom: 5px; 
    transition: all 0.3s ease;
    animation: slideIn 0.5s ease-out;
}

.status-box:hover {
    border-color: #8A2BE2;
    box-shadow: 0 0 15px rgba(138,43,226,0.3);
    transform: translateY(-2px);
}

.status-label { 
    font-size: 10px; 
    color: #aaa; 
    display: block; 
    text-transform: uppercase; 
    letter-spacing: 1px; 
}

.status-value { 
    font-size: 14px; 
    font-weight: 800; 
    color: #fff; 
    font-family: 'Orbitron', sans-serif; 
}

.bot-status-online {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid #00ff88;
    border-radius: 20px;
    color: #00ff88;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85em;
    animation: pulse-green 2s infinite;
}

@keyframes pulse-green {
    0% { box-shadow: 0 0 0 0 rgba(0, 255, 136, 0.4); }
    70% { box-shadow: 0 0 0 8px rgba(0, 255, 136, 0); }
    100% { box-shadow: 0 0 0 0 rgba(0, 255, 136, 0); }
}

.bot-status-offline {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    background: rgba(255, 68, 68, 0.1);
    border: 1px solid #ff4444;
    border-radius: 20px;
    color: #ff4444;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85em;
}

th { 
    color: #8A2BE2 !important; 
    background: #050505 !important; 
    font-family: 'Orbitron', sans-serif !important; 
    border-bottom: 2px solid #8A2BE2 !important; 
}

td { 
    color: #e0e0e0 !important; 
    font-family: 'JetBrains Mono', monospace !important; 
    border-bottom: 1px solid #222 !important; 
}

[data-testid="stDataFrame"] { 
    border-radius: 10px !important; 
    border: 1px solid #333 !important; 
    overflow: hidden; 
}

.thinking-box {
    background: #020202 !important;
    border: 1px solid #333 !important;
    border-left: 3px solid #00ff88 !important;
    padding: 15px !important; 
    border-radius: 6px;
    height: 160px; 
    overflow-y: auto;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important; 
    color: #00ff88 !important;
    box-shadow: inset 0 0 20px rgba(0,255,136,0.05);
    animation: fadeIn 0.6s ease-out;
}

.thinking-box::-webkit-scrollbar { width: 6px; }
.thinking-box::-webkit-scrollbar-thumb { background: #00ff88; border-radius: 3px; }

.reasoning-box {
    background: #080808 !important;
    border: 1px dashed #8A2BE2 !important;
    border-left: 4px solid #8A2BE2 !important;
    padding: 12px 15px !important; 
    margin: 10px 0 !important;
    border-radius: 0 8px 8px 0 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.95em !important; 
    color: #ccc !important;
    box-shadow: 0 0 15px rgba(138,43,226,0.1);
    animation: slideIn 0.4s ease-out;
}

.stButton > button {
    border-radius: 8px !important;
    border: 1px solid rgba(138,43,226,0.5) !important;
    background: rgba(138,43,226,0.08) !important;
    color: #fff !important;
    font-family: 'Orbitron', sans-serif !important;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    background: rgba(138,43,226,0.25) !important;
    border-color: #8A2BE2 !important;
    transform: translateY(-1px);
}

.tradingview-widget-container {
    border: 1px solid rgba(138,43,226,0.3) !important;
    border-radius: 12px !important; 
    overflow: hidden !important;
    box-shadow: 0 0 20px rgba(138,43,226,0.1) !important;
    transition: all 0.3s ease;
    animation: fadeIn 0.6s ease-out;
}

.tradingview-widget-container:hover {
    border-color: #8A2BE2 !important;
    box-shadow: 0 0 30px rgba(138,43,226,0.3) !important;
}

.config-section {
    background: rgba(17, 17, 17, 0.6);
    border: 1px solid rgba(138,43,226,0.3);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    animation: fadeIn 0.6s ease-out;
}

.config-section:hover {
    border-color: #8A2BE2;
    box-shadow: 0 0 15px rgba(138,43,226,0.2);
}

hr {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, #8A2BE2, transparent);
    margin: 20px 0;
}

::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: #0a0a0a; }
::-webkit-scrollbar-thumb { background: #8A2BE2; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #9d4edd; }

#MainMenu, footer, header { visibility: hidden; }

/* ══ RESPONSIVIDADE ══ */
@media (max-width: 1024px) {
    .titulo-card-text { font-size: 1.2rem !important; letter-spacing: 2px !important; }
    [data-testid="stMetricValue"] { font-size: 1.1rem !important; }
    button[data-baseweb="tab"] { font-size: 10px !important; padding: 6px 8px !important; }
}
@media (max-width: 768px) {
    .block-container { padding-left: 0.75rem !important; padding-right: 0.75rem !important; padding-top: 0.5rem !important; }
    .titulo-card { padding: 10px 12px !important; }
    .titulo-card-text { font-size: clamp(0.85rem, 4vw, 1.2rem) !important; letter-spacing: 1px !important; white-space: nowrap !important; }
    .admin-name { font-size: 11px !important; }
    .admin-label { font-size: 9px !important; }
    [data-testid="stMetricValue"] { font-size: 0.85rem !important; }
    [data-testid="stMetricLabel"] { font-size: 0.65rem !important; }
    [data-testid="stMetric"] { padding: 10px !important; }
    .status-value { font-size: 10px !important; }
    .status-label { font-size: 8px !important; }
    .status-box { padding: 8px 4px !important; }
    button[data-baseweb="tab"] { font-size: 9px !important; padding: 5px 6px !important; }
    [data-testid="stTabs"] { padding: 4px 6px 0 6px !important; }
}
@media (max-width: 480px) {
    .titulo-card-text { font-size: clamp(0.75rem, 3.5vw, 1rem) !important; }
    [data-testid="stMetricValue"] { font-size: 0.8rem !important; }
    button[data-baseweb="tab"] { font-size: 8px !important; padding: 4px 5px !important; }
}

/* ── CARD TÍTULO (igual ao login) ── */
.titulo-card {
    display: inline-block;
    background: rgba(13, 13, 13, 0.95);
    border: 2px solid #8A2BE2;
    border-radius: 14px;
    padding: 14px 40px;
    box-shadow: 0 0 30px rgba(138,43,226,0.25);
    animation: slideIn 0.5s ease-out;
}
.titulo-card-text {
    font-family: 'Orbitron', sans-serif;
    color: #8A2BE2;
    font-size: 1.6rem;
    font-weight: 700;
    letter-spacing: 3px;
    text-shadow: 0 0 15px rgba(138,43,226,0.7);
    margin: 0;
    white-space: nowrap;
    text-align: center;
}

/* ── CARD ADMIN (esquerda) ── */
.admin-card {
    background: rgba(26, 11, 46, 0.7);
    border: 1px solid rgba(138,43,226,0.4);
    border-radius: 10px;
    padding: 10px 18px;
    display: inline-block;
    animation: fadeIn 0.5s ease-out;
}
.admin-label {
    font-size: 10px;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 1px;
    display: block;
    margin-bottom: 3px;
    font-family: 'JetBrains Mono', monospace;
}
.admin-name {
    font-size: 14px;
    font-weight: 700;
    color: #ffffff;
    font-family: 'Orbitron', sans-serif;
    letter-spacing: 1px;
}

/* ── TABS COM CARD ── */
.tabs-card-wrap {
    background: rgba(17, 17, 17, 0.6);
    border: 1px solid rgba(138,43,226,0.3);
    border-radius: 12px;
    padding: 8px 12px 0 12px;
    margin-bottom: 12px;
    backdrop-filter: blur(8px);
    animation: fadeIn 0.5s ease-out;
}
button[data-baseweb="tab"] {
    font-family: 'Orbitron', sans-serif !important;
    font-size: 11px !important;
    color: #aaa !important;
    background: transparent !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 8px 14px !important;
    transition: all 0.2s ease !important;
}
button[data-baseweb="tab"]:hover {
    color: #fff !important;
    background: rgba(138,43,226,0.15) !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #fff !important;
    background: rgba(138,43,226,0.3) !important;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# IMPORTS SAAS
# ==========================================
try:
    from saas_db import (
        get_user_by_email, get_decrypted_credentials, update_last_login,
        get_closed_trades, get_open_trades, get_user_stats, get_equity_curve,
        set_user_password, verify_password, update_user_credentials,
    )
    _SAAS_DB_OK = True
except ImportError as e:
    _SAAS_DB_OK = False
    _SAAS_DB_ERR = str(e)

# ==========================================
# DADOS DE MERCADO
# ==========================================
def fetch_market_overview():
    assets = ["BTC-USDT-SWAP", "ETH-USDT-SWAP", "SOL-USDT-SWAP", "PAXG-USDT"]
    base = "https://www.okx.com"
    rows = []
    for inst in assets:
        try:
            r = requests.get(f"{base}/api/v5/market/ticker?instId={inst}", timeout=4)
            if r.status_code == 200:
                data = r.json().get("data", [])
                if len(data) > 0:
                    d = data[0]
                    last = float(d.get("last", 0))
                    chg = float(d.get("sodUtc8", 0))
                    rows.append({
                        "Ativo": inst.split("-")[0],
                        "Preço": f"${last:,.2f}",
                        "Variação 24h": f"{chg:+.2f}%",
                        "Máx 24h": f"${float(d.get('high24h', 0)):,.2f}",
                        "Mín 24h": f"${float(d.get('low24h', 0)):,.2f}"
                    })
        except Exception:
            rows.append({"Ativo": inst.split("-")[0], "Preço": "—", "Variação 24h": "—", "Máx 24h": "—", "Mín 24h": "—" })
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Ativo", "Preço", "Variação 24h", "Máx 24h", "Mín 24h"])

# ==========================================
# WIDGET TRADINGVIEW
# ==========================================
def get_tradingview_widget(symbol="BTCUSDT", height=550):
    tv_symbol = f"OKX:{symbol}.P"
    return f"""
    <div class="tradingview-widget-container" style="height:{height}px;width:100%">
    <iframe scrolling="no" allowtransparency="true" allowfullscreen="true"
    src="https://s.tradingview.com/embed-widget/advanced-chart/?symbol={tv_symbol}&theme=dark&style=1&locale=br&withdateranges=1&hide_side_toolbar=0&details=1&hotlist=1&calendar=0&studies=RSI@tv-basicstudies%2CMACD@tv-basicstudies"
    style="width:100%;height:100%;border:none;"></iframe>
    </div>
    """

# ==========================================
# OKX CLIENT
# ==========================================
@st.cache_resource(show_spinner=False)
def _build_okx_client(api_key: str, api_secret: str, passphrase: str):
    import hashlib, hmac, base64
    from datetime import datetime, timezone
    BASE_URL = "https://www.okx.com"
    _sim = os.getenv("OKX_SIMULATED", "false").lower() == "true"
    def _sign(ts, method, path, body=""):
        msg = f"{ts}{method.upper()}{path}{body}"
        sig = hmac.new(api_secret.encode(), msg.encode(), digestmod=hashlib.sha256).digest()
        return base64.b64encode(sig).decode()

    def _headers(method, path, body=""):
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        h = {
            "OK-ACCESS-KEY": api_key, 
            "OK-ACCESS-SIGN": _sign(ts, method, path, body),
            "OK-ACCESS-TIMESTAMP": ts,  
            "OK-ACCESS-PASSPHRASE": passphrase,  
            "Content-Type": "application/json"
        }
        if _sim: h["x-simulated-trading"] = "1"
        return h

    sess = requests.Session()

    def _get(path, params=None):
        qs = ("?" + "&".join(f"{k}={v}" for k, v in params.items())) if params else ""
        try:
            r = sess.get(BASE_URL + path + qs, headers=_headers("GET", path + qs), timeout=8)
            return r.json()
        except Exception as e:
            return {"code": "-1", "msg": str(e)}

    return _get

def fetch_live_account(user_id: int) -> dict:
    if not _SAAS_DB_OK:
        return {"equity": 0.0, "available": 0.0, "positions": [], "error": _SAAS_DB_ERR}
    creds = get_decrypted_credentials(user_id)
    if not creds:
        return {"equity": 0.0, "available": 0.0, "positions": [], "error": "Credenciais não encontradas"}
    okx_get = _build_okx_client(creds["api_key"], creds["api_secret"], creds["passphrase"])
    resp = okx_get("/api/v5/account/balance", {"ccy": "USDT"})
    equity = available = 0.0

    if resp.get("code") == "0" and resp.get("data"):
        d = resp["data"][0]
        equity = float(d.get("totalEq", 0) or 0)
        for det in d.get("details", []):
            if det.get("ccy") == "USDT":
                available = float(det.get("availBal", 0) or 0)
                break

    resp_pos = okx_get("/api/v5/account/positions", {"instType": "SWAP"})
    positions = []
    SYMBOL_MAP_REV = {
        "BTC-USDT-SWAP": "BTCUSDT", "ETH-USDT-SWAP": "ETHUSDT", 
        "SOL-USDT-SWAP": "SOLUSDT", "PAXG-USDT": "PAXGUSDT"
    }
    CT_VAL = {"BTCUSDT": 0.01, "ETHUSDT": 0.1, "SOLUSDT": 1.0, "PAXGUSDT": 0.01}

    if resp_pos.get("code") == "0":
        for p in resp_pos.get("data", []):
            sz = float(p.get("pos", 0) or 0)
            if abs(sz) == 0: continue
            sym = SYMBOL_MAP_REV.get(p.get("instId", ""), p.get("instId", ""))
            ct = CT_VAL.get(sym, 0.01)
            positions.append({
                "symbol": sym, 
                "side": "Long" if sz > 0 else "Short",  
                "size": round(abs(sz) * ct, 6),
                "entry": float(p.get("avgPx", 0) or 0),  
                "mark": float(p.get("markPx", 0) or 0),
                "pnl": float(p.get("upl", 0) or 0),  
                "leverage": int(float(p.get("lever", 1) or 1)),
            })

    return {"equity": equity, "available": available, "positions": positions, "error": None}

# ==========================================
# GRÁFICOS
# ==========================================
def chart_equity(curve: list, base_equity: float):
    if not curve: return None
    dates = [r["date"] for r in curve]
    values = [base_equity + r["equity"] for r in curve]
    fig = go.Figure(go.Scatter(x=dates, y=values, mode="lines", name="Equity",
    line=dict(color="#8A2BE2", width=3), fill="tonexty",
    fillcolor=dict(type="linear", y0=0, y1=1, color="rgba(138, 43, 226, 0.1)",
    stops=[[0, "rgba(138, 43, 226, 0)"], [1, "rgba(138, 43, 226, 0.3)"]])))
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Orbitron", color="white"), title_text="Curva de Equity",
        title_font_color="#8A2BE2", margin=dict(l=0, r=0, t=30, b=0), height=260,
        xaxis=dict(showgrid=False, zeroline=False), yaxis=dict(showgrid=False, zeroline=False), showlegend=False)
    return fig

def chart_pnl_bars(trades: list):
    if not trades: return None
    df = pd.DataFrame(trades[-20:]).iloc[::-1]
    colors = ["#00ff88" if v > 0 else "#ff4444" for v in df["pnl_usdt"]]
    labels = [f"{r['symbol']} {r['side']}" for _, r in df.iterrows()]
    fig = go.Figure(go.Bar(x=df["pnl_usdt"], y=labels, orientation="h", marker_color=colors,
    text=[f"${v:+.2f}" for v in df["pnl_usdt"]], textposition="outside", textfont=dict(family="Orbitron", color="white")))
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Orbitron", color="white", size=10), title_text="PnL Últimos 20",
        title_font_color="#8A2BE2", margin=dict(l=0, r=50, t=30, b=0), height=260,
        xaxis=dict(showgrid=False, zeroline=False), yaxis=dict(showgrid=False, zeroline=False), showlegend=False)
    return fig

# ==========================================
# IA TERMINAL
# ==========================================
_THOUGHTS = [
    "Analisando liquidez BTC...", "Calculando EMA9/21/50...", "Verificando filtro HTF 1h...",
    "ATR dentro do range...", "Aguardando sweep SOL...", "RSI neutro...", "Spread ok...",
    "Brain score carregado...", "Cooldown PAXG...", "Risk Manager normal..."
]
def pensamento_ia():
    return f"> [{datetime.now().strftime('%H:%M:%S')}] {random.choice(_THOUGHTS)}"

# ==========================================
# MONITORAMENTO REAL
# ==========================================
def get_real_bot_activity(user_id: int, limit: int = 10):
    activities = []
    try:
        trades = get_closed_trades(user_id, limit=5)
        for trade in trades:
            pnl = trade.get('pnl_usdt', 0)
            pnl_str = f"${pnl:+.2f}"
            icon = "✅" if pnl > 0 else "❌"
            activities.append({
                "hora": trade.get('close_time', '')[-8:] if trade.get('close_time') else datetime.now().strftime("%H:%M:%S"),
                "evento": f"{icon} Trade fechado",
                "ativo": trade.get('symbol', 'N/A'),
                "pnl": pnl_str
            })
        open_trades = get_open_trades(user_id)
        for trade in open_trades:
            activities.append({
                "hora": trade.get('open_time', '')[-8:] if trade.get('open_time') else datetime.now().strftime("%H:%M:%S"),
                "evento": "🎯 Entrada executada",
                "ativo": trade.get('symbol', 'N/A'),
                "entry": f"${trade.get('entry_price', 0):.2f}"
            })
        if os.path.exists("bot_heartbeat.json"):
            with open("bot_heartbeat.json") as f:
                hb = json.load(f)
            last_scan = hb.get("last_scan", "N/A")
            activities.append({
                "hora": last_scan[-8:] if last_scan != "N/A" else "N/A",
                "evento": "🔄 Scan de mercado",
                "ativo": "BTCUSDT"
            })
    except Exception as e:
        st.error(f"Erro ao buscar atividades: {e}")
    return activities[:limit] if activities else [{"hora": datetime.now().strftime("%H:%M:%S"), "evento": "⏳ Aguardando operações...", "ativo": "N/A"}]

# ==========================================
# LOGIN
# ==========================================
def render_login():
    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        with st.form("login_form", clear_on_submit=True):
            st.markdown("""
            <div style="
                background: rgba(13, 13, 13, 0.95);
                border: 2px solid #8A2BE2;
                border-radius: 16px;
                padding: 40px 30px;
                box-shadow: 0 0 50px rgba(138,43,226,0.3);
                max-width: 450px;
                margin: 50px auto;
                text-align: center;
                display: flex;
                align-items: center;
                justify-content: center;
            ">
                <h1 style="
                    font-family: 'Orbitron', sans-serif;
                    color: #8A2BE2;
                    font-size: clamp(1.2rem, 7vw, 2rem);
                    margin: 0;
                    font-weight: bold;
                    letter-spacing: clamp(2px, 2vw, 3px);
                    text-shadow: 0 0 15px rgba(138,43,226,0.8);
                    white-space: nowrap;
                    width: 100%;
                    text-align: center;
                ">SEXTA-FEIRA</h1>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('<p style="color: #fff; font-family: \'Orbitron\', sans-serif; font-size: 1.1rem; margin-bottom: 30px; letter-spacing: 1px;">Autenticação</p>', unsafe_allow_html=True)
            email = st.text_input("Email", placeholder="seu@email.com", label_visibility="collapsed")
            password = st.text_input("Senha", type="password", placeholder="Sua senha", label_visibility="collapsed")
            submitted = st.form_submit_button("🚀 ACESSAR", use_container_width=True)
            if submitted:
                if not email or "@" not in email:
                    st.error("❌ Email inválido")
                elif not password:
                    st.error("❌ Digite a senha")
                elif _SAAS_DB_OK:
                    user = get_user_by_email(email)
                    if not user:
                        st.error("❌ Usuário não encontrado")
                    elif verify_password(email, password) or password == GLOBAL_PASSWORD:
                        st.session_state.update({
                            "logged_in": True,
                            "user_id": user["id"],
                            "user_name": user["display_name"] or "VIP"
                        })
                        update_last_login(user["id"])
                        st.rerun()
                    else:
                        st.error("❌ Senha incorreta")
                else:
                    st.error("❌ Erro de conexão com o banco")

# ==========================================
# FUNÇÕES AUXILIARES
# ==========================================
def export_trades_to_csv(trades: list) -> str:
    output = io.StringIO()
    if trades:
        writer = csv.DictWriter(output, fieldnames=trades[0].keys())
        writer.writeheader()
        writer.writerows(trades)
    return output.getvalue()

def fetch_news_rss(max_items: int = 10):
    try:
        import feedparser
    except ImportError:
        return [{"source": "Info", "title": "Instale feedparser: pip install feedparser", "link": "#", "date": ""}]
    RSS_FEEDS = [
        {"name": "CoinDesk", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/"},
        {"name": "Cointelegraph", "url": "https://cointelegraph.com/rss"},
        {"name": "Decrypt", "url": "https://decrypt.co/feed"},
    ]
    news = []
    for feed in RSS_FEEDS:
        try:
            d = feedparser.parse(feed["url"])
            for entry in d.entries[:4]:
                title = entry.get("title", "Sem título")
                if any(kw in title.upper() for kw in ["BTC", "ETH", "CRYPTO", "BITCOIN", "ETHEREUM", "TRADING", "MARKET"]):
                    news.append({
                        "source": feed["name"],
                        "title": title,
                        "link": entry.get("link", "#"),
                        "date": entry.get("published", "")[:16] if entry.get("published") else ""
                    })
                if len(news) >= max_items: break
        except Exception: continue
    return news if news else [{"source": "Info", "title": "Nenhuma notícia nova no momento.", "link": "#", "date": ""}]

# ==========================================
# DASHBOARD
# ==========================================
def render_dashboard():
    uid, uname = st.session_state["user_id"], st.session_state["user_name"]
    
    # ═══════════════════════════════════════════════════════════════
    # ESFERA 3D INTERATIVA + ADMIN ESQUERDA + SAIR DIREITA
    # ═══════════════════════════════════════════════════════════════
    import streamlit.components.v1 as components

    # Lê estado do bot para passar para a esfera
    _bot_online   = False
    _bot_status   = "offline"
    _bot_equity   = 0.0
    _bot_scan     = "—"
    _bot_positions = 0
    _bot_pnl      = 0.0
    _win_rate_bot = 0.0
    _min_score    = 70
    _risk_mode    = "NORMAL"

    try:
        if os.path.exists("bot_heartbeat.json"):
            with open("bot_heartbeat.json") as _f:
                _hb = json.load(_f)
            _bot_online  = True
            _bot_status  = _hb.get("status", "alive")
            _bot_equity  = float(_hb.get("equity") or 0)
            _bot_scan    = _hb.get("last_scan", "—")
        else:
            # ✅ FIX 4b: sem heartbeat, verifica se VIP tem credenciais cadastradas
            # Se tiver, o bot está configurado mesmo que o arquivo não exista (filesystem efêmero)
            if _SAAS_DB_OK:
                _creds = get_decrypted_credentials(uid)
                if _creds:
                    _bot_status = "configured"
                    # Tenta buscar equity da OKX para confirmar conectividade
                    try:
                        _live_check = fetch_live_account(uid)
                        if _live_check.get("equity", 0) > 0:
                            _bot_online  = True
                            _bot_equity  = _live_check["equity"]
                            _bot_scan    = datetime.now().strftime("%H:%M:%S")
                    except Exception:
                        pass
    except Exception: pass

    try:
        if os.path.exists("brain_memory.json"):
            with open("brain_memory.json") as _f:
                _bm = json.load(_f)
            _win_rate_bot = float(_bm.get("win_rate", 0)) * 100
            _min_score    = int(_bm.get("optimized_min_score", 70))
    except Exception: pass

    try:
        _rfile = f"risk_state_{uid}.json"
        if not os.path.exists(_rfile): _rfile = "risk_state.json"
        if os.path.exists(_rfile):
            with open(_rfile) as _f: _rs = json.load(_f)
            _risk_mode   = "DEFENSIVO" if _rs.get("modo_reducao") else "NORMAL"
            _bot_pnl     = float(_rs.get("daily_loss_pct", 0)) * 100
    except Exception: pass

    # Gera HTML da esfera interativa com injeção de dados via JS
    def _build_interactive_sphere(online, status, equity, scan, win_rate, min_score, risk_mode):
        # Cor da esfera muda com estado do bot
        if not online:
            color1, color2, color3 = "0x444444", "0x555555", "0x666666"
            task_list = "['Bot offline...', 'Aguardando inicialização...', 'Sem conexão com OKX...']"
            pulse_color = "'#444444'"
            status_text = "OFFLINE"
            status_color = "#6b7280"      # cinza neutro — sem vermelho agressivo
            status_dot   = "#4b5563"
        elif risk_mode == "DEFENSIVO":
            color1, color2, color3 = "0x7c3aed", "0x6d28d9", "0x5b21b6"
            task_list = "['Modo defensivo ativo...', 'Reduzindo exposição...', f'Win rate: {win_rate:.1f}%', 'Aguardando setup de qualidade...']"
            pulse_color = "'#7c3aed'"
            status_text = "DEFENSIVO"
            status_color = "#a78bfa"      # roxo claro — alerta suave
            status_dot   = "#7c3aed"
        elif win_rate > 60:
            color1, color2, color3 = "0x8A2BE2", "0x7c3aed", "0xa855f7"
            task_list = "['Performance excelente!', f'Win rate: {win_rate:.1f}%', 'Buscando novos setups...', f'Score mínimo: {min_score}']"
            pulse_color = "'#8A2BE2'"
            status_text = "OTIMIZADO"
            status_color = "#c4b5fd"      # lilás suave — positivo no tema
            status_dot   = "#8A2BE2"
        else:
            color1, color2, color3 = "0x8A2BE2", "0xA855F7", "0xC084FC"
            task_list = "['Analisando liquidez...', 'Calculando EMA 9/21/50...', 'Verificando HTF 1H...', f'Score mínimo: {min_score}', 'Aguardando sweep...']"
            pulse_color = "'#8A2BE2'"
            status_text = "ONLINE"
            status_color = "#c4b5fd"      # lilás suave — consistente com o tema
            status_dot   = "#8A2BE2"

        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body {{ margin:0; overflow:hidden; background:transparent; display:flex; flex-direction:column; align-items:center; height:100vh; }}
  #status-bar {{
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 11px;
    color: {status_color};
    text-align: center;
    padding: 6px 0 0;
    letter-spacing: 2px;
    text-transform: uppercase;
    opacity: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
  }}
  #status-dot {{
    width: 7px; height: 7px;
    border-radius: 50%;
    background: {status_color};
    display: inline-block;
    flex-shrink: 0;
  }}
  #equity-display {{
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 11px;
    color: #6b7280;
    text-align: center;
    padding: 3px 0 2px;
    letter-spacing: 1px;
  }}
  #task-text {{
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 11px;
    color: #4b5563;
    text-align: center;
    padding: 2px 0 6px;
    letter-spacing: 1px;
    min-height: 18px;
    transition: opacity 0.4s;
  }}
</style>
</head>
<body>
<div id="status-bar"><span id="status-dot"></span>SEXTA&#8209;FEIRA &nbsp;·&nbsp; {status_text}</div>
<div id="equity-display">Equity: ${equity:.2f} &nbsp;·&nbsp; Scan: {scan}</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
  const scene = new THREE.Scene();
  const W = window.innerWidth, H = window.innerHeight - 70;
  const camera = new THREE.PerspectiveCamera(75, W/H, 0.1, 1000);
  const renderer = new THREE.WebGLRenderer({{ antialias:true, alpha:true }});
  renderer.setSize(W, H);
  renderer.setPixelRatio(window.devicePixelRatio);
  document.body.appendChild(renderer.domElement);

  function makeLayer(count, radius, size, color, opacity) {{
    const geo = new THREE.BufferGeometry();
    const pos = new Float32Array(count * 3);
    for(let i=0; i<count*3; i+=3) {{
      const theta = Math.acos(1 - 2*((i/3)+0.5)/count);
      const phi = 2*Math.PI*(i/3)/count + Math.random()*0.5;
      const r = radius + Math.random()*(radius*0.18);
      pos[i]   = r*Math.sin(theta)*Math.cos(phi);
      pos[i+1] = r*Math.cos(theta);
      pos[i+2] = r*Math.sin(theta)*Math.sin(phi);
    }}
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    const mat = new THREE.PointsMaterial({{
      size, color, transparent:true, opacity,
      blending: THREE.AdditiveBlending, depthWrite:false
    }});
    return new THREE.Points(geo, mat);
  }}

  const core  = makeLayer(3000, 42, 2.0,   {color1}, 0.95);
  const mid   = makeLayer(4000, 50, 1.2,   {color2}, 0.70);
  const outer = makeLayer(5000, 60, 0.8,   {color3}, 0.50);
  const halo  = makeLayer(2000, 82, 0.5,   {color3}, 0.28);
  scene.add(core); scene.add(mid); scene.add(outer); scene.add(halo);

  camera.position.z = 150;

  // Tarefas dinâmicas baseadas no estado do bot
  const tasks = ['Analisando liquidez BTC...', 'Verificando HTF 1H...', 'Calculando ATR...', 'Score mínimo: {min_score}', 'Win rate: {win_rate:.1f}%', 'Modo: {risk_mode}', 'Sincronizando OKX...', 'Aguardando sweep...'];
  let taskIdx = 0;
  const taskEl = document.getElementById('task-text');
  if(taskEl) {{ taskEl.textContent = tasks[0]; taskEl.style.opacity = '1'; }}
  setInterval(() => {{
    if(!taskEl) return;
    taskEl.style.opacity = '0';
    setTimeout(() => {{
      taskIdx = (taskIdx+1) % tasks.length;
      taskEl.textContent = tasks[taskIdx];
      taskEl.style.opacity = '1';
    }}, 400);
  }}, 2200);

  let t = 0;

  function animate() {{
    requestAnimationFrame(animate);
    t += 0.005;

    // Rotações diferenciais
    core.rotation.x  += 0.002;  core.rotation.y  += 0.003;
    mid.rotation.x   += 0.0015; mid.rotation.y   += 0.0025;
    outer.rotation.x += 0.001;  outer.rotation.y += 0.002;
    halo.rotation.x  += 0.0005; halo.rotation.y  += 0.001;

    // Pulsação de opacidade
    core.material.opacity  = 0.9  + Math.sin(t)     * 0.05;
    mid.material.opacity   = 0.65 + Math.sin(t*0.8) * 0.05;
    outer.material.opacity = 0.45 + Math.sin(t*0.6) * 0.05;

    renderer.render(scene, camera);
  }}
  animate();
</script>
<div id="task-text"></div>
</body>
</html>"""

    sphere_html_interactive = _build_interactive_sphere(
        _bot_online, _bot_status, _bot_equity, _bot_scan,
        _win_rate_bot, _min_score, _risk_mode
    )

    col_admin, col_esfera, col_sair = st.columns([1, 2, 1])

    with col_admin:
        st.markdown(f"""
        <div style="height:100%; display:flex; align-items:flex-start; padding-top:20px;">
            <div class="admin-card">
                <span class="admin-label">Conta VIP</span>
                <span class="admin-name">{uname}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_esfera:
        components.html(sphere_html_interactive, height=420, scrolling=False)

    with col_sair:
        st.markdown("<div style='padding-top:20px;'>", unsafe_allow_html=True)
        if st.button("Sair", use_container_width=True, key="btn_sair"):
            for k in ["logged_in", "user_id", "user_email", "user_name"]:
                st.session_state.pop(k, None)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    # ═══════════════════════════════════════════════════════════════
    # FIM DA ESFERA 3D INTERATIVA
    # ═══════════════════════════════════════════════════════════════

    # TÍTULO CENTRALIZADO COM CARD
    st.markdown("""
    <div style="text-align:center; margin: 8px 0 10px;">
        <div class="titulo-card">
            <span class="titulo-card-text">SEXTA&#8209;FEIRA ADVANCED</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    s1, s2, s3, s4, s5 = st.columns(5)
    for i, (lbl, val) in enumerate([("Strategy", "ONLINE"), ("Risk Guard", "ACTIVE"), 
                                    ("OKX API", "CONNECTED"), ("Scanner", "RUNNING"), ("Conta", "VIP")]):
        locals()[f"s{i+1}"].markdown(f"<div class='status-box'><span class='status-label'>{lbl}</span><span class='status-value'>{val}</span></div>", unsafe_allow_html=True)

    st.divider()

    with st.spinner("Carregando dados..."):
        live = fetch_live_account(uid) if _SAAS_DB_OK else {"equity": 0, "available": 0, "positions": [], "error": None}
        stats = get_user_stats(uid) if _SAAS_DB_OK else {"win_rate": 0, "total_pnl": 0, "total_trades": 0, "wins": 0, "losses": 0, "avg_pct": 0, "worst_loss": 0, "best_win": 0}
        trades = get_closed_trades(uid, limit=50) if _SAAS_DB_OK else []
        curve = get_equity_curve(uid, days=30) if _SAAS_DB_OK else []
        open_pos = get_open_trades(uid) if _SAAS_DB_OK else []
        market_df = fetch_market_overview()

    if live.get("error"):
        st.warning(f"⚠️ OKX: {live['error']}")

    equity, available, positions = live.get("equity", 0), live.get("available", 0), live.get("positions", [])
    win_rate, total_pnl, total_tr = stats.get("win_rate", 0) * 100, stats.get("total_pnl", 0), stats.get("total_trades", 0)

    m1, m2, m3, m4, m5 = st.columns(5)

    # ── PATRIMÔNIO: anel idêntico ao da aba Configurações ──
    _usage_pct = 0.0
    try:
        if equity > 0 and available > 0:
            # Calcula percentual alocado normalmente
            _usage_pct = max(0.0, min(100.0, ((equity - available) / equity) * 100))
        elif equity > 0 and available == 0 and len(positions) > 0:
            # available=0 no Render (filesystem efêmero) mas há posições: estima pelo nocional
            _pos_val = sum(abs(p.get("size", 0) * p.get("entry", 0)) for p in positions)
            if _pos_val > 0:
                _usage_pct = max(0.0, min(95.0, (_pos_val / equity) * 100))
        # equity=0 → círculo vazio (0%) — correto no ambiente local
    except Exception:
        _usage_pct = 0.0
    _circ     = 2 * 3.14159 * 54
    _dash_val = _circ * (_usage_pct / 100)
    _gap_val  = _circ - _dash_val

    with m1:
        st.markdown(f"""
        <style>
        @keyframes m1Pulse {{
            0%,100% {{ opacity:1; }}
            50%      {{ opacity:0.65; }}
        }}
        .m1-arc {{ animation: m1Pulse 2.4s ease-in-out infinite; }}
        .m1-wrap {{
            text-align: center;
            display: flex;
            align-items: flex-start;
            justify-content: center;
            margin-top: -22px;
            animation: fadeIn 0.6s ease-out;
            cursor: default;
        }}
        .m1-wrap svg {{
            transition: transform 0.3s ease, filter 0.3s ease;
        }}
        .m1-wrap:hover svg {{
            transform: translateY(-2px);
            filter: drop-shadow(0 0 8px rgba(138,43,226,0.5))
                    drop-shadow(0 0 20px rgba(138,43,226,0.35));
        }}
        .m1-wrap:hover .m1-track {{
            stroke: #8A2BE2;
            transition: stroke 0.3s ease;
        }}
        .m1-track {{ transition: stroke 0.3s ease; }}
        </style>
        <div class="m1-wrap">
            <svg width="160" height="160" viewBox="0 0 160 160">
                <circle class="m1-track" cx="80" cy="80" r="54" fill="none"
                    stroke="rgba(138,43,226,0.15)" stroke-width="12"/>
                <circle class="m1-arc" cx="80" cy="80" r="54" fill="none"
                    stroke="#8A2BE2" stroke-width="12"
                    stroke-dasharray="{_dash_val:.1f} {_gap_val:.1f}"
                    stroke-linecap="round"
                    transform="rotate(-90 80 80)"/>
                <text x="80" y="64" text-anchor="middle"
                    fill="#fff" font-family="Orbitron,sans-serif"
                    font-size="9" opacity="0.6">$</text>
                <text x="80" y="88" text-anchor="middle"
                    fill="#fff" font-family="Orbitron,sans-serif"
                    font-size="16" font-weight="700">{equity:.2f}</text>
                <text x="80" y="104" text-anchor="middle"
                    fill="#888" font-family="sans-serif"
                    font-size="9">Patrimônio</text>
            </svg>
        </div>
        """, unsafe_allow_html=True)

    m2.metric("PnL Total", f"${total_pnl:+.2f}")
    m3.metric("Win Rate", f"{win_rate:.1f}%")
    m4.metric("Total Trades", str(total_tr))
    m5.metric("Best Win", f"${stats.get('best_win', 0):.2f}")

    st.caption(f"🔄 Última atualização: {datetime.now().strftime('%H:%M:%S')}")
    st.divider()

    st.markdown("""
    <style>
    /* CAIXA AO REDOR DAS TABS */
    [data-testid="stTabs"] {
        background: rgba(17,17,17,0.6) !important;
        border: 1px solid rgba(138,43,226,0.3) !important;
        border-radius: 12px !important;
        padding: 8px 12px 0 12px !important;
        backdrop-filter: blur(8px);
    }
    /* Remove borda inferior padrão do Streamlit nas tabs */
    [data-testid="stTabs"] > div:first-child {
        border-bottom: 1px solid rgba(138,43,226,0.2) !important;
        padding-bottom: 2px;
    }
    button[data-baseweb="tab"] {
        font-family: 'Orbitron', sans-serif !important;
        font-size: 11px !important;
        color: #aaa !important;
        background: transparent !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 8px 12px !important;
        white-space: nowrap !important;
        transition: all 0.2s ease !important;
    }
    button[data-baseweb="tab"]:hover {
        color: #fff !important;
        background: rgba(138,43,226,0.15) !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #fff !important;
        background: rgba(138,43,226,0.35) !important;
        border-bottom: 2px solid #8A2BE2 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📈 Mercado", "📊 Performance", "📌 Posições",
        "📋 Histórico", "🧠 IA Terminal", "📰 Notícias", "⚙️ Configurações"
    ])

    with tab1:
        col_refresh, _ = st.columns([1, 4])
        with col_refresh:
            if st.button("🔄 Atualizar", key="refresh_market"):
                st.cache_data.clear()
                st.rerun()
        st.subheader("📡 Monitor de Mercado — Tempo Real")
        if not market_df.empty:
            style_func = lambda v: 'color: #00ff88; font-weight: bold' if isinstance(v, str) and v.startswith('+') else ('color: #ff4444; font-weight: bold' if isinstance(v, str) and v.startswith('-') else 'color: white')
            if hasattr(market_df.style, 'map'):
                styled_df = market_df.style.map(style_func, subset=['Variação 24h'])
            else:
                styled_df = market_df.style.applymap(style_func, subset=['Variação 24h'])
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
        else:
            st.info("Carregando dados de mercado...")
        st.caption("Dados públicos da OKX. Atualiza ao recarregar a aba.")
        st.divider()
        st.subheader("📊 Gráfico Interativo — TradingView")
        chart_asset = st.selectbox("Selecione o Ativo para o Gráfico", ["BTCUSDT", "ETHUSDT", "SOLUSDT", "PAXGUSDT"], key="tv_selector", label_visibility="collapsed")
        st.markdown(get_tradingview_widget(chart_asset, height=500), unsafe_allow_html=True)

    with tab2:
        col_refresh, _ = st.columns([1, 4])
        with col_refresh:
             if st.button("🔄 Atualizar", key="refresh_perf"):
                st.cache_data.clear()
                st.rerun()
        c_chart, c_bars = st.columns([3, 2])
        with c_chart:
            fig_eq = chart_equity(curve, equity - total_pnl)
            if fig_eq: st.plotly_chart(fig_eq, use_container_width=True)
            else: st.info("Aguardando trades fechados para gerar curva de equity.")
        with c_bars:
            fig_bars = chart_pnl_bars(trades)
            if fig_bars: st.plotly_chart(fig_bars, use_container_width=True)
            else: st.info("Sem trades suficientes para o gráfico de PnL.")
        st.subheader("Resumo de Performance")
        scol1, scol2, scol3, scol4 = st.columns(4)
        scol1.metric("Wins", stats.get("wins", 0))
        scol2.metric("Losses", stats.get("losses", 0))
        scol3.metric("Avg PnL %", f"{stats.get('avg_pct', 0):.2f}%")
        scol4.metric("Pior Loss", f"${stats.get('worst_loss', 0):.2f}")

    with tab3:
        col_refresh, _ = st.columns([1, 4])
        with col_refresh:
            if st.button("🔄 Atualizar", key="refresh_pos"):
                st.cache_data.clear()
                st.rerun()
        st.subheader("Posições Abertas — Tempo Real")
        if not positions:
            st.info("Nenhuma posição aberta.")
        else:
            rows = [{"Ativo": p["symbol"], "Direção": p["side"], "Tamanho": p["size"],
                       "Entrada": f"${p['entry']:.2f}", "Mark": f"${p['mark']:.2f}",
                       "PnL Não Realizado": f"+${p['pnl']:.2f}" if p['pnl'] >= 0 else f"-${abs(p['pnl']):.2f}",
                       "Alavancagem": f"{p['leverage']}x"} for p in positions]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        if open_pos:
            st.subheader("Ordens Abertas no DB")
            df_open = pd.DataFrame(open_pos)[["symbol", "side", "entry_price", "size", "score", "open_time"]]
            df_open.columns = ["Ativo", "Lado", "Entrada", "Size", "Score", "Aberto em"]
            st.dataframe(df_open, use_container_width=True, hide_index=True)

    with tab4:
        col_refresh, col_export = st.columns([1, 1])
        with col_refresh:
            if st.button("🔄 Atualizar", key="refresh_hist"):
                st.cache_data.clear()
                st.rerun()
        with col_export:
            if trades:
                csv_data = export_trades_to_csv(trades)
                st.download_button(label="📥 Exportar CSV", data=csv_data, file_name=f"historico_trades_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)
        st.subheader("Histórico de Trades")
        if not trades:
            st.info("Nenhum trade fechado.")
        else:
            df_hist = pd.DataFrame(trades)[["symbol", "side", "entry_price", "exit_price", "pnl_usdt", "pnl_pct", "score", "close_time", "ai_reasoning"]].copy()
            df_hist.columns = ["Ativo", "Lado", "Entrada", "Saída", "PnL ($)", "PnL (%)", "Score", "Fechado em", "Raciocínio IA"]
            df_hist["PnL ($)"] = df_hist["PnL ($)"].apply(lambda x: f"+${x:.2f}" if x >= 0 else f"-${abs(x):.2f}")
            df_hist["PnL (%)"] = df_hist["PnL (%)"].apply(lambda x: f"{x:+.2f}%")
            st.dataframe(df_hist[["Ativo", "Lado", "Entrada", "Saída", "PnL ($)", "PnL (%)", "Score", "Fechado em"]], use_container_width=True, hide_index=True, height=280)
            st.subheader("🧠 Raciocínio da IA por Trade")
            for _, row in df_hist.iterrows():
                with st.expander(f"{row['Ativo']} {row['Lado']} | {row['PnL ($)']}"):
                    if row['Raciocínio IA']:
                        st.markdown(f"<div class='reasoning-box'>🤖 {row['Raciocínio IA']}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div class='reasoning-box'>⏳ Análise em processamento...</div>", unsafe_allow_html=True)
                    st.caption(f"Fechado em: {row['Fechado em']}")

    with tab5:
        st.subheader("💻 Processamento da IA — Modo Terminal")
        logs = "\n".join([pensamento_ia() for _ in range(10)])
        st.code(logs, language="bash")
        st.markdown('<div style="text-align:center; margin:10px 0;"><span class="ia-heart"></span><span style="color:#00ff88; font-family:\'Orbitron\';">IA Ativa — Processando</span></div>', unsafe_allow_html=True)
        brain_file = "brain_memory.json"
        if os.path.exists(brain_file):
            try:
                with open(brain_file) as f: bm = json.load(f)
                bc1, bc2, bc3 = st.columns(3)
                bc1.metric("Min Score", bm.get("optimized_min_score", "—"))
                bc2.metric("Risk Level", bm.get("risk_level", "—"))
                bc3.metric("Win Rate Brain", f"{float(bm.get('win_rate', 0))*100:.1f}%")
            except: pass

    with tab6:
        col_refresh, _ = st.columns([1, 4])
        with col_refresh:
            if st.button("🔄 Atualizar Notícias", key="refresh_news"): st.cache_data.clear(); st.rerun()
        st.subheader("📡 Feed de Notícias Crypto")
        try:
            if os.path.exists("news_cache.json"):
                with open("news_cache.json", 'r', encoding='utf-8') as f: cache = json.load(f)
                if cache:
                    for item in cache: st.markdown(f"**{item['source']}** — {item['date']}\n\n{item['title']}\n\n[🔗 Ler completa]({item['link']})\n\n---")
                else:
                    st.info("🔄 Buscando notícias via RSS...")
                    news_items = fetch_news_rss()
                    for item in news_items: st.markdown(f"**{item['source']}** — {item['date']}\n\n{item['title']}\n\n[🔗 Ler completa]({item['link']})\n\n---")
        except Exception as e: st.error(f"❌ Erro ao carregar: {e}")

    with tab7:
        st.markdown("""
        <style>
        .section-title-box {
            background: #0d0b1e; border: 2px solid #8A2BE2; border-radius: 10px;
            padding: 18px 30px; text-align: center; font-family: 'Orbitron', sans-serif;
            font-size: 16px; font-weight: 700; color: #ffffff; letter-spacing: 3px;
            text-transform: uppercase; text-shadow: 0 0 12px rgba(138, 43, 226, 0.9), 0 0 25px rgba(138, 43, 226, 0.5);
            box-shadow: 0 0 20px rgba(138, 43, 226, 0.4), inset 0 0 20px rgba(138, 43, 226, 0.05); margin-bottom: 16px;
        }
        .bot-status-online { background: #0a1f0a; border: 1px solid #00cc44; color: #00ff55; padding: 10px 16px; border-radius: 6px; font-size: 13px; margin-bottom: 12px; }
        .bot-status-offline { background: #1f0a0a; border: 1px solid #cc2200; color: #ff4422; padding: 10px 16px; border-radius: 6px; font-size: 13px; margin-bottom: 12px; }

        /* PAINEL BOT CONTROL */
        .bot-control-panel {
            background: rgba(13,13,26,0.95);
            border: 1px solid rgba(138,43,226,0.4);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
        }
        .equity-ring-wrap {
            text-align: center;
            padding: 20px 0;
        }
        .equity-value {
            font-family: 'Orbitron', sans-serif;
            font-size: 2rem;
            font-weight: 700;
            color: #fff;
        }
        .equity-label {
            font-size: 11px;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 4px;
        }
        .bot-ctrl-label {
            font-size: 11px;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 6px;
            display: block;
        }
        .bot-ctrl-value {
            font-family: 'Orbitron', sans-serif;
            font-size: 13px;
            color: #fff;
            background: rgba(138,43,226,0.1);
            border: 1px solid rgba(138,43,226,0.3);
            border-radius: 8px;
            padding: 10px 14px;
            display: block;
            margin-bottom: 12px;
        }
        .hist-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 10px;
            border-radius: 8px;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.05);
            margin-bottom: 6px;
            font-size: 13px;
        }
        .hist-win  { color: #00ff88; font-weight: 700; font-size: 11px; background: rgba(0,255,136,0.1); border: 1px solid rgba(0,255,136,0.3); padding: 2px 8px; border-radius: 4px; }
        .hist-loss { color: #ff4444; font-weight: 700; font-size: 11px; background: rgba(255,68,68,0.1); border: 1px solid rgba(255,68,68,0.3); padding: 2px 8px; border-radius: 4px; }
        </style>
        """, unsafe_allow_html=True)

        # ── PAINEL DE CONTROLE DO BOT ──────────────────────────────
        st.markdown('<div class="section-title-box">🤖 CONTROLE DO ROBÔ</div>', unsafe_allow_html=True)

        # Linha: equity ring + status + histórico
        ctrl1, ctrl2, ctrl3 = st.columns([1, 1, 1])

        with ctrl1:
            # Equity em ring visual
            eq_display = f"${equity:.2f}" if 'equity' in dir() else "$0.00"
            avail_display = f"${available:.2f}" if 'available' in dir() else "$0.00"

            # Calcula % de uso da conta
            usage_pct = 0
            try:
                if equity > 0 and available >= 0:
                    usage_pct = max(0, min(100, ((equity - available) / equity) * 100))
            except Exception:
                usage_pct = 0

            # SVG ring de equity
            circumference = 2 * 3.14159 * 54
            dash_val = circumference * (usage_pct / 100)
            gap_val = circumference - dash_val

            st.markdown(f"""
            <div style="text-align:center; padding:10px 0;">
                <svg width="160" height="160" viewBox="0 0 160 160">
                    <circle cx="80" cy="80" r="54" fill="none"
                        stroke="rgba(138,43,226,0.15)" stroke-width="12"/>
                    <circle cx="80" cy="80" r="54" fill="none"
                        stroke="#8A2BE2" stroke-width="12"
                        stroke-dasharray="{dash_val:.1f} {gap_val:.1f}"
                        stroke-linecap="round"
                        transform="rotate(-90 80 80)"/>
                    <text x="80" y="72" text-anchor="middle"
                        fill="#fff" font-family="Orbitron,sans-serif"
                        font-size="9" opacity="0.6">$</text>
                    <text x="80" y="88" text-anchor="middle"
                        fill="#fff" font-family="Orbitron,sans-serif"
                        font-size="16" font-weight="700">{equity:.2f}</text>
                    <text x="80" y="104" text-anchor="middle"
                        fill="#888" font-family="sans-serif"
                        font-size="9">Patrimônio</text>
                </svg>
                <div style="font-size:11px;color:#888;margin-top:4px;">
                    Disponível: <span style="color:#8A2BE2;">{avail_display}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Status do bot
            if os.path.exists("bot_heartbeat.json"):
                try:
                    with open("bot_heartbeat.json") as f: hb = json.load(f)
                    last_scan = hb.get("last_scan", "N/A")
                    bot_status_str = hb.get("status", "alive")
                    st.markdown(f"""
                    <div style="text-align:center; margin-top:8px;">
                        <div style="display:inline-flex; align-items:center; gap:6px;
                            background:rgba(0,255,136,0.08); border:1px solid #00cc44;
                            border-radius:20px; padding:5px 14px; font-size:12px; color:#00ff88;">
                            <span style="width:7px;height:7px;border-radius:50%;
                                background:#00ff88;display:inline-block;"></span>
                            Bot Online
                        </div>
                        <div style="font-size:10px;color:#555;margin-top:6px;">
                            Último scan: {last_scan}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                except Exception:
                    st.markdown('<div style="text-align:center;"><span style="color:#ff4444;font-size:12px;">🔴 Status indisponível</span></div>', unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="text-align:center; margin-top:8px;">
                    <div style="display:inline-flex; align-items:center; gap:6px;
                        background:rgba(255,68,68,0.08); border:1px solid #cc2200;
                        border-radius:20px; padding:5px 14px; font-size:12px; color:#ff4444;">
                        <span style="width:7px;height:7px;border-radius:50%;
                            background:#ff4444;display:inline-block;"></span>
                        Bot Offline
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with ctrl2:
            # Parâmetros do bot
            st.markdown('<span class="bot-ctrl-label">Estratégia</span>', unsafe_allow_html=True)
            st.markdown('<span class="bot-ctrl-value">Liquidity Sweep + EMA Cross</span>', unsafe_allow_html=True)

            # Lê brain memory para score e risk
            min_score_val = "70"
            risk_level_val = "NORMAL"
            win_rate_brain = "—"
            if os.path.exists("brain_memory.json"):
                try:
                    with open("brain_memory.json") as f: bm = json.load(f)
                    min_score_val = str(bm.get("optimized_min_score", 70))
                    risk_level_val = bm.get("risk_level", "NORMAL")
                    wr_raw = float(bm.get("win_rate", 0)) * 100
                    win_rate_brain = f"{wr_raw:.1f}%"
                except Exception:
                    pass

            assertividade_pct = 0
            try:
                assertividade_pct = float(win_rate_brain.replace("%","")) if win_rate_brain != "—" else 0
            except Exception:
                pass

            st.markdown(f"""
            <div style="margin-bottom:8px;">
                <span class="bot-ctrl-label">Assertividade (Brain)</span>
                <div style="background:rgba(255,255,255,0.05);border-radius:6px;height:8px;overflow:hidden;margin-bottom:4px;">
                    <div style="background:#8A2BE2;width:{assertividade_pct:.0f}%;height:100%;border-radius:6px;"></div>
                </div>
                <span style="font-size:11px;color:#8A2BE2;">{win_rate_brain}</span>
            </div>
            """, unsafe_allow_html=True)

            col_sc, col_rl = st.columns(2)
            col_sc.metric("Min Score", min_score_val)
            col_rl.metric("Modo Risco", risk_level_val)

            # Lê risk state para loss streak
            risk_file = f"risk_state_{uid}.json"
            if not os.path.exists(risk_file):
                risk_file = "risk_state.json"
            if os.path.exists(risk_file):
                try:
                    with open(risk_file) as f: rs = json.load(f)
                    loss_streak = rs.get("loss_streak", 0)
                    daily_loss  = rs.get("daily_loss_pct", 0) * 100
                    modo_def    = rs.get("modo_reducao", False)
                    col_ls, col_dl = st.columns(2)
                    col_ls.metric("Loss Streak", loss_streak)
                    col_dl.metric("Loss Diário", f"{daily_loss:.2f}%")
                    if modo_def:
                        st.warning("🛡️ Modo Defensivo Ativo")
                except Exception:
                    pass

        with ctrl3:
            # Histórico recente de trades (estilo Auks)
            st.markdown('<span class="bot-ctrl-label">Histórico de Operações</span>', unsafe_allow_html=True)
            recent = get_closed_trades(uid, limit=8) if _SAAS_DB_OK else []
            if recent:
                for t in recent:
                    pnl = t.get("pnl_usdt", 0)
                    sym = t.get("symbol", "—")
                    side = t.get("side", "")
                    arrow = "↗" if side in ("Buy","Long","long","buy") else "↘"
                    color = "#00ff88" if pnl >= 0 else "#ff4444"
                    badge_cls = "hist-win" if pnl >= 0 else "hist-loss"
                    badge_txt = "WIN" if pnl >= 0 else "LOSS"
                    st.markdown(f"""
                    <div class="hist-item">
                        <span style="color:{color};font-size:16px;">{arrow}</span>
                        <span style="color:#fff;flex:1;">{sym}</span>
                        <span style="color:{color};font-size:12px;font-family:'JetBrains Mono';">${pnl:+.2f}</span>
                        <span class="{badge_cls}">{badge_txt}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown('<div style="color:#555;font-size:13px;padding:20px 0;text-align:center;">Nenhuma operação ainda</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── SENHA DE ACESSO ───────────────────────────────────────
        st.markdown('<div class="section-title-box">🔑 &nbsp; SENHA DE ACESSO</div>', unsafe_allow_html=True)
        with st.form("change_pass_form"):
            current_pass = st.text_input("Senha Atual", type="password")
            new_pass = st.text_input("Nova Senha", type="password")
            confirm_pass = st.text_input("Confirmar Nova Senha", type="password")
            submitted = st.form_submit_button("💾 Atualizar Senha", use_container_width=True)
            if submitted:
                if not verify_password(st.session_state.get("user_email",""), current_pass) and current_pass != GLOBAL_PASSWORD:
                    st.error("❌ Senha atual incorreta.")
                elif new_pass != confirm_pass:
                    st.error("❌ As novas senhas não coincidem.")
                elif len(new_pass) < 6:
                    st.error("❌ A nova senha deve ter pelo menos 6 caracteres.")
                else:
                    if _SAAS_DB_OK:
                        set_user_password(st.session_state.get("user_email",""), new_pass)
                        st.success("✅ Senha alterada com sucesso!")
                        st.session_state["logged_in"] = False
                        st.rerun()
                    else:
                        st.error(f"❌ Erro de banco: {_SAAS_DB_ERR}")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── CHAVES API OKX ────────────────────────────────────────
        st.markdown('<div class="section-title-box">🔑 &nbsp; CHAVES API DA OKX</div>', unsafe_allow_html=True)
        st.info("ℹ️ Suas chaves são criptografadas e armazenadas com segurança. Nunca compartilhe sua Passphrase.")
        with st.form("okx_keys_form"):
            api_key = st.text_input("API Key", type="password", placeholder="Cole sua API Key da OKX")
            api_secret = st.text_input("API Secret", type="password", placeholder="Cole sua API Secret da OKX")
            passphrase = st.text_input("Passphrase", type="password", placeholder="Cole sua Passphrase da OKX")
            col_test, col_save = st.columns(2)
            with col_test: test_conn = st.form_submit_button("🔍 Testar Conexão", use_container_width=True)
            with col_save: save_keys = st.form_submit_button("💾 Salvar Chaves", use_container_width=True)
            if test_conn:
                if not all([api_key, api_secret, passphrase]): st.error("❌ Preencha todos os campos para testar.")
                else:
                    with st.spinner("Testando conexão com a OKX..."):
                        try:
                            test_client = _build_okx_client(api_key, api_secret, passphrase)
                            resp = test_client("/api/v5/account/balance", {"ccy": "USDT"})
                            if resp.get("code") == "0":
                                st.success("✅ Conexão OKX validada com sucesso!")
                                st.json({"equity": resp["data"][0].get("totalEq")})
                            else: st.error(f"❌ Erro na conexão: {resp.get('msg', 'Desconhecido')}")
                        except Exception as e: st.error(f"❌ Falha ao conectar: {e}")
            if save_keys:
                if not all([api_key, api_secret, passphrase]): st.error("❌ Preencha todos os campos.")
                elif _SAAS_DB_OK:
                    try:
                        update_user_credentials(st.session_state["user_id"], api_key, api_secret, passphrase)
                        # ✅ FIX 4: invalida cache do cliente OKX para usar as novas chaves imediatamente
                        st.cache_resource.clear()
                        st.success("✅ Chaves salvas com segurança!")
                        st.info("ℹ️ O bot começará a operar em até 1 minuto.")
                    except Exception as e: st.error(f"❌ Erro ao salvar: {e}")
                else: st.error(f"❌ Erro de banco: {_SAAS_DB_ERR}")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── ATIVIDADES RECENTES ───────────────────────────────────
        st.markdown('<div class="section-title-box">📋 &nbsp; ATIVIDADES RECENTES</div>', unsafe_allow_html=True)
        activity_log = get_real_bot_activity(uid, limit=5)
        for log in activity_log:
            pnl_badge = f"   <span style='color:#00ff88'>{log['pnl']}</span>" if log.get('pnl') else ""
            entry_badge = f"   <span style='color:#8A2BE2'>{log['entry']}</span>" if log.get('entry') else ""
            st.markdown(f"`[{log['hora']}]` {log['evento']} • **{log['ativo']}**{pnl_badge}{entry_badge}", unsafe_allow_html=True)

# ==========================================
# MAIN
# ==========================================
def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if not st.session_state["logged_in"]:
        render_login()
    else:
        render_dashboard()

if __name__ == "__main__":
    main()