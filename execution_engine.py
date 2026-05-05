# execution_engine.py - JARVIS PRO SAAS (COM IA ANTHROPIC)
import time
import threading
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from okx_connect import OKXClient, place_order, get_price, get_position, update_stop_loss, adjust_qty, get_closed_pnl
except ImportError:
    try:
        from bybit_connect import place_order, get_price, get_position, update_stop_loss, adjust_qty, get_closed_pnl
    except ImportError:
        def place_order(**k): return None
        def get_price(s): return None
        def get_position(s): return None
        def update_stop_loss(s, p): return False
        def adjust_qty(s, q): return q
        def get_closed_pnl(s, l=1): return {"retCode": -1, "result": {"list": []}}

from risk_manager import registrar_resultado
from saas_db import save_trade, update_trade_exit # Importa do saas_db atualizado
from anthropic_agent import generate_reasoning # Importa o agente de IA

try:
    from config import ASSET_CONFIG, MAX_TRADES_ABERTOS, MAX_DAILY_LOSS, RISK_PER_TRADE, TRADE_COOLDOWN
except ImportError:
    ASSET_CONFIG, MAX_TRADES_ABERTOS, MAX_DAILY_LOSS, RISK_PER_TRADE, TRADE_COOLDOWN = {}, 2, 0.05, 0.005, 900

try:
    from obsidian_agent import ObsidianAgent
    obsidian_agent = ObsidianAgent()
except ImportError:
    obsidian_agent = None

try:
    import telegram_bot as tg
except ImportError:
    tg = None

try:
    from alert_monitor import send_telegram_alert
except ImportError:
    send_telegram_alert = lambda msg, type=None, chat_id=None: None

def get_asset_trading_params(symbol: str) -> dict:
    return {**{"trailing_pct": 0.005, "breakeven_pct": 0.003, "partial_close_pct": 0.5, "partial_trigger_pct": 0.004}, **ASSET_CONFIG.get(symbol, {})}

state_lock = threading.Lock()
trades_hoje = 0
pnl_hoje_usdt = 0.0
_posicoes_ativas = {}
_data_lock = threading.Lock()
_partial_done, _last_stop = {}, {}

def get_trades_count():
    with state_lock: return trades_hoje
def get_daily_pnl():
    with state_lock: return pnl_hoje_usdt
def is_position_open(symbol: str):
    with state_lock: return symbol in _posicoes_ativas
def add_position_thread(symbol, thread):
    with state_lock: _posicoes_ativas[symbol] = thread
def remove_position_thread(symbol):
    with state_lock: _posicoes_ativas.pop(symbol, None)

def executar_ordem(*args, **kwargs):
    if args and hasattr(args[0], 'place_order'): return _executar_ordem_saas(*args, **kwargs)
    else: return _executar_ordem_legacy(*args, **kwargs)

def _executar_ordem_saas(client, symbol, side, signal_data, user_id=None):
    return _executar_ordem_core(client=client, symbol=symbol, side=side, entry=signal_data.get('entry'), stop=signal_data.get('stop'), take=signal_data.get('take'), size=0.01, score=signal_data.get('score', 70), user_id=user_id)

def _executar_ordem_legacy(symbol, side, entry, stop, take, size, leverage=None, score=70, user_id=None):
    return _executar_ordem_core(client=None, symbol=symbol, side=side, entry=entry, stop=stop, take=take, size=size, score=score, user_id=user_id)

def _executar_ordem_core(client, symbol, side, entry, stop, take, size, score=70, user_id=None):
    global trades_hoje, pnl_hoje_usdt
    if is_position_open(symbol): return False
    with state_lock:
        if len(_posicoes_ativas) >= MAX_TRADES_ABERTOS or trades_hoje >= 10: return False
        try:
            _info = client.get_account_info() if client else (get_account_info() if 'get_account_info' in globals() else None)
            _equity = float(_info.get("equity", 0)) if _info else 0
        except: _equity = 0
        if pnl_hoje_usdt <= -(_equity * MAX_DAILY_LOSS if _equity > 0 else MAX_DAILY_LOSS * 100): return False

    price = get_price(symbol) if not client else client.get_price(symbol)
    if price is None: return False
    qty = adjust_qty(symbol, float(size)) if not client else client.adjust_qty(symbol, float(size))
    if qty <= 0: return False

    try:
        resp = client.place_order(symbol=symbol, side=side, qty=qty, stopLoss=stop, takeProfit=take, reduce_only=False) if client else place_order(symbol=symbol, side=side, qty=qty, stopLoss=stop, takeProfit=take, reduce_only=False)
        if not resp: return False

        logger.info(f"[EXEC] {symbol} | {side} | Qty:{qty} | Entry:{entry} | SL:{stop} | TP:{take} | Score:{score}")
        
        # ✅ GERAR RACIOCÍNIO COM IA
        ai_text = "Setup técnico padrão"
        try:
            ai_text = generate_reasoning(symbol, side, score, entry)
            logger.info(f"🧠 IA Gerou: {ai_text}")
        except Exception as e:
            logger.warning(f"⚠️ Falha na IA: {e}")

        # Salva no banco (se tiver user_id)
        if user_id:
            save_trade(user_id, symbol, side, entry, qty, score, ai_text)
        else:
            save_trade(symbol, side, entry, qty, score, ai_text) # Fallback se user_id não vier

        open_time = datetime.now()
        if obsidian_agent:
            try: obsidian_agent.log_trade({"symbol": symbol, "side": side, "open_time": open_time, "entry": entry, "stop": stop, "take": take, "qty": qty, "score": score, "status": "OPEN", "pnl_usdt": 0.0})
            except: pass

        if tg:
            try: tg.enviar_sinal_com_grafico(ativo=symbol, direcao=side, score=str(score), entrada=entry, take=take, stop=stop, hora=open_time.strftime("%H:%M:%S"))
            except: pass

        vip_group = os.getenv("TELEGRAM_VIP_GROUP_ID")
        if vip_group:
            msg = (f"🚀 **NOVO TRADE ABERTO**\n\n"
                   f"📦 Ativo: `{symbol}`\n🎯 Direção: **{side}**\n💰 Entrada: `${entry}`\n🛑 Stop: `${stop}`\n🎁 Take: `${take}`\n🧠 Score: {score}/100")
            send_telegram_alert(msg, "success", chat_id=vip_group)

        thread = threading.Thread(target=monitorar_posicao, args=(symbol, side, entry, qty, score, open_time, client), daemon=True)
        thread.start()
        add_position_thread(symbol, thread)
        with state_lock: trades_hoje += 1
        return True
    except Exception as e:
        logger.critical(f"[ERRO CRÍTICO] executar_ordem: {e}")
        if tg: tg.alerta_erro(str(e))
        return False

def monitorar_posicao(symbol, side, entry_price, initial_qty, score=70, open_time=None, client=None):
    logger.info(f"[MONITOR] {symbol} iniciado")
    start_time, timeout = time.time(), 3600 * 6
    params = get_asset_trading_params(symbol)
    local_partial_done, local_last_stop, is_long = False, entry_price, str(side).upper() in ["LONG", "BUY"]
    try:
        while True:
            if time.time() - start_time > timeout: break
            pos = client.get_position(symbol) if client else get_position(symbol)
            current_size = float(pos.get("size", 0)) if pos else 0

            if current_size == 0:
                exit_price = get_price(symbol) if not client else client.get_price(symbol) or entry_price
                final_pnl = 0.0
                try:
                    hist = client.get_closed_pnl(symbol, limit=1) if client else (get_closed_pnl(symbol, limit=1) if 'get_closed_pnl' in globals() else {"retCode": -1})
                    if hist and hist.get("retCode") == 0 and hist.get("result", {}).get("list"):
                        final_pnl = float(hist["result"]["list"][0].get("closedPnl", 0))
                except:
                    diff = (exit_price - entry_price) if is_long else (entry_price - exit_price)
                    final_pnl = diff * initial_qty
                
                pnl_pct = (final_pnl / (initial_qty * entry_price)) * 100 if entry_price > 0 else 0
                # update_trade_exit(symbol, exit_price, final_pnl, pnl_pct) # Comentado para evitar erro de user_id missing
                logger.info(f"[FECHADO] {symbol} | PnL: ${final_pnl:.2f} ({pnl_pct:.2f}%)")

                if obsidian_agent and open_time:
                    try: obsidian_agent.update_trade_close(symbol=symbol, side=side, open_time=open_time, pnl=final_pnl, status="CLOSED")
                    except: pass
                if tg:
                    try: tg.alerta_stop(symbol) if final_pnl < 0 else tg._send(f"TARGET HIT\n{symbol}\nPnL: ${final_pnl:.2f}")
                    except: pass

                vip_group = os.getenv("TELEGRAM_VIP_GROUP_ID")
                if vip_group:
                    emoji = "🤑" if final_pnl > 0 else "📉"
                    msg = (f"{emoji} **TRADE FECHADO**\n\n📦 Ativo: `{symbol}`\n💰 Resultado: **${final_pnl:.2f}** ({pnl_pct:.2f}%)\n🎯 Entrada: `${entry_price}`\n🏁 Saída: `${exit_price}`")
                    send_telegram_alert(msg, "info" if final_pnl >= 0 else "error", chat_id=vip_group)

                with state_lock:
                    global pnl_hoje_usdt
                    pnl_hoje_usdt += final_pnl
                    registrar_resultado(pnl_pct / 100)
                break

            if client: current_price = float(pos.get("markPrice", 0)) or client.get_price(symbol)
            else: current_price = float(pos.get("markPrice", 0)) or get_price(symbol)
            if current_price is None: time.sleep(2); continue

            if not local_partial_done and current_size == initial_qty:
                if _fazer_parcial(symbol, side, entry_price, current_price, current_size, params, client):
                    local_partial_done = True
                    with _data_lock: _partial_done[symbol] = True

            new_stop = _calcular_trailing(side, entry_price, current_price, local_last_stop, params)
            if new_stop is not None:
                with _data_lock: prev = _last_stop.get(symbol)
                if prev != new_stop:
                    try:
                        ok = client.update_stop_loss(symbol, new_stop) if client else update_stop_loss(symbol, new_stop)
                        if ok:
                            with _data_lock: _last_stop[symbol] = new_stop
                            local_last_stop = new_stop
                    except: pass
            time.sleep(2)
    except Exception as e: logger.error(f"[ERRO MONITOR] {symbol}: {e}")
    finally:
        remove_position_thread(symbol)
        with _data_lock: _partial_done.pop(symbol, None); _last_stop.pop(symbol, None)

def _fazer_parcial(symbol, side, entry, current_price, size, params, client=None):
    gain_pct = (current_price - entry) / entry if str(side).upper() in ["LONG", "BUY"] else (entry - current_price) / entry
    if gain_pct < params["partial_trigger_pct"]: return False
    try:
        qty_close = round(size * params["partial_close_pct"], 3)
        if qty_close <= 0: return False
        opp_side = "Sell" if str(side).upper() in ["LONG", "BUY"] else "Buy"
        resp = client.place_order(symbol=symbol, side=opp_side, qty=qty_close, reduce_only=True) if client else place_order(symbol=symbol, side=opp_side, qty=qty_close, reduce_only=True)
        if resp: logger.info(f"[PARCIAL] {symbol}: {qty_close} fechados."); return True
    except: pass
    return False

def _calcular_trailing(side, entry, current_price, last_stop, params):
    is_long = str(side).upper() in ["LONG", "BUY"]
    gain_pct = (current_price - entry) / entry if is_long else (entry - current_price) / entry
    if gain_pct > params["trailing_pct"]: dist = current_price * params["trailing_pct"]; new_stop = current_price - dist if is_long else current_price + dist
    elif gain_pct > params["breakeven_pct"]: new_stop = entry
    else: return None
    new_stop = round(new_stop, 2)
    if (is_long and new_stop <= last_stop) or (not is_long and new_stop >= last_stop): return None
    return new_stop

def reset_daily_counters():
    global trades_hoje, pnl_hoje_usdt
    with state_lock: trades_hoje = 0; pnl_hoje_usdt = 0.0
    with _data_lock: _partial_done.clear(); _last_stop.clear()
    logger.info("[RESET] Contadores diários zerados.")