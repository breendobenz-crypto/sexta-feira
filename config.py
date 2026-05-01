# ===============================
# JARVIS CONFIG - v4 PAXG REATIVADO + OKX COMPAT
# v3: PAXG desativado, fixes criticos
# v4: PAXG reativado com filtros robustos:
#     - gold_filter HTF 1h obrigatorio
#     - session_filter London/NY ouro
#     - max_leverage=3, allow_counter_trend=False
#     - cooldown_paxg=1800s (30min pos-loss)
#     - min_score=78, RSI conservador 75/25
#     - COMPATIBILIDADE OKX: aliases para okx_connect.py
# ===============================
import os
from dotenv import load_dotenv

load_dotenv()

# --------------------------------
# OKX API
# --------------------------------
OKX_API_KEY = os.getenv("OKX_API_KEY", "")
OKX_API_SECRET = os.getenv("OKX_API_SECRET", "")
OKX_PASSPHRASE = os.getenv("OKX_PASSPHRASE", "")
OKX_TESTNET = os.getenv("OKX_TESTNET", "false").lower() == "true"

# Símbolos na OKX (formato com hífen para API)
OKX_SYMBOLS = [
    "BTC-USDT",
    "ETH-USDT",
    "SOL-USDT",
    "PAXG-USDT",
]

# Mapeamento de quantidades mínimas (Bybit/OKX)
MIN_QTY_MAP = {
    "BTCUSDT":  0.001,
    "ETHUSDT":  0.01,
    "SOLUSDT":  0.1,
    "PAXGUSDT": 0.01,
}

TIMEFRAME                 = "5"
CANDLE_LIMIT              = 200
CANDLE_DELAY              = 10
DASHBOARD_UPDATE_INTERVAL = 5

# --------------------------------
# EXECUCAO
# --------------------------------
LEVERAGE   = 3
ORDER_TYPE = "Market"
ORDER_SIZE = 1

# --------------------------------
# RISK MANAGEMENT
# --------------------------------
RISK_PER_TRADE        = 0.005
MAX_DAILY_LOSS        = 0.05
LOSS_STREAK_LIMIT     = 3
RISK_REDUCTION_FACTOR = 0.5
MIN_CAPITAL_REQUIRED  = 20
MAX_GLOBAL_EXPOSURE   = 0.20
MAX_TRADES_ABERTOS    = 1
RISCO_POR_TRADE       = 0.01
STOP_MAXIMO_PERCENT   = 0.02

# --------------------------------
# ASSET CONFIG POR ATIVO
# --------------------------------
ASSET_CONFIG = {
    "BTCUSDT": {
        "min_score": 70, "max_leverage": 5,
        "atr_multiplier_stop": 2.5, "atr_multiplier_tp": 4.0,
        "min_stop_pct": 0.003, "max_stop_pct": 0.03,
        "position_size_pct": 0.25, "max_trades_per_day": 5,
        "allow_counter_trend": False, "high_vol_threshold": 0.025,
        "low_vol_threshold": 0.004, "sweep_lookback": 15,
        "min_volume_mult": 1.1, "htf_required": True,
        "rsi_block_long": 70, "rsi_block_short": 30,
        "btc_correlation": False, "use_gold_filter": False,
        "session_filter": False, "max_spread_pct": 0.0008,
        "max_slippage_pct": 0.15, "pause_after_losses": 3,
    },
    "ETHUSDT": {
        "min_score": 75, "max_leverage": 3,
        "atr_multiplier_stop": 3.0, "atr_multiplier_tp": 5.0,
        "min_stop_pct": 0.004, "max_stop_pct": 0.035,
        "position_size_pct": 0.25, "max_trades_per_day": 3,
        "allow_counter_trend": False, "high_vol_threshold": 0.03,
        "low_vol_threshold": 0.005, "sweep_lookback": 15,
        "min_volume_mult": 1.1, "htf_required": True,
        "rsi_block_long": 70, "rsi_block_short": 30,
        "btc_correlation": True, "use_gold_filter": False,
        "session_filter": False, "max_spread_pct": 0.0010,
        "max_slippage_pct": 0.15, "pause_after_losses": 3,
    },
    "SOLUSDT": {
        "min_score": 80, "max_leverage": 2,
        "atr_multiplier_stop": 3.5, "atr_multiplier_tp": 6.0,
        "min_stop_pct": 0.006, "max_stop_pct": 0.04,
        "position_size_pct": 0.20, "max_trades_per_day": 2,
        "allow_counter_trend": False, "high_vol_threshold": 0.04,
        "low_vol_threshold": 0.006, "sweep_lookback": 15,
        "min_volume_mult": 1.1, "htf_required": True,
        "rsi_block_long": 70, "rsi_block_short": 30,
        "btc_correlation": True, "use_gold_filter": False,
        "session_filter": False, "max_spread_pct": 0.0015,
        "max_slippage_pct": 0.25, "pause_after_losses": 2,
    },
    "PAXGUSDT": {
        # Ouro tokenizado: regime totalmente diferente de crypto
        # v4: session_filter=True (Londres 07-11 + NY 13-17 UTC)
        #     gold_filter_htf=True (EMA50>EMA200 no 1h obrigatorio)
        #     cooldown_paxg=1800 (30min entre trades)
        #     stop mais largo: min 0.5% para sobreviver ao noise do 5m
        "min_score": 78, "max_leverage": 3,
        "atr_multiplier_stop": 2.5, "atr_multiplier_tp": 5.0,
        "min_stop_pct": 0.005, "max_stop_pct": 0.025,
        "position_size_pct": 0.20, "max_trades_per_day": 3,
        "allow_counter_trend": False,
        "high_vol_threshold": 0.015, "low_vol_threshold": 0.003,
        "sweep_lookback": 30, "min_volume_mult": 1.0,
        "htf_required": False,
        "rsi_block_long": 75, "rsi_block_short": 25,
        "btc_correlation": False,
        "use_gold_filter": True,
        "gold_filter_htf": True,
        "session_filter": True,
        "max_spread_pct": 0.0012,
        "max_slippage_pct": 0.15,
        "pause_after_losses": 2,
        "cooldown_override": 1800,
    },
}

# --------------------------------
# VOLATILIDADE
# --------------------------------
MIN_VOLATILITY = 0.8
MAX_VOLATILITY = 3.5

# --------------------------------
# QUANT MODE
# --------------------------------
QUANT_MODE         = True
MIN_SCORE_ENTRY    = 75
ANTI_FAKE_BREAKOUT = True
TREND_CONFIRMATION = True

# --------------------------------
# SCORE DINAMICO
# --------------------------------
BASE_SCORE_TO_TRADE = 70
VOL_HIGH_MULT       = 1.15
VOL_LOW_MULT        = 0.85
TRADE_COOLDOWN      = 900

# --------------------------------
# TAKE PROFIT / STOP
# --------------------------------
RR_RATIO            = 2.0
ATR_MULTIPLIER_STOP = 2.5

# --------------------------------
# TELEGRAM
# --------------------------------
TELEGRAM_TOKEN        = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID      = os.getenv("TELEGRAM_CHAT_ID", "")
TELEGRAM_ADMIN_IDS    = [TELEGRAM_CHAT_ID] if TELEGRAM_CHAT_ID else []
TELEGRAM_SIGNAL_GROUP = os.getenv("TELEGRAM_SIGNAL_GROUP", "")

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    print("[WARN] TELEGRAM_TOKEN ou TELEGRAM_CHAT_ID nao configurados.")

# --------------------------------
# ELEVENLABS
# --------------------------------
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
VOICE_ID           = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

# --------------------------------
# ANTHROPIC
# --------------------------------
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# --------------------------------
# LOGS
# --------------------------------
ENABLE_LOG = True
LOG_TRADES = True

# --------------------------------
# WATCHDOG
# --------------------------------
WATCHDOG_RESTART_SECONDS = 5

# --------------------------------
# STREAMLIT
# --------------------------------
DASHBOARD_PORT    = 8501
AUTO_OPEN_BROWSER = True

# --------------------------------
# GOOGLE SHEETS
# --------------------------------
GOOGLE_SHEET_ID   = os.getenv("GOOGLE_SHEET_ID", "")
GOOGLE_SHEET_NAME = "Jarvis_Trades"

# --------------------------------
# TRADINGVIEW
# --------------------------------
TRADINGVIEW_CHART_URL = os.getenv(
    "TRADINGVIEW_CHART_URL",
    "https://www.tradingview.com/x/nL79vv8a/"
)

# --------------------------------
# OBSIDIAN
# --------------------------------
OBSIDIAN_TRADES_PATH = os.getenv("OBSIDIAN_TRADES_PATH", "trades")

# --------------------------------
# HEARTBEAT
# --------------------------------
HEARTBEAT_FILE = "bot_heartbeat.json"

# --------------------------------
# ALIASES E COMPATIBILIDADE
# --------------------------------
DEFAULT_QTY      = ORDER_SIZE
DEFAULT_LEVERAGE = LEVERAGE

# ==========================================
# COMPATIBILIDADE COM OKX_CONNECT.PY (CRÍTICO)
# ==========================================

# 1. Alias para o nome que okx_connect.py espera (OKX_API_SECRET)

# 2. Define SYMBOLS no formato interno (sem hífen) para o bot
#    Converte: ["BTC-USDT", ...] → ["BTCUSDT", ...]
SYMBOLS = [s.replace("-USDT", "USDT") for s in OKX_SYMBOLS]

DB_NAME = "jarvis_trades.db"
