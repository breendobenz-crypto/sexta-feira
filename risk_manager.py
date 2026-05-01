# risk_manager.py - JARVIS PRO (V4 - CORRIGIDO & OTIMIZADO)
import json
import os
from datetime import datetime, timezone
from okx_connect import get_account_info, get_price
from config import (
    RISK_PER_TRADE,
    MAX_DAILY_LOSS,
    LOSS_STREAK_LIMIT,
    RISK_REDUCTION_FACTOR,
    ASSET_CONFIG,
    MIN_QTY_MAP,
    SYMBOLS,
    HEARTBEAT_FILE
)

# ==========================================
# CONFIG EXTRA + DEFAULTS SEGUROS
# ==========================================
DEFAULT_LEVERAGE = 5
STATE_FILE = "risk_state.json"
DEFAULT_ASSET_RISK = {
    "max_risk_pct": 0.01,
    "min_leverage": 2,
    "max_leverage": 5,
    "volatility_adjust": True,
    "small_bank_mode": True
}

# ==========================================
# ❤️ HEARTBEAT PARA O GUARDIÃO
# ==========================================
def _log_risk_activity(action: str, symbol: str = None, details: dict = None):
    try:
        if os.path.exists(HEARTBEAT_FILE):
            with open(HEARTBEAT_FILE, "r") as f:
                hb = json.load(f)
            hb["last_risk_action"] = action
            hb["last_risk_symbol"] = symbol
            hb["last_risk_details"] = details or {}
            hb["last_risk_time"] = datetime.now(timezone.utc).isoformat()
            with open(HEARTBEAT_FILE, "w") as f:
                json.dump(hb, f)
    except:
        pass

# ==========================================
# GESTÃO DE ESTADO PERSISTENTE
# ==========================================
def carregar_risk_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                data = json.load(f)
            last_date = data.get('date', None)
            today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            if last_date != today:
                print(f"[RISK] Novo dia detectado ({today}). Resetando contadores diários.")
                _log_risk_activity("daily_reset")
                new_state = {
                    "loss_streak": 0,
                    "daily_loss_pct": 0.0,
                    "modo_reducao": False,
                    "date": today
                }
                try:
                    with open(STATE_FILE, "w") as _fw:
                        json.dump(new_state, _fw, indent=2)
                except Exception:
                    pass
                return new_state
            return data
        except Exception as e:
            print(f"[ERRO] Falha ao ler estado de risco: {e}")
            _log_risk_activity("state_load_failed", details={"error": str(e)})

    return {
        "loss_streak": 0,
        "daily_loss_pct": 0.0,
        "modo_reducao": False,
        "date": datetime.now(timezone.utc).strftime('%Y-%m-%d')
    }

def salvar_risk_state(state):
    try:
        state['date'] = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"[ERRO] Falha ao salvar estado de risco: {e}")
        _log_risk_activity("state_save_failed", details={"error": str(e)})

try:
    risk_state = carregar_risk_state()
except Exception:
    risk_state = {
        "loss_streak": 0,
        "daily_loss_pct": 0.0,
        "modo_reducao": False,
        "date": datetime.now(timezone.utc).strftime('%Y-%m-%d')
    }
loss_streak = risk_state['loss_streak']
daily_loss_pct = risk_state['daily_loss_pct']
modo_reducao = risk_state['modo_reducao']

def sincronizar_variaveis():
    global loss_streak, daily_loss_pct, modo_reducao, risk_state
    risk_state = carregar_risk_state()
    loss_streak = risk_state['loss_streak']
    daily_loss_pct = risk_state['daily_loss_pct']
    modo_reducao = risk_state['modo_reducao']

# ==========================================
# PODE OPERAR? (KILL SWITCH)
# ==========================================
def pode_operar(symbol: str = None):
    global daily_loss_pct
    sincronizar_variaveis()
    if daily_loss_pct <= -MAX_DAILY_LOSS:
        print(f"🚫 KILL SWITCH ATIVADO - Loss Diário: {daily_loss_pct:.2%} (Limite: {-MAX_DAILY_LOSS:.2%})")
        _log_risk_activity("kill_switch_global", details={"daily_loss": daily_loss_pct})
        return False

    if symbol and symbol in ASSET_CONFIG:
        asset_cfg = ASSET_CONFIG[symbol]
        if asset_cfg.get("pause_after_losses") and loss_streak >= asset_cfg.get("pause_after_losses", 999):
            print(f"⏸️ {symbol} pausado temporariamente após {loss_streak} losses")
            _log_risk_activity("asset_paused", symbol=symbol)
            return False

    return True

# ==========================================
# REGISTRAR RESULTADO REAL
# ==========================================
def registrar_resultado(resultado_pct: float, symbol: str = None):
    global risk_state, modo_reducao
    risk_state['daily_loss_pct'] += resultado_pct

    if resultado_pct < 0:
        risk_state['loss_streak'] += 1
    else:
        risk_state['loss_streak'] = 0

    if risk_state['loss_streak'] >= LOSS_STREAK_LIMIT:
        if not risk_state['modo_reducao']:
            print(f"⚠️ MODO DEFENSIVO ATIVADO (Streak: {risk_state['loss_streak']})")
            _log_risk_activity("defensive_mode_activated", details={"streak": risk_state['loss_streak']})
        risk_state['modo_reducao'] = True
    elif resultado_pct > 0 and risk_state['modo_reducao']:
        risk_state['modo_reducao'] = False
        print("✅ MODO NORMAL RESTAURADO após lucro.")
        _log_risk_activity("normal_mode_restored")

    salvar_risk_state(risk_state)
    sincronizar_variaveis()

# ==========================================
# RISCO DINÂMICO (POR ATIVO)
# ==========================================
def risco_atual(symbol: str = None) -> float:
    base = RISK_PER_TRADE
    if symbol and symbol in ASSET_CONFIG:
        asset_cfg = ASSET_CONFIG[symbol]
        base = asset_cfg.get("max_risk_pct", base)

    if modo_reducao:
        base *= RISK_REDUCTION_FACTOR

    return min(base, 0.03)

# ==========================================
# VOLATILIDADE (AJUSTE POR ATIVO)
# ==========================================
def ajustar_por_volatilidade(symbol: str, distancia_stop: float, price: float) -> float:
    if price == 0 or distancia_stop == 0:
        return 1.0
    pct = distancia_stop / price

    if symbol and symbol in ASSET_CONFIG:
        asset_cfg = ASSET_CONFIG[symbol]
        high_vol_threshold = asset_cfg.get("high_vol_threshold", 0.02)
        low_vol_threshold = asset_cfg.get("low_vol_threshold", 0.005)
    else:
        high_vol_threshold = 0.02
        low_vol_threshold = 0.005

    if pct > high_vol_threshold:
        return 0.7
    if pct < low_vol_threshold:
        return 1.2
    return 1.0

# ==========================================
# CORE PROFISSIONAL (CÁLCULO DE QUANTIDADE)
# ==========================================
def calcular_quantidade(symbol: str, entry: float, stop: float, leverage: int = None) -> float:
    try:
        account = get_account_info()
        if not account:
            _log_risk_activity("calc_failed_no_account", symbol=symbol)
            return 0
        
        equity = account.get("equity", 0)
        available_balance = account.get("availableBalance", 0)
        
        if equity <= 0 or entry <= 0 or stop <= 0:
            return 0

        risk_pct = risco_atual(symbol)
        risco_usdt = equity * risk_pct

        distancia = abs(entry - stop)
        if distancia == 0:
            return 0

        fator_vol = ajustar_por_volatilidade(symbol, distancia, entry)
        qty_base = (risco_usdt / distancia) * fator_vol

        if leverage is None:
            asset_cfg = ASSET_CONFIG.get(symbol, DEFAULT_ASSET_RISK)
            leverage = asset_cfg.get("max_leverage", DEFAULT_LEVERAGE)
        
        if equity < 100 and leverage > 3:
            leverage = 3
            print(f"[SMALL BANK] Leverage reduzido para 3x em {symbol} (Equity: ${equity:.2f})")

        valor_nominal = qty_base * entry
        margem_necessaria = valor_nominal / leverage
        max_usable_balance = available_balance * 0.90

        if margem_necessaria > max_usable_balance:
            print(f"[RISK WARN] {symbol}: Margem insuficiente. Necessário: ${margem_necessaria:.2f}, Disponível: ${max_usable_balance:.2f}")
            qty_max_possible = (max_usable_balance * leverage) / entry
            print(f"[RISK ADJUST] {symbol}: Lote reduzido de {qty_base:.4f} para {qty_max_possible:.4f}")
            qty_base = qty_max_possible

        min_qty = MIN_QTY_MAP.get(symbol, 0.001)
        step_defaults = {
            "BTCUSDT": 0.001,
            "ETHUSDT": 0.01,
            "SOLUSDT": 0.1,
            "PAXGUSDT": 0.01
        }
        step = step_defaults.get(symbol, 0.01)
        qty_final = round((qty_base // step) * step, 6)
        
        if qty_final < min_qty:
            if qty_base >= min_qty * 0.95:
                print(f"[SMALL BANK FIX] {symbol}: qty {qty_base:.4f} → MIN {min_qty}")
                qty_final = min_qty
            else:
                print(f"[RISK BLOCK] {symbol}: qty {qty_final:.4f} < min {min_qty}. Trade cancelado.")
                _log_risk_activity("qty_blocked", symbol=symbol, details={"qty": qty_final, "min": min_qty})
                return 0

        _log_risk_activity("qty_calculated", symbol=symbol, details={
            "entry": entry, "stop": stop, "qty": qty_final, "leverage": leverage
        })
        return max(qty_final, 0.0)

    except Exception as e:
        print(f"[RISK ERROR] Falha em calcular_quantidade({symbol}): {e}")
        _log_risk_activity("calc_exception", symbol=symbol, details={"error": str(e)})
        return 0

# ==========================================
# AJUSTE FINAL (WRAPPER)
# ==========================================
def ajustar_qty(symbol: str, size_multiplier: float, entry: float = None, stop: float = None) -> float:
    try:
        price = entry if entry else get_price(symbol)
        if not price:
            return 0
        if stop is None:
            stop = price * 0.99 if size_multiplier > 0 else price * 1.01

        base_qty = calcular_quantidade(symbol, price, stop)
        if base_qty == 0:
            return 0
        
        final_qty = base_qty * size_multiplier
        min_qty = MIN_QTY_MAP.get(symbol, 0.001)
        return round(max(final_qty, min_qty), 6)
    except Exception as e:
        print(f"[RISK ERROR] Falha em ajustar_qty({symbol}): {e}")
        return 0

# ==========================================
# STATUS E UTILS
# ==========================================
def get_risk_status() -> dict:
    sincronizar_variaveis()
    return {
        "loss_streak": loss_streak,
        "daily_loss_pct": round(daily_loss_pct, 4),
        "modo_reducao": modo_reducao,
        "risco_atual_pct": round(risco_atual(), 4),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def reset_risk_state():
    global risk_state
    risk_state = {
        "loss_streak": 0,
        "daily_loss_pct": 0.0,
        "modo_reducao": False,
        "date": datetime.now(timezone.utc).strftime('%Y-%m-%d')
    }
    salvar_risk_state(risk_state)
    sincronizar_variaveis()
    print("[RISK] Estado de risco resetado manualmente.")
    _log_risk_activity("manual_reset")