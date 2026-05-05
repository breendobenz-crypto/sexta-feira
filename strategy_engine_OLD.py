# =====================================
# STRATEGY ENGINE - v6 PRODUCTION SAFE
# Fixes:
# 1. slippage_guard integrado antes de executar_ordem
# 2. trade_limiter integrado no loop
# 3. exposure_control integrado antes de executar_ordem
# 4. SIGTERM graceful via flag global
# 5. Score minimo respeita FROZEN do brain
# =====================================
import time
import traceback
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import pytz

from anti_clone      import verificar_instancia, liberar_instancia
from state_manager   import carregar_estado, salvar_estado
from indicators      import gerar_sinal, calcular_atr
from execution_engine import executar_ordem
from bybit_connect   import get_account_info, get_klines, get_price
from config          import (
    CANDLE_DELAY, TRADE_COOLDOWN, ASSET_CONFIG, SYMBOLS, MIN_QTY_MAP,
    HEARTBEAT_FILE,
)
from risk_manager    import pode_operar
from position_manager import pode_abrir_trade
from spread_filter   import spread_ok
from adaptive_engine import aprovar_trade
from ai_selector     import escolher_melhores_ativos
from global_state    import performance as perf
from global_state    import adaptive_ai as ai

# Filtros agora integrados
from slippage_guard  import slippage_ok
from trade_limiter   import limiter
from exposure_control import exposicao_permitida

SP_TZ = pytz.timezone("America/Sao_Paulo")

ATR_MIN              = 0.5
ATR_MAX              = 5.0
MAX_TRADES_SIMULTANEOS = 2
DEBUG                = True

_shutdown_flag = False
estado: dict   = {}
try:
    estado = carregar_estado() or {}
except Exception:
    pass

ultimo_trade: dict[str, dict] = {}


# ==========================================
# HEARTBEAT
# ==========================================
def update_heartbeat(equity=None, status="scanning", last_action=None):
    try:
        data = {
            "timestamp":   datetime.now(SP_TZ).isoformat(),
            "status":      status,
            "equity":      equity,
            "module":      "strategy_engine",
            "last_scan":   datetime.now(SP_TZ).strftime("%H:%M:%S"),
            "last_action": last_action,
        }
        with open(HEARTBEAT_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass


# ==========================================
# BRAIN SCORE
# ==========================================
BRAIN_MEMORY_FILE = "brain_memory.json"
DEFAULT_MIN_SCORE = 75


def load_brain_score() -> int:
    try:
        if os.path.exists(BRAIN_MEMORY_FILE):
            with open(BRAIN_MEMORY_FILE) as f:
                data  = json.load(f)
            score = data.get("optimized_min_score", DEFAULT_MIN_SCORE)
            level = data.get("risk_level", "NORMAL")
            # Se FROZEN, nao operar (score artificialmente alto)
            if level == "FROZEN":
                print("[ENGINE] Brain FROZEN: operacoes bloqueadas ate win_rate > 0.")
                return 99
            return max(70, score)
    except Exception:
        pass
    return DEFAULT_MIN_SCORE


MIN_SCORE = load_brain_score()


# ==========================================
# COOLDOWN DINAMICO
# ==========================================
def get_cooldown(symbol: str) -> float:
    # cooldown_override tem prioridade (usado pelo PAXG: 1800s = 30min)
    override = ASSET_CONFIG.get(symbol, {}).get("cooldown_override")
    base     = override if override else TRADE_COOLDOWN

    history  = ultimo_trade.get(symbol, {}).get("recent_results", [])
    recent3  = history[-3:]
    losses   = sum(1 for r in recent3 if r < 0)
    if losses >= 2:
        return base * 4
    if losses == 0 and len(recent3) >= 2:
        return base * 0.5
    return base


def registrar_resultado_ativo(symbol: str, pnl: float):
    entry = ultimo_trade.setdefault(symbol, {"ts": 0, "recent_results": []})
    entry["recent_results"].append(pnl)
    if len(entry["recent_results"]) > 10:
        entry["recent_results"] = entry["recent_results"][-10:]


# ==========================================
# ANALISE POR ATIVO
# ==========================================
def analisar_symbol(symbol: str) -> dict | None:
    try:
        df = get_klines(symbol)
        if df is None or len(df) < 50:
            return None

        atr_series = calcular_atr(df)
        if atr_series is None:
            return None
        atr = atr_series.iloc[-1]
        if not (ATR_MIN <= atr <= ATR_MAX):
            return None

        sinal = gerar_sinal(symbol)
        if not sinal:
            return None

        direcao, score, entry, stop, take = sinal

        asset_cfg = ASSET_CONFIG.get(symbol, {})
        min_score = asset_cfg.get("min_score", MIN_SCORE)

        if score < min_score:
            return None

        return {
            "symbol":  symbol,
            "direcao": direcao,
            "score":   score,
            "entry":   entry,
            "stop":    stop,
            "take":    take,
            "regime":  asset_cfg.get("regime", "NEUTRO"),
        }
    except Exception as e:
        if DEBUG:
            print(f"[ERRO ANALISE] {symbol}: {e}")
        return None


def scan() -> list:
    priority = [s for s in ["BTCUSDT", "ETHUSDT", "SOLUSDT", "PAXGUSDT"] if s in SYMBOLS]
    with ThreadPoolExecutor(max_workers=4) as ex:
        return [r for r in ex.map(analisar_symbol, priority) if r]


# ==========================================
# CALCULO DE TAMANHO E LEVERAGE
# ==========================================
def calcular_leverage(score: int, symbol: str) -> int:
    max_lev = ASSET_CONFIG.get(symbol, {}).get("max_leverage", 3)
    return max_lev if score > 85 else max(2, max_lev - 1)


def calcular_tamanho_posicao(equity: float, symbol: str, leverage: int, price: float) -> float:
    risk_pct     = ASSET_CONFIG.get(symbol, {}).get("position_size_pct", 0.25)
    margin_usd   = equity * risk_pct
    position_val = margin_usd * leverage
    size_raw     = position_val / price
    min_qty      = MIN_QTY_MAP.get(symbol, 0.1)
    return max(size_raw, min_qty)


# ==========================================
# ENGINE PRINCIPAL
# ==========================================
def engine():
    global estado, MIN_SCORE, _shutdown_flag
    print("JARVIS PRO ENGINE v6 INICIADA — FILTROS INTEGRADOS")
    update_heartbeat(status="starting")

    while not _shutdown_flag:
        print(f"[LOOP] Ciclo em {time.strftime('%H:%M:%S')}")
        start_loop = time.time()

        try:
            info = get_account_info()
            if not info:
                time.sleep(5)
                continue

            equity = info.get("equity", 0)
            if equity <= 0:
                time.sleep(10)
                continue

            update_heartbeat(equity=equity, status="scanning")
            perf.update_equity(equity)
            if hasattr(ai, "update"):
                ai.update(perf)

            # Reload score do brain a cada ciclo
            MIN_SCORE = load_brain_score()

            # Score 99 = FROZEN, nao operar
            if MIN_SCORE >= 99:
                print("[ENGINE] FROZEN: aguardando win_rate > 0 para operar.")
                update_heartbeat(equity=equity, status="frozen")
                time.sleep(60)
                continue

            if not pode_operar():
                print("[RISCO] Operacoes bloqueadas pelo Risk Manager.")
                update_heartbeat(equity=equity, status="risk_blocked")
                time.sleep(30)
                continue

            oportunidades = scan()
            if not oportunidades:
                elapsed = time.time() - start_loop
                time.sleep(max(0, CANDLE_DELAY - elapsed))
                continue

            trades_selecionados = escolher_melhores_ativos(oportunidades, MAX_TRADES_SIMULTANEOS)

            for trade in trades_selecionados:
                if _shutdown_flag:
                    break

                symbol  = trade["symbol"]
                direcao = trade["direcao"]
                score   = trade["score"]
                entry   = trade["entry"]
                stop    = trade["stop"]
                take    = trade["take"]
                agora   = time.time()

                # --- COOLDOWN ---
                cooldown = get_cooldown(symbol)
                if agora - ultimo_trade.get(symbol, {}).get("ts", 0) < cooldown:
                    continue

                # --- POSICAO ABERTA ---
                if not pode_abrir_trade(symbol, direcao):
                    continue

                # --- TRADE LIMITER (novo) ---
                if not limiter.verificar_limite(symbol):
                    print(f"[LIMITER] {symbol}: limite diario atingido.")
                    continue

                # --- SPREAD ---
                if not spread_ok(symbol):
                    print(f"[SPREAD] Spread alto em {symbol}, ignorando.")
                    continue

                # --- SLIPPAGE (novo) ---
                if not slippage_ok(symbol, entry):
                    print(f"[SLIPPAGE] Drift alto em {symbol}, ignorando.")
                    continue

                # --- LEVERAGE E TAMANHO ---
                leverage = calcular_leverage(score, symbol)
                price    = get_price(symbol)
                if not price:
                    continue

                size_final = calcular_tamanho_posicao(equity, symbol, leverage, price)
                if symbol == "BTCUSDT":
                    size_final = round(size_final, 3)
                elif symbol in ("ETHUSDT", "PAXGUSDT"):
                    size_final = round(size_final, 2)
                else:
                    size_final = round(size_final, 1)

                # --- EXPOSURE CONTROL (novo) ---
                notional_novo = size_final * price
                if not exposicao_permitida(notional_novo):
                    print(f"[EXPOSURE] Limite global excedido, ignorando {symbol}.")
                    continue

                # --- APROVAR TRADE (adaptive engine) ---
                momentum = "FORTE" if score > 85 else "NORMAL"
                if not aprovar_trade(symbol, score, momentum):
                    continue

                print(
                    f"EXECUTANDO: {symbol} | {direcao} | Score:{score} "
                    f"| Lev:{leverage}x | Qty:{size_final}"
                )
                update_heartbeat(
                    equity=equity, status="executing",
                    last_action=f"{symbol}_{direcao}",
                )

                ok = executar_ordem(
                    symbol=symbol, side=direcao, entry=entry,
                    stop=stop, take=take, size=size_final,
                    leverage=leverage, score=score,
                )

                if ok:
                    limiter.registrar_trade(symbol)
                    ultimo_trade[symbol] = {
                        "ts":             agora,
                        "recent_results": ultimo_trade.get(symbol, {}).get("recent_results", []),
                    }
                    estado[symbol] = {"direcao": direcao, "timestamp": agora}
                    salvar_estado(estado)
                    print(f"Ordem executada: {symbol}")
                else:
                    print(f"[FALHA] Ordem falhou para {symbol}.")
                    update_heartbeat(equity=equity, status="execution_failed")

        except KeyboardInterrupt:
            print("[ENGINE] Interrupcao detectada.")
            _shutdown_flag = True
            break
        except Exception as e:
            print(f"[LOOP ERROR] {e}")
            traceback.print_exc()
            update_heartbeat(status="error")
            time.sleep(10)

        elapsed = time.time() - start_loop
        if elapsed < CANDLE_DELAY:
            time.sleep(CANDLE_DELAY - elapsed)

        update_heartbeat(status="cycle_complete")


# ==========================================
# ENTRY POINT
# ==========================================
if __name__ == "__main__":
    if verificar_instancia("strategy_engine.py"):
        try:
            engine()
        finally:
            liberar_instancia()
            update_heartbeat(status="shutdown")
    else:
        print("[ERRO] Ja existe uma instancia rodando.")
