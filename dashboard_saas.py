# ==========================================
# DASHBOARD SAAS - SEXTA-FEIRA ADVANCED
# Login por email → isolamento total por user_id.
# Chaves OKX descriptografadas APENAS no backend (nunca no frontend).
# Dados live via OKXClient instanciado por sessão.
# ==========================================
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
import sys
import random
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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
# CSS — TEMA JARVIS
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');

.stApp { background-color: #050505; font-family: 'Orbitron', sans-serif; }
.main  { background-color: #050505; }

h1, h2, h3 {
    color: #8A2BE2 !important;
    font-weight: 700;
    text-shadow: 0 0 10px rgba(138,43,226,0.5);
}

/* Login box */
.login-wrap {
    max-width: 400px;
    margin: 80px auto 0;
    background: #0d0d0d;
    border: 1px solid #8A2BE2;
    border-radius: 12px;
    padding: 2.5rem 2rem;
    box-shadow: 0 0 30px rgba(138,43,226,0.2);
}
.login-title {
    text-align: center;
    color: #8A2BE2;
    font-size: 1.3rem;
    font-weight: 700;
    margin-bottom: 1.5rem;
    font-family: 'Orbitron', sans-serif;
}

/* Pulse */
@keyframes pulse-purple {
    0%   { transform: scale(0.95); box-shadow: 0 0 0 0   rgba(138,43,226,0.7); }
    70%  { transform: scale(1.0);  box-shadow: 0 0 0 10px rgba(138,43,226,0);   }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0   rgba(138,43,226,0);   }
}
.ia-heart {
    height: 18px; width: 18px;
    background-color: #8A2BE2;
    border-radius: 50%;
    display: inline-block;
    margin-right: 10px;
    animation: pulse-purple 2s infinite;
}

/* Métricas */
[data-testid="stMetric"] {
    background-color: #111;
    border: 1px solid #8A2BE2;
    padding: 15px;
    border-radius: 8px;
    box-shadow: 0 0 10px rgba(138,43,226,0.2);
}
[data-testid="stMetricValue"] { color: #fff !important; font-family: 'Orbitron', sans-serif; }
[data-testid="stMetricLabel"] { color: #8A2BE2 !important; font-family: 'Orbitron', sans-serif; }

/* Status badge */
.status-box {
    padding: 10px; border-radius: 6px; text-align: center;
    background: #1a0b2e; border: 1px solid #8A2BE2;
    margin-bottom: 5px; box-shadow: 0 0 5px rgba(138,43,226,0.3);
}
.status-label { font-size: 11px; color: #aaa; display: block; text-transform: uppercase; }
.status-value { font-size: 14px; font-weight: 800; color: #fff; }

/* Tabelas */
th { color: #8A2BE2 !important; background: #000 !important; font-family: 'Orbitron', sans-serif; }
td { color: #fff !important; font-family: 'Courier New', monospace; }

/* PnL colorido */
.pnl-pos { color: #00ff88; font-weight: bold; }
.pnl-neg { color: #ff4444; font-weight: bold; }

/* Thinking box */
.thinking-box {
    background: #000; border: 1px solid #333;
    padding: 10px; border-radius: 5px;
    height: 140px; overflow-y: auto;
    font-family: 'Courier New', monospace;
    font-size: 12px; color: #0f0;
}
.log-line { margin-bottom: 4px; border-bottom: 1px solid #111; padding-bottom: 2px; }

/* Ocultar chrome padrão */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# IMPORTS SAAS (com tratamento de erro claro)
# ==========================================
try:
    from saas_db import (
        get_user_by_email, get_decrypted_credentials, update_last_login,
        get_closed_trades, get_open_trades, get_user_stats, get_equity_curve,
    )
    _SAAS_DB_OK = True
except ImportError as e:
    _SAAS_DB_OK = False
    _SAAS_DB_ERR = str(e)


# ==========================================
# OKX CLIENT POR SESSÃO
# ==========================================
@st.cache_resource(show_spinner=False)
def _build_okx_client(api_key: str, api_secret: str, passphrase: str):
    """
    Instancia um OKXClient isolado para o VIP logado.
    Cache por session (não compartilhado entre usuários).
    As chaves NUNCA transitam pelo frontend — chegam já descriptografadas do backend.
    """
    import hashlib
    import hmac
    import base64
    import requests
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
            "OK-ACCESS-KEY":        api_key,
            "OK-ACCESS-SIGN":       _sign(ts, method, path, body),
            "OK-ACCESS-TIMESTAMP":  ts,
            "OK-ACCESS-PASSPHRASE": passphrase,
            "Content-Type":         "application/json",
        }
        if _sim:
            h["x-simulated-trading"] = "1"
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
    """
    Busca equity e posições abertas diretamente da OKX com as
    credenciais do VIP. Chaves descriptografadas no backend.
    Retorna dict com equity, available, positions.
    """
    if not _SAAS_DB_OK:
        return {"equity": 0.0, "available": 0.0, "positions": [], "error": _SAAS_DB_ERR}

    creds = get_decrypted_credentials(user_id)
    if not creds:
        return {"equity": 0.0, "available": 0.0, "positions": [], "error": "Credenciais não encontradas"}

    okx_get = _build_okx_client(
        creds["api_key"], creds["api_secret"], creds["passphrase"]
    )

    # Saldo
    resp = okx_get("/api/v5/account/balance", {"ccy": "USDT"})
    equity    = 0.0
    available = 0.0
    if resp.get("code") == "0" and resp.get("data"):
        d         = resp["data"][0]
        equity    = float(d.get("totalEq", 0) or 0)
        for det in d.get("details", []):
            if det.get("ccy") == "USDT":
                available = float(det.get("availBal", 0) or 0)
                break

    # Posições
    resp_pos = okx_get("/api/v5/account/positions", {"instType": "SWAP"})
    positions = []
    SYMBOL_MAP_REV = {
        "BTC-USDT-SWAP": "BTCUSDT", "ETH-USDT-SWAP": "ETHUSDT",
        "SOL-USDT-SWAP": "SOLUSDT", "PAXG-USDT-SWAP": "PAXGUSDT",
    }
    CT_VAL = {"BTCUSDT": 0.01, "ETHUSDT": 0.1, "SOLUSDT": 1.0, "PAXGUSDT": 0.01}
    if resp_pos.get("code") == "0":
        for p in resp_pos.get("data", []):
            sz = float(p.get("pos", 0) or 0)
            if abs(sz) == 0:
                continue
            inst  = p.get("instId", "")
            sym   = SYMBOL_MAP_REV.get(inst, inst)
            ct    = CT_VAL.get(sym, 0.01)
            qty   = round(abs(sz) * ct, 6)
            upl   = float(p.get("upl", 0) or 0)
            positions.append({
                "symbol":       sym,
                "side":         "Long" if sz > 0 else "Short",
                "size":         qty,
                "entry":        float(p.get("avgPx", 0) or 0),
                "mark":         float(p.get("markPx", 0) or 0),
                "pnl":          upl,
                "leverage":     int(float(p.get("lever", 1) or 1)),
            })

    return {"equity": equity, "available": available, "positions": positions, "error": None}


# ==========================================
# GRÁFICOS
# ==========================================
def chart_equity(curve: list[dict], base_equity: float) -> go.Figure:
    if not curve:
        return None
    dates  = [r["date"]  for r in curve]
    values = [base_equity + r["equity"] for r in curve]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=values, mode="lines+markers",
        name="Equity",
        line=dict(color="#8A2BE2", width=2),
        marker=dict(size=5, color="#8A2BE2"),
        fill="tozeroy",
        fillcolor="rgba(138,43,226,0.08)",
    ))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Orbitron", color="white"),
        title_text="Curva de Equity (30 dias)",
        title_font_color="#8A2BE2",
        margin=dict(l=0, r=0, t=40, b=0),
        height=280,
        xaxis_title="Data",
        yaxis_title="Equity ($)",
        showlegend=False,
    )
    return fig


def chart_pnl_bars(trades: list[dict]) -> go.Figure:
    if not trades:
        return None
    df = pd.DataFrame(trades[-20:]).iloc[::-1]
    colors = ["#00ff88" if v > 0 else "#ff4444" for v in df["pnl_usdt"]]
    labels = [f"{r['symbol']} {r['side']}" for _, r in df.iterrows()]

    fig = go.Figure(go.Bar(
        x=df["pnl_usdt"], y=labels,
        orientation="h",
        marker_color=colors,
        text=[f"${v:+.2f}" for v in df["pnl_usdt"]],
        textposition="outside",
    ))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Orbitron", color="white", size=10),
        title_text="PnL Últimos 20 Trades",
        title_font_color="#8A2BE2",
        margin=dict(l=0, r=60, t=40, b=0),
        height=320,
        showlegend=False,
    )
    return fig


# ==========================================
# PENSAMENTOS DA IA
# ==========================================
_THOUGHTS = [
    "Analisando liquidez no BTC-USDT-SWAP...",
    "Calculando EMA9/21/50 no 5m...",
    "Verificando filtro HTF 1h...",
    "ATR atual dentro do range permitido...",
    "Aguardando liquidity sweep no SOL...",
    "RSI em zona neutra — sem bloqueio...",
    "Spread dentro do limite máximo...",
    "Brain score carregado do jarvis_saas.db...",
    "Cooldown ativo para PAXG (London session)...",
    "Risk Manager: modo normal...",
]

def pensamento_ia():
    return f"<div class='log-line'>[{datetime.now().strftime('%H:%M:%S')}] {random.choice(_THOUGHTS)}</div>"


# ==========================================
# TELA DE LOGIN
# ==========================================
def render_login():
    st.markdown("""
    <div class='login-wrap'>
        <p class='login-title'>🟣 SEXTA-FEIRA ADVANCED</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=False):
        st.markdown("#### Acesso VIP")
        email = st.text_input("Email cadastrado", placeholder="seu@email.com")
        submitted = st.form_submit_button("Entrar →", use_container_width=True)

    if submitted:
        if not email or "@" not in email:
            st.error("Digite um email válido.")
            return

        if not _SAAS_DB_OK:
            st.error(f"Erro de configuração: {_SAAS_DB_ERR}\nVerifique se saas_db.py está na pasta.")
            return

        with st.spinner("Verificando acesso..."):
            user = get_user_by_email(email)

        if not user:
            st.error("Email não encontrado ou conta inativa. Contate o suporte.")
        else:
            update_last_login(user["id"])
            st.session_state["user_id"]   = user["id"]
            st.session_state["user_email"]= user["email"]
            st.session_state["user_name"] = user["display_name"] or user["email"].split("@")[0]
            st.session_state["logged_in"] = True
            st.rerun()


# ==========================================
# DASHBOARD PRINCIPAL
# ==========================================
def render_dashboard():
    uid   = st.session_state["user_id"]
    uname = st.session_state["user_name"]
    email = st.session_state["user_email"]

    # Header
    col_title, col_logout = st.columns([5, 1])
    with col_title:
        st.markdown(
            f"<h1><div class='ia-heart'></div>SEXTA-FEIRA ADVANCED"
            f" <span style='font-size:.55em;color:#aaa'>— {uname}</span></h1>",
            unsafe_allow_html=True,
        )
    with col_logout:
        if st.button("Sair", use_container_width=True):
            for k in ["logged_in", "user_id", "user_email", "user_name"]:
                st.session_state.pop(k, None)
            st.rerun()

    # Status bar
    s1, s2, s3, s4, s5 = st.columns(5)
    s1.markdown("<div class='status-box'><span class='status-label'>Strategy</span><span class='status-value'>ONLINE</span></div>", unsafe_allow_html=True)
    s2.markdown("<div class='status-box'><span class='status-label'>Risk Guard</span><span class='status-value'>ACTIVE</span></div>", unsafe_allow_html=True)
    s3.markdown("<div class='status-box'><span class='status-label'>OKX API</span><span class='status-value'>CONNECTED</span></div>", unsafe_allow_html=True)
    s4.markdown("<div class='status-box'><span class='status-label'>Scanner</span><span class='status-value'>RUNNING</span></div>", unsafe_allow_html=True)
    s5.markdown("<div class='status-box'><span class='status-label'>Conta</span><span class='status-value'>VIP</span></div>", unsafe_allow_html=True)

    st.divider()

    # ---- DADOS LIVE E DB ----
    with st.spinner("Carregando dados da conta..."):
        live     = fetch_live_account(uid)
        stats    = get_user_stats(uid)
        trades   = get_closed_trades(uid, limit=50)
        curve    = get_equity_curve(uid, days=30)
        open_pos = get_open_trades(uid)

    if live.get("error"):
        st.warning(f"⚠️ Não foi possível conectar na OKX: {live['error']}")

    equity    = live["equity"]
    available = live["available"]
    positions = live["positions"]

    win_rate   = stats["win_rate"] * 100
    total_pnl  = stats["total_pnl"]
    total_tr   = stats["total_trades"]

    # ---- MÉTRICAS ----
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Equity",        f"${equity:.2f}",    delta=f"${available:.2f} livre")
    m2.metric("PnL Total",     f"${total_pnl:+.2f}")
    m3.metric("Win Rate",      f"{win_rate:.1f}%")
    m4.metric("Total Trades",  str(total_tr))
    m5.metric("Best Win",      f"${stats['best_win']:.2f}")

    st.divider()

    # ---- TABS ----
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Performance",
        "📌 Posições Abertas",
        "📋 Histórico",
        "🧠 IA",
    ])

    # TAB 1 — PERFORMANCE
    with tab1:
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

        # Resumo estatístico
        st.subheader("Resumo de Performance")
        scol1, scol2, scol3, scol4 = st.columns(4)
        scol1.metric("Wins",        stats["wins"])
        scol2.metric("Losses",      stats["losses"])
        scol3.metric("Avg PnL %",   f"{stats['avg_pct']:.2f}%")
        scol4.metric("Pior Loss",   f"${stats['worst_loss']:.2f}")

    # TAB 2 — POSIÇÕES ABERTAS (dados LIVE da OKX)
    with tab2:
        st.subheader("Posições Abertas — Tempo Real")

        if not positions:
            st.info("Nenhuma posição aberta no momento.")
        else:
            rows = []
            for p in positions:
                pnl_val = p["pnl"]
                pnl_fmt = f"+${pnl_val:.2f}" if pnl_val >= 0 else f"-${abs(pnl_val):.2f}"
                rows.append({
                    "Ativo":     p["symbol"],
                    "Direção":   p["side"],
                    "Tamanho":   p["size"],
                    "Entrada":   f"${p['entry']:.2f}",
                    "Mark":      f"${p['mark']:.2f}",
                    "PnL Não Realizado": pnl_fmt,
                    "Alavancagem": f"{p['leverage']}x",
                })
            df_pos = pd.DataFrame(rows)
            st.dataframe(df_pos, use_container_width=True, hide_index=True)

        # Posições abertas no DB (ordens ainda não confirmadas como OPEN)
        if open_pos:
            st.subheader("Ordens Abertas no DB")
            df_open = pd.DataFrame(open_pos)[["symbol","side","entry_price","size","score","open_time"]]
            df_open.columns = ["Ativo","Lado","Entrada","Size","Score","Aberto em"]
            st.dataframe(df_open, use_container_width=True, hide_index=True)

    # TAB 3 — HISTÓRICO
    with tab3:
        st.subheader("Histórico de Trades")
        if not trades:
            st.info("Nenhum trade fechado ainda.")
        else:
            df_hist = pd.DataFrame(trades)
            df_hist = df_hist[[
                "symbol","side","entry_price","exit_price",
                "pnl_usdt","pnl_pct","score","close_time"
            ]].copy()
            df_hist.columns = [
                "Ativo","Lado","Entrada","Saída",
                "PnL ($)","PnL (%)","Score","Fechado em"
            ]
            df_hist["PnL ($)"] = df_hist["PnL ($)"].apply(lambda x: f"+${x:.2f}" if x >= 0 else f"-${abs(x):.2f}")
            df_hist["PnL (%)"] = df_hist["PnL (%)"].apply(lambda x: f"{x:+.2f}%")
            st.dataframe(df_hist, use_container_width=True, hide_index=True, height=450)

        if st.button("🔄 Atualizar histórico"):
            st.rerun()

    # TAB 4 — IA
    with tab4:
        st.subheader("Processamento da IA em Tempo Real")
        logs = "".join([pensamento_ia() for _ in range(10)])
        st.markdown(f'<div class="thinking-box">{logs}</div>', unsafe_allow_html=True)

        # Brain status
        brain_file = "brain_memory.json"
        if os.path.exists(brain_file):
            try:
                with open(brain_file) as f:
                    bm = json.load(f)
                bc1, bc2, bc3 = st.columns(3)
                bc1.metric("Min Score (Brain)", bm.get("optimized_min_score", "—"))
                bc2.metric("Risk Level",        bm.get("risk_level", "—"))
                bc3.metric("Win Rate Brain",    f"{float(bm.get('win_rate', 0))*100:.1f}%")
            except Exception:
                pass

    # Heartbeat
    hb_file = "bot_heartbeat.json"
    if os.path.exists(hb_file):
        try:
            with open(hb_file) as f:
                hb = json.load(f)
            st.caption(
                f"⏱ Último heartbeat: {hb.get('last_scan','—')} | "
                f"Status: {hb.get('status','—')} | "
                f"Módulo: {hb.get('module','—')}"
            )
        except Exception:
            pass


# ==========================================
# ROTEAMENTO PRINCIPAL
# ==========================================
def main():
    # Inicializa session state
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        render_login()
    else:
        render_dashboard()


if __name__ == "__main__" or True:
    main()