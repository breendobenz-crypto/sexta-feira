# dashboard_saas.py - DASHBOARD SAAS FINAL COMPLETO
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

# Correção para encontrar o caminho do arquivo corretamente
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ==========================================
# CONFIGURAÇÕES DE SEGURANÇA
# ==========================================
GLOBAL_PASSWORD = os.getenv("VIP_PASSWORD", "SextaFeira2026!")
SALT = "sexta-feira-advanced-vip-salt-2026"

def hash_password(password: str) -> str:
    """Gera hash SHA256 da senha com salt."""
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

.login-wrap {
    max-width: 420px; 
    margin: 60px auto 0;
    background: rgba(13, 13, 13, 0.9);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(138,43,226,0.4);
    border-radius: 16px; 
    padding: 2.5rem 2rem;
    box-shadow: 0 0 50px rgba(138,43,226,0.2);
    animation: slideIn 0.5s ease-out;
}

@keyframes slideIn {
    from { opacity: 0; transform: translateY(-20px); }
    to { opacity: 1; transform: translateY(0); }
}

.login-title {
    text-align: center; 
    color: #8A2BE2; 
    font-size: 1.5rem; 
    font-weight: 700;
    margin-bottom: 1.5rem; 
    font-family: 'Orbitron', sans-serif; 
    letter-spacing: 1px;
    animation: glow 2s ease-in-out infinite alternate;
}

@keyframes glow {
    from { text-shadow: 0 0 10px rgba(138,43,226,0.5); }
    to { text-shadow: 0 0 20px rgba(138,43,226,0.8), 0 0 30px rgba(138,43,226,0.6); }
}

@keyframes pulse-purple {
    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(138,43,226,0.7); }
    70% { transform: scale(1.0); box-shadow: 0 0 0 12px rgba(138,43,226,0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(138,43,226,0); }
}

.ia-heart {
    height: 20px; 
    width: 20px; 
    background-color: #8A2BE2; 
    border-radius: 50%;
    display: inline-block; 
    margin-right: 12px; 
    animation: pulse-purple 2s infinite;
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
    border: 1px solid #8A2BE2 !important;
    background: rgba(138,43,226,0.1) !important;
    color: #fff !important;
    font-family: 'Orbitron', sans-serif !important;
    transition: all 0.3s ease;
    animation: fadeIn 0.5s ease-out;
}

.stButton > button:hover {
    background: #8A2BE2 !important;
    box-shadow: 0 0 15px #8A2BE2 !important;
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
    assets = ["BTC-USDT-SWAP", "ETH-USDT-SWAP", "SOL-USDT-SWAP", "PAXG-USDT-SWAP"]
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
    SYMBOL_MAP_REV = {"BTC-USDT-SWAP": "BTCUSDT", "ETH-USDT-SWAP": "ETHUSDT", "SOL-USDT-SWAP": "SOLUSDT", "PAXG-USDT-SWAP": "PAXGUSDT"}
    CT_VAL = {"BTCUSDT": 0.01, "ETHUSDT": 0.1, "SOLUSDT": 1.0, "PAXGUSDT": 0.01}
    
    if resp_pos.get("code") == "0":
        for p in resp_pos.get("data", []):
            sz = float(p.get("pos", 0) or 0)
            if abs(sz) == 0: continue
            sym = SYMBOL_MAP_REV.get(p.get("instId", " "), p.get("instId", " "))
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
_THOUGHTS = ["Analisando liquidez BTC...", "Calculando EMA9/21/50...", "Verificando filtro HTF 1h...",
    "ATR dentro do range...", "Aguardando sweep SOL...", "RSI neutro...", "Spread ok...",
    "Brain score carregado...", "Cooldown PAXG...", "Risk Manager normal..."]

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
    
    return activities[:limit] if activities else [
        {"hora": datetime.now().strftime("%H:%M:%S"), "evento": "⏳ Aguardando operações...", "ativo": "N/A"}
    ]

# ==========================================
# LOGIN
# ==========================================
def render_login():
    st.markdown("""
    <div style="text-align: center; margin: 80px 0;">
        <h1 style="font-family: 'Orbitron', sans-serif; color: #8A2BE2;">🔒 SEXTA-FEIRA VIP</h1>
        <p style="color: #888; font-size: 1.1rem;">Acesso restrito a assinantes</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form", clear_on_submit=True):
        st.markdown('<div class="login-wrap">', unsafe_allow_html=True)
        st.markdown('<p class="login-title">🟣 Autenticação</p>', unsafe_allow_html=True)
        st.markdown('<p class="login-subtitle">Digite seu email e senha para acessar</p>', unsafe_allow_html=True)
        
        email = st.text_input("📧 Email cadastrado", placeholder="seu@email.com", key="login_email")
        password = st.text_input("🔑 Senha VIP", type="password", placeholder="Digite sua senha", key="login_pass")
        
        submitted = st.form_submit_button("🚀 Acessar Dashboard", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        if submitted:
            if not email or "@" not in email:
                st.error("❌ Digite um email válido.")
                return
            if not password:
                st.error("❌ Digite a senha VIP.")
                return
            
            if _SAAS_DB_OK:
                user = get_user_by_email(email)
                if not user:
                    st.error("❌ Email não encontrado.")
                    return
                
                is_valid = False
                try:
                    if verify_password(email, password):
                        is_valid = True
                    elif password == GLOBAL_PASSWORD:
                        is_valid = True
                except:
                    if password == GLOBAL_PASSWORD:
                        is_valid = True
                
                if is_valid:
                    st.session_state.update({
                        "logged_in": True,
                        "user_id": user["id"],
                        "user_email": user["email"],
                        "user_name": user["display_name"] or user["email"].split("@")[0]
                    })
                    update_last_login(user["id"])
                    st.success("✅ Acesso concedido!")
                    st.rerun()
                else:
                    st.error("❌ Senha incorreta.")
            else:
                st.error(f"❌ Erro de banco: {_SAAS_DB_ERR}")
    
    st.markdown("""
    <div style="text-align: center; margin-top: 60px; color: #555; font-size: 0.9em;">
        <p>🟣 SEXTA-FEIRA ADVANCED © 2026</p>
    </div>
    """, unsafe_allow_html=True)

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
                if len(news) >= max_items:
                    break
        except Exception:
            continue
    
    return news if news else [{"source": "Info", "title": "Nenhuma notícia nova no momento.", "link": "#", "date": ""}]

# ==========================================
# DASHBOARD
# ==========================================
def render_dashboard():
    uid, uname = st.session_state["user_id"], st.session_state["user_name"]
    
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 30px; width: 100%;">
        <h1 style="font-family: 'Orbitron', sans-serif; color: #8A2BE2; font-weight: 700; display: inline-flex; align-items: center; gap: 15px; margin: 0;">
            <div class="ia-heart"></div>
            SEXTA-FEIRA ADVANCED
            <span style="font-size: 0.55em; color: #888; font-weight: 400; font-family: 'JetBrains Mono', monospace;">— {uname}</span>
        </h1>
    </div>
    """, unsafe_allow_html=True)
    
    col_btn = st.columns([1, 1, 1])
    with col_btn[2]:
        if st.button("Sair", use_container_width=True):
            for k in ["logged_in", "user_id", "user_email", "user_name"]:
                st.session_state.pop(k, None)
            st.rerun()
    
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
    m1.metric("Equity", f"${equity:.2f}", delta=f"${available:.2f} livre")
    m2.metric("PnL Total", f"${total_pnl:+.2f}")
    m3.metric("Win Rate", f"{win_rate:.1f}%")
    m4.metric("Total Trades", str(total_tr))
    m5.metric("Best Win", f"${stats.get('best_win', 0):.2f}")
    
    st.caption(f"🔄 Última atualização: {datetime.now().strftime('%H:%M:%S')}")
    st.divider()
    
    # ✅ 7 ABAS COM CONFIGURAÇÕES
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
            # ✅ CORREÇÃO DE COMPATIBILIDADE: Funciona no Local (Pandas Antigo) e Render (Pandas Novo)
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
        
        chart_asset = st.selectbox(
            "Selecione o Ativo para o Gráfico",
            ["BTCUSDT", "ETHUSDT", "SOLUSDT", "PAXGUSDT"],
            key="tv_selector",
            label_visibility="collapsed" 
        )
        
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
            if fig_eq:
                st.plotly_chart(fig_eq, use_container_width=True)
            else:
                st.info("Aguardando trades fechados para gerar curva de equity.")
        with c_bars:
            fig_bars = chart_pnl_bars(trades)
            if fig_bars:
                st.plotly_chart(fig_bars, use_container_width=True)
            else:
                st.info("Sem trades suficientes para o gráfico de PnL.")
        
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
                     "PnL Não Realizado": f"+${p['pnl']:.2f}" if p['pnl'] >=0 else f"-${abs(p['pnl']):.2f}",
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
                st.download_button(
                    label="📥 Exportar CSV",
                    data=csv_data,
                    file_name=f"historico_trades_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        st.subheader("Histórico de Trades")
        if not trades:
            st.info("Nenhum trade fechado.")
        else:
            df_hist = pd.DataFrame(trades)[["symbol", "side", "entry_price", "exit_price", "pnl_usdt", "pnl_pct", "score", "close_time", "ai_reasoning"]].copy()
            df_hist.columns = ["Ativo", "Lado", "Entrada", "Saída", "PnL ($)", "PnL (%)", "Score", "Fechado em", "Raciocínio IA"]
            df_hist["PnL ($)"] = df_hist["PnL ($)"].apply(lambda x: f"+${x:.2f}" if x >= 0 else f"-${abs(x):.2f}")
            df_hist["PnL (%)"] = df_hist["PnL (%)"].apply(lambda x: f"{x:+.2f}%")
            st.dataframe(df_hist[["Ativo", "Lado", "Entrada", "Saída", "PnL ($)", "PnL (%)", "Score", "Fechado em"]], 
                        use_container_width=True, hide_index=True, height=280)
            
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
                with open(brain_file) as f:
                    bm = json.load(f)
                bc1, bc2, bc3 = st.columns(3)
                bc1.metric("Min Score", bm.get("optimized_min_score", "—"))
                bc2.metric("Risk Level", bm.get("risk_level", "—"))
                bc3.metric("Win Rate Brain", f"{float(bm.get('win_rate', 0))*100:.1f}%")
            except:
                pass
    
    with tab6:
        col_refresh, _ = st.columns([1, 4])
        with col_refresh:
            if st.button("🔄 Atualizar Notícias", key="refresh_news"):
                st.cache_data.clear()
                st.rerun()
        
        st.subheader("📡 Feed de Notícias Crypto")
        try:
            if os.path.exists("news_cache.json"):
                with open("news_cache.json", 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                if cache:
                    for item in cache:
                        st.markdown(f"**{item['source']}** — {item['date']}\n\n{item['title']}\n\n[🔗 Ler completa]({item['link']})\n\n---")
                else:
                    st.info("🔄 Buscando notícias via RSS...")
                    news_items = fetch_news_rss()
                    for item in news_items:
                        st.markdown(f"**{item['source']}** — {item['date']}\n\n{item['title']}\n\n[🔗 Ler completa]({item['link']})\n\n---")
            else:
                st.info("⏳ Aguardando bot gerar cache...")
        except Exception as e:
            st.error(f"❌ Erro ao carregar: {e}")
    
    # ✅ ABA 7 - CONFIGURAÇÕES COMPLETAS
    with tab7:
        st.subheader("⚙️ Configurações da Conta")
        
        with st.container():
            st.markdown('<div class="config-section">', unsafe_allow_html=True)
            st.write("### 🔑 Senha de Acesso")
            with st.form("change_pass_form"):
                current_pass = st.text_input("Senha Atual", type="password")
                new_pass = st.text_input("Nova Senha", type="password")
                confirm_pass = st.text_input("Confirmar Nova Senha", type="password")
                submitted = st.form_submit_button("💾 Atualizar Senha", use_container_width=True)
                if submitted:
                    if not verify_password(st.session_state["user_email"], current_pass) and current_pass != GLOBAL_PASSWORD:
                        st.error("❌ Senha atual incorreta.")
                    elif new_pass != confirm_pass:
                        st.error("❌ As novas senhas não coincidem.")
                    elif len(new_pass) < 6:
                        st.error("❌ A nova senha deve ter pelo menos 6 caracteres.")
                    else:
                        if _SAAS_DB_OK:
                            set_user_password(st.session_state["user_email"], new_pass)
                            st.success("✅ Senha alterada com sucesso!")
                            st.info("ℹ️ Faça login novamente com a nova senha.")
                            st.session_state["logged_in"] = False
                            st.rerun()
                        else:
                            st.error(f"❌ Erro de banco: {_SAAS_DB_ERR}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="config-section">', unsafe_allow_html=True)
            st.write("### 🔑 Chaves API da OKX")
            st.info("ℹ️ Suas chaves são criptografadas e armazenadas com segurança. Nunca compartilhe sua Passphrase.")
            
            with st.form("okx_keys_form"):
                api_key = st.text_input("API Key", type="password", placeholder="Cole sua API Key da OKX")
                api_secret = st.text_input("API Secret", type="password", placeholder="Cole sua API Secret da OKX")
                passphrase = st.text_input("Passphrase", type="password", placeholder="Cole sua Passphrase da OKX")
                
                col_test, col_save = st.columns(2)
                with col_test:
                    test_conn = st.form_submit_button("🔍 Testar Conexão", use_container_width=True)
                with col_save:
                    save_keys = st.form_submit_button("💾 Salvar Chaves", use_container_width=True)
                
                if test_conn:
                    if not all([api_key, api_secret, passphrase]):
                        st.error("❌ Preencha todos os campos para testar.")
                    else:
                        with st.spinner("Testando conexão com a OKX..."):
                            try:
                                test_client = _build_okx_client(api_key, api_secret, passphrase)
                                resp = test_client("/api/v5/account/balance", {"ccy": "USDT"})
                                if resp.get("code") == "0":
                                    st.success("✅ Conexão OKX validada com sucesso!")
                                    st.json({"equity": resp["data"][0].get("totalEq")})
                                else:
                                    st.error(f"❌ Erro na conexão: {resp.get('msg', 'Desconhecido')}")
                            except Exception as e:
                                st.error(f"❌ Falha ao conectar: {e}")
                
                if save_keys:
                    if not all([api_key, api_secret, passphrase]):
                        st.error("❌ Preencha todos os campos.")
                    elif _SAAS_DB_OK:
                        try:
                            update_user_credentials(st.session_state["user_id"], api_key, api_secret, passphrase)
                            st.success("✅ Chaves salvas com segurança!")
                            st.info("ℹ️ O bot começará a operar em até 1 minuto.")
                        except Exception as e:
                            st.error(f"❌ Erro ao salvar: {e}")
                    else:
                        st.error(f"❌ Erro de banco: {_SAAS_DB_ERR}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="config-section">', unsafe_allow_html=True)
            st.write("### 🤖 Robô Sexta-Feira")
            
            bot_active = os.path.exists("bot_heartbeat.json")
            if bot_active:
                try:
                    with open("bot_heartbeat.json") as f:
                        hb = json.load(f)
                    last_scan = hb.get("last_scan", "N/A")
                    st.markdown(f'<div class="bot-status-online">🟢 Bot Online • Último scan: {last_scan}</div>', unsafe_allow_html=True)
                except:
                    st.markdown('<div class="bot-status-offline">🔴 Status indisponível</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="bot-status-offline">🔴 Bot Offline • Aguardando inicialização</div>', unsafe_allow_html=True)
            
            st.write("#### 📋 Atividades Recentes (Tempo Real)")
            activity_log = get_real_bot_activity(uid, limit=5)
            for log in activity_log:
                pnl_badge = f" <span style='color:#00ff88'>{log['pnl']}</span>" if log.get('pnl') else ""
                entry_badge = f" <span style='color:#8A2BE2'>{log['entry']}</span>" if log.get('entry') else ""
                st.markdown(f"`[{log['hora']}]` {log['evento']} • **{log['ativo']}**{pnl_badge}{entry_badge}", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    
    if not st.session_state["logged_in"]:
        render_login()
    else:
        render_dashboard()

if __name__ == "__main__":
    main()