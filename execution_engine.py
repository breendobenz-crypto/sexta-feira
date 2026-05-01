# execution_engine.py - JARVIS PRO SAAS (V5 - MULTI-CONTA & THREAD-SAFE)
# Funcionalidades: Obsidian Agent, Trailing Stop, Parcial, Telegram, Risk Manager, Thread Locks
# Compatível com: okx_connect.py (classe OKXClient) e modo legado

import time
import threading
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ==========================================
# IMPORTS CORE (COM FALLBACK SEGURO)
# ==========================================
try:
    from okx_connect import OKXClient, place_order, get_price, get_position, update_stop_loss, adjust_qty, get_closed_pnl
except ImportError:
    try:
        from bybit_connect import place_order, get_price, get_position, update_stop_loss, adjust_qty, get_closed_pnl
    except ImportError:
        # Fallback vazio para não quebrar imports
        def place_order(**k): return None
        def get_price(s): return None
        def get_position(s): return None
        def update_stop_loss(s, p): return False
        def adjust_qty(s, q): return q
        def get_closed_pnl(s, l=1): return {"retCode": -1, "result": {"list": []}}

from risk_manager import registrar_resultado

# Config (com defaults se não existir)
try:
    from config import ASSET_CONFIG, MAX_TRADES_ABERTOS, MAX_DAILY_LOSS, RISK_PER_TRADE, TRADE_COOLDOWN
except ImportError:
    ASSET_CONFIG = {}
    MAX_TRADES_ABERTOS = 2
    MAX_DAILY_LOSS = 0.05
    RISK_PER_TRADE = 0.005
    TRADE_COOLDOWN = 900

# Database (com fallback)
try:
    from database import save_trade, update_trade_exit
except ImportError:
    save_trade = lambda *a, **k: None
    update_trade_exit = lambda *a, **k: None

# ==========================================
# MÓDULOS OPCIONAIS (OBSIDIAN & TELEGRAM)
# ==========================================
try:
    from obsidian_agent import ObsidianAgent
    obsidian_agent = ObsidianAgent()
    logger.info("🟣 [OBSIDIAN] Agente de escrita carregado.")
except ImportError:
    obsidian_agent = None
    logger.warning("⚠️ [OBSIDIAN] Não carregado. Logs automáticos desativados.")

try:
    import telegram_bot as tg
except ImportError:
    tg = None
    logger.warning("⚠️ [TELEGRAM] Não carregado. Notificações desativadas.")

# ==========================================
# CONFIG POR ATIVO
# ==========================================
def get_asset_trading_params(symbol: str) -> dict:
    defaults = {
        "trailing_pct": 0.005,
        "breakeven_pct": 0.003,
        "partial_close_pct": 0.5,
        "partial_trigger_pct": 0.004,
    }
    return {**defaults, **ASSET_CONFIG.get(symbol, {})}

# ==========================================
# ESTADO GLOBAL — PROTEGIDO POR LOCKS
# ==========================================
state_lock = threading.Lock()
trades_hoje = 0
pnl_hoje_usdt = 0.0
_posicoes_ativas: dict[str, threading.Thread] = {}

# Lock para dados compartilhados entre threads
_data_lock = threading.Lock()
_partial_done: dict[str, bool] = {}
_last_stop: dict[str, float] = {}

def get_trades_count() -> int:
    with state_lock:
        return trades_hoje

def get_daily_pnl() -> float:
    with state_lock:
        return pnl_hoje_usdt

def is_position_open(symbol: str) -> bool:
    with state_lock:
        return symbol in _posicoes_ativas

def add_position_thread(symbol: str, thread: threading.Thread):
    with state_lock:
        _posicoes_ativas[symbol] = thread

def remove_position_thread(symbol: str):
    with state_lock:
        _posicoes_ativas.pop(symbol, None)

# ==========================================
# EXECUTAR ORDEM (ASSINATURA FLEXÍVEL)
# ==========================================
def executar_ordem(*args, **kwargs):
    """
    Assinatura flexível para compatibilidade SaaS/Legacy:
    
    Modo SaaS: executar_ordem(client, symbol, direction, signal_data)
    Modo Legacy: executar_ordem(symbol, side, entry, stop, take, size, score=70)
    """
    # Detecta modo pelo primeiro argumento
    if args and hasattr(args[0], 'place_order'):
        # Modo SaaS: primeiro arg é OKXClient
        return _executar_ordem_saas(*args, **kwargs)
    else:
        # Modo Legacy
        return _executar_ordem_legacy(*args, **kwargs)

def _executar_ordem_saas(client, symbol, side, signal_data):
    """Executa ordem usando cliente OKX isolado (SaaS mode)."""
    entry = signal_data.get('entry')
    stop = signal_data.get('stop')
    take = signal_data.get('take')
    score = signal_data.get('score', 70)
    size = 0.01  # Será calculado pelo risk_manager
    
    return _executar_ordem_core(
        client=client, symbol=symbol, side=side,
        entry=entry, stop=stop, take=take, size=size, score=score
    )

def _executar_ordem_legacy(symbol, side, entry, stop, take, size, leverage=None, score=70):
    """Executa ordem usando funções globais (Legacy mode)."""
    return _executar_ordem_core(
        client=None, symbol=symbol, side=side,
        entry=entry, stop=stop, take=take, size=size, score=score
    )

def _executar_ordem_core(client, symbol, side, entry, stop, take, size, score=70):
    """Lógica central de execução de ordem."""
    global trades_hoje, pnl_hoje_usdt
    
    if is_position_open(symbol):
        logger.warning(f"[BLOCK] Posição ativa em {symbol}")
        return False

    with state_lock:
        if len(_posicoes_ativas) >= MAX_TRADES_ABERTOS:
            logger.warning(f"[BLOCK] Limite de {MAX_TRADES_ABERTOS} trades abertos atingido.")
            return False
        if trades_hoje >= 10:
            logger.warning("[BLOCK] Limite diário de trades atingido.")
            return False
        
        # Kill Switch Diário
        try:
            if client:
                _info = client.get_account_info()
            else:
                _info = get_account_info() if 'get_account_info' in globals() else None
            _equity = float(_info.get("equity", 0)) if _info else 0
        except:
            _equity = 0
            
        _kill_threshold = _equity * MAX_DAILY_LOSS if _equity > 0 else MAX_DAILY_LOSS * 100
        if pnl_hoje_usdt <= -_kill_threshold:
            logger.critical(f"[KILL SWITCH] Loss diário ${abs(pnl_hoje_usdt):.2f} excedeu limite.")
            if tg: tg.alerta_kill()
            return False

    price = get_price(symbol) if not client else client.get_price(symbol)
    if price is None:
        logger.error(f"[ERRO] Preço indisponível para {symbol}")
        return False

    qty = adjust_qty(symbol, float(size)) if not client else client.adjust_qty(symbol, float(size))
    if qty <= 0:
        logger.warning(f"[BLOCK] Quantidade inválida: {size} -> {qty}")
        return False

    try:
        # Executa ordem
        if client:
            resp = client.place_order(symbol=symbol, side=side, qty=qty, stopLoss=stop, takeProfit=take, reduce_only=False)
        else:
            resp = place_order(symbol=symbol, side=side, qty=qty, stopLoss=stop, takeProfit=take, reduce_only=False)
            
        if not resp:
            logger.error(f"[ERRO] Falha ao enviar ordem para {symbol}")
            return False

        logger.info(f"[EXEC] {symbol} | {side} | Qty:{qty} | Entry:{entry} | SL:{stop} | TP:{take} | Score:{score}")
        save_trade(symbol, side, entry, qty, score)

        # 🟣 [OBSIDIAN] Cria nota de trade (Fire & Forget)
        open_time = datetime.now()
        if obsidian_agent:
            try:
                obsidian_agent.log_trade({
                    "symbol": symbol, "side": side, "open_time": open_time,
                    "entry": entry, "stop": stop, "take": take,
                    "qty": qty, "score": score, "status": "OPEN", "pnl_usdt": 0.0
                })
            except Exception as e:
                logger.warning(f"[WARN] Falha ao logar trade no Obsidian (abertura): {e}")

        # 📢 Telegram
        if tg:
            hora = open_time.strftime("%H:%M:%S")
            tg.enviar_sinal_com_grafico(
                ativo=symbol, direcao=side, score=str(score),
                entrada=entry, take=take, stop=stop, hora=hora
            )

        # 🧵 Inicia Monitoramento
        thread = threading.Thread(
            target=monitorar_posicao,
            args=(symbol, side, entry, qty, score, open_time, client),
            daemon=True
        )
        thread.start()
        add_position_thread(symbol, thread)

        with state_lock:
            trades_hoje += 1
        return True

    except Exception as e:
        logger.critical(f"[ERRO CRÍTICO] executar_ordem: {e}")
        if tg: tg.alerta_erro(str(e))
        return False

# ==========================================
# MONITOR DE POSIÇÃO
# ==========================================
def monitorar_posicao(symbol, side, entry_price, initial_qty, score=70, open_time=None, client=None):
    logger.info(f"[MONITOR] {symbol} iniciado (Score:{score})")
    start_time = time.time()
    timeout = 3600 * 6  # 6 horas máximo
    params = get_asset_trading_params(symbol)
    
    # Estado local da thread
    local_partial_done = False
    local_last_stop = entry_price
    side_upper = str(side).upper()
    is_long = side_upper in ["LONG", "BUY"]

    try:
        while True:
            if time.time() - start_time > timeout:
                logger.info(f"[TIMEOUT] Monitor {symbol} encerrado por tempo.")
                break

            # Pega posição
            if client:
                pos = client.get_position(symbol)
            else:
                pos = get_position(symbol)
            current_size = float(pos.get("size", 0)) if pos else 0

            # Posição Fechada (Alvo ou Stop)
            if current_size == 0:
                exit_price = get_price(symbol) if not client else client.get_price(symbol)
                if exit_price is None:
                    exit_price = entry_price
                    
                final_pnl = 0.0
                try:
                    # Tenta pegar PnL real da exchange
                    if client:
                        hist = client.get_closed_pnl(symbol, limit=1)
                    else:
                        hist = get_closed_pnl(symbol, limit=1) if 'get_closed_pnl' in globals() else {"retCode": -1}
                    if hist and hist.get("retCode") == 0:
                        rows = hist.get("result", {}).get("list", [])
                        if rows:
                            final_pnl = float(rows[0].get("closedPnl", 0))
                except:
                    # Fallback matemático
                    diff = (exit_price - entry_price) if is_long else (entry_price - exit_price)
                    final_pnl = diff * initial_qty

                pnl_pct = (final_pnl / (initial_qty * entry_price)) * 100 if entry_price > 0 else 0
                update_trade_exit(symbol, exit_price, final_pnl, pnl_pct)
                
                logger.info(f"[FECHADO] {symbol} | PnL: ${final_pnl:.2f} ({pnl_pct:.2f}%)")

                # 🟣 [OBSIDIAN] Atualiza nota com resultado
                if obsidian_agent and open_time:
                    try:
                        obsidian_agent.update_trade_close(
                            symbol=symbol, side=side, open_time=open_time,
                            pnl=final_pnl, status="CLOSED"
                        )
                    except Exception as e:
                        logger.warning(f"[WARN] Falha ao atualizar Obsidian (fechamento): {e}")

                # 📢 Alertas
                if tg:
                    if final_pnl < 0:
                        tg.alerta_stop(symbol)
                    else:
                        tg._send(f"TARGET HIT\n{symbol}\nPnL: ${final_pnl:.2f}")

                with state_lock:
                    global pnl_hoje_usdt
                    pnl_hoje_usdt += final_pnl
                    registrar_resultado(pnl_pct / 100)

                break

            # Monitoramento Ativo
            if client:
                current_price = float(pos.get("markPrice", 0)) if pos else client.get_price(symbol)
            else:
                current_price = float(pos.get("markPrice", 0)) if pos else get_price(symbol)
            if current_price is None:
                time.sleep(2)
                continue

            # Parcial
            if not local_partial_done and current_size == initial_qty:
                if _fazer_parcial(symbol, side, entry_price, current_price, current_size, params, client):
                    local_partial_done = True
                    with _data_lock:
                        _partial_done[symbol] = True

            # Trailing Stop
            new_stop = _calcular_trailing(side, entry_price, current_price, local_last_stop, params)
            if new_stop is not None:
                with _data_lock:
                    prev = _last_stop.get(symbol)
                if prev != new_stop:
                    try:
                        if client:
                            ok = client.update_stop_loss(symbol, new_stop)
                        else:
                            ok = update_stop_loss(symbol, new_stop)
                        if ok:
                            with _data_lock:
                                _last_stop[symbol] = new_stop
                            local_last_stop = new_stop
                            logger.info(f"[TRAIL] {symbol} stop → {new_stop}")
                    except Exception as e:
                        logger.error(f"[ERRO TRAIL] {e}")

            time.sleep(2)

    except Exception as e:
        logger.error(f"[ERRO MONITOR] {symbol}: {e}")
    finally:
        remove_position_thread(symbol)
        with _data_lock:
            _partial_done.pop(symbol, None)
            _last_stop.pop(symbol, None)
        logger.info(f"[CLEANUP] Thread {symbol} encerrada.")

# ==========================================
# PARCIAL
# ==========================================
def _fazer_parcial(symbol, side, entry, current_price, size, params, client=None) -> bool:
    gain_pct = (current_price - entry) / entry if str(side).upper() in ["LONG", "BUY"] else (entry - current_price) / entry
    if gain_pct < params["partial_trigger_pct"]:
        return False
    try:
        qty_close = round(size * params["partial_close_pct"], 3)
        if qty_close <= 0:
            return False
        
        opp_side = "Sell" if str(side).upper() in ["LONG", "BUY"] else "Buy"
        if client:
            resp = client.place_order(symbol=symbol, side=opp_side, qty=qty_close, reduce_only=True)
        else:
            resp = place_order(symbol=symbol, side=opp_side, qty=qty_close, reduce_only=True)
            
        if resp:
            logger.info(f"[PARCIAL] {symbol}: {qty_close} fechados com {gain_pct:.2%} lucro.")
            return True
    except Exception as e:
        logger.error(f"[ERRO PARCIAL] {e}")
    return False

# ==========================================
# TRAILING STOP
# ==========================================
def _calcular_trailing(side, entry, current_price, last_stop, params) -> float | None:
    is_long = str(side).upper() in ["LONG", "BUY"]
    gain_pct = (current_price - entry) / entry if is_long else (entry - current_price) / entry
    
    if gain_pct > params["trailing_pct"]:
        dist = current_price * params["trailing_pct"]
        new_stop = current_price - dist if is_long else current_price + dist
    elif gain_pct > params["breakeven_pct"]:
        new_stop = entry
    else:
        return None

    new_stop = round(new_stop, 2)
    if is_long and new_stop <= last_stop:
        return None
    if not is_long and new_stop >= last_stop:
        return None
    return new_stop

# ==========================================
# RESET DIÁRIO
# ==========================================
def reset_daily_counters():
    global trades_hoje, pnl_hoje_usdt
    with state_lock:
        trades_hoje = 0
        pnl_hoje_usdt = 0.0
    with _data_lock:
        _partial_done.clear()
        _last_stop.clear()
    logger.info("[RESET] Contadores diários zerados.")